import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *

# --------- ACTION ---------
class Action:
    def __init__(self, entity):
        self.entity = entity
        
        self.action = ''
        self.animation_offset = Position(0,0)
        self.flip = False
    
    def set_action(self,action):
        if action != self.action:
            self.action = action
            try:
                self.animation = self.entity.game.animation_assets[self.entity.type + '/' + self.action].copy()
                self.animation.frame = 0
                self.animation.done = False
            except Exception as e:
                pass