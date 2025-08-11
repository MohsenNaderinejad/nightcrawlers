import pygame, sys, pathlib, os
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.tilemap import *
from src.entities.enemy import *
from src.entities.players import *
from src.entities.player import *
from src.items.items import *
from src.entities.boss import Boss
from src.engine.cameras import *
from src.items.save import *
from src.engine.sound import SoundManager
import src.cut_scenes.boss_battle_phase_one as boss_battle_cutscene_phase_one
import src.cut_scenes.boss_battle_phase_two as boss_battle_cutscene_phase_two
import src.cut_scenes.boss_battle_phase_three as boss_battle_cutscene_phase_three
import src.cut_scenes.boss_battle_phase_four as boss_battle_cutscene_phase_four
import src.cut_scenes.final_cutscene as final_cutscene

class Phase:
    def __init__(self, game, phase_number=1):
        self.Game = game
        self.phase = phase_number
        self.sub_phase = False
        self.tilemap_sub_number = 1
        self.tilemaps = {}

    def add_tilemap(self, tilemap_path):
        self.tilemaps[str(self.phase) + '_' + str(self.tilemap_sub_number)] = tilemap_path
        self.tilemap_sub_number += 1

    def __str__(self):
        return f"Phase {self.phase} with {len(self.tilemaps)} tilemaps"

