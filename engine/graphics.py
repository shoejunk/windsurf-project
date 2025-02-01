import pygame
from typing import List, Dict, Optional, Tuple, Union
from .core import Component
import math

class SpriteComponent(Component):
    def __init__(self, source: Union[str, pygame.Surface]):
        super().__init__()
        if isinstance(source, str):
            self.sprite = pygame.image.load(source).convert_alpha()
        else:
            self.sprite = source
        self.width = self.sprite.get_width()
        self.height = self.sprite.get_height()
        self.scale = 1.0
        self.rotation = 0.0
        self.flip_x = False
        self.flip_y = False
        
    def set_scale(self, scale: float) -> None:
        self.scale = scale
        scaled_width = int(self.width * scale)
        scaled_height = int(self.height * scale)
        self.sprite = pygame.transform.scale(self.sprite, (scaled_width, scaled_height))
        
    def render(self, screen: pygame.Surface) -> None:
        if not self.entity:
            return
            
        rotated = pygame.transform.rotate(self.sprite, self.rotation)
        if self.flip_x or self.flip_y:
            rotated = pygame.transform.flip(rotated, self.flip_x, self.flip_y)
            
        rect = rotated.get_rect()
        rect.center = (self.entity.x, self.entity.y)
        screen.blit(rotated, rect)

class AnimationComponent(Component):
    def __init__(self):
        super().__init__()
        self.animations: Dict[str, List[pygame.Surface]] = {}
        self.current_animation: Optional[str] = None
        self.frame_index = 0
        self.frame_time = 0
        self.frame_duration = 0.1  # seconds per frame
        self.playing = False
        self.looping = True
        
    def add_animation(self, name: str, spritesheet_path: str, 
                     frame_width: int, frame_height: int, 
                     frame_count: int) -> None:
        spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        frames = []
        
        for i in range(frame_count):
            frame_surface = pygame.Surface((frame_width, frame_height), 
                                        pygame.SRCALPHA)
            frame_surface.blit(spritesheet, 
                             (0, 0), 
                             (i * frame_width, 0, frame_width, frame_height))
            frames.append(frame_surface)
            
        self.animations[name] = frames
        
    def play(self, animation_name: str, loop: bool = True) -> None:
        if animation_name not in self.animations:
            return
            
        if self.current_animation != animation_name:
            self.current_animation = animation_name
            self.frame_index = 0
            self.frame_time = 0
            
        self.playing = True
        self.looping = loop
        
    def stop(self) -> None:
        self.playing = False
        self.frame_index = 0
        self.frame_time = 0
        
    def update(self, delta_time: float) -> None:
        if not self.playing or not self.current_animation:
            return
            
        self.frame_time += delta_time
        if self.frame_time >= self.frame_duration:
            self.frame_time = 0
            self.frame_index += 1
            
            frames = self.animations[self.current_animation]
            if self.frame_index >= len(frames):
                if self.looping:
                    self.frame_index = 0
                else:
                    self.playing = False
                    self.frame_index = len(frames) - 1
                    
    def render(self, screen: pygame.Surface) -> None:
        if not self.entity or not self.current_animation:
            return
            
        frames = self.animations[self.current_animation]
        if 0 <= self.frame_index < len(frames):
            frame = frames[self.frame_index]
            rect = frame.get_rect()
            rect.center = (self.entity.x, self.entity.y)
            screen.blit(frame, rect)

class ParticleSystem(Component):
    class Particle:
        def __init__(self, x: float, y: float, velocity: Tuple[float, float], 
                     lifetime: float, color: Tuple[int, int, int, int], 
                     size: float = 2.0):
            self.x = x
            self.y = y
            self.velocity_x, self.velocity_y = velocity
            self.lifetime = lifetime
            self.max_lifetime = lifetime
            self.color = color
            self.size = size
            
    def __init__(self):
        super().__init__()
        self.particles: List[ParticleSystem.Particle] = []
        
    def emit(self, count: int, velocity_range: Tuple[float, float], 
             lifetime_range: Tuple[float, float], 
             color: Tuple[int, int, int, int], size_range: Tuple[float, float]) -> None:
        if not self.entity:
            return
            
        import random
        for _ in range(count):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(*velocity_range)
            velocity_x = speed * math.cos(angle)
            velocity_y = speed * math.sin(angle)
            lifetime = random.uniform(*lifetime_range)
            size = random.uniform(*size_range)
            
            particle = self.Particle(
                self.entity.x, self.entity.y,
                (velocity_x, velocity_y),
                lifetime, color, size
            )
            self.particles.append(particle)
            
    def update(self, delta_time: float) -> None:
        # Update existing particles
        for particle in self.particles[:]:
            particle.x += particle.velocity_x * delta_time
            particle.y += particle.velocity_y * delta_time
            particle.lifetime -= delta_time
            
            if particle.lifetime <= 0:
                self.particles.remove(particle)
                
    def render(self, screen: pygame.Surface) -> None:
        for particle in self.particles:
            # Create a surface for the particle with alpha channel
            particle_surface = pygame.Surface((particle.size * 2, particle.size * 2), pygame.SRCALPHA)
            
            # Calculate alpha based on remaining lifetime
            alpha = int((particle.lifetime / particle.max_lifetime) * particle.color[3])
            color = (*particle.color[:3], alpha)
            
            # Draw the particle
            pygame.draw.circle(particle_surface, color, 
                             (particle.size, particle.size), 
                             particle.size)
            
            # Blit the particle surface onto the screen
            screen.blit(particle_surface, 
                       (int(particle.x - particle.size),
                        int(particle.y - particle.size)))
