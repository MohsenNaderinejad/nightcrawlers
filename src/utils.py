import pygame, sys, pathlib, os, math
parent_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from config import *
from collections import OrderedDict


# ---------------------- CLASSES ---------------------
class LRUCache(OrderedDict):
    def __init__(self, capacity):
        self.capacity = capacity
        super().__init__()

    def __getitem__(self, key):
        if key in self:
            self.move_to_end(key)  # Move to most recently used position
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.capacity:
            self.popitem(last=False)  # Remove least recently used item

# --------- POSITION ---------
class Position:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.__hash = hash((self.x, self.y))

    def tuple(self):
        return (self.x, self.y)

    def __eq__(self, value):
        if not isinstance(value, Position):
            return NotImplemented
        return self.x == value.x and self.y == value.y
    
    def __ne__(self, value):
        if not isinstance(value, Position):
            return NotImplemented
        return self.x != value.x or self.y != value.y

    def __repr__(self):
        return f"{self.x};{self.y}"
    
    def __hash__(self):
        return self.__hash
    
    def __add__(self, value):
        if not isinstance(value, (Position, pygame.Vector2)):
            return NotImplemented
        return Position(self.x + value.x, self.y + value.y)
    
    def __sub__(self, value):
        if not isinstance(value, (Position, pygame.Vector2)):
            return NotImplemented
        return Position(self.x - value.x, self.y - value.y)
    
    def __mul__(self, value):
        if not isinstance(value, (int, float)):
            return NotImplemented
        return Position(self.x * value, self.y * value)
    
    def __truediv__(self, value):
        if not isinstance(value, (int, float)):
            return NotImplemented
        return Position(self.x / value, self.y / value)
    
    def __floordiv__(self, value):
        if not isinstance(value, (int, float)):
            return NotImplemented
        return Position(self.x // value, self.y // value)

    def to_key(self):
        return f"{self.x};{self.y}"
    
    def copy(self):
        return Position(self.x, self.y)

    @staticmethod
    def from_key(key):
        x, y = map(float, key.split(";"))
        return Position(x, y)

# --------- COORDINATE SYSTEM ---------
class CoordinateSystem:
    def __init__(self, origin, unit):
        if not isinstance(origin, Position):
            return NotImplemented

        self.unit = unit

        self.origin = Position(*origin.tuple())
    
    def update_origin(self, new_origin):
        if not isinstance(new_origin, Position):
            return NotImplemented
        
        self.origin = Position(*new_origin.tuple())
    
    def vector(self, target: Position):
        if not isinstance(target, Position):
            return NotImplemented
        return target - self.origin

    def vector_size(self, target: Position):
        if not isinstance(target, Position):
            return NotImplemented

        vec = target - self.origin
        return math.sqrt(vec.x ** 2 + vec.y ** 2) * self.unit
    
    def normalized_vector(self, target: Position):
        if not isinstance(target, Position):
            return NotImplemented

        vec = target - self.origin
        size = math.sqrt(vec.x**2 + vec.y**2)

        if size == 0:
            return Position(0, 0)

        return vec / size * self.unit

    def angle(self, target: Position):
        if not isinstance(target, Position):
            return NotImplemented

        vec = target - self.origin
        angle_rad = math.atan2(vec.y, vec.x)
        return math.degrees(angle_rad)
    
# --------- ANIMATION ---------
class Animation:
    def __init__(self, images, img_dur = 5, loop = True):
        self.images = images
        self.image_duration = img_dur
        self.loop = loop
        self.frame = 0
        self.done = False

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (len(self.images) * self.image_duration)
        else:
            self.frame  = min(self.frame + 1, len(self.images) * self.image_duration - 1)
            if self.frame >= len(self.images) * self.image_duration - 1:
                self.done = True

    def reset(self):
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.image_duration, self.loop)

    def image(self):
        return self.images[int(self.frame / self.image_duration)]
    
