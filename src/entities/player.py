import pygame, sys, pathlib, math
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from .physics_entities import *
from .status import *
from src.engine.cameras import Camera
from src.items.dialogue import *
from src.network.utils import NetworkPlayerController
import time
# ------ PLAYER ------
class Player(PhysicsEntity):
    def __init__(self, game, e_type, position: Position, size: tuple, index=0, GNetwork=False, remote_player=False):
        super().__init__(game, e_type, position, size)

        self.index = index
        self.GNetwork = GNetwork
        if self.GNetwork:
            self.__id = None
            self.__hashtag = None
        self.remote_player = remote_player

        self.air_time = 0
        self.default_name = 'P' + str(self.index)
        self.name = self.default_name

        self.max_jump_time = 1
        self.jump_time = self.max_jump_time
        
        self.max_jump_speed = 3

        self.wall_slide = False
        self.wall_slide_speed = 0.5

        self.max_dash_speed = 8
        self.dashing_frame = 0

        self.x_axis_change_parameter = 0.1

        self.HP = Status(150 if not DEBUG else 15000)
        self.HP_increased = False
        self.hp_increase_amount = 0
        self.MP = Status(60 if not DEBUG else 6000)
        self.MP_increased = False
        self.mp_increase_amount = 0

        self.after_death_time = 180
        self.max_hurt_frame_counter = 32
        self.hurt_frame_counter = 0
        try:
            self.partitioned_health_bar_frame = self.HP.max_value / (len(self.game.ui_assets['player_health_bar']) - 1)
            self.partitioned_mana_bar_frame = self.MP.max_value / (len(self.game.ui_assets['player_mana_bar']) - 1)
        except Exception as e:
            self.partitioned_health_bar_frame = self.HP.max_value / 38
            self.partitioned_mana_bar_frame = self.MP.max_value / 38

        if not self.GNetwork:
            self.controller = PlayerController(self) if self.index == 0 else PlayerMultiplayerController(self, self.index)
        else:
            if self.remote_player:
                self.controller = NetworkPlayerController(self)
            else:
                self.controller = PlayerController(self)

        self.blindness_frame_count = 0

        # Increase Gun Damage
        self.bullet_damage_increased = False
        self.bullet_damage_time = None

        # Increase Jump Times
        self.double_jump_max_time = 7.500
        self.double_jump_time = 0

        # Shield Item
        self.have_shield = False
        self.time_shield = None
        self.shield_max_time = 7.500
        self.SHIELD = Status(50)
        try:
            self.shield_length_bar = len(self.game.ui_assets['player_shield_bar'])
        except Exception as e:
            self.shield_length_bar = 32
        self.partitioned_shield_bar_frame = self.SHIELD.max_value / (self.shield_length_bar - 1)

        self.shoot_key = 'L_CLICK'
        if self.index >= 1 and not self.GNetwork:
            self.shoot_key = 'SHOOT'
        self.reload_key = 'RELOAD'
        self.change_gun_key = 'CHANGE_GUN'

        self.death_times = 0
        self.is_dead = False
        self.death_times_changed = False
        if self.index >= 1 or self.GNetwork:
            self.rounds_won = 0

        self.bound_by_screen = False

        self.switch_gun_rest_frame = 0
        self.switch_gun_rest_frame_max = 90

        self.invincible = False

        # Dialogues
        self.monologue = MonologueBox('Pixel Game.otf', padding=6)

        self._hud_cache = LRUCache(150)
        self._last_rendered = LRUCache(150)
        self._name_box_cache = None
        self._name_box_pos = None
        self._name_changed = True
        self._frame_counter = 0

        self._cached_fonts = LRUCache(50)

        try:
            self.sound_manager.add_sfx('death',self.game.sounds['hero/death'], 0.3)
            self.sound_manager.add_sfx('dash',self.game.sounds['hero/dash'], 0.2)
            self.sound_manager.add_sfx('jump',self.game.sounds['hero/jump'], 0.055)
            self.sound_manager.add_sfx('walk',self.game.sounds['hero/walk'], 0.065)
            self.walk_sound_timer = 0
        except Exception as e:
            pass

        self.__group_number = None

    def set_group_number(self, group_number):
        self.__group_number = group_number

    @property
    def group_number(self):
        return self.__group_number
    
    @property
    def id(self):
        return self.__id
    
    def set_id(self, id):
        self.__id = id

    @property
    def hashtag(self):
        return self.__hashtag
    
    def set_hashtag(self, hashtag):
        self.__hashtag = hashtag

    def shoot(self):
        if self.index == 0 or self.GNetwork:
            player_point = pygame.Vector2((self.position - self.game.camera.render_scroll).tuple())
            base_direction = (self.controller.mouse_pos_vector2 - player_point).normalize()
            
        else:
            base_direction = pygame.Vector2(1, 0) if not self.animation_manager.flip else pygame.Vector2(-1, 0)
        angle = math.degrees(math.atan2(base_direction.y, base_direction.x))
        snapped_angle = round(angle / 45) * 45
        radians = math.radians(snapped_angle)
        snapped_vector = pygame.Vector2(math.cos(radians), math.sin(radians)).normalize()
        self.arsenal.current_gun.shoot(snapped_vector, self.index, self.group_number)

    def reload(self):
        if self.arsenal.current_gun:
            self.arsenal.current_gun.reload()

    def change_name(self, new_name):
        if self.name != new_name:
            self.name = new_name
            self._name_changed = True

    def reset_position(self):
        self.position = self.last_saved_position.copy()

    def hp_reduction(self, amount):
        if self.game.level.identifier == 'network_multiplayer_client':
            return
        if self.have_shield:
            remaining_damage = amount - self.SHIELD.actual_value
            if remaining_damage > 0:
                self.HP.decrease(remaining_damage)
                self.SHIELD.actual_value = 0
                self.have_shield = False
            else:
                self.SHIELD.decrease(amount)
        else:
            self.HP.decrease(amount)

    def action_manager(self):
        if self.after_death_time == 180:
            if self.hurt:
                self.hurt = False
                self.hurt_frame_counter = self.max_hurt_frame_counter
            else:
                self.hurt_frame_counter = max(0, self.hurt_frame_counter - 1)

            if self.hurt_frame_counter == self.max_hurt_frame_counter:
                self.animation_manager.set_action('hurt')
                
            self.wall_slide = False
            if self.hurt_frame_counter == 0:
                if (self.collisions.collision['right'] or self.collisions.collision['left']) and self.air_time > 4 and self.collisions.tilemap_collide:
                    self.wall_slide = True
                    self.velocity.y = min(self.velocity.y, self.wall_slide_speed)
                    if self.collisions.collision['right']:
                        self.animation_manager.flip = False
                    else:
                        self.animation_manager.flip = True
                    self.animation_manager.set_action('wall_slide')

            if not self.wall_slide and self.hurt_frame_counter == 0:
                if self.air_time > 4:
                    if self.last_movement.y < 0:
                        self.animation_manager.set_action('jump')
                    if self.last_movement.y > 0:
                        self.animation_manager.set_action('fall')
                elif self.controller.movement['LMove'] - self.controller.movement['RMove'] != 0:
                    try:
                        if self.walk_sound_timer > 0:
                            self.walk_sound_timer -= 1
                        else:
                            self.sound_manager.play_sfx('walk')
                            self.walk_sound_timer = 30
                    except Exception as e:
                        pass
                    self.animation_manager.set_action('walk')
                else:
                    self.animation_manager.set_action('idle')

    def dash_update(self):
        if self.dashing_frame > 0:
            self.dashing_frame = max(0, self.dashing_frame - 1)
            self.invincible = True
        elif self.dashing_frame < 0:
            self.invincible = True
            self.dashing_frame = min(0, self.dashing_frame + 1)
        else:
            self.invincible = False

    def dash_speed_update(self):
        if abs(self.dashing_frame) > 50:
            self.velocity.x = (abs(self.dashing_frame) / self.dashing_frame) * 8
            if abs(self.dashing_frame) == 51:
                self.velocity.x *= 0.1
        
        if self.velocity.x > 0:
            self.velocity.x = max(self.velocity.x - self.x_axis_change_parameter, 0)
        else:
            self.velocity.x = min(self.velocity.x + self.x_axis_change_parameter, 0)

    def check_around_rect(self):
        entity_rect = self.rect()
        return entity_rect.inflate(20, 20)

    def check_around_for_enemies(self, enemies):
        enemies_around = []
        entity_rect = self.check_around_rect()
        for enemy in enemies:
            if entity_rect.colliderect(enemy.rect()):
                enemies_around.append(enemy)
        return enemies_around

    def x_axis_collision_detector(self, tilemap, frame_movement_position):
        self.position.x += frame_movement_position.x
        entity_rect = self.rect()
        for rect in tilemap.physics_tiles_rect(self.position):
            if entity_rect.colliderect(rect):
                if frame_movement_position.x < 0:
                    entity_rect.left = rect.right
                    self.collisions.change('left', True)
                    self.collisions.tilemap_collision()
                if self.position.x != entity_rect.x:
                    self.position.x = entity_rect.x

        for rect in tilemap.physics_tiles_rect(self.position + Position(self.size[0], 0)):
            if entity_rect.colliderect(rect):
                if frame_movement_position.x > 0:
                    entity_rect.right = rect.left
                    self.collisions.change('right', True)
                    self.collisions.tilemap_collision()
                if self.position.x != entity_rect.x:
                    self.position.x = entity_rect.x

        players = self.game.level.players
        for player in players:
            if player != self and player.animation_manager.action != 'death':
                if entity_rect.colliderect(player.rect()):
                    if frame_movement_position.x > 0:
                        entity_rect.right = player.rect().left
                        self.collisions.change('right', True)
                    if frame_movement_position.x < 0:
                        entity_rect.left = player.rect().right
                        self.collisions.change('left', True)
                    if self.position.x != entity_rect.x:
                        self.position.x = entity_rect.x

    def y_axis_collision_detector(self, tilemap, frame_movement_position):
        self.position.y += frame_movement_position.y
        entity_rect = self.rect()

        for rect in tilemap.physics_tiles_rect(self.position):
            if entity_rect.colliderect(rect):
                if frame_movement_position.y < 0:
                    entity_rect.top = rect.bottom
                    self.collisions.change('up', True)
                    self.collisions.tilemap_collision()
                if self.position.y != entity_rect.y:
                    self.position.y = entity_rect.y
        for rect in tilemap.physics_tiles_rect(self.position + Position(0, self.size[1])):
            if entity_rect.colliderect(rect):
                if frame_movement_position.y > 0:
                    entity_rect.bottom = rect.top
                    self.collisions.change('down', True)
                    self.collisions.tilemap_collision()
                if self.position.y != entity_rect.y:
                    self.position.y = entity_rect.y

        players = self.game.level.players
        for player in players:
            if player != self and player.animation_manager.action != 'death':
                if entity_rect.colliderect(player.rect()):
                    if frame_movement_position.y > 0:
                        entity_rect.bottom = player.rect().top
                        self.collisions.change('down', True)
                    if frame_movement_position.y < 0:
                        entity_rect.top = player.rect().bottom
                        self.collisions.change('up', True)
                    if self.position.y != entity_rect.y:
                        self.position.y = entity_rect.y

    def bounding_update(self, camera: Camera, left = True, right = True, top = True, bottom = True):
        cam_left = camera.render_scroll.x
        cam_right = camera.render_scroll.x + DISPLAY_SIZE[0]
        cam_top = camera.render_scroll.y
        cam_bottom = camera.render_scroll.y + DISPLAY_SIZE[1]

        entity_rect = self.rect()

        # If left of screen
        if entity_rect.left < cam_left and left:
            self.position.x += cam_left - entity_rect.left
        # If right of screen
        if entity_rect.right > cam_right and right:
            self.position.x -= entity_rect.right - cam_right
        # If top of screen
        if entity_rect.top < cam_top and top:
            self.position.y += cam_top - entity_rect.top
        # If bottom of screen
        if entity_rect.bottom > cam_bottom and bottom:
            self.position.y -= entity_rect.bottom - cam_bottom

    def item_checker(self):
        # Bullet Damage Increase
        if self.bullet_damage_time != None and self.bullet_damage_increased and (time.perf_counter() - self.bullet_damage_time)>=10.000:
            if self.arsenal.current_gun.type == 'dua_colt':
                self.arsenal.current_gun.right_colt.bullet_damage = (10/11) * self.arsenal.current_gun.right_colt.bullet_damage 
                self.arsenal.current_gun.left_colt.bullet_damage = (10/11) * self.arsenal.current_gun.left_colt.bullet_damage
            else:
                self.arsenal.current_gun.bullet_damage = (5/6) * self.arsenal.current_gun.bullet_damage
            self.bullet_damage_increased = False

        # Double Jump
        if self.max_jump_time > 1 and ((time.perf_counter() - self.double_jump_time) >= self.double_jump_max_time):
            self.max_jump_time = 1

        # Shield
        if self.have_shield == True and time.perf_counter() - self.time_shield > self.shield_max_time:
            self.have_shield = False

    def update(self, tilemap, camera, unit_scaler=None, enemies=None):
        if self.game.level.pause_frame == 0 and self.game.level.pause_between_phases:
            self.clear_clicks()
        if not self.game.cutscene_mode:
            self.item_checker()
        self.update_coordinate_system(camera)
        self.collisions.reset()

        fr_movement = self.velocity
        if self.animation_manager.action != 'death':
            if self.game.level.pause_between_phases:
                fr_movement = self.velocity
                self.controller.movement['RMove'] = 0
                self.controller.movement['LMove'] = 0
            else:
                fr_movement = self.frame_movement(self.controller)
        if self.animation_manager.action == 'death':
            fr_movement = Position()

        if not self.game.cutscene_mode:
            self.arsenal.update(tilemap, enemies, self.game.level.players)
        self.x_axis_collision_detector(tilemap, fr_movement)
        self.y_axis_collision_detector(tilemap, fr_movement)
        if self.bound_by_screen:
            self.bounding_update(camera=camera)
        if self.animation_manager.action != 'death' and self.freeze_time <= 0 and not self.game.cutscene_mode:
            self.flip_update(self.controller)
        self.velocity.y = min(self.max_fall_speed, self.velocity.y + self.fall_change_parameter)
        if self.collisions.collision['up'] or self.collisions.collision['down']:
            self.velocity.y = 0
        if self.freeze_time <= 0:
            try:
                self.animation_manager.animation.update()
            except Exception as e:
                pass
        self.position_vector2 = pygame.Vector2(self.position.x + self.size[0] // 2, self.position.y + self.size[1] // 2)

        if self.HP.check() and not (self.game.level.pause_between_phases or self.game.cutscene_mode):
            if self.game.level.identifier == 'network_multiplayer_client':
                return
            self.death_action()

        if self.MP.actual_value != self.MP.max_value and self.game.level.identifier != 'network_multiplayer_client':
            self.MP.change_actual(self.MP.actual_value + 0.1)

        self.air_time += 1
        if self.collisions.collision['down']:
            self.air_time = 0
            self.jump_time = self.max_jump_time

        if self.fall_out_off_platfrom(tilemap=tilemap) and not (self.game.level.pause_between_phases or self.game.cutscene_mode):
            if self.game.level.identifier == 'network_multiplayer_client':
                return
            self.death_action()

        if self.animation_manager.action != 'death': 
            if self.index == 0 or self.GNetwork:
                if self.controller.mouse_movements[self.shoot_key] and self.arsenal.current_gun and (self.animation_manager.action != 'wall_slide' and self.animation_manager.action != 'death'):
                    self.shoot()
            elif self.index >= 1:
                if self.controller.movement[self.shoot_key] and self.arsenal.current_gun and (self.animation_manager.action != 'wall_slide' and self.animation_manager.action != 'death'):
                    self.shoot()

            if self.controller.movement[self.reload_key]:
                self.reload()

            self.switch_gun_rest_frame = max(0, self.switch_gun_rest_frame - 1)
            if self.controller.movement[self.change_gun_key] and self.switch_gun_rest_frame <= 0:
                if self.arsenal.current_gun:
                    self.switch_gun_rest_frame = self.switch_gun_rest_frame_max
                    self.arsenal.switch_gun()

        self.action_manager()
        self.dash_update()
        self.dash_speed_update()

        if self.collisions.collision['down']:
            self.save_timer -= 1

        self.last_movement.x = self.controller.movement['RMove'] - self.controller.movement['LMove']
        self.last_movement.y = self.velocity.y

    def clear_clicks(self):
        if self.index == 0 or self.GNetwork:
            self.controller.mouse_movements[self.shoot_key] = False
        else:
            self.controller.movement[self.shoot_key] = False
        self.controller.click_during_pause = False
        self.controller.clear_movement()

    def render(self, screen, camera):
        if not self.game.cutscene_mode:
            self.arsenal.render(screen, camera)
        
        super().render(screen, camera)
        if hasattr(self.game, 'reply_from'):
            if self.game.reply_from == 'player' and self.game.reply_frames >= 1 and self.game.level.sub_phase_number > 1 and not self.game.cutscene_mode:
                self.monologue.render_overhead_dialogue(screen, camera, Position(self.rect().x, self.rect().y), self.game.response, font_size=20, entity_width=self.size[0])

    def _get_cached_font(self, name, size):
        key = f"{name}_{size}"
        if key not in self._cached_fonts:
            self._cached_fonts[key] = load_font(name, size)
        return self._cached_fonts[key]

    def render_HUD(self, screen: pygame.Surface, scale=1.0):
        self._frame_counter = (self._frame_counter + 1) % 60
        if (self.GNetwork or self.game.level.identifier == 'one_device_multiplayer'):
            if self.animation_manager.action != 'death':
                self.render_name_box(screen)
            scale = 0.8
        
        alpha = 128 if self.animation_manager.action == 'death' else 255
        
        base_y = SCREEN_SIZE[1] - (143 * scale) - 10
        if self.GNetwork:
            if self.game.level.mode == 1:
                flip_x = self.index > 1
            else:
                flip_x = self.index > 2
        else:
            flip_x = self.index > 1
        gun_box_w = int(75 * scale)

        base_x = 0
        if flip_x:
            if (self.index == 3 or self.index == 2):
                base_x = SCREEN_SIZE[0] - 10
            else:
                base_x = SCREEN_SIZE[0] - 10 - 215
            gun_x = base_x
            next_x = base_x - gun_box_w - int(5 * scale)
        else:
            if self.index == 1 or self.index == 0:
                base_x = 10
            else:
                base_x = 10 + 215
            gun_x = base_x
            next_x = base_x + gun_box_w + int(5 * scale)

        self.render_gun_box(screen, gun_x, base_y + int(60 * scale), gun_box_w, flip_x, scale, alpha)
        self.render_player_image(screen, next_x, base_y, flip_x, scale, alpha)
        self.render_health_bar(screen, next_x, base_y + int(60 * scale), flip_x, scale, alpha)
        self.render_mana_bar(screen, next_x, base_y + int(90 * scale), flip_x, scale, alpha)
        self.render_shield_bar(screen, next_x, base_y + int(125 * scale), flip_x, scale, alpha)

    def render_name_box(self, screen):
        entity_rect = self.rect()
        entity_pos = Position(entity_rect.x, entity_rect.y) - self.game.camera.render_scroll
        display_to_screen_scale_x = SCREEN_SIZE[0] / DISPLAY_SIZE[0]
        display_to_screen_scale_y = SCREEN_SIZE[1] / DISPLAY_SIZE[1]
        screen_entity_x = entity_pos.x * display_to_screen_scale_x
        screen_entity_y = entity_pos.y * display_to_screen_scale_y
        screen_entity_width = entity_rect.width * display_to_screen_scale_x
        
        current_pos = (screen_entity_x, screen_entity_y)
        
        if (self._name_box_cache is None or 
            self._name_changed or 
            self._name_box_pos is None or
            abs(current_pos[0] - self._name_box_pos[0]) > 2 or 
            abs(current_pos[1] - self._name_box_pos[1]) > 2):
            
            font = self._get_cached_font('Leviathans.ttf', 19)
            text_surface = font.render(self.name, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            
            padding_x = 12
            padding_y = 6
            box_width = text_rect.width + padding_x * 2
            box_height = text_rect.height + padding_y * 2
            box_x = screen_entity_x + (screen_entity_width - box_width) // 2
            box_y = screen_entity_y - box_height - 16
            
            screen_margin = 8
            if box_x < screen_margin:
                box_x = screen_margin
            elif box_x + box_width > SCREEN_SIZE[0] - screen_margin:
                box_x = SCREEN_SIZE[0] - box_width - screen_margin
            
            if box_y < screen_margin:
                box_y = screen_margin
            elif box_y + box_height > SCREEN_SIZE[1] - screen_margin:
                box_y = SCREEN_SIZE[1] - box_height - screen_margin
            
            box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            box.fill((60, 60, 60, 215))
            pygame.draw.rect(box, (200, 200, 200, 120), (0, 0, box_width, box_height), width=2, border_radius=4)
            
            text_pos = ((box_width - text_rect.width) // 2, (box_height - text_rect.height) // 2)
            box.blit(text_surface, text_pos)
            
            self._name_box_cache = box
            self._name_box_pos = (box_x, box_y)
            self._name_changed = False
        
        screen.blit(self._name_box_cache, self._name_box_pos)

    def render_gun_box(self, screen, base_x, base_y, box_width, flip_x=False, scale=1.0, alpha=255):
        gun = self.arsenal.current_gun
        if not gun:
            return
        
        if gun.type == "dua_colt":
            ammo = gun.right_colt.magazine.ammo + gun.left_colt.magazine.ammo
            total = gun.right_colt.magazine.total_ammo + gun.left_colt.magazine.total_ammo
        else:
            ammo = gun.magazine.ammo
            total = gun.magazine.total_ammo
            
        cache_key = f"gun_box_{gun.type}_{ammo}_{total}_{flip_x}_{scale}_{alpha}"
        draw_x = base_x - box_width if flip_x else base_x
        
        if cache_key not in self._hud_cache:
            box_w = box_width
            box_h = int(75 * scale)
            
            gun_box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            
            border_radius = int(14 * scale)
            border_thickness = max(3, int(2.5 * scale))
            pygame.draw.rect(gun_box, (30, 30, 30, alpha), (0, 0, box_w, box_h), border_radius=border_radius)
            pygame.draw.rect(gun_box, (220, 220, 220, alpha), (0, 0, box_w, box_h), width=border_thickness, border_radius=border_radius)
            
            if hasattr(gun, "gun_surf"):
                gun_img = gun.gun_surf
            elif gun.type == "dua_colt":
                gun_img = gun.right_colt.gun_surf
            else:
                return
            
            gun_img = pygame.transform.flip(gun_img, flip_x, False)
            angle = 45 if not flip_x else -45
            rotated_img = pygame.transform.rotozoom(gun_img, angle, 1.0)
            
            if alpha < 255:
                rotated_img = rotated_img.copy()  
                rotated_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
            
            ammo_text = f"{ammo}/{total}"
            font = self._get_cached_font("Leviathans.ttf", int(20 * scale))
            text_width, text_height = font.size(ammo_text)
            
            vertical_padding = int(6 * scale)
            gap_between_image_and_text = int(4 * scale)
            
            content_height = int(box_h - 2 * vertical_padding)
            img_max_h = content_height - text_height - gap_between_image_and_text
            img_max_w = int(box_w * 0.8)
            
            img_w, img_h = rotated_img.get_size()
            scale_factor = min(img_max_w / img_w, img_max_h / img_h)
            img_w = int(img_w * scale_factor)
            img_h = int(img_h * scale_factor)
            gun_img_scaled_and_rotated = pygame.transform.scale(rotated_img, (img_w, img_h))
            
            content_total_height = img_h + gap_between_image_and_text + text_height
            start_y = (box_h - content_total_height) // 2
            
            img_x = (box_w - img_w) // 2
            img_y = start_y
            
            gun_box.blit(gun_img_scaled_and_rotated, (img_x, img_y))
            
            text_x = (box_w - text_width) // 2
            text_y = img_y + img_h + gap_between_image_and_text
            
            text_surf = pygame.Surface((text_width + 4, text_height + 4), pygame.SRCALPHA)
            draw_text_with_outline(
                text_surf, ammo_text, font, 2, 2,
                text_color=(255, 255, 255, alpha),
                outline_color=(0, 0, 0, alpha),
                thickness=2,
                center=False
            )
            gun_box.blit(text_surf, (text_x-2, text_y-2))
            
            self._hud_cache[cache_key] = gun_box
        
        screen.blit(self._hud_cache[cache_key], (draw_x, base_y))

    def render_player_image(self, screen, base_x, base_y, flip_x=False, scale=1.0, alpha=255):
        cache_key = f"player_image_{self.type}_{flip_x}_{scale}_{self.name}_{alpha}_{self.group_number}"
        
        if cache_key not in self._hud_cache or self._frame_counter == 0:
            image = self.game.player_assets[self.type]
            image_size = image.get_size()
            scaled_size = (int(image_size[0] * 3 * scale), int(image_size[1] * 3 * scale))
            
            max_name_width = 150
            surf_width = scaled_size[0] + max_name_width + int(20 * scale)
            surf_height = max(scaled_size[1] + int(10 * scale), 60)
            
            player_surf = pygame.Surface((surf_width, surf_height), pygame.SRCALPHA)
            
            image_scaled = pygame.transform.scale(image, scaled_size)
            image_scaled = pygame.transform.flip(image_scaled, flip_x, False)
            
            if alpha < 255:
                image_scaled = image_scaled.copy()
                image_scaled.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
            
            draw_x_local = 0 if not flip_x else surf_width - scaled_size[0]
            player_surf.blit(image_scaled, (draw_x_local, int(10 * scale)))
            
            font = self._get_cached_font('Leviathans.ttf', int(30 * scale))
            text_width, text_height = font.size(self.name)
            
            name_x_local = scaled_size[0] + int(20 * scale) if not flip_x else surf_width - scaled_size[0] - text_width - int(20 * scale)
            name_y_local = (surf_height - text_height) // 2
            
            if self.group_number is None:
                base_color = (255, 255, 255)    # White
            elif self.group_number == 1:
                base_color = (255, 60, 60)      # Vibrant red
            elif self.group_number == 2:
                base_color = (30, 144, 255)     # Dodger blue
            elif self.group_number == 3:
                base_color = (50, 205, 50)      # Lime green
            elif self.group_number == 4:
                base_color = (148, 0, 211)      # Royal purple
            else:
                base_color = (255, 255, 255)    # Default to white
            
            text_color = (base_color[0], base_color[1], base_color[2], alpha)
            outline_color = (0, 0, 0, alpha)
            
            text_surf = pygame.Surface((text_width + 4, text_height + 4), pygame.SRCALPHA)
            draw_text_with_outline(
                text_surf, self.name, font, 2, 2,
                text_color=text_color,
                outline_color=outline_color,
                thickness=2,
                center=False
            )
            
            player_surf.blit(text_surf, (name_x_local, name_y_local))
            
            draw_x_screen = base_x - scaled_size[0] if flip_x else base_x
            self._hud_cache[cache_key] = {"surf": player_surf, "pos": (draw_x_screen - (surf_width - scaled_size[0]) if flip_x else draw_x_screen, base_y)}
        
        screen.blit(self._hud_cache[cache_key]["surf"], self._hud_cache[cache_key]["pos"])

    def render_health_bar(self, screen, base_x, base_y, flip_x=False, scale=1.0, alpha=255):
        hp_value = int(self.HP.actual_value)
        cache_key = f"health_bar_{hp_value}_{flip_x}_{scale}_{alpha}"
        
        if cache_key not in self._hud_cache:
            holder = self.game.ui_assets['player_status_bar_holder']
            frame = (len(self.game.ui_assets['player_health_bar']) - 1) - math.ceil(self.HP.actual_value / self.partitioned_health_bar_frame)
            bar = self.game.ui_assets['player_health_bar'][frame]

            holder_size = holder.get_size()
            bar_size = bar.get_size()

            holder_w = int(holder_size[0] * 3 * scale)
            holder_h = int(holder_size[1] * 3 * scale)
            bar_w = int(bar_size[0] * 3 * scale)
            bar_h = int(bar_size[1] * 3 * scale)
            
            total_width = holder_w + 100
            health_surf = pygame.Surface((total_width, holder_h), pygame.SRCALPHA)
            
            holder_img = pygame.transform.scale(holder, (holder_w, holder_h))
            bar_img = pygame.transform.scale(bar, (bar_w, bar_h))
            holder_img = pygame.transform.flip(holder_img, False, flip_x)
            bar_img = pygame.transform.flip(bar_img, flip_x, False)
            
            if alpha < 255:
                holder_img = holder_img.copy()
                bar_img = bar_img.copy()
                holder_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
                bar_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
            
            local_holder_x = 0 if not flip_x else total_width - holder_w
            health_surf.blit(holder_img, (local_holder_x, 0))
            health_surf.blit(bar_img, (local_holder_x + int(9 * scale), int(9 * scale)))
            
            font = self._get_cached_font('Leviathans.ttf', int(26 * scale))
            text = str(hp_value)
            text_width, text_height = font.size(text)
            text_x = holder_w + int(10 * scale) if not flip_x else total_width - holder_w - text_width - int(10 * scale)
            text_y = int(6 * scale)
            
            text_surf = pygame.Surface((text_width + 4, text_height + 4), pygame.SRCALPHA)
            draw_text_with_outline(
                text_surf, text, font, 2, 2,
                text_color=(255, 255, 255, alpha),
                outline_color=(0, 0, 0, alpha),
                thickness=2,
                center=False
            )
            health_surf.blit(text_surf, (text_x-2, text_y-2))
            
            hud_x = base_x if not flip_x else base_x - total_width
            self._hud_cache[cache_key] = {"surf": health_surf, "pos": (hud_x, base_y)}
            
        screen.blit(self._hud_cache[cache_key]["surf"], self._hud_cache[cache_key]["pos"])

    def render_mana_bar(self, screen, base_x, base_y, flip_x=False, scale=1.0, alpha=255):
        mp_value = int(self.MP.actual_value)
        cache_key = f"mana_bar_{mp_value}_{flip_x}_{scale}_{alpha}"
        
        if cache_key not in self._hud_cache:
            holder = self.game.ui_assets['player_status_bar_holder']
            frame = (len(self.game.ui_assets['player_mana_bar']) - 1) - math.ceil(self.MP.actual_value / self.partitioned_mana_bar_frame)
            bar = self.game.ui_assets['player_mana_bar'][frame]

            holder_size = holder.get_size()
            bar_size = bar.get_size()
            holder_w = int(holder_size[0] * 3 * scale)
            holder_h = int(holder_size[1] * 3 * scale)
            bar_w = int(bar_size[0] * 3 * scale)
            bar_h = int(bar_size[1] * 3 * scale)
            
            total_width = holder_w + 100
            mana_surf = pygame.Surface((total_width, holder_h), pygame.SRCALPHA)
            
            holder_img = pygame.transform.scale(holder, (holder_w, holder_h))
            bar_img = pygame.transform.scale(bar, (bar_w, bar_h))
            holder_img = pygame.transform.flip(holder_img, False, True)
            bar_img = pygame.transform.flip(bar_img, False, True)
            
            if flip_x:
                holder_img = pygame.transform.flip(holder_img, True, False)
                bar_img = pygame.transform.flip(bar_img, True, False)
            
            if alpha < 255:
                holder_img = holder_img.copy()
                bar_img = bar_img.copy()
                holder_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
                bar_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
            
            local_holder_x = 0 if not flip_x else total_width - holder_w
            mana_surf.blit(holder_img, (local_holder_x, 0))
            mana_surf.blit(bar_img, (local_holder_x + int(9 * scale), int(9 * scale)))
            
            font = self._get_cached_font('Leviathans.ttf', int(26 * scale))
            text = str(mp_value)
            text_width, text_height = font.size(text)
            text_x = holder_w + int(10 * scale) if not flip_x else total_width - holder_w - text_width - int(10 * scale)
            text_y = int(6 * scale)
            
            text_surf = pygame.Surface((text_width + 4, text_height + 4), pygame.SRCALPHA)
            draw_text_with_outline(
                text_surf, text, font, 2, 2,
                text_color=(255, 255, 255, alpha),
                outline_color=(0, 0, 0, alpha),
                thickness=2,
                center=False
            )
            mana_surf.blit(text_surf, (text_x-2, text_y-2))
            
            hud_x = base_x if not flip_x else base_x - total_width
            self._hud_cache[cache_key] = {"surf": mana_surf, "pos": (hud_x, base_y)}
            
        screen.blit(self._hud_cache[cache_key]["surf"], self._hud_cache[cache_key]["pos"])

    def render_shield_bar(self, screen, base_x, base_y, flip_x=False, scale=1.0, alpha=255):
        shield_value = int(self.SHIELD.actual_value)
        cache_key = f"shield_bar_{shield_value}_{self.have_shield}_{flip_x}_{scale}_{alpha}"
        
        if cache_key not in self._hud_cache or self._frame_counter % 30 == 0:
            if self.have_shield:
                frame_index = (len(self.game.ui_assets['player_shield_bar']) - 1) - math.floor(self.SHIELD.actual_value / self.partitioned_shield_bar_frame)
                shield_text = str(shield_value)
            else:
                frame_index = len(self.game.ui_assets['player_shield_bar']) - 1
                shield_text = "0"

            bar = self.game.ui_assets['player_shield_bar'][frame_index]
            bar_size = bar.get_size()
            bar_w = int(bar_size[0] * 3 * scale)
            bar_h = int(bar_size[1] * 2 * scale)
            
            total_width = bar_w + 70
            shield_surf = pygame.Surface((total_width, bar_h + 10), pygame.SRCALPHA)
            
            bar_img = pygame.transform.scale(bar, (bar_w, bar_h))
            if flip_x:
                bar_img = pygame.transform.flip(bar_img, True, False)
            
            if alpha < 255:
                bar_img = bar_img.copy()
                bar_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
            
            local_bar_x = 0 if not flip_x else total_width - bar_w
            shield_surf.blit(bar_img, (local_bar_x, 0))
            
            font = self._get_cached_font('Leviathans.ttf', int(26 * scale))
            text_width, text_height = font.size(shield_text)
            text_x = bar_w + int(18 * scale) if not flip_x else total_width - bar_w - text_width - int(17 * scale)
            text_y = 0
            
            text_surf = pygame.Surface((text_width + 4, text_height + 4), pygame.SRCALPHA)
            draw_text_with_outline(
                text_surf, shield_text, font, 2, 2,
                text_color=(255, 255, 255, alpha),
                outline_color=(0, 0, 0, alpha),
                thickness=2,
                center=False
            )
            shield_surf.blit(text_surf, (text_x-2, text_y-2))
            
            draw_x = base_x + int(10 * scale) if not flip_x else base_x - total_width - int(10 * scale)
            self._hud_cache[cache_key] = {"surf": shield_surf, "pos": (draw_x, base_y)}
            
        screen.blit(self._hud_cache[cache_key]["surf"], self._hud_cache[cache_key]["pos"])

    def death(self):
        self.air_time = 0
        if self.game.level.identifier == 'simple_level':
            self.game.level.enemies.change_to_unsaved()
        if self.index == 0:
            self.game.fade_out(self.game.screen)
            self.game.game_over(self.type)
        if hasattr(self.game.level, 'save_game'):
            if self.game.level.save_game.current_save_tile != None:
                self.position = self.game.level.save_game.current_save_tile.position
            elif self.game.level.save_game.current_save_tile == None:
                self.reset_position()
        if self.game.level.identifier == 'boss' and self.game.level.pending_action == 'kill_player':
            return
        if not self.GNetwork:
            self.death_times += 1
        if not (self.game.level.identifier == 'network_multiplayer_server' or self.game.level.identifier == 'network_multiplayer_client' or self.game.level.identifier == 'one_device_multiplayer'):
            self.reset_position()
        self.HP.change_max(150)
        self.HP.reset()
        self.MP.change_max(60)
        self.MP.reset()
        self.is_dead = False
        self.death_times_changed = False
        self.bullet_damage_increased = False
        self.bullet_damage_time = None
        self.have_shield = False
        self.arsenal.reset_guns()
        try:
            self.partitioned_health_bar_frame = self.HP.max_value / (len(self.game.ui_assets['player_health_bar']) - 1)
            self.partitioned_mana_bar_frame = self.MP.max_value / (len(self.game.ui_assets['player_mana_bar']) - 1)
        except Exception as e:
            self.partitioned_health_bar_frame = self.HP.max_value / 38
            self.partitioned_mana_bar_frame = self.MP.max_value / 38

    def is_team_eliminated(self):
        if self.GNetwork:
            return self.game.level.teams[self.__group_number].team_has_been_eliminated
        return False

    def is_round_over(self):
        if self.GNetwork:
            return self.game.level.round_over
        return True

    def death_action(self):
        if self.after_death_time == 180:
            self.is_dead = True
            try:
                self.animation_manager.set_action('death')
            except Exception as e:
                self.animation_manager.action = 'death'
            try:
                self.sound_manager.play_sfx('death')
            except Exception as e:
                pass
        
        self.after_death_time = max(self.after_death_time - 1, 0)
        
        if self.after_death_time <= 0:
            
            if not getattr(self, "death_times_changed", False):
                self.death_times += 1
                self.death_times_changed = True
            
            if self.is_round_over():
                self.after_death_time = 180
                self.death()

    def jump(self):
        if self.animation_manager.action == 'death' or self.game.cutscene_mode:
            return False
        if self.wall_slide:
            if self.animation_manager.flip and self.last_movement.x < 0:
                self.velocity.x = 2.5
                self.velocity.y = -2.5
                self.air_time = 5
                self.jump_time = max(0 , self.jump_time - 1)
                return True
            if not self.animation_manager.flip and self.last_movement.x > 0:
                self.velocity.x = -2.5
                self.velocity.y = -2.5
                self.air_time = 5
                self.jump_time = max(0, self.jump_time - 1)
                return True

        if self.jump_time:
            self.velocity.y = -self.max_jump_speed
            self.jump_time -= 1
            self.air_time = 5
            try:
                self.sound_manager.play_sfx('jump')
            except Exception as e:
                pass
            return True
    
    def dash(self):
        if self.animation_manager.action == 'death' or self.game.cutscene_mode:
            return
        if self.MP.actual_value < 20:
            return
        if not self.dashing_frame:
            try:
                self.sound_manager.play_sfx('dash')
            except Exception as e:
                pass
            if self.last_movement.x < 0:
                self.dashing_frame = -FPS
            else:
                self.dashing_frame = FPS
            self.MP.change_actual(self.MP.actual_value-20)

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()
        self.arsenal.stop_all_sfx()

    @property
    def ABL_snapshot(self):
        ABL_snapshot = {
            "ABL": {
                "SHIELD": {
                    'actual_value': self.SHIELD.actual_value,
                    'max_value': self.SHIELD.max_value,
                    'partitioned_shield_bar_frame': self.partitioned_shield_bar_frame,
                    'have_shield': self.have_shield,
                    'time_shield': self.time_shield,
                    'shield_max_time': self.shield_max_time
                },
                "DOUBLE_JUMP": {
                    'double_jump_time': self.double_jump_time,
                    'max_jump_time': self.max_jump_time,
                    'double_jump_max_time': self.double_jump_max_time
                },
                "HP_INC": {
                    'hp_increase_amount': self.hp_increase_amount,
                    'partitioned_health_bar_frame': self.partitioned_health_bar_frame,
                    'HP_increased': self.HP_increased,
                },
                "MP_INC": {
                    'mp_increase_amount': self.mp_increase_amount,
                    'partitioned_mana_bar_frame': self.partitioned_mana_bar_frame,
                    'MP_increased': self.MP_increased,
                },
            }
        }
        return ABL_snapshot

    def apply_ABL_snapshot(self, snapshot: dict):
        if 'SHIELD' in snapshot:
            shield_data = snapshot['SHIELD']
            self.SHIELD.actual_value = shield_data['actual_value']
            self.SHIELD.max_value = shield_data['max_value']
            self.partitioned_shield_bar_frame = shield_data['partitioned_shield_bar_frame']
            self.have_shield = shield_data['have_shield']
            self.time_shield = shield_data['time_shield']
            self.shield_max_time = shield_data['shield_max_time']
        if 'DOUBLE_JUMP' in snapshot:
            double_jump_data = snapshot['DOUBLE_JUMP']
            self.double_jump_time = double_jump_data['double_jump_time']
            self.max_jump_time = double_jump_data['max_jump_time']
            self.double_jump_max_time = double_jump_data['double_jump_max_time']
        if 'HP_INC' in snapshot:
            hp_inc_data = snapshot['HP_INC']
            if hp_inc_data['HP_increased']:
                self.HP.change_max(hp_inc_data['hp_increase_amount'] + self.HP.max_value)
            self.partitioned_health_bar_frame = hp_inc_data['partitioned_health_bar_frame']
        if 'MP_INC' in snapshot:
            mp_inc_data = snapshot['MP_INC']
            if mp_inc_data['MP_increased']:
                self.MP.change_max(mp_inc_data['mp_increase_amount'] + self.MP.max_value)
            self.partitioned_mana_bar_frame = mp_inc_data['partitioned_mana_bar_frame']

    def apply_arsenal_snapshot(self, snapshot: dict):
        if 'arsenal' in snapshot:
            self.arsenal.apply_snapshot(snapshot['arsenal'])

class BeanHead(Player):
    def __init__(self, game, position: Position, size: tuple, index=0, GNetwork=False, remote_player=False):
        super().__init__(game, 'beanhead', position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        self.max_jump_speed = 3.5
        self.walk_speed = 1.5
        self.arsenal.add_gun_available_for_player('revolver')
        self.arsenal.add_gun('revolver')
        self.arsenal.add_gun_available_for_player('colt')
        self.arsenal.add_gun('colt')
        self.arsenal.default_gun()

class Crow(Player):
    def __init__(self, game, position: Position, size: tuple, index=0, GNetwork=False, remote_player=False):
        super().__init__(game, 'crow', position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        self.max_jump_speed = 2.75
        self.walk_speed = 1.0
        self.arsenal.add_gun_available_for_player('shotgun')
        self.arsenal.add_gun('shotgun')
        self.arsenal.add_gun_available_for_player('colt')
        self.arsenal.add_gun('colt')
        self.arsenal.default_gun()

class RedHood(Player):
    def __init__(self, game, position: Position, size: tuple, index=0, GNetwork=False, remote_player=False):
        super().__init__(game, 'redhood', position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        self.max_jump_speed = 3
        self.walk_speed = 1.2
        self.arsenal.add_gun_available_for_player('dua_colt')
        self.arsenal.add_gun('dua_colt')
        self.arsenal.add_gun_available_for_player('colt')
        self.arsenal.add_gun('colt')
        self.arsenal.default_gun()

class TheManWithHat(Player):
    def __init__(self, game, position: Position, size: tuple, index=0, GNetwork=False, remote_player=False):
        super().__init__(game, 'the_man_with_hat', position, size, index, GNetwork=GNetwork, remote_player=remote_player)
        self.max_jump_speed = 2.75
        self.walk_speed = 1.0
        self.arsenal.add_gun_available_for_player('m95')
        self.arsenal.add_gun('m95')
        self.arsenal.add_gun_available_for_player('colt')
        self.arsenal.add_gun('colt')
        self.arsenal.default_gun()