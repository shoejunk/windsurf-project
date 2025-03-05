import pygame
import math
import random
from engine.core import GameEngine, Scene, Entity, Component
from engine.physics import PhysicsComponent
from engine.graphics import SpriteComponent
from engine.weapons import WeaponComponent
from engine.world import World, Wall, LandingPad
from engine.camera import Camera
import os

class ParticleEmitter:
    def __init__(self):
        self.particles = []
        self.entity = None
        
    def set_entity(self, entity):
        self.entity = entity
        
    def handle_event(self, event: pygame.event.Event) -> None:
        pass  # No event handling needed
        
    def update(self, delta_time: float) -> None:
        """Update all particles"""
        # Update existing particles
        for particle in self.particles[:]:  # Copy list for safe removal
            particle['x'] += particle['vel_x'] * delta_time
            particle['y'] += particle['vel_y'] * delta_time
            particle['time'] += delta_time
            
            # Remove dead particles
            if particle['time'] >= particle['lifetime']:
                self.particles.remove(particle)
                
    def render(self, surface: pygame.Surface) -> None:
        """Draw all particles"""
        if not self.entity or not self.entity.scene:
            return
            
        camera = self.entity.scene.camera
        
        # Create a temporary surface for particles
        particle_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for particle in self.particles:
            alpha = int(255 * (1 - particle['time'] / particle['lifetime']))
            color = (*particle['color'], alpha)
            screen_x = int(particle['x'] - camera.x)
            screen_y = int(particle['y'] - camera.y)
            
            # Only draw if on screen
            if (0 <= screen_x <= surface.get_width() and 
                0 <= screen_y <= surface.get_height()):
                pygame.draw.circle(particle_surf, color, (screen_x, screen_y), 2)
        
        # Blit particle surface onto main surface
        surface.blit(particle_surf, (0, 0))
        
    def emit(self, x: float, y: float, vel_x: float, vel_y: float, color: tuple, lifetime: float) -> None:
        """Emit a new particle"""
        if len(self.particles) < 100:  # Limit max particles
            self.particles.append({
                'x': x,
                'y': y,
                'vel_x': vel_x,
                'vel_y': vel_y,
                'color': color,
                'lifetime': lifetime,
                'time': 0
            })

class InputComponent(Component):
    def __init__(self):
        self.keys = pygame.key.get_pressed()
        
    def update(self, delta_time: float) -> None:
        self.keys = pygame.key.get_pressed()
        
    def is_key_pressed(self, key: int) -> bool:
        return self.keys[key]


class Helicopter(Entity):
    def __init__(self, x: float = 100, y: float = 100):
        super().__init__(x, y)
        self.width = 64  # Match sprite size
        self.height = 32
        self.velocity_x = 0
        self.velocity_y = 0
        self.state = "landed"  # landed, taking_off, flying
        self.fuel = 100
        self.max_speed = 300
        self.gravity = 200  # Gravity acceleration
        self.terminal_velocity = 200  # Maximum falling speed
        self.shoot_cooldown = 0.2  # Seconds between shots
        self.time_since_last_shot = 0.0
        
        # Create helicopter sprite
        sprite_size = (64, 32)
        sprite_surface = pygame.Surface(sprite_size, pygame.SRCALPHA)
        
        # Body
        body_color = (50, 50, 50)  # Dark gray
        body_rect = pygame.Rect(16, 8, 32, 16)
        pygame.draw.rect(sprite_surface, body_color, body_rect)
        
        # Cockpit
        cockpit_color = (100, 149, 237)  # Cornflower blue
        cockpit_rect = pygame.Rect(40, 10, 8, 8)
        pygame.draw.rect(sprite_surface, cockpit_color, cockpit_rect)
        
        # Main rotor
        rotor_color = (169, 169, 169)  # Dark gray
        rotor_rect = pygame.Rect(8, 4, 48, 2)
        pygame.draw.rect(sprite_surface, rotor_color, rotor_rect)
        
        # Tail
        tail_rect = pygame.Rect(8, 12, 8, 4)
        pygame.draw.rect(sprite_surface, body_color, tail_rect)
        
        # Tail rotor
        tail_rotor_rect = pygame.Rect(4, 10, 2, 8)
        pygame.draw.rect(sprite_surface, rotor_color, tail_rotor_rect)
        
        # Landing gear
        gear_color = (128, 128, 128)  # Gray
        left_gear_rect = pygame.Rect(20, 24, 4, 4)
        right_gear_rect = pygame.Rect(40, 24, 4, 4)
        pygame.draw.rect(sprite_surface, gear_color, left_gear_rect)
        pygame.draw.rect(sprite_surface, gear_color, right_gear_rect)
        
        # Create and add components
        self.sprite = SpriteComponent(sprite_surface)
        self.add_component(self.sprite)
        
        self.physics = PhysicsComponent()
        self.add_component(self.physics)
        
        self.input = InputComponent()
        self.add_component(self.input)
        
        self.weapon = WeaponComponent()
        self.add_component(self.weapon)
        
    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.width/2,
            self.y - self.height/2,
            self.width,
            self.height
        )
        
    def render(self, screen: pygame.Surface) -> None:
        super().render(screen)
        
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        
    def update(self, delta_time: float) -> None:
        """Update helicopter state and position"""
        keys = pygame.key.get_pressed()
        
        # Update shoot cooldown
        if hasattr(self, 'weapon'):
            self.time_since_last_shot += delta_time
        
        if self.state == "landed":
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.state = "taking_off"
                self.velocity_y = -50  # Initial upward velocity
        
        elif self.state in ["taking_off", "flying"]:
            # Apply gravity
            self.velocity_y = min(self.velocity_y + self.gravity * delta_time, self.terminal_velocity)
            
            # Vertical movement
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.velocity_y = max(self.velocity_y - 400 * delta_time, -self.max_speed)
            
            # Horizontal movement
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.velocity_x = max(self.velocity_x - 200 * delta_time, -self.max_speed)
                self.sprite.flip_x = True
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.velocity_x = min(self.velocity_x + 200 * delta_time, self.max_speed)
                self.sprite.flip_x = False
            else:
                # Gradually slow down horizontal movement
                if abs(self.velocity_x) < 10:
                    self.velocity_x = 0
                else:
                    self.velocity_x *= 0.95
            
            # Shooting
            if keys[pygame.K_SPACE] and self.time_since_last_shot >= self.shoot_cooldown:
                direction = -400 if self.sprite.flip_x else 400
                self.weapon.fire(self.x, self.y, direction, 0)
                self.time_since_last_shot = 0
            
            # Update position
            self.x += self.velocity_x * delta_time
            self.y += self.velocity_y * delta_time
            
            # Check for landing
            if self.scene:
                for pad in self.scene.world.landing_pads:
                    if pad.check_landing(self.get_collision_rect()) and self.velocity_y > 0:
                        self.state = "landed"
                        self.velocity_x = 0
                        self.velocity_y = 0
                        # Center the helicopter on the pad
                        self.x = pad.x + pad.width/2
                        self.y = pad.y - self.height/2
                        break

