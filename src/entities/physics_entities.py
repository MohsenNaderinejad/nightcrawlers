import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from .action import *
from src.items.arsenal import Arsenal
from src.engine.sound import SoundManager

# --------- PHYSICS ENTITY ---------
class PhysicsEntity:
    def __init__(self, game, e_type, position, size):
        self.game = game
        self.type = e_type
        self.__position = Position(*position)

        self.position_vector2 = pygame.Vector2(position)
        self.size = size

        self.velocity = Position()
        self.last_movement = Position()
        
        self.walk_speed = 4
        self.run_speed = 6
        self.max_fall_speed = 5
        self.fall_change_parameter = 0.1
    
        self.collisions = CollisionMap(self)
        self.collisionable = True
        self.tilemap_collision_flag = True

        self.animation_manager = Action(self)
        self.animation_manager.set_action('idle')

        self.entity_coordinate_system = None

        self.last_saved_position = self.position.copy()
        self.total_time_save = 60
        self.save_timer = self.total_time_save

        self.arsenal = Arsenal(self)

        self.max_freeze_time = 120
        self.freeze_time = 0

        self.hurt = False
        self.max_hurt_frame_counter = 0
        self.hurt_frame_counter = 0

        self.max_blindness_frame = 240
        self.blindness_frame_count = 0
        self.blindness_radius = self.size[0] * 2 if self.size[0] > self.size[1] else self.size[1] * 2

        self.black_screen_radius = max(self.size)
        self.show_black_circle = False
        
        self.sound_manager = SoundManager()

    @property
    def position(self):
        return self.__position
    
    @position.setter
    def position(self, value):
        if not isinstance(value, Position):
            raise ValueError("Position must be a Position object.")
        self.__position = value

    def freeze(self):
        self.freeze_time = self.max_freeze_time

    def blind(self):
        self.blindness_frame_count = self.max_blindness_frame

    def update_coordinate_system(self, camera, unit_scaler=None):
        temp_centered_position = Position(*self.rect().center)
        tmp_pos = temp_centered_position + self.animation_manager.animation_offset - camera.render_scroll
        if self.entity_coordinate_system is None:
            self.entity_coordinate_system = CoordinateSystem(tmp_pos, SCREEN_SIZE[0]/DISPLAY_SIZE[0])
        else:
            self.entity_coordinate_system.update_origin(tmp_pos)

    def rect(self):
        return pygame.rect.Rect(self.position.x, self.position.y, self.size[0], self.size[1])
    
    
    def render(self, screen, camera, scale_size=None):
        temp_pos = (self.position - camera.render_scroll + self.animation_manager.animation_offset).tuple()

        entity_IMG = pygame.transform.flip(self.animation_manager.animation.image(),self.animation_manager.flip,False)
        if not self.animation_manager.flip and self.animation_manager.action == 'wall_slide':
            if self.type == 'beanhead' or self.type == 'redhood':
                temp_pos = (temp_pos[0] + 3, temp_pos[1])
            elif self.type == 'crow':
                temp_pos = (temp_pos[0] + 6, temp_pos[1])
        if self.animation_manager.action == 'death' and self.type == 'boss_red':
            temp_pos = (temp_pos[0], temp_pos[1] + 7)  # Adjust position for boss death animation
        if scale_size:
            entity_IMG = pygame.transform.scale(entity_IMG, scale_size)
        screen.blit(entity_IMG, temp_pos)

    def frame_movement(self, controller):
        if self.freeze_time > 0:
            self.freeze_time -= 1
            return Position(0, 0) + self.velocity
        move = Position(controller.movement['RMove'] - controller.movement['LMove'], 0) * self.walk_speed
        return move + self.velocity
    
    def x_axis_collision_detector(self, tilemap, frame_movement_position):
        self.position.x += frame_movement_position.x

        if self.tilemap_collision_flag:
            entity_rect = self.rect()
            for rect in tilemap.physics_tiles_rect(self.position):
                if entity_rect.colliderect(rect):
                    if frame_movement_position.x < 0:
                        entity_rect.left = rect.right
                        self.collisions.change('left', True)
                    if self.position.x != entity_rect.x:
                        self.position.x = entity_rect.x

            for rect in tilemap.physics_tiles_rect(self.position + Position(self.size[0], 0)):
                if entity_rect.colliderect(rect):
                    if frame_movement_position.x > 0:
                        entity_rect.right = rect.left
                        self.collisions.change('right', True)
                    if self.position.x != entity_rect.x:
                        self.position.x = entity_rect.x

    def y_axis_collision_detector(self, tilemap, frame_movement_position):
        self.position.y += frame_movement_position.y
        
        if self.tilemap_collision_flag:
            entity_rect = self.rect()
            for rect in tilemap.physics_tiles_rect(self.position + Position(0, self.size[1])):
                if entity_rect.colliderect(rect):
                    if frame_movement_position.y > 0:
                        entity_rect.bottom = rect.top
                        self.collisions.change('down', True)
                    if self.position.y != entity_rect.y:
                        self.position.y = entity_rect.y
            
            for rect in tilemap.physics_tiles_rect(self.position):
                if entity_rect.colliderect(rect):
                    if frame_movement_position.y < 0:
                        entity_rect.top = rect.bottom
                        self.collisions.change('up', True)
                    if self.position.y != entity_rect.y:
                        self.position.y = entity_rect.y

    def flip_update(self, controller:PlayerController):
        if controller.movement['LMove']:
            self.animation_manager.flip = True
        elif self.animation_manager.flip and controller.movement['RMove']:
            self.animation_manager.flip = False

    def fall_out_off_platfrom(self, tilemap):
        if self.position.y > tilemap.max_y_axis_tile():
            return True
        return False