class BossPhase:
    def __init__(self, game, player_style='BeanHead', scaler=1.0, player_manager=None):
        self.Game = game
        self.players = player_manager if player_manager else PlayerManager(self.Game, Mode.SinglePlayer)
        self.player_style = player_style
        self.player_scaler = scaler
        if player_manager is None:
            self.players.add_player(self.player_style, (0, 0), (self.Game.player_assets[self.player_style].get_width() * self.player_scaler, self.Game.player_assets[self.player_style].get_height() * self.player_scaler))
        self.tilemap = None
        self.BOSS = Boss(self.Game, (0, 0), (self.Game.assets['enemies'][5].get_width(), self.Game.assets['enemies'][5].get_height()))

        self.phase_number = 0
        self.sub_phase_number = 1

        self.sound_manager = SoundManager()

        self.CutScenes = {
            1 : boss_battle_cutscene_phase_one.boss_intro_cutscene,
            2 : boss_battle_cutscene_phase_two.boss_second_phase_explanation,
            3 : boss_battle_cutscene_phase_three.boss_third_phase_tired,
            4 : boss_battle_cutscene_phase_four.boss_fourth_phase_endgame,
            5 : final_cutscene.THE_END
        }

        self.enemies = Enemies(self.Game)
        self.enemies_teleportation_positions = []
        self.spawn_position_occupancy = {}
        self.itemList = Items(self)
        self.max_enemies_can_be_spawned = 0
        self.max_enemies_reached_frame = None
        self.enemy_cull_delay = 60
        
        # The BLACK RADIUS
        self.black_circle_screen_frame = 25
        self.black_circle_entities = []
        self.black_circle_radius_fade = {}
        self.black_circle_fade_out = False
        self.black_circle_fade_speed = 10
        self.black_circle_closing_in = False
        self.black_circle_closing_in_boss = False
        self.black_circle_player_multiplier = 4

        self.identifier = 'boss'
        self.phase = None

        self.pause_between_phases = False
        self.pending_action = ''
        self.max_pause_frame = 120
        self.pause_frame = 0

        self.cameras = []

    def set_music(self):
        if self.Game.cutscene_mode:
            music_name = 'boss_cutscene_' + str(self.phase_number)
        else:
            music_name = 'boss_phase_' + str(self.phase_number) + '_' + str(self.sub_phase_number)
        self.sound_manager.play_music(self.Game.music[music_name], loop=True, volume=0.17)
        self.Game.last_music = music_name

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()
        self.enemies.stop_all_sfx()
        self.BOSS.sound_manager.stop_all_sfx()
        self.players.stop_all_sfx()
        self.itemList.stop_all_sfx()

    def camera_position_extractor(self):
        del self.cameras
        self.cameras = []
        for camera in self.tilemap.extract_tile_by_pair([('hero', 1)], keep=False):
            self.cameras.append(CameraTarget(camera.position))
        return None
    
    def reset_black_circle_entities_and_radius_fade_out(self):
        self.black_circle_entities = []
        self.black_circle_radius_fade = {}

    def initialize_player(self):
        player_selected = self.players.get_player()
        self.Game.particle_manager.clear_particles()
        for player in self.tilemap.extract_tile_by_pair([('hero', 0)], keep=False):
            player_selected.position = player.position.copy()
        player_selected.controller.set_mouse_image(self.Game.assets['cursor'])
        player_selected.clear_clicks()
        player_selected.arsenal.clear_bullets()
        player_selected.controller.clear_movement()
        if self.Game.client:
            player_selected.change_name(self.Game.client.name)
        self.black_circle_entities.append(player_selected)
        self.black_circle_radius_fade[player_selected] = player_selected.black_screen_radius
        self.black_circle_screen_frame = 25
        self.black_circle_fade_out = False
        player_selected.show_black_circle = True
        if self.sub_phase_number == 1:
            self.black_circle_radius_fade[player_selected] *= self.black_circle_player_multiplier

    def initialize_boss(self):
        if self.sub_phase_number >= 2:
            for spawner in self.tilemap.extract_tile_by_pair([('enemies', 5)], keep=False):
                self.BOSS.position = spawner.position.copy()

            self.extract_boss_teleports()
            self.extract_enemies_summon_positions()
            self.black_circle_entities.append(self.BOSS)
            self.black_circle_radius_fade[self.BOSS] = self.BOSS.black_screen_radius
            self.black_circle_screen_frame = 25
            self.BOSS.show_black_circle = False
            self.black_circle_fade_out = False
            self.BOSS.in_action = True

    def extract_enemies_summon_positions(self):
        self.enemies_teleportation_positions = []
        self.spawn_position_occupancy = {}
        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 6)], keep=False):
            pos = spawner.position.copy()
            self.enemies_teleportation_positions.append(pos)
            self.spawn_position_occupancy[pos] = None  # Mark as initially empty
        self.max_enemies_can_be_spawned = len(self.enemies_teleportation_positions) // 2 + (len(self.enemies_teleportation_positions) % 2)

    def initialize_enemies(self):
        self.enemies.clear()
        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 0)], keep=False):
            self.enemies.add_enemy(Bomber, spawner.position.tuple(), (self.Game.assets['enemies'][0].get_width() * 0.6, self.Game.assets['enemies'][0].get_height() * 0.6))

        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 1)], keep=False):
            self.enemies.add_enemy(Freezer, spawner.position.tuple(), (self.Game.assets['enemies'][1].get_width() * 0.9, self.Game.assets['enemies'][1].get_height() * 0.9))

        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 2)], keep=False):
            self.enemies.add_enemy(Tank, spawner.position.tuple(), (self.Game.assets['enemies'][2].get_width() * 0.8, self.Game.assets['enemies'][2].get_height() * 0.8))

        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 3)], keep=False):
            self.enemies.add_enemy(Samurai, (spawner.position).tuple(), (self.Game.assets['enemies'][3].get_width() * 0.7, self.Game.assets['enemies'][3].get_height() * 0.7))

    def extract_boss_teleports(self):
        self.BOSS.reset_boss_teleportation_positions()
        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 4)], keep=False):
            self.BOSS.add_teleportation_position(spawner.position.tuple())

    def nearest_enemies_spawn_position(self, position):
        for pos in sorted(
            self.enemies_teleportation_positions,
            key=lambda p: (p.x - position.x)**2 + (p.y - position.y)**2
        ):
            enemy = self.spawn_position_occupancy.get(pos)
            if enemy is None or enemy.HP.check():
                return pos
        return None
    
    def cull_far_enemies_if_needed(self):
        if self.max_enemies_reached_frame is None:
            return
        now = pygame.time.get_ticks()
        if now - self.max_enemies_reached_frame < self.enemy_cull_delay * 1000 / 60:
            return

        player = self.players.get_player()
        enemies = list(self.enemies.enemies)
        enemies = [e for e in enemies if e.HP.check() == False]

        if len(enemies) < 2:
            return

        # Sort by distance descending (farthest first)
        enemies.sort(key=lambda e: (e.position.x - player.position.x)**2 + (e.position.y - player.position.y)**2, reverse=True)

        # Kill half of the enemies
        half = len(enemies) // 2
        for e in enemies[:half]:
            e.HP.change_actual(0)

        self.max_enemies_reached_frame = None

    def summon_enemies(self):
        if random.random() < 0.005:  # 0.5% chance to summon enemies each frame
            if self.enemies.enemy_count >= self.max_enemies_can_be_spawned:
                if self.max_enemies_reached_frame is None:
                    self.max_enemies_reached_frame = pygame.time.get_ticks()
                return
            else:
                self.max_enemies_reached_frame = None

            choice = random.choice(self.enemies.enemy_types)
            choice_position = self.nearest_enemies_spawn_position(self.players.get_player().position)
            if choice_position is None:
                return 
            position = Position(choice_position.x, choice_position.y)
            if choice == Bomber:
                self.enemies.add_enemy(Bomber, position.tuple(), (self.Game.assets['enemies'][0].get_width() * 0.6, self.Game.assets['enemies'][0].get_height() * 0.6))
            if choice == Tank:
                self.enemies.add_enemy(Tank, position.tuple(), (self.Game.assets['enemies'][2].get_width() * 0.8, self.Game.assets['enemies'][2].get_height() * 0.8))
            if choice == Samurai:
                self.enemies.add_enemy(Samurai, position.tuple(), (self.Game.assets['enemies'][3].get_width() * 0.7, self.Game.assets['enemies'][3].get_height() * 0.7))
            if choice == Freezer:
                self.enemies.add_enemy(Freezer, position.tuple(), (self.Game.assets['enemies'][1].get_width() * 0.6, self.Game.assets['enemies'][1].get_height() * 0.6))

            enemy = self.enemies.enemies[-1]
            self.spawn_position_occupancy[choice_position] = enemy

    # Ending Real-Battle Phase -> Goes to next phase Pre-Phase
    def check_end_phase(self):
        if self.BOSS.in_action and self.BOSS.REMAINED_HP.check():
            self.Game.cutscene_mode = True
            self.stop_all_sfx()
            self.pause('pre_phase')

    # Ending Pre-Phase -> Goes to Real-Battle Phase
    def check_end_pre_phase(self):
        if self.enemies.enemy_count == 0:
            self.Game.cutscene_mode = True
            self.stop_all_sfx()
            self.pause('real_battle')

    # Starting Pre-Phase
    def start_pre_phase(self):
        self.phase_number += 1
        self.sub_phase_number = 1
        self.phase = Phase(self.Game, self.phase_number)
        if self.phase_number == 1:
            self.set_music()
        self.phase_extractor()
        self.reset_black_circle_entities_and_radius_fade_out()
        self.initialize_player()
        self.enemies.clear()
        if self.phase_number >= 3:
            self.BOSS.red_eye_mode_activator()
        if not DEBUG:
            self.initialize_enemies()
        self.itemList.clear()
        self.itemList.extract_items_position()
        self.BOSS.in_action = False
        self.BOSS.REMAINED_HP.change_actual(self.BOSS.REMAINED_HP.max_value)
        self.making_black_circle_around_existing_entites(boss=False)
        self.black_circle_closing_in = True

    def pause(self, pending_action: str):
        self.pause_between_phases = True
        self.pending_action = pending_action
        self.pause_frame = self.max_pause_frame

    # Starting Real_Battle 
    def start_real_battle(self):
        self.sub_phase_number += 1
        self.phase_extractor()
        self.initialize_player()
        self.initialize_boss()
        self.enemies.clear()
        self.initialize_enemies()
        self.itemList.clear()
        self.itemList.extract_items_position()
        self.camera_position_extractor()
        self.CutScenes[self.phase_number](self.Game)
        self.set_music()

    # Ending Game
    def end_game(self):
        self.sound_manager.stop_all_sfx()
        self.enemies.clear()
        self.itemList.clear()
        pygame.mixer.music.load(self.Game.music['ending'])
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
        self.CutScenes[5](self.Game)

    def phase_extractor(self):
        self.tilemap = TileMap(self.Game, tile_size=32)
        phase_str = 'boss/' + str(self.phase_number - 1) + '_' + str(self.sub_phase_number)
        self.phase.add_tilemap(BASE_MAP_PATH + phase_str + '.json')
        phase_key = str(self.phase_number) + '_' + str(self.sub_phase_number)
        self.tilemap.load(self.phase.tilemaps[phase_key])

    def making_black_circle_around_existing_entites(self, boss=True, player=True):
        if boss:
            self.black_circle_radius_fade[self.BOSS] = max(DISPLAY_SIZE)
        if player:
            self.black_circle_radius_fade[self.players.get_player()] = max(DISPLAY_SIZE)

    def black_circle_closing_frames(self):
        player_radius = self.black_circle_radius_fade[self.players.get_player()]
        self.black_circle_radius_fade[self.players.get_player()] = max(player_radius - self.black_circle_fade_speed, self.players.get_player().black_screen_radius * self.black_circle_player_multiplier)

    def black_circle_closing_check(self):
        if self.black_circle_radius_fade[self.players.get_player()] == self.players.get_player().black_screen_radius * self.black_circle_player_multiplier:
            self.black_circle_closing_in = False
            self.black_circle_screen_frame = 25

    def update(self):
        if self.sub_phase_number == 1:
            if self.pause_between_phases:
                if self.pending_action == 'real_battle' and self.pause_frame == 0:
                    self.start_real_battle()
                    self.pause_between_phases = False
            else:
                self.check_end_pre_phase()
                
        if self.phase_number < 4 and self.sub_phase_number > 1:
            if self.pause_between_phases:
                if self.pending_action == 'pre_phase' and self.pause_frame == 0:
                    self.start_pre_phase()
                    self.pause_between_phases = False
                    self.Game.cutscene_mode = False
                    self.set_music()
            else:
                self.check_end_phase()
        
        if self.pending_action == 'end' and self.pause_frame == 0:
            self.pending_action = 'kill_player'
            self.end_game()

        if not self.Game.cutscene_mode:
            self.itemList.update()

        if self.BOSS.in_action:
            self.BOSS.update(self.tilemap, self.Game.camera, 1, self.players.get_player())
        if not self.Game.cutscene_mode and self.sub_phase_number > 1:
            self.summon_enemies()
            self.cull_far_enemies_if_needed()
        if self.black_circle_closing_in:
            self.black_circle_closing_frames()
            self.black_circle_closing_check()

        self.pause_frame = max(0, self.pause_frame - 1)

    def render(self, surface, camera):
        self.tilemap.render(surface, camera)
        if not self.Game.cutscene_mode:
            self.itemList.render(surface, camera)
        if self.BOSS.in_action:
            self.BOSS.render(surface, camera=camera)

    def clear_players_clicks(self):
        for player in self.players.get_players():
            player.clear_clicks()

