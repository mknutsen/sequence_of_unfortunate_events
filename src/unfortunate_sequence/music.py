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

MICROSECONDS_PER_MINUTE = 60000000
MICROSECONDS_PER_SECOND = 1000000


def display_sequence(sequence: List[Optional[Message]], beats_per_measure, number_bars_in_sequence, sequences_per_beat):
    string = "".join([f"{i :<4}" for i in range(1, 1 + number_bars_in_sequence)]) + "\n"
    for index, item in enumerate(sequence, start=1):
        string += f"{item.note if item else '_' :<4}"

        if index % (sequences_per_beat * beats_per_measure) == 0:
            string += "\n"
    return string


class Button(Sprite):
    def __init__(self, x, y, width, height, index, note, channel):
        Sprite.__init__(self)
        self.image = Surface((width, height))
        print(index, "create", x, y, " - ", x + width, y + height)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.column_index = index
        self.note = note
        self.highlight = False
        self.message = None
        self.channel = channel

    def update(self) -> None:
        color = (255, 255, 255) if self.message is None else (0, 0, 0)
        color = (100, 100, 100) if self.highlight else color
        self.image.fill(color)

    def click(self, x, y):
        if self.rect.collidepoint(x, y):
            self.fill_note()

    def fill_note(self):
        self.message = Message(type='note_on', channel=self.channel, note=self.note, time=0,
                               velocity=127)

    def get_message(self) -> Optional[Message]:
        return self.message

    def togggle_highlight(self):
        self.highlight = not self.highlight


class Sequence:
    def __init__(self, note, sequences_per_beat, bpm, sequence_length, channel, beats_per_measure,
                 column_index):
        self.sequence: List[Optional[Button]] = [None, ] * sequence_length
        seq_len = len(self.sequence)
        self.note = note
        button_width = SCREEN_WIDTH / seq_len
        button_height = 50
        self.column_index = column_index
        self.sprites = Group()
        for index in range(0, floor(seq_len)):
            button = Button(x=index * button_width, y=2 * button_height * column_index, width=button_width,
                            height=button_height, note=note, index=index, channel=channel)
            self.sprites.add(button)
            self.sequence[index] = button


class MidiChannel:

    def create_sequence(self):
        note = self.last_note
        if note in self.sequences:
            return
        self.sequences[note] = Sequence(note, self.sequences_per_beat, 0, self.get_sequence_length(), self.channel,
                                        self.beats_per_measure, column_index=len(self.sequences))

    def toggle_mute(self):
        self.mute = not self.mute

    def set_bpm(self, beats_per_minute):
        self.MICROSECONDS_PER_BEAT = MICROSECONDS_PER_MINUTE / beats_per_minute
        self.calculate_sleep_seconds()

    def calculate_sleep_seconds(self):
        self.sleep_seconds = self.MICROSECONDS_PER_BEAT / MICROSECONDS_PER_SECOND / self.sequences_per_beat
        num_sequences = len(self.sequences)
        seq_len = self.get_sequence_length()
        button_width = SCREEN_WIDTH / seq_len
        button_height = 50

        for note, sequence in self.sequences.items():
            for beat in range(0, self.get_sequence_length()):
                try:
                    button = sequence.sequence[beat]
                except Exception as e:
                    logging.error(e)
                    logging.error(f"making new button {sequence.note} {beat} {sequence.column_index}")
                    button = Button(x=0, y=0, width=0, height=button_height, note=sequence.note,
                                    index=sequence.column_index, channel=self.channel)
                    sequence.sequence[beat] = button

                button.x = beat * button_width
                button.y = 2 * sequence.column_index * button_height
                button.image = Surface((button_width, button_height))
                button.rect = button.image.get_rect(topleft=(button.x, button.y))

    def modify_sequences_per_beat(self, modifier):
        self.sequences_per_beat *= modifier
        self.calculate_sleep_seconds()

    def modify_sequence_length(self, modifier):
        self.sequence_length *= modifier
        self.calculate_sleep_seconds()

    def get_sprites(self) -> Group:
        return Group([sprite for seq in self.sequences.values() for sprite in seq.sprites])

    def __init__(self, sequences_per_beat, bpm, sequence_length: int, channel, send_function, beats_per_measure):
        self.channel = channel
        self.mute = False
        self.color = (randint(0, 255), randint(0, 255), randint(0, 255))
        self.last_note = 50
        self.sequence_length: int = int(sequence_length)
        self.beats_per_measure = beats_per_measure
        self.sequences_per_beat = sequences_per_beat
        self.sequences: Dict[int, Sequence] = {}
        self.set_bpm(bpm)
        self.calculate_sleep_seconds()

        # self.create_sequence()
        def _target():
            logging.debug(f"sleep {self.channel} {self.sleep_seconds}")
            while True:
                for i in range(0, self.get_sequence_length()):
                    for key, value in self.sequences.items():
                        value.sequence[i].togggle_highlight()
                        note = value.sequence[i].get_message()
                        logging.debug(f"note {i} {note}")
                        if note and not self.mute:
                            send_function(note)
                    sleep(self.sleep_seconds)
                    for key, value in self.sequences.items():
                        value.sequence[i].highlight = False

        self.playing_thread = Thread(target=_target)
        self.playing_thread.daemon = True
        self.playing_thread.start()

    def fill_note(self, beat_count, note, velocity=127):
        if note not in self.sequences:
            logging.error(f"making {note} {self.channel}")
            self.last_note = note
            self.create_sequence()
        self.sequences[note].sequence[beat_count].fill_note()

    def make_sequence(self):
        sequence: List[Optional[Message]] = [None, ] * self.sequence_length
        return sequence

    def get_sequence_length(self) -> int:
        return int(self.sequence_length)
