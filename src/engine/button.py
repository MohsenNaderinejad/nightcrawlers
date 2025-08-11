import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from config import ALLOWED_WORDS, FPS
from src.engine.sound import SoundManager

class Button:
    def __init__(self, name, game, position:tuple, dimensions:tuple, action, arguments = None, sound_active = None):
        self.name = name
        self.status = 'idle'
        self.game = game

        self.rect = pygame.Rect(position[0], position[1], dimensions[0], dimensions[1])
        self.action = action
        self.arguments = arguments

        if sound_active:
            self.sound_manager = SoundManager()
            self.sound_manager.set_sfx_volume(0.2)
            self.sound_manager.add_sfx('Active', sound_active)

    def set_status(self, status):
        self.status = status

    def render(self, screen:pygame.Surface):
        screen.blit(self.game.ui_assets[self.name + '/' + self.status], self.rect)
    
    def execute(self):
        if self.action:
            self.sound_manager.play_sfx('Active')
            pygame.time.delay(100)
            if self.arguments == None:
                self.action()
            else:
                if type(self.arguments) != tuple:
                    self.action(self.arguments)
                else:
                    self.action(*self.arguments)

class TextBox(Button):
    def __init__(self, name, game, position, dimensions, max_length, font:pygame.font.Font, color, screen, sound_active=None):
        super().__init__(name, game, position, dimensions, None, screen, sound_active)
        self.text = ''
        self.max_length = max_length
        self.font = font
        self.color = color
    
    def execute(self):
        self.sound_manager.play_sfx('Active')
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        running = False
                    
                    if event.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]

                    elif event.unicode in ALLOWED_WORDS and len(self.text) <= self.max_length - 1:
                        self.text += event.unicode
            
            self.render(self.arguments)

            pygame.display.update()
            self.game.clock.tick(FPS)
    
    def render(self, screen):
        super().render(screen)

        text = self.font.render(self.text, True, self.color)
        screen.blit(text, (self.rect.x + 25, self.rect.y + 25))