# --------- CONTROLLER ---------
class Controller:
    def __init__(self, up_key=pygame.K_w, down_key=pygame.K_s, left_key=pygame.K_a, right_key=pygame.K_d, jump_key=pygame.K_SPACE, fshift_key=pygame.K_LSHIFT, sshift_key=pygame.K_RSHIFT, shoot_key=pygame.K_q, reload_key=pygame.K_r, change_gun_key=pygame.K_v):
        self.up_key = up_key
        self.down_key = down_key
        self.left_key = left_key
        self.right_key = right_key
        self.jump_key = jump_key
        self.fshift_key = fshift_key
        self.sshift_key = sshift_key
        self.shoot_key = shoot_key
        self.change_gun_key = change_gun_key
        self.reload_key = reload_key
        self.movement = {
            'UMove': False,
            'DMove': False,
            'LMove': False,
            'RMove': False,
            'Jump': False,
            'SHIFT': False,
            'SHOOT': False,
            'RELOAD': False,
            'CHANGE_GUN': False
        }
        self.click_during_pause = False

    @property
    def keys(self):
        return {
            'jump_key': self.jump_key,
            'left_key': self.left_key,
            'right_key': self.right_key,
            'shoot_key': self.shoot_key,
            'fshift_key': self.fshift_key,
            'sshift_key': self.sshift_key,
            'reload_key': self.reload_key,
            'change_gun_key': self.change_gun_key
        }

    def change_keys(self, key_bind: dict):
        up_key = key_bind.get('up_key', None)
        down_key = key_bind.get('down_key', None)
        left_key = key_bind.get('left_key', None)
        right_key = key_bind.get('right_key', None)
        shoot_key = key_bind.get('shoot_key', None)
        jump_key = key_bind.get('jump_key', None)
        fshift_key = key_bind.get('fshift_key', None)
        sshift_key = key_bind.get('sshift_key', None)
        reload_key = key_bind.get('reload_key', None)
        change_gun_key = key_bind.get('change_gun_key', None)

        if shoot_key is not None:
            self.shoot_key = shoot_key
        if up_key is not None:
            self.up_key = up_key
        if down_key is not None:
            self.down_key = down_key
        if left_key is not None:
            self.left_key = left_key
        if right_key is not None:
            self.right_key = right_key
        if jump_key is not None:
            self.jump_key = jump_key
        if fshift_key is not None:
            self.fshift_key = fshift_key
        if sshift_key is not None:
            self.sshift_key = sshift_key
        if reload_key is not None:
            self.reload_key = reload_key
        if change_gun_key is not None:
            self.change_gun_key = change_gun_key

    def update(self, event, game, movement=None):
        if event.type == pygame.KEYDOWN:
            if event.key == self.up_key:
                movement['UMove'] = True
            if event.key == self.down_key:
                movement['DMove'] = True
            if event.key == self.left_key:
                movement['LMove'] = True
            if event.key == self.right_key:
                movement['RMove'] = True
            if event.key == self.fshift_key or event.key == self.sshift_key:
                movement['SHIFT'] = True
            if event.key == self.jump_key:
                movement['Jump'] = True
            if event.key == self.shoot_key:
                self.movement['SHOOT'] = True
                if game.level.pause_between_phases:
                    self.click_during_pause = True
            if event.key == self.reload_key:
                self.movement['RELOAD'] = True
            if event.key == self.change_gun_key:
                self.movement['CHANGE_GUN'] = True
        if event.type == pygame.KEYUP:
            if event.key == self.up_key:
                movement['UMove'] = False
            if event.key == self.down_key:
                movement['DMove'] = False
            if event.key == self.left_key:
                movement['LMove'] = False
            if event.key == self.right_key:
                movement['RMove'] = False
            if event.key == self.fshift_key or event.key == self.sshift_key:
                movement['SHIFT'] = False
            if event.key == self.jump_key:
                movement['Jump'] = False
            if event.key == self.shoot_key:
                self.movement['SHOOT'] = False
            if event.key == self.reload_key:
                self.movement['RELOAD'] = False
            if event.key == self.change_gun_key:
                self.movement['CHANGE_GUN'] = False

    def update_for_editor(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == self.up_key:
                self.movement['UMove'] = True
            if event.key == self.down_key:
                self.movement['DMove'] = True
            if event.key == self.left_key:
                self.movement['LMove'] = True
            if event.key == self.right_key:
                self.movement['RMove'] = True
            if event.key == self.fshift_key or event.key == self.sshift_key:
                self.movement['SHIFT'] = True

        if event.type == pygame.KEYUP:
            if event.key == self.up_key:
                self.movement['UMove'] = False
            if event.key == self.down_key:
                self.movement['DMove'] = False
            if event.key == self.left_key:
                self.movement['LMove'] = False
            if event.key == self.right_key:
                self.movement['RMove'] = False
            if event.key == self.fshift_key or event.key == self.sshift_key:
                self.movement['SHIFT'] = False

    def clear_movement(self):
        self.movement = {
            'UMove': False,
            'DMove': False,
            'LMove': False,
            'RMove': False,
            'Jump': False,
            'SHIFT': False,
            'SHOOT': False,
            'RELOAD': False,
            'CHANGE_GUN': False
        }

# --------- MOUSE ---------
class Mouse:
    def __init__(self):
        self.mouse_movements = {
            'L_CLICK': False,
            'R_CLICK': False,
            'M_CLICK': False
        }
        self.mouse_pos = Position()
        self.mouse_pos_vector2 = pygame.Vector2(self.mouse_pos.tuple())
        self.click_during_pause = False
    
    def update_mouse_click(self, event, game):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mouse_movements['L_CLICK'] = True
                if hasattr(game, 'level') and game.level.pause_between_phases:
                    self.click_during_pause = True
            if event.button == 3:
                self.mouse_movements['R_CLICK'] = True
            if event.button == 2:
                self.mouse_movements['M_CLICK'] = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_movements['L_CLICK'] = False
            if event.button == 3:
                self.mouse_movements['R_CLICK'] = False
            if event.button == 2:
                self.mouse_movements['M_CLICK'] = False


    def update_mouse_position(self, event=None):
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos.x, self.mouse_pos.y = pygame.mouse.get_pos()

    def update(self, event, game):
        self.update_mouse_click(event, game)
        self.update_mouse_position(event)

    def set_mouse_image(self, image: pygame.image):
        pygame.mouse.set_visible(False)
        self.custom_cursor_image_rect = image.get_rect()
        self.custom_cursor_image = image

    def unset_mouse_image(self):
        pygame.mouse.set_visible(True)
        self.custom_cursor_image = None
        self.custom_cursor_image_rect = None

# --------- JOYSTICK CONTROLLER ---------
class JoystickController:
    def __init__(self, joystick_index=0):
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(joystick_index)
        self.joystick.init()

        self.LT = 0.0
        self.RT = 0.0
        self.joystick_name = self.joystick.get_name()
        self.joystick_id = self.joystick.get_id()


    def update(self, event, movement):
        axis_x = self.joystick.get_axis(0)
        axis_y = self.joystick.get_axis(1)
        self.LT = self.joystick.get_axis(2)
        self.RT = self.joystick.get_axis(5)

        if event.type == pygame.JOYAXISMOTION:
            if axis_x < -0.5:
                movement['LMove'] = True
                movement['RMove'] = False
            elif axis_x > 0.5:
                movement['RMove'] = True
                movement['LMove'] = False
            else:
                movement['LMove'] = False
                movement['RMove'] = False

            if axis_y < -0.5:
                movement['UMove'] = True
                movement['DMove'] = False
            elif axis_y > 0.5:
                movement['DMove'] = True
                movement['UMove'] = False
            else:
                movement['UMove'] = False
                movement['DMove'] = False

    def controller_touched(self):
        # Check buttons
        for i in range(self.joystick.get_numbuttons()):
            if self.joystick.get_button(i):
                return True

        # Check axes (joysticks, triggers)
        for i in range(self.joystick.get_numaxes()):
            if abs(self.joystick.get_axis(i)) > 0.1:
                return True

        # Check hat switches (D-pad)
        for i in range(self.joystick.get_numhats()):
            if self.joystick.get_hat(i) != (0, 0):
                return True

        return False

# --------- PLAYER CONTROLLER ---------
class PlayerController(Controller, Mouse):
    def __init__(self, entity, up_key=pygame.K_w, down_key=pygame.K_s, left_key=pygame.K_a, right_key=pygame.K_d, jump_key=pygame.K_SPACE, fshift_key=pygame.K_LSHIFT, sshift_key=pygame.K_RSHIFT, change_gun_key=pygame.K_v, reload_key=pygame.K_r):
        Controller.__init__(self, up_key, down_key, left_key, right_key, jump_key, fshift_key, sshift_key, reload_key=reload_key, change_gun_key=change_gun_key)
        Mouse.__init__(self)
        self.movement = {
            'UMove': False,
            'DMove': False,
            'LMove': False,
            'RMove': False,
            'Jump': False,
            'SHIFT': False,
            'SHOOT': False,
            'RELOAD': False,
            'CHANGE_GUN': False
        }

        self.entity = entity
        self.in_world_mouse_pos = Position()
        self.joystick_controller = None
        if pygame.joystick.get_count() > 0:
            self.joystick_controller = JoystickController()

    def update(self, event, game):
        Controller.update(self, event, game, self.movement)
        Mouse.update(self, event, game)
        if self.joystick_controller:
            self.joystick_controller.update(event, self.movement)
        
        world_mouse_x = self.mouse_pos.x / (game.screen_size[0] / game.display_size[0])
        world_mouse_y = self.mouse_pos.y / (game.screen_size[1] / game.display_size[1])

        self.in_world_mouse_pos = Position(world_mouse_x, world_mouse_y)
        self.mouse_pos_vector2 = pygame.Vector2(self.in_world_mouse_pos.tuple())

        if event.type == pygame.KEYDOWN:
            if event.key == self.jump_key and self.entity.freeze_time <= 0 and not self.entity.game.cutscene_mode:
                self.entity.jump()
            if (event.key == self.fshift_key or event.key == self.sshift_key) and not self.entity.game.cutscene_mode:
                self.entity.dash()

    def render_mouse(self, surface):
        if self.entity.game.cutscene_mode:
            return
        temp_pos = (self.mouse_pos / (self.entity.game.screen_size[0] / self.entity.game.display_size[0]))
        self.custom_cursor_image_rect.center = temp_pos.tuple()
        surface.blit(self.custom_cursor_image, self.custom_cursor_image_rect)

    def inputs(self):
        inputs = dict(self.movement, **self.mouse_movements)
        return inputs
    
    def apply_snapshot(self, snapshot: dict, server_side=False):
        if server_side:
            pass
        if not server_side:
            new_x = snapshot.get("x", self.entity.position.x)
            dx = new_x - self.entity.position.x
            if abs(dx) > 0.5:
                self.entity.position.x += dx * 0.5

            new_y = snapshot.get("y", self.entity.position.y)
            dy = new_y - self.entity.position.y
            if abs(dy) > 0.75:
                self.entity.position.y += dy * 0.5

        if not server_side:
            self.entity.HP.actual_value = snapshot.get("hp", self.entity.HP.actual_value)
            self.entity.MP.actual_value = snapshot.get("mp", self.entity.MP.actual_value)
            self.entity.after_death_time = snapshot.get("after_death_time", self.entity.after_death_time)

        if not server_side and self.entity.remote_player:
            input_data = snapshot.get("input", {})
            for key in self.movement:
                self.movement[key] = input_data.get(key, False)
            for key in self.mouse_movements:
                self.mouse_movements[key] = input_data.get(key, False)

            mouse_data = snapshot.get("mouse", {})
            mouse_x = mouse_data.get("x", self.mouse_pos_vector2.x)
            mouse_y = mouse_data.get("y", self.mouse_pos_vector2.y)
            self.mouse_pos_vector2 = pygame.Vector2(mouse_x, mouse_y)

            if input_data.get("Jump") and self.entity.freeze_time <= 0:
                self.entity.jump()
            if input_data.get("SHIFT"):
                self.entity.dash()

# --------- MULTIPLAYER CONTROLLER ---------
class PlayerMultiplayerController(Controller):
    def __init__(self, entity, index, up_key=pygame.K_w, down_key=pygame.K_s, left_key=pygame.K_a, right_key=pygame.K_d, jump_key=pygame.K_SPACE, fshift_key=pygame.K_LSHIFT, sshift_key=pygame.K_RSHIFT, shoot_key=pygame.K_q, reload_key=pygame.K_r, change_gun_key=pygame.K_v):
        Controller.__init__(self, up_key, down_key, left_key, right_key, jump_key, fshift_key, sshift_key, shoot_key, reload_key, change_gun_key)
        self.index = index
        self.entity = entity
        self.movement = {
            'UMove': False,
            'DMove': False,
            'LMove': False,
            'RMove': False,
            'Jump': False,
            'SHIFT': False,
            'SHOOT': False,
            'RELOAD': False,
            'CHANGE_GUN': False
        }

    def update(self, event):
        Controller.update(self, event, self.entity.game, self.movement)
        if event.type == pygame.KEYDOWN:
            if event.key == self.jump_key and self.entity.freeze_time <= 0 and not self.entity.game.cutscene_mode:
                self.entity.jump()
            if (event.key == self.fshift_key or event.key == self.sshift_key) and not self.entity.game.cutscene_mode:
                self.entity.dash()

# --------- ENEMY CONTROLLER ---------
class EnemyController:
    def __init__(self):
        self.movement = {
            'UMove': False,
            'DMove': False,
            'LMove': False,
            'RMove': False,
            'Jump': False,
            'SHIFT': False
        }

# --------- COLLISION MAP ---------
class CollisionMap:
    def __init__(self, entity):
        self.entity = entity
        self.collision = { 'up' : False , 'left' : False , 'down' : False , 'right' : False}
        self.tilemap_collide = False
    
    def change(self, direction, value):
        if direction in self.collision:
            self.collision[direction] = value
        else:
            raise ValueError('Invalid Direction')
        
    def tilemap_collision(self):
        self.tilemap_collide = True
        
    def reset(self):
        self.collision = { 'up' : False , 'left' : False , 'down' : False , 'right' : False}
        self.tilemap_collide = False

# --------------------- CONSTANTS ---------------------
# -------- PATHS --------
# Set BASE_IMAGE_PATH relative to the project root, regardless of CWD
BASE_DIR = pathlib.Path(__file__).resolve().parent
BASE_IMAGE_PATH = str(BASE_DIR / 'assets' / 'images') + os.sep
BASE_SOUND_PATH = str(BASE_DIR / 'assets' / 'sounds') + os.sep
BASE_MUSIC_PATH = str(BASE_DIR / 'assets' / 'music') + os.sep
BASE_MAP_PATH = str(BASE_DIR / 'assets' / 'maps') + os.sep
BASE_FONT_PATH = str(BASE_DIR / 'assets' / 'Fonts') + os.sep

# -------- NEIGHBOUR OFFSET --------
NEIGHBOUR_OFFSET = [
    Position(-1, -1), Position(0, -1), Position(1, -1),
    Position(-1,  0), Position(0,  0), Position(1,  0),
    Position(-1,  1), Position(0,  1), Position(1,  1)
]

# --------------------- FUNCTIONS ---------------------
# -------- LOAD IMAGE(S) / LOAD SOUND(S) / LOAD MUSICS(S) --------

def load_image(filename, player_loader=False, color_key_selector=False, color_key=None, scale_size=1):
    if player_loader:
        img = pygame.image.load(BASE_IMAGE_PATH + filename).convert_alpha()
        if scale_size != 1:
            img = pygame.transform.scale(img, (img.get_width() * scale_size, img.get_height() * scale_size))
        img.set_colorkey((0, 0, 0))
        return img
    elif color_key_selector:
        if color_key is None:
            img = pygame.image.load(BASE_IMAGE_PATH + filename).convert_alpha()
            if scale_size != 1:
                img = pygame.transform.scale(img, (img.get_width() * scale_size, img.get_height() * scale_size))
            return img
        img = pygame.image.load(BASE_IMAGE_PATH + filename).convert_alpha()
        if scale_size != 1:
            img = pygame.transform.scale(img, (img.get_width() * scale_size, img.get_height() * scale_size))
        img.set_colorkey(color_key)
        return img
    else:
        img = pygame.image.load(BASE_IMAGE_PATH + filename).convert_alpha()
        pixel_array = pygame.PixelArray(img)

        pixel_array.replace((255,255,255),(0,0,0,0))
        pixel_array.replace((0,0,0),(0,0,0,0))
        if scale_size != 1:
            img = pygame.transform.scale(img, (img.get_width() * scale_size, img.get_height() * scale_size))

        del pixel_array
        return img

def load_sound(filename):
    sound = pygame.mixer.Sound(BASE_SOUND_PATH + filename)
    return sound

def load_music(filename):
    pygame.mixer.music.load(BASE_MUSIC_PATH + filename)

def load_font(filename, size=8):
    font = pygame.font.Font(BASE_FONT_PATH + filename, size)
    return font

def load_images(path, player_loader=False, color_key_selector=False, color_key=None, scale_size=1):
    images = []
    for filename in sorted(os.listdir(BASE_IMAGE_PATH + path)):
        img = load_image(path + '/' + filename, player_loader=player_loader, color_key_selector=color_key_selector, color_key=color_key, scale_size=scale_size)
        images.append(img)
    return images

def load_sounds(path):
    sounds = []
    for filename in sorted(os.listdir(BASE_SOUND_PATH + path)):
        sound = load_sound(path + '/' + filename)
        sounds.append(sound)
    return sounds

def load_music_files(path):
    music_files = []
    for filename in sorted(os.listdir(BASE_MUSIC_PATH + path)):
        music = load_music(path + '/' + filename)
        music_files.append(music)
    return music_files

def draw_text_with_outline(screen, text, font, x, y, text_color, outline_color, thickness=2, center=True):
    text_surface = font.render(text, True, text_color)
    outline_surface = font.render(text, True, outline_color)

    rect = text_surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    for dx in [-thickness, 0, thickness]:
        for dy in [-thickness, 0, thickness]:
            if dx == 0 and dy == 0:
                continue
            offset_rect = rect.copy()
            offset_rect.x += dx
            offset_rect.y += dy
            screen.blit(outline_surface, offset_rect)

    screen.blit(text_surface, rect)

def render_mouse_cursor(surface, custom_cursor_image):
    pygame.mouse.set_visible(False)
    mouse_pos = pygame.mouse.get_pos()
    custom_cursor_image_rect = custom_cursor_image.get_rect(topleft=mouse_pos)
    surface.blit(custom_cursor_image, custom_cursor_image_rect)