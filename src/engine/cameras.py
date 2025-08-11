import pygame, sys, pathlib, os
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *

# --------- CAMERA ---------
class Camera:
    def __init__(self):
        self.scroll = Position()
        self.render_scroll = Position()
        self.camera_speed = 2

    def update_by_target(self, target):
        self.scroll.x += (target.rect().centerx - (self.scroll.x + DISPLAY_SIZE[0] / 2)) / 10
        self.scroll.y += (target.rect().centery - (self.scroll.y + DISPLAY_SIZE[1] / 2)) / 10
        self.render_scroll.x = int(self.scroll.x)
        self.render_scroll.y = int(self.scroll.y)

    def update_by_controller(self, controller):
        self.scroll.x += (controller.movement['RMove'] - controller.movement['LMove']) * self.camera_speed
        self.scroll.y += (controller.movement['DMove'] - controller.movement['UMove']) * self.camera_speed
        self.render_scroll.x = int(self.scroll.x)
        self.render_scroll.y = int(self.scroll.y)

class CameraTarget:
    def __init__(self, position):
        self.position = position
        self.center_position = Position(position.x + 8, position.y + 8)
        self.camera_entity = pygame.rect.Rect(self.position.x, self.position.y, 16, 16)

    def rect(self):
        return self.camera_entity
    
    def set_position(self, position):
        if isinstance(position, Position):
            self.position = position
            self.center_position = Position(position.x + 8, position.y + 8)
            self.camera_entity = pygame.rect.Rect(self.position.x, self.position.y, 16, 16)
        else:
            raise ValueError("Position must be a Position object.")
        self.update()
        
    def update(self):
        self.camera_entity.centerx = self.center_position.x
        self.camera_entity.centery = self.center_position.y

class CameraBox(Camera):
    def __init__(self, player_manager):
        super().__init__()
        self.player_manager = player_manager
        players = [(player.rect().centerx, player.rect().centery) for player in self.player_manager.get_players()]
        average_x = sum(x for x, y in players) // len(players)
        average_y = sum(y for x, y in players) // len(players)
        self.camera_box = pygame.Rect(average_x-100, average_y-100, 200, 200)
        self.camera_entity = pygame.rect.Rect(self.camera_box.centerx, self.camera_box.centery, 2, 2)

    def rect(self):
        return self.camera_entity

    def update(self):
        players = [(player.rect().centerx, player.rect().centery) for player in self.player_manager.get_players()]
        average_x = sum(x for x, y in players) // len(players)
        average_y = sum(y for x, y in players) // len(players)
        # X-Axis Correction
        if average_x < self.camera_box.left:
            self.camera_entity.centerx = self.camera_box.left
        elif average_x > self.camera_box.right:
            self.camera_entity.centerx = self.camera_box.right
        else:
            self.camera_entity.centerx = average_x

        # Y-Axis Correction
        if average_y < self.camera_box.top:
            self.camera_entity.centery = self.camera_box.top
        elif average_y > self.camera_box.bottom:
            self.camera_entity.centery = self.camera_box.bottom
        else:
            self.camera_entity.centery = average_y
        super().update_by_target(self)
