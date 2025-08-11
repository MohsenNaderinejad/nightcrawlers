import pygame, sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.tilemap import *
from config import *
from src.engine.cameras import *

# ---------------------- EDITOR ---------------------
# --------- INITIALIZE ---------
pygame.init()

RENDER_SCALE = 1600/880

map = 'levels/3.json'

class LevelEditor:

    def __init__(self):
        pygame.display.set_caption("editor") # CAPTION
        self.screen_size = SCREEN_SIZE # SCREEN SIZE
        self.display_size = DISPLAY_SIZE # DISPLAY SIZE
        self.screen = pygame.display.set_mode(self.screen_size) # SCREEN SIZE
        self.display = pygame.Surface(self.display_size) # DISPLAY SIZE ( SHOWN ON SCREEN FOR BETTER VIEW )
        self.clock = pygame.time.Clock() # FOR SETTING FPS
        self.controller = Controller() # CONTROLLER
        self.mouse = Mouse() # MOUSE

        # INITIAL ASSETS FOR EDITOR
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
            'hero': load_images('tiles/spawners/Heros', player_loader=True),
            'enemies': load_images('tiles/spawners/Enemies', player_loader=True, scale_size=0.9),
            'item':load_images('Items', player_loader=True),
            'save':load_images('save')
        }

        self.tilemap = TileMap(self, tile_size=32, editor_mode=True) # MAKING THE GRID FOR TILEMAP
        self.tile_list = list(self.assets) # GETTING KEY NAMES FOR TILEMAP
        self.camera = Camera() # SETTING CAMERA FOR MOVING AROUND MAP

        self.tile_group = 0 # GROUP IMAGES -> e.g. 'decor', 'grass', 'stone', 'large_decor'
        self.tile_variant = 0 # VARIANT OF THE IMAGE -> e.g. 0, 1, 2, 3, 4

        self.ongrid = True # FOR HAVING COLLISION OR NOT

    def run(self):

        # FIRST LOADING A MAP
        self.tilemap.load(BASE_MAP_PATH + map)

        while True:
            self.display = pygame.Surface(self.display_size) # DISPLAY SIZE ( SHOWN ON SCREEN FOR BETTER VIEW )
            RENDER_SCALE = self.screen_size[0] / self.display_size[0] # RENDER SCALE FOR SCALING THE DISPLAY SIZE TO SCREEN SIZE
            self.display.fill((0, 0, 0)) # FILLING THE DISPLAY WITH BLACK

            self.camera.update_by_controller(self.controller) # UPDATING THE CAMERA BY CONTROLLER MOVEMENT
            current_tile = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy() # MAKING A COPY OF THE CURRENT TILE
            current_tile.set_alpha(127) # MAKING THE TILE TRANSPARENT

            self.tilemap.render(self.display, camera=self.camera) # RENDERING THE TILEMAP BASED ON CAMERA POSITION

            mpos = (self.mouse.mouse_pos.x / RENDER_SCALE, self.mouse.mouse_pos.y / RENDER_SCALE) # SETTING TEMP MOUSE POSITION DIVIDING BY RENDER SCALE
            # GETTING THE TILE POSITION BASED ON MOUSE POSITION
            tile_pos = ((mpos[0] + self.camera.render_scroll.x) // self.tilemap.tile_size, (mpos[1] + self.camera.render_scroll.y) // self.tilemap.tile_size)
            tile_pos = Position(tile_pos[0], tile_pos[1])

            # DISPLAYIGN TILES BASED ON 'ONGRID' OR 'OFFGRID'
            # 'OFFGRID' -> BACKGROUND IMAGES THAT DOES NOT HAVE COLLISIONS ON
            if self.ongrid:
                self.display.blit(current_tile, (tile_pos.x * self.tilemap.tile_size - self.camera.render_scroll.x, tile_pos.y * self.tilemap.tile_size - self.camera.render_scroll.y))
            else:
                self.display.blit(current_tile, mpos)

            # ADDING ONGRID AND OFFGRID TILES TO MAP
            if self.mouse.mouse_movements['L_CLICK'] and self.ongrid:
                self.tilemap.tilemap[tile_pos] = Tile(self.tile_list[self.tile_group], position=tile_pos, variant=self.tile_variant)
            # REMOVING ONGRID AND OFFGRID TILES TO MAP
            if self.mouse.mouse_movements['R_CLICK']:
                if tile_pos in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_pos]
                for tile in self.tilemap.offgrid_tiles:
                    tile_image = self.assets[tile.tile_type][tile.variant]
                    tile_rect = pygame.Rect(tile.position.x - self.camera.render_scroll.x, tile.position.y - self.camera.render_scroll.y, tile_image.get_width(), tile_image.get_height())
                    self.display.blit(tile_image, tile_rect)
                    if tile_rect.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
                        break

            # DISPLAYING CURRENT_TILES BEFORE PUTTING THEM ON MAP
            self.display.blit(current_tile, (5,5))

            # GETTING EVENTS
            for event in pygame.event.get():

                self.controller.update_for_editor(event)
                self.mouse.update(event, game=self)
                
                # QUTING THE EDITOR
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    # FOR TURNGIN OFF AND ON FOR 'ongrid' BOOL
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    # FOR SAVING MAP
                    if event.key == pygame.K_x:
                        self.tilemap.save(BASE_MAP_PATH + map)

                if self.mouse.mouse_movements['L_CLICK']:
                    if not self.ongrid:
                        tile_pos = Position((mpos[0] + self.camera.render_scroll.x), (mpos[1] + self.camera.render_scroll.y))
                        self.tilemap.add_offgrid_tile(self.tile_list[self.tile_group], tile_pos, variant=self.tile_variant)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.controller.movement['SHIFT']:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0


            self.screen.blit(pygame.transform.scale(self.display, self.screen_size), (0, 0))
            pygame.display.update()
            self.clock.tick(FPS)


LevelEditor().run()
