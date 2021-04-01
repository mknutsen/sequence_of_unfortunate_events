import logging

from math import ceil, floor
from threading import Thread
from time import sleep, time_ns
from typing import Dict, List, Optional

from mido import Message
from random import choice, randint

from pygame import Color, Surface
from pygame.sprite import Group, Sprite

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000


def display_sequence(sequence: List[Optional[Message]], beats_per_measure, number_bars_in_sequence, sequences_per_beat):
    string = "".join([f"{i :<4}" for i in range(1, 1 + number_bars_in_sequence)]) + "\n"
    for index, item in enumerate(sequence, start=1):
        string += f"{item.note if item else '_' :<4}"

        if index % (sequences_per_beat * beats_per_measure) == 0:
            string += "\n"
    return string


class Button(Sprite):
    def __init__(self, x, y, width, height, check_callback, index, click_callback, note):
        Sprite.__init__(self)
        self.image = Surface((width, height))
        print(index, "create", x, y, " - ", x + width, y + height)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.check_callback = check_callback
        self.index = index
        self.click_callback = click_callback
        self.note = note

    def update(self) -> None:
        color = (255, 255, 255) if self.check_callback(self.index, self.note) else (0, 0, 0)
        self.image.fill(color)

    def click(self, x, y):
        if self.rect.collidepoint(x, y):
            print("pass", x, y, self.index)
            self.click_callback(self.index, self.note)


class Track:

    def create_sequence(self):
        note = self.last_note
        if note in self.sequences:
            return
        sequence = self.make_sequence()
        self.sequences[note] = sequence
        num_sequences = len(self.sequences)
        seq_len = len(sequence)
        button_width = SCREEN_WIDTH / seq_len / 2
        button_height = 50
        for index in range(0, floor(seq_len)):
            self.sprites.add(
                Button(x=index * button_width * 2, y=2 * button_height * num_sequences, width=button_width, height=button_height,
                       check_callback=self._check, note=note,
                       click_callback=self._click, index=index))

    def toggle_mute(self):
        self.mute = not self.mute

    def __init__(self, number_bars_in_sequence, beats_per_measure, sequences_per_beat, MICROSECONDS_PER_BEAT,
                 MICROSECONDS_PER_SECOND, NANOSECONDS_PER_MICROSECOND, channel, send_function):
        self.channel = channel
        self.mute = False
        self.color = (randint(0, 255), randint(0, 255), randint(0, 255))
        self.last_note = 50
        self.sequences: Dict[int, List[Optional[Message]]] = {}
        self.start_time_ns = time_ns()
        self.sprites = Group()
        self.number_bars_in_sequence = number_bars_in_sequence
        self.beats_per_measure = beats_per_measure
        self.sequences_per_beat = sequences_per_beat

        def _clear(sequence_number, note):
            self.sequences[note][sequence_number] = None

        def _click(sequence_number, note):
            if _check(sequence_number, note):
                _clear(sequence_number, note)
            else:
                self.fill_note(beat_count=sequence_number, note=note)

        def _check(sequence_number, note) -> bool:
            return self.sequences[note][sequence_number] is not None

        self._click = _click
        self._clear = _clear
        self._check = _check

        # self.create_sequence()
        def _target():
            current_time_ns = time_ns()
            nanosecond_delta = current_time_ns - self.start_time_ns
            microsecond_delta: int = floor(nanosecond_delta / NANOSECONDS_PER_MICROSECOND)
            beat_count: int = ceil(microsecond_delta / MICROSECONDS_PER_BEAT)
            sleep_seconds = MICROSECONDS_PER_BEAT / MICROSECONDS_PER_SECOND / sequences_per_beat
            logging.debug(f"sleep {self.channel} {sleep_seconds}")
            while True:
                for i in range(0, self.get_sequence_length()):
                    for key, value in self.sequences.items():
                        note = value[i]
                        logging.debug(f"note {i} {note}")
                        if note and not self.mute:
                            send_function(note)
                    sleep(sleep_seconds)

        self.playing_thread = Thread(target=_target)
        self.playing_thread.daemon = True
        self.playing_thread.start()

    def fill_note(self, beat_count, note, velocity=127):
        if note not in self.sequences:
            logging.error(f"making {note} {self.channel}")
            self.last_note = note
            self.create_sequence()
        self.sequences[note][beat_count] = Message(type='note_on', channel=self.channel, note=note, time=0,
                                                   velocity=velocity)

    def make_sequence(self):
        sequence: List[Optional[Message]] = [None, ] * (
                self.number_bars_in_sequence * self.beats_per_measure * self.sequences_per_beat)
        return sequence

    def get_sequence_length(self):
        return self.number_bars_in_sequence * self.beats_per_measure * self. \
            sequences_per_beat
