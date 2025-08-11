import pygame, sys, pathlib, time, threading
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.tilemap import *
from src.entities.players import *
from src.entities.player import *
from src.items.items import *
from src.engine.sound import SoundManager
from src.network.client.client import GameClient
from src.network.multiplayer_modes.server_side_game import ServerGame
from src.utils import *
class MMode:
    OVV2 = 1 # 1 v 1
    OVV3 = 2 # 1 v 1 v 1
    OVV4 = 3 # 1 v 1 v 1 v 1
    TVV2 = 4 # 2 v 2

class Team:
    def __init__(self, team_id: int, name=None):
        self.team_id = team_id
        if name is None:
            name = f"Team {team_id}"
        self.rounds_won = 0
        self.death_count = 0
        self.team_has_been_eliminated = False
        self.name = name
        self.players = []

    def add_player(self, player):
        self.players.append(player)
        player.set_group_number(self.team_id)

    def kill_all_players(self):
        for player in self.players:
            player.death_action()

    def get_total_hp(self):
        return sum(player.HP.actual_value for player in self.players)

    def remove_player(self, player):
        self.players.remove(player)

    def get_players(self):
        return self.players
    
    def set_name(self, name: str):
        self.name = name

    def reset_death_times(self):
        for player in self.players:
            player.death_times = self.death_count
            player.after_death_time = 180
            player.death_times_changed = False

    def reset_flip(self, flip: bool):
        for player in self.players:
            player.animation_manager.flip = flip

    def reset_actions(self):
        for player in self.players:
            player.animation_manager.set_action('idle')

    def reset_stats(self):
        for player in self.players:
            player.reset_position()
            player.HP.change_max(150)
            player.HP.reset()
            player.MP.change_max(60)
            player.MP.reset()
            player.after_death_time = 180
            player.death_times_changed = False
            player.animation_manager.set_action('idle')
            player.hurt = False
            player.hurt_frame_counter = 0
            player.death_times_changed = False
            player.bullet_damage_increased = False
            player.bullet_damage_time = None
            player.have_shield = False
            player.arsenal.reset_guns()
            try:
                player.partitioned_health_bar_frame = player.HP.max_value / (len(player.game.ui_assets['player_health_bar']) - 1)
                player.partitioned_mana_bar_frame = player.MP.max_value / (len(player.game.ui_assets['player_mana_bar']) - 1)
            except Exception as e:
                player.partitioned_health_bar_frame = player.HP.max_value / 38
                player.partitioned_mana_bar_frame = player.MP.max_value / 38
        self.team_has_been_eliminated = False

    def reset_position(self):
        for player in self.players:
            player.reset_position()

    def clear_bullets(self):
        for player in self.players:
            player.arsenal.clear_bullets()

    def calculate_death_count(self):
        if not self.players:
            self.death_count = 0
            return
            
        self.death_count = min(player.death_times for player in self.players)

    def team_eliminated(self):
        all_dead = True
        for player in self.players:
            if player.death_times <= self.death_count:
                all_dead = False
                break
        
        self.team_has_been_eliminated = all_dead
        return self.team_has_been_eliminated

    def clear_inputs(self):
        for player in self.players:
            player.clear_clicks()

    def __repr__(self):
        return f"Team {self.team_id} with players: {[player.name for player in self.players]}"
    
    def apply_snapshot(self, snapshot: dict):
        self.rounds_won = snapshot.get("rounds_won", self.rounds_won)
        self.death_count = snapshot.get("death_count", self.death_count)
        self.team_has_been_eliminated = snapshot.get("team_eliminated", self.team_has_been_eliminated)
        self.team_id = snapshot.get("team_id", self.team_id)

    def get_snapshot(self):
        return {
            "rounds_won": self.rounds_won,
            "death_count": self.death_count,
            "team_id": self.team_id,
            "team_eliminated": self.team_has_been_eliminated,
        }

