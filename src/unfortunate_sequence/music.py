import logging

from math import ceil, floor
from threading import Thread
from time import sleep, time_ns
from typing import List, Optional

from mido import Message
from random import choice
from pygame.sprite import Group
from pygame_menu import Menu
from pygame_menu.themes import THEME_BLUE, THEME_DARK, THEME_DEFAULT, THEME_GREEN, THEME_ORANGE, THEME_SOLARIZED
from pygame_menu.widgets import Button

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000


def display_sequence(sequence: List[Optional[Message]], beats_per_measure, number_bars_in_sequence, sequences_per_beat):
    string = "".join([f"{i :<4}" for i in range(1, 1 + number_bars_in_sequence)]) + "\n"
    for index, item in enumerate(sequence, start=1):
        string += f"{item.note if item else '_' :<4}"

        if index % (sequences_per_beat * beats_per_measure) == 0:
            string += "\n"
    return string


class BeatButton(object):
    def click(self):
        logging.debug("click!")

    def __init__(self, widget: Button, track_number):
        widget.set_onchange(self.click)


class Track:
    def __init__(self, number_bars_in_sequence, beats_per_measure, sequences_per_beat, MICROSECONDS_PER_BEAT,
                 MICROSECONDS_PER_SECOND, NANOSECONDS_PER_MICROSECOND, port_out, channel):
        self.channel = channel
        self.sequence: List[Optional[Message]] = [None, ] * (
                number_bars_in_sequence * beats_per_measure * sequences_per_beat)
        self.start_time_ns = time_ns()
        self.sprites = Group()
        self.menu = Menu(title=f"channel {channel} - vibe responsibly", width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                         theme=choice(
                             (THEME_BLUE, THEME_DARK, THEME_DEFAULT, THEME_GREEN, THEME_ORANGE, THEME_SOLARIZED)))
        for index in range(1, 1 + len(self.sequence)):
            self.menu.add.button(f"{index}", None)

        # i vape indoors
        swag = {int(widget._title): BeatButton(widget=widget, track_number=int(widget._title)) for widget in self.menu.get_widgets()}

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
