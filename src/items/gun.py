import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from src.items.bullet import *

class EnemyGunInterface:
    def __init__(self, game, type, bullet_damage, bullet_speed, fire_rate):
        self.game = game
        self.type = type
        self.bullet_damage = bullet_damage
        self.bullet_speed = bullet_speed
        self.fire_rate = fire_rate
        self.shoot_cooldown = 0
        self.bullets = Bullets()
        self.rect = None

    def shoot(self, direction):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.fire_rate
            position = Position(self.rect.centerx, self.rect.centery + 2)
            self.bullets.add_bullet(Bullet(position, direction, self.bullet_speed, self))
            return True
        return False

    def render(self, surface, camera, player):
        if player:
            for bullet in self.bullets.bullets:
                bullet.render(surface, camera)

    def update(self, tilemap, enemies=None, players=None):
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)

        for bullet in self.bullets.bullets:
            bullet.update(tilemap, enemies=enemies, players=players)

class FreezerGun(EnemyGunInterface):
    def __init__(self, game):
        super().__init__(
            game=game,
            type='freezer',
            bullet_damage=ENEMY_GUNS['freezer']['bullet_damage'],
            bullet_speed=ENEMY_GUNS['freezer']['bullet_speed'],
            fire_rate=ENEMY_GUNS['freezer']['fire_rate']
        )
        try:
            self.bullet_image = self.game.gun_assets['guns_bullets']['freezer']
        except Exception as e:
            pass

    def shoot(self, direction):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.fire_rate
            position = Position(self.rect.centerx, self.rect.centery)
            self.bullets.add_bullet(FreezeBullet(position, direction, self.bullet_speed, self))
            return True
        return False

class SimpleGun(EnemyGunInterface):
    def __init__(self, game):
        super().__init__(
            game=game,
            type='simple_gun',
            bullet_damage=ENEMY_GUNS['simple_gun']['bullet_damage'],
            bullet_speed=ENEMY_GUNS['simple_gun']['bullet_speed'],
            fire_rate=ENEMY_GUNS['simple_gun']['fire_rate']
        )
        try:
            self.bullet_image = self.game.gun_assets['guns_bullets']['simple']
        except Exception as e:
            pass

    def shoot(self, direction):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.fire_rate
            position = Position(self.rect.centerx, self.rect.centery)
            self.bullets.add_bullet(EnemySimpleBullet(position, direction, self.bullet_speed, self))
            return True
        return False

class BlinderGun(EnemyGunInterface):
    def __init__(self, game):
        super().__init__(
            game=game,
            type='blinder_gun',
            bullet_damage=ENEMY_GUNS['blinder_gun']['bullet_damage'],
            bullet_speed=ENEMY_GUNS['blinder_gun']['bullet_speed'],
            fire_rate=ENEMY_GUNS['blinder_gun']['fire_rate']
        )
        try:
            self.bullet_image = self.game.gun_assets['guns_bullets']['blinder']
        except Exception as e:
            pass

    def shoot(self, direction):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.fire_rate
            position = Position(self.rect.centerx, self.rect.centery)
            self.bullets.add_bullet(EnemyBlindingBullet(position, direction, self.bullet_speed, self))
            return True
        return False

class Magazine:
    def __init__(self, capacity, total_ammo):
        self.capacity = capacity
        self.total_ammo = total_ammo
        self.ammo = min(capacity, total_ammo)
        self.total_ammo = max(0, total_ammo - self.ammo)

    def reload(self) -> bool:
        if self.total_ammo > 0:
            ammo_needed = self.capacity - self.ammo
            if ammo_needed > 0:
                ammo_to_reload = min(ammo_needed, self.total_ammo)
                self.ammo += ammo_to_reload
                self.total_ammo -= ammo_to_reload
                return True
        return False
    
    def decrease_ammo(self, amount):
        if amount < 0:
            raise ValueError("Amount to decrease cannot be negative.")
        self.ammo = max(0, self.ammo - amount)

    @property
    def snapshot(self):
        return {
            "ammo": self.ammo,
            "total_ammo": self.total_ammo
        }
    
    def apply_snapshot(self, snapshot):
        if 'ammo' in snapshot:
            self.ammo = snapshot['ammo']
        if 'total_ammo' in snapshot:
            self.total_ammo = snapshot['total_ammo']

