import pygame, sys, pathlib, math
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.tilemap import *
from src.entities.enemy import *
from src.entities.players import *
from src.entities.player import *
from src.items.items import *
from src.engine.sound import SoundManager
class Multiplyer:
    def __init__(self, Game, Arena_ID=1):
        self.Game = Game
        self.arena_address = BASE_MAP_PATH + 'Arena/' + str(Arena_ID) + '.json'
        self.sound_manager = SoundManager()
        self.tilemap = TileMap(self.Game, tile_size=32)
        self.tilemap.load(self.arena_address)  # LOAD THE MAP
        self.players = PlayerManager(self.Game, Mode.Multiplayer)  # PLAYERS
        self.player_positions = {}
        self.enemies = Enemies(self.Game)  # ENEMIES
        self.death_count = {}

        self.match_max_timer = 60 * 60 * 2 + 1 # (FRAMES x SECONDS x MINUTES)
        self.match_timer = self.match_max_timer
        self.rounds_to_win_for_each_player = 4
        self.rounds_played = 0
        self.FONT = load_font('Pixel Game.otf', 32)

        self.itemList = Items(self)
        self.itemList.extract_items_position()

        self.pause_between_phases = False
        self.pending_action = ''
        self.max_pause_frame = 239
        self.pause_frame = 0

        self.delaying_reset = False
        self.reset_delay_timer = 0
        self.RESET_DELAY_DURATION = 60 # 1 second

        self.identifier = 'one_device_multiplayer'

        self.sound_manager.play_music(self.Game.music['multi_player_background'], loop=True, volume=0.1)
        self.Game.last_music = 'multi_player_background'
        self.pause('start')

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()
        self.enemies.stop_all_sfx()
        self.players.stop_all_sfx()
        self.itemList.stop_all_sfx()

    def initialize_players(self, player_one_char, player_two_char):
        # Initialize player one
        for player in self.tilemap.extract_tile_by_pair([('hero', 0)], keep=False):
            self.players.add_player(player_one_char, player.position.tuple(), (self.Game.player_assets[player_one_char].get_width(), self.Game.player_assets[player_one_char].get_height()), 1)
            self.players.get_player(1).last_saved_position = player.position
            self.players.get_player(1).controller.change_keys(PLAYER_ONE_KEY_BIND)
            self.death_count[1] = 0

        # Initialize player two
        for player in self.tilemap.extract_tile_by_pair([('hero', 1)], keep=False):
            self.players.add_player(player_two_char, player.position.tuple(), (self.Game.player_assets[player_two_char].get_width(), self.Game.player_assets[player_two_char].get_height()), 2)
            self.players.get_player(2).last_saved_position = player.position
            self.players.get_player(2).controller.change_keys(PLAYER_TWO_KEY_BIND)
            self.players.get_player(2).animation_manager.flip = True
            self.death_count[2] = 0

        self.tilemap.extract_tile_by_pair([('hero', 2), ('hero', 3)], keep=False) # deleteing the spawner for player 3 and 4

        self.P1 = self.players.get_player(1)
        self.P2 = self.players.get_player(2)

    def battle(self):
        if self.P1.rounds_won == self.rounds_to_win_for_each_player:
            self.stop_all_sfx()
            self.Game.match_over(1)
        elif self.P2.rounds_won == self.rounds_to_win_for_each_player:
            self.stop_all_sfx()
            self.Game.match_over(2)

    def clear_players_clicks(self):
        for player in self.players.get_players():
            player.clear_clicks()

    def reset_game(self):
        self.P1.HP.reset()
        self.P1.MP.reset()
        self.P1.reset_position()
        self.P1.animation_manager.flip = False

        self.P2.HP.reset()
        self.P2.MP.reset()
        self.P2.reset_position()
        self.P2.animation_manager.flip = True

        for player in self.players:
            player.clear_clicks()
            player.arsenal.clear_bullets()
            player.controller.clear_movement()

        self.match_timer = self.match_max_timer

        self.Game.particle_manager.clear_particles()

        if self.death_count[1] != self.P1.death_times:
            self.P1.death_times = self.death_count[1]
        if self.death_count[2] != self.P2.death_times:
            self.P2.death_times = self.death_count[2]

        self.P1.animation_manager.set_action('idle')
        self.P2.animation_manager.set_action('idle')

    def update(self):
        if self.pause_between_phases and self.pause_frame > 0:
            self.pause_frame = max(0, self.pause_frame - 1)
            return
        if self.pause_between_phases and self.pause_frame <= 0:
            self.pause_between_phases = False
            self.Game.cutscene_mode = False

        self.itemList.update()

        if self.delaying_reset:
            self.pause('start')
            self.reset_game()
            self.delaying_reset = False
            return

        self.match_timer = max(0, self.match_timer - 1)

        p1_dead = self.death_count[1] != self.P1.death_times
        p2_dead = self.death_count[2] != self.P2.death_times

        if p1_dead or p2_dead:
            self.death_count[1] = self.P1.death_times
            self.death_count[2] = self.P2.death_times
            self.rounds_played += 1
            self.P1.arsenal.clear_bullets()
            self.P2.arsenal.clear_bullets()

            if p1_dead and p2_dead:
                print("Draw round - both died.")
                self.rounds_played -= 1
            elif p1_dead:
                self.P2.rounds_won += 1
            elif p2_dead:
                self.P1.rounds_won += 1

            self.delaying_reset = True
            self.pause('reset', 180)

        elif self.match_timer == 0:
            self.rounds_played += 1
            if self.P1.HP.actual_value > self.P2.HP.actual_value:
                self.P1.rounds_won += 1
            elif self.P1.HP.actual_value < self.P2.HP.actual_value:
                self.P2.rounds_won += 1
            else:
                self.rounds_played -= 1

            self.P1.arsenal.clear_bullets()
            self.P2.arsenal.clear_bullets()

            self.delaying_reset = True
            self.pause('reset', 180)

        self.battle()

    def pause(self, pending_action: str, max_timer: int = 239):
        self.Game.cutscene_mode = True
        self.pause_between_phases = True
        self.pending_action = pending_action
        self.pause_frame = max_timer

    def render(self, surface, camera):
        self.tilemap.render(surface, camera)
        self.itemList.render(surface, camera)

    def render_HUD(self, screen):
        self.board_render(screen)
        self.rounds_for_player(screen)
        if self.pause_between_phases and self.pending_action == 'start':
            self.render_timer_countdown(screen)

    def board_render(self, screen):
        time_min = self.match_timer // (60 * 60)
        time_sec = (self.match_timer // 60 - time_min * 60) % 60
        time_min = str(time_min).zfill(2)
        time_sec = str(time_sec).zfill(2)
        time = time_min + ' : ' + time_sec
        
        self.FONT = load_font('Leviathans.ttf', 100)
        draw_text_with_outline(screen, time, self.FONT,
                                               SCREEN_SIZE[0] // 2, 30,
                                               text_color=(255, 255, 255),
                                               outline_color=(0, 0, 0),
                                               thickness=3.5)

        self.FONT = load_font('Leviathans.ttf', 40)
        draw_text_with_outline(screen, 'ROUND ' + str(self.rounds_played + 1), self.FONT,
                                               SCREEN_SIZE[0] // 2, 85,
                                               text_color=(255, 255, 255),
                                               outline_color=(0, 0, 0),
                                               thickness=3.5)

    def rounds_for_player(self, screen):
        top_left_p1 = (SCREEN_SIZE[0]/2 - 367, 15)
        top_left_p2 = (SCREEN_SIZE[0]/2 + 150, 15)
        p1_rounds = pygame.transform.scale_by(self.Game.ui_assets['round_bar_red'][(self.P1.rounds_won) % 5], 5)
        p1_rounds = pygame.transform.flip(p1_rounds, True, False)
        p2_rounds = pygame.transform.flip(self.Game.ui_assets['round_bar_blue'][(self.P2.rounds_won) % 5], False, False)
        p2_rounds = pygame.transform.scale_by(p2_rounds, 5)
        screen.blit(p1_rounds, top_left_p1)
        screen.blit(p2_rounds, top_left_p2)

    def render_timer_countdown(self, screen):
        screen_center = (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2)
        seconds_remainging_to_start = math.floor(self.pause_frame / 60)

        self.FONT = load_font('Leviathans.ttf', 290)
        if self.pause_frame <= 60:
            seconds_remainging_to_start = 'GO!'
        else:
            seconds_remainging_to_start = str(seconds_remainging_to_start)
        
        transparent_surface = pygame.Surface((SCREEN_SIZE[0], SCREEN_SIZE[1]), pygame.SRCALPHA)
        transparent_surface.fill((0, 0, 0, 150))  # Semi-transparent black
        screen.blit(transparent_surface, (0, 0))
        draw_text_with_outline(screen, str(seconds_remainging_to_start), self.FONT,
                                               screen_center[0], screen_center[1],
                                               text_color=(255, 255, 255),
                                               outline_color=(0, 0, 0),
                                               thickness=10)

