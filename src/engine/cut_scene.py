import pygame, sys, pathlib, os
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.tilemap import *
from src.entities.player import *
from src.entities.enemy import *
from src.engine.level import *
from src.engine.multiplyer import *
from src.engine.cameras import *
from src.items.dialogue import *

class CutSceneManager:
    def __init__(self, game):
        self.game = game
        self.active = True
        self.steps = []
        self.current_step = 0
        self.dialogue_shown = False
        self.waiting_for_input = False
        self.max_skip_frame = 120
        self.skip_frame = 0

    def add_step(self, func):
        self.steps.append(func)

    def reset(self):
        self.active = True
        self.steps = []
        self.current_step = 0
        self.dialogue_shown = False
        self.waiting_for_input = False
        self.max_skip_frame = 120
        self.skip_frame = 0

    def update(self):
        if not self.active:
            return
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_j] and not self.game.level.sub_phase_number == 3:
            self.skip_frame += 1
            if self.skip_frame >= self.max_skip_frame:
                self.end_cutscene()
                return
        else:
            self.skip_frame = 0

        if self.dialogue_shown:
            if not self.game.dialogue_manager.active:
                self.next_step()
            return
        if self.current_step < len(self.steps):
            self.steps[self.current_step](self)

    def next_step(self):
        self.current_step += 1
        self.dialogue_shown = False
        self.waiting_for_input = False
        if self.current_step >= len(self.steps):
            self.end_cutscene()

    def end_cutscene(self):
        self.active = False
        self.game.target_entity = self.game.level.players.get_player()
        self.game.dialogue_manager.clear_script()
        self.game.level.players.get_player().controller.movement['RMove'] = 0
        self.game.level.players.get_player().controller.movement['LMove'] = 0
        if self.game.level.pending_action != 'finish':
            self.game.cutscene_mode = False

        if self.game.level.identifier == 'boss':
            self.game.level.set_music()

    def handle_event(self, event, player):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.game.dialogue_manager.active:
                self.game.dialogue_manager.handle_input(event)
            elif self.waiting_for_input:
                self.next_step()

    def render(self, screen, camera):
        if self.active:
            self.game.dialogue_manager.render(screen, camera)