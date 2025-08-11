import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from src.engine.cameras import Camera
from src.engine.sound import SoundManager

class Bullet:
    def __init__(self, position: Position, direction: Position, speed, gun, whom = '', team_id=None):
        self.sound_manager = SoundManager()
        try:
            self.sound_manager.set_sfx_volume(0.35)
            self.sound_manager.add_sfx('active',load_sound('Simple.wav'))
            self.sound_manager.add_sfx('hurt',load_sound('Hurt.wav'))
        except Exception as e:
            pass
        self.direction = direction
        self.gun = gun
        if whom != 'enemy':
            self.rect = self.gun.bullet_image.get_rect(center=position.tuple())
        else:
            self.rect = None
        self.velocity = self.direction * speed
        self.air_time = 0
        self.max_air_time = 360
        self.max_frame_count = 0
        self.frame_count = 0
        self.collisionable = True
        self.whom=whom
        self.team_id = team_id
        if whom == 'player':
            self.max_frame_count = 25

    def kill(self):
        self.gun.bullets.remove_bullet(self)
        try:
            self.gun.game.particle_manager.add_particle('bullet_collision', Position(self.rect.centerx, self.rect.centery))
        except Exception as e:
            pass

    def update(self, tilemap, enemies=None, players=None, boss=None):
        try:
            self.sound_manager.set_sfx_volume(0.35)
        except Exception as e:
            pass
        self.frame_count = min(self.frame_count + 1, self.max_frame_count)
        if self.frame_count == self.max_frame_count:
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            self.air_time += 1
            if self.air_time > self.max_air_time:
                self.kill()

            if self.collisionable:
                for tile in tilemap.physics_tiles_rect(Position(self.rect.x, self.rect.y)):
                    if self.rect.colliderect(tile):
                        try:
                            self.sound_manager.play_sfx('active')
                        except Exception as e:
                            pass
                        self.kill()
                        break

            for player in players:
                hitable = True
                if self.team_id is not None:
                    hitable = player.group_number != self.team_id
                if player.rect().colliderect(self.rect) and not player.HP.check() and hitable:
                    try:
                        self.sound_manager.play_sfx('hurt')
                    except Exception as e:
                        pass
                    player.hp_reduction(self.gun.bullet_damage)
                    player.HP_time = 120
                    player.hurt = True
                    self.kill()
                    break
            if enemies:
                for enemy in enemies:
                    if enemy.rect().colliderect(self.rect) and not enemy.HP.check():
                        try:
                            self.sound_manager.play_sfx('hurt')
                        except Exception as e:
                            pass
                        enemy.HP.decrease(self.gun.bullet_damage)
                        enemy.HP_time = 120
                        enemy.hurt = True
                        self.kill()
                        break

            if boss and not boss.invincible:
                if boss.rect().colliderect(self.rect) and not boss.HP.check():
                    try:
                        self.sound_manager.play_sfx('hurt')
                    except Exception as e:
                        pass
                    boss.hp_reduction(self.gun.bullet_damage)
                    self.kill()
        

    def render(self, surface, camera: Camera):
        if self.frame_count == self.max_frame_count:
            draw_x = self.rect.x - camera.render_scroll.x
            draw_y = self.rect.y - camera.render_scroll.y
            surface.blit(self.gun.bullet_image, (draw_x, draw_y))

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()

class FreezeBullet(Bullet):
    def __init__(self, position: Position, direction: Position, speed, gun, whom='enemy'):
        super().__init__(position, direction, speed, gun, whom)
        self.collisionable = True
        self.rect = self.gun.bullet_image.get_rect(center=position.tuple())

        self.sound_manager.add_sfx('active',load_sound('Freezer.wav'))

    def update(self, tilemap, enemies=None, players=None):
        self.sound_manager.set_sfx_volume(0.35)
        self.frame_count = min(self.frame_count + 1, self.max_frame_count)
        if self.frame_count == self.max_frame_count:
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            self.air_time += 1
            if self.air_time > self.max_air_time:
                self.kill()

            if self.collisionable:
                for tile in tilemap.physics_tiles_rect(Position(self.rect.x, self.rect.y)):
                    if self.rect.colliderect(tile):
                        self.sound_manager.play_sfx('active')
                        self.kill()
                        break

            for player in players:
                if player.rect().colliderect(self.rect) and not player.HP.check() and not player.invincible:
                    self.sound_manager.play_sfx('active')
                    player.hp_reduction(self.gun.bullet_damage)
                    player.freeze()
                    player.HP_time = 120
                    self.kill()
                    break

class EnemySimpleBullet(Bullet):
    def __init__(self, position: Position, direction: Position, speed, gun, whom='enemy'):
        super().__init__(position, direction, speed, gun)
        self.collisionable = True
        self.rect = self.gun.bullet_image.get_rect(center=position.tuple())

    def update(self, tilemap, enemies=None, players=None):
        self.sound_manager.set_sfx_volume(0.35)
        self.frame_count = min(self.frame_count + 1, self.max_frame_count)
        if self.frame_count == self.max_frame_count:
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            self.air_time += 1
            if self.air_time > self.max_air_time:
                self.kill()

            if self.collisionable:
                for tile in tilemap.physics_tiles_rect(Position(self.rect.x, self.rect.y)):
                    if self.rect.colliderect(tile):
                        self.sound_manager.play_sfx('active')
                        self.kill()
                        break

            for player in players:
                if player.rect().colliderect(self.rect) and not player.HP.check() and not player.invincible:
                    self.sound_manager.play_sfx('hurt')
                    player.hp_reduction(self.gun.bullet_damage)
                    player.HP_time = 120
                    player.hurt = True
                    self.kill()
                    break

class EnemyBlindingBullet(Bullet):
    def __init__(self, position: Position, direction: Position, speed, gun, whom='enemy'):
        super().__init__(position, direction, speed, gun)
        self.collisionable = True
        self.rect = self.gun.bullet_image.get_rect(center=position.tuple())
        self.max_blindness_frame = 300

        self.sound_manager.add_sfx('active',load_sound('Blinder.wav'), 0.1)

    def update(self, tilemap, enemies=None, players=None):
        self.sound_manager.set_sfx_volume(0.35)
        self.frame_count = min(self.frame_count + 1, self.max_frame_count)
        if self.frame_count == self.max_frame_count:
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            self.air_time += 1
            if self.air_time > self.max_air_time:
                self.kill()

            if self.collisionable:
                for tile in tilemap.physics_tiles_rect(Position(self.rect.x, self.rect.y)):
                    if self.rect.colliderect(tile):
                        self.kill()
                        break

            for player in players:
                if player.rect().colliderect(self.rect) and not player.HP.check():
                    self.sound_manager.play_sfx('active')
                    player.blindness_frame_count = self.max_blindness_frame
                    self.kill()
                    break

class Bullets:
    def __init__(self):
        self.bullets = list()

    def add_bullet(self, bullet):
        self.bullets.append(bullet)

    def remove_bullet(self, bullet):
        if bullet in self.bullets:
            self.bullets.remove(bullet)

    def clear(self):
        del self.bullets
        self.bullets = list()

    def update(self, tilemap, enemies=None, players=None):
        for bullet in self.bullets:
            bullet.update(tilemap, enemies, players)

    def render(self, surface, camera):
        for bullet in self.bullets:
            bullet.render(surface, camera)

    def stop_all_sfx(self):
        for bullet in self.bullets:
            bullet.stop_all_sfx()