import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *
from config import *
from src.items.gun import Colt, Shotgun, DuaColt, Revolver, M95
from src.engine.sound import SoundManager

class Arsenal:
    def __init__(self, player):
        self.sound_manager = SoundManager()
        self.sound_manager.set_sfx_volume(0.05)
        self.sound_manager.add_sfx('Switch',load_sound('Switch.wav'))
        self.player = player
        self.guns = []
        self.guns_available_for_player = []
        self.current_gun = None

    def add_gun_available_for_player(self, gun_type):
        if gun_type in PLAYER_WEAPONS:
            self.guns_available_for_player.append(gun_type)
        else:
            raise ValueError(f"Gun type '{gun_type}' is not available in the arsenal.")

    def add_gun(self, gun_type):
        if gun_type in PLAYER_WEAPONS and gun_type in self.guns_available_for_player:
            if gun_type == 'colt':
                gun = Colt(self.player.game)
            elif gun_type == 'shotgun':
                gun = Shotgun(self.player.game)
            elif gun_type == 'dua_colt':
                gun = DuaColt(self.player.game)
            elif gun_type == 'revolver':
                gun = Revolver(self.player.game)
            elif gun_type == 'm95':
                gun = M95(self.player.game)
            else:
                raise ValueError(f"Gun type '{gun_type}' is not recognized.")
            self.guns.append(gun)
            if self.current_gun is None:
                self.current_gun = gun
        else:
            raise ValueError(f"Gun type '{gun_type}' is not available in the arsenal.")

    def switch_gun(self):
        if self.guns:
            self.sound_manager.play_sfx('Switch')
            current_index = self.guns.index(self.current_gun)
            next_index = (current_index + 1) % len(self.guns)
            self.current_gun = self.guns[next_index]
        else:
            raise ValueError("No guns available in the arsenal to switch.")

    def clear_bullets(self):
        for gun in self.guns:
            gun.clear_bullets()

    def update(self, tilemap, enemies=None, players=None):
        try:
            self.sound_manager.set_sfx_volume(0.05)
        except Exception as e:
            pass
        if self.current_gun:
            self.current_gun.update(tilemap, enemies=enemies, players=players, player=self.player)
        for gun in self.guns:
            if gun != self.current_gun:
                gun.update(tilemap, enemies=enemies, players=players, player=self.player)
    
    def stop_all_sfx(self):
        for gun in self.guns:
            gun.stop_all_sfx()

    def render(self, surface, camera):
        if self.current_gun:
            self.current_gun.render(surface, camera, self.player)
        for gun in self.guns:
            if gun != self.current_gun:
                gun.render_bullets(surface, camera)

    def default_gun(self):
        if not self.current_gun and len(self.guns) >= 1:
            self.current_gun = self.guns[0]

    def remove_gun(self, gun):
        if gun in self.guns:
            del self.guns[gun]
        else:
            raise ValueError(f"Gun '{gun}' is not in the arsenal.")
        
    def unequip_gun(self):
        self.current_gun = None

    def reset_guns(self):
        for gun in self.guns:
            gun.reset_gun()

    @property
    def snapshot(self):
        return {
            "current_gun": self.current_gun.type if self.current_gun else None,
            "guns": [gun.snapshot for gun in self.guns]
        }
    
    def apply_snapshot(self, snapshot):
        if 'current_gun' in snapshot:
            gun_type = snapshot['current_gun']
            self.current_gun = next((gun for gun in self.guns if gun.type == gun_type), None)
        if 'guns' in snapshot:
            for gun_snapshot in snapshot['guns']:
                gun_type = gun_snapshot.get('type')
                for gun in self.guns:
                    if gun.type == gun_type:
                        gun.apply_snapshot(gun_snapshot)
                        break