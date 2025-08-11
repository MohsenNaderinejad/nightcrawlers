import pygame, sys, pathlib, random
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from .physics_entities import *
from .status import *
from src.items.gun import *
from src.entities.enemy import *
from src.items.dialogue import MonologueBox

class Boss(Enemy):
    def __init__(self, game, position, size):
        super().__init__(game, 'boss_normal', position, size)
        self.HP = Status(BOSS_ATTRS['HP'])
        self.attack_damage = BOSS_ATTRS['attack_damage']
        self.aggro_range = BOSS_ATTRS['aggro_range']
        self.attack_range = BOSS_ATTRS['attack_range']
        self.sight_range = BOSS_ATTRS['sight_range']
        self.field_of_view = BOSS_ATTRS['field_of_view']
        self.prev_field_of_view = self.field_of_view
        self.collisionable = True

        self.walk_speed = BOSS_ATTRS['walk_speed']
        self.run_speed = BOSS_ATTRS['run_speed']

        self.max_attack_frame = 48
        self.attack_frame_start = 24
        self.attack_frame_end = 24
        self.reset_attack_frame_range()

        self.boss_teleportation_positions = list()
        self.boss_teleportation_cooldown = 0
        self.boss_teleportation_cooldown_max = BOSS_ATTRS['boss_teleportation_cooldown_max']
        self.teleport_distance_threshold = BOSS_ATTRS['teleport_distance_threshold']
        self.last_teleport_position = None

        self.partitioned_health_bar_frame = self.HP.max_value / (len(self.game.ui_assets['boss_health_bar']) - 1)

        self.REMAINED_HP = Status(BOSS_ATTRS['REMAINED_HP'])

        self.red_eye_mode = True
        self.invincible = False
        self.in_action = True
        self.show_black_circle = False

        self.monologue = MonologueBox('Pixel Game.otf', padding=6)

        self.sound_manager.add_sfx('death',self.game.sounds['boss/death'])
        self.sound_manager.add_sfx('attack',self.game.sounds['boss/attack'])
        self.sound_manager.add_sfx('walk',self.game.sounds['boss/walk'])
        self.sound_manager.add_sfx('teleport',self.game.sounds['boss/teleport'], 0.06)

    def red_eye_mode_activator(self):
        self.red_eye_mode = True
        self.type = 'boss_red'

    def render(self, screen, camera, scaler=1):
        super().render(screen, camera, scaler)
        if hasattr(self.game, 'reply_from'):
            if self.game.reply_from == 'boss' and self.game.reply_frames >= 1 and self.game.level.sub_phase_number > 1 and not self.game.cutscene_mode:
                self.monologue.render_overhead_dialogue(screen, camera, Position(self.rect().x, self.rect().y), self.game.response, font_size=20, entity_width=self.size[0])

    def render_HUD(self, screen):
        actual_health_bar_frame = (len(self.game.ui_assets['boss_health_bar']) - 1) - math.ceil(self.HP.actual_value / self.partitioned_health_bar_frame)
        health_bar_img_raw = self.game.ui_assets['boss_health_bar'][actual_health_bar_frame]
        scaled_size = (health_bar_img_raw.get_width() * 3, health_bar_img_raw.get_height() * 3)
        health_bar_img = pygame.transform.scale(health_bar_img_raw, scaled_size)
        health_bar_img_rect = health_bar_img.get_rect(center=(SCREEN_SIZE[0] / 2, 30))
        screen.blit(health_bar_img, health_bar_img_rect)

        #Enemy Name
        font = load_font('KnightWarrior-w16n8.otf', 30)
        draw_text_with_outline(screen, "THE GOD OF CHAOS AND FEAR", font,
                       SCREEN_SIZE[0] // 2, 70,
                       text_color=(255, 255, 255),
                       outline_color=(0, 0, 0),
                       thickness=2)


    def hp_reduction(self, amount):
        portion = 1 if not self.red_eye_mode else 0.65
        if random.random() < 0.1: # 10% chance to reduce less HP
            portion = random.choice([0, 0.25, 0.5])
        amount = min(amount * portion, self.REMAINED_HP.actual_value)
        self.REMAINED_HP.decrease(amount)
        self.HP.decrease(amount)

    def player_collision_detector(self, player, frame_movement_position):
        pass

    def death(self):
        self.animation_manager.set_action('death')
        self.game.cutscene_mode = True
        self.show_black_circle = True
        self.game.level.sub_phase_number = 3
        self.game.level.pause('end')

    def reset_boss_teleportation_positions(self):
        self.boss_teleportation_positions = []

    def boss_teleportation(self, player):
        distance_to_player = math.hypot(self.position.x - player.position.x, self.position.y - player.position.y)

        if distance_to_player < self.teleport_distance_threshold:
            return

        if self.boss_teleportation_cooldown == 0:
            self.boss_teleportation_cooldown = self.boss_teleportation_cooldown_max
            if len(self.boss_teleportation_positions) > 0:
                if self.last_teleport_position and self.last_teleport_position == self.nearest_teleportation_positions(player):
                    return
                new_pos = self.nearest_teleportation_positions(player)
                if new_pos:
                    self.last_teleport_position = new_pos
                    self.position = new_pos.copy()
                    self.sound_manager.play_sfx('teleport')

    def nearest_teleportation_positions(self, player):
        if not self.boss_teleportation_positions:
            return None

        valid_positions = [pos for pos in self.boss_teleportation_positions if pos != self.last_teleport_position]

        if not valid_positions:
            return None

        nearest_position = min(
            valid_positions,
            key=lambda pos: math.hypot(pos.x - player.position.x, pos.y - player.position.y)
        )
        return nearest_position

    def add_teleportation_position(self, position):
        if isinstance(position, Position):
            self.boss_teleportation_positions.append(position)
        elif isinstance(position, tuple):
            self.boss_teleportation_positions.append(Position(*position))
        else:
            raise TypeError("Position must be a Position object or a tuple of (x, y).")

    def update(self, tilemap, camera, unit_scaler, player):
        super().update(tilemap, camera, unit_scaler, player)
        if not self.game.cutscene_mode and not self.animation_manager.action == 'death':
            self.boss_teleportation(player=player)
        self.boss_teleportation_cooldown = max(0, self.boss_teleportation_cooldown - 1)