class GunInterface:
    def __init__(self, game, type, magazine_capacity, total_ammo, fire_rate, bullet_speed, bullet_damage, ammo_reduction, total_reload_time, flip_direction = False):
        self.game = game
        self.type = type
        self.sound_manager = SoundManager()
        try:
            self.sound_manager.add_sfx('shoot',load_sound('Shoot.mp3'), 0.05)
            self.sound_manager.add_sfx('reload',load_sound('Reload.mp3'), 0.18)
        except Exception as e:
            pass
        self.magazine_capacity = magazine_capacity
        self.total_ammo = total_ammo
        self.magazine = Magazine(magazine_capacity, total_ammo)
        self.ammo_reduction = ammo_reduction
        self.total_reload_time = total_reload_time
        self.reload_time = 0

        self.fire_rate = fire_rate
        self.shoot_cooldown = 0
        self.bullet_speed = bullet_speed
        self.original_bullet_speed = self.bullet_speed
        self.bullet_damage = bullet_damage
        self.original_bullet_damage = self.bullet_damage
        
        self.bullets = Bullets()
        try:
            self.gun_image = pygame.transform.smoothscale_by(self.game.gun_assets['guns'][self.type], 0.8)
            self.gun_surf = self.gun_image
            self.bullet_image = self.game.gun_assets['guns_bullets'][self.type]
            self.rect = self.gun_image.get_rect()
        except Exception as e:
            pass

        self.flip_direction = flip_direction

    def shoot(self, direction=None, index=0, player_team_id=None):
        if self.magazine.ammo > 0 and self.shoot_cooldown == 0 and self.reload_time == 0:
            self.shoot_cooldown = self.fire_rate

            if self.flip_direction:
                direction = -direction

            direction_vec = direction.normalize()
            gun_center = pygame.Vector2(self.rect.centerx, self.rect.centery)
            barrel_length = max(self.rect.width, self.rect.height) * 0.7  # tweak if needed
            barrel_tip = gun_center + direction_vec * barrel_length
            position = Position(barrel_tip.x, barrel_tip.y)

            self.bullets.add_bullet(Bullet(position, direction, self.bullet_speed, self, team_id=player_team_id))

            angle_deg = math.degrees(math.atan2(direction.y, direction.x))
            try:
                self.game.particle_manager.add_particle(
                    p_type=self.type,
                    pos=position,
                    velocity=direction * 2,
                    frame=0,
                    angle=angle_deg
                )
            except Exception as e:
                pass
            self.magazine.ammo -= self.ammo_reduction
            try:
                self.sound_manager.play_sfx('shoot')
            except Exception as e:
                pass
        elif self.magazine.ammo <= 0:
            self.reload()

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()
        self.bullets.stop_all_sfx()

    def reload(self):
        reloaded = self.magazine.reload()
        if reloaded:
            self.reload_time = self.total_reload_time
            try:
                self.sound_manager.play_sfx('reload')
            except Exception as e:
                pass
        return reloaded

    def update(self, tilemap, enemies=None, players=None, player=None):
        self.sound_manager.sfx['shoot'].set_volume(0.05)
        self.sound_manager.sfx['reload'].set_volume(0.18)
        self.reload_time = max(0, self.reload_time - 1)
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)

        for bullet in self.bullets.bullets:
            try:
                bullet.update(tilemap, enemies=enemies, players=players, boss=self.game.level.BOSS)
            except:
                bullet.update(tilemap, enemies=enemies, players=players)

        player_rect = player.rect()
        self.rect.center = player_rect.center + self._get_direction(player) * ((player.size[1] + player.size[0])/2)
        try:
            if self._get_direction(player) == pygame.Vector2(0, 1) or self._get_direction(player) == pygame.Vector2(0, -1):
                self.rect.x += 3
                self.rect.y = self.rect.y - self.gun_image.get_height() / 2 if self._get_direction(player) == pygame.Vector2(0, -1) else self.rect.y
        except Exception as e:
            pass
        self._rotate_gun(player)

    def _get_direction(self, player):
        if player.index > 0 and not player.GNetwork:
            out_put = pygame.Vector2(1, 0) if not player.animation_manager.flip else pygame.Vector2(-1, 0)
            return -out_put if self.flip_direction else out_put 

        player_point = pygame.Vector2((player.position - self.game.camera.render_scroll).tuple())
        raw_vector = (player.controller.mouse_pos_vector2 - player_point).normalize()

        angle = math.degrees(math.atan2(raw_vector.y, raw_vector.x))

        snapped_angle = round(angle / 45) * 45
        radians = math.radians(snapped_angle)
        snapped_vector = pygame.Vector2(math.cos(radians), math.sin(radians)).normalize()

        return -snapped_vector if self.flip_direction else snapped_vector
    
    def _rotate_gun(self, player):
        direction = self._get_direction(player)
        angle = math.degrees(math.atan2(direction.x, direction.y)) - 90
        try:
            if direction.x > 0:
                self.gun_image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
            else:
                self.gun_image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
                self.gun_image = pygame.transform.flip(self.gun_image, False, True)
        except Exception as e:
            pass
    
    def clear_bullets(self):
        self.bullets.clear()

    def render(self, surface, camera, player):
        if player:
            for bullet in self.bullets.bullets:
                bullet.render(surface, camera)

            if player.animation_manager.action != 'death' and player.animation_manager.action != 'wall_slide':
                
                draw_x = self.rect.x - camera.render_scroll.x
                draw_y = self.rect.y - camera.render_scroll.y
                
                surface.blit(self.gun_image, (draw_x, draw_y))

    def render_bullets(self, surface, camera):
        for bullet in self.bullets.bullets:
            bullet.render(surface, camera)

    @property
    def snapshot(self):
        return {
            "type": self.type,
            "magazine": self.magazine.snapshot,
            'bullet_damage': self.bullet_damage,
            'bullet_speed': self.bullet_speed,
        }
    
    def apply_snapshot(self, snapshot):
        if 'type' in snapshot:
            self.type = snapshot['type']
        if 'magazine' in snapshot:
            self.magazine.apply_snapshot(snapshot['magazine'])
        if 'bullet_damage' in snapshot:
            self.bullet_damage = snapshot['bullet_damage']
        if 'bullet_speed' in snapshot:
            self.bullet_speed = snapshot['bullet_speed']

    def reset_gun(self):
        self.bullet_damage = self.original_bullet_damage
        self.bullet_speed = self.original_bullet_speed
        self.magazine = Magazine(self.magazine_capacity, self.total_ammo)
        self.shoot_cooldown = 0

