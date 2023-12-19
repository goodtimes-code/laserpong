import string
import random

import pygame as pg

import pymunk
import pymunk.pygame_util
from pymunk import Vec2d

import helios

import asyncio

LASER_ON = True
LASER_INTENSITY = 2
LINE_WIDTH = 5

DIRECTION_UP = Vec2d(0,-50)
DIRECTION_DOWN = Vec2d(0,50)

class Pong2():

    # config
    PADDLE_WIDTH=10
    PADDLE_HEIGHT=50
    PADDLE_STEPS=50


    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((682, 682)) # display output dimension
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()

        self.surface = pg.Surface((4095, 4095)) # laser output dimension
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

        pg.joystick.init()
        self.joystick_count = pg.joystick.get_count()
        print('Joysticks found: ' + str(self.joystick_count))

        if self.joystick_count > 0:
            self.joystick1 = pg.joystick.Joystick(0)
            self.joystick2 = pg.joystick.Joystick(1)
            print('Joystick1, Buttons found: ' + str(self.joystick1.get_numbuttons()))
            print('Joystick2, Buttons found: ' + str(self.joystick2.get_numbuttons()))

        self.p1_paddle_body = pymunk.Body(100, 100, pymunk.Body.KINEMATIC) # mass, moment, body_tape
        self.p1_paddle_body.position = (self.PADDLE_WIDTH/2 + 15, 0 + 15)
        self.p1_paddle = pymunk.Segment(self.p1_paddle_body, (0,0), (0,self.PADDLE_HEIGHT), self.PADDLE_WIDTH)
        self.p1_paddle.elasticity = 0.95
        self.p1_paddle.friction = 0.9
        self.p1_paddle.color = (255, 0, 0, 255) # red
        self.space.add(self.p1_paddle_body, self.p1_paddle)

        self.p2_paddle_body = pymunk.Body(100, 100, pymunk.Body.KINEMATIC)
        self.p2_paddle_body.position = (self.screen_rect.width-30, 0 + 15)
        self.p2_paddle = pymunk.Segment(self.p2_paddle_body, (0,0), (0,self.PADDLE_HEIGHT), self.PADDLE_WIDTH)
        self.p2_paddle.elasticity = 0.95
        self.p2_paddle.friction = 0.9
        self.p2_paddle.color = (0, 255, 0, 255) # green
        self.space.add(self.p2_paddle_body, self.p2_paddle)

        #self.ball_origin_pos = [self.p1_paddle_body.position[0] + self.PADDLE_WIDTH, self.p1_paddle_body.position[1]]
        #self.scaled_ball_origin_pos = (self.ball_origin_pos[0] / self.ratio_x, self.ball_origin_pos[1] / self.ratio_y)
        self.ball_origin_steps = 25
        self.next_ball_for_player = 1
        self.ball_speed = 300

        space_collision_handler = self.space.add_collision_handler(0, 0)
        space_collision_handler.post_solve = self.space_handle_collision


    def space_handle_collision(self, arbiter, space, data):
        self.play_sound('pop')
        self.ball_speed += 15

        
    def add_static_line(self, from_x, from_y, to_x, to_y):
        static_line = pymunk.Segment(self.space.static_body, (from_x, from_y), (to_x, to_y), LINE_WIDTH)
        static_line.elasticity = 0.95
        static_line.friction = 0.9
        self.lines.append(static_line)
        self.space.add(static_line)


    def process_events(self) -> None:

        # mouse position
        self.mouse_pos = list(pg.mouse.get_pos())
        self.scaled_mouse_pos = (self.mouse_pos[0] / self.ratio_x, self.mouse_pos[1] / self.ratio_y)

        pg.event.pump()

        # key events and mouse click events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
            elif event.type == pg.KEYDOWN and event.key == pg.key.key_code('B'):
                self.remove_all_balls()
            elif event.type == pg.KEYDOWN and event.key == pg.key.key_code('L'):
                self.remove_all_lines()
            elif event.type == pg.KEYDOWN and event.key == pg.key.key_code('W'):
                self.move_paddle(self.p1_paddle, DIRECTION_UP)
            elif event.type == pg.KEYDOWN and event.key == pg.key.key_code('S'):
                self.move_paddle(self.p1_paddle, DIRECTION_DOWN)
            elif event.type == pg.KEYDOWN and event.key == pg.K_UP:
                self.move_paddle(self.p2_paddle, DIRECTION_UP)
            elif event.type == pg.KEYDOWN and event.key == pg.K_DOWN:
                self.move_paddle(self.p2_paddle, DIRECTION_DOWN)
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.tmp_mouse_from_x = self.mouse_pos[0]
                self.tmp_mouse_from_y = self.mouse_pos[1]
            elif event.type == pg.MOUSEBUTTONUP:
                self.add_static_line(self.tmp_mouse_from_x, self.tmp_mouse_from_y, self.mouse_pos[0], self.mouse_pos[1])
            elif event.type == pg.JOYBUTTONDOWN or (event.type == pg.KEYDOWN and event.key == pg.K_SPACE):
                if self.joystick_count > 0:
                    joystick1 = pg.joystick.Joystick(0) # without this, joystick stops working after some button presses
                    joystick2 = pg.joystick.Joystick(1)

                if len(self.balls) == 0:
                    self.create_ball()
            elif event.type == pg.JOYAXISMOTION:
                joystick_num = event.joy

                if event.axis == 0: # left/right
                    x_value = int(event.value * self.PADDLE_STEPS)

                    if len(self.balls) == 0:
                        if joystick_num == 0:
                            self.p1_paddle.body.position -= Vec2d(x_value,0)
                        else:
                            self.p2_paddle.body.position -= Vec2d(x_value,0)
                
                if event.axis == 1: # up/down
                    if event.value >= 1:
                        direction = DIRECTION_UP
                    elif event.value < -1:
                        direction = DIRECTION_DOWN
                    else:
                        direction = 0

                    if joystick_num == 0:
                        paddle = self.p1_paddle
                    else:
                        paddle = self.p2_paddle

                    if paddle and direction != 0:
                        self.move_paddle(paddle, direction)
                    

    def move_paddle(self, paddle, direction) -> None:
        if direction == DIRECTION_UP and paddle.body.position[1] > 15:
            paddle.body.position += DIRECTION_UP
        elif direction == DIRECTION_DOWN and ((paddle.body.position[1] + 2*self.PADDLE_HEIGHT + 15) < self.screen_rect.height ):
            paddle.body.position += DIRECTION_DOWN


    def update_screen(self) -> None:
        self.scaled_surface = pg.transform.scale(self.surface, self.screen_rect.size)
        self.screen.blit(self.scaled_surface, (0, 0))

        self.space.debug_draw( pymunk.pygame_util.DrawOptions(self.screen) )

        
        pg.draw.circle(self.screen, 'green', (self.mouse_pos[0], self.mouse_pos[1]), LINE_WIDTH)
        if LASER_ON:
            # draw mouse position (green point)
            helios.draw_point(self.scaled_mouse_pos[0], self.scaled_mouse_pos[1], 0, int(40*LASER_INTENSITY), 0)

            # blank
            helios.draw_line(self.scaled_mouse_pos[0], self.scaled_mouse_pos[1], self.p1_paddle_body.position[0] / self.ratio_x, (self.p1_paddle_body.position[1] + self.PADDLE_HEIGHT) / self.ratio_y, 0, 0, 0)

            # draw paddle player 1
            helios.draw_line(self.p1_paddle_body.position[0] / self.ratio_x, self.p1_paddle_body.position[1] / self.ratio_y, self.p1_paddle.body.position[0] / self.ratio_x, (self.p1_paddle_body.position[1] + self.PADDLE_HEIGHT) / self.ratio_y, int(50*LASER_INTENSITY), 0, 0)
            
            # blank
            helios.draw_line(self.p1_paddle.body.position[0] / self.ratio_x, (self.p1_paddle_body.position[1] + self.PADDLE_HEIGHT) / self.ratio_y, self.p2_paddle_body.position[0] / self.ratio_x, self.p2_paddle_body.position[1] / self.ratio_y, 0, 0, 0)

            # draw paddle player 2
            helios.draw_line(self.p2_paddle_body.position[0] / self.ratio_x, self.p2_paddle_body.position[1] / self.ratio_y, self.p2_paddle.body.position[0] / self.ratio_x, (self.p2_paddle_body.position[1] + self.PADDLE_HEIGHT) / self.ratio_y, 0, int(50*LASER_INTENSITY), 0)


        # update display
        pg.display.flip()

        
    def create_ball(self) -> None:

        if self.next_ball_for_player == 1:
            x_pos = self.p1_paddle_body.position[0] + (self.PADDLE_WIDTH + 30)
            y_pos = self.p1_paddle_body.position[1] + self.PADDLE_HEIGHT/2
            direction = 1
            self.next_ball_for_player = 2
        else: #player == 2
            x_pos = self.p2_paddle_body.position[0] - (self.PADDLE_WIDTH + 15)
            y_pos = self.p2_paddle_body.position[1] + self.PADDLE_HEIGHT/2
            direction = -1
            self.next_ball_for_player = 1

        mass = 15
        self.ball_radius = 10
        inertia = pymunk.moment_for_circle(mass, 0, self.ball_radius, (0, 0))
        body = pymunk.Body(mass, inertia)
        body.position = x_pos, y_pos
        shape = pymunk.Circle(body, self.ball_radius, (0, 0))
        shape.elasticity = 0.75
        shape.friction = 0

        direction = (self.surface_rect.width/2 * direction,200)
        body.apply_impulse_at_local_point(Vec2d(*direction))

        def constant_velocity(body, gravity, damping, dt):
            body.velocity = body.velocity.normalized() * self.ball_speed
        
        body.velocity_func = constant_velocity

        self.play_sound('new_ball')
        self.space.add(body, shape)
        self.balls.append(shape)


    def update_balls(self):
        # remove balls that fall out of screen bottom
        balls_to_remove = [ball for ball in self.balls if ball.body.position.y >= 670 or ball.body.position.x >= self.p2_paddle_body.position[0] or ball.body.position.x < self.p1_paddle_body.position[0] or ball.body.position.y < 0]
        for ball in balls_to_remove:
            self.space.remove(ball, ball.body)
            self.balls.remove(ball)

            self.play_sound('error')
            pg.time.wait(1000)
            self.ball_speed = 300
            self.create_ball()

        # draw ball (blue point)
        if LASER_ON:
            for ball in self.balls:
                helios.draw_circle(ball.body.position[0] / self.ratio_x, ball.body.position[1] / self.ratio_y, self.ball_radius / self.ratio_x, 0, 0, int(70*LASER_INTENSITY))


    def play_sound(self, filename):
        pg.mixer.music.load('sound/'+filename+'.wav')
        pg.mixer.music.play(0,0.0)


    def remove_all_balls(self):
        for ball in self.balls:
            self.space.remove(ball, ball.body)
            self.balls.remove(ball)


    def remove_all_lines(self):
        for line in self.lines:
            self.space.remove(line)
            self.lines.remove(line)


    def run(self):
        while self.running:

            # progress time forward
            for x in range(self.physics_steps_per_frame):
                self.space.step(self.dt)

            self.process_events()
            self.update_balls()
            self.update_screen()

            self.clock.tick(60)


    def quit(self):
        pg.quit()


def main():
    if LASER_ON:
        helios.initialize()

    game = Pong2()
    game.run()
    game.quit()

    if LASER_ON:
        helios.close()
    

if __name__ == "__main__":
    main()