class Level:

    def __init__(self,Game,player_style='BeanHead', scaler=1.0, chapter=0):
        self.Game=Game
        self.tilemaps = {
            '0' : BASE_MAP_PATH + 'levels/0.json',
            '1' : BASE_MAP_PATH + 'levels/1.json',
            '2' : BASE_MAP_PATH + 'levels/2.json',
            '3' : BASE_MAP_PATH + 'levels/3.json',
        }
        self.sound_manager = SoundManager()
        self.chapter = chapter
        self.tilemap = TileMap(self.Game, tile_size=32) # MAKING THE GRID FOR TILEMAP
        self.tilemap.load(self.tilemaps[str(chapter)]) # LOAD THE MAP
        self.enemies = Enemies(self.Game) # ENEMIES
        self.players = PlayerManager(self.Game, Mode.SinglePlayer) # PLAYERS
        self.player_style = player_style # DEFAULT PLAYER STYLE
        self.player_scaler = scaler # DEFAULT PLAYER SCALER
        self.itemList = Items(self)
        self.save_game = Save_game(self)

        self.pause_between_phases = False
        self.pending_action = ''
        self.max_pause_frame = 120
        self.pause_frame = 0

        self.identifier = 'simple_level'
        self.initialize_player()
        if not DEBUG:
            self.initialize_enemies()
        self.itemList.extract_items_position()
        self.save_game.extract_items_position()
        self.set_music()

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()
        self.enemies.stop_all_sfx()
        self.players.stop_all_sfx()
        self.itemList.stop_all_sfx()
        
    def set_music(self):
        music_name = 'background_theme_' + str(self.chapter + 1)
        self.sound_manager.play_music(self.Game.music[music_name], loop=True, volume=0.17)
        self.Game.last_music = music_name

    def initialize_player(self):
        for player in self.tilemap.extract_tile_by_pair([('hero', 0)], keep=False):
            self.players.add_player(self.player_style, player.position.tuple(), (self.Game.player_assets[self.player_style].get_width() * self.player_scaler, self.Game.player_assets[self.player_style].get_height() * self.player_scaler))
        self.players.get_player().controller.set_mouse_image(self.Game.assets['cursor']) # CHANGE THE CURSOR IMAGE
        if self.Game.client:
            self.players.get_player().change_name(self.Game.client.name)

    def initialize_enemies(self):
        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 0)], keep=False):
            self.enemies.add_enemy(Bomber, spawner.position.tuple(), (self.Game.assets['enemies'][0].get_width() * 0.6, self.Game.assets['enemies'][0].get_height() * 0.6))

        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 1)], keep=False):
            self.enemies.add_enemy(Freezer, spawner.position.tuple(), (self.Game.assets['enemies'][1].get_width() * 0.9, self.Game.assets['enemies'][1].get_height() * 0.9))

        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 2)], keep=False):
            self.enemies.add_enemy(Tank, spawner.position.tuple(), (self.Game.assets['enemies'][2].get_width() * 0.8, self.Game.assets['enemies'][2].get_height() * 0.8))

        for spawner in self.tilemap.extract_tile_by_pair([('enemies', 3)], keep=False):
            self.enemies.add_enemy(Samurai, (spawner.position).tuple(), (self.Game.assets['enemies'][3].get_width() * 0.7, self.Game.assets['enemies'][3].get_height() * 0.7))
    
    def update(self):
        self.itemList.update()
        self.save_game.update()
        if self.enemies.enemy_count == 0:
            self.stop_all_sfx()
            self.players.get_player().clear_clicks()
            self.players.get_player().arsenal.clear_bullets()
            self.players.get_player().controller.clear_movement()
            self.chapter = self.Game.level_over(self.chapter)
            if self.chapter > len(self.tilemaps)-1:
                self.Game.boss_level(self.player_style, self.players)
            if self.chapter <= len(self.tilemaps)-1:
                self.save_game.clear()
                self.Game.particle_manager.clear_particles()
                self.enemies.clear()
                self.tilemap = TileMap(self.Game, tile_size=32) 
                self.tilemap.load(self.tilemaps[str(self.chapter)])
                for i in self.tilemap.extract_tile_by_pair([('hero', 0)], keep=False):
                    if i.variant==0:
                        self.playerBlock=i

                spawner_pos = self.playerBlock.position
                
                self.players.get_player().position = Position(spawner_pos.x, spawner_pos.y) 

                self.itemList.extract_items_position()
                self.save_game.extract_items_position()
                self.initialize_player()
                if not DEBUG:
                    self.initialize_enemies()
                self.set_music()

    def render(self, surface, camera):
        self.tilemap.render(surface, camera)
        self.itemList.render(surface, camera)
        self.save_game.render(surface, camera)

    def clear_players_clicks(self):
        for player in self.players.get_players():
            player.clear_clicks()