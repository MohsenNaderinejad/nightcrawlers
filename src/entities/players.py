import pygame, sys, pathlib, math
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from .physics_entities import *
from .status import *
from .player import BeanHead, Crow, RedHood, TheManWithHat

class Mode:
    SinglePlayer = 0
    Multiplayer = 1

class PlayerManager:
    def __init__(self, game, mode):
        self.game = game
        self.__players = []
        self.player_count = 0
        self.mode = mode

    def stop_all_sfx(self):
        for player in self.__players:
            player.stop_all_sfx()

    def add_player(self, player_type, position, size, index=0, GNetwork=False, remote_player=False):
        player = None
        if player_type == 'beanhead':
            player = BeanHead(self.game, position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        elif player_type == 'crow':
            player = Crow(self.game, position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        elif player_type == 'redhood':
            player = RedHood(self.game, position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        elif player_type == 'the_man_with_hat':
            player = TheManWithHat(self.game, position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        else:
            raise ValueError(f"Player type '{player_type}' is not recognized.")

        self.__players.append(player)
        self.player_count += 1

    def update(self, tilemap, camera, unit_scaler, enemies):
        for player in self.__players:
            player.update(tilemap, camera, unit_scaler, enemies)

    def render(self, surface, camera):
        for player in self.__players:
            player.render(surface, camera)

    def render_HUD(self, screen, scale=1.0):
        for player in self.__players:
            player.render_HUD(screen, scale)

    def single_player(self):
        return self.mode == Mode.SinglePlayer

    def multiplayer(self):
        return self.mode == Mode.Multiplayer
    
    def clear(self):
        self.__players = []
        self.player_count = 0
    
    def get_player(self, index=0):
        if self.single_player():
            return self.__players[0]
        elif self.multiplayer():
            return self.__players[index-1]

    def get_players(self):
        if self.single_player():
            return [self.__players[0]]
        elif self.multiplayer():
            return self.__players

    def __iter__(self):
        return iter(self.__players)

    def __next__(self):
        if self.player_count == 0:
            raise StopIteration
        else:
            self.player_count -= 1
            return self.__players[self.player_count]

    def __getitem__(self, index):
        return self.__players[index]