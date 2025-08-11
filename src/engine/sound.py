import pygame

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sfx = {}
        self.music_volume = 0.2
        self.sfx_volume = 0.1
        self.music_muted = False
        self.sfx_muted = False

    # SOUND EFFECTS
    def add_sfx(self, name, sound, volume=None):
        self.sfx[name] = sound
        if volume is None:
            self.sfx[name].set_volume(self.sfx_volume)
        else:
            self.sfx[name].set_volume(volume)

    def play_sfx(self, name):
        if not self.sfx_muted and name in self.sfx:
            self.sfx[name].play()

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0, min(1, volume))
        for sound in self.sfx.values():
            sound.set_volume(self.sfx_volume)

    def stop_all_sfx(self):
        for sound in self.sfx.values():
            sound.stop()

    def mute_sfx(self, mute=True):
        self.sfx_muted = mute

    def pause_all_sfx(self):
        pygame.mixer.pause()

    def unpause_all_sfx(self):
        pygame.mixer.unpause()
    
    # MUSIC
    def play_music(self, filepath, loop=True, volume=None):
        pygame.mixer.music.load(filepath)
        if volume is None:
            pygame.mixer.music.set_volume(self.music_volume if not self.music_muted else 0)
        else:
            pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1 if loop else 0)

    def stop_music(self):
        pygame.mixer.music.stop()

    def stop_sfx(self, name):
        if not self.sfx_muted and name in self.sfx:
            self.sfx[name].stop()

    def pause_music(self):
        pygame.mixer.music.pause()

    def unpause_music(self):
        pygame.mixer.music.unpause()

    def set_music_volume(self, volume):
        self.music_volume = max(0, min(1, volume))
        if not self.music_muted:
            pygame.mixer.music.set_volume(self.music_volume)

    def mute_music(self, mute=True):
        self.music_muted = mute
        pygame.mixer.music.set_volume(0 if mute else self.music_volume)

    # GENERAL MUTE
    def mute_all(self):
        self.mute_music(True)
        self.mute_sfx(True)

    def unmute_all(self):
        self.mute_music(False)
        self.mute_sfx(False)
