import pygame, sys, pathlib, time
parent_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from config import *
from src.utils import Controller

log_address = "./network_player_controller_log.txt"

class NetworkPlayerController(Controller):
    def __init__(self, entity):
        super().__init__()
        self.entity = entity
        self.last_input_time = time.perf_counter()
        self.movement = {
            'UMove': False,
            'DMove': False,
            'LMove': False,
            'RMove': False,
            'Jump': False,
            'SHIFT': False,
            'SHOOT': False,
            'RELOAD': False,
            'CHANGE_GUN': False,
        }
        self.mouse_movements = {
            'L_CLICK': False,
            'R_CLICK': False,
            'M_CLICK': False
        }
        self.mouse_pos_vector2 = pygame.Vector2(0, 0)

    def apply_snapshot(self, snapshot: dict, server_side=False):
        self.last_input_time = snapshot.get("timestamp", self.last_input_time)
        if server_side and not self.entity.game.level.delaying_reset:
            self.entity.position.x = snapshot.get("x", self.entity.position.x)
            self.entity.position.y = snapshot.get("y", self.entity.position.y)
        if not server_side:
            new_x = snapshot.get("x", self.entity.position.x)
            dx = new_x - self.entity.position.x
            if abs(dx) > 1:
                self.entity.position.x = new_x

            new_y = snapshot.get("y", self.entity.position.y)
            dy = new_y - self.entity.position.y
            if abs(dy) > 1:
                self.entity.position.y = new_y

        if not server_side:
            self.entity.HP.apply_snapshot(snapshot.get("HP"))
            self.entity.MP.apply_snapshot(snapshot.get("MP"))
            self.entity.after_death_time = snapshot.get("after_death_time", self.entity.after_death_time)
            if snapshot.get("action") == 'death':
                self.entity.animation_manager.set_action(snapshot.get("action", self.entity.animation_manager.action))

        input_data = snapshot.get("input", {})
        for key in self.movement:
            self.movement[key] = input_data.get(key, False)
        for key in self.mouse_movements:
            self.mouse_movements[key] = input_data.get(key, False)

        mouse_data = snapshot.get("mouse", {})
        mouse_x = mouse_data.get("x", self.mouse_pos_vector2.x)
        mouse_y = mouse_data.get("y", self.mouse_pos_vector2.y)
        self.mouse_pos_vector2 = pygame.Vector2(mouse_x, mouse_y)

        if input_data.get("Jump") and self.entity.freeze_time <= 0:
            self.entity.jump()
        if input_data.get("SHIFT"):
            self.entity.dash()

    def inputs(self):
        inputs = dict(self.movement, **self.mouse_movements)
        return inputs
    
    def reset_all_inputs(self):
        for key in self.movement:
            self.movement[key] = False
        for key in self.mouse_movements:
            self.mouse_movements[key] = False
        self.mouse_pos_vector2 = pygame.Vector2(0, 0)