class NetWorkMultiplayerServer:
    def __init__(self, Arena_ID: int, mode: MMode, PINFS: dict):
        self.server_time = time.perf_counter()
        self.mode = mode
        if self.mode == MMode.OVV2 or self.mode == MMode.TVV2:
            self.teams = {
                1: Team(1),
                2: Team(2)
            }
        elif self.mode == MMode.OVV3:
            self.teams = {
                1: Team(1),
                2: Team(2),
                3: Team(3)
            }
        elif self.mode == MMode.OVV4:
            self.teams = {
                1: Team(1),
                2: Team(2),
                3: Team(3),
                4: Team(4)
            }
        self.PINFS = PINFS
        self.player_assets_size = {
            'beanhead': (16, 18),
            'crow': (20, 30),
            'redhood': (16, 28),
            'the_man_with_hat': (22, 28),
        }
        self.arena_address = BASE_MAP_PATH + 'Arena/' + str(Arena_ID) + '.json'
        self.tilemap = TileMap(None, tile_size=32)
        self.tilemap.load(self.arena_address)  # LOAD THE MAP
        self.Game = ServerGame()
        self.players = PlayerManager(self.Game, Mode.Multiplayer)
        self.Enemies = None
        self.itemList = Items(self)
        self.itemList.extract_items_position()

        self.match_max_timer = 60 * 60 * 2 + 1 # (FRAMES x SECONDS x MINUTES) --> 2:00
        self.match_timer = self.match_max_timer
        self.rounds_to_win_for_each_team = 4
        self.rounds_played = 0
        self.round_over = False

        self.pause_between_phases = False
        self.pending_action = ''
        self.max_pause_frame = 239
        self.pause_frame = 0

        self.delaying_reset = False
        self.reset_delay_timer = 0

        self.identifier = 'network_multiplayer_server'

        self.pause('start')

        self.match_over = False
        self.winner = None

    def pause(self, pending_action: str, max_timer: int = 239):
        self.Game.cutscene_mode = True
        self.pause_between_phases = True
        self.pending_action = pending_action
        self.pause_frame = max_timer

    def battle(self):
        for team in self.teams.values():
            if team.rounds_won == self.rounds_to_win_for_each_team:
                self.match_over = True
                self.winner = team.team_id
                return
            
    def reset_game(self):
        for team in self.teams.values():
            team.reset_flip(True if team.team_id % 2 == 0 else False)
            team.reset_stats()
            team.reset_death_times()
            team.clear_bullets()
            team.reset_actions()
            team.clear_inputs()

        self.match_timer = self.match_max_timer
        self.round_over = False
            
    def update(self):
        self.server_time = time.perf_counter()
        self.Game.camera.update()
        if self.match_over:
            return
        self.player_update()
        if self.pause_between_phases and self.pause_frame > 0:
            self.pause_frame = max(0, self.pause_frame - 1)
            return
        if self.pause_between_phases and self.pause_frame <= 0:
            self.pause_between_phases = False
            self.Game.cutscene_mode = False

        self.itemList.update()

        if self.delaying_reset:
            self.reset_game()
            self.pause('start')
            self.delaying_reset = False
            return
        
        self.match_timer = max(0, self.match_timer - 1)

    def player_update(self):
        now = time.perf_counter()
        threads = []
        
        player_connections = [
            (self.P1_CONN, self.P1),
            (self.P2_CONN, self.P2),
        ]
        if hasattr(self, 'P3_CONN') and self.P3_CONN:
            player_connections.append((self.P3_CONN, self.P3))
        if hasattr(self, 'P4_CONN') and self.P4_CONN:
            player_connections.append((self.P4_CONN, self.P4))

        def process_player(conn, player):
            if conn is None or player is None:
                return
                
            latest_snapshot = None
            with conn.lock:
                if conn.input_buffer:
                    latest_snapshot = conn.input_buffer[-1].copy()
                    conn.input_buffer.clear()
            
            if latest_snapshot:
                player.controller.apply_snapshot(latest_snapshot, server_side=True)
                conn.last_applied_input_time = now
            elif now - getattr(conn, 'last_applied_input_time', conn.last_snapshot_time) > 0.5:
                player.controller.reset_all_inputs()

        for conn, player in player_connections:
            if conn is None or player is None:
                continue
            t = threading.Thread(target=process_player, args=(conn, player))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for conn, player in player_connections:
            if conn is None or player is None:
                continue
            
            player.update(self.tilemap, self.Game.camera)

        for team in self.teams.values():
            team.clear_inputs()

    def initialize_players(self):
        player_numbers = [1, 2, 3, 4]
        for player_number in player_numbers:
            try:
                player_info = self.PINFS[str(player_number)]
                for player in self.tilemap.extract_tile_by_pair([('hero', player_number - 1)], keep=False):
                    remote = True
                    player_op = player_info["operator"]
                    self.players.add_player(player_op, player.position.tuple(), (self.player_assets_size[player_op][0], self.player_assets_size[player_op][1]), player_number, GNetwork=True, remote_player=remote)
                    selected_player = self.players.get_player(player_number)
                    selected_player.last_saved_position = player.position
                    selected_player.set_id(player_info["id"])
                    selected_player.set_hashtag(player_info["hashtag"])
                    selected_player.change_name(player_info["name"])
            except Exception as e:
                self.tilemap.extract_tile_by_pair([('hero', player_number - 1)], keep=False)

        self.P1 = self.players.get_player(1)
        self.P1_CONN = None
        self.P2 = self.players.get_player(2)
        self.P2_CONN = None
        if '3' in self.PINFS:
            self.P3 = self.players.get_player(3)
            self.P3_CONN = None
        if '4' in self.PINFS:
            self.P4 = self.players.get_player(4)
            self.P4_CONN = None

    @property
    def snapshot(self):
        snapshot = {
            "server_time": self.server_time,
            "MTimer": self.match_timer,
            "cutscene_mode": self.Game.cutscene_mode,
            "rounds_played": self.rounds_played,
            "pause_between_phases": self.pause_between_phases,
            "pause_frame": self.pause_frame,
            "pending_action": self.pending_action,
            "delaying_reset": self.delaying_reset,
            "PUs": self.itemList.snapshot["PUs"],
            "round_over": self.round_over
        }
        return snapshot
    
    @property
    def P1_ADDITIONAL_INFO(self):
        return {
            "after_death_time": self.P1.after_death_time,
            "HP": self.P1.HP.snapshot,
            "MP": self.P1.MP.snapshot,
            "action": self.P1.animation_manager.action,
            **self.P1.ABL_snapshot,
            'arsenal': self.P1.arsenal.snapshot,
            "is_dead": self.P1.is_dead,
        }

    @property
    def P2_ADDITIONAL_INFO(self):
        return {
            "after_death_time": self.P2.after_death_time,
            "HP": self.P2.HP.snapshot,
            "MP": self.P2.MP.snapshot,
            **self.P2.ABL_snapshot,
            'action': self.P2.animation_manager.action,
            'arsenal': self.P2.arsenal.snapshot,
            "is_dead": self.P2.is_dead,
        }
    
    @property
    def P3_ADDITIONAL_INFO(self):
        return {
            "after_death_time": self.P3.after_death_time,
            "HP": self.P3.HP.snapshot,
            "MP": self.P3.MP.snapshot,
            **self.P3.ABL_snapshot,
            'action': self.P3.animation_manager.action,
            'arsenal': self.P3.arsenal.snapshot,
            "is_dead": self.P3.is_dead,
        }
    
    @property
    def P4_ADDITIONAL_INFO(self):
        return {
            "after_death_time": self.P4.after_death_time,
            "HP": self.P4.HP.snapshot,
            "MP": self.P4.MP.snapshot,
            **self.P4.ABL_snapshot,
            'action': self.P4.animation_manager.action,
            'arsenal': self.P4.arsenal.snapshot,
            "is_dead": self.P4.is_dead,
        }