class PhysicsComponent(Component):
    def __init__(self):
        super().__init__()
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.gravity = 60.0  # Reduced gravity further
        self.force_x = 0.0
        self.force_y = 0.0
        
    def apply_force(self, x: float, y: float) -> None:
        self.force_x += x
        self.force_y += y
        
    def update(self, delta_time: float) -> None:
        # Apply forces
        self.velocity_x += self.force_x * delta_time
        self.velocity_y += self.force_y * delta_time
        
        # Clear forces
        self.force_x = 0.0
        self.force_y = 0.0
        
        # Cap velocities with stricter downward limit
        max_speed_x = 150  # Reduced from 200
        max_speed_y_up = 180  # Reduced from 250
        max_speed_y_down = 100  # Keep downward speed limited for control
        self.velocity_x = min(max(self.velocity_x, -max_speed_x), max_speed_x)
        self.velocity_y = min(max(self.velocity_y, -max_speed_y_up), max_speed_y_down)

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.target = None
        self.screen_width = 800
        self.screen_height = 600
        self.world_width = 4000
        self.world_height = 4000
        
    def set_target(self, target):
        self.target = target
        
    def update(self, delta_time: float):
        if self.target:
            # Center camera on target
            target_x = self.target.x - self.screen_width/2
            target_y = self.target.y - self.screen_height/2
            
            # Clamp camera to world bounds
            self.x = max(0, min(target_x, self.world_width - self.screen_width))
            self.y = max(0, min(target_y, self.world_height - self.screen_height))

