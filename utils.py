"""Utility helpers shared across the project."""

from __future__ import annotations

import math
from pathlib import Path

import pygame

import settings


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value so it always stays in a safe range."""
    return max(minimum, min(maximum, value))


def lerp(start: float, end: float, amount: float) -> float:
    """Linear interpolation used for smooth movement and animations."""
    return start + (end - start) * amount


def damp(current: float, target: float, speed: float, dt: float) -> float:
    """Frame-rate independent smoothing."""
    amount = 1.0 - math.exp(-speed * dt)
    return lerp(current, target, amount)


def damp_vector(current: pygame.Vector2, target: pygame.Vector2, speed: float, dt: float) -> pygame.Vector2:
    """Frame-rate independent smoothing for vector values."""
    amount = 1.0 - math.exp(-speed * dt)
    return current.lerp(target, amount)


def load_image(path: Path | str, size: tuple[int, int], alpha: bool = True) -> pygame.Surface:
    """Load and scale an image while preserving transparency when possible."""
    image = pygame.image.load(str(path))
    image = image.convert_alpha() if alpha else image.convert()
    return pygame.transform.smoothscale(image, size)


def scale_background(path: Path | str, size: tuple[int, int]) -> pygame.Surface:
    """Load the background and stretch it to screen size."""
    background = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(background, size)


def create_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Try a few clean fonts and fall back to the default one."""
    preferred_fonts = ["bahnschrift", "segoeui", "arialroundedmtbold", "verdana"]
    font = pygame.font.SysFont(preferred_fonts, size, bold=bold)
    return font or pygame.font.Font(None, size)


def format_seconds(seconds: float) -> str:
    """Turn a raw second value into MM:SS."""
    safe_seconds = max(0, int(math.ceil(seconds)))
    minutes, seconds_left = divmod(safe_seconds, 60)
    return f"{minutes:02d}:{seconds_left:02d}"


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill_color: tuple[int, int, int],
    shadow_offset: int = 6,
    radius: int = 18,
) -> None:
    """Draw a rounded panel with a simple drop shadow."""
    shadow_rect = rect.move(0, shadow_offset)
    pygame.draw.rect(surface, settings.SHADOW, shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    pygame.draw.rect(surface, settings.OUTLINE, rect, width=3, border_radius=radius)


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    position: tuple[int, int],
    *,
    center: bool = False,
) -> pygame.Rect:
    """Render text and return its final rect for layout reuse."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = position
    else:
        text_rect.topleft = position
    surface.blit(text_surface, text_rect)
    return text_rect
