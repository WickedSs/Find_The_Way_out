import os, sys, pygame, random, uuid, operator, math, numpy
from tkinter import HORIZONTAL
from Entities.Item import Item
from Entities.Particles import Ball_Explosion
from Settings import *


ROOT = os.path.dirname(sys.modules['__main__'].__file__)
DECORATIONS_FOLDER = "Assets\Decorations"


class Ball(Item):
    def __init__(self, width, height, animate, scale, side=None, x=0, y=0, scalex=2, scaley=2):
        super().__init__(width, height, animate, scale, side, x, y, scalex, scaley)
        self.asset_name = "Ball"
        self.animation_type = "Single"
        self.status = "Idle"
        self.shoot_speed = 20
        self.path = os.path.join(DECORATIONS_FOLDER, self.asset_name)
        self.multiple_animations()
        self.get_frame()
        self.exploision = Ball_Explosion("default", 53, 60)
        self.collided, self.effect_taken, self.got_hit = False, False, False

    def launch(self, collision, player):
        self.rect.x -= self.shoot_speed
        if self.rect.colliderect(player.rect):
            self.shoot_speed, self.hide_image = 0, True
            self.player_effect(player)
            self.collided = True
            self.exploision.rect.x, self.exploision.rect.y = player.rect.left - ROOM_OFFSET_X * 64, player.rect.bottom - ROOM_OFFSET_Y * 160
        
        for sprite in collision.sprites():
            if self.rect.colliderect(sprite.rect):
                self.shoot_speed, self.hide_image = 0, True
                self.collided = True
                self.player_effect(player)
                self.exploision.rect.x, self.exploision.rect.y = sprite.rect.x + sprite.rect.w / 2 - 58, sprite.rect.y + sprite.rect.h / 2 - 105
                
        if self.collided and not self.got_hit:
            if abs(player.rect.right - self.rect.left) <= 10:
                player.hit_blow = tuple(map(operator.mul, player.hit_blow, (-1, 1)))
                player.hit_blow_inc = tuple(map(operator.mul, player.hit_blow_inc, (-1, 1)))
                player.hit, self.got_hit = True, True
        
        if self.got_hit:
            finished = self.exploision.play_animation_once()
            print("Effect:", finished, self.exploision.animation_index)
            if finished:
                self.got_hit = False
                self.kill()
                
    def player_effect(self, player):
        if player.health > 0 and not self.effect_taken:
            if player.health >= 50:
                player.health -= 50
            else:
                player.health = 0
            self.effect_taken = True

class Cannon(Item):
    def __init__(self, width, height, animate, scale, side, x, y):
        super().__init__(width, height, animate, scale, side, x, y)
        self.display_surface = pygame.display.get_surface()
        self.asset_name = "Cannon"
        self.animation_type = "Multiple"
        self.status = "Idle"
        self.path = os.path.join(DECORATIONS_FOLDER, self.asset_name)
        self.multiple_animations()
        self.get_frame()
        self.debug, self.balls_group = False, pygame.sprite.Group()
        self.circle_pos, self.circle_radius = ((self.rect.x + self.rect.width/2), (self.rect.y + self.rect.height / 2)), 400
        self.delay = pygame.time.get_ticks()
        self.trigger_ball = False


    def points_in_circle_np(self, radius, x0=0, y0=0):
        top_half = y0 >= self.circle_pos[1] - radius and y0 <= self.circle_pos[1]
        left_half = (x0 >= self.circle_pos[0] - radius and x0 <= self.circle_pos[0]) 
        right_half = x0 >= self.circle_pos[0] and x0 <= self.circle_pos[0] + self.circle_radius
        if (left_half or right_half) and top_half:
            return True
        
        self.animation_index = 0
        return False

    def on_collision(self, player, item_list, Level, collision_sprites):
        if self.points_in_circle_np(self.circle_radius, player.rect.x, player.rect.y):
            self.status = "Fire"
            self.working_animation = self.animations[self.status]
            self.shoot()

        for sprite in self.balls_group.sprites():
            sprite.launch(collision_sprites, player)
            sprite.draw()

    def debug_draw(self):
        pygame.draw.circle(self.display_surface, (0, 255, 0), self.circle_pos, self.circle_radius, 2)
        # pygame.draw.arc(self.display_surface, (0, 255, 0), [(self.rect.x + self.rect.width/2), (self.rect.y + self.rect.height / 2), 50, 50], 0, math.pi, 2)

    def shoot(self):
        if (pygame.time.get_ticks() - self.delay) / 1000 >= 0.5:
            self.animation_index += 0.12
            if self.animation_index > 4.00 and self.animation_index < 4.15:
                self.trigger_ball = True

            if self.animation_index >= len(self.working_animation):
                self.delay = pygame.time.get_ticks()
                self.animation_index = 0
            
            self.get_frame()
        
        if self.trigger_ball:
            self.balls_group.add(Ball(15, 15, False, True, None, self.rect.x - 58, self.rect.y - 105))
            self.trigger_ball = False
            print("New Ball Group:", self.balls_group)

