import pygame, sys, pathlib, json, threading, time
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.tilemap import *
from src.entities.player import *
from src.entities.enemy import *
from src.engine.level import *
from src.engine.multiplyer import *
from src.engine.button import *
from src.engine.cameras import *
from src.engine.cut_scene import *
from src.engine.effect import *
from src.items.dialogue import *
from src.scripts.dynamic_convos import fetch_completion
from src.items.particle import ParticleManager
from src.engine.sound import SoundManager
from src.network.client.client import GameClient
from src.network.network_multiplayer import MMode
from src.network.multiplayer_modes.NMOVV2.NMOVV2_Client import NMOVV2Client
from src.network.multiplayer_modes.NMOVV3.NMOVV3_Client import NMOVV3Client
from src.network.multiplayer_modes.NMOVV4.NMOVV4_Client import NMOVV4Client
from src.network.multiplayer_modes.NMTVV2.NMTVV2_Client import NMTVV2Client

# ---------------------- GAME ---------------------
# --------- INITIALIZE ---------
pygame.init()
pygame.joystick.init()

def draw_blurred_visibility_circle(mask_surface, center, radius, blur_width=50):
    for i in range(blur_width, 0, -1):
        alpha = int(255 * (i / blur_width))
        pygame.draw.circle(
            mask_surface,
            (0, 0, 0, alpha),
            center,
            radius + i
        )
    pygame.draw.circle(mask_surface, (0, 0, 0, 0), center, radius)

