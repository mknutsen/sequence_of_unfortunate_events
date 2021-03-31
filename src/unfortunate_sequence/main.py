import logging
import math
from mido import Message, open_output

from time import time_ns
from typing import Optional

import sys
from random import choice, randint
import pygame

from datetime import datetime

from music import Button, display_sequence, Track, SCREEN_WIDTH, SCREEN_HEIGHT

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
record = False


def get_time_microsecond():
    dt = datetime.now()
    return dt.microsecond


start_time = datetime.now()

_HORIZONTAL_OFFSET = 0
_VERTICAL_OFFSET = 0
shift = 0
selected_track = None
tracks = None
velocity = 127
movement = (0,0,0)


def set_settings() -> None:
    pass


def parse_key(event) -> Optional[int]:
    global shift, selected_track, tracks, velocity, record, movement
    logging.info(event.__dict__)
    number = event.key - pygame.K_0
    logging.error(f"new track! {number} {pygame.K_0}")
    if 0 <= number <= 9:
        logging.error(f"new track! {number}")
        selected_track = tracks[number]

    if event.key == pygame.K_m:
        selected_track.toggle_mute()
    if event.key == pygame.K_r:
        record = not record
    if event.key == pygame.K_n:
        velocity += 15
    if event.key == pygame.K_b:
        velocity -= 15

    if event.key == pygame.K_z:
        shift += -1

    elif event.key == pygame.K_x:
        shift += 1
    try:
        translation = {pygame.K_a: 48,
                       pygame.K_w: 49,
                       pygame.K_s: 50,
                       pygame.K_e: 51,
                       pygame.K_d: 532,
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


def text_objects(text, font):
    black = (0, 0, 0)
    textSurface = font.render(text, True, black)
    return textSurface, textSurface.get_rect()


def message_display(text, screen, x, y):
    largeText = pygame.font.Font('freesansbold.ttf', 20)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.topleft = (x, y)
    screen.blit(TextSurf, TextRect)


def main():
    global selected_track, tracks, velocity, record
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    # port_in = open_input('USB MIDI Device')
    port_out = open_output('mio')
    # port_out.reset()

    MOVEMENT = 5

    pygame.init()

    # infoObject = pygame.display.Info()
    # SCREEN_WIDTH = infoObject.current_w
    # SCREEN_HEIGHT = infoObject.current_h

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
              range(1, 11)]
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Set the x, y postions of the mouse click
                (x, y) = event.pos
                for sprite in selected_track.sprites:
                    if not isinstance(sprite, Button):
                        logging.error(f"suspicious! {sprite.__dict__}")
                        continue
                    sprite.click(x=x, y=y)

            # loop over, quite pygamex
            elif event.type == pygame.KEYDOWN:
                note = parse_key(event)
                if note:
                    port_out.send(
                        Message(type='note_on', channel=selected_track.channel, note=note, time=0, velocity=velocity))
                    selected_track.last_note = note
                    if record:
                        sequence_index = beat_count % len(selected_track.sequence)
                        selected_track.fill_note(beat_count=sequence_index, note=note, velocity=velocity)
                        logging.error(
                            display_sequence(sequence=selected_track.sequence, beats_per_measure=beats_per_measure,
                                             number_bars_in_sequence=number_bars_in_sequence,
                                             sequences_per_beat=sequences_per_beat))

                logging.info(f"beat_count {beat_count} microsecond_delta {microsecond_delta}")

        screen.fill(selected_track.color)
        selected_track.sprites.draw(screen)
        selected_track.sprites.update()
        message_display(f"{selected_track.last_note} play ne", screen, 0, SCREEN_HEIGHT - 20)
        message_display("ROLLING" if record else "chill", screen, 0, SCREEN_HEIGHT - 40)
        message_display(f"Track {selected_track.channel}", screen, 0, SCREEN_HEIGHT - 60)
        message_display(f"Shift {shift}", screen, 0, SCREEN_HEIGHT - 80)
        message_display(f"Velocity {velocity}", screen, 0, SCREEN_HEIGHT - 100)
        if selected_track.mute:
            message_display(f"MUTED haha epic", screen, 0, SCREEN_HEIGHT - 200)
        pygame.display.flip()
        # selected_track.menu.mainloop(screen)
        clock.tick()


if __name__ == "__main__":
    main()
