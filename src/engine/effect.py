import pygame, sys, pathlib, math, random
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from config import SCREEN_SIZE

scanlines = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
for y in range(0,SCREEN_SIZE[1], 2):
    pygame.draw.line(scanlines, (0,0,0,30), (0,y), (SCREEN_SIZE[0],y))

def draw_vintage(surface : pygame.Surface):
    vintage = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)

    for y in range(SCREEN_SIZE[1]):
        for x in range(SCREEN_SIZE[0]):
            dx = (x - SCREEN_SIZE[0] / 2) / (SCREEN_SIZE[0] / 2)
            dy = (y - SCREEN_SIZE[1] / 2) / (SCREEN_SIZE[1] / 2)
            dist = math.sqrt(dx * dx + dy * dy)
            alpha = min(255, max(0, int((dist - 0.5) * 300)))
            vintage.set_at((x,y), (0,0,0,alpha))

    surface.blit(vintage, (0,0))

def draw_noise(surface : pygame.Surface):
    noise = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    for _ in range(5000):
        x = random.randint(0, SCREEN_SIZE[0] - 1)
        y = random.randint(0, SCREEN_SIZE[1] - 1)
        gray = random.randint(0, 50)
        noise.set_at((x, y), (gray, gray, gray, 20))
    
    surface.blit(noise, (0, 0))