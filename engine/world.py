import pygame
from typing import List, Optional, Tuple
from .core import Entity, Component
from .physics import PhysicsComponent

class Wall(Entity):
    def __init__(self, x: float, y: float, width: float, height: float, 
                 destructible: bool = False, color: Tuple[int, int, int] = (100, 100, 100)):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.destructible = destructible
        self.color = color
        self.health = 100 if destructible else float('inf')
        
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.width/2, self.y - self.height/2, 
                         self.width, self.height)
        
    def take_damage(self, amount: float) -> bool:
        """Returns True if wall is destroyed"""
        if not self.destructible:
            return False
        self.health -= amount
        if self.health <= 0:
            return True
        # Darken color as wall takes damage
        damage_factor = self.health / 100
        self.color = tuple(int(c * damage_factor) for c in (200, 150, 150))
        return False
    
    def render(self, screen: pygame.Surface) -> None:
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)
        # Add a darker outline
        pygame.draw.rect(screen, (max(0, self.color[0]-30), 
                                max(0, self.color[1]-30), 
                                max(0, self.color[2]-30)), rect, 2)

class LandingPad:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = (0, 255, 0)  # Green for landing pads
        self.surface_height = y - height/2  # The top surface of the pad
        
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.width/2, self.y - self.height/2, 
                         self.width, self.height)
                         
    def is_safe_landing(self, entity_rect: pygame.Rect, velocity_y: float) -> bool:
        """Check if the entity is landing safely from above"""
        # Check if entity is near the top surface
        entity_bottom = entity_rect.bottom
        if abs(entity_bottom - self.surface_height) > 5:  # Small tolerance for landing
            return False
            
        # Check if entity is horizontally aligned
        pad_rect = self.get_rect()
        return (entity_rect.left >= pad_rect.left and 
                entity_rect.right <= pad_rect.right)
        
    def render(self, screen: pygame.Surface) -> None:
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)
        # Draw a white H on the landing pad
        line_width = max(2, int(self.width * 0.1))
        # Vertical lines of H
        pygame.draw.line(screen, (255, 255, 255),
                        (rect.left + self.width * 0.2, rect.top + self.height * 0.2),
                        (rect.left + self.width * 0.2, rect.top + self.height * 0.8),
                        line_width)
        pygame.draw.line(screen, (255, 255, 255),
                        (rect.right - self.width * 0.2, rect.top + self.height * 0.2),
                        (rect.right - self.width * 0.2, rect.top + self.height * 0.8),
                        line_width)
        # Horizontal line of H
        pygame.draw.line(screen, (255, 255, 255),
                        (rect.left + self.width * 0.2, rect.top + self.height * 0.5),
                        (rect.right - self.width * 0.2, rect.top + self.height * 0.5),
                        line_width)

class World:
    def __init__(self):
        self.walls: List[Wall] = []
        self.landing_pads: List[LandingPad] = []
        
    def add_wall(self, wall: Wall) -> None:
        self.walls.append(wall)
        
    def add_landing_pad(self, pad: LandingPad) -> None:
        self.landing_pads.append(pad)
        
    def remove_wall(self, wall: Wall) -> None:
        if wall in self.walls:
            self.walls.remove(wall)
            
    def check_collision(self, rect: pygame.Rect) -> Optional[Wall]:
        """Returns the first wall that collides with the given rect"""
        for wall in self.walls:
            if wall.get_rect().colliderect(rect):
                return wall
        return None
    
    def handle_projectile_collision(self, projectile_rect: pygame.Rect, damage: float) -> bool:
        """Returns True if projectile should be destroyed"""
        wall = self.check_collision(projectile_rect)
        if wall:
            if wall.destructible:
                if wall.take_damage(damage):
                    self.remove_wall(wall)
            return True
        return False
    
    def handle_entity_collision(self, entity_rect: pygame.Rect) -> bool:
        """Returns True if entity collides with any wall"""
        return self.check_collision(entity_rect) is not None
        
    def is_on_landing_pad(self, entity_rect: pygame.Rect, velocity_y: float) -> bool:
        """Check if an entity is on a landing pad"""
        for pad in self.landing_pads:
            if pad.is_safe_landing(entity_rect, velocity_y):
                print(f"Safe landing detected! VelY: {velocity_y}")
                return True
        return False
        
    def render(self, screen: pygame.Surface) -> None:
        for pad in self.landing_pads:
            pad.render(screen)
        for wall in self.walls:
            wall.render(screen)
