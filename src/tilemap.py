from .utils import *
import pygame
import json

NEIGHBOUR_OFFSET = [
    Position(-1, -1), Position(0, -1), Position(1, -1),
    Position(-1,  0), Position(0,  0), Position(1,  0),
    Position(-1,  1), Position(0,  1), Position(1,  1)
]

class Tile:
    def __init__(self, tile_type, variant=1, position=Position()):
        self.item_spawned = False
        self.tile_type = tile_type
        self.variant = variant
        self.position = position
        self.is_walkable = True
        self.is_visible = True
        self.has_physics = True
        self.spawn_time = None
        if self.tile_type == 'item':
            self.is_visible = False

    def __repr__(self):
        return f"Tile(type={self.tile_type}, variant={self.variant}, position={self.position}, walkable={self.is_walkable}, visible={self.is_visible})"
    
    def copy(self):
        return Tile(self.tile_type, self.variant, self.position.copy())

class TileMap:
    def __init__(self, game, tile_size, editor_mode = False):
        self.tile_size = tile_size
        self.has_physics_tiles = ['stone', 'grass']
        self.game = game
        self.editor_mode = editor_mode

        self.tilemap = {}
        self.offgrid_tiles = []

    def add_tile(self, tile_type, position, variant=1):
        tile = Tile(tile_type, position=position, variant=variant)
        if tile_type == 'item':
            tile.spawn_time = pygame.time.get_ticks()
        if self.editor_mode:
            tile.is_visible = True
        self.tilemap[position] = tile
        return tile
    
    def add_offgrid_tile(self, tile_type, position, variant=1):
        tile = Tile(tile_type, position=position, variant=variant)
        if tile_type == 'item':
            tile.spawn_time = pygame.time.get_ticks()
        if self.editor_mode:
            tile.is_visible = True
        self.offgrid_tiles.append(tile)
        return tile

    def remove_tile(self, position):
        if position in self.tilemap:
            del self.tilemap[position]
            return True
        
        for i, tile in enumerate(self.offgrid_tiles.copy()):
            if tile.position == position:
                del self.offgrid_tiles[i]
                return True

        return False 

    def extract_tile_by_pair(self, pairs, keep = True):
        matches = list()
        for tile in self.offgrid_tiles.copy():
            if (tile.tile_type, tile.variant) in pairs:
                matches.append(tile)
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for tile in self.tilemap.copy().values():
            if (tile.tile_type, tile.variant) in pairs:
                matches.append(tile.copy())
                matches[-1].position = tile.position.copy()
                matches[-1].position *= self.tile_size
                if not keep:
                    del self.tilemap[tile.position]

        return matches

    def tiles_around(self, position, enemy_ai = False):
        if not enemy_ai:
            tiles = []
            tile_pos = Position(position.x // self.tile_size, position.y // self.tile_size)
            for offset in NEIGHBOUR_OFFSET:
                neighbour_pos = Position(tile_pos.x + offset.x, tile_pos.y + offset.y)
                if neighbour_pos in self.tilemap:
                    tiles.append(self.tilemap[neighbour_pos])
            return tiles
        else:
            not_tiles = []
            neighbour_pos_bottom_right = (position + Position(8, 0)) // self.tile_size
            neighbour_pos_bottom_left = (position + Position(-8, 0)) // self.tile_size

            if neighbour_pos_bottom_right in self.tilemap:
                not_tiles.append(1)
            if neighbour_pos_bottom_left in self.tilemap:
                not_tiles.append(-1)

            return not_tiles

    def max_y_axis_tile(self):
        max_y = 0
        for tile_pos in self.tilemap.keys():
            if tile_pos.y > max_y:
                max_y = tile_pos.y

        max_y += 10
        max_y *= self.tile_size
        return max_y

    def save(self, path):
        with open(path, 'w') as file:
            tmp_tile_map = dict()
            tmp_offgrid_tiles = list()
            for tile in self.offgrid_tiles:
                tile_pos_tmp = tile.position.to_key()
                tmp_offgrid_tiles.append({'tile_type': tile.tile_type, 'variant': tile.variant, 'position': tile_pos_tmp})
            for tilek, tilev in self.tilemap.items():
                tile_pos_tmp = tilek.to_key()
                tmp_tile_map[tile_pos_tmp] = {'tile_type': tilev.tile_type, 'variant': tilev.variant, 'position': tile_pos_tmp}
            json.dump({'tilemap': tmp_tile_map, 'offgrid_tiles': tmp_offgrid_tiles, 'tile_size': self.tile_size}, file, indent=4)

    def load(self, path):
        with open(path, 'r') as file:
            data = json.load(file)
            for tilek, tilev in data['tilemap'].items():
                tile_pos_tmp = Position.from_key(tilek)
                self.tilemap[tile_pos_tmp] = Tile(tilev['tile_type'], position=tile_pos_tmp, variant=tilev['variant'])
                if self.tilemap[tile_pos_tmp].tile_type == 'item':
                    self.tilemap[tile_pos_tmp].spawn_time = pygame.time.get_ticks()
                if self.editor_mode:
                    self.tilemap[tile_pos_tmp].is_visible = True
            for tile in data['offgrid_tiles']:
                tile_pos_tmp = Position.from_key(tile['position'])
                self.offgrid_tiles.append(Tile(tile['tile_type'], position=tile_pos_tmp, variant=tile['variant']))
                if self.offgrid_tiles[-1].tile_type == 'item':
                    self.offgrid_tiles[-1].spawn_time = pygame.time.get_ticks()
                if self.editor_mode:
                    self.offgrid_tiles[-1].is_visible = True
            self.tile_size = data['tile_size']

    def physics_tiles_rect(self, position):
        rects = []
        for tile in self.tiles_around(position):
            if tile.tile_type in self.has_physics_tiles:
                rect = pygame.Rect(tile.position.x * self.tile_size, tile.position.y * self.tile_size, self.tile_size, self.tile_size)
                rects.append(rect)
        return rects

    def render(self, screen, camera):
        for tile in self.offgrid_tiles:
            if tile.is_visible:
                tile_pos = (tile.position.x - camera.render_scroll.x, tile.position.y - camera.render_scroll.y)
                screen.blit(self.game.assets[tile.tile_type][tile.variant], tile_pos)

        for x in range(int(camera.render_scroll.x // self.tile_size), int((camera.render_scroll.x + self.game.display_size[0]) // self.tile_size) + 1):
            for y in range(int(camera.render_scroll.y // self.tile_size), int((camera.render_scroll.y + self.game.display_size[1]) // self.tile_size) + 1):
                tile_pos = Position(x, y)
                if tile_pos in self.tilemap:
                    tile = self.tilemap[tile_pos]
                    if tile.is_visible:
                        tile_pos = (tile.position.x * self.tile_size - camera.render_scroll.x, tile.position.y * self.tile_size - camera.render_scroll.y)
                        image = self.game.assets[tile.tile_type][tile.variant]
                        screen.blit(image, tile_pos)
