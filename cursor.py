"""Virtual paw cursor controlled by the player's real hand."""

from __future__ import annotations

import pygame

import settings
from utils import damp, damp_vector, load_image


class Cursor(pygame.sprite.Sprite):
    """Screen cursor that smoothly follows the detected hand position."""

    def __init__(self) -> None:
        super().__init__()
        size = (settings.CURSOR_SIZE, settings.CURSOR_SIZE)
        self.open_image = load_image(settings.PAW_OPEN_PATH, size)
        self.closed_image = load_image(settings.PAW_CLOSED_PATH, size)

        self.position = pygame.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        self.target_position = self.position.copy()
        self.velocity = pygame.Vector2()

        self.closed = False
        self.just_hit = False
        self.current_scale = settings.CURSOR_OPEN_SCALE

        self.image = self.open_image
        self.rect = self.image.get_rect(center=self.position)

    def update(self, target_position: tuple[float, float], is_closed: bool, dt: float) -> None:
        previous_closed = self.closed
        previous_position = self.position.copy()

        self.closed = is_closed
        self.just_hit = self.closed and not previous_closed
        self.target_position.update(target_position)

        self.position = damp_vector(self.position, self.target_position, settings.CURSOR_SMOOTHING, dt)
        if dt > 0:
            self.velocity = (self.position - previous_position) / dt

        speed_boost = min(0.1, self.velocity.length() * 0.00006)
        target_scale = settings.CURSOR_CLOSED_SCALE if self.closed else settings.CURSOR_OPEN_SCALE + speed_boost
        self.current_scale = damp(self.current_scale, target_scale, settings.CURSOR_SCALE_SPEED, dt)

        base_image = self.closed_image if self.closed else self.open_image
        scaled_size = max(42, int(base_image.get_width() * self.current_scale))
        self.image = pygame.transform.smoothscale(base_image, (scaled_size, scaled_size))
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y)))

    def get_hit_rect(self) -> pygame.Rect:
        """Shrink the rect a bit so the hit feels accurate."""
        return self.rect.inflate(-int(self.rect.width * 0.48), -int(self.rect.height * 0.4))

    def draw(self, surface: pygame.Surface) -> None:
        shadow_rect = self.rect.inflate(-int(self.rect.width * 0.32), -int(self.rect.height * 0.7))
        shadow_rect.center = (self.rect.centerx + 6, self.rect.centery + self.rect.height // 2 - 4)
        shadow_surface = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 85), shadow_surface.get_rect())
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(self.image, self.rect)