class GameScene(Scene):
    def __init__(self):
        super().__init__()
        self.world = World()
        self.camera = Camera()
        self.helicopter = None
        self.game_over = False
        self.load_level("levels/level1.json")
        self.spawn_helicopter()
        
    def spawn_helicopter(self) -> None:
        """Spawn the helicopter at the first landing pad"""
        # Clear any existing entities
        self.entities.clear()
        self.helicopter = None
        
        if self.world.landing_pads:
            pad = self.world.landing_pads[0]
            spawn_x = pad.x + pad.width/2  # Center on pad
            spawn_y = pad.y - 20  # Above the pad
            self.helicopter = Helicopter(spawn_x, spawn_y)
            self.add_entity(self.helicopter)
            self.camera.set_target(self.helicopter)
            print(f"Spawned helicopter at ({spawn_x}, {spawn_y})")  # Debug
            
    def restart_game(self) -> None:
        """Restart the game with the same level"""
        print("Restarting game...")  # Debug
        # Clear entities
        self.entities.clear()
        self.helicopter = None
        # Reset game state
        self.game_over = False
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
        # Respawn helicopter
        self.spawn_helicopter()
            
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.game_over:
            self.restart_game()
        else:
            for entity in self.entities:
                entity.handle_event(event)
                
    def update(self, delta_time: float) -> None:
        if not self.game_over:
            # Update camera
            self.camera.update(delta_time)
            
            # Update all entities and their components
            for entity in self.entities:
                # Update entity
                entity.update(delta_time)
                # Update components
                for component in entity.components:
                    component.update(delta_time)
                    
            # Handle helicopter collisions
            if self.helicopter:
                collision_rect = self.helicopter.get_collision_rect()
                
                # Check wall collisions
                for wall in self.world.walls:
                    wall_rect = wall.get_rect()
                    if wall_rect.colliderect(collision_rect):
                        print(f"Helicopter hit wall at ({wall.x}, {wall.y})")  # Debug
                        # Crash the helicopter
                        self.game_over = True
                        self.helicopter = None
                        break
                        
                # Check landing pad collisions
                if not self.game_over:  # Only check if we haven't crashed
                    for pad in self.world.landing_pads:
                        if pad.check_landing(collision_rect):
                            if self.helicopter.velocity_y > 0:  # Moving downward
                                if self.helicopter.velocity_y < 100:  # Safe landing speed
                                    # Safe landing
                                    self.helicopter.state = "landed"
                                    self.helicopter.velocity_x = 0
                                    self.helicopter.velocity_y = 0
                                    # Center on pad
                                    self.helicopter.x = pad.x + pad.width/2
                                    self.helicopter.y = pad.y - self.helicopter.height/2
                                else:
                                    # Crash landing - too fast
                                    print("Crash landing - too fast!")  # Debug
                                    self.game_over = True
                                    self.helicopter = None
                            break
                
                # Check if out of bounds
                if self.helicopter and (
                    self.helicopter.y > self.world.height + 100 or 
                    self.helicopter.y < -100 or 
                    self.helicopter.x < -100 or 
                    self.helicopter.x > self.world.width + 100):
                    print("Helicopter out of bounds!")  # Debug
                    self.game_over = True
                    self.helicopter = None
                    
    def render(self, screen: pygame.Surface) -> None:
        """Render the game scene"""
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Render world (walls and landing pads)
        self.world.render(screen, self.camera.x, self.camera.y)
        
        # Render all entities and their components
        for entity in self.entities:
            # Convert world coordinates to screen coordinates
            screen_x = entity.x - self.camera.x
            screen_y = entity.y - self.camera.y
            
            # Save original position
            orig_x, orig_y = entity.x, entity.y
            
            # Temporarily adjust position for rendering
            entity.x = screen_x
            entity.y = screen_y
            
            # Render entity and components
            for component in entity.components:
                component.render(screen)
                
            # Restore original position
            entity.x, entity.y = orig_x, orig_y
            
        # Draw game over message if needed
        if self.game_over:
            font = pygame.font.Font(None, 74)
            text = font.render('Game Over! Press R to restart', True, (255, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (400, 300)
            screen.blit(text, text_rect)
        
    def handle_collision(self, wall: Wall, collision_rect: pygame.Rect) -> None:
        if not self.helicopter:
            return
            
        # Get the collision direction and overlap
        wall_rect = wall.get_rect()
        
        # Calculate overlap on each side
        left_overlap = collision_rect.right - wall_rect.left
        right_overlap = wall_rect.right - collision_rect.left
        top_overlap = collision_rect.bottom - wall_rect.top
        bottom_overlap = wall_rect.bottom - collision_rect.top
        
        # Find the smallest overlap to determine collision direction
        overlaps = [
            ("left", left_overlap),
            ("right", right_overlap),
            ("top", top_overlap),
            ("bottom", bottom_overlap)
        ]
        collision_side, min_overlap = min(overlaps, key=lambda x: x[1])
        
        # Check if this is a safe landing
        is_safe_landing = (
            collision_side == "top" and  # Must hit from above
            self.helicopter.velocity_y > 0 and  # Must be moving downward
            self.helicopter.velocity_y < 100 and  # Not too fast vertically
            abs(self.helicopter.velocity_x) < 50  # Not too fast horizontally
        )
        
        if not is_safe_landing:
            # Collision from side or bottom, or unsafe landing - destroy helicopter
            self.game_over = True
            self.helicopter = None
            return
            
        # Safe landing - stop movement
        self.helicopter.state = "landed"
        self.helicopter.velocity_x = 0
        self.helicopter.velocity_y = 0
        
        # Adjust position to rest on top of surface
        self.helicopter.y = wall_rect.top - collision_rect.height / 2
        
    def load_level(self, level_path: str) -> None:
        if not os.path.exists(level_path):
            print(f"Error: Level file not found: {level_path}")
            return
            
        try:
            self.world.load_level(level_path)
            print(f"Loaded level from {level_path}")
        except Exception as e:
            print(f"Error loading level: {e}")
            return
            
    def add_entity(self, entity: Entity) -> None:
        super().add_entity(entity)
        entity.scene = self  

def main():
    print("Starting game...")
    engine = GameEngine(800, 600, "Fort Apocalypse Inspired Game")
    scene = GameScene()
    engine.add_scene("game", scene)
    engine.set_scene("game")
    engine.run()

if __name__ == "__main__":
    main()
