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

class NMOVV4Server(NetWorkMultiplayerServer):
    def __init__(self, Arena_ID: int, PINFS, P1_CONN, P2_CONN, P3_CONN, P4_CONN):
        super().__init__(Arena_ID, MMode.OVV4, PINFS)
        self.rounds_to_win_for_each_team = 2
        self.match_max_timer = (60 * 60 * 3) + 1
        self.match_timer = self.match_max_timer
        self.initialize_players()
        self.Game.set_camera(self.players)
        self.Game.set_level(self)
        self.t1_dead = False
        self.t2_dead = False
        self.t3_dead = False
        self.t4_dead = False
        self.P1_CONN = P1_CONN
        self.P2_CONN = P2_CONN
        self.P3_CONN = P3_CONN
        self.P4_CONN = P4_CONN
        self.str_match_end = f"{self.P1.name}/{self.P1.hashtag} vs {self.P2.name}/{self.P2.hashtag} vs {self.P3.name}/{self.P3.hashtag} vs {self.P4.name}/{self.P4.hashtag}"

    def initialize_players(self):
        super().initialize_players()
        self.P1.animation_manager.flip = False
        self.P2.animation_manager.flip = True
        self.P3.animation_manager.flip = False
        self.P4.animation_manager.flip = True
        self.grouping(self.P1, self.P2, self.P3, self.P4)

    def grouping(self, P1, P2, P3=None, P4=None):
        self.teams[1].add_player(P1)
        self.teams[2].add_player(P2)
        self.teams[3].add_player(P3)
        self.teams[4].add_player(P4)

    def update(self):
        super().update()

        self.t1_dead = self.teams[1].team_eliminated()
        self.t2_dead = self.teams[2].team_eliminated()
        self.t3_dead = self.teams[3].team_eliminated()
        self.t4_dead = self.teams[4].team_eliminated()

        atleast_a_player_is_still_alive = 3 <= int(self.t1_dead) + int(self.t2_dead) + int(self.t3_dead) + int(self.t4_dead) <= 4

        if atleast_a_player_is_still_alive:
            self.teams[1].calculate_death_count()
            self.teams[2].calculate_death_count()
            self.teams[3].calculate_death_count()
            self.teams[4].calculate_death_count()
            for team in self.teams.values():
                team.clear_bullets()
            self.rounds_played += 1

            if self.t1_dead and self.t2_dead and self.t3_dead and self.t4_dead:
                print("Draw round")
                self.rounds_played -= 1
            elif self.t2_dead and self.t3_dead and self.t4_dead:
                self.teams[1].rounds_won += 1
            elif self.t1_dead and self.t3_dead and self.t4_dead:
                self.teams[2].rounds_won += 1
            elif self.t1_dead and self.t2_dead and self.t4_dead:
                self.teams[3].rounds_won += 1
            elif self.t1_dead and self.t2_dead and self.t3_dead:
                self.teams[4].rounds_won += 1

            self.delaying_reset = True
            self.round_over = True
            self.pause('reset', 180)

        elif self.match_timer <= 0 and not self.delaying_reset:
            self.rounds_played += 1
            teams_hp_order = [team for team in self.teams.values()].sort(reverse=True, key=team.get_total_hp())
            if teams_hp_order[0].get_total_hp() == teams_hp_order[0].get_total_hp():
                self.rounds_played -= 1
            else:
                teams_hp_order[0].rounds_won += 1

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
        snapshot["t3_dead"] = self.t3_dead
        snapshot["t4_dead"] = self.t4_dead
        snapshot["teams"] = {str(team.team_id): team.get_snapshot() for team in self.teams.values()}
        return snapshot