class Candle:
    def __init__(self):
        pass
    

class Chains:
    def __init__(self, x, y):
        pass


class Door(Item):
    def __init__(self, width, height, animate, scale, side, x, y):
        super().__init__(width, height, animate, scale, side, x, y)
        self.id = str(uuid.uuid4()).split("-")[0]
        self.asset_name = "Door"
        self.animation_type = "Multiple"
        self.animations = {}
        self.animation_index = 0
        self.status = "Opening"
        self.delay = None
        self.destinations = None
        self.next_destination, self.destination_door, self.destination_room, self.next_phases = None, None, None, [False, False, False]
        self.shift_distance_x, self.shift_distance_y = 0, 0
        self.open, self.action, self.played, self.shift, self.slight_delay = False, False, 0, False, -1
        self.path = os.path.join(DECORATIONS_FOLDER, self.asset_name)
        self.multiple_animations()
        self.get_frame()

    def set_room_coords(self, room, door):
        self.room_coords = room
        self.door_coords = door

    def set_destination(self, destination):
        self.destination = destination
        # print("Door: ", self.id, [filt.id for filt in self.destination])

    def on_collision(self, player, items_list, level, collision_sprites):
        if player.rect.colliderect(self.rect) and not self.open and not self.action:
            self.action = player.trigger_floating_text("[E]", self.rect.x + self.rect.w / 3, self.rect.y)
            if self.action:
                self.open = True
            
        if self.open and self.action and self.played == 0:
            self.status = "Opening"
            status = self.play_animation_once()
            player.disable_movement = True
            if status:
                # player.overlay.dim_screen_counter = 0
                # player.overlay.dim_screen_bool = status
                player.hide_player = True
                self.slight_delay = pygame.time.get_ticks()
                self.open = self.action = player.E_Action = False
                self.played = 1
        
        if self.destination and self.slight_delay != -1:
            if (pygame.time.get_ticks() - self.slight_delay) / 1000 >= 2:
                self.next_destination = random.choice(self.destination)
                self.destination_room = self.next_destination.room_coords
                self.destination_door = self.next_destination.door_coords
                if self.next_destination.rect.x - self.rect.x > 0:
                    self.offset_x = -self.destination_room[0]
                    self.offset_y = -self.destination_room[1]
                else:
                    self.offset_x = self.destination_room[0]
                    self.offset_y = self.destination_room[1]
                
                sign_x = self.offset_x / -self.offset_x if self.offset_x != 0 else 0
                sign_y = self.offset_y / -self.offset_y if self.offset_y != 0 else 0
                player.level.camera.shift_to = self.destination_room
                player.level.camera.set_increment((sign_x, sign_y))
                player.level.camera.is_shifting = True
                self.status = "Closing"
                self.play_animation_once()
                self.next_phases[0] = True
                self.slight_delay = -1
                    
                        
        
        if self.next_phases[0]:
            self.next_destination.status = "Opening"
            status = self.next_destination.play_animation_once()
            if status:
                self.next_phases[0] = False
                self.next_phases[1] = True
                self.next_destination.animation_index = 0
                print("Broke of first!")
        
        if self.next_phases[1]:
            self.next_destination.status = "Closing"
            status = self.next_destination.play_animation_once()
            if status:
                self.next_phases[1] = False
                self.next_phases[2] = True
                print("Broke of second")
        
        if self.next_phases[2]:
            player.rect.x, player.rect.y = (self.destination_door[0] + ROOM_OFFSET_X) * SCALE_SIZE, (self.destination_door[1] + ROOM_OFFSET_Y + 1) * SCALE_SIZE
            player.hide_player = False
            player.disable_movement = False
            self.played = 0
            self.next_phases = [False, False, False]
            self.slight_delay = -1
            self.get_frame()        
            self.next_phases = [False, False, False]
            print("Broke of third")
                    
    def play_animation_once(self):
        self.animation_index += 0.12
        if self.animation_index >= len(self.working_animation):
            self.animation_index = 0
            return True
        else:
            self.get_frame()
            self.display_surface.blit(self.image, self.rect)
            return False


class Window:
    def __init__(self):
        pass


class Barrel_UP:
    def __init__(self):
        pass


class Barrel_Down:
    def __init__(self):
        pass
    

class Bottle_UP_1:
    def __init__(self):
        pass
    

class Bottle_UP_2:
    def __init__(self):
        pass
    

class Bottle_Down_1:
    def __init__(self):
        pass
    

class Bottle_Down_2:
    def __init__(self):
        pass