class Game:
    def __init__(self):
        pygame.display.set_caption("Night Crawlers") # CAPTION
        self.screen_size = SCREEN_SIZE # SCREEN SIZE
        self.display_size = DISPLAY_SIZE # DISPLAY SIZE ( SHOWN ON SCREEN FOR BETTER VIEW
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.HWSURFACE | pygame.DOUBLEBUF) # SCREEN SIZE
        self.display = pygame.Surface(DISPLAY_SIZE) # DISPLAY SIZE ( SHOWN ON SCREEN FOR BETTER VIEW )
        self.hud_display = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock() # FOR SETTING FPS
        self.cutscene_mode = False
        self.cutscene_manager = CutSceneManager(self)
        self.dialogue_manager = DialogueManager(MonologueBox('KnightWarrior-w16n8.otf', padding=2, font_size=35))
        self.particle_manager = ParticleManager(self)
        self.sound_manager = SoundManager()
        self.network_game_mode = None

        self.sound_manager.set_sfx_volume(1.5)
        self.sound_manager.set_music_volume(0.45)
        self.last_music = ''
        self.sfx_cooldown = 500
        self.last_sfx_time = 0
        
        pygame.display.set_icon(load_image('BeanHead Head.png',color_key_selector=True)) # ICON

        self.arena_ID = 1
        self.loading_done = False
        self.client = None
        self.character_index = 0

        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

    def loading_assets(self):
        self.ui_assets = {
            'player_status_bar_holder': load_image('UI/status_bar_player/holder.png', color_key_selector=True, color_key=(255, 255, 255)),
            'player_health_bar': load_images('UI/status_bar_player/health', color_key_selector=True, color_key=(255, 255, 255)),
            'player_mana_bar': load_images('UI/status_bar_player/mana', color_key_selector=True, color_key=(255, 255, 255)),
            'player_shield_bar': load_images('UI/status_bar_player/shield', color_key_selector=True, color_key=(255, 255, 255)),
            'round_bar_red': load_images('UI/rounds/red', color_key_selector=True),
            'round_bar_blue': load_images('UI/rounds/blue', color_key_selector=True),
            'round_bar_green': load_images('UI/rounds/green', color_key_selector=True),
            'round_bar_purple': load_images('UI/rounds/purple', color_key_selector=True),
            'boss_health_bar': load_images('UI/status_bar_boss/health', color_key_selector=True),

            #Buttons
            'account/idle': load_image('UI/Buttons/Account/Idle.png',color_key_selector=True),
            'account/hovered': load_image('UI/Buttons/Account/Hovered.png',color_key_selector=True),
            'account/pressed': load_image('UI/Buttons/Account/Pressed.png',color_key_selector=True),

            'play/idle': load_image('UI/Buttons/Play/Idle.png',color_key_selector=True),
            'play/hovered': load_image('UI/Buttons/Play/Hovered.png',color_key_selector=True),
            'play/pressed': load_image('UI/Buttons/Play/Pressed.png',color_key_selector=True),

            'quit/idle': load_image('UI/Buttons/Quit/Idle.png',color_key_selector=True),
            'quit/hovered': load_image('UI/Buttons/Quit/Hovered.png',color_key_selector=True),
            'quit/pressed': load_image('UI/Buttons/Quit/Pressed.png',color_key_selector=True),

            '_/idle': load_image('UI/Buttons/_/Idle.png',color_key_selector=True),
            '_/hovered': load_image('UI/Buttons/_/Hovered.png',color_key_selector=True),
            '_/pressed': load_image('UI/Buttons/_/Pressed.png',color_key_selector=True),
            
            '1v1/idle': load_image('UI/Buttons/1V1/Idle.png',color_key_selector=True),
            '1v1/hovered': load_image('UI/Buttons/1V1/Hovered.png',color_key_selector=True),
            '1v1/pressed': load_image('UI/Buttons/1V1/Pressed.png',color_key_selector=True),
            
            '1v1v1/idle': load_image('UI/Buttons/1V1V1/Idle.png',color_key_selector=True),
            '1v1v1/hovered': load_image('UI/Buttons/1V1V1/Hovered.png',color_key_selector=True),
            '1v1v1/pressed': load_image('UI/Buttons/1V1V1/Pressed.png',color_key_selector=True),
            
            '1v1v1v1/idle': load_image('UI/Buttons/1V1V1V1/Idle.png',color_key_selector=True),
            '1v1v1v1/hovered': load_image('UI/Buttons/1V1V1V1/Hovered.png',color_key_selector=True),
            '1v1v1v1/pressed': load_image('UI/Buttons/1V1V1V1/Pressed.png',color_key_selector=True),
            
            '2v2/idle': load_image('UI/Buttons/2V2/Idle.png',color_key_selector=True),
            '2v2/hovered': load_image('UI/Buttons/2V2/Hovered.png',color_key_selector=True),
            '2v2/pressed': load_image('UI/Buttons/2V2/Pressed.png',color_key_selector=True),
            
            'back1/idle': load_image('UI/Buttons/Back1/Idle.png',color_key_selector=True),
            'back1/hovered': load_image('UI/Buttons/Back1/Hovered.png',color_key_selector=True),
            'back1/pressed': load_image('UI/Buttons/Back1/Pressed.png',color_key_selector=True),
            
            'back2/idle': load_image('UI/Buttons/Back2/Idle.png',color_key_selector=True),
            'back2/hovered': load_image('UI/Buttons/Back2/Hovered.png',color_key_selector=True),
            'back2/pressed': load_image('UI/Buttons/Back2/Pressed.png',color_key_selector=True),
            
            'character/idle': load_image('UI/Buttons/Character/Idle.png',color_key_selector=True),
            'character/hovered': load_image('UI/Buttons/Character/Hovered.png',color_key_selector=True),
            'character/pressed': load_image('UI/Buttons/Character/Pressed.png',color_key_selector=True),
            
            'confirm/idle': load_image('UI/Buttons/Confirm/Idle.png',color_key_selector=True),
            'confirm/hovered': load_image('UI/Buttons/Confirm/Hovered.png',color_key_selector=True),
            'confirm/pressed': load_image('UI/Buttons/Confirm/Pressed.png',color_key_selector=True),
            
            'continue/idle': load_image('UI/Buttons/Continue/Idle.png',color_key_selector=True),
            'continue/hovered': load_image('UI/Buttons/Continue/Hovered.png',color_key_selector=True),
            'continue/pressed': load_image('UI/Buttons/Continue/Pressed.png',color_key_selector=True),
            
            'left/idle': load_image('UI/Buttons/Left/Idle.png',color_key_selector=True),
            'left/hovered': load_image('UI/Buttons/Left/Hovered.png',color_key_selector=True),
            'left/pressed': load_image('UI/Buttons/Left/Pressed.png',color_key_selector=True),
            
            'load/idle': load_image('UI/Buttons/Load/Idle.png',color_key_selector=True),
            'load/hovered': load_image('UI/Buttons/Load/Hovered.png',color_key_selector=True),
            'load/pressed': load_image('UI/Buttons/Load/Pressed.png',color_key_selector=True),
            
            'local/idle': load_image('UI/Buttons/Local/Idle.png',color_key_selector=True),
            'local/hovered': load_image('UI/Buttons/Local/Hovered.png',color_key_selector=True),
            'local/pressed': load_image('UI/Buttons/Local/Pressed.png',color_key_selector=True),
            
            'main/idle': load_image('UI/Buttons/Main/Idle.png',color_key_selector=True),
            'main/hovered': load_image('UI/Buttons/Main/Hovered.png',color_key_selector=True),
            'main/pressed': load_image('UI/Buttons/Main/Pressed.png',color_key_selector=True),
            
            'map/idle': load_image('UI/Buttons/Map/Idle.png',color_key_selector=True),
            'map/hovered': load_image('UI/Buttons/Map/Hovered.png',color_key_selector=True),
            'map/pressed': load_image('UI/Buttons/Map/Pressed.png',color_key_selector=True),
            
            'multi/idle': load_image('UI/Buttons/Multi/Idle.png',color_key_selector=True),
            'multi/hovered': load_image('UI/Buttons/Multi/Hovered.png',color_key_selector=True),
            'multi/pressed': load_image('UI/Buttons/Multi/Pressed.png',color_key_selector=True),
            
            'new/idle': load_image('UI/Buttons/New/Idle.png',color_key_selector=True),
            'new/hovered': load_image('UI/Buttons/New/Hovered.png',color_key_selector=True),
            'new/pressed': load_image('UI/Buttons/New/Pressed.png',color_key_selector=True),
            
            'next/idle': load_image('UI/Buttons/Next/Idle.png',color_key_selector=True),
            'next/hovered': load_image('UI/Buttons/Next/Hovered.png',color_key_selector=True),
            'next/pressed': load_image('UI/Buttons/Next/Pressed.png',color_key_selector=True),
            
            'online/idle': load_image('UI/Buttons/Online/Idle.png',color_key_selector=True),
            'online/hovered': load_image('UI/Buttons/Online/Hovered.png',color_key_selector=True),
            'online/pressed': load_image('UI/Buttons/Online/Pressed.png',color_key_selector=True),
            
            'photo/idle': load_image('UI/Buttons/Photo/Idle.png',color_key_selector=True),
            'photo/hovered': load_image('UI/Buttons/Photo/Hovered.png',color_key_selector=True),
            'photo/pressed': load_image('UI/Buttons/Photo/Pressed.png',color_key_selector=True),
            
            'restart/idle': load_image('UI/Buttons/Restart/Idle.png',color_key_selector=True),
            'restart/hovered': load_image('UI/Buttons/Restart/Hovered.png',color_key_selector=True),
            'restart/pressed': load_image('UI/Buttons/Restart/Pressed.png',color_key_selector=True),
            
            'resume/idle': load_image('UI/Buttons/Resume/Idle.png',color_key_selector=True),
            'resume/hovered': load_image('UI/Buttons/Resume/Hovered.png',color_key_selector=True),
            'resume/pressed': load_image('UI/Buttons/Resume/Pressed.png',color_key_selector=True),
            
            'right/idle': load_image('UI/Buttons/Right/Idle.png',color_key_selector=True),
            'right/hovered': load_image('UI/Buttons/Right/Hovered.png',color_key_selector=True),
            'right/pressed': load_image('UI/Buttons/Right/Pressed.png',color_key_selector=True),
            
            'single/idle': load_image('UI/Buttons/Single/Idle.png',color_key_selector=True),
            'single/hovered': load_image('UI/Buttons/Single/Hovered.png',color_key_selector=True),
            'single/pressed': load_image('UI/Buttons/Single/Pressed.png',color_key_selector=True),
            
            'start/idle': load_image('UI/Buttons/Start/Idle.png',color_key_selector=True),
            'start/hovered': load_image('UI/Buttons/Start/Hovered.png',color_key_selector=True),
            'start/pressed': load_image('UI/Buttons/Start/Pressed.png',color_key_selector=True),
            
            'text_box/idle': load_image('UI/Buttons/Text Box/Idle.png',color_key_selector=True),
            'text_box/hovered': load_image('UI/Buttons/Text Box/Selected.png',color_key_selector=True),
            'text_box/pressed': load_image('UI/Buttons/Text Box/Selected.png',color_key_selector=True),
            
            'x/idle': load_image('UI/Buttons/X/Idle.png',color_key_selector=True),
            'x/hovered': load_image('UI/Buttons/X/Hovered.png',color_key_selector=True),
            'x/pressed': load_image('UI/Buttons/X/Pressed.png',color_key_selector=True),

            'rematch/idle': load_image('UI/Buttons/Rematch/Idle.png',color_key_selector=True),
            'rematch/hovered': load_image('UI/Buttons/Rematch/Hovered.png',color_key_selector=True),
            'rematch/pressed': load_image('UI/Buttons/Rematch/Pressed.png',color_key_selector=True),

            'login/idle': load_image('UI/Buttons/Login/Idle.png',color_key_selector=True),
            'login/hovered': load_image('UI/Buttons/Login/Hovered.png',color_key_selector=True),
            'login/pressed': load_image('UI/Buttons/Login/Pressed.png',color_key_selector=True),

            'signup/idle': load_image('UI/Buttons/Sign In/Idle.png',color_key_selector=True),
            'signup/hovered': load_image('UI/Buttons/Sign In/Hovered.png',color_key_selector=True),
            'signup/pressed': load_image('UI/Buttons/Sign In/Pressed.png',color_key_selector=True),

            'logout/idle': load_image('UI/Buttons/Logout/Idle.png',color_key_selector=True),
            'logout/hovered': load_image('UI/Buttons/Logout/Hovered.png',color_key_selector=True),
            'logout/pressed': load_image('UI/Buttons/Logout/Pressed.png',color_key_selector=True),

            'join/idle': load_image('UI/Buttons/Join/Idle.png',color_key_selector=True),
            'join/hovered': load_image('UI/Buttons/Join/Hovered.png',color_key_selector=True),
            'join/pressed': load_image('UI/Buttons/Join/Pressed.png',color_key_selector=True),

            'host/idle': load_image('UI/Buttons/Host/Idle.png',color_key_selector=True),
            'host/hovered': load_image('UI/Buttons/Host/Hovered.png',color_key_selector=True),
            'host/pressed': load_image('UI/Buttons/Host/Pressed.png',color_key_selector=True),

            'invite/idle': load_image('UI/Buttons/Invite/Idle.png', color_key_selector=True),
            'invite/hovered': load_image('UI/Buttons/Invite/Hovered.png', color_key_selector=True),
            'invite/pressed': load_image('UI/Buttons/Invite/Pressed.png', color_key_selector=True),

            'accept/idle': load_image('UI/Buttons/Accept/Idle.png', color_key_selector=True),
            'accept/hovered': load_image('UI/Buttons/Accept/Hovered.png', color_key_selector=True),
            'accept/pressed': load_image('UI/Buttons/Accept/Pressed.png', color_key_selector=True),

            'decline/idle': load_image('UI/Buttons/Decline/Idle.png', color_key_selector=True),
            'decline/hovered': load_image('UI/Buttons/Decline/Hovered.png', color_key_selector=True),
            'decline/pressed': load_image('UI/Buttons/Decline/Pressed.png', color_key_selector=True),

            'send/idle': load_image('UI/Buttons/Send/Idle.png', color_key_selector=True),
            'send/hovered': load_image('UI/Buttons/Send/Hovered.png', color_key_selector=True),
            'send/pressed': load_image('UI/Buttons/Send/Pressed.png', color_key_selector=True),

            'random/idle': load_image('UI/Buttons/Random/Idle.png', color_key_selector=True),
            'random/hovered': load_image('UI/Buttons/Random/Hovered.png', color_key_selector=True),
            'random/pressed': load_image('UI/Buttons/Random/Pressed.png', color_key_selector=True),

            'invitation/idle': load_image('UI/Buttons/Invitation/Idle.png', color_key_selector=True),
            'invitation/hovered': load_image('UI/Buttons/Invitation/Hovered.png', color_key_selector=True),
            'invitation/pressed': load_image('UI/Buttons/Invitation/Pressed.png', color_key_selector=True),
        }

        self.assets = {
            'grass': load_images('tiles/grass'),
            'Boxes': load_images('Boxes'),
            'Bushes': load_images('Bushes'),
            'Fence': load_images('Fence'),
            'Grass': load_images('Grass'),
            'Pointers': load_images('Pointers'),
            'Ridges': load_images('Ridges'),
            'Stones': load_images('Stones'),
            'Ladders': load_images('Ladders'),
            'Trees': load_images('Trees'),
            'Willows': load_images('Willows'),
            'cursor': load_image('best_cross.png'),
            'normal_cursor': load_image('normal_cursor.png'),
            'hero': load_images('tiles/spawners/Heros', player_loader=True),
            'enemies': load_images('tiles/spawners/Enemies', player_loader=True, scale_size=1),
            'bullet_image': load_image('projectile.png'),
            'item':load_images('Items', player_loader=True),
            'save':load_images('save'),

            'background': load_image('5_71.png'),
            'main_menu': load_image('Main Menu.png',color_key_selector=True),
            'play_menu': load_image('Play Menu.png',color_key_selector=True),
            'singleplayer_menu': load_image('Single Menu.png',color_key_selector=True),
            'character_select_single': load_image('Character Single.png',color_key_selector=True),
            'multiplayer_menu': load_image('Multi Select Menu.png',color_key_selector=True),
            'local_menu': load_image('Multi Menu.png',color_key_selector=True),
            'map_select': load_image('Map Select.png',color_key_selector=True),
            'character_select_multi': load_image('Character Multi.png',color_key_selector=True),
            'user_info': load_image('User Show.png',color_key_selector=True),
            'sign_up': load_image('User SignIn.png',color_key_selector=True),
            'game_over': load_image('Game Over.png',color_key_selector=True),
            'credits': load_image('Credits.png',color_key_selector=True),
            'level_completed': load_image('Level Completed.png',color_key_selector=True),
            'pause_menu': load_image('Pause Menu.png',color_key_selector=True),
            'match_over': load_image('Match Over.png',color_key_selector=True),
            'account_menu': load_image('Account Menu.png',color_key_selector=True),
            'online_select': load_image('Online Select.png',color_key_selector=True),
            'mode_select': load_image('Mode Select.png',color_key_selector=True),
            'lobby_code': load_image('Lobby Code.png',color_key_selector=True),
            'invite_menu': load_image('Invite Menu.png', color_key_selector=True),
            'waiting_for_invitation': load_image('Waiting For Invitation.png', color_key_selector=True),
            'waiting_for_accept': load_image('Waiting For Accept.png', color_key_selector=True),
            'match_invitation': load_image('Match Invitation.png', color_key_selector=True),
            'invitation_accepted': load_image('Invitation Accepted.png', color_key_selector=True),
            'invitation_rejected': load_image('Invitation Rejected.png', color_key_selector=True),
            'error_page': load_image('Error Page.png', color_key_selector=True),

            'in_queue': load_images('In Queue', color_key_selector=True),
            'waiting': load_images('Waiting', color_key_selector=True),
            'synchronizing': load_images('Synchronizing', color_key_selector=True),
            'sending_invitation': load_images('Sending Invitation', color_key_selector=True),
            'sending_acceptance': load_images('Sending Acceptance', color_key_selector=True),
            'sending_rejection': load_images('Sending Rejection', color_key_selector=True),
            'sending_match_request': load_images('Sending Match Request', color_key_selector=True),
            'match_starting': load_images('Match Starting', color_key_selector=True),
            'canceling_match_request': load_images('Canceling Match Request', color_key_selector=True),
            'canceling_invitation': load_images('Canceling Invitation', color_key_selector=True),
        }

        self.player_assets = {
            'beanhead': load_image('entities/heros/beanhead/picture.png', player_loader=True),
            'crow': load_image('entities/heros/crow/picture.png',color_key_selector=True),
            'redhood': load_image('entities/heros/redhood/picture.png', color_key_selector=True),
            'boss_normal': load_image('entities/Boss/picture_n.png', player_loader=True, scale_size=1),
            'boss_red': load_image('entities/Boss/picture_r.png', player_loader=True, scale_size=1),
            'the_man_with_hat': load_image('entities/heros/the_man_with_hat/picture.png', color_key_selector=True),
        }

        self.animation_assets = {
            'beanhead/idle': Animation(load_images('entities/heros/beanhead/idle', player_loader=True)),
            'beanhead/jump': Animation(load_images('entities/heros/beanhead/jump', player_loader=True)),
            'beanhead/walk': Animation(load_images('entities/heros/beanhead/walk', player_loader=True)),
            'beanhead/fall': Animation(load_images('entities/heros/beanhead/fall', player_loader=True)),
            'beanhead/wall_slide': Animation(load_images('entities/heros/beanhead/wall_slide', player_loader=True)),
            'beanhead/shoot': Animation(load_images('entities/heros/beanhead/shoot', player_loader=True), loop=False),
            'beanhead/hurt': Animation(load_images('entities/heros/beanhead/hurt', player_loader=True), loop=False, img_dur=8),
            'beanhead/death': Animation(load_images('entities/heros/beanhead/death', player_loader=True), loop=False, img_dur=8),

            'redhood/idle': Animation(load_images('entities/heros/redhood/idle', color_key_selector=True), img_dur=8),
            'redhood/jump': Animation(load_images('entities/heros/redhood/jump', color_key_selector=True), loop=False),
            'redhood/walk': Animation(load_images('entities/heros/redhood/walk', color_key_selector=True)),
            'redhood/fall': Animation(load_images('entities/heros/redhood/fall', color_key_selector=True)),
            'redhood/wall_slide': Animation(load_images('entities/heros/redhood/wall_slide', color_key_selector=True)),
            'redhood/hurt': Animation(load_images('entities/heros/redhood/hurt', color_key_selector=True), loop=False, img_dur=8),
            'redhood/death': Animation(load_images('entities/heros/redhood/death', color_key_selector=True), loop=False, img_dur=8),

            'crow/idle': Animation(load_images('entities/heros/crow/idle', color_key_selector=True)),
            'crow/jump': Animation(load_images('entities/heros/crow/jump', color_key_selector=True), loop=False),
            'crow/walk': Animation(load_images('entities/heros/crow/walk', color_key_selector=True)),
            'crow/fall': Animation(load_images('entities/heros/crow/fall', color_key_selector=True)),
            'crow/wall_slide': Animation(load_images('entities/heros/crow/wall_slide', color_key_selector=True)),
            'crow/hurt': Animation(load_images('entities/heros/crow/hurt', color_key_selector=True), loop=False, img_dur=8),
            'crow/death': Animation(load_images('entities/heros/crow/death', color_key_selector=True), loop=False, img_dur=8),
            'crow/land': Animation(load_images('entities/heros/crow/land', color_key_selector=True), loop=False, img_dur=8),

            'the_man_with_hat/idle': Animation(load_images('entities/heros/the_man_with_hat/idle', color_key_selector=True), img_dur=6),
            'the_man_with_hat/jump': Animation(load_images('entities/heros/the_man_with_hat/jump', color_key_selector=True), loop=False, img_dur=6),
            'the_man_with_hat/walk': Animation(load_images('entities/heros/the_man_with_hat/walk', color_key_selector=True), img_dur=6),
            'the_man_with_hat/fall': Animation(load_images('entities/heros/the_man_with_hat/fall', color_key_selector=True), img_dur=6),
            'the_man_with_hat/wall_slide': Animation(load_images('entities/heros/the_man_with_hat/wall_slide', color_key_selector=True)),
            'the_man_with_hat/hurt': Animation(load_images('entities/heros/the_man_with_hat/hurt', color_key_selector=True), loop=False, img_dur=8),
            'the_man_with_hat/death': Animation(load_images('entities/heros/the_man_with_hat/death', color_key_selector=True), loop=False, img_dur=8),

            'bomber/idle': Animation(load_images('entities/bomber/idle', player_loader=True, scale_size=0.6)),
            'bomber/death': Animation(load_images('entities/bomber/death', player_loader=True, scale_size=0.6), loop=False),
            'bomber/walk': Animation(load_images('entities/bomber/walk', player_loader=True, scale_size=0.6), img_dur=3),
            'bomber/run': Animation(load_images('entities/bomber/run', player_loader=True, scale_size=0.6), img_dur=3),
            'bomber/hurt': Animation(load_images('entities/bomber/hurt', player_loader=True, scale_size=0.6), loop=False, img_dur=8),

            'freezer/idle': Animation(load_images('entities/freezer/idle', player_loader=True, scale_size=0.9)),
            'freezer/death': Animation(load_images('entities/freezer/idle', player_loader=True, scale_size=0.9), loop=False),
            'freezer/walk': Animation(load_images('entities/freezer/walk', player_loader=True, scale_size=0.9), img_dur=4),
            'freezer/run': Animation(load_images('entities/freezer/walk', player_loader=True, scale_size=0.9), img_dur=4),
            'freezer/hurt': Animation(load_images('entities/freezer/hurt', player_loader=True, scale_size=0.9), loop=False, img_dur=8),
            'freezer/attack': Animation(load_images('entities/freezer/attack', player_loader=True, scale_size=0.9), loop=False, img_dur=4),

            'tank/idle': Animation(load_images('entities/tank/idle', player_loader=True, scale_size=0.9)),
            'tank/death': Animation(load_images('entities/tank/death', player_loader=True, scale_size=0.9), loop=False),
            'tank/walk': Animation(load_images('entities/tank/walk', player_loader=True, scale_size=0.9), img_dur=4),
            'tank/run': Animation(load_images('entities/tank/walk', player_loader=True, scale_size=0.9), img_dur=4),
            'tank/hurt': Animation(load_images('entities/tank/hurt', player_loader=True, scale_size=0.9), loop=False, img_dur=8),
            'tank/attack': Animation(load_images('entities/tank/attack', player_loader=True, scale_size=0.9), loop=False, img_dur=4),

            'samurai/idle': Animation(load_images('entities/samurai/idle', player_loader=True, scale_size=0.7)),
            'samurai/death': Animation(load_images('entities/samurai/death', player_loader=True, scale_size=0.7), loop=False, img_dur=8),
            'samurai/walk': Animation(load_images('entities/samurai/walk', player_loader=True, scale_size=0.7)),
            'samurai/run': Animation(load_images('entities/samurai/run', player_loader=True, scale_size=0.7)),
            'samurai/hurt': Animation(load_images('entities/samurai/hurt', player_loader=True, scale_size=0.7)),
            'samurai/attack_1': Animation(load_images('entities/samurai/attack_1', player_loader=True, scale_size=0.7), loop=False, img_dur=8),
            'samurai/attack_3': Animation(load_images('entities/samurai/attack_3', player_loader=True, scale_size=0.7), loop=False, img_dur=8),

            'boss_normal/idle': Animation(load_images('entities/Boss/idle/normal', player_loader=True, scale_size=1)),
            'boss_normal/walk': Animation(load_images('entities/Boss/walk/normal', player_loader=True, scale_size=1)),
            'boss_normal/run': Animation(load_images('entities/Boss/run/normal', player_loader=True, scale_size=1)),
            'boss_normal/hurt': Animation(load_images('entities/Boss/hurt/normal', player_loader=True, scale_size=1), loop=False, img_dur=8),
            'boss_normal/attack': Animation(load_images('entities/Boss/attack/normal', player_loader=True, scale_size=1), loop=False, img_dur=8),
            'boss_red/idle': Animation(load_images('entities/Boss/idle/red', player_loader=True, scale_size=1)),
            'boss_red/walk': Animation(load_images('entities/Boss/walk/red', player_loader=True, scale_size=1)),
            'boss_red/run': Animation(load_images('entities/Boss/run/red', player_loader=True, scale_size=1)),
            'boss_red/hurt': Animation(load_images('entities/Boss/hurt/red', player_loader=True, scale_size=1), loop=False, img_dur=8),
            'boss_red/attack': Animation(load_images('entities/Boss/attack/red', player_loader=True, scale_size=1), loop=False, img_dur=8),
            'boss_red/death': Animation(load_images('entities/Boss/death', player_loader=True, scale_size=1), loop=False, img_dur=8),
        }

        self.effects = {
            'Circle_explosion': Animation(load_images('effects/Circle_explosion', color_key_selector=True, scale_size=0.5), loop=False),
            'item_eating': Animation(load_images('effects/item_eating', color_key_selector=True, scale_size=0.5), loop=False),
            'item_loading': Animation(load_images('effects/item_loading', color_key_selector=True, scale_size=0.5), loop=False),
            'item_destroyed': Animation(load_images('effects/item_destroyed', color_key_selector=True, scale_size=0.5), loop=False),
            'Explosion_blue_circle': Animation(load_images('effects/Explosion_blue_circle', color_key_selector=True, scale_size=0.5), loop=False),
            'Explosion_two_colors': Animation(load_images('effects/Explosion_two_colors', color_key_selector=True, scale_size=0.5), loop=False),
            'bullet_collision': Animation(load_images('effects/bullet_collision', color_key_selector=True, scale_size=0.5), loop=False),
            'bonefire': Animation(load_images('effects/bonefire', color_key_selector=True, scale_size=1)),
            'blood_explosion': Animation(load_images('effects/blood_explosion', color_key_selector=True, scale_size=0.5), loop=False),
            'colt': Animation(load_images('effects/Shooting/colt', color_key_selector=True, scale_size=0.5), loop=False, img_dur=2),
            'shotgun': Animation(load_images('effects/Shooting/shotgun', color_key_selector=True, scale_size=0.5), loop=False, img_dur=2),
            'revolver': Animation(load_images('effects/Shooting/revolver', color_key_selector=True, scale_size=0.5), loop=False, img_dur=2),
            'm95': Animation(load_images('effects/Shooting/m95', color_key_selector=True, scale_size=0.5), loop=False, img_dur=2),
        }

        self.music = {
            'background_theme_1': BASE_MUSIC_PATH + '33. The Clock Tower.mp3',
            'background_theme_2': BASE_MUSIC_PATH + '24. A Valley of Thieves.mp3',
            'background_theme_3': BASE_MUSIC_PATH + '14. Sacred Archives.mp3',
            'background_theme_4': BASE_MUSIC_PATH + '06. Wandering in the Palace.mp3',
            'multi_player_background': BASE_MUSIC_PATH + '22. The Darkest of Souls.mp3',
            'gameover': BASE_MUSIC_PATH + 'Undertale Game Over Theme.mp3',
            'boss_phase_1_1': BASE_MUSIC_PATH + '02. Dark Souls III.mp3',
            'boss_phase_1_2': BASE_MUSIC_PATH + '23. Judgement of Mourning.flac',
            'boss_phase_2_1': BASE_MUSIC_PATH + '24 Gates of Hell.mp3',
            'boss_phase_2_2': BASE_MUSIC_PATH + 'Ludwig, the Holy Blade   Bloodborne.mp3',
            'boss_phase_3_1': BASE_MUSIC_PATH + '51 Escaping the Sandworm.mp3',
            'boss_phase_3_2': BASE_MUSIC_PATH + '42. Shattered Memories.flac',
            'boss_phase_4_1': BASE_MUSIC_PATH + '56 Malenia, Blade of Miquella.mp3',
            'boss_phase_4_2': BASE_MUSIC_PATH + '29. Wing of Hypocrisy.flac',
            'boss_cutscene_1': BASE_MUSIC_PATH + '02 Opening.mp3',
            'boss_cutscene_2': BASE_MUSIC_PATH + '01 The Way of the Ghost.mp3',
            'boss_cutscene_3': BASE_MUSIC_PATH + '24. Ragnarök.mp3',
            'boss_cutscene_4': BASE_MUSIC_PATH + '4. Higgs.mp3',
            'ending': BASE_MUSIC_PATH + '1. Should We Have Connected.mp3',
            'menu': BASE_MUSIC_PATH + '01. Main Theme.mp3',
        }

        self.sounds = {
            #GAME
            'GameOver': load_sound('Game-Over.mp3'),
            'Winner': load_sound('Winner.mp3'),

            #ENTITIES
            'hero/death': load_sound('Hero Death.wav'),
            'hero/dash': load_sound('Hero Dash.wav'),
            'hero/jump': load_sound('Hero Jump.wav'),
            'hero/walk': load_sound('Hero Walk.wav'),
            
            'bomber/death': load_sound('Bomber Death.wav'),
            'bomber/walk': load_sound('Bomber Walk.wav'),
            'bomber/attack': load_sound('Bomber Attack.wav'),

            'samurai/death':load_sound('Samurai Death.wav'),
            'samurai/walk': load_sound('Samurai Walk.wav'),
            'samurai/attack': load_sound('Samurai Attack.wav'),
            
            'freezer/death': load_sound('Freezer Death.wav'),
            'freezer/attack': load_sound('Freezer Attack.wav'),

            'tank/death': load_sound('Tank Death.wav'),
            'tank/walk': load_sound('Tank Walk.wav'),
            'tank/attack': load_sound('Tank Attack.mp3'),

            'boss/walk': load_sound('Boss Walk.wav'),
            'boss/attack': load_sound('Boss Attack.wav'),
            'boss/death': load_sound('Boss Death.mp3'),
            'boss/teleport': load_sound('Teleport.mp3'),

            'item_apear': load_sound('item_apear.mp3'),
            'item_destruction': load_sound('item_destruction.mp3'),

            #BUTTONS
            'Cursor_1': load_sound('Click_1.wav'),
            'Cursor_2': load_sound('Click_2.wav'),
            'Cursor_3': load_sound('Click_3.wav'),
        }
        self.sound_manager.add_sfx('Hover',self.sounds['Cursor_2'])
        self.sound_manager.add_sfx('GameOver', self.sounds['GameOver'], 0.4)
        self.sound_manager.add_sfx('Winner', self.sounds['Winner'], 0.6)

        self.gun_assets = {
            'guns': {'colt': load_image('weapons/colt/colt.png', color_key_selector=True, color_key=(255, 255, 255)),
                     'shotgun': load_image('weapons/shotgun/shotgun.png', color_key_selector=True, color_key=(255, 255, 255)),
                     'revolver': load_image('weapons/revolver/revolver.png', color_key_selector=True, color_key=(255, 255, 255)),
                     'm95': load_image('weapons/m95/m95.png', color_key_selector=True, color_key=(255, 255, 255)),},
            'guns_bullets': {'colt': load_image('weapons/colt/bullet/bullet.png', color_key_selector=True),
                             'shotgun': load_image('weapons/shotgun/bullet/bullet.png', color_key_selector=True),
                             'revolver': load_image('weapons/revolver/bullet/bullet.png', color_key_selector=True),
                             'm95': load_image('weapons/m95/bullet/bullet.png', color_key_selector=True),
                             'freezer': load_image('weapons/freezer/bullet.png', color_key_selector=True, color_key=(255, 255, 255)),
                             'simple': load_image('weapons/simple/bullet.png', color_key_selector=True, color_key=(255, 255, 255)),
                             'blinder': load_image('weapons/blinder/bullet.png', color_key_selector=True, color_key=(0, 0, 0))},
        }

        pygame.time.delay(1)
        self.loading_done = True
    
    def run(self):
        cursor = load_image('normal_cursor.png')
        loading_thread = threading.Thread(target=self.loading_assets)
        loading_thread.start()

        loading = {
            0:load_image('Loading 1.png',color_key_selector=True),
            1:load_image('Loading 2.png',color_key_selector=True),
            2:load_image('Loading 3.png',color_key_selector=True),
            3:load_image('Loading Completed.png',color_key_selector=True)
        }

        dots = 0

        while not self.loading_done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            dots = (pygame.time.get_ticks()//500) % 3

            self.screen.blit(loading[dots],(0,0))
            render_mouse_cursor(self.screen,cursor)

            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)

            pygame.display.update()
            self.clock.tick(FPS)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self.sound_manager.play_sfx('Hover')
                    running = False
                if event.type == pygame.QUIT:
                    self.quit()
                
            self.screen.blit(loading[3],(0,0))
            render_mouse_cursor(self.screen,cursor)

            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)

            pygame.display.update()
            self.clock.tick(FPS)

        self.main_menu()

    def quit(self):
        pygame.quit()
        sys.exit()
    
    def back(self, running):
        running[0] = False

    def confirming_back(self, running, chose_char):
        chose_char[0] = True
        running[0] = False

    def client_show(self):
        if self.client is not None:
            client_text = f"Client: {self.client.name}#{self.client.hashtag}"
            draw_text_with_outline(self.screen, client_text, 
                                  load_font('Pixel Game.otf', 50), 
                                  1150, 825, (255, 255, 255), (0, 0, 0), 2, False)

    def main_menu(self):
        if self.last_music != 'menu':
            self.sound_manager.play_music(self.music['menu'])
            self.last_music = 'menu'
        buttons = [
            [
                Button('play', self, (95,395), (310,110), self.play_menu, sound_active=self.sounds['Cursor_3']),
                Button('account', self, (495,395), (310,110), self.account_management, sound_active=self.sounds['Cursor_3']),
            ],
            [
                Button('quit', self, (295,595), (310,110), self.quit, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0 # 0, 1

        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['main_menu'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def client_delete(self):
        self.client.close_client()
        del self.client
        self.client = None

    def logout_client(self):
        while self.client.running:
            self.client.send_logout_request()
            time.sleep(0.01)
        self.client_delete()

    def account_management(self):
        if self.client is None:
            buttons = [
                [
                    Button('signup', self, (95,395), (310,110), self.sign_up, sound_active=self.sounds['Cursor_3']),
                    Button('login', self, (495,395), (310,110), self.login, sound_active=self.sounds['Cursor_3']),
                ],
                [
                    Button('back2', self, (295,595), (310,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
                ]
            ]
            selected_index = 0
            column_index = 0 # 0, 1

            while True:
                #Events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                    
                    if event.type == pygame.KEYDOWN:
                        #Movement
                        if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                            self.sound_manager.play_sfx('Hover')
                            column_index = (column_index + 1) % 2
                            selected_index = 0
                        
                        if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                            self.sound_manager.play_sfx('Hover')
                            selected_index = (selected_index + 1) % 2
                        
                        #Activating
                        if event.key == pygame.K_RETURN:
                            buttons[column_index][selected_index].set_status('pressed')

                    #Mouse Movement
                    if event.type == pygame.MOUSEMOTION:
                        for c_index ,column in enumerate(buttons):
                            for s_index ,button in enumerate(column):
                                if button.rect.collidepoint(event.pos):
                                    column_index = c_index
                                    selected_index = s_index
                                    button.set_status('hovered')
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for c_index ,column in enumerate(buttons):
                            for s_index ,button in enumerate(column):
                                if button.rect.collidepoint(event.pos):
                                    column_index = c_index
                                    selected_index = s_index
                                    button.set_status('pressed')
                
                #Conditions
                if buttons[column_index][selected_index].status != 'pressed':
                    buttons[column_index][selected_index].set_status('hovered')
                
                #Rendering
                self.screen.blit(self.assets['account_menu'],(0,0))

                for column in buttons:
                    for button in column:
                        button.render(self.screen)
                
                render_mouse_cursor(self.screen, self.assets['normal_cursor'])
                
                self.screen.blit(scanlines,(0,0))
                draw_noise(self.screen)
                
                pygame.display.update()
                self.clock.tick(FPS)

                for column in buttons:
                    for button in column:
                        if button.status == 'pressed':
                            button.execute()
                
                #Reseting
                for column in buttons:
                    for button in column:
                        button.set_status('idle')
        else:
            running = [True]
            def logout(running):
                self.logout_client()
                running[0] = False
            
            buttons = [
                Button('logout', self, (95,695), (310,110), logout, running, self.sounds['Cursor_3']),
                Button('back2', self, (595,695), (310,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
            selected_index = 0

            while running[0]:
                #Events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                    
                    if event.type == pygame.KEYDOWN:
                        #Movement
                        if (event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT):
                            self.sound_manager.play_sfx('Hover')
                            selected_index = (selected_index + 1) % 2
                        
                        #Activating
                        if event.key == pygame.K_RETURN:
                            buttons[selected_index].set_status('pressed')
                    
                    #Mouse Movement
                    if event.type == pygame.MOUSEMOTION:
                        for s_index ,button in enumerate(buttons):
                            if button.rect.collidepoint(event.pos):
                                selected_index = s_index
                                button.set_status('hovered')
                    
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for s_index ,button in enumerate(buttons):
                            if button.rect.collidepoint(event.pos) and event.button == 1:
                                selected_index = s_index
                                button.set_status('pressed')
                
                #Conditions
                if buttons[selected_index].status != 'pressed':
                    buttons[selected_index].set_status('hovered')

                #Rendering
                self.screen.blit(self.assets['user_info'],(0,0))

                draw_text_with_outline(self.screen, self.client.name, load_font('Pixel Game.otf', 36), 225, 395, (109,93,57), (0,0,0), 2, False)
                draw_text_with_outline(self.screen, self.client.hashtag, load_font('Pixel Game.otf', 36), 225, 525, (109,93,57), (0,0,0), 2, False)

                for button in buttons:
                    button.render(self.screen)

                render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
                self.screen.blit(scanlines,(0,0))
                draw_noise(self.screen)

                pygame.display.update()
                self.clock.tick(FPS)
                
                for button in buttons:
                    if button.status == 'pressed':
                        button.execute()
            
                #Reseting
                for button in buttons:
                    button.set_status('idle')

    def sign_up(self):
        running = [True]

        def confirm(username, hashtag, running):
            try:
                self.client_creation(username, hashtag, login=False)
            except ValueError:
                draw_text_with_outline(self.screen, 'Player Already Exists!', load_font('Pixel Game.otf',72), 465, 385, (255,255,255), (0,0,0))
                draw_text_with_outline(self.screen, 'Press Any Button To Continue', load_font('Pixel Game.otf',72), 465, 585, (255,255,255), (0,0,0))

                last_screen = self.screen.copy()

                running[0] = True
                while running[0]:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.quit()
                        
                        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            running[0] = False
                    
                    self.screen.blit(last_screen, (0,0))

                    pygame.display.update()
                    self.clock.tick(FPS)
                self.client_delete()
                return
            
            self.client.error_message = None
            running[0] = False
            self.main_menu()

        username = ''
        hashtag = ''

        buttons = [
            [
                TextBox('text_box', self, (95,195), (810,110), 12, load_font('Ithaca.ttf',72), (109,93,57), self.screen, self.sounds['Cursor_3'])
            ],
            [
                TextBox('text_box', self, (95,495), (810,110), 8, load_font('Ithaca.ttf',72), (109,93,57), self.screen, self.sounds['Cursor_3'])
            ],
            [
                Button('confirm', self, (95,695), (310,110), confirm, (username, hashtag, running), self.sounds['Cursor_3']),
                Button('back2', self, (595,695), (310,110), self.back, running, self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:

                    #Movement
                    if event.key == pygame.K_UP:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index - 1) % 3
                        if column_index != 2:
                            selected_index = 0

                    if event.key == pygame.K_DOWN:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 3
                        if column_index != 2:
                            selected_index = 0

                    if (event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT) and column_index == 2:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')
                
                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos) and event.button == 1:
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')

            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            username = buttons[0][0].text
            hashtag = buttons[1][0].text
            buttons[2][0].arguments = (username, hashtag, running)
            #Rendering
            self.screen.blit(self.assets['sign_up'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def login(self):
        running = [True]

        def confirm(username, hashtag, running):
            try:
                self.client_creation(username, hashtag, login=True)
            except ValueError:
                draw_text_with_outline(self.screen, 'Player Not Found!', load_font('Pixel Game.otf',72), 465, 385, (255,255,255), (0,0,0))
                draw_text_with_outline(self.screen, 'Press Any Button To Continue', load_font('Pixel Game.otf',72), 465, 585, (255,255,255), (0,0,0))

                last_screen = self.screen.copy()

                running[0] = True
                while running[0]:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.quit()
                        
                        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            running[0] = False
                    
                    self.screen.blit(last_screen, (0,0))

                    pygame.display.update()
                    self.clock.tick(FPS)
                self.client_delete()
                return
            
            except ConnectionRefusedError:
                draw_text_with_outline(self.screen, 'Player Already Logged In!', load_font('Pixel Game.otf',72), 465, 385, (255,255,255), (0,0,0))
                draw_text_with_outline(self.screen, 'Press Any Button To Continue', load_font('Pixel Game.otf',72), 465, 585, (255,255,255), (0,0,0))

                last_screen = self.screen.copy()

                running[0] = True
                while running[0]:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.quit()
                        
                        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            running[0] = False
                    
                    self.screen.blit(last_screen, (0,0))

                    pygame.display.update()
                    self.clock.tick(FPS)
                self.client_delete()
                return
            
            self.client.error_message = None
            running[0] = False
            self.main_menu()

        username = ''
        hashtag = ''

        buttons = [
            [
                TextBox('text_box', self, (95,195), (810,110), 12, load_font('Ithaca.ttf',72), (109,93,57), self.screen, self.sounds['Cursor_3'])
            ],
            [
                TextBox('text_box', self, (95,495), (810,110), 8, load_font('Ithaca.ttf',72), (109,93,57), self.screen, self.sounds['Cursor_3'])
            ],
            [
                Button('confirm', self, (95,695), (310,110), confirm, (username, hashtag, running), self.sounds['Cursor_3']),
                Button('back2', self, (595,695), (310,110), self.back, running, self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:

                    #Movement
                    if event.key == pygame.K_UP:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index - 1) % 3
                        if column_index != 2:
                            selected_index = 0

                    if event.key == pygame.K_DOWN:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 3
                        if column_index != 2:
                            selected_index = 0

                    if (event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT) and column_index == 2:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')
                
                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos) and event.button == 1:
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')

            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            username = buttons[0][0].text
            hashtag = buttons[1][0].text
            buttons[2][0].arguments = (username, hashtag, running)
            
            #Rendering
            self.screen.blit(self.assets['sign_up'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def play_menu(self):
        buttons = [
            [
                Button('single', self, (95,395), (310,110), self.singleplayer_menu, sound_active=self.sounds['Cursor_3']),
                Button('multi', self, (495,395), (310,110), self.multiplayer_menu, sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('back2', self, (295,595), (310,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0
        
        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['play_menu'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def singleplayer_menu(self):
        characters = ['redhood','beanhead','crow','the_man_with_hat']

        file = open('following_chapter.bin', 'r')
        chapter = int(file.read())
        file.close()

        def new(character):
            file = open('following_chapter.bin', 'w')
            file.write('0')
            file.close()

            self.singleplayer_game(character)

        def character_select():
            characters = ['redhood','beanhead','crow','the_man_with_hat']
            last_character = self.character_index

            def next_character():
                self.character_index = (self.character_index + 1) % 4
            
            def prev_character():
                self.character_index = (self.character_index - 1) % 4
            
            def last():
                self.character_index = last_character
                self.singleplayer_menu()
            
            buttons = [
                [
                    Button('left', self, (95,295), (110,110), prev_character, sound_active=self.sounds['Cursor_3']),
                    Button('right', self, (800,295), (110,110), next_character, sound_active=self.sounds['Cursor_3'])
                ],
                [
                    Button('confirm', self, (95,695), (310,110), self.singleplayer_menu, sound_active=self.sounds['Cursor_3']),
                    Button('back2', self, (595,695), (310,110), last, sound_active=self.sounds['Cursor_3'])
                ]
            ]
            selected_index = 0
            column_index = 0

            while True:
                #Events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                    
                    if event.type == pygame.KEYDOWN:
                        #Movement
                        if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                            self.sound_manager.play_sfx('Hover')
                            column_index = (column_index + 1) % 2
                            selected_index = 0
                        
                        if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)):
                            self.sound_manager.play_sfx('Hover')
                            selected_index = (selected_index + 1) % 2
                        
                        #Activating
                        if event.key == pygame.K_RETURN:
                            buttons[column_index][selected_index].set_status('pressed')

                    #Mouse Movement
                    if event.type == pygame.MOUSEMOTION:
                        for c_index ,column in enumerate(buttons):
                            for s_index ,button in enumerate(column):
                                if button.rect.collidepoint(event.pos):
                                    column_index = c_index
                                    selected_index = s_index
                                    button.set_status('hovered')
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for c_index ,column in enumerate(buttons):
                            for s_index ,button in enumerate(column):
                                if button.rect.collidepoint(event.pos):
                                    column_index = c_index
                                    selected_index = s_index
                                    button.set_status('pressed')
                
                #Conditions
                if buttons[column_index][selected_index].status != 'pressed':
                    buttons[column_index][selected_index].set_status('hovered')
                
                #Rendering
                self.screen.blit(self.assets['character_select_single'],(0,0))

                for column in buttons:
                    for button in column:
                        button.render(self.screen)
                
                player = pygame.transform.scale_by(self.player_assets[characters[self.character_index]],10)
                player_rect = player.get_rect()
                player_pos = (500 - (player_rect.width / 2), 350 - (player_rect.height / 2))
                self.screen.blit(player, player_pos)
                
                self.client_show()
                render_mouse_cursor(self.screen, self.assets['normal_cursor'])
                
                self.screen.blit(scanlines,(0,0))
                draw_noise(self.screen)
                
                pygame.display.update()
                self.clock.tick(FPS)

                for column in buttons:
                    for button in column:
                        if button.status == 'pressed':
                            button.execute()
                
                #Reseting
                for column in buttons:
                    for button in column:
                        button.set_status('idle')
            
        buttons=[
            [
                Button('new', self, (95,395), (310,110), new, characters[self.character_index], self.sounds['Cursor_3']),
                Button('continue', self, (595,395), (310,110), self.singleplayer_game, (characters[self.character_index], chapter),sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('character', self, (95,595), (310,110), character_select, sound_active=self.sounds['Cursor_3']),
                Button('back2', self, (595,595), (310,110), self.play_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        if chapter >= 4:
            buttons[0][1] = Button('continue', self, (595,395), (310,110), self.boss_level, (characters[self.character_index], None), sound_active=self.sounds['Cursor_3'])
        selected_index = 0
        column_index = 0

        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)):
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['singleplayer_menu'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def multiplayer_menu(self):
        buttons = [
            [
                Button('local', self, (95,395), (310,110), self.local_play, sound_active=self.sounds['Cursor_3']),
                Button('online', self, (495,395), (310,110), self.online_play, sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('back2', self, (295,595), (310,110), self.play_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['multiplayer_menu'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def character_select_single(self, character_index, chose_char, back_button_enabled=True):
        running = [True]
        characters = ['redhood','beanhead','crow','the_man_with_hat']
        last_character = character_index

        def next_character(character_index):
            character_index[0] = (character_index[0] + 1) % 4
        
        def prev_character(character_index):
            character_index[0] = (character_index[0] - 1) % 4
        
        def exit(running):
            running[0] = False
        
        buttons = [
            [
                Button('left', self, (95,295), (110,110), prev_character, (character_index, ), sound_active=self.sounds['Cursor_3']),
                Button('right', self, (800,295), (110,110), next_character, (character_index, ), sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('confirm', self, (95,695), (310,110), self.confirming_back, (running, chose_char, ), sound_active=self.sounds['Cursor_3']),
                Button('back2', self, (595,695), (310,110), exit if back_button_enabled else None, (running, ), sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)):
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['character_select_single'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            player = pygame.transform.scale_by(self.player_assets[characters[character_index[0]]],10)
            player_rect = player.get_rect()
            player_pos = (500 - (player_rect.width / 2), 350 - (player_rect.height / 2))
            self.screen.blit(player, player_pos)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def character_select_multi(self, character_index):
        characters = ['redhood','beanhead','crow','the_man_with_hat']
        last_character = character_index
        
        running = [True]

        def last(character_index, last_character, running):
            character_index = last_character
            running[0] = False
            
        def next_character(character_index, player_number):
            character_index[player_number-1] = (character_index[player_number-1] + 1) % 4
        
        def prev_character(character_index, player_number):
            character_index[player_number-1] = (character_index[player_number-1] - 1) % 4

        buttons = [
            [
                Button('left', self, (95,145), (110,110), prev_character, (character_index, 1), self.sounds['Cursor_3']),
                Button('right', self, (800,145), (110,110), next_character, (character_index, 1), self.sounds['Cursor_3']),
            ],
            [
                Button('left', self, (95,445), (110,110), prev_character, (character_index, 2), self.sounds['Cursor_3']),
                Button('right', self, (800,445), (110,110), next_character, (character_index, 2), self.sounds['Cursor_3']),
            ],
            [
                Button('confirm', self, (95,695), (310,110), self.back, running, self.sounds['Cursor_3']),
                Button('back2', self, (595,695), (310,110), last, (character_index, last_character, running), self.sounds['Cursor_3']),
            ]
        ]
        selected_index = 0
        column_index = 0
        
        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if event.key == pygame.K_UP :
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index - 1) % 3
                    
                    if event.key == pygame.K_DOWN:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 3
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)):
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['character_select_multi'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)

            player = pygame.transform.scale_by(self.player_assets[characters[character_index[0]]],5)
            player_rect = player.get_rect()
            self.screen.blit(player,(500 - (player_rect.width / 2), 200 - (player_rect.height / 2)))

            player = pygame.transform.scale_by(self.player_assets[characters[character_index[1]]],5)
            player_rect = player.get_rect()
            self.screen.blit(player,(500 - (player_rect.width / 2), 500 - (player_rect.height / 2)))
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def local_play(self):
        characters = ['redhood','beanhead','crow','the_man_with_hat']
        character_index = [0,0]
        
        def map_selection():
            running = [True]
            maps = [load_image('Map1.png'), load_image('Map2.png'), load_image('Map3.png'), load_image('Map4.png')]

            def set_map(index, running):
                self.arena_ID = index
                running[0] = False
            
            buttons = [
                [
                    Button('photo', self, (95,95), (110,110), set_map, (4,running), self.sounds['Cursor_3']),
                    Button('photo', self, (695,95), (110,110), set_map, (3,running), self.sounds['Cursor_3'])
                ],
                [
                    Button('photo', self, (95,395), (110,110), set_map, (2,running), self.sounds['Cursor_3']),
                    Button('photo', self, (695,395), (110,110), set_map, (1,running), self.sounds['Cursor_3'])
                ],
                [
                    Button('back1', self, (395,695), (210,110), self.back, running, self.sounds['Cursor_3']),
                ]
            ]
            selected_index = 0
            column_index = 0


            while running[0]:
                #Events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                        
                    if event.type == pygame.KEYDOWN:
                        #Movement
                        if event.key == pygame.K_UP:
                            self.sound_manager.play_sfx('Hover')
                            column_index = (column_index - 1) % 3
                            if column_index == 2:
                                selected_index = 0
                        
                        if event.key == pygame.K_DOWN:
                            self.sound_manager.play_sfx('Hover')
                            column_index = (column_index + 1) % 3
                            if column_index == 2:
                                selected_index = 0
                        
                        if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index != 2:
                            self.sound_manager.play_sfx('Hover')
                            selected_index = (selected_index + 1) % 2
                        
                        #Activating
                        if event.key == pygame.K_RETURN:
                            buttons[column_index][selected_index].set_status('pressed')

                    #Mouse Movement
                    if event.type == pygame.MOUSEMOTION:
                        for c_index ,column in enumerate(buttons):
                            for s_index ,button in enumerate(column):
                                if button.rect.collidepoint(event.pos):
                                    column_index = c_index
                                    selected_index = s_index
                                    button.set_status('hovered')
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for c_index ,column in enumerate(buttons):
                            for s_index ,button in enumerate(column):
                                if button.rect.collidepoint(event.pos):
                                    column_index = c_index
                                    selected_index = s_index
                                    button.set_status('pressed')
                
                #Conditions
                if buttons[column_index][selected_index].status != 'pressed':
                    buttons[column_index][selected_index].set_status('hovered')
                
                #Rendering
                self.screen.blit(self.assets['map_select'],(0,0))

                for column in buttons:
                    for button in column:
                        button.render(self.screen)
                
                self.screen.blit(maps[0],(125,125))
                self.screen.blit(maps[1],(725,125))
                self.screen.blit(maps[2],(125,425))
                self.screen.blit(maps[3],(725,425))
                self.client_show()
                render_mouse_cursor(self.screen, self.assets['normal_cursor'])
                
                self.screen.blit(scanlines,(0,0))
                draw_noise(self.screen)
                
                pygame.display.update()
                self.clock.tick(FPS)

                for column in buttons:
                    for button in column:
                        if button.status == 'pressed':
                            button.execute()
                
                #Reseting
                for column in buttons:
                    for button in column:
                        button.set_status('idle')

        buttons = [
                [
                    Button('start', self, (95,395), (310,110), self.multiplayer_game, (characters[character_index[0]], characters[character_index[1]]), self.sounds['Cursor_3']),
                    Button('map', self, (595,395), (310,110), map_selection, sound_active=self.sounds['Cursor_3'])
                ],
                [
                    Button('character', self, (95,595), (310,110), self.character_select_multi, (character_index, ), self.sounds['Cursor_3']),
                    Button('back2', self, (595,595), (310,110), self.multiplayer_menu, sound_active=self.sounds['Cursor_3'])
                ]
        ]
        selected_index = 0
        column_index = 0
        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)):
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            buttons[0][0].arguments = (characters[character_index[0]], characters[character_index[1]])
            
            #Rendering
            self.screen.blit(self.assets['local_menu'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def online_play(self):
        if self.client is None:
            draw_text_with_outline(self.screen, 'You Do Not Have An Account!', load_font('Pixel Game.otf',72), 465, 385, (255,255,255), (0,0,0))
            draw_text_with_outline(self.screen, 'Press Any Button To Continue', load_font('Pixel Game.otf',72), 465, 585, (255,255,255), (0,0,0))
            
            last_screen = self.screen.copy()

            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                        
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        running = False
                    
                self.screen.blit(last_screen, (0,0))

                pygame.display.update()
                self.clock.tick(FPS)
                
            return
        
        self.network_game_mode = None
        
        buttons = [
            [
                Button('invite', self, (95,395), (310,110), self.invite_player, sound_active=self.sounds['Cursor_3']),
                Button('random', self, (495,395), (310,110), self.select_mode, sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('invitation', self, (95,595), (310,110), self.handle_incoming_invitation, sound_active=self.sounds['Cursor_3']),
                Button('back2', self, (495,595), (310,110), self.multiplayer_menu, sound_active=self.sounds['Cursor_3'])  # Fixed: was self.multiplayer_game
            ]
        ]
        selected_index = 0
        column_index = 0
        
        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)):  # Fixed: removed condition for column_index == 0
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['online_select'],(0,0))  # Fixed: was self.assets['play_menu']

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')
    
    def invite_player(self):
        running = [True]

        def confirm(username, hashtag, running):
            if not username.strip() or not hashtag.strip():
                self._show_error_message('Please fill both fields!')
                return
            
            running[0] = False
            self._send_invitation_persistent(username.strip(), hashtag.strip())

        username = ''
        hashtag = ''

        buttons = [
            [
                TextBox('text_box', self, (95,195), (810,110), 12, load_font('Ithaca.ttf',72), (109,93,57), self.screen, self.sounds['Cursor_3'])
            ],
            [
                TextBox('text_box', self, (95,495), (810,110), 8, load_font('Ithaca.ttf',72), (109,93,57), self.screen, self.sounds['Cursor_3'])
            ],
            [
                Button('send', self, (95,695), (310,110), confirm, (username, hashtag, running), self.sounds['Cursor_3']),
                Button('back2', self, (595,695), (310,110), self.back, running, self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if event.key == pygame.K_UP:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index - 1) % 3
                        if column_index != 2:
                            selected_index = 0

                    if event.key == pygame.K_DOWN:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 3
                        if column_index != 2:
                            selected_index = 0

                    if (event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT) and column_index == 2:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')
                
                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos) and event.button == 1:
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')

            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            username = buttons[0][0].text
            hashtag = buttons[1][0].text
            buttons[2][0].arguments = (username, hashtag, running)
            
            #Rendering
            self.screen.blit(self.assets['invite_menu'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def _send_invitation_persistent(self, username, hashtag):
        frame_index = 0
        frame_counter = 0
        animation_speed = 24
        
        while not self.client.invitation_sent_successfully and not self.client.error_message:
            self.client.send_invitation(username, hashtag)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.client.clear_invitation_info()
                        return
            
            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['sending_invitation'])
                frame_counter = 0
            
            self.screen.blit(self.assets['sending_invitation'][frame_index], (0, 0))
            
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            time.sleep(0.001)
        
        if self.client.error_message:
            self._show_error_message(self.client.error_message)
            return
        
        self._wait_for_invitation_response()

    def _wait_for_invitation_response(self):
        timeout = 30
        start_time = time.time()
        
        def cancel_invitation():
            cancel_wait_start = time.time()
            frame_index = 0
            frame_counter = 0
            animation_speed = 24
            
            while self.client.invitation_ongoing and time.time() - cancel_wait_start < 3:
                self.client.send_invitation_cancel()

                frame_counter += 1
                if frame_counter >= animation_speed:
                    frame_index = (frame_index + 1) % len(self.assets['canceling_invitation'])
                    frame_counter = 0

                self.screen.blit(self.assets['canceling_invitation'][frame_index], (0, 0))
                render_mouse_cursor(self.screen, self.assets['normal_cursor'])
                self.client_show()
                self.screen.blit(scanlines, (0, 0))
                draw_noise(self.screen)
                pygame.display.update()
                self.clock.tick(FPS)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                
                time.sleep(0.1)
            
            self.client.clear_invitation_info()
            self.online_play()
        
        cancel_button = Button('back1', self, (395, 695), (210, 110), cancel_invitation, sound_active=self.sounds['Cursor_3'])
        
        while (time.time() - start_time) < timeout:
            if self.client.invitation_accepted:
                self._handle_invitation_accepted()
                return
            elif hasattr(self.client, 'invitation_rejected') and self.client.invitation_rejected:
                self._handle_invitation_rejected()
                return
            elif not self.client.invitation_ongoing:
                self.online_play()
                return
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                    
                if event.type == pygame.MOUSEMOTION:
                    if cancel_button.rect.collidepoint(event.pos):
                        cancel_button.set_status('hovered')
                    else:
                        cancel_button.set_status('idle')
                        
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if cancel_button.rect.collidepoint(event.pos):
                        cancel_button.set_status('pressed')
            
            self.screen.blit(self.assets['waiting_for_accept'], (0, 0))
            
            remaining_time = int(timeout - (time.time() - start_time))
            time_text = f"Time remaining: {remaining_time}s"
            draw_text_with_outline(self.screen, time_text, 
                                load_font('Pixel Game.otf', 36), 
                                500, 845, (255, 255, 255), (0, 0, 0), 2, True)
            
            if hasattr(self.client, 'player_invitation_info') and self.client.player_invitation_info:
                invited_player = f"Waiting for {self.client.player_invitation_info['name']}#{self.client.player_invitation_info['hashtag']}"
                draw_text_with_outline(self.screen, invited_player, 
                                    load_font('Pixel Game.otf', 28), 
                                    500, 870, (200, 200, 255), (0, 0, 0), 2, True)
            
            cancel_button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            if cancel_button.status == 'pressed':
                cancel_button.execute()
                return
        
        self.client.send_invitation_cancel()
        time.sleep(0.2)
        self.client.clear_invitation_info()
        self._show_error_message("Invitation timed out")
        self.online_play()

    def _handle_invitation_accepted(self):
        start_time = time.time()
        while time.time() - start_time < 2:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

            self.screen.blit(self.assets['invitation_accepted'], (0, 0))
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

        self.network_game_mode = 'SPFM'
        self.client_character_selection(back_button_enabled=False)

    def _handle_invitation_rejected(self):
        start_time = time.time()

        while time.time() - start_time < 2:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            
            self.screen.blit(self.assets['invitation_rejected'], (0, 0))
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            pygame.display.update()
            self.clock.tick(FPS)
        
        self.client.clear_invitation_info()
        self.online_play()

    def _show_error_message(self, message):
        if self.client:
            self.client.error_message = None
            self.client.error_type = None
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
            

            self.screen.blit(self.assets['error_page'], (0, 0))
            draw_text_with_outline(self.screen, 'Error', 
                                load_font('Pixel Game.otf', 72), 
                                500, 345, (255, 100, 100), (0, 0, 0), 2, True)
            draw_text_with_outline(self.screen, message, 
                                load_font('Pixel Game.otf', 36), 
                                500, 425, (255, 255, 255), (0, 0, 0), 2, True)
            draw_text_with_outline(self.screen, 'Click or Press Any Key to Continue', 
                                load_font('Pixel Game.otf', 36), 
                                500, 585, (255, 255, 255), (0, 0, 0), 2, True)
            
            self.client_show()
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
        
    def handle_incoming_invitation(self):
        if (self.client and self.client.invitation_received and self.client.invitation_ongoing):    
            self.show_invitation_dialog()
            return
        else:
            self._show_waiting_for_invitation()

    def _show_waiting_for_invitation(self):
        running = [True]
        
        def go_back():
            running[0] = False
            self.online_play()
        
        buttons = [
            Button('back1', self, (395, 695), (210, 110), go_back, sound_active=self.sounds['Cursor_3'])
        ]
        
        while running[0]:
            if (self.client and self.client.invitation_received and not self.client.invitation_ongoing):
                self.show_invitation_dialog()
                return
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        buttons[0].set_status('pressed')
                
                if event.type == pygame.MOUSEMOTION:
                    if buttons[0].rect.collidepoint(event.pos):
                        buttons[0].set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if buttons[0].rect.collidepoint(event.pos):
                        buttons[0].set_status('pressed')
            
            if buttons[0].status != 'pressed':
                buttons[0].set_status('hovered')
            
            # Rendering
            self.screen.blit(self.assets['waiting_for_invitation'], (0, 0))
            
            buttons[0].render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            if buttons[0].status == 'pressed':
                buttons[0].execute()
            
            buttons[0].set_status('idle')

    def show_invitation_dialog(self):
        if not (self.client and self.client.invitation_received and self.client.invitation_ongoing):
            self.online_play()
            return
        
        inviter = self.client.player_invitation_info
        dialog_running = [True]
        
        def accept_invitation():
            dialog_running[0] = False
            self._send_invitation_acceptance()
            self._handle_invitation_accepted()
        
        def decline_invitation():
            dialog_running[0] = False
            self._send_invitation_rejection()
            self.online_play()
        
        buttons = [
            Button('accept', self, (95, 495), (310, 110), accept_invitation, sound_active=self.sounds['Cursor_3']),
            Button('decline', self, (495, 495), (310, 110), decline_invitation, sound_active=self.sounds['Cursor_3'])
        ]
        selected_index = 0
        
        start_time = time.time()
        check_interval = 1.0
        last_check_time = start_time
        
        while dialog_running[0]:
            current_time = time.time()
            
            if current_time - last_check_time >= check_interval:
                if not self.client.invitation_ongoing:
                    self._show_error_message("Invitation is no longer valid")
                    self.online_play()
                    return
                last_check_time = current_time
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_LEFT) or (event.key == pygame.K_RIGHT):
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2

                    if event.key == pygame.K_RETURN:
                        buttons[selected_index].set_status('pressed')
                
                if event.type == pygame.MOUSEMOTION:
                    for s_index, button in enumerate(buttons):
                        if button.rect.collidepoint(event.pos):
                            selected_index = s_index
                            button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for s_index, button in enumerate(buttons):
                        if button.rect.collidepoint(event.pos):
                            selected_index = s_index
                            button.set_status('pressed')
            
            if buttons[selected_index].status != 'pressed':
                buttons[selected_index].set_status('hovered')
            
            self.screen.blit(self.assets['match_invitation'], (0, 0))
            
            invitation_text = f"Invitation from {inviter['name']}#{inviter['hashtag']}"
            draw_text_with_outline(self.screen, invitation_text, load_font('Pixel Game.otf', 46), 
                                465, 400, (109, 93, 57), (0, 0, 0), 2, True)
            
            for button in buttons:
                button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            for button in buttons:
                if button.status == 'pressed':
                    button.execute()
                    break
            
            for button in buttons:
                button.set_status('idle')

    def _send_invitation_acceptance(self):
        frame_index = 0
        frame_counter = 0
        animation_speed = 24
        
        while self.client.invitation_ongoing and not self.client.invitation_accepted:
            self.client.send_invitation_acceptance()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            
            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['sending_acceptance'])
                frame_counter = 0
            
            self.screen.blit(self.assets['sending_acceptance'][frame_index], (0, 0))
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            time.sleep(0.001)

    def _send_invitation_rejection(self):
        frame_index = 0
        frame_counter = 0
        animation_speed = 24
        
        while self.client.invitation_ongoing:
            self.client.send_invitation_rejection()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['sending_rejection'])
                frame_counter = 0
            self.screen.blit(self.assets['sending_rejection'][frame_index], (0, 0))
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            time.sleep(0.001)
        
        self.client.clear_invitation_info()

    def random_play(self, mode: MMode):
        self.network_game_mode = None
        if mode == MMode.OVV2:
            self.network_game_mode = 'OVV2'
        if mode == MMode.OVV3:
            self.network_game_mode = 'OVV3'
        if mode == MMode.OVV4:
            self.network_game_mode = 'OVV4'
        if mode == MMode.TVV2:
            self.network_game_mode = 'TVV2'

        self.client_character_selection()

    def client_character_selection(self, back_button_enabled=True):
        characters = ['redhood','beanhead','crow','the_man_with_hat']
        characters_index = [0]
        character_chosed = [False]
        self.character_select_single(characters_index, character_chosed, back_button_enabled)
        if character_chosed[0] == False:
            return
        selected_operator = characters[characters_index[0]]
        self.client.send_match_request(self.network_game_mode, selected_operator)

        frame_index = 0
        frame_counter = 0
        animation_speed = 24

        while self.client.mode is None and self.client.player_operator is None:
            self.client.send_match_request(self.network_game_mode, selected_operator)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['sending_match_request'])
                frame_counter = 0
            self.screen.blit(self.assets['sending_match_request'][frame_index], (0, 0))
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            pygame.display.update()
            self.clock.tick(FPS)
            
            time.sleep(0.001)

        self.join_network_lobby(cancel_button_available=back_button_enabled)

    def select_mode(self):
        buttons = [
            [
                Button('1v1', self, (95,415), (310,110), self.random_play, MMode.OVV2, self.sounds['Cursor_3']),
                Button('1v1v1', self, (495,415), (310,110), self.random_play, MMode.OVV3, self.sounds['Cursor_3'])
            ],
            [
                Button('x', self, (395,515), (110,110), self.online_play, sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('1v1v1v1', self, (95,615), (310,110), self.random_play, MMode.OVV4, self.sounds['Cursor_3']),
                Button('2v2', self, (495,615), (310,110), self.random_play, MMode.TVV2, self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if event.key == pygame.K_UP:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index - 1) % 3
                        if column_index == 1:
                            selected_index = 0

                    if event.key == pygame.K_DOWN:
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 3
                        if column_index == 1:
                            selected_index = 0

                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and (column_index != 1):
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                        
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                    
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
                
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['mode_select'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()    
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
                
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
                
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
                
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def singleplayer_game(self, character, chapter=0):
        self.sound_manager.stop_music()
        self.cutscene_mode = False
        self.camera = Camera() # SETTING CAMERA FOR MOVING AROUND MAP

        cursor_flag = True
        if hasattr(self, "level"):
            del self.level
        self.level = Level(self, character, chapter=chapter)

        while True:
            self.display.blit(pygame.transform.scale(self.assets['background'], DISPLAY_SIZE), (0, 0))

            self.camera.update_by_target(self.level.players.get_player())
            
            self.level.render(self.display, self.camera)
            self.level.update()
            self.particle_manager.update()

            if self.cutscene_mode:
                self.cutscene_manager.update()

            self.level.enemies.update(self.level.tilemap, self.camera, SCREEN_SIZE[0] / DISPLAY_SIZE[0], self.level.players.get_player())
            self.level.enemies.render(self.display, self.camera)

            self.level.players.update(self.level.tilemap, self.camera, SCREEN_SIZE[0] / DISPLAY_SIZE[0], self.level.enemies)
            self.level.players.render(self.display, self.camera)

            if cursor_flag:
                self.level.players.get_player().controller.render_mouse(self.display)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEMOTION:
                    cursor_flag = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.sound_manager.pause_music()
                        self.sound_manager.pause_all_sfx()
                        self.level.clear_players_clicks()
                        self.level.players.get_player().controller.unset_mouse_image()
                        self.pause_menu()
                        self.level.players.get_player().controller.set_mouse_image(self.assets['cursor']) 
                        self.sound_manager.unpause_music()
                        self.sound_manager.unpause_all_sfx()
                self.level.players.get_player().controller.update(event=event, game=self)

            self.particle_manager.render(self.display, self.camera)
            self.blinder_effect()
            self.screen.blit(pygame.transform.scale(self.display, SCREEN_SIZE), (0, 0))
            self.level.players.render_HUD(self.screen)
            if self.cutscene_mode:
                self.cutscene_manager.render()
            pygame.display.update()
            self.clock.tick(FPS)

    def choose_replier(self):
        dynamic_chance = random.random() < 0.25
        self.reply_from = random.choice(['boss', 'player'])
        valid_replies = [reply for reply, shown in self.responses[self.reply_from][str(self.level.phase_number)].items() if not shown]
        if not valid_replies or dynamic_chance:
            self.can_show_reply = False
            threading.Thread(target=fetch_completion, args=(self.reply_from, self), daemon=True).start()
            return
        self.response = random.choice(valid_replies)
        self.reply_frames = self.max_reply_frames
        self.responses[self.reply_from][str(self.level.phase_number)][self.response] = True
        self.replier_chosen = True

    def boss_level(self, character, player_manager):
        if hasattr(self, "level"):
            del self.level
        self.sound_manager.stop_music()
        self.sound_manager.stop_all_sfx()
        self.cutscene_mode = False

        self.dialogue_manager.clear_script()
        self.cutscene_manager.reset()
        if hasattr(self, "cutscene_manager"):
            del self.cutscene_manager
        self.cutscene_manager = CutSceneManager(self)
        self.camera = Camera()

        self.level = BossPhase(self, character, 1, player_manager=player_manager)
        self.level.start_pre_phase()
        self.target_entity = self.level.players.get_player()

        self.reply_from = ""
        self.delay_between_replies = random.randrange(420, 601, 60)
        self.max_reply_frames = 300
        self.reply_frames = 0
        self.can_show_reply = True
        self.replier_chosen = False

        self.responses = {'boss': dict(),
                          'player': dict()}
        
        with open('src/scripts/boss.json', 'r') as f:
            replies = json.load(f)
            self.responses['boss']["1"] = dict()
            self.responses['boss']["2"] = dict()
            self.responses['boss']["3"] = dict()
            self.responses['boss']["4"] = dict()
            if replies.get("1", None):
                for reply in replies["1"]:
                    self.responses['boss']["1"][reply] = False
            if replies.get("2", None):
                for reply in replies["2"]:
                    self.responses['boss']["2"][reply] = False
            if replies.get("3", None):
                for reply in replies["3"]:
                    self.responses['boss']["3"][reply] = False
            if replies.get("4", None):
                for reply in replies["4"]:
                    self.responses['boss']["4"][reply] = False

        with open('src/scripts/player.json', 'r') as f:
            replies = json.load(f)
            self.responses['player']["1"] = dict()
            self.responses['player']["2"] = dict()
            self.responses['player']["3"] = dict()
            self.responses['player']["4"] = dict()
            if  replies.get("1", None):
                for reply in replies["1"]:
                    self.responses['player']["1"][reply] = False
            if replies.get("2", None):
                for reply in replies["2"]:
                    self.responses['player']["2"][reply] = False
            if replies.get("3", None):
                for reply in replies["3"]:
                    self.responses['player']["3"][reply] = False
            if replies.get("4", None):
                for reply in replies["4"]:
                    self.responses['player']["4"][reply] = False
        running = True
        while running:
            if self.level.pending_action == 'finish':
                self.credits()

            if self.can_show_reply and self.level.sub_phase_number > 1 and not self.cutscene_mode:
                self.delay_between_replies = max(0, self.delay_between_replies - 1)
                if self.delay_between_replies == 0:
                    if not self.replier_chosen:
                        self.choose_replier()
                    else:
                        self.reply_frames = max(0, self.reply_frames - 1)
                        if self.reply_frames == 0:
                            self.replier_chosen = False
                            self.delay_between_replies = random.randrange(420, 601, 60)
    
            self.display.blit(pygame.transform.scale(self.assets['background'], DISPLAY_SIZE), (0, 0))
            
            self.camera.update_by_target(self.target_entity)
            self.level.render(self.display, self.camera)

            self.level.players.update(self.level.tilemap, self.camera, SCREEN_SIZE[0] / DISPLAY_SIZE[0], self.level.enemies)
            if self.cutscene_mode:
                self.cutscene_manager.update()
            self.level.update()
            self.particle_manager.update()

            self.level.enemies.update(self.level.tilemap, self.camera, SCREEN_SIZE[0] / DISPLAY_SIZE[0], self.level.players.get_player())
            self.level.enemies.render(self.display, self.camera)

            self.level.players.render(self.display, self.camera)


            self.level.players.get_player().controller.render_mouse(self.display)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.sound_manager.pause_music()
                        self.sound_manager.pause_all_sfx()
                        self.level.clear_players_clicks()
                        self.level.players.get_player().controller.unset_mouse_image()
                        self.pause_menu()
                        self.level.players.get_player().controller.set_mouse_image(self.assets['cursor']) 
                        self.sound_manager.unpause_music()
                        self.sound_manager.unpause_all_sfx()
                if self.cutscene_mode:
                    self.cutscene_manager.handle_event(event, self.level.players.get_player())
                else:
                    self.level.players.get_player().controller.update(event=event, game=self)

            self.particle_manager.render(self.display, self.camera)
            self.blinder_effect()
            self.the_black_circle()
            self.screen.blit(pygame.transform.scale(self.display, SCREEN_SIZE), (0, 0))

            # RENDER HUDs
            if not self.cutscene_mode:
                self.level.players.render_HUD(self.screen)
                if self.level.BOSS.in_action:
                    self.level.BOSS.render_HUD(self.screen)
            else:
                self.cutscene_manager.render(self.screen, self.camera)

            pygame.display.update()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def blinder_effect(self):
        if self.level.players.get_player().blindness_frame_count > 0:
            player = self.level.players.get_player()
            self.level.players.get_player().blindness_frame_count -= 1
            mask = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
            mask.fill((255, 255, 255, player.blindness_frame_count if player.blindness_frame_count <= 255 else 255))
            self.display.blit(mask, (0, 0))

    def the_black_circle(self):
        if (self.level.black_circle_screen_frame > 0 or self.level.black_circle_fade_out):
            if self.level.black_circle_screen_frame > 0 and not self.cutscene_mode and not self.level.black_circle_closing_in and not self.level.sub_phase_number == 1 and not self.level.sub_phase_number == 3:
                self.level.black_circle_screen_frame -= 1
                if self.level.black_circle_screen_frame == 0:
                    self.level.black_circle_fade_out = True

            mask = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
            mask.fill((0, 0, 0, 255))

            finished_entities = []

            for entity in self.level.black_circle_entities:
                screen_x = entity.rect().centerx - self.camera.scroll.x
                screen_y = entity.rect().centery - self.camera.scroll.y

                radius = self.level.black_circle_radius_fade.get(entity, 0)
                if self.level.black_circle_screen_frame == 0 and self.level.black_circle_fade_out:
                    radius += self.level.black_circle_fade_speed
                    self.level.black_circle_radius_fade[entity] = radius

                if entity.show_black_circle:
                    draw_blurred_visibility_circle(mask, (int(screen_x), int(screen_y)), radius)

                if radius > max(DISPLAY_SIZE):
                    finished_entities.append(entity)

            if len(finished_entities) == len(self.level.black_circle_entities):
                self.level.black_circle_entities.clear()
                self.level.black_circle_radius_fade.clear()
                self.level.black_circle_fade_out = False

            self.display.blit(mask, (0, 0))

    def multiplayer_game(self, character1, character2):
        self.cutscene_mode = False
        
        self.sound_manager.stop_music()
        self.sound_manager.stop_all_sfx()

        self.level = Multiplyer(self,self.arena_ID)
        self.level.initialize_players(character1, character2)

        self.camera = CameraBox(self.level.players)

        while True:
            self.display.blit(pygame.transform.scale(self.assets['background'], DISPLAY_SIZE), (0, 0))

            self.camera.update()

            self.level.render(self.display, self.camera)
            self.level.update()
            self.particle_manager.update()

            self.level.players.update(self.level.tilemap, self.camera, SCREEN_SIZE[0] / DISPLAY_SIZE[0], self.level.enemies)
            self.level.players.render(self.display, self.camera)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.sound_manager.pause_music()
                        self.sound_manager.pause_all_sfx()
                        self.level.clear_players_clicks()
                        self.pause_menu_local()
                        self.sound_manager.unpause_music()
                        self.sound_manager.unpause_all_sfx()

                for player in self.level.players.get_players():
                    player.controller.update(event=event)

            self.particle_manager.render(self.display, self.camera)
            self.screen.blit(pygame.transform.scale(self.display, SCREEN_SIZE), (0, 0))
            self.level.players.render_HUD(self.screen)
            self.level.render_HUD(self.screen)
            pygame.display.update()
            self.clock.tick(FPS)

    def fade_out(self, surface, speed=5):
        fade = pygame.Surface(SCREEN_SIZE)
        fade.fill((0, 0, 0))
        for alpha in range(0, 255, speed):
            fade.set_alpha(alpha)
            surface.blit(fade, (0, 0))
            pygame.display.update()
            pygame.time.delay(1)

    def pause_menu(self):
        characters = ['redhood','beanhead','crow','the_man_with_hat']
        file = open('following_chapter.bin', 'r')
        chapter = int(file.read())
        file.close()

        pygame.mixer.music.pause()

        last_screen = pygame.transform.scale(self.display, SCREEN_SIZE)
        fade = pygame.Surface(SCREEN_SIZE)
        fade.fill((0,0,0))
        fade.set_alpha(50)
        last_screen.blit(fade, (0,0))

        running = [True]

        buttons = [
            [
                Button('resume', self, (95,395), (310,110), self.back, running, self.sounds['Cursor_3']),
                Button('restart', self, (595,395), (310,110), self.singleplayer_game, (characters[self.character_index], chapter), self.sounds['Cursor_3']),
            ],
            [
                Button('main', self, (295,595), (410,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        if chapter >= 4:
            buttons[0][1] = Button('restart', self, (595,395), (310,110), self.boss_level, (characters[self.character_index], None), sound_active=self.sounds['Cursor_3'])
        selected_index = 0
        column_index = 0
        
        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')
                    
                    #Quit
                    if event.key == pygame.K_ESCAPE:
                        running[0] = False

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(last_screen,(0,0))
            self.screen.blit(self.assets['pause_menu'], (0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
                        if button.name == 'restart' and chapter >= 4:
                            return
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

        pygame.mixer.unpause()
    
    def pause_menu_local(self):
        pygame.mixer.music.pause()

        last_screen = pygame.transform.scale(self.display, SCREEN_SIZE)
        fade = pygame.Surface(SCREEN_SIZE)
        fade.fill((0,0,0))
        fade.set_alpha(50)
        last_screen.blit(fade, (0,0))

        running = [True]

        buttons = [
            [
                Button('resume', self, (95,395), (310,110), self.back, running, self.sounds['Cursor_3']),
                Button('rematch', self, (595,395), (310,110), self.local_play, sound_active=self.sounds['Cursor_3']),
            ],
            [
                Button('main', self, (295,595), (410,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0
        
        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')
                    
                    #Quit
                    if event.key == pygame.K_ESCAPE:
                        running[0] = False

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(last_screen,(0,0))
            self.screen.blit(self.assets['pause_menu'], (0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

        pygame.mixer.unpause()

    def level_over(self, chapter):
        pygame.mixer.music.pause()

        self.fade_out(self.screen)
        characters = ['redhood','beanhead','crow','the_man_with_hat']
        running = [True]

        self.chapter = chapter

        def next_chapter():
            running[0] = False

            #Save
            self.chapter = self.chapter + 1
            file = open('following_chapter.bin', 'w')
            file.write(str(self.chapter))
            file.close()

        
        buttons = [
            [
                Button('next', self, (95,395), (310,110), next_chapter, sound_active=self.sounds['Cursor_3']),
                Button('restart', self, (595,395), (310,110), self.singleplayer_game, (characters[self.character_index], chapter), self.sounds['Cursor_3'])
            ],
            [
                Button('main', self, (295,595), (410,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while running[0]:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['level_completed'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

        pygame.mixer.unpause()        
        return self.chapter

    def game_over(self, character):
        self.fade_out(self.screen)
        self.sound_manager.stop_music()
        self.sound_manager.play_music(self.music['gameover'], loop=True, volume=0.2)
        
        buttons=[
            [
                Button('back2', self, (595,395), (310,110), self.singleplayer_menu, sound_active=self.sounds['Cursor_3']),
            ],
            [
                Button('main', self, (295,595), (410,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]

        if self.level.identifier == 'boss':
            buttons[0].insert(0, Button('restart', self, (95,395), (310,110), self.boss_level, (character, None), self.sounds['Cursor_3']))

        elif self.level.identifier == 'simple_level':
            buttons[0].insert(0, Button('restart', self, (95,395), (310,110), self.singleplayer_game, (character, self.level.chapter), self.sounds['Cursor_3']))

        selected_index = 0
        column_index = 0

        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['game_over'],(0,0))

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')
    
    def match_over(self,winner:int):
        self.sound_manager.stop_music()
        self.sound_manager.play_sfx('Winner')
        buttons = [
            [
                Button('rematch', self, (95,395), (310,110), self.local_play, sound_active=self.sounds['Cursor_3']),
                Button('quit', self, (595,395), (310,110), self.quit, sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('main', self, (295,595), (410,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0

        while True:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['match_over'],(0,0))

            draw_text_with_outline(self.screen, f'Player {winner} is the winner!', load_font('Pixel Game.otf',30), 510, 350, (109,93,57), (0,0,0), 1)

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')

    def credits(self):
        self.fade_out(self.screen)

        running = [True]

        one_button = Button('_', self, (395,595), (210,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
        one_button.set_status('hovered')

        while running[0]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        one_button.set_status('pressed')
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if one_button.rect.collidepoint(event.pos) and event.button == 1:
                        one_button.set_status('pressed')
            
            if one_button.status != 'pressed':
                one_button.set_status('hovered')
            
            self.screen.blit(self.assets['credits'], (0,0))

            one_button.render(self.screen)

            render_mouse_cursor(self.screen, self.assets['normal_cursor'])

            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)

            pygame.display.update()
            self.clock.tick(FPS)

            if one_button.status == 'pressed':
                one_button.execute()

    def client_creation(self, player_name: str, player_hashtag: str, login: bool = True):
        self.client = GameClient(player_name, player_hashtag)
        self.client.account(login=login)

        while self.client.id is None:
            if self.client.error_type:
                if self.client.error_type == 'player_already_online':
                    raise ConnectionRefusedError(f"[CLIENT] Error: {self.client.error_message}")
                self.client.error_type = None
                raise ValueError(f"[CLIENT] Error: {self.client.error_message}")
            pygame.time.wait(50)

    def join_network_lobby(self, cancel_button_available=True):
        all_operators_received = False
        received_operators = {}
        opponent_ready = False
        
        def on_state(message):
            nonlocal opponent_ready, all_operators_received, received_operators
            msg_type = message.get("type")
            
            if msg_type == "opp_ready":
                for player_number, ops in message.get("operators").items():
                    if ops["id"] == self.client.id:
                        self.client.player_number = int(player_number)
                    else:
                        opponent_ready = True
            
            elif msg_type == "operator_sync":
                received_operators = message.get("operators", {})
                self.arena_ID = message.get("AID")
                self.client.send_operator_confirm()
                
            elif msg_type == "all_operators_confirmed":
                all_operators_received = True

        self.client.state_callback = on_state

        initial_snapshot = {
            "id": self.client.id,
            "hashtag": self.client.hashtag,
            "player_operator": self.client.player_operator,
            "name": self.client.name,
            "input": {
                "LMove": False,
                "RMove": False,
                "Jump": False,
                "SHOOT": False,
                "RELOAD": False,
                "CHANGE_GUN": False,
            },
            "x": 0,
            "y": 0,
            "action": "idle",
            "flip": False,
            "hp": 150,
            "mp": 60,
            "after_death_time": 180,
            "mouse": {
                "x": 0,
                "y": 0
            },
            "player_number": 0
        }
        self.client.send_snapshot(initial_snapshot)

        frame_index = 0
        frame_counter = 0
        animation_speed = 24
        
        def cancel_matchmaking():
            cancel_confirmed = False
            self.client.mode = None
            
            frame_index = 0
            frame_counter = 0
            
            while not cancel_confirmed and self.client.running:
                self.client.send_match_request_cancel()
                
                if self.client.mode is None and not self.client.in_queue:
                    cancel_confirmed = True
                    break
                frame_counter += 1
                if frame_counter >= animation_speed:
                    frame_index = (frame_index + 1) % len(self.assets['canceling_match_request'])
                    frame_counter = 0
                self.screen.blit(self.assets['canceling_match_request'][frame_index], (0, 0))
                self.client_show()
                render_mouse_cursor(self.screen, self.assets['normal_cursor'])
                self.screen.blit(scanlines, (0, 0))
                draw_noise(self.screen)
                pygame.display.update()
                self.clock.tick(FPS)
                    
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                
                time.sleep(0.001)
            
            self.online_play()

        back_button = Button('back1', self, (395, 695), (210, 110), cancel_matchmaking if cancel_button_available else None, sound_active=self.sounds['Cursor_3'])

        while not opponent_ready:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                    
                if event.type == pygame.MOUSEMOTION:
                    if back_button.rect.collidepoint(event.pos):
                        back_button.set_status('hovered')
                    else:
                        back_button.set_status('idle')
                        
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_button.rect.collidepoint(event.pos):
                        back_button.set_status('pressed')
            
            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['in_queue'])
                frame_counter = 0
                
            self.screen.blit(self.assets['in_queue'][frame_index], (0, 0))
            back_button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
            
            if back_button.status == 'pressed':
                back_button.execute()
        
        confirmation_sent_time = time.perf_counter()
        frame_index = 0
        frame_counter = 0
        
        while not all_operators_received:
            if received_operators and time.perf_counter() - confirmation_sent_time > 0.05:
                self.client.send_operator_confirm()
                confirmation_sent_time = time.perf_counter()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            
            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['synchronizing'])
                frame_counter = 0
            
            self.screen.blit(self.assets['synchronizing'][frame_index], (0, 0))
            
            expected_players = 2
            if self.client.mode == 'OVV3':
                expected_players = 3
            elif self.client.mode in ['OVV4', 'TVV2']:
                expected_players = 4
                
            progress_text = f"Synchronizing: {len(received_operators)}/{expected_players}"
            draw_text_with_outline(self.screen, progress_text, 
                                load_font('Pixel Game.otf', 36), 
                                500, 650, (255, 255, 255), (0, 0, 0), 2, True)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
        
        start_time = time.time()
        frame_index = 0
        frame_counter = 0
        
        while time.time() - start_time < 1.5:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                    
            frame_counter += 1
            if frame_counter >= animation_speed:
                frame_index = (frame_index + 1) % len(self.assets['match_starting'])
                frame_counter = 0
                
            self.screen.blit(self.assets['match_starting'][frame_index], (0, 0))
            
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines, (0, 0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)
        
        self.player_operators = received_operators
        self.networked_game()

    def networked_game(self):
        if self.client.mode == 'OVV2' or self.client.mode == 'SPFM':
            self.level = NMOVV2Client(self, Arena_ID=self.arena_ID, client=self.client, PINFS=self.player_operators)
        if self.client.mode == 'OVV3':
            self.level = NMOVV3Client(self, Arena_ID=self.arena_ID, client=self.client, PINFS=self.player_operators)
        if self.client.mode == 'OVV4':
            self.level = NMOVV4Client(self, Arena_ID=self.arena_ID, client=self.client, PINFS=self.player_operators)
        elif self.client.mode == 'TVV2':
            self.level = NMTVV2Client(self, Arena_ID=self.arena_ID, client=self.client, PINFS=self.player_operators)
        
        self.camera = CameraBox(self.level.players)

        self.forced_exit = False
        self.match_end = False
        running = True
        self.exit_message = None
        self.show_winner_page = False
        self.winner_number = None

        def on_state_update(snapshots: dict):
            msg_type = snapshots.get("type")
            if msg_type == 'forced_exit':
                self.forced_exit = True
                self.exit_message = snapshots.get("message")
                return
            elif msg_type == 'match_over':
                self.match_end = True
                self.exit_message = snapshots.get("message")
                return
            for snapshot in snapshots['players']:
                player = self.level.players.get_player(snapshot["player_number"])
                player.apply_ABL_snapshot(snapshot.get("ABL", {}))
                player.apply_arsenal_snapshot(snapshot)
                if snapshot["id"] == self.client.id:
                    if player:
                        player.HP.apply_snapshot(snapshot.get("HP"))
                        player.MP.apply_snapshot(snapshot.get("MP"))
                        player.after_death_time = snapshot.get("after_death_time", player.after_death_time)
                        if self.level.delaying_reset:
                                player.position.x = snapshot.get("x", player.position.x)
                                player.position.y = snapshot.get("y", player.position.y)
                        if snapshot.get("action") == 'death':
                            player.animation_manager.set_action(snapshot.get("action", player.animation_manager.action))
                        self.level.last_confirmed_pos = pygame.Vector2(snapshot.get("x", 0), snapshot.get("y", 0))
                    continue
                if player:
                    player.controller.apply_snapshot(snapshot)

            if hasattr(self.level, 'apply_server_snapshot'):
                self.level.apply_server_snapshot(snapshots.get('game_stats', {}))

        self.client.state_callback = on_state_update
        self.previous_time = None

        try:
            while running:
                if self.forced_exit:
                    running = False
                    raise Exception(self.exit_message)
                elif self.match_end:
                    running = False
                    self.show_winner_page = True
                    self.winner_number = self.exit_message
                    continue

                self.display.blit(pygame.transform.scale(self.assets['background'], DISPLAY_SIZE), (0, 0))
                self.camera.update()
                self.level.render(self.display, self.camera)
                self.level.update()
                self.level.send_this_player_snapshot()
                self.particle_manager.update()

                self.level.players.update(self.level.tilemap, self.camera, SCREEN_SIZE[0] / DISPLAY_SIZE[0], self.level.enemies)
                self.level.players.render(self.display, self.camera)


                time_diff = self.level.now - self.level.last_confirmed_server_time
                self.previous_time = time_diff if self.previous_time is None else self.previous_time 
                if time_diff - self.previous_time > 1:
                    print(f"[RECONCILE] Snap back: time_diff = {time_diff - self.previous_time}")
                    self.level.this_player().position = Position(self.level.last_confirmed_pos.x, 
                                                                self.level.last_confirmed_pos.y)
                    self.previous_time = time_diff
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    self.level.this_player().controller.update(event=event, game=self)

                self.particle_manager.render(self.display, self.camera)
                if self.level.this_player().animation_manager.action != 'death':
                    self.level.this_player().controller.render_mouse(self.display)
                self.screen.blit(pygame.transform.scale(self.display, SCREEN_SIZE), (0, 0))
                self.level.players.render_HUD(self.screen)
                self.level.render_HUD(self.screen)
                pygame.display.update()
                self.clock.tick(FPS)
        except Exception as e:
            print(f"[DISCONNECT] Returning to lobby: {e}")
            self.client.exit_match()
            self.winner_page_choice(0)

        if self.show_winner_page:
            self.client.exit_match()
            self.winner_page_choice(self.winner_number)

    def winner_page_choice(self, winner_number):
        self.sound_manager.stop_music()
        if winner_number != 0:
            self.sound_manager.play_sfx('Winner')
        
        buttons = [
            [
                Button('rematch', self, (95,395), (310,110), self.online_play, sound_active=self.sounds['Cursor_3']),
                Button('quit', self, (595,395), (310,110), self.quit, sound_active=self.sounds['Cursor_3'])
            ],
            [
                Button('main', self, (295,595), (410,110), self.main_menu, sound_active=self.sounds['Cursor_3'])
            ]
        ]
        selected_index = 0
        column_index = 0
        choice = None

        while choice is None:
            #Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                if event.type == pygame.KEYDOWN:
                    #Movement
                    if (event.key == pygame.K_UP) or (event.key == pygame.K_DOWN):
                        self.sound_manager.play_sfx('Hover')
                        column_index = (column_index + 1) % 2
                        selected_index = 0
                    
                    if ((event.key == pygame.K_RIGHT) or (event.key == pygame.K_LEFT)) and column_index == 0:
                        self.sound_manager.play_sfx('Hover')
                        selected_index = (selected_index + 1) % 2
                    
                    #Activating
                    if event.key == pygame.K_RETURN:
                        buttons[column_index][selected_index].set_status('pressed')

                #Mouse Movement
                if event.type == pygame.MOUSEMOTION:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('hovered')
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_index ,column in enumerate(buttons):
                        for s_index ,button in enumerate(column):
                            if button.rect.collidepoint(event.pos):
                                column_index = c_index
                                selected_index = s_index
                                button.set_status('pressed')
            
            #Conditions
            if buttons[column_index][selected_index].status != 'pressed':
                buttons[column_index][selected_index].set_status('hovered')
            
            #Rendering
            self.screen.blit(self.assets['match_over'],(0,0))

            if winner_number != 0:
                draw_text_with_outline(self.screen, f'Team {winner_number} is the winner!', load_font('Pixel Game.otf',30), 510, 350, (109,93,57), (0,0,0), 1)
            elif winner_number == 0:
                draw_text_with_outline(self.screen, f'A Player Disconnected', load_font('Pixel Game.otf',30), 510, 350, (109,93,57), (0,0,0), 1)

            for column in buttons:
                for button in column:
                    button.render(self.screen)
            self.client_show()
            render_mouse_cursor(self.screen, self.assets['normal_cursor'])
            
            self.screen.blit(scanlines,(0,0))
            draw_noise(self.screen)
            
            pygame.display.update()
            self.clock.tick(FPS)

            for column in buttons:
                for button in column:
                    if button.status == 'pressed':
                        choice = button.execute()
            
            #Reseting
            for column in buttons:
                for button in column:
                    button.set_status('idle')