import pygame
from typing import List, Optional, Tuple
from .core import Entity, Component
from .physics import PhysicsComponent
import json
import os
import random

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
        """Get collision rectangle in world coordinates"""
        return pygame.Rect(self.x - self.width/2, self.y - self.height/2,
                         self.width, self.height)
                         
    def take_damage(self, amount: float) -> bool:
        """Returns True if wall is destroyed"""
        if self.destructible:
            self.health -= amount
            if self.health <= 0:
                return True
        return False
        
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        """Render wall with camera offset"""
        # Convert world coordinates to screen coordinates
        screen_x = self.x - camera_x - self.width/2
        screen_y = self.y - camera_y - self.height/2
        
        # Get rect in screen coordinates
        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        
        # Draw wall
        pygame.draw.rect(screen, self.color, rect)
        # Draw border
        pygame.draw.rect(screen, (max(0, self.color[0]-30), 
                                max(0, self.color[1]-30), 
                                max(0, self.color[2]-30)), rect, 2)

class LandingPad:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Create landing pad sprite
        sprite_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Base platform (dark gray)
        platform_color = (50, 50, 50)
        platform_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(sprite_surface, platform_color, platform_rect)
        
        # Landing markers (yellow)
        marker_color = (255, 255, 0)
        marker_width = 10
        # Left marker
        pygame.draw.rect(sprite_surface, marker_color, 
                        pygame.Rect(0, 0, marker_width, height))
        # Right marker
        pygame.draw.rect(sprite_surface, marker_color, 
                        pygame.Rect(width - marker_width, 0, marker_width, height))
        
        # H symbol (white)
        h_color = (255, 255, 255)
        h_width = width // 3
        h_height = height - 10
        h_x = (width - h_width) // 2
        h_y = 5
        
        # Vertical lines of H
        pygame.draw.rect(sprite_surface, h_color, 
                        pygame.Rect(h_x, h_y, 4, h_height))
        pygame.draw.rect(sprite_surface, h_color, 
                        pygame.Rect(h_x + h_width - 4, h_y, 4, h_height))
        # Horizontal line of H
        pygame.draw.rect(sprite_surface, h_color, 
                        pygame.Rect(h_x, h_y + h_height//2 - 2, h_width, 4))
                        
        self.sprite = sprite_surface
        
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle in world coordinates"""
        return pygame.Rect(self.x - self.width/2, self.y - self.height/2,
                         self.width, self.height)
                         
    def check_landing(self, entity_rect: pygame.Rect) -> bool:
        """Check if the entity can land on this pad"""
        pad_rect = self.get_rect()
        
        # Must be above the pad
        if entity_rect.bottom < pad_rect.top:
            return False
            
        # Must be within horizontal bounds
        if (entity_rect.centerx < pad_rect.left or 
            entity_rect.centerx > pad_rect.right):
            return False
            
        # Must be close to the pad surface
        if abs(entity_rect.bottom - pad_rect.top) > 10:
            return False
            
        return True
        
    def is_safe_landing(self, entity_rect: pygame.Rect, velocity_y: float) -> bool:
        """Check if the entity is landing safely from above"""
        # Check if entity is near the top surface
        entity_bottom = entity_rect.bottom
        if abs(entity_bottom - (self.y - self.height/2)) > 5:  # Small tolerance for landing
            return False
            
        # Check if entity is horizontally aligned
        pad_rect = self.get_rect()
        return (entity_rect.left >= pad_rect.left and 
                entity_rect.right <= pad_rect.right)
        
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        """Render landing pad with camera offset"""
        screen_x = self.x - camera_x - self.width/2
        screen_y = self.y - camera_y - self.height/2
        screen.blit(self.sprite, (screen_x, screen_y))

class World:
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.walls: List[Wall] = []
        self.landing_pads: List[LandingPad] = []
        
    def load_level(self, level_path: str) -> None:
        """Load a level from a JSON file"""
        if not os.path.exists(level_path):
            raise FileNotFoundError(f"Level file not found: {level_path}")
            
        with open(level_path, 'r') as f:
            level_data = json.load(f)
            
        # Set world dimensions
        self.width = level_data.get('width', 800)
        self.height = level_data.get('height', 600)
        
        # Clear existing objects
        self.walls.clear()
        self.landing_pads.clear()
        
        # Load walls
        for wall_data in level_data.get('walls', []):
            wall = Wall(
                wall_data['x'],
                wall_data['y'],
                wall_data['width'],
                wall_data['height'],
                wall_data.get('destructible', False)
            )
            self.walls.append(wall)
            
        # Load landing pads
        for pad_data in level_data.get('landing_pads', []):
            pad = LandingPad(
                pad_data['x'],
                pad_data['y'],
                pad_data.get('width', 80),  # Default 80 wide
                pad_data.get('height', 20)  # Default 20 tall
            )
            self.landing_pads.append(pad)
            print(f"Added landing pad at ({pad.x}, {pad.y}) with size {pad.width}x{pad.height}")
            
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
        
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for pad in self.landing_pads:
            pad.render(screen, camera_x, camera_y)
        for wall in self.walls:
            wall.render(screen, camera_x, camera_y)
