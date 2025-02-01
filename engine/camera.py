import pygame
from typing import Tuple, Optional
from .core import Entity

class Camera:
    def __init__(self, width: int, height: int, world_bounds: Tuple[int, int, int, int]):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        # world_bounds is (left, top, right, bottom)
        self.world_bounds = world_bounds
        self.target: Optional[Entity] = None
        self.lerp_speed = 5.0  # Speed of camera movement (higher = faster)
        
    def set_target(self, target: Entity) -> None:
        """Set the entity for the camera to follow"""
        self.target = target
        
    def update(self, delta_time: float) -> None:
        if not self.target:
            return
            
        # Calculate desired camera position (center on target)
        target_x = self.target.x - self.width / 2
        target_y = self.target.y - self.height / 2
        
        # Smoothly move camera towards target
        self.x += (target_x - self.x) * self.lerp_speed * delta_time
        self.y += (target_y - self.y) * self.lerp_speed * delta_time
        
        # Clamp camera position to world bounds
        self.x = max(self.world_bounds[0], min(self.x, self.world_bounds[2] - self.width))
        self.y = max(self.world_bounds[1], min(self.y, self.world_bounds[3] - self.height))
        
    def get_surface_pos(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        return (world_x - self.x, world_y - self.y)
        
    def get_world_pos(self, surface_x: float, surface_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        return (surface_x + self.x, surface_y + self.y)
        
    def in_view(self, world_x: float, world_y: float, margin: float = 0) -> bool:
        """Check if a world position is within the camera view"""
        screen_x, screen_y = self.get_surface_pos(world_x, world_y)
        return (-margin <= screen_x <= self.width + margin and 
                -margin <= screen_y <= self.height + margin)
