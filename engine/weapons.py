import pygame
from typing import List, Tuple
from .core import Component

class Projectile:
    def __init__(self, x: float, y: float, velocity_x: float, velocity_y: float):
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.radius = 3
        self.damage = 10
        self.lifetime = 2.0  # Seconds
        self.time_alive = 0.0
        
    def update(self, delta_time: float) -> bool:
        """Update projectile position and lifetime. Returns False if projectile should be removed."""
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        self.time_alive += delta_time
        return self.time_alive < self.lifetime
        
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                         self.radius * 2, self.radius * 2)
                         
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        # Draw bullet
        pygame.draw.circle(screen, (255, 255, 0), (screen_x, screen_y), self.radius)
        # Draw glow effect
        pygame.draw.circle(screen, (255, 200, 0), (screen_x, screen_y), self.radius + 1, 1)

class WeaponComponent(Component):
    def __init__(self):
        super().__init__()
        self.projectiles: List[Projectile] = []
        self.cooldown = 0.2  # Seconds between shots
        self.time_since_last_shot = self.cooldown  # Start ready to fire
        
    def fire(self, x: float, y: float, velocity_x: float, velocity_y: float) -> None:
        """Fire a projectile if cooldown is ready"""
        if self.time_since_last_shot >= self.cooldown:
            print(f"Firing projectile at ({x}, {y}) with velocity ({velocity_x}, {velocity_y})")  # Debug
            # Offset projectile spawn to be in front of helicopter
            offset = 20 if velocity_x > 0 else -20
            self.projectiles.append(Projectile(x + offset, y, velocity_x, velocity_y))
            self.time_since_last_shot = 0.0
            
    def update(self, delta_time: float) -> None:
        """Update projectiles and handle collisions"""
        self.time_since_last_shot += delta_time
        
        # Update projectiles
        for projectile in self.projectiles[:]:  # Copy list for safe iteration
            if not projectile.update(delta_time):
                print(f"Removing expired projectile at ({projectile.x}, {projectile.y})")  # Debug
                self.projectiles.remove(projectile)
                continue
                
            # Check wall collisions if we have access to the scene
            if self.entity and self.entity.scene:
                projectile_rect = projectile.get_rect()
                for wall in self.entity.scene.world.walls:
                    wall_rect = wall.get_rect()
                    if wall_rect.colliderect(projectile_rect):
                        print(f"Projectile hit wall at ({wall.x}, {wall.y})")  # Debug
                        if wall.destructible:
                            wall.take_damage(10)  # Damage wall
                        self.projectiles.remove(projectile)
                        break
                        
    def render(self, screen: pygame.Surface) -> None:
        """Render all active projectiles"""
        if not self.entity or not self.entity.scene or not hasattr(self.entity.scene, 'camera'):
            return
            
        camera = self.entity.scene.camera
        for projectile in self.projectiles:
            projectile.render(screen, camera.x, camera.y)
