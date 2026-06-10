"""Rat enemy sprite that moves around the screen randomly."""

from __future__ import annotations

import math
import random

import pygame

import settings
from utils import clamp, load_image


class Rat(pygame.sprite.Sprite):
    """Single enemy rat with random movement and a short hit animation."""

    def __init__(self, play_area: pygame.Rect, speed_multiplier: float = 1.0) -> None:
        super().__init__()
        self.play_area = play_area
        self.speed_multiplier = float(speed_multiplier)
        self.original_image = load_image(settings.RAT_IMAGE_PATH, (settings.RAT_SIZE, settings.RAT_SIZE))
        self.position = pygame.Vector2()
        self.velocity = pygame.Vector2()
        self.direction_timer = 0.0
        self.idle_phase = random.uniform(0.0, math.tau)
        self.hit_timer = 0.0
        self.scale = 1.0
        self.rotation = 0.0
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.respawn()

    @property
    def can_be_hit(self) -> bool:
        return self.hit_timer <= 0.0

    def respawn(self) -> None:
        margin = 100
        self.position.xy = (
            random.randint(self.play_area.left + margin, self.play_area.right - margin),
            random.randint(self.play_area.top + margin, self.play_area.bottom - margin),
        )
        self.velocity = self._random_velocity()
        self.direction_timer = random.uniform(settings.RAT_DIRECTION_CHANGE_MIN, settings.RAT_DIRECTION_CHANGE_MAX)
        self.idle_phase = random.uniform(0.0, math.tau)
        self.hit_timer = 0.0
        self.scale = 1.0
        self.rotation = 0.0
        self._refresh_image()

    def _random_velocity(self) -> pygame.Vector2:
        direction = pygame.Vector2(random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0))
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        speed = random.uniform(settings.RAT_SPEED_MIN, settings.RAT_SPEED_MAX) * getattr(self, "speed_multiplier", 1.0)
        return direction.normalize() * speed

    def trigger_hit(self) -> None:
        if self.can_be_hit:
            self.hit_timer = settings.RAT_HIT_DURATION

    def update(self, dt: float) -> None:
        self.idle_phase += dt * settings.RAT_IDLE_BOB_SPEED

        if self.hit_timer > 0.0:
            self.hit_timer = max(0.0, self.hit_timer - dt)
            progress = 1.0 - (self.hit_timer / settings.RAT_HIT_DURATION)
            self.scale = 1.0 + math.sin(progress * math.pi) * 0.45
            self.rotation = math.sin(progress * math.pi * 3.0) * 12.0

            if self.hit_timer <= 0.0:
                self.respawn()
                return
        else:
            self.direction_timer -= dt
            if self.direction_timer <= 0.0:
                new_velocity = self._random_velocity()
                self.velocity = self.velocity.lerp(new_velocity, 0.35)
                self.direction_timer = random.uniform(
                    settings.RAT_DIRECTION_CHANGE_MIN,
                    settings.RAT_DIRECTION_CHANGE_MAX,
                )

            self.position += self.velocity * dt
            self._bounce_inside_area()
            self.scale = 1.0 + math.sin(self.idle_phase) * 0.04
            self.rotation = math.sin(self.idle_phase * 0.65) * 4.0

        self._refresh_image()

    def _bounce_inside_area(self) -> None:
        half_width = self.rect.width / 2
        half_height = self.rect.height / 2

        if self.position.x - half_width <= self.play_area.left:
            self.position.x = self.play_area.left + half_width
            self.velocity.x *= -1
        elif self.position.x + half_width >= self.play_area.right:
            self.position.x = self.play_area.right - half_width
            self.velocity.x *= -1

        if self.position.y - half_height <= self.play_area.top:
            self.position.y = self.play_area.top + half_height
            self.velocity.y *= -1
        elif self.position.y + half_height >= self.play_area.bottom:
            self.position.y = self.play_area.bottom - half_height
            self.velocity.y *= -1

        self.position.x = clamp(self.position.x, self.play_area.left + half_width, self.play_area.right - half_width)
        self.position.y = clamp(self.position.y, self.play_area.top + half_height, self.play_area.bottom - half_height)

    def _refresh_image(self) -> None:
        bob_offset = math.sin(self.idle_phase * 1.25) * settings.RAT_IDLE_BOB_AMOUNT
        self.image = pygame.transform.rotozoom(self.original_image, self.rotation, self.scale)
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y + bob_offset)))

    def get_hit_rect(self) -> pygame.Rect:
        """Tighten the rat hitbox to match the body better than the transparent image bounds."""
        return self.rect.inflate(-int(self.rect.width * 0.3), -int(self.rect.height * 0.26))

    def draw(self, surface: pygame.Surface) -> None:
        shadow_rect = self.rect.inflate(-int(self.rect.width * 0.34), -int(self.rect.height * 0.76))
        shadow_rect.center = (self.rect.centerx, self.rect.bottom - 10)
        shadow_surface = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 100), shadow_surface.get_rect())
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(self.image, self.rect)
