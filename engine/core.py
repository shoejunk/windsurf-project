import pygame
import sys
from typing import Dict, List, Optional, Type

class GameEngine:
    def __init__(self, width: int = 800, height: int = 600, title: str = "Game"):
        pygame.init()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60
        self.delta_time = 0
        self.scenes: Dict[str, 'Scene'] = {}
        self.current_scene: Optional['Scene'] = None
        
    def add_scene(self, name: str, scene: 'Scene') -> None:
        self.scenes[name] = scene
        scene.engine = self
        
    def set_scene(self, name: str) -> None:
        if name in self.scenes:
            self.current_scene = self.scenes[name]
            self.current_scene.on_enter()
            
    def run(self) -> None:
        self.running = True
        while self.running:
            self.delta_time = self.clock.tick(self.fps) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.current_scene:
                    self.current_scene.handle_event(event)
            
            if self.current_scene:
                self.current_scene.update(self.delta_time)
                self.current_scene.render(self.screen)
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

class Scene:
    def __init__(self):
        self.engine: Optional[GameEngine] = None
        self.entities: List['Entity'] = []
        self.camera = None
    
    def add_entity(self, entity: 'Entity') -> None:
        self.entities.append(entity)
        entity.scene = self
    
    def handle_event(self, event: pygame.event.Event) -> None:
        for entity in self.entities:
            entity.handle_event(event)
    
    def update(self, delta_time: float) -> None:
        for entity in self.entities:
            for component in entity.components:
                component.update(delta_time)
    
    def render(self, screen: pygame.Surface) -> None:
        for entity in self.entities:
            if not self.camera:
                return
            
            # Adjust position for camera
            screen_x = entity.x - self.camera.x
            screen_y = entity.y - self.camera.y
            
            # Save original position
            orig_x, orig_y = entity.x, entity.y
            
            # Temporarily adjust position for rendering
            entity.x = screen_x
            entity.y = screen_y
            
            # Render all components
            for component in entity.components:
                component.render(screen)
                
            # Restore original position
            entity.x, entity.y = orig_x, orig_y
            
    def on_enter(self) -> None:
        pass
    
    def on_exit(self) -> None:
        pass

class Entity:
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y
        self.width = 0
        self.height = 0
        self.components = []
        self.scene = None
        
    def add_component(self, component: 'Component') -> None:
        self.components.append(component)
        component.entity = self
        
    def get_component(self, component_type: Type['Component']) -> Optional['Component']:
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None
        
    def update(self, delta_time: float) -> None:
        pass  # Let scene handle component updates
        
    def render(self, screen: pygame.Surface) -> None:
        pass  # Let scene handle component renders
        
    def handle_event(self, event: pygame.event.Event) -> None:
        for component in self.components:
            component.handle_event(event)
    
    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.width/2, self.y - self.height/2,
                         self.width, self.height)

class Component:
    def __init__(self):
        self.entity: Optional[Entity] = None
    
    def handle_event(self, event: pygame.event.Event) -> None:
        pass
    
    def update(self, delta_time: float) -> None:
        pass
    
    def render(self, screen: pygame.Surface) -> None:
        pass
