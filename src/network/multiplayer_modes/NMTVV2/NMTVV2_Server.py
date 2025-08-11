import sys, pathlib, time
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.tilemap import *
from src.entities.enemy import *
from src.entities.players import *
from src.entities.player import *
from src.items.items import *
from src.engine.sound import SoundManager
from src.network.network_multiplayer import NetWorkMultiplayerServer, MMode, Team

class NMTVV2Server(NetWorkMultiplayerServer):
    def __init__(self, Arena_ID: int, PINFS, P1_CONN, P2_CONN, P3_CONN, P4_CONN):
        super().__init__(Arena_ID, MMode.TVV2, PINFS)
        self.rounds_to_win_for_each_team = 2
        self.match_max_timer = (60 * 60 * 2.5) + 1 # 2.5 minutes
        self.match_timer = self.match_max_timer
        self.initialize_players()
        self.Game.set_camera(self.players)
        self.Game.set_level(self)
        self.t1_dead = False
        self.t2_dead = False
        self.P1_CONN = P1_CONN
        self.P2_CONN = P2_CONN
        self.P3_CONN = P3_CONN
        self.P4_CONN = P4_CONN
        self.str_match_end = f"{self.P1.name}/{self.P1.hashtag} & {self.P2.name}/{self.P2.hashtag} vs {self.P3.name}/{self.P3.hashtag} & {self.P4.name}/{self.P4.hashtag}"

    def initialize_players(self):
        super().initialize_players()
        self.P1.animation_manager.flip = False
        self.P2.animation_manager.flip = False
        self.P3.animation_manager.flip = True
        self.P4.animation_manager.flip = True
        self.grouping(self.P1, self.P2, self.P3, self.P4)

    def grouping(self, P1, P2, P3=None, P4=None):
        self.teams[1].add_player(P1)
        self.teams[1].add_player(P2)
        self.teams[2].add_player(P3)
        self.teams[2].add_player(P4)

    def update(self):
        super().update()

        self.t1_dead = self.teams[1].team_eliminated()
        self.t2_dead = self.teams[2].team_eliminated()

        if self.t1_dead or self.t2_dead:
            self.teams[1].calculate_death_count()
            self.teams[2].calculate_death_count()
            for team in self.teams.values():
                team.clear_bullets()
            self.rounds_played += 1

            if self.t1_dead and self.t2_dead:
                print("Draw round")
                self.rounds_played -= 1
            elif self.t1_dead:
                self.teams[2].rounds_won += 1
            elif self.t2_dead:
                self.teams[1].rounds_won += 1

            self.delaying_reset = True
            self.round_over = True
            self.pause('reset', 180)

        elif self.match_timer <= 0 and not self.delaying_reset:
            self.rounds_played += 1
            for team in self.teams.values():
                team.calculate_death_count()
            if self.teams[1].get_total_hp() > self.teams[2].get_total_hp():
                self.teams[1].rounds_won += 1
            elif self.teams[1].get_total_hp() < self.teams[2].get_total_hp():
                self.teams[2].rounds_won += 1
            else:
                self.rounds_played -= 1

            for team in self.teams.values():
                team.clear_bullets()

            self.delaying_reset = True
            self.round_over = True
            self.pause('reset', 180)

        self.battle()

    @property
    def snapshot(self):
        snapshot = super().snapshot
        snapshot["t1_dead"] = self.t1_dead
        snapshot["t2_dead"] = self.t2_dead
        snapshot["teams"] = {str(team.team_id): team.get_snapshot() for team in self.teams.values()}
        return snapshot