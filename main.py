from time import sleep
from typing import Optional

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


def set_settings() -> None:
    pass


def parse_key(event) -> Optional[int]:
    print(event.__dict__)
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
        return translation[event.key]
    except:
        return None


def main():
    global sprites

    sprites = pygame.sprite.Group()

    BEATS_PER_MINUTE = 60
    SECONDS_PER_MINUTE = 60
    TIMEDELTA_PER_BEAT = BEATS_PER_MINUTE / SECONDS_PER_MINUTE

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
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                note = parse_key(event)
                if note:
                    port_out.send(Message(type='note_on', channel=0, note=note, time=0))
                    # sleep(1)
                    # port_out.send(Message(type='note_off', channel=0, note=note, time=0))
        sprites.draw(screen)
        sprites.update()
        pygame.display.flip()
        clock.tick()


if __name__ == "__main__":
    main()
