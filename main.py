import pygame
import math
import random
from engine.core import GameEngine, Scene, Entity, Component
from engine.physics import PhysicsComponent
from engine.graphics import SpriteComponent
from engine.weapons import WeaponComponent
from engine.world import World, Wall, LandingPad
from engine.camera import Camera

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
        self.physics = PhysicsComponent()
        self.input = InputComponent()
        self.state = "landed"  # landed, taking_off, flying
        self.initial_y = y  # Store initial Y for takeoff check
        self.scene = None  # Will be set when added to scene
        
        # Create a more detailed helicopter sprite
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
        
        # Create sprite component
        self.sprite = SpriteComponent(sprite_surface)
        self.sprite.set_scale(1.0)
        self.add_component(self.sprite)
        
        # Create weapon system
        self.weapon = WeaponComponent()
        self.add_component(self.weapon)
        
    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - 15, self.y - 10, 30, 20)
        
    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        
        # Update input first
        self.input.update(delta_time)
        
        # Handle input
        base_thrust = 400.0  # Base thrust for movement
        moving = False
        moving_vertically = False
        
        # State machine
        if self.state == "landed":
            # Reset physics when landed
            self.physics.velocity_x = 0
            self.physics.velocity_y = 0
            
            # Check for takeoff
            if self.input.is_key_pressed(pygame.K_UP):
                self.state = "taking_off"
                self.physics.velocity_y = -25
                return
                
        elif self.state == "taking_off":
            # Keep upward velocity during takeoff
            self.physics.velocity_y = -25
            moving = True
            moving_vertically = True
            if self.y < self.initial_y - 50:
                self.state = "flying"
                
        elif self.state == "flying":
            # Always apply gravity in flying state
            self.physics.apply_force(0, self.physics.gravity)
            
            # Apply thrust based on input
            if self.input.is_key_pressed(pygame.K_UP):
                self.physics.apply_force(0, -self.physics.gravity * 3.0)  # Increased from 2.0 to 3.0
                moving = True
                moving_vertically = True
            if self.input.is_key_pressed(pygame.K_DOWN):
                self.physics.apply_force(0, base_thrust * 0.6)  # Increased downward thrust too
                moving = True
                moving_vertically = True
                
            # Fire weapon
            if self.input.is_key_pressed(pygame.K_SPACE):
                # Fire in the direction the helicopter is facing
                direction = 180 if self.sprite.flip_x else 0
                self.weapon.fire(direction)
        
        # Horizontal movement always works (but slower when landed)
        horizontal_thrust = base_thrust * (0.1 if self.state == "landed" else 0.4)  # Increased horizontal thrust
        if self.input.is_key_pressed(pygame.K_LEFT):
            self.physics.apply_force(-horizontal_thrust, 0)
            self.sprite.flip_x = True
            moving = True
        if self.input.is_key_pressed(pygame.K_RIGHT):
            self.physics.apply_force(horizontal_thrust, 0)
            self.sprite.flip_x = False
            moving = True
            
        # Update physics if not landed
        if self.state != "landed":
            self.physics.update(delta_time)
            self.x += self.physics.velocity_x * delta_time
            self.y += self.physics.velocity_y * delta_time


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
        
    def set_target(self, target):
        self.target = target
        
    def update(self, delta_time: float):
        if self.target:
            self.x = self.target.x - 400  # Center horizontally
            self.y = self.target.y - 300  # Center vertically

