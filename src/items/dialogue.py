import pygame, sys, pathlib, math
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.utils import *

class MonologueBox:
    def __init__(self, font, text_color=(0, 0, 0), box_color=(255, 255, 255), padding=5, roundness=10, font_size=20):
        self.font = font
        self.font_size = font_size
        self.text_color = text_color
        self.box_color = box_color
        self.padding = padding
        self.roundness = roundness
        self.typing_index = 0
        self.typing_timer = 0
        self.typing_speed = 2
        self.last_text = ""

    def render_overhead_dialogue(self, screen, camera, position, text, font_size=20, entity_width=10, offset=Position()):
        font_loaded = load_font(self.font, font_size)
        
        max_line_width = 240
        lines = self.wrap_text(text, font_loaded, max_line_width)
        line_height = font_loaded.get_height()
        box_width = max(font_loaded.size(line)[0] for line in lines)
        box_height = line_height * len(lines)

        box_rect = pygame.Rect(0, 0, box_width + self.padding * 2, box_height + self.padding * 2)
        screen_pos = (position - camera.render_scroll - offset).tuple()
        box_rect.midbottom = (screen_pos[0] + 0.5 * entity_width, screen_pos[1] - 15)
        pygame.draw.rect(screen, self.box_color, box_rect, border_radius=self.roundness)

        for i, line in enumerate(lines):
            line_surface = font_loaded.render(line, True, self.text_color)
            line_pos = (box_rect.left + self.padding, box_rect.top + self.padding + i * line_height)
            screen.blit(line_surface, line_pos)


    def enlargement_picture_factor(self, width, height):
        base_scale = 5.0
        size_factor = (width * height) / (16 * 28)
        scale = base_scale / math.sqrt(size_factor)
        return max(3.0, min(scale, 5.0))

    def render_bottom_dialogue(self, screen, player, text, show_left=True):
        screen_width, screen_height = SCREEN_SIZE
        dialogue_height = 160
        dialogue_box = pygame.Rect(60, screen_height - dialogue_height - 20, screen_width - 120, dialogue_height)

        player_img = pygame.transform.scale_by(player.game.player_assets[player.type], self.enlargement_picture_factor(player.game.player_assets[player.type].get_width(), player.game.player_assets[player.type].get_height()))
        img_width, img_height = player_img.get_size()
        img_x = dialogue_box.left + 30 if show_left else dialogue_box.right - 30 - img_width
        img_y = dialogue_box.top - img_height // 1.5
        player_img = pygame.transform.flip(player_img, not show_left, False)
        screen.blit(player_img, (img_x, img_y))

        pygame.draw.rect(screen, (20, 20, 20), dialogue_box, border_radius=20)
        pygame.draw.rect(screen, (255, 255, 255), dialogue_box, 2, border_radius=20)

        font = load_font(self.font, self.font_size)
        text_x = dialogue_box.left + 60

        if text != self.last_text:
            self.last_text = text
            self.typing_index = 0
            self.typing_timer = 0

        self.typing_timer += 1
        if self.typing_timer >= self.typing_speed:
            self.typing_index += 1
            self.typing_timer = 0

        visible_text = text[:self.typing_index]
        wrapped_visible = self.wrap_text(visible_text, font, dialogue_box.width - img_width - 60)

        for i, line in enumerate(wrapped_visible):
            text_surface = font.render(line, True, (255, 255, 255))
            text_y = dialogue_box.top + 30 + i * 50
            screen.blit(text_surface, (text_x, text_y))


    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines, current = [], ''
        for word in words:
            test_line = current + word + ' '
            if font.size(test_line)[0] < max_width:
                current = test_line
            else:
                lines.append(current.strip())
                current = word + ' '
        lines.append(current.strip())
        return lines
    
    @property
    def typing_done(self):
        return self.typing_index >= len(self.last_text)
    
    def skip_typing(self):
        self.typing_index = len(self.last_text)

class DialogueManager:
    def __init__(self, monologue_box):
        self.monologue_box = monologue_box
        self.active = False
        self.entity = None
        self.text = ""
        self.bottom_mode = True
        self.show_left = True
        self.waiting_for_input = False

        self.script = []
        self.script_index = 0

    def start(self, entity, text, bottom_mode=True, show_left=True):
        self.entity = entity
        self.text = text
        self.bottom_mode = bottom_mode
        self.show_left = show_left
        self.active = True
        self.waiting_for_input = True
        self.script = []
        self.script_index = 0
        self._reset_typing()

    def start_script(self, script):
        self.script = script
        self.script_index = 0
        self.active = True
        self._apply_current_line()

    def _apply_current_line(self):
        line = self.script[self.script_index]
        self.entity = line["entity"]
        self.text = line["text"]
        self.bottom_mode = line.get("bottom_mode", True)
        self.show_left = line.get("show_left", True)
        self.waiting_for_input = True
        self._reset_typing()

    def clear_script(self):
        self.script = []
        self.script_index = 0
        self.active = False
        self.waiting_for_input = False
        self.text = ""
        self.entity = None
        self.bottom_mode = True
        self.show_left = True

    def _reset_typing(self):
        self.monologue_box.last_text = ""
        self.monologue_box.typing_index = 0
        self.monologue_box.typing_timer = 0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if not self.monologue_box.typing_done:
                self.monologue_box.skip_typing()
            else:
                if self.script:
                    self.script_index += 1
                    if self.script_index >= len(self.script):
                        self.active = False
                        self.waiting_for_input = False
                    else:
                        self._apply_current_line()
                else:
                    self.active = False
                    self.waiting_for_input = False

    def render(self, screen, camera):
        if not self.active:
            return
        if self.bottom_mode:
            self.monologue_box.render_bottom_dialogue(screen, self.entity, self.text, show_left=self.show_left)
        else:
            self.monologue_box.render_overhead_dialogue(screen, camera, self.entity.position, self.text)

    @property
    def is_done(self):
        return not self.active
