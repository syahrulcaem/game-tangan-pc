"""Procedural game sounds so the project works without extra audio assets."""

from __future__ import annotations

import math
from array import array

import pygame


class SoundManager:
    """Create and play small synthesized sound effects."""

    def __init__(self) -> None:
        self.enabled = True
        self.hit_sound: pygame.mixer.Sound | None = None
        self.game_over_sound: pygame.mixer.Sound | None = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.hit_sound = self._make_tone((880, 1320), 110, 0.28)
            self.game_over_sound = self._make_tone((392, 262), 380, 0.24)
        except pygame.error:
            self.enabled = False

    def _make_tone(
        self,
        frequencies: tuple[int, ...],
        duration_ms: int,
        volume: float,
        sample_rate: int = 44100,
    ) -> pygame.mixer.Sound:
        sample_count = int(sample_rate * (duration_ms / 1000.0))
        waveform = array("h")

        for sample_index in range(sample_count):
            time_value = sample_index / sample_rate
            envelope = max(0.0, 1.0 - (sample_index / sample_count)) ** 1.8
            sample_value = 0.0

            for frequency in frequencies:
                sample_value += math.sin(2.0 * math.pi * frequency * time_value)

            sample_value /= max(1, len(frequencies))
            sample_value *= volume * envelope
            sample_value_int = int(sample_value * 32767)

            # Duplicate the value for left and right channels.
            waveform.append(sample_value_int)
            waveform.append(sample_value_int)

        return pygame.mixer.Sound(buffer=waveform.tobytes())

    def play_hit(self) -> None:
        if self.enabled and self.hit_sound:
            self.hit_sound.play()

    def play_game_over(self) -> None:
        if self.enabled and self.game_over_sound:
            self.game_over_sound.play()