class Revolver(GunInterface):
    def __init__(self, game, flip_direction = False):
        super().__init__(
            game=game,
            type='revolver',
            magazine_capacity=PLAYER_WEAPONS_CONFIG['revolver']['magazine_capacity'],
            total_ammo=PLAYER_WEAPONS_CONFIG['revolver']['total_ammo'],
            fire_rate=PLAYER_WEAPONS_CONFIG['revolver']['fire_rate'],
            bullet_speed=PLAYER_WEAPONS_CONFIG['revolver']['bullet_speed'],
            bullet_damage=PLAYER_WEAPONS_CONFIG['revolver']['bullet_damage'],
            ammo_reduction=PLAYER_WEAPONS_CONFIG['revolver']['ammo_reduction'],
            total_reload_time=PLAYER_WEAPONS_CONFIG['revolver']['total_reload_time'],
            flip_direction=flip_direction
        )

class Colt(GunInterface):
    def __init__(self, game, flip_direction = False):
        super().__init__(
            game=game,
            type='colt',
            magazine_capacity=PLAYER_WEAPONS_CONFIG['colt']['magazine_capacity'],
            total_ammo=PLAYER_WEAPONS_CONFIG['colt']['total_ammo'],
            fire_rate=PLAYER_WEAPONS_CONFIG['colt']['fire_rate'],
            bullet_speed=PLAYER_WEAPONS_CONFIG['colt']['bullet_speed'],
            bullet_damage=PLAYER_WEAPONS_CONFIG['colt']['bullet_damage'],
            ammo_reduction=PLAYER_WEAPONS_CONFIG['colt']['ammo_reduction'],
            total_reload_time=PLAYER_WEAPONS_CONFIG['colt']['total_reload_time'],
            flip_direction=flip_direction
        )

