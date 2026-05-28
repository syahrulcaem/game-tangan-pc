"""Small visual effects used when the player lands a hit."""

from __future__ import annotations

import math

import pygame

import settings


class HitEffect(pygame.sprite.Sprite):
    """Arcade-style burst animation shown when the rat gets hit."""

    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__()
        self.position = pygame.Vector2(position)
        self.age = 0.0
        self.lifetime = 0.35

    def update(self, dt: float) -> None:
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()

    def draw(self, surface: pygame.Surface) -> None:
        progress = min(1.0, self.age / self.lifetime)
        alpha = max(0, int(255 * (1.0 - progress)))
        radius = 20 + int(50 * progress)

        effect_surface = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        center = pygame.Vector2(effect_surface.get_width() / 2, effect_surface.get_height() / 2)

        pygame.draw.circle(
            effect_surface,
            (*settings.GOLD, alpha),
            center,
            max(4, radius),
            width=5,
        )

        for index in range(8):
            angle = (math.tau / 8) * index + progress
            start = center + pygame.Vector2(math.cos(angle), math.sin(angle)) * (radius * 0.55)
            end = center + pygame.Vector2(math.cos(angle), math.sin(angle)) * (radius + 12)
            pygame.draw.line(effect_surface, (*settings.RED, alpha), start, end, width=4)

        rect = effect_surface.get_rect(center=self.position)
        surface.blit(effect_surface, rect)
