import pygame
from typing import Dict, Set
from .core import Component

class InputComponent(Component):
    def __init__(self):
        super().__init__()
        self.keys_pressed: Set[int] = set()
        self.keys_down: Set[int] = set()
        self.keys_up: Set[int] = set()
        
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
            self.keys_down.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)
            self.keys_up.add(event.key)
    
    def update(self, delta_time: float) -> None:
        # Clear one-frame key states
        self.keys_down.clear()
        self.keys_up.clear()
    
    def is_key_pressed(self, key: int) -> bool:
        return key in self.keys_pressed
    
    def is_key_down(self, key: int) -> bool:
        return key in self.keys_down
    
    def is_key_up(self, key: int) -> bool:
        return key in self.keys_up
