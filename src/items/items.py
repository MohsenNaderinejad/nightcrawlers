from src.utils import *
from src.entities.status import *
import random
import pygame
from src.engine.sound import SoundManager
import time
class Items:
    def __init__(self, level):
        self.spawn_time = 0
        self.level = level
        self.item_can_be_spawned = True

        self.max_items_spawned = 3
        self.items_spawned = 0
        self.items = []

        # Item types with their respective spawn chances ---> Total chance = 100%
        bullet_items = [Bullet_items] * (37 * 2 - 1) # 73 in 200
        heal_items = [Heal_items] * (28 * 2 - 1) # 55 in 200
        shield_items = [Shield_items] * (15 * 2 - 1) # 29 in 200
        jump_items = [Jump_items] * (10 * 2 - 1) # 19 in 200
        more_damage = [More_damage] * (10 * 2 - 1) # 19 in 200
        hp_increase = [HP_Increase] * 2 # 2 in 200
        mp_increase = [MP_Increase] * 3 # 3 in 200
        # bullet_items + heal_items + shield_items + jump_items + more_damage + hp_increase + mp_increase
        self.item_type = bullet_items + heal_items + shield_items + jump_items + more_damage + hp_increase + mp_increase
        self.new_delay_time()
        self.last_item_removed = time.perf_counter()

        self.item_positions = dict()
        
        try:
            self.sound_manager = SoundManager()
            self.sound_manager.add_sfx('Grab',load_sound('PickUp.wav'), 0.065)
            self.sound_manager.add_sfx('item_apear', self.level.Game.sounds['item_apear'], 0.065)
            self.sound_manager.add_sfx('item_destruction', self.level.Game.sounds['item_destruction'], 0.065)
        except Exception as e:
            pass

        self.basic_snapshot = {
            'delay_time': self.delay_time,
            'last_item_spawned': self.last_item_spawned,
        }
        self.server_time = time.perf_counter()
        self.took_items = list()

    def clear(self):
        del self.item_positions
        del self.items
        self.item_positions = dict()
        self.items = []
        self.items_spawned = 0

    def new_delay_time(self):
        self.delay_time = random.randrange(10000, 15001, 2500) / 1000.0  # Random delay between 10 and 15 seconds
        self.last_item_spawned = time.perf_counter()
        self.basic_snapshot = {
            'delay_time': self.delay_time,
            'last_item_spawned': self.last_item_spawned, 
        }

    def extract_items_position(self):
        self.item_positions = {}
        for item in self.level.tilemap.extract_tile_by_pair([('item', 0), ('item', 1), ('item', 2), ('item', 3), ('item', 4), ('item', 5), ('item', 6)], keep=False):
            self.item_positions[item.position] = True

    def choice_random(self):
        players = self.level.players.get_players()
        avg_x = sum([p.position.x for p in players]) / len(players)
        avg_y = sum([p.position.y for p in players]) / len(players)
        avg_pos = Position(avg_x, avg_y)
        self.item_chosen = random.choice(self.item_type)
        self.item_valid_positions = [pos for pos in self.item_positions if self.item_positions[pos]]
        if not self.item_valid_positions:
            return
        self.item_chosen_pos = min(
            self.item_valid_positions,
            key=lambda pos: (pos.x - avg_pos.x) ** 2 + (pos.y - avg_pos.y) ** 2
        )
        self.item_positions[self.item_chosen_pos] = False

        if self.item_chosen == Bullet_items:
            item = Bullet_items(self.item_chosen_pos, self.level)
        if self.item_chosen == Shield_items:
            item = Shield_items(self.item_chosen_pos, self.level)
        if self.item_chosen == Jump_items:
            item = Jump_items(self.item_chosen_pos, self.level)
        if self.item_chosen == Heal_items:
            item = Heal_items(self.item_chosen_pos, self.level)
        if self.item_chosen == More_damage:
            item = More_damage(self.item_chosen_pos, self.level)
        if self.item_chosen == HP_Increase:
            item = HP_Increase(self.item_chosen_pos, self.level)
        if self.item_chosen == MP_Increase:
            item = MP_Increase(self.item_chosen_pos, self.level)

        item.spawn_time = time.perf_counter()
        self.items.append(item)
        self.new_delay_time()
        self.items_spawned += 1
        try:
            self.level.Game.particle_manager.add_particle('item_loading', self.item_chosen_pos + Position(item.image.get_width() // 2, item.image.get_height() // 2))
            self.sound_manager.play_sfx('item_apear')
        except Exception as e:
            pass
        if self.items_spawned >= self.max_items_spawned:
            self.item_can_be_spawned = False

    def remove_item(self, index, self_destruct=True):
        if not self_destruct:
            self.took_items.append({
                'x': self.items[index].position.x,
                'y': self.items[index].position.y
            })
        item_center = self.items[index].position + Position(self.items[index].image.get_width() // 2, self.items[index].image.get_height() // 2)
        self.item_positions[self.items[index].position] = True
        del self.items[index]
        self.last_item_removed = time.perf_counter()
        self.items_spawned -= 1
        if self.items_spawned < self.max_items_spawned:
            self.item_can_be_spawned = True
        try:
            if self_destruct:
                self.level.Game.particle_manager.add_particle('item_destroyed', item_center)
                self.sound_manager.play_sfx('item_destruction')
            else:
                self.level.Game.particle_manager.add_particle('item_eating', item_center)
                self.sound_manager.play_sfx('Grab')
        except Exception as e:
            pass

    def stop_all_sfx(self):
        self.sound_manager.stop_all_sfx()

    def delete_item_after_collision(self, item):
        if item in self.items:
            player = self.level.players[item.item_owner]
            player.HP_increased = False
            player.MP_increased = False
            if item.e_type == 0: # AMMO ADDING
                if player.arsenal.current_gun.type == 'dua_colt':
                    player.arsenal.current_gun.right_colt.magazine.total_ammo += player.arsenal.current_gun.right_colt.magazine.capacity * 3
                    player.arsenal.current_gun.left_colt.magazine.total_ammo += player.arsenal.current_gun.left_colt.magazine.capacity * 3
                else:
                    player.arsenal.current_gun.magazine.total_ammo += player.arsenal.current_gun.magazine.capacity * 3

            if item.e_type == 1: # SHIELD
                player.time_shield = time.perf_counter()
                player.have_shield = True
                player.SHIELD = Status(random.choice([25, 50, 75]))
                player.shield_max_time = random.choice([7.500, 10.000])
                player.partitioned_shield_bar_frame = player.SHIELD.max_value / (player.shield_length_bar - 1)

            if item.e_type == 2: # DOUBLE JUMP
                player.double_jump_time = time.perf_counter()
                player.max_jump_time = random.choice([2, 3])
                player.double_jump_max_time = random.choice([5.000, 7.500, 10.000])

            if item.e_type == 3: # HP ADDING
                player.HP.actual_value = min(player.HP.actual_value + 30, player.HP.max_value)

            if item.e_type == 4: # MORE DAMAGE
                if not player.bullet_damage_increased:
                    if player.arsenal.current_gun.type == 'dua_colt':
                        player.arsenal.current_gun.right_colt.bullet_damage += int(player.arsenal.current_gun.right_colt.bullet_damage * 0.1)
                        player.arsenal.current_gun.left_colt.bullet_damage += int(player.arsenal.current_gun.left_colt.bullet_damage * 0.1)
                    else:
                        player.arsenal.current_gun.bullet_damage += int(player.arsenal.current_gun.bullet_damage * 0.2)
                    player.bullet_damage_increased = True
                    player.bullet_damage_time = time.perf_counter()

            if item.e_type == 5: # HP INCREASE
                player.hp_increase_amount = random.choice([10, 20, 25, 35])
                player.HP.change_max(player.hp_increase_amount + player.HP.max_value)
                player.HP_increased = True
                try:
                    player.partitioned_health_bar_frame = player.HP.max_value / (len(player.game.ui_assets['player_health_bar']) - 1)
                except Exception as e:
                    player.partitioned_health_bar_frame = player.HP.max_value / 38

            if item.e_type == 6: # MP INCREASE
                player.mp_increase_amount = random.choice([10, 20, 30])
                player.MP.change_max(player.mp_increase_amount + player.MP.max_value)
                player.MP_increased = True
                try:
                    player.partitioned_mana_bar_frame = player.MP.max_value / (len(player.game.ui_assets['player_mana_bar']) - 1)
                except Exception as e:
                    player.partitioned_mana_bar_frame = player.MP.max_value / 38

            index = self.items.index(item)
            self.remove_item(index, False)

    def update(self):
        self.sound_manager.set_sfx_volume(0.065)
        if time.perf_counter() * 2 - self.last_item_spawned  - self.last_item_removed > self.delay_time and self.item_can_be_spawned \
            and self.items_spawned < self.max_items_spawned:
            self.choice_random()
        for item in self.items:
            index = self.items.index(item)
            if (time.perf_counter() - item.spawn_time) > 7.500:
                self.remove_item(index)
                self.item_can_be_spawned = True
            if item.check_collision():
                self.item_can_be_spawned = True
                self.delete_item_after_collision(item)

    def render(self, screen, camera):
        for item in self.items:
            item_pos = (item.rrect().x - camera.render_scroll.x, item.rrect().y - camera.render_scroll.y)
            screen.blit(item.image, item_pos)

    def updateClient(self):
        for item in self.items:
            index = self.items.index(item)
            if (self.server_time - item.spawn_time) > 7.500:
                self.remove_item(index)

    @property
    def snapshot(self):
        tmp_took_items = self.took_items.copy()
        # print('[ITEMS] Took items:', tmp_took_items)
        self.took_items = list()  # Reset took_items after snapshot to avoid duplication
        # we have basic snapshot
        snapshot = {
            "PUs": {
                "items": [],
                **self.basic_snapshot,  # Include the basic snapshot data
                'server_time': time.perf_counter(),
                'took_items': tmp_took_items,  # Include the took items
            }
        }
        for item in self.items:
            if item.item_snapped:
                continue
            item_data = {
                "position": {
                    "x": item.position.x,
                    "y": item.position.y
                },
                "variant": item.variant,
                "spawn_time": item.spawn_time,
            }
            snapshot['PUs']["items"].append(item_data)
            item.item_snapped = True
        return snapshot
    
    def apply_snapshot(self, snapshot):
        self.server_time = snapshot.get("server_time", self.server_time)
        self.last_item_spawned = snapshot.get("last_item_spawned", self.last_item_spawned)
        self.delay_time = snapshot.get("delay_time", self.delay_time)
        for item_data in snapshot.get("items", []):
            position = item_data.get("position")
            variant = item_data.get("variant")
            spawn_time = item_data.get("spawn_time", None)
            position = Position(position["x"], position["y"]) if position else Position(0, 0)
            item = Item(position, self.level, variant, spawn_time=spawn_time)
            self.items.append(item)
            try:
                self.level.Game.particle_manager.add_particle('item_loading', position + Position(item.image.get_width() // 2, item.image.get_height() // 2))
                self.sound_manager.play_sfx('item_apear')
            except Exception as e:
                pass
        for took_item_data in snapshot.get("took_items", []):
            position = Position(took_item_data["x"], took_item_data["y"]) if took_item_data else Position(0, 0)
            for item in self.items:
                if item.position == position:
                    self.remove_item(self.items.index(item), self_destruct=False)
                    break
        self.took_items = list()

class Item():
    def __init__(self, position:Position, level, variant = 0, spawn_time=None):
        self.position = position
        self.variant = variant
        self.e_type = variant
        self.level = level
        self.item_owner = None
        self.spawn_time = time.perf_counter() if spawn_time is None else spawn_time
        self.item_snapped = False
        try:
            self.image = self.level.Game.assets['item'][variant]
        except Exception as e:
            pass

    def check_collision(self):
        for index in range(len(self.level.players.get_players())):
            if self.rrect().colliderect(self.level.players[index].rect()):
                self.item_owner = index
                return True
        return False

    def rrect(self):
       return pygame.rect.Rect(self.position.x, self.position.y, self.image.get_width(), self.image.get_height())


class Bullet_items(Item):
    def __init__(self, position:Position, level):
        super().__init__(position, level, 0)

class Shield_items(Item):
    def __init__(self,position:Position ,level):
        super().__init__(position, level, 1)

class Jump_items(Item):
    def __init__(self,position:Position,level):
        super().__init__(position, level, 2)

class Heal_items(Item):
    def __init__(self,position:Position,level):
        super().__init__(position, level, 3)

class More_damage(Item):
    def __init__(self,position:Position,level):
        super().__init__(position, level, 4)

class HP_Increase(Item):
    def __init__(self, position:Position, level):
        super().__init__(position, level, 5)

class MP_Increase(Item):
    def __init__(self, position:Position, level):
        super().__init__(position, level, 6)