class NetWorkMultiplayerClient:
    def __init__(self, Game, Arena_ID: int, mode: MMode, client: GameClient, PINFS: dict):
        self.mode = mode
        self.last_confirmed_server_time = time.perf_counter()
        self.now = time.perf_counter()
        if self.mode == MMode.OVV2 or self.mode == MMode.TVV2:
            self.teams = {
                1: Team(1),
                2: Team(2)
            }
        elif self.mode == MMode.OVV3:
            self.teams = {
                1: Team(1),
                2: Team(2),
                3: Team(3)
            }
        elif self.mode == MMode.OVV4:
            self.teams = {
                1: Team(1),
                2: Team(2),
                3: Team(3),
                4: Team(4)
            }
        self.PINFS = PINFS
        self.sound_manager = SoundManager()
        self.client = client
        self.Game = Game
        self.player_number_in_match = client.player_number
        self.arena_address = BASE_MAP_PATH + 'Arena/' + str(Arena_ID) + '.json'
        self.tilemap = TileMap(self.Game, tile_size=32)
        self.tilemap.load(self.arena_address)  # LOAD THE MAP

        self.players = PlayerManager(self.Game, Mode.Multiplayer)  # PLAYERS

        self.enemies = None

        self.match_timer = 0
        self.rounds_played = 0
        self.round_over = False

        self.FONT = load_font('Pixel Game.otf', 32)

        self.itemList = Items(self)

        self.pause_between_phases = False
        self.pending_action = ''
        self.pause_frame = 0

        self.delaying_reset = False
        self.server_delaying_reset = False
        self.reset_delay_timer = 0
        self.RESET_DELAY_DURATION = 0 # 3 seconds

        self.identifier = 'network_multiplayer_client'

        self.set_music()
        self.last_confirmed_pos = pygame.Vector2(0, 0)

        self._hud_cache = LRUCache(150)
        self._cached_fonts = LRUCache(50)
        self._frame_counter = 0
        self._last_timer = 0
        self._last_rounds = 0
        self._bar_cache = {"team1": None, "team2": None, "team3": None, "team4": None}

    def _get_cached_font(self, name, size):
        key = f"{name}_{size}"
        if key not in self._cached_fonts:
            self._cached_fonts[key] = load_font(name, size)
        return self._cached_fonts[key]

    def send_this_player_snapshot(self):
        player = self.this_player()
        mouse_pos = player.controller.mouse_pos_vector2
        input = player.controller.inputs()
        snapshot = {
            "timestamp": time.perf_counter(),
            "input": input,
            "x": player.position.x,
            "y": player.position.y,
            "mouse": {
                "x": mouse_pos.x,
                "y": mouse_pos.y
                }
        }
        self.client.send_snapshot(snapshot)

    def apply_server_snapshot(self, snapshot: dict):
        self.match_timer = snapshot.get("MTimer", self.match_timer)
        self.Game.cutscene_mode = snapshot.get("cutscene_mode", self.Game.cutscene_mode)
        self.rounds_played = snapshot.get("rounds_played", self.rounds_played)
        self.pause_between_phases = snapshot.get("pause_between_phases", self.pause_between_phases)
        self.pause_frame = snapshot.get("pause_frame", self.pause_frame)
        self.pending_action = snapshot.get("pending_action", self.pending_action)
        self.server_delaying_reset = snapshot.get("delaying_reset", self.server_delaying_reset)
        self.delaying_reset = snapshot.get("delaying_reset", self.delaying_reset)
        self.itemList.apply_snapshot(snapshot.get("PUs", {}))
        self.last_confirmed_server_time = snapshot.get("server_time", self.last_confirmed_server_time)
        self.round_over = snapshot.get("round_over", self.round_over)

    def set_music(self):
        self.sound_manager.play_music(self.Game.music['multi_player_background'], loop=True, volume=0.1)
        self.Game.last_music = 'multi_player_background'

    def initialize_players(self):
        player_numbers = [1, 2, 3, 4]
        for player_number in player_numbers:
            try:
                player_info = self.PINFS[str(player_number)]
                for player in self.tilemap.extract_tile_by_pair([('hero', player_number - 1)], keep=False):
                    remote = False if player_number == self.player_number_in_match else True
                    player_op = player_info["operator"]
                    self.players.add_player(player_op, player.position.tuple(), (self.Game.player_assets[player_op].get_width(), self.Game.player_assets[player_op].get_height()), player_number, GNetwork=True, remote_player=remote)
                    selected_player = self.players.get_player(player_number)
                    selected_player.last_saved_position = player.position
                    selected_player.set_id(player_info["id"])
                    selected_player.set_hashtag(player_info["hashtag"])
                    selected_player.change_name(player_info["name"])
            except:
                self.tilemap.extract_tile_by_pair([('hero', player_number - 1)], keep=False)

        self.P1 = self.players.get_player(1)
        self.P2 = self.players.get_player(2)
        if '3' in self.PINFS:
            self.P3 = self.players.get_player(3)
        if '4' in self.PINFS:
            self.P4 = self.players.get_player(4)

        self.this_player().controller.set_mouse_image(self.Game.assets['cursor'])

    def reset_game(self):
        for team in self.teams.values():
            team.reset_position()
            team.reset_actions()
            team.reset_death_times()
            team.reset_flip(True if team.team_id % 2 == 0 else False)
        self.Game.particle_manager.clear_particles()
        self.round_over = False

    def update(self):
        self.now = time.perf_counter()
        if self.pause_between_phases and self.pause_frame > 0:
            return

        self.itemList.updateClient()

        if self.server_delaying_reset:
            if self.delaying_reset:
                self.reset_game()
                self.delaying_reset = False
            return

    def render(self, surface, camera):
        self.tilemap.render(surface, camera)
        self.itemList.render(surface, camera)

    def this_player(self):
        if self.player_number_in_match == 1:
            return self.P1
        elif self.player_number_in_match == 2:
            return self.P2
        elif self.player_number_in_match == 3:
            return self.P3
        elif self.player_number_in_match == 4:
            return self.P4

    def render_HUD(self, screen):
        self._frame_counter = (self._frame_counter + 1) % 60
        self.board_render(screen)
        self.round_bars(screen)
        if self.pause_between_phases and self.pending_action == 'start':
            self.render_timer_countdown(screen)

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()
        self.enemies.stop_all_sfx()
        self.players.stop_all_sfx()
        self.itemList.stop_all_sfx()

    def clear_players_clicks(self):
        for player in self.players.get_players():
            player.clear_clicks()

    def board_render(self, screen):
        time_min = int(self.match_timer // (60 * 60))
        time_sec = int((self.match_timer // 60 - time_min * 60) % 60)
        time_min_str = str(time_min).zfill(2)
        time_sec_str = str(time_sec).zfill(2)
        time_str = time_min_str + ' : ' + time_sec_str
        
        timer_width = 230
        timer_height = 65
        round_width = 230
        round_height = 30
        
        right_padding = 15
        timer_x = SCREEN_SIZE[0] - timer_width - right_padding
        round_x = SCREEN_SIZE[0] - round_width - right_padding
        
        timer_y = 10
        round_y = timer_y + timer_height
        
        if "timer" not in self._hud_cache or time_str != self._last_timer or self._frame_counter % 30 == 0:
            self._last_timer = time_str
            
            timer_surf = pygame.Surface((timer_width, timer_height), pygame.SRCALPHA)
            
            font = self._get_cached_font('Leviathans.ttf', 80)
            time_text = font.render(time_str, True, (255, 255, 255))
            time_width, time_height = time_text.get_size()
            
            draw_text_with_outline(
                timer_surf, time_str, font, (timer_width - time_width) // 2, (timer_height - time_height) // 2,
                text_color=(255, 255, 255),
                outline_color=(0, 0, 0),
                thickness=4,
                center=False
            )
            
            self._hud_cache["timer"] = timer_surf
        
        if "round" not in self._hud_cache or self._last_rounds != self.rounds_played or self._frame_counter % 30 == 0:
            self._last_rounds = self.rounds_played
            
            round_surf = pygame.Surface((round_width, round_height), pygame.SRCALPHA)
            
            round_text = f'ROUND {self.rounds_played + 1}'
            font = self._get_cached_font('Leviathans.ttf', 30)
            
            text_width = font.size(round_text)[0]
            text_x = round_width - text_width - 3
            
            draw_text_with_outline(
                round_surf, round_text, font, text_x, round_height // 2,
                text_color=(255, 255, 255),
                outline_color=(0, 0, 0),
                thickness=3,
                center=True
            )
            
            self._hud_cache["round"] = round_surf
        
        if "timer" in self._hud_cache:
            screen.blit(self._hud_cache["timer"], (timer_x, timer_y))
        
        if "round" in self._hud_cache:
            screen.blit(self._hud_cache["round"], (round_x, round_y))
        
    def round_bars(self, screen):
        if self.mode == MMode.OVV2 or self.mode == MMode.TVV2:
            teams_to_show = [1, 2]
        elif self.mode == MMode.OVV3:
            teams_to_show = [1, 2, 3]
        elif self.mode == MMode.OVV4:
            teams_to_show = [1, 2, 3, 4]
        else:
            teams_to_show = [1, 2]
        
        cache_update_needed = any(self._bar_cache[f"team{i}"] is None for i in teams_to_show) or self._frame_counter % 30 == 0
        
        if cache_update_needed:
            base_x = 15
            base_y = 15
            bar_spacing = 29

            team_colors = {
                1: 'red',
                2: 'blue', 
                3: 'green',
                4: 'purple'
            }
            
            for i, team_id in enumerate(teams_to_show):
                team = self.teams[team_id]
                color = team_colors[team_id]
                
                rounds_won = (team.rounds_won * 2) % 5 if self.mode != MMode.OVV2 else team.rounds_won % 5
                team_bar = self.Game.ui_assets[f'round_bar_{color}'][rounds_won]
                
                scaled_bar = pygame.transform.scale_by(team_bar, 4.5)
                
                bar_y = base_y + (i * bar_spacing)
                bar_pos = (base_x, bar_y)
                
                self._bar_cache[f"team{team_id}"] = {"surf": scaled_bar, "pos": bar_pos}
        
        for team_id in teams_to_show:
            if self._bar_cache[f"team{team_id}"]:
                screen.blit(self._bar_cache[f"team{team_id}"]["surf"], self._bar_cache[f"team{team_id}"]["pos"])

    def render_timer_countdown(self, screen):
        seconds_remaining = math.floor(self.pause_frame / 60)
        cache_key = f"countdown_{seconds_remaining}"
        
        if cache_key not in self._hud_cache:
            overlay = pygame.Surface((SCREEN_SIZE[0], SCREEN_SIZE[1]), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            
            if self.pause_frame <= 60:
                text = 'GO!'
            else:
                text = str(seconds_remaining)
                
            font = self._get_cached_font('Leviathans.ttf', 290)
            text_surface = font.render(text, True, (255, 255, 255))
            text_width, text_height = text_surface.get_size()
            
            text_x = (SCREEN_SIZE[0] - text_width) // 2
            text_y = (SCREEN_SIZE[1] - text_height) // 2
            
            draw_text_with_outline(
                overlay, text, font, text_x, text_y,
                text_color=(255, 255, 255),
                outline_color=(0, 0, 0),
                thickness=10,
                center=False
            )
                        
            self._hud_cache[cache_key] = overlay
            
        screen.blit(self._hud_cache[cache_key], (0, 0))