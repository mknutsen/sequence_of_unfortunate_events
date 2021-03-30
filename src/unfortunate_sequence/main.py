import logging
import math
from mido import Message, open_output

from time import time_ns
from typing import Optional

import sys

import pygame

from datetime import datetime

from music import display_sequence, Track

beats_per_measure = 4
number_bars_in_sequence = 1
sequences_per_beat = 4
BEATS_PER_MINUTE = 60
MICROSECONDS_PER_MINUTE = 60000000
SECONDS_PER_MINUTE = 60
MICROSECONDS_PER_SECOND = 1000000
MICROSECONDS_PER_BEAT = MICROSECONDS_PER_MINUTE / BEATS_PER_MINUTE
MICROSECONDS_PER_BAR = MICROSECONDS_PER_BEAT * beats_per_measure
NANOSECONDS_PER_MICROSECOND = 1000
TIME_THRESHOLD = MICROSECONDS_PER_MINUTE / SECONDS_PER_MINUTE


def get_time_microsecond():
    dt = datetime.now()
    return dt.microsecond


start_time = datetime.now()

_HORIZONTAL_OFFSET = 0
_VERTICAL_OFFSET = 0
shift = 0
selected_track = None
tracks = None


def set_settings() -> None:
    pass


def parse_key(event) -> Optional[int]:
    global shift, selected_track, tracks
    logging.info(event.__dict__)
    number = event.key - pygame.K_9
    if 0 <= number <= 9:
        selected_track = tracks[number]

    if event.key == pygame.K_z:
        shift += -1

    elif event.key == pygame.K_x:
        shift += 1
    try:
        translation = {pygame.K_a: 48,
                       pygame.K_w: 49,
                       pygame.K_s: 50,
                       pygame.K_e: 51,
                       pygame.K_d: 52,
                       pygame.K_f: 53,
                       pygame.K_t: 54,
                       pygame.K_g: 55,
                       pygame.K_y: 56,
                       pygame.K_h: 57,
                       pygame.K_u: 58,
                       pygame.K_j: 59, }
        return translation[event.key] + shift * 12
    except:
        return None


def main():
    global selected_track, tracks
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    # port_in = open_input('USB MIDI Device')
    port_out = open_output('mio')
    # port_out.reset()

    MOVEMENT = 5

    pygame.init()

    # infoObject = pygame.display.Info()
    # SCREEN_WIDTH = infoObject.current_w
    # SCREEN_HEIGHT = infoObject.current_h

    SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000

    # sprite_list_name = [Shape() for _ in range(0, 1)]
    set_settings()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1000, 1000))
    start_time_ns = time_ns()
    count = 0

    tracks = [Track(number_bars_in_sequence=number_bars_in_sequence, beats_per_measure=beats_per_measure,
                    MICROSECONDS_PER_BEAT=MICROSECONDS_PER_BEAT, MICROSECONDS_PER_SECOND=MICROSECONDS_PER_SECOND,
                    NANOSECONDS_PER_MICROSECOND=NANOSECONDS_PER_MICROSECOND,
                    port_out=port_out, sequences_per_beat=sequences_per_beat, channel=i) for i in
              range(0, 10)]
    selected_track = tracks[0]
    while True:
        current_time_ns = time_ns()
        nanosecond_delta = current_time_ns - start_time_ns
        microsecond_delta: int = math.floor(nanosecond_delta / NANOSECONDS_PER_MICROSECOND)
        beat_count: int = math.floor(microsecond_delta / MICROSECONDS_PER_BEAT)
        for event in pygame.event.get():
            logging.debug(f"{event.__dict__}")
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                note = parse_key(event)
                if note:
                    port_out.send(Message(type='note_on', channel=0, note=note, time=0))

                    sequence_index = beat_count % len(selected_track.sequence)
                    selected_track.sequence[sequence_index] = Message(type='note_on', channel=0, note=note, time=0)
                    logging.error(
                        display_sequence(sequence=selected_track.sequence, beats_per_measure=beats_per_measure,
                                         number_bars_in_sequence=number_bars_in_sequence,
                                         sequences_per_beat=sequences_per_beat))

                logging.info(f"beat_count {beat_count} microsecond_delta {microsecond_delta}")

        selected_track.sprites.draw(screen)
        selected_track.sprites.update()
        pygame.display.flip()
        clock.tick()


if __name__ == "__main__":
    main()
