import pygame
from typing import Tuple, Optional
from .core import Component

class PhysicsComponent(Component):
    def __init__(self):
        super().__init__()
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.acceleration = 0.0
        self.max_speed = 500.0  # Increased max speed for better control
        self.drag = 0.95
        self.gravity = 200.0  # Increased gravity further
        self.rotation = 0.0
        self.collision_radius = 20
        
    def apply_force(self, force_x: float, force_y: float) -> None:
        self.velocity_x += force_x
        self.velocity_y += force_y
        
        # Limit speed
        speed = (self.velocity_x ** 2 + self.velocity_y ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.velocity_x *= scale
            self.velocity_y *= scale
    
    def update(self, delta_time: float) -> None:
        if self.entity:
            # Apply gravity
            self.velocity_y += self.gravity * delta_time
            
            # Apply drag (more drag horizontally than vertically)
            self.velocity_x *= self.drag
            self.velocity_y *= 0.95  # Increased vertical drag slightly for better control
            
            # Update position
            self.entity.x += self.velocity_x * delta_time
            self.entity.y += self.velocity_y * delta_time
    
    def check_collision(self, other: 'PhysicsComponent') -> bool:
        if not self.entity or not other.entity:
            return False
            
        dx = self.entity.x - other.entity.x
        dy = self.entity.y - other.entity.y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        return distance < (self.collision_radius + other.collision_radius)

class CollisionManager:
    @staticmethod
    def resolve_collision(phys1: PhysicsComponent, phys2: PhysicsComponent) -> None:
        if not phys1.entity or not phys2.entity:
            return
            
        # Calculate collision normal
        dx = phys2.entity.x - phys1.entity.x
        dy = phys2.entity.y - phys1.entity.y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        if distance == 0:
            return
            
        nx = dx / distance
        ny = dy / distance
        
        # Calculate relative velocity
        rvx = phys2.velocity_x - phys1.velocity_x
        rvy = phys2.velocity_y - phys1.velocity_y
        
        # Calculate impulse
        restitution = 0.8
        j = -(1 + restitution) * (rvx * nx + rvy * ny)
        
        # Apply impulse
        phys1.velocity_x -= j * nx
        phys1.velocity_y -= j * ny
        phys2.velocity_x += j * nx
        phys2.velocity_y += j * ny
