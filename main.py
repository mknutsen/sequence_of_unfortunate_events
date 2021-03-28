import math
from multiprocessing import Manager
from threading import Thread
from time import sleep, time, time_ns
from typing import List, Optional

import sys

import pygame
from mido import get_output_names, get_input_names, open_input, open_output, Message

from datetime import datetime


def get_time_microsecond():
    dt = datetime.now()
    return dt.microsecond


start_time = datetime.now()

#     for msg in port_in.iter_pending():
#         print("msg!!", msg)
#         if msg.type != "clock":
#             msglog.append({"msg": msg, "due": time.time() + echo_delay})
#         # else:
#         #     print("epic and base0 d")
#     # print("epic and based 1")
#     print("iter")
#     while len(msglog) > 0 and msglog[0]["due"] <= time.time():
#         # print("in here", len(msglog))
#         port_out.send(msglog.popleft()["msg"])
#     # print("epic and based")
#     time.sleep(1)

_HORIZONTAL_OFFSET = 0
_VERTICAL_OFFSET = 0
shift = 0


def set_settings() -> None:
    pass


def parse_key(event) -> Optional[int]:
    global shift
    print(event.__dict__)
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


def display_sequence(sequence: List[Optional[Message]], beats_per_measure, number_bars_in_sequence, sequences_per_beat):
    string = "".join([f"{i :<4}" for i in range(1, 1 + number_bars_in_sequence)]) + "\n"
    for index, item in enumerate(sequence, start=1):
        string += f"{item.note if item else '_' :<4}"

        if index % beats_per_measure == 0:
            string += "\n"

    print(string)


def main():
    global sprites

    sprites = pygame.sprite.Group()

    beats_per_measure = 4
    number_bars_in_sequence = 1
    sequences_per_beat = 1
    BEATS_PER_MINUTE = 60
    MICROSECONDS_PER_MINUTE = 60000000
    SECONDS_PER_MINUTE = 60
    MICROSECONDS_PER_SECOND = MICROSECONDS_PER_MINUTE * SECONDS_PER_MINUTE
    MICROSECONDS_PER_BEAT = MICROSECONDS_PER_MINUTE / BEATS_PER_MINUTE
    MICROSECONDS_PER_BAR = MICROSECONDS_PER_BEAT * beats_per_measure
    NANOSECONDS_PER_MICROSECOND = 1000
    TIME_THRESHOLD = MICROSECONDS_PER_MINUTE / SECONDS_PER_MINUTE

    # port_in = open_input('USB MIDI Device')
    port_out = open_output('mio')
    # port_out.reset()

    MOVEMENT = 5

    pygame.init()

    infoObject = pygame.display.Info()
    SCREEN_WIDTH = infoObject.current_w
    SCREEN_HEIGHT = infoObject.current_h

    # sprite_list_name = [Shape() for _ in range(0, 1)]
    set_settings()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1000, 1000))
    # screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    # print("framerate:", framerate)
    # print("tolerance:", _TOLERANCE)
    start_time_ns = time_ns()
    count = 0
    # with Manager() as manager:
    sequence: List[Optional[Message]] = [None, ] * number_bars_in_sequence * beats_per_measure * sequences_per_beat


    def _target():
        current_time_ns = time_ns()
        nanosecond_delta = current_time_ns - start_time_ns
        microsecond_delta: int = math.floor(nanosecond_delta / NANOSECONDS_PER_MICROSECOND)
        beat_count: int = math.ceil(microsecond_delta / MICROSECONDS_PER_BEAT)
        sequence_index = beat_count % len(sequence)
        while True:
            for i in range(0, len(sequence)):
                note = sequence[i]
                if note:
                    try:
                        print(f"note {i} {note}")
                        port_out.send(note)
                    except Exception as e:
                        print("failure", note)
                        print(e)
                sleep(1)
            print("hey! count")
            display_sequence(sequence=sequence, beats_per_measure=beats_per_measure,
                             number_bars_in_sequence=number_bars_in_sequence,
                             sequences_per_beat=sequences_per_beat)


    playing_thread = Thread(target=_target)
    playing_thread.daemon = True
    playing_thread.start()

    while True:
        current_time_ns = time_ns()
        nanosecond_delta = current_time_ns - start_time_ns
        microsecond_delta: int = math.floor(nanosecond_delta / NANOSECONDS_PER_MICROSECOND)
        beat_count: int = math.floor(microsecond_delta / MICROSECONDS_PER_BEAT)
        sequence_index = beat_count % len(sequence)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                note = parse_key(event)
                try:
                    sequence[sequence_index] = Message(type='note_on', channel=0, note=note, time=0)
                except Exception as e:
                    print(f"Invalid note: {note}\n {e}")
                print("beat_count", beat_count, "sequence_index", sequence_index, "microsecond_delta",
                      microsecond_delta)
                display_sequence(sequence=sequence, beats_per_measure=beats_per_measure,
                                 number_bars_in_sequence=number_bars_in_sequence,
                                 sequences_per_beat=sequences_per_beat)
        sprites.draw(screen)
        sprites.update()
        pygame.display.flip()
        clock.tick()

if __name__ == "__main__":
    main()
