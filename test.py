import string
import random

import pygame as pg

import pymunk
import pymunk.pygame_util
from pymunk import Vec2d

import helios

import asyncio

LASER_ON = False
LINE_WIDTH = 5

class Pong2():

    # config
    PADDLE_WIDTH=10
    PADDLE_HEIGHT=341 # screen height/2


    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((682, 682))
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()

        self.surface = pg.Surface((4095, 4095))
        self.surface.fill(pg.Color("white"))
        self.surface_rect = self.surface.get_rect()

        self.ratio_x = (self.screen_rect.width / self.surface_rect.width)
        self.ratio_y = (self.screen_rect.height / self.surface_rect.height)

        self.hover = False
        self.running = True

        # physics
        self.space = pymunk.Space()
        self.dt = 1.0 / 60.0
        self.physics_steps_per_frame = 1

        self.balls: List[pymunk.Circle] = []
        self.lines: List[pymunk.Segment] = []
        self.ticks_to_next_ball = 50

        body = pymunk.Body(mass=0, moment=0, body_type=pymunk.Body.STATIC)
        self.p1_paddle = pymunk.Segment(body, (self.PADDLE_WIDTH/2 + 15, 0 + 15), (self.PADDLE_WIDTH/2 + 15, 0 + self.PADDLE_HEIGHT), self.PADDLE_WIDTH)
        self.p1_paddle.elasticity = 0.95
        self.p1_paddle.friction = 0.9
        self.p1_paddle.color = (255, 0, 0, 255) # red

        self.space.add(body, self.p1_paddle)
        #self.p1_paddle.body.position += Vec2d(50,0)


    def process_events(self) -> None:

        # key events and mouse click events
        for event in pg.event.get():
            #print(event)
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
            elif event.type == pg.KEYDOWN and event.key == pg.key.key_code('S'):
                #self.p1_paddle.body.position += Vec2d(0,50)
                #pg.display.flip()
                self.p1_paddle.color = (0, 255, 0, 255) # green
                self.p1_paddle.body.position += Vec2d(0,100)
            elif event.type == pg.KEYDOWN and event.key == pg.key.key_code('I'):
                for s in self.space.shapes:
                    print(s.body.position)
                    print(s.color)
  

    def update_screen(self) -> None:
        self.scaled_surface = pg.transform.scale(self.surface, self.screen_rect.size)
        self.screen.blit(self.scaled_surface, (0, 0))

        self.space.debug_draw( pymunk.pygame_util.DrawOptions(self.screen) )

        # update display
        pg.display.flip()
        pg.display.update()


    def run(self):
        while self.running:

            # progress time forward
            for x in range(self.physics_steps_per_frame):
                self.space.step(self.dt)

            self.process_events()
            self.update_screen()

            self.clock.tick(60)


    def quit(self):
        pg.quit()


def main():
    game = Pong2()
    game.run()
    game.quit()

    if LASER_ON:
        helios.close()
    

if __name__ == "__main__":
    main()