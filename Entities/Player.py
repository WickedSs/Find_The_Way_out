
from Core.Characters import Characters
from Settings import *
import os, sys, pygame, random
from PIL import Image
import numpy as np
from Entities.Particles import Particles


ROOT = os.path.dirname(sys.modules['__main__'].__file__)
CHARACTER_FOLDER = "Assets\Characters"
PARTICLES_FOLDER = "Assets\Particles"


class NetworkPlayer:
    def __init__(self, x, y, direction, width, height, selected_animation, flipped, player_id):
        self.character = 0
        self.x, self.y = x, y
        self.direction = direction
        self.selected_animation = selected_animation
        self.flipped = flipped
        self.width, self.height, = width, height
        self.player_id = player_id        

class Player:
    def __init__(self, overlay, level, x, y):
        self.display_surface = pygame.display.get_surface()
        self.characters = Characters()
        self.x, self.y = x, y
        self.overlay = overlay
        self.level = level
        self.playerID = None
        self.player_name = "Gwynbleidd"

        # Objects
        self.character = self.characters.characters[0]
        self.particle = Particles(self.character.character_name)
        
        # paramaters
        self.health, self.max_health = 100, 100
        self.mana, self.max_mana = 60, 60
        self.speed = PLAYER_SPEED
        self.jumpForce = -12
        self.dash_distance = 50
        self.gravity = 0.8
        self.collision_tolorance = 2
        self.direction = pygame.math.Vector2(0, 0)
        self.selected_animation, self.selected_particle = 0, 0
        self.animation_index, self.particles_index = 0, 0
        self.player_fov, self.player_hiddenarea = 80, 1000
        self.previous_block_position = -1
        
        # dash paramaters
        self.dash_speed = 150
        self.dash_time = 1
        self.dash_bool = False
        self.time_between_dahses = 0
        self.dash_masks = []
        
        # booleans
        self.disable_movement = False
        self.hide_player = False
        self.flipped = False
        self.jumped = False
        self.on_ground = False
        self.blocked = False
        self.falling = False
        self.E_Action, self.floating_text = False, False
        self.killed = False

        self.particles_names = self.particle.particle_folders
        self.particle_folder = self.particles_names[self.selected_particle]
        self.current_particle = self.particle.particles[self.particle_folder]["frames"][0]
        self.particles_path = os.path.join(ROOT, PARTICLES_FOLDER, self.character.character_name)

        self.animations_names = self.character.animations_folders
        self.selected_folder = self.animations_names[self.selected_animation]
        self.current_animation = self.character.animations[self.selected_folder]["frames"][0]
        self.frames_path = os.path.join(ROOT, CHARACTER_FOLDER, self.character.character_name)
        
        # player data
        self.player_portrait_name = self.character.animations[self.selected_folder]["frames"][0]
        self.player_portrait = pygame.image.load(os.path.join(self.frames_path, self.selected_folder, "cropped", self.current_animation))
        self.player_portrait = pygame.transform.scale(self.player_portrait, (self.player_portrait.get_rect().w * 1.2, self.player_portrait.get_rect().h * 1.2))
        self.collected_maps = 0
        
        self.image = pygame.image.load(os.path.join(self.frames_path, self.selected_folder, "cropped", self.current_animation))
        old_rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (old_rect.w * 2, old_rect.h * 2))
        self.normal_image = self.image
        self.flipped_image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = self.x, self.y
        self.center_circle = [self.rect.x + self.rect.w / 2, self.rect.y + self.rect.h / 2]

    def set_playerID(self, playerID):
        self.playerID = playerID

    def isInside(self, circle, rad, x, y):
        if ((x - circle[0]) * (x - circle[0]) +
            (y - circle[1]) * (y - circle[1]) <= rad * rad):
            return True;
        else:
            return False;

    def player_update(self, network_player):
        network_player.x, network_player.y = self.rect.x, self.rect.y
        network_player.direction = (self.direction.x, self.direction.y)
        network_player.selected_animation = self.selected_animation
        return network_player

    def repetitive_bullshit_character(self):
        old_rect = self.rect.copy()
        self.image = pygame.image.load(os.path.join(self.frames_path, self.selected_folder, "cropped", self.current_animation[int(self.animation_index)]))
        self.image = pygame.transform.scale(self.image, (old_rect.width, old_rect.height))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = old_rect.x, old_rect.y
        self.normal_image = self.image
        self.flipped_image = pygame.transform.flip(self.image, True, False)
    
    def repetitive_bullshit_particle(self):
        frame_path = os.path.join(self.particles_path, self.particle_folder, "cropped", self.particle.particles[self.particle_folder]["frames"][int(self.particles_index)])
        self.particle_image = pygame.image.load(frame_path)
        self.particles_rect = self.particle_image.get_rect()
        self.particle_image = pygame.transform.scale(self.particle_image, (self.particles_rect.width * 2, self.particles_rect.height * 2))
        self.particles_rect = self.particle_image.get_rect()
        self.normal_particle_image = self.particle_image
        self.flipped_particles_image = pygame.transform.flip(self.particle_image, True, False)
        
        if self.flipped:
            self.particles_rect.x, self.particles_rect.y = self.rect.right - 8, self.rect.bottom - 15
            self.display_surface.blit(self.flipped_particles_image, self.particles_rect)
        else:
            self.particles_rect.x, self.particles_rect.y = self.rect.left - 20, self.rect.bottom - 15
            self.display_surface.blit(self.normal_particle_image, self.particles_rect)

    def draw_run_particles(self):
        self.particles_index += 0.12
        if self.particles_index >= len(self.particle.particles[self.particle_folder]["frames"]):
            self.particles_index = 0
        self.repetitive_bullshit_particle()


    def input(self):
        if not self.disable_movement:
            keys_pressed = pygame.key.get_pressed()
            if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_q]:
                self.direction.x = -1
                self.flipped = True
            elif keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
                self.direction.x = 1
                self.flipped = False
            else:
                self.direction.x = 0
                
                
            # if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_z]:
            #     self.direction.y = -1
            # elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            #     self.direction.y = 1
            # else:
            #     self.direction.y = 0

            if keys_pressed[pygame.K_SPACE]:
                # if not self.jumped and not self.falling:
                self.on_ground = False
                self.jump()

            if keys_pressed[pygame.K_f]:
                if self.player_fov <= 80 * 2:
                    self.player_fov += 5
                    
            if keys_pressed[pygame.K_e] and self.floating_text:
                self.E_Action = True
                
            if keys_pressed[pygame.K_LSHIFT]:
                if not self.dash_bool and self.mana >= 20 and self.time_between_dahses == 0:
                    self.dash_bool = True
                    self.mana -= 20
                    self.time_between_dahses = 3
                    
            if keys_pressed[pygame.K_v]:
                damage_taken = random.randrange(0, 20)
                if self.health < damage_taken:
                    damage_taken = self.health
                
                self.take_damage(damage_taken)
                

    def animate(self):
        self.animation_index += 0.12
        if self.animation_index >= len(self.character.animations[self.selected_folder]["frames"]):
            self.animation_index = 0
        
        self.repetitive_bullshit_character()
        self.mask = pygame.mask.from_surface(self.image)

        if self.flipped:
            self.image = self.flipped_image
        else:
            self.image = self.normal_image

  
    def horizontal_collision(self, collision_sprites):
        self.rect.x += self.direction.x * self.speed
        # self.rect.y += self.direction.y * self.speed
        if self.previous_block_position != -1 and self.rect.x != self.previous_block_position:
            self.blocked = False
            self.previous_block_position = -1

        for sprite in collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if self.direction.x < 0:
                    self.rect.left = sprite.rect.right
                    self.blocked = True
                    self.previous_block_position = self.rect.x
                elif self.direction.x > 0:
                    self.rect.right = sprite.rect.left
                    self.blocked = True
                    self.previous_block_position = self.rect.x
              
    def vertical_collision(self, collision_sprites):
        self.apply_gravity()
        for sprite in collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if self.direction.y > 0:
                    self.rect.bottom = sprite.rect.top
                    self.direction.y = 0
                    self.on_ground = True
                    self.jumped = False
                    self.falling = False
                elif self.direction.y < 0:
                    self.rect.top = sprite.rect.bottom
                    self.direction.y = 0
                    self.falling = False

    def take_damage(self, amount):
        self.health -= amount

    def dash(self):
        start_dash_position = self.rect.copy()
        end_dash_position = self.rect.x + self.dash_speed
        direction = -1 if self.flipped else 1
        colors= [(202, 240, 248), (173, 232, 244), (144, 224, 239), (72, 202, 228), (0, 180, 216)]
        start_positions = [(20*direction), 0, (40*direction), (60* direction), (70* direction), (80* direction)]
        for i in range(len(colors)):
            pygame.draw.rect(self.display_surface, colors[0], (start_dash_position.x - start_positions[i], start_dash_position.y + (i * 10), end_dash_position - start_dash_position.x, 10))
            
            if self.flipped:
                start_dash_position.x -= self.dash_speed / len(colors)
            else:
                start_dash_position.x += self.dash_speed / len(colors)
            
        direction = -1 if self.flipped else 1
        self.rect.x += self.dash_speed * direction
        # self.level.dash_scroll()
        self.dash_bool = False

    def focus_player(self):
        return

    def jump(self):
        self.direction.y = self.jumpForce
        self.jumped = True
        
    def apply_gravity(self):
        self.direction.y += self.gravity
        self.rect.y += self.direction.y

    def get_animation(self):
        if self.direction.y < 0:
            self.selected_animation = 2
        elif self.direction.y > 1:
            self.falling = True
            self.selected_animation = 3
        else:
            if self.direction.x != 0:
                self.selected_animation = 1
            else:
                self.selected_animation = 0
        
        self.selected_folder = self.animations_names[self.selected_animation]
        self.current_animation = self.character.animations[self.selected_folder]["frames"]
    
    def field_of_view(self, screen):
        self.fov_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.fill_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(self.fill_surface, (0, 0, 0), self.center_circle, self.player_fov)
        pygame.draw.circle(self.fov_surface, (0, 0, 0), self.center_circle, self.player_hiddenarea)
        self.fov_surface.blit(self.fill_surface, (0, 0), special_flags = pygame.BLEND_RGBA_SUB)
        screen.blit(self.fov_surface, (0, 0))

    def dim_screen(self, screen):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
        dim.set_alpha(128)
        dim.fill((0, 0, 0))
        screen.blit(dim, (0, 0))

    def draw(self, screen):
        # self.field_of_view(screen)
        if not self.killed:
            if not self.hide_player:
                screen.blit(self.image, self.rect)
            if not self.jumped and not self.falling and self.direction.x != 0:
                self.draw_run_particles()
        # self.dim_screen(screen)
        
    def trigger_floating_text(self, text, posx, posy):
        self.floating_text = True
        self.overlay.draw_text(text, posx, posy)
        if self.E_Action:
            self.floating_text = False
            return True
        
        return False

    def update(self, collision_sprites):
        self.center_circle = [self.rect.x + self.rect.w / 2, self.rect.y + self.rect.h / 2]
        if not self.hide_player:
            self.horizontal_collision(collision_sprites)
            self.vertical_collision(collision_sprites)
        self.input()
        self.get_animation()
        self.animate()
        
        if self.health <= 0:
            self.killed = False
        
        if self.dash_bool:
            self.dash()
            self.speed = PLAYER_SPEED
            self.dash_minus = pygame.time.get_ticks()
            
        if self.time_between_dahses > 0:
            self.time_between_dahses -= (pygame.time.get_ticks() - self.dash_minus) / 1000
            if self.time_between_dahses < 0:
                self.time_between_dahses = 0


