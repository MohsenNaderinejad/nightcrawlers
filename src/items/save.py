from src.utils import *
from src.entities.status import *
import random
import pygame
class Save_game:
    def __init__(self ,level):
        self.level = level
        self.dead_enemy_pos = []
        self.spawn_positions = []
        self.saves = []
        self.current_save_tile = None

    def add_save_pos(self ,save_pos):
        new_save = Save(save_pos,self.level)
        self.saves.append(new_save)

    def extract_items_position(self):
        self.spawn_positions = self.level.tilemap.extract_tile_by_pair([('save', 0)], keep=False)
        for save_pos in self.spawn_positions:
            save = Save(save_pos, self.level)
            self.saves.append(save)
    
    def clear(self):
        self.dead_enemy_pos = []
        self.spawn_positions = []
        self.saves = []
        self.current_save_tile = None

    def update(self):
        for save in self.saves:
            save.update()
            if save.check_save_point() and self.level.players[0].controller.movement['DMove']:
                # print("Save point reached")
                self.level.enemies.enemies_unsaved = self.level.enemies.enemies
                self.current_save_tile = save

    def render(self, surface, camera):
        for save in self.saves:
            save.render(surface, camera)

    def save_dead_enemies(self ,enemy_pos):
        self.dead_enemy_pos.append(enemy_pos)

class Save:
    def __init__(self, save_pos, level):
        self.level = level
        self.position = save_pos.position + Position(8, -32)
        self.animation = self.level.Game.effects['bonefire'].copy()

    def check_save_point(self):
        if self.rrect().colliderect(self.level.players[0].rect()):
            return True
        
    def update(self):
        self.animation.update()

    def rrect(self):
        img = self.animation.image()
        return pygame.rect.Rect(self.position.x, self.position.y, img.get_width(), img.get_height())

    def render(self, surface, camera):
        img = self.animation.image()
        surface.blit(img, (self.position.x - camera.render_scroll.x, self.position.y - camera.render_scroll.y))