class GameScene(Scene):
    def __init__(self):
        super().__init__()
        self.world = World()
        self.camera = Camera()  # Create camera before spawning helicopter
        self.game_over = False
        self.game_over_reason = ""
        self.generate_world()
        self.spawn_helicopter()  # Spawn helicopter after camera is created
        
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
            self.helicopter.physics.velocity_y > 0 and  # Must be moving downward
            self.helicopter.physics.velocity_y < 100 and  # Not too fast vertically
            abs(self.helicopter.physics.velocity_x) < 50  # Not too fast horizontally
        )
        
        if not is_safe_landing:
            # Collision from side or bottom, or unsafe landing - destroy helicopter
            self.game_over = True
            self.game_over_reason = "Helicopter crashed!"
            self.helicopter = None
            return
            
        # Safe landing - stop movement
        self.helicopter.state = "landed"
        self.helicopter.physics.velocity_x = 0
        self.helicopter.physics.velocity_y = 0
        
        # Adjust position to rest on top of surface
        self.helicopter.y = wall_rect.top - collision_rect.height / 2
        
    def update(self, delta_time: float) -> None:
        if self.game_over:
            return
            
        if self.helicopter:
            # Update helicopter first
            self.helicopter.update(delta_time)
            
            # Check for landing pad collision first
            if self.helicopter.state == "flying":
                heli_rect = self.helicopter.get_collision_rect()
                for pad in self.world.landing_pads:
                    # Check if helicopter is above and close to the pad
                    pad_rect = pad.get_rect()
                    if (heli_rect.centerx >= pad_rect.left and 
                        heli_rect.centerx <= pad_rect.right and
                        abs(heli_rect.bottom - pad_rect.top) < 10 and
                        self.helicopter.physics.velocity_y > 0 and  # Moving downward
                        self.helicopter.physics.velocity_y < 100 and  # Not too fast
                        abs(self.helicopter.physics.velocity_x) < 50):  # Not moving too fast horizontally
                        # Safe landing
                        self.helicopter.state = "landed"
                        self.helicopter.physics.velocity_x = 0
                        self.helicopter.physics.velocity_y = 0
                        self.helicopter.y = pad_rect.top - heli_rect.height/2
                        break
            
            # Check wall collisions
            collision_rect = self.helicopter.get_collision_rect()
            wall = self.world.check_collision(collision_rect)
            if wall:
                self.handle_collision(wall, collision_rect)
                
            # Update camera to follow helicopter
            if self.helicopter:  # Check again as it might be destroyed
                self.camera.update(delta_time)
            
            # Update weapon and handle projectile collisions
            if self.helicopter and hasattr(self.helicopter, 'weapon'):
                # Update projectiles
                for projectile in self.helicopter.weapon.projectiles[:]:
                    # Check wall collisions
                    wall = self.world.check_collision(pygame.Rect(
                        projectile.x - projectile.radius, 
                        projectile.y - projectile.radius,
                        projectile.radius * 2, 
                        projectile.radius * 2))
                    
                    if wall:
                        # Try to damage the wall
                        if wall.take_damage(projectile.damage):
                            # Wall was destroyed
                            self.world.remove_wall(wall)
                        # Remove projectile regardless of wall type
                        self.helicopter.weapon.projectiles.remove(projectile)
    
    def render(self, screen: pygame.Surface) -> None:
        # Create a surface for camera view
        camera_surf = pygame.Surface((800, 600))
        camera_surf.fill((135, 206, 235))  # Sky blue background
        
        # Draw world
        for wall in self.world.walls:
            # Convert world coordinates to screen coordinates
            wall_rect = wall.get_rect()
            screen_rect = pygame.Rect(
                wall_rect.x - self.camera.x,
                wall_rect.y - self.camera.y,
                wall_rect.width,
                wall_rect.height
            )
            if (0 <= screen_rect.right and screen_rect.left <= 800 and
                0 <= screen_rect.bottom and screen_rect.top <= 600):
                wall.x -= self.camera.x
                wall.y -= self.camera.y
                wall.render(camera_surf)
                wall.x += self.camera.x
                wall.y += self.camera.y
        
        # Draw landing pads
        for pad in self.world.landing_pads:
            pad_rect = pad.get_rect()
            screen_rect = pygame.Rect(
                pad_rect.x - self.camera.x,
                pad_rect.y - self.camera.y,
                pad_rect.width,
                pad_rect.height
            )
            if (0 <= screen_rect.right and screen_rect.left <= 800 and
                0 <= screen_rect.bottom and screen_rect.top <= 600):
                pad.x -= self.camera.x
                pad.y -= self.camera.y
                pad.render(camera_surf)
                pad.x += self.camera.x
                pad.y += self.camera.y
        
        # Draw helicopter and its components
        if self.helicopter and hasattr(self.helicopter, 'sprite'):
            screen_x = self.helicopter.x - self.camera.x
            screen_y = self.helicopter.y - self.camera.y
            if 0 <= screen_x <= 800 and 0 <= screen_y <= 600:
                # Temporarily move helicopter to screen coordinates
                orig_x, orig_y = self.helicopter.x, self.helicopter.y
                self.helicopter.x, self.helicopter.y = screen_x, screen_y
                self.helicopter.sprite.render(camera_surf)
                
                # Draw projectiles
                if hasattr(self.helicopter, 'weapon'):
                    for projectile in self.helicopter.weapon.projectiles:
                        proj_screen_x = projectile.x - self.camera.x
                        proj_screen_y = projectile.y - self.camera.y
                        if 0 <= proj_screen_x <= 800 and 0 <= proj_screen_y <= 600:
                            # Temporarily move projectile to screen coordinates
                            orig_proj_x, orig_proj_y = projectile.x, projectile.y
                            projectile.x, projectile.y = proj_screen_x, proj_screen_y
                            projectile.render(camera_surf)
                            projectile.x, projectile.y = orig_proj_x, orig_proj_y
                
                self.helicopter.x, self.helicopter.y = orig_x, orig_y
        
        # Draw game over message if needed
        if self.game_over:
            font = pygame.font.Font(None, 64)
            text = font.render(self.game_over_reason, True, (255, 0, 0))
            text_rect = text.get_rect(center=(400, 300))
            camera_surf.blit(text, text_rect)
            
            # Draw restart message
            font = pygame.font.Font(None, 32)
            text = font.render("Press R to restart", True, (255, 255, 255))
            text_rect = text.get_rect(center=(400, 350))
            camera_surf.blit(text, text_rect)
        
        # Final blit to screen
        screen.blit(camera_surf, (0, 0))

    def is_grid_space_free(self, grid_x: int, grid_y: int, width: int = 1, height: int = 1) -> bool:
        """Check if a rectangular area in the grid is free"""
        if (grid_x < 0 or grid_x + width > self.grid_width or 
            grid_y < 0 or grid_y + height > self.grid_height):
            return False
            
        for x in range(grid_x, grid_x + width):
            for y in range(grid_y, grid_y + height):
                if self.grid[x][y]:
                    return False
        return True
        
    def place_block(self, grid_x: int, grid_y: int, destructible: bool = True):
        """Place a block in the grid and create the wall"""
        if not self.is_grid_space_free(grid_x, grid_y):
            return
            
        self.grid[grid_x][grid_y] = True
        color = (200, 150, 150) if destructible else (80, 80, 80)
        x = grid_x * self.block_size + self.block_size/2
        y = grid_y * self.block_size + self.block_size/2
        self.world.add_wall(Wall(x, y, self.block_size, self.block_size, destructible, color))
        
    def create_wall_line(self, grid_x: int, grid_y: int, blocks: int, vertical: bool = False, destructible: bool = True):
        """Create a line of wall blocks either horizontally or vertically"""
        if vertical:
            if not self.is_grid_space_free(grid_x, grid_y, 1, blocks):
                return
            for i in range(blocks):
                self.place_block(grid_x, grid_y + i, destructible)
        else:
            if not self.is_grid_space_free(grid_x, grid_y, blocks, 1):
                return
            for i in range(blocks):
                self.place_block(grid_x + i, grid_y, destructible)
    
    def place_landing_pad(self, grid_x: int, grid_y: int) -> None:
        """Place a landing pad at the specified grid position"""
        if not self.is_grid_space_free(grid_x, grid_y, 2, 1):  
            return
            
        # Mark grid spaces as occupied
        for dx in range(2):
            self.grid[grid_x + dx][grid_y] = True
        
        # Create landing pad (2x1 blocks)
        x = (grid_x + 1) * self.block_size
        y = grid_y * self.block_size + self.block_size/2
        self.world.add_landing_pad(LandingPad(x, y, self.block_size * 2, self.block_size))
        
    def setup_world(self):
        # Create border walls (indestructible)
        # Top border
        self.create_wall_line(0, 0, self.grid_width, False, False)
        
        # Bottom border
        self.create_wall_line(0, self.grid_height - 1, self.grid_width, False, False)
        
        # Left border
        for y in range(self.grid_height):
            self.place_block(0, y, False)
        
        # Right border
        for y in range(self.grid_height):
            self.place_block(self.grid_width - 1, y, False)
            
        # Place landing pads
        # Starting pad
        self.place_landing_pad(3, self.grid_height - 5)
        
        # Additional landing pads
        landing_pad_positions = [
            (self.grid_width - 5, self.grid_height - 5),  
            (self.grid_width - 5, 4),  
            (3, 4),  
            (self.grid_width // 2 - 1, self.grid_height // 2 - 1),  
        ]
        
        for pos in landing_pad_positions:
            self.place_landing_pad(*pos)
        
        # Create vertical columns of destructible walls
        for x in range(8, self.grid_width - 8, 10):
            if random.random() < 0.7:  
                height_blocks = random.randint(3, 8)
                y = random.randint(5, self.grid_height - height_blocks - 5)
                self.create_wall_line(x, y, height_blocks, True, True)
        
        # Create horizontal barriers
        for y in range(8, self.grid_height - 8, 8):
            if random.random() < 0.5:  
                width_blocks = random.randint(3, 8)
                x = random.randint(5, self.grid_width - width_blocks - 5)
                self.create_wall_line(x, y, width_blocks, False, True)
        
        # Add some indestructible obstacles
        for _ in range(20):
            width_blocks = random.randint(2, 4)
            height_blocks = random.randint(1, 2)
            attempts = 0
            while attempts < 10:  
                grid_x = random.randint(5, self.grid_width - width_blocks - 5)
                grid_y = random.randint(5, self.grid_height - height_blocks - 5)
                if self.is_grid_space_free(grid_x, grid_y, width_blocks, height_blocks):
                    for dx in range(width_blocks):
                        for dy in range(height_blocks):
                            self.place_block(grid_x + dx, grid_y + dy, False)
                    break
                attempts += 1
                
    def spawn_helicopter(self) -> None:
        """Spawn the helicopter at the first landing pad"""
        # Find the first landing pad
        if self.world.landing_pads:
            pad = self.world.landing_pads[0]
            spawn_x = pad.x
            spawn_y = pad.surface_height - 12  # Adjusted to sit properly on pad
            print(f"Spawning helicopter at {spawn_x}, {spawn_y}")
            self.helicopter = Helicopter(spawn_x, spawn_y)
            self.helicopter.state = "landed"  # Set initial state
            self.add_entity(self.helicopter)
            self.camera.set_target(self.helicopter)

    def add_entity(self, entity: Entity) -> None:
        super().add_entity(entity)
        entity.scene = self  

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.game_over:
                # Reset game
                self.game_over = False
                self.game_over_reason = ""
                self.world = World()
                self.generate_world()
                self.spawn_helicopter()
        if event.type == pygame.USEREVENT + 1:
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)
            self.spawn_helicopter()
    
    def generate_world(self):
        self.world_width = 3000
        self.world_height = 2000
        self.block_size = 40
        self.grid_width = self.world_width // self.block_size
        self.grid_height = self.world_height // self.block_size
        self.grid = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.setup_world()

def main():
    engine = GameEngine(800, 600, "Fort Apocalypse Inspired Game")
    game_scene = GameScene()
    engine.add_scene("game", game_scene)
    engine.set_scene("game")
    engine.run()

if __name__ == "__main__":
    main()