class DuaColt:
    def __init__(self, game):
        self.game = game
        self.type = 'dua_colt'
        self.right_colt = Colt(game)
        self.left_colt = Colt(game, flip_direction=True)

    def update(self, tilemap, enemies=None, players=None, player=None):
        self.right_colt.update(tilemap, enemies=enemies, players=players, player=player)
        self.left_colt.update(tilemap, enemies=enemies, players=players, player=player)

    def shoot(self, direction, index = 0, player_team_id=None):
        if index >= 1:
            self.right_colt.shoot(direction, index-1, player_team_id=player_team_id)
            self.left_colt.shoot(direction, index-1, player_team_id=player_team_id)
        else:
            self.right_colt.shoot(direction, index, player_team_id=player_team_id)
            self.left_colt.shoot(direction, index, player_team_id=player_team_id)

    def clear_bullets(self):
        self.right_colt.clear_bullets()
        self.left_colt.clear_bullets()

    def reload(self):
        reloaded = self.right_colt.reload() or self.left_colt.reload()
        return reloaded

    def render(self, surface, camera, player):
        self.right_colt.render(surface, camera, player)
        self.left_colt.render(surface, camera, player)

    def render_bullets(self, surface, camera):
        self.right_colt.render_bullets(surface, camera)
        self.left_colt.render_bullets(surface, camera)

    def stop_all_sfx(self):
        self.right_colt.stop_all_sfx()
        self.left_colt.stop_all_sfx()

    @property
    def snapshot(self):
        return {
            "type": self.type,
            "right_colt": self.right_colt.snapshot,
            "left_colt": self.left_colt.snapshot
        }
    
    def apply_snapshot(self, snapshot):
        if 'type' in snapshot:
            self.type = snapshot['type']
        if 'right_colt' in snapshot:
            self.right_colt.apply_snapshot(snapshot['right_colt'])
        if 'left_colt' in snapshot:
            self.left_colt.apply_snapshot(snapshot['left_colt'])

    def reset_gun(self):
        self.right_colt.reset_gun()
        self.left_colt.reset_gun()

class M95(GunInterface):
    def __init__(self, game):
        super().__init__(
            game=game,
            type='m95',
            magazine_capacity=PLAYER_WEAPONS_CONFIG['m95']['magazine_capacity'],
            total_ammo=PLAYER_WEAPONS_CONFIG['m95']['total_ammo'],
            fire_rate=PLAYER_WEAPONS_CONFIG['m95']['fire_rate'],
            bullet_speed=PLAYER_WEAPONS_CONFIG['m95']['bullet_speed'],
            bullet_damage=PLAYER_WEAPONS_CONFIG['m95']['bullet_damage'],
            ammo_reduction=PLAYER_WEAPONS_CONFIG['m95']['ammo_reduction'],
            total_reload_time=PLAYER_WEAPONS_CONFIG['m95']['total_reload_time']
        )

class Shotgun(GunInterface):
    def __init__(self, game):
        super().__init__(
            game=game,
            type='shotgun',
            magazine_capacity=PLAYER_WEAPONS_CONFIG['shotgun']['magazine_capacity'],
            total_ammo=PLAYER_WEAPONS_CONFIG['shotgun']['total_ammo'],
            fire_rate=PLAYER_WEAPONS_CONFIG['shotgun']['fire_rate'],
            bullet_speed=PLAYER_WEAPONS_CONFIG['shotgun']['bullet_speed'],
            bullet_damage=PLAYER_WEAPONS_CONFIG['shotgun']['bullet_damage'],
            ammo_reduction=PLAYER_WEAPONS_CONFIG['shotgun']['ammo_reduction'],
            total_reload_time=PLAYER_WEAPONS_CONFIG['shotgun']['total_reload_time']
        )
        self.gun_image = pygame.transform.smoothscale_by(self.game.gun_assets['guns'][self.type], 0.5)
        self.gun_surf = self.gun_image
        self.bullet_image = self.game.gun_assets['guns_bullets'][self.type]
        self.rect = self.gun_image.get_rect()

    def shoot(self, direction, index=0, player_team_id=None):
        if self.magazine.ammo > 0 and self.shoot_cooldown == 0 and self.reload_time == 0:
            self.shoot_cooldown = self.fire_rate

            if self.flip_direction:
                direction = -direction

            direction_vec = direction.normalize()
            gun_center = pygame.Vector2(self.rect.centerx, self.rect.centery)
            barrel_length = max(self.rect.width, self.rect.height) * 0.8
            barrel_tip = gun_center + direction_vec * barrel_length
            position = Position(barrel_tip.x, barrel_tip.y)

            base_angle = math.atan2(direction.y, direction.x)
            spread_degrees = [-5, 0, 5]

            for deg in spread_degrees:
                angle = base_angle + math.radians(deg)
                spread_dir = pygame.Vector2(math.cos(angle), math.sin(angle)).normalize()
                self.bullets.add_bullet(Bullet(position.copy(), spread_dir, self.bullet_speed, self, team_id=player_team_id))

            angle_deg = math.degrees(math.atan2(direction.y, direction.x))
            try:
                self.game.particle_manager.add_particle(
                    p_type=self.type,
                    pos=position,
                    velocity=direction_vec * 2,
                    frame=0,
                    angle=angle_deg
                )
            except Exception as e:
                pass
            try:
                self.sound_manager.play_sfx('shoot')
            except Exception as e:
                pass
            self.magazine.ammo -= self.ammo_reduction
        elif self.magazine.ammo <= 0:
            self.reload()

