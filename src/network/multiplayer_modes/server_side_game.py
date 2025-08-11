import pygame, sys, pathlib, os
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from src.engine.cameras import CameraBox
from src.utils import load_image, load_images
pygame.init()
pygame.display.set_mode((1600, 900), flags=pygame.NOFRAME | pygame.HIDDEN)
pygame.display.set_caption("Server Game")

class ServerGame:
    def __init__(self):
        self.assets = {
            'item':load_images('Items', player_loader=True),
        }
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
        self.camera = None
        self.level = None
        self.cutscene_mode = False

    def set_camera(self, player_manager):
        self.camera = CameraBox(player_manager)

    def set_level(self, level):
        self.level = level