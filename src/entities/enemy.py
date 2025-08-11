import pygame, sys, pathlib, random
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from .physics_entities import *
from .status import *
from src.items.gun import *

# --------- ENEMY ---------
class Enemy(PhysicsEntity):
    def __init__(self, game, e_type, position, size):
        super().__init__(game, e_type, position, size)
        self.HP = Status(100)
        self.MP = Status(50)
        self.controller = EnemyController()
        self.attack_cooldown = 0
        self.max_attack_cooldown = 120  # frames
        self.attack_damage = 1

        self.aggro_range = 90
        self.attack_range = 40
        self.sight_range = 100
        self.field_of_view = 90
        self.prev_field_of_view = self.field_of_view

        self.HP_time = 0
        self.after_death_time = 120

        self.max_hurt_frame_counter = 16
        self.hurt_frame_counter = 0

        self.enemy_in_air = False

        self.attack_frame_counter = 0
        self.max_attack_frame = 0
        self.attack_frame_start = 0
        self.attack_frame_end = 0
        self.attack_frame_range = [self.max_attack_frame - self.attack_frame_end, self.max_attack_frame - self.attack_frame_start]

        self.attack_action = 'attack'
        self.death_times = 0

        self.random_walk_timer = 0
        self.walk_sound_timer = 0

    def flip_update(self):
        if self.controller.movement['RMove'] > self.controller.movement['LMove']:
            self.animation_manager.flip = False
        elif self.controller.movement['LMove'] > self.controller.movement['RMove']:
            self.animation_manager.flip = True

    def reset_attack_frame_range(self):
        self.attack_frame_range = [self.max_attack_frame - self.attack_frame_end, self.max_attack_frame - self.attack_frame_start]

    def facing_angle(self):
        return 0 if not self.animation_manager.flip else 180
    
    def in_attack_frame_range(self):
        boolean = self.attack_frame_counter in range(self.attack_frame_range[0], self.attack_frame_range[1] + 1)
        return boolean


    def player_collision_detector(self, player, frame_movement_position):
        pass

    def death(self):
        self.sound_manager.play_sfx('death')
        self.game.level.enemies.remove_enemy(self)

    def can_see_player(self, player):
        distance = self.entity_coordinate_system.vector_size(player.position - player.game.camera.render_scroll)
        if distance > self.sight_range:
            return False
        angle_to_player = self.entity_coordinate_system.angle(player.position - player.game.camera.render_scroll)
        facing_angle = self.facing_angle()
        delta_angle = (angle_to_player - facing_angle + 180) % 360 - 180
        return abs(delta_angle) <= self.field_of_view / 2
    
    def in_aggro_range(self, player):
        distance = self.entity_coordinate_system.vector_size(player.position - self.game.camera.render_scroll)
        if distance > self.aggro_range:
            return False
        angle_to_player = self.entity_coordinate_system.angle(player.position - self.game.camera.render_scroll)
        facing_angle = self.facing_angle()
        delta_angle = (angle_to_player - facing_angle + 180) % 360 - 180
        return abs(delta_angle) <= self.field_of_view / 2

    def not_fall(self, tilemap, player):
        check_position = Position(
            self.rect().right if not self.animation_manager.flip else self.rect().left,
            self.rect().bottom
        )
        tiles_nearby = tilemap.tiles_around(check_position, enemy_ai = True)
        moving_right = self.controller.movement['RMove'] > self.controller.movement['LMove']
        moving_left = self.controller.movement['LMove'] > self.controller.movement['RMove']
        if moving_right and 1 not in tiles_nearby:
            self.controller.movement['RMove'] = 0
        if moving_left and -1 not in tiles_nearby:
            self.controller.movement['LMove'] = 0

    def flip_towards_player(self, player):
        if self.in_aggro_range(player):
            angle_to_player = self.entity_coordinate_system.angle(player.position - self.game.camera.render_scroll)
            player_on_right = -90 <= angle_to_player <= 90
            if player_on_right:
                self.animation_manager.flip = False
            else:
                self.animation_manager.flip = True
            return
        if self.hurt and not self.can_see_player(player):
            angle_to_player = self.entity_coordinate_system.angle(player.position - self.game.camera.render_scroll)
            player_on_right = -90 <= angle_to_player <= 90
            if player_on_right:
                self.animation_manager.flip = False
            else:
                self.animation_manager.flip = True
            return
        
    def flip_towards_entity(self, entity):
        angle_to_entity = self.entity_coordinate_system.angle(entity.position - self.game.camera.render_scroll)
        entity_on_right = -90 <= angle_to_entity <= 90
        if entity_on_right:
            self.animation_manager.flip = False
        else:
            self.animation_manager.flip = True

    def apply_ai_behavior(self, player):
        if self.hurt_frame_counter <= 0:
            distance_x = abs(self.rect().x - player.rect().x)
            if self.in_aggro_range(player):
                self.field_of_view = 360
                self.controller.movement['RMove'] = int(player.position.x > self.position.x) * self.run_speed 
                self.controller.movement['LMove'] = int(player.position.x < self.position.x) * self.run_speed
                if distance_x < self.attack_range:
                    self.controller.movement['RMove'] = 0
                    self.controller.movement['LMove'] = 0
            else:
                if self.field_of_view != self.prev_field_of_view:
                    self.controller.movement['RMove'] = 0
                    self.controller.movement['LMove'] = 0
                self.field_of_view = self.prev_field_of_view
                if self.random_walk_timer > 0:
                    self.random_walk_timer -= 1
                else:
                    if random.random() < 0.01:  # Random Movement
                        direction = random.choice(['left', 'right', 'idle'])
                        if direction == 'left':
                            self.controller.movement['LMove'] = self.walk_speed
                            self.controller.movement['RMove'] = 0
                        elif direction == 'right':
                            self.controller.movement['RMove'] = self.walk_speed
                            self.controller.movement['LMove'] = 0
                        else:
                            self.controller.movement['RMove'] = 0
                            self.controller.movement['LMove'] = 0
                        self.random_walk_timer = random.randint(30, 90)  # 0.5 to 1.5 seconds

            self.flip_towards_player(player)
        else:
            self.controller.movement['RMove'] = 0
            self.controller.movement['LMove'] = 0

    def action_manager(self, player, fr_movement):
        if self.attack_frame_counter == 0:
            if self.hurt_frame_counter == 0 and not self.hurt:
                if fr_movement.x != 0 and not (self.collisions.collision['left'] or self.collisions.collision['right']):
                    if self.in_aggro_range(player):
                        if self.walk_sound_timer > 0:
                            self.walk_sound_timer -= 1
                        else:
                            self.sound_manager.play_sfx('walk')
                            self.walk_sound_timer = 15
                        self.animation_manager.set_action('run')
                    else:
                        if self.walk_sound_timer > 0:
                            self.walk_sound_timer -= 1
                        else:
                            self.sound_manager.play_sfx('walk')
                            self.walk_sound_timer = 30
                        self.animation_manager.set_action('walk')
                else:
                    self.animation_manager.set_action('idle')
            else:
                if self.hurt:
                    self.hurt = False
                    self.hurt_frame_counter = self.max_hurt_frame_counter
                else:
                    self.hurt_frame_counter = max(0, self.hurt_frame_counter - 1)

                if self.hurt_frame_counter == self.max_hurt_frame_counter:
                    self.animation_manager.set_action('hurt')

    def update(self, tilemap, camera, unit_scaler, player):
        if self.animation_manager.action != 'death':
            self.update_coordinate_system(camera, unit_scaler)
            if not self.game.cutscene_mode:
                self.apply_ai_behavior(player)
            else:
                pass
            self.collisions.reset()
            self.not_fall(tilemap, player)

            fr_movement = self.velocity
            if self.animation_manager.action != 'death':
                if self.game.level.pause_between_phases:
                    fr_movement = self.velocity
                    self.controller.movement['RMove'] = 0
                    self.controller.movement['LMove'] = 0
                else:
                    fr_movement = self.frame_movement(self.controller)


            self.player_collision_detector(player, fr_movement)
            self.x_axis_collision_detector(tilemap, fr_movement)
            self.y_axis_collision_detector(tilemap, fr_movement)

            if self.attack_frame_counter == 0:
                self.action_manager(player, fr_movement)

            self.flip_update()

            if self.can_see_player(player) and self.check_attack_range(player) and not self.game.cutscene_mode:
                if self.attack_cooldown <= 0:
                    if self.max_attack_frame <= 0:
                        if self.type != 'bomber':
                            self.attack(player)
                            self.attack_cooldown = self.max_attack_cooldown
                    else:
                        self.animation_manager.set_action(self.attack_action)
                        self.attack_frame_counter = self.max_attack_frame
                        self.attack_cooldown = self.max_attack_cooldown

            if self.in_attack_frame_range() and self.max_attack_frame > 0 and not self.game.cutscene_mode:
                self.attack(player)
            
            if self.attack_frame_counter == 0:
                self.attack_cooldown = max(0, self.attack_cooldown - 1)
            self.attack_frame_counter = max(0, self.attack_frame_counter - 1)
            
            if not self.enemy_in_air:
                self.velocity.y = min(self.max_fall_speed, self.velocity.y + self.fall_change_parameter)

            if self.collisions.collision['up'] or self.collisions.collision['down']:
                self.velocity.y = 0

            self.last_movement.x = self.controller.movement['RMove'] - self.controller.movement['LMove']

            if self.fall_out_off_platfrom(tilemap):
                self.death()
                return

        if self.HP.check():
            self.animation_manager.set_action('death')
            self.after_death_time = max(self.after_death_time - 1, 0)
            self.collisionable = False

        if self.animation_manager.action == 'death' and self.after_death_time <= 0:
            self.death_times += 1
            if self.death_times >= 2:
                return
            self.death()
            return

        self.animation_manager.animation.update()

    def check_attack_range(self, player):
        return self.rect().inflate(self.attack_range, self.attack_range).colliderect(player.rect())

    def attack(self, player):
        self.sound_manager.play_sfx('attack')
        player.hp_reduction(self.attack_damage)
        player.hurt = True

    def render(self, screen, camera:Camera, scaler=1):
        temp_image_size = self.animation_manager.animation.image().get_size()
        scale_size = (temp_image_size[0] , temp_image_size[1])
        super().render(screen, camera, scale_size)

        if self.HP_time and not self.HP.check() and not self.type.startswith('boss'):
            BAR_WIDTH = 18
            BAR_HEIGHT = 2

            temp_pos = (self.position - camera.render_scroll + self.animation_manager.animation_offset + Position(self.size[0] // 2, -self.size[1] // 2)).tuple()
            if self.type == 'samurai':
                temp_pos = (temp_pos[0], temp_pos[1])

            pygame.draw.rect(screen, (255, 255, 255), (*temp_pos, BAR_WIDTH, BAR_HEIGHT))

            fill_ratio = self.HP.actual_value / self.HP.max_value
            pygame.draw.rect(screen, (255, 0, 0), (*temp_pos, BAR_WIDTH * fill_ratio, BAR_HEIGHT))

            self.HP_time -= 1

class Bomber(Enemy):
    def __init__(self, game, position, size):
        super().__init__(game, 'bomber', position, size)

        self.attack_damage = ENEMY_ATTRS['bomber']['attack_damage']
        self.HP = Status(ENEMY_ATTRS['bomber']['HP'])
        self.aggro_range = ENEMY_ATTRS['bomber']['aggro_range']
        self.attack_range = ENEMY_ATTRS['bomber']['attack_range']
        self.sight_range = ENEMY_ATTRS['bomber']['sight_range']
        self.field_of_view = ENEMY_ATTRS['bomber']['field_of_view']
        self.walk_speed = ENEMY_ATTRS['bomber']['walk_speed']
        self.run_speed = ENEMY_ATTRS['bomber']['run_speed']

        self.prev_field_of_view = self.field_of_view
        self.collisionable = True

        self.sound_manager.add_sfx('death',self.game.sounds['bomber/death'])
        self.sound_manager.add_sfx('attack',self.game.sounds['bomber/attack'], 0.085)


    def death(self, type='by_gun_shot'):
        if type != 'by_gun_shot':
            super().death()
        else:
            self.game.level.enemies.remove_enemy(self)
            self.sound_manager.play_sfx('death')


    def attack(self, player):
        super().attack(player)
        center_position = self.position.copy() + Position(self.size[0] // 2, self.size[1] // 2)
        self.game.particle_manager.add_particle('Circle_explosion', center_position)
        self.death('by_gun_shot')

    def update(self, tilemap, camera, unit_scaler, player):
        super().update(tilemap, camera, unit_scaler, player)
        if self.animation_manager.action == 'death':
            self.animation_manager.animation_offset = Position(0, 2)

    def player_collision_detector(self, player, frame_movement_position):
        # X axis
        temp_x = self.position.x
        temp_x += frame_movement_position.x
        entity_rect = self.rect()
        entity_rect.x = temp_x
        player_rect = player.rect()
        if entity_rect.colliderect(player_rect) and player.collisionable and not player.invincible:
                self.attack(player)
                return
        
        # Y axis
        temp_y = self.position.y
        temp_y += frame_movement_position.y
        entity_rect = self.rect()
        entity_rect.y = temp_y
        player_rect = player.rect()
        if entity_rect.colliderect(player_rect) and player.collisionable and not player.invincible:
                self.attack(player)
                return

class Freezer(Enemy):
    def __init__(self, game, position, size):
        super().__init__(game, 'freezer', position, size)
        
        self.attack_damage = ENEMY_ATTRS['freezer']['attack_damage']
        self.HP = Status(ENEMY_ATTRS['freezer']['HP'])
        self.aggro_range_x = ENEMY_ATTRS['freezer']['aggro_range_x']
        self.aggro_range_y = ENEMY_ATTRS['freezer']['aggro_range_y']
        self.attack_range = ENEMY_ATTRS['freezer']['attack_range']
        self.sight_range_x = ENEMY_ATTRS['freezer']['sight_range_x']
        self.sight_range_y = ENEMY_ATTRS['freezer']['sight_range_y']
        self.walk_speed = ENEMY_ATTRS['freezer']['walk_speed']
        self.run_speed = ENEMY_ATTRS['freezer']['run_speed']

        self.collisionable = True
        self.enemy_in_air = True
        self.prev_field_of_view = self.field_of_view

        self.max_attack_frame = 16
        self.attack_frame_start = 8
        self.attack_frame_end = 8
        self.reset_attack_frame_range()

        self.gun = FreezerGun(self.game)
        self.gun.rect = self.rect()
        self.gun.rect.y += self.size[1]
        self.max_attack_cooldown = self.gun.fire_rate

        self.sound_manager.add_sfx('death',self.game.sounds['freezer/death'])
        self.sound_manager.add_sfx('attack',self.game.sounds['freezer/attack'], 0.15)

    def death(self):
        super().death()
        center_position = self.position.copy() + Position(self.size[0] // 2, self.size[1] // 2)
        self.game.particle_manager.add_particle('Explosion_blue_circle', center_position)

    def attack(self, player):
        bullet_direction = self.entity_coordinate_system.normalized_vector(player.position- self.game.camera.render_scroll)
        shot = self.gun.shoot(bullet_direction)
        if shot:
            self.sound_manager.play_sfx('attack')


    def update(self, tilemap, camera, unit_scaler, player):
        super().update(tilemap, camera, unit_scaler, player)
        if self.animation_manager.action != 'death':
            if self.can_see_player(player) and not self.game.cutscene_mode:
                if self.attack_cooldown <= 0:
                    self.attack(player)
                    self.attack_cooldown = self.max_attack_cooldown
        self.gun.update(tilemap, self.game.level.enemies, self.game.level.players)
        self.gun.rect = self.rect()
        self.gun.rect.y += ( self.size[1] * 2 ) / 3

    def render(self, screen, camera:Camera, scaler=1):
        super().render(screen, camera, scaler)
        self.gun.render(screen, camera, self)

    def can_see_player(self, player):
        distance_x = abs(self.rect().centerx - player.rect().centerx)
        distance_y = player.rect().centery - self.rect().centery
        return distance_x < self.sight_range_x and distance_y < self.sight_range_y
    
    def apply_ai_behavior(self, player):
        distance_x = abs(self.rect().centerx - player.rect().centerx)
        if distance_x < self.aggro_range_x:
            self.controller.movement['RMove'] = int(player.position.x > self.position.x) * self.run_speed
            self.controller.movement['LMove'] = int(player.position.x < self.position.x) * self.run_speed
            if distance_x < self.attack_range:
                self.controller.movement['RMove'] = 0
                self.controller.movement['LMove'] = 0
        else:
            random_directions = [1, 0]
            if random.random() < 0.01:  # Random Movement
                self.controller.movement['RMove'] = random.choice(random_directions) * self.walk_speed
                self.controller.movement['LMove'] = random.choice(random_directions) * self.walk_speed
                if distance_x < self.attack_range:
                    self.controller.movement['RMove'] = 0
                    self.controller.movement['LMove'] = 0

class Tank(Enemy):
    def __init__(self, game, position, size):
        super().__init__(game, 'tank', position, size)
        
        self.HP = Status(ENEMY_ATTRS['tank']['HP'])
        self.aggro_range = ENEMY_ATTRS['tank']['aggro_range']
        self.attack_range = ENEMY_ATTRS['tank']['attack_range']
        self.sight_range = ENEMY_ATTRS['tank']['sight_range']
        self.field_of_view = ENEMY_ATTRS['tank']['field_of_view']
        self.walk_speed = ENEMY_ATTRS['tank']['walk_speed']
        self.run_speed = ENEMY_ATTRS['tank']['run_speed']

        self.prev_field_of_view = self.field_of_view
        self.collisionable = True

        self.attack_frame_start = 4
        self.attack_frame_end = 4
        self.max_attack_frame = 16
        self.reset_attack_frame_range()

        available_guns = [SimpleGun, SimpleGun, BlinderGun, FreezerGun]
        self.gun = random.choice(available_guns)(self.game)
        self.gun.rect = self.rect()
        self.gun.rect.x += self.size[0]
        self.max_attack_cooldown = self.gun.fire_rate

        self.animation_manager.animation_offset = Position(0, -3)

        self.sound_manager.add_sfx('death',self.game.sounds['tank/death'])
        self.sound_manager.add_sfx('attack',self.game.sounds['tank/attack'])

    def death(self):
        super().death()
        center_position = self.position.copy() + Position(self.size[0] // 2, self.size[1] // 2)
        mid_bottom_postion = Position(center_position.x, center_position.y + self.size[1] // 2)
        self.game.particle_manager.add_particle('Explosion_two_colors', mid_bottom_postion, mid_bottom=True, offset=Position(0, 17))

    def attack(self, player):
        bullet_direction = self.entity_coordinate_system.normalized_vector(player.position - self.game.camera.render_scroll)
        shot = self.gun.shoot(bullet_direction)
        if shot:
            self.sound_manager.play_sfx('attack')

    def render(self, screen, camera:Camera, scaler=1):
        self.gun.render(screen, camera, self)
        super().render(screen, camera, scaler)

    def update(self, tilemap, camera, unit_scaler, player):
        super().update(tilemap, camera, unit_scaler, player)
        self.gun.update(tilemap, self.game.level.enemies, self.game.level.players)
        self.gun.rect = self.rect()
        self.gun.rect.y += 1
        self.gun.rect.x += self.size[0] - 5 if not self.animation_manager.flip else -5

class Samurai(Enemy):
    def __init__(self, game, position, size):
        super().__init__(game, 'samurai', position, size)
        
        self.HP = Status(ENEMY_ATTRS['samurai']['HP'])
        self.aggro_range = ENEMY_ATTRS['samurai']['aggro_range']
        self.attack_range = ENEMY_ATTRS['samurai']['attack_range']
        self.sight_range = ENEMY_ATTRS['samurai']['sight_range']
        self.field_of_view = ENEMY_ATTRS['samurai']['field_of_view']
        self.walk_speed = ENEMY_ATTRS['samurai']['walk_speed']
        self.run_speed = ENEMY_ATTRS['samurai']['run_speed']

        self.prev_field_of_view = self.field_of_view
        self.collisionable = False

        self.sound_manager.add_sfx('death',self.game.sounds['samurai/death'])
        self.sound_manager.add_sfx('attack',self.game.sounds['samurai/attack'])

        self.choose_attack()

    def choose_attack(self):
        attacks = [1, 3]
        choice = random.choice(attacks)
        self.attack_action = "attack_" + str(choice)
        if choice == 1:
            self.max_attack_frame = 32
            self.attack_frame_start = 16
            self.attack_frame_end = 16
            self.attack_damage = ENEMY_ATTRS['samurai']['attack_damage']['attack_1']
        elif choice == 3:
            self.max_attack_frame = 32
            self.attack_frame_start = 16
            self.attack_frame_end = 16
            self.attack_damage = ENEMY_ATTRS['samurai']['attack_damage']['attack_3']
        self.reset_attack_frame_range()

    def sword_collision(self, player):
        rect_collide = self.rect().colliderect(player.rect()) if not player.invincible else False
        return rect_collide
    
    def player_collision_detector(self, player, frame_movement_position):
        pass

    def attack(self, player):
        self.choose_attack()
        if self.sword_collision(player=player): 
            super().attack(player=player)

class Enemies:
    def __init__(self, game):
        self.game = game
        self.enemies = []
        self.enemies_unsaved = []
        self.enemy_types = [Bomber, Bomber, Bomber, Freezer, Tank, Tank, Tank, Samurai]
        self.enemy_count = 0
        self.enemy_cout_unsaved = 0

    def add_enemy(self, enemy_type, position, size):
        if enemy_type not in self.enemy_types:
            raise ValueError(f"Enemy type '{enemy_type}' is not recognized.")
        if enemy_type == Bomber:
            enemy = Bomber(self.game, position, size)
        elif enemy_type == Freezer:
            enemy = Freezer(self.game, position, size)
        elif enemy_type == Tank:
            enemy = Tank(self.game, position, size)
        elif enemy_type == Samurai:
            enemy = Samurai(self.game, position, size)
        self.enemies.append(enemy)
        self.enemies_unsaved.append(enemy)
        self.enemy_count += 1
        self.enemy_cout_unsaved += 1

    def clear(self):
        del self.enemies
        self.enemies = []
        self.enemy_count = 0

    def stop_all_sfx(self):
        for enemy in self.enemies:
            enemy.sound_manager.stop_all_sfx()

    def update(self, tilemap, camera, unit_scaler, player):
        for enemy in self.enemies:
            enemy.update(tilemap, camera, unit_scaler, player)

    def remove_enemy(self, enemy):
        if enemy in self.enemies:
            self.enemies.remove(enemy)
            #self.game.level.save.dead_enemy_pos.append(enemy.position(self))
            self.enemy_count -= 1
            if self.game.level.identifier == 'boss':
                for pos, assigned in self.game.level.spawn_position_occupancy.items():
                    if assigned == enemy:
                        self.game.level.spawn_position_occupancy[pos] = None
        else:
            raise ValueError("Enemy not found in the list.")

    def render(self, screen, camera):
        for enemy in self.enemies:
            enemy.render(screen, camera, scaler=1)
        
    def __iter__(self):
        return iter(self.enemies)

    def __next__(self):
        if self.enemy_count == 0:
            raise StopIteration
        else:
            self.enemy_count -= 1
            return self.enemies[self.enemy_count]
        
    def __getitem__(self, index):
        return self.enemies[index]
    
    def change_to_unsaved(self):
        self.enemies=[]
        for enemy in self.enemies_unsaved:
            if enemy.type == "bomber":
                enemy = Bomber(self.game,enemy.position.tuple(),enemy.size)
            elif enemy.type == "freezer":
                enemy = Freezer(self.game,enemy.position.tuple(),enemy.size)
            elif enemy.type == "tank":
                enemy = Tank(self.game,enemy.position.tuple(),enemy.size)
            elif enemy.type == "samurai":
                enemy = Samurai(self.game,enemy.position.tuple(),enemy.size)
            self.enemies.append(enemy)

        self.enemy_count=self.enemy_cout_unsaved
        