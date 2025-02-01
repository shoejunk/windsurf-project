import pygame
import math
from typing import List, Optional
from engine.core import Component, Entity

class Projectile(Entity):
    def __init__(self, x: float, y: float, velocity_x: float, velocity_y: float, 
                 damage: float = 10.0, lifetime: float = 2.0):
        super().__init__(x, y)
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.damage = damage
        self.lifetime = lifetime
        self.radius = 3
        
    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        self.lifetime -= delta_time
        
    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, (255, 255, 0), 
                         (int(self.x), int(self.y)), self.radius)
        # Add a glowing effect
        pygame.draw.circle(screen, (255, 200, 0), 
                         (int(self.x), int(self.y)), self.radius + 1, 1)

class WeaponComponent(Component):
    def __init__(self):
        super().__init__()
        self.projectiles: List[Projectile] = []
        self.fire_rate = 0.35  # Increased delay between shots (was 0.15)
        self.fire_timer = 0.0
        self.projectile_speed = 400.0
        self.can_fire = True
        
    def update(self, delta_time: float) -> None:
        # Update fire rate timer
        if not self.can_fire:
            self.fire_timer += delta_time
            if self.fire_timer >= self.fire_rate:
                self.can_fire = True
                self.fire_timer = 0.0
        
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update(delta_time)
            if projectile.lifetime <= 0:
                self.projectiles.remove(projectile)
    
    def fire(self, direction: float = 0.0) -> None:
        if not self.can_fire or not self.entity:
            return
            
        # Calculate projectile velocity based on direction
        angle_rad = math.radians(direction)
        velocity_x = self.projectile_speed * math.cos(angle_rad)
        velocity_y = self.projectile_speed * math.sin(angle_rad)
        
        # Calculate spawn position based on angle
        # Increase offset when firing at angles to avoid spawning inside helicopter
        base_offset = 25
        angle_factor = abs(math.sin(angle_rad))  # Increases offset when firing at angles
        spawn_offset = base_offset * (1 + angle_factor * 0.5)
        
        spawn_x = self.entity.x + spawn_offset * math.cos(angle_rad)
        spawn_y = self.entity.y + spawn_offset * math.sin(angle_rad)
        
        projectile = Projectile(spawn_x, spawn_y, velocity_x, velocity_y)
        self.projectiles.append(projectile)
        
        # Reset fire timer
        self.can_fire = False
        self.fire_timer = 0.0
    
    def render(self, screen: pygame.Surface) -> None:
        for projectile in self.projectiles:
            projectile.render(screen)
