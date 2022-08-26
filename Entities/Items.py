import os, sys, pygame
from Entities.Item import *
from Settings import *
from Entities.Particles import *

ROOT = os.path.dirname(sys.modules['__main__'].__file__)
ITEMS_FOLDER = "Assets\Items"





class Big_Map(Item):
    def __init__(self, width, height, animate, scale, x, y):
        super().__init__(width, height, animate, scale, x, y)
        self.display_surface = pygame.display.get_surface()
        self.asset_name = "Big_Map"
        self.animation_type = "Multiple"
        self.status = "Idle"
        self.path = os.path.join(ITEMS_FOLDER, self.asset_name)
        self.status_path = os.path.join(self.path, self.status)
        self.multiple_animations()
        self.working_animation = self.animations[self.status]
        self.out_particle = Big_Map_particle("Out", 19, 19)
        
    def on_pickup(self, player):
        if player.rect.colliderect(self.rect) and not self.hide_image:
            self.out_particle.set_position(self.rect.x, self.rect.y)
            self.hide_image = True

        if self.hide_image:
            self.disappear = self.out_particle.play_animation_once()
        
    def player_effect(self, player):
        player.collected_maps += 1
        return


class Chest(Item):
    def __init__(self, width, height, animate, scale, x, y):
        super().__init__(width, height, animate, scale, x, y)
        self.asset_name = "Chest"
        self.animation_type = "Multiple"
        self.status = "Idle"
        self.open = False
        self.path = os.path.join(ITEMS_FOLDER, self.asset_name)
        self.status_path = os.path.join(self.path, self.status)
        self.multiple_animations()
        self.working_animation = self.animations[self.status]
        self.possible_loot = [Big_Map(30, 31, True, True, 1 * SCALE_SIZE, 4 * SCALE_SIZE)]
        # self.big_map = Big_Map(30, 31, True, 1 * SCALE_SIZE, 4 * SCALE_SIZE)
        
    def on_pickup(self, player):
        if player.rect.colliderect(self.rect) and not self.open:
            action = player.trigger_floating_text("[E]", self.rect.x + self.rect.w / 2 - 10, self.rect.y - 40)
            if action:
                self.status = "Unlocked"
                self.open = True
        
        if self.open:
            self.unlock_chest(player)
    
    def unlock_chest(self, player):
        status = self.play_animation_once()
        if status:
            self.player_effect(player)
            self.open = False
            
    def player_effect(self, player):
        return

class Blue_Diamond(Item):
    def __init__(self):
        self.asset_name = "Blue_Diamond"
        self.animation_type = "Single"
        self.animations = {}
        self.animation_names = []
        self.path = os.path.join(ITEMS_FOLDER, self.asset_name)
        self.single_animations()
        self.working_animation = self.animations["frame"]
        
        
class Blue_Potion(Item):
    def __init__(self):
        pass


class Gold_Coin(Item):
    def __init__(self):
        pass


class Silver_Coin(Item):
    def __init__(self):
        pass

    
class Golden_Skull(Item):
    def __init__(self):
        pass


class Green_Bottle(Item):
    def __init__(self):
        pass


class Green_Diamond(Item):
    def __init__(self):
        pass


class Red_Diamond(Item):
    def __init__(self):
        pass
    

class Red_Postion(Item):
    def __init__(self):
        pass
