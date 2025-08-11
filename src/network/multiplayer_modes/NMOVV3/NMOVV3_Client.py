import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.tilemap import *
from src.entities.enemy import *
from src.entities.players import *
from src.entities.player import *
from src.items.items import *
from src.network.network_multiplayer import NetWorkMultiplayerClient, MMode

class NMOVV3Client(NetWorkMultiplayerClient):
    def __init__(self, Game, Arena_ID: int, client, PINFS):
        super().__init__(Game, Arena_ID, MMode.OVV3, client, PINFS)
        self.initialize_players()
        self.t1_dead = False
        self.t2_dead = False
        self.t3_dead = False

    def initialize_players(self):
        super().initialize_players()
        self.P1.animation_manager.flip = False
        self.P2.animation_manager.flip = True
        self.P3.animation_manager.flip = False
        self.grouping(self.P1, self.P2, self.P3)

    def grouping(self, P1, P2, P3=None, P4=None):
        self.teams[1].add_player(P1)
        self.teams[2].add_player(P2)
        self.teams[3].add_player(P3)

    def update(self):
        super().update()

        atleast_a_player_is_still_alive = 2 <= int(self.t1_dead) + int(self.t2_dead) + int(self.t3_dead) <= 3

        if atleast_a_player_is_still_alive:
            for team in self.teams.values():
                team.clear_bullets()

        elif self.match_timer <= 0:
            for team in self.teams.values():
                team.clear_bullets()

    def apply_server_snapshot(self, snapshot):
        super().apply_server_snapshot(snapshot)
        self.teams[1].apply_snapshot(snapshot.get("teams")['1'])
        self.teams[2].apply_snapshot(snapshot.get("teams")['2'])
        self.teams[3].apply_snapshot(snapshot.get("teams")['3'])
        self.t1_dead = snapshot.get("t1_dead", False)
        self.t2_dead = snapshot.get("t2_dead", False)
        self.t3_dead = snapshot.get("t3_dead", False)