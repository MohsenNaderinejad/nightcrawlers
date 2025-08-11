import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *

# ----- STATUS -----
class Status:
    def __init__(self, max_value):
        self.max_value = max_value
        self.actual_value = float(max_value)
        self.empty = False

    def change_max(self, max_value):
        if max_value <= 0:
            raise ValueError('Invalid Max Value')

        last_max_value = self.max_value
        self.max_value = max_value
        self.actual_value *= float(self.max_value / last_max_value)
        
    def change_actual(self, actual_value):
        if(actual_value < 0):
            actual_value = 0
            return
        
        elif(actual_value > self.max_value):
            self.actual_value = self.max_value
            return
        
        self.actual_value = actual_value
        
        if self.actual_value <= 0.001:
            self.empty = True
        else:
            self.empty = False

    def check(self):
        if self.actual_value <= 0:
            self.empty = True
        return self.empty
    
    def decrease(self, value):
        if value < 0:
            raise ValueError('Invalid Decrease Value')
        self.actual_value -= value
        if self.actual_value <= 0.001:
            self.actual_value = 0
            self.empty = True

    def reset(self):
        self.actual_value = self.max_value
        self.empty = False

    @property
    def snapshot(self):
        return {
            "max_value": self.max_value,
            "actual_value": self.actual_value,
            "empty": self.empty   
        }

    def apply_snapshot(self, snapshot):
        self.max_value = snapshot.get('max_value', self.max_value)
        self.actual_value = snapshot.get('actual_value', self.actual_value)
        self.empty = snapshot.get('empty', self.empty)
