import logging

from math import ceil, floor
from threading import Thread
from time import sleep, time_ns
from typing import List, Optional

from mido import Message
from random import choice

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
    def __init__(self, x, y, width, height, check_callback, index, click_callback):
        Sprite.__init__(self)
        self.image = Surface((width, height))
        print(index, "create", x, y, " - ", x + width, y + height)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.check_callback = check_callback
        self.index = index
        self.click_callback = click_callback

    def update(self) -> None:
        color = (255, 255, 255) if self.check_callback(self.index) else (0, 0, 0)
        self.image.fill(color)

    def click(self, x, y):
        if self.rect.collidepoint(x, y):
            print("pass", x, y, self.index)
            self.click_callback(self.index)


class Track:

    def create_sequence(self, _check, _click):
        seq_len = len(self.sequence)
        button_width = SCREEN_WIDTH / seq_len
        button_height = 50
        for index in range(0, floor(seq_len)):
            self.sprites.add(
                Button(x=index  * button_width, y=100, width=button_width, height=button_height,
                       check_callback=_check,
                       click_callback=_click, index=index))

    def __init__(self, number_bars_in_sequence, beats_per_measure, sequences_per_beat, MICROSECONDS_PER_BEAT,
                 MICROSECONDS_PER_SECOND, NANOSECONDS_PER_MICROSECOND, port_out, channel):
        self.channel = channel
        self.sequence: List[Optional[Message]] = [None, ] * (
                number_bars_in_sequence * beats_per_measure * sequences_per_beat)
        self.start_time_ns = time_ns()
        self.sprites = Group()

        def _clear(sequence_number):
            self.sequence[sequence_number] = None

        def _click(sequence_number):
            if _check(sequence_number):
                _clear(sequence_number)
            else:
                self.fill_note(beat_count=sequence_number, note=50)

        def _check(sequence_number) -> bool:
            return self.sequence[sequence_number] is not None

        self.create_sequence(_check=_check, _click=_click)

        def _target():
            current_time_ns = time_ns()
            nanosecond_delta = current_time_ns - self.start_time_ns
            microsecond_delta: int = floor(nanosecond_delta / NANOSECONDS_PER_MICROSECOND)
            beat_count: int = ceil(microsecond_delta / MICROSECONDS_PER_BEAT)
            sleep_seconds = MICROSECONDS_PER_BEAT / MICROSECONDS_PER_SECOND / sequences_per_beat
            logging.info(f"sleep {sleep_seconds}")
            while True:
                for i in range(0, len(self.sequence)):
                    note = self.sequence[i]
                    logging.debug(f"note {i} {note}")
                    if note:
                        port_out.send(note)
                    sleep(sleep_seconds)

        self.playing_thread = Thread(target=_target)
        self.playing_thread.daemon = True
        self.playing_thread.start()

    def fill_note(self, beat_count, note):
        self.sequence[beat_count] = Message(type='note_on', channel=self.channel, note=note, time=0, velocity=127)
