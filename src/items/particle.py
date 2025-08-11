import sys, pathlib, pygame

from numpy import angle
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import Position

class Particle:
    def __init__(self, game, p_type, pos: Position, velocity: Position = Position(), frame=0, angle=0, mid_bottom=False, left_bottom=False, right_bottom=False, offset=Position()):
        self.game = game
        self.type = p_type
        self.pos = pos
        self.velocity = velocity
        self.angle = angle
        self.animation = self.game.effects[p_type].copy()
        self.animation.frame = frame
        self.mid_bottom = mid_bottom
        self.left_bottom = left_bottom
        self.right_bottom = right_bottom
        self.offset = offset
    
    def update(self):
        kill = False
        if self.animation.done:
            kill = True
        
        self.pos += self.velocity
        
        self.animation.update()
        
        return kill
    
    def render(self, surf, camera):
        img = self.animation.image()
        rotated = pygame.transform.rotozoom(img, -self.angle, 1)
        render_pos = self.pos + self.offset - camera.render_scroll
        if self.mid_bottom:
            rect = rotated.get_rect(midbottom=render_pos.tuple())
        elif self.left_bottom:
            rect = rotated.get_rect(leftbottom=render_pos.tuple())
        elif self.right_bottom:
            rect = rotated.get_rect(rightbottom=render_pos.tuple())
        else:
            rect = rotated.get_rect(center=render_pos.tuple())
        surf.blit(rotated, rect.topleft)

class ParticleManager:
    def __init__(self, game):
        self.game = game
        self.particles = []

    def clear_particles(self):
        self.particles.clear()

    def add_particle(self, p_type, pos: Position, velocity: Position = Position(), frame=0, angle=0, mid_bottom=False, left_bottom=False, right_bottom=False, offset=Position()):
        particle = Particle(self.game, p_type, pos, velocity, frame, angle, mid_bottom, left_bottom, right_bottom, offset)
        self.particles.append(particle)
    
    def update(self):
        for particle in self.particles[:]:
            if particle.update():
                self.particles.remove(particle)
    
    def render(self, surf, camera):
        for particle in self.particles:
            particle.render(surf, camera)
