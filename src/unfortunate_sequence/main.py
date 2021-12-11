import logging
import math
from mido import Message, open_output

from time import time_ns
from typing import Optional

import sys
from random import choice, randint
import pygame

from datetime import datetime

from music import Button, display_sequence, MidiChannel, SCREEN_WIDTH, SCREEN_HEIGHT

beats_per_measure = 4
number_bars_in_sequence = 4
sequences_per_beat = 4
BEATS_PER_MINUTE = 110
MICROSECONDS_PER_MINUTE = 60000000
SECONDS_PER_MINUTE = 60
MICROSECONDS_PER_SECOND = 1000000
MICROSECONDS_PER_BEAT = MICROSECONDS_PER_MINUTE / BEATS_PER_MINUTE
MICROSECONDS_PER_BAR = MICROSECONDS_PER_BEAT * beats_per_measure
NANOSECONDS_PER_MICROSECOND = 1000
TIME_THRESHOLD = MICROSECONDS_PER_MINUTE / SECONDS_PER_MINUTE
record = False
port_out = open_output('mio')


def update_tempo(tempo):
    global BEATS_PER_MINUTE, MICROSECONDS_PER_BEAT, tracks
    BEATS_PER_MINUTE = tempo
    MICROSECONDS_PER_BEAT = MICROSECONDS_PER_MINUTE / BEATS_PER_MINUTE
    for track in tracks:
        track.set_bpm(beats_per_minute=BEATS_PER_MINUTE, sequences_per_beat=sequences_per_beat)


def get_time_microsecond():
    dt = datetime.now()
    return dt.microsecond


start_time = datetime.now()

_HORIZONTAL_OFFSET = 0
_VERTICAL_OFFSET = 0
shift = 0
selected_track = None
tracks = None
tempo = 127
movement = (0, 0, 0)


def set_settings() -> None:
    pass


def global_send(message: Message) -> None:
    try:
        port_out.send(message)
    except Exception as e:
        logging.error(message.__dict__)
        logging.error(str(e))


def parse_key(event) -> Optional[int]:
    global shift, selected_track, tracks, tempo, record, movement
    logging.info(event.__dict__)
    number = event.key - pygame.K_0
    # logging.error(f"new track! {number} {pygame.K_0}")
    if 0 <= number <= 9:
        logging.error(f"new track! {number}")
        selected_track = tracks[number]

    if event.key == pygame.K_COMMA:
        selected_track.modify_sequence_length(1 / 2)
    if event.key == pygame.K_PERIOD:
        selected_track.modify_sequence_length(2)

    if event.key == pygame.K_SEMICOLON:
        selected_track.modify_beats_per_sequence(1 / 2)
    if event.key == pygame.K_QUOTE:
        selected_track.modify_beats_per_sequence(2)

    if event.key == pygame.K_n:
        selected_track.create_sequence()
    if event.key == pygame.K_m:
        selected_track.toggle_mute()
    if event.key == pygame.K_r:
        record = not record
    if event.key == pygame.K_b:
        tempo += 5
        update_tempo(tempo)
    if event.key == pygame.K_v:
        tempo -= 5
        update_tempo(tempo)

    if event.key == pygame.K_z:
        shift += -1

    elif event.key == pygame.K_x:
        shift += 1
    try:
        translation = {pygame.K_a: 48,
                       pygame.K_w: 49,
                       pygame.K_s: 50,
                       pygame.K_e: 51,
                       pygame.K_d: 53,
                       pygame.K_f: 53,
                       pygame.K_t: 54,
                       pygame.K_g: 55,
                       pygame.K_y: 56,
                       pygame.K_h: 57,
                       pygame.K_u: 58,
                       pygame.K_j: 59, }
        value = translation[event.key] + shift * 12
        if value > 127:
            value = 127
        elif value < 0:
            value = 0
        return value
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
    global selected_track, tracks, tempo, record
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

    tracks = [
        MidiChannel(bpm=BEATS_PER_MINUTE, sequences_per_beat=sequences_per_beat, beats_per_measure=beats_per_measure,
                    sequence_length=(beats_per_measure * number_bars_in_sequence * sequences_per_beat),
                    send_function=global_send, channel=i) for i in
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
                for sprite in selected_track.get_sprites():
                    if not isinstance(sprite, Button):
                        logging.error(f"suspicious! {sprite.__dict__}")
                        continue
                    sprite.click(x=x, y=y)

            # loop over, quite pygamex
            elif event.type == pygame.KEYDOWN:
                note = parse_key(event)
                if note:
                    try:
                        global_send(
                            Message(type='note_on', channel=selected_track.channel, note=note, time=0, velocity=tempo))

                        selected_track.last_note = note
                        if record:
                            sequence_index = beat_count % selected_track.get_sequence_length()
                            selected_track.fill_note(beat_count=sequence_index, note=note, velocity=127)

                    except Exception as e:
                        logging.error(
                            f"type='note_on', channel={selected_track.channel}, note={note}, time=0, velocity={127}")
                        logging.error(str(e))
                logging.info(f"beat_count {beat_count} microsecond_delta {microsecond_delta}")

        screen.fill(selected_track.color)
        selected_track.get_sprites().draw(screen)
        selected_track.get_sprites().update()
        message_display(f"{selected_track.last_note} play ne", screen, 0, SCREEN_HEIGHT - 20)
        message_display("ROLLING" if record else "chill", screen, 0, SCREEN_HEIGHT - 40)
        message_display(f"Track {selected_track.channel}", screen, 0, SCREEN_HEIGHT - 60)
        message_display(f"Shift {shift}", screen, 0, SCREEN_HEIGHT - 80)
        message_display(f"Tempo {tempo}", screen, 0, SCREEN_HEIGHT - 100)
        if selected_track.mute:
            message_display(f"MUTED haha epic", screen, 0, SCREEN_HEIGHT - 200)
        pygame.display.flip()
        # selected_track.menu.mainloop(screen)
        clock.tick()


if __name__ == "__main__":
    main()
