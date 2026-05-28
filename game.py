"""Main game object that coordinates pygame, sprites, UI, and hand tracking."""

from __future__ import annotations

import pygame

import settings
from cursor import Cursor
from effects import HitEffect
from hand_tracking import HandTracker
from rat import Rat
from sounds import SoundManager
from utils import create_font, draw_panel, draw_text, format_seconds, scale_background


class Button:
    """Simple rounded button used on the game-over screen."""

    def __init__(
        self,
        text: str,
        rect: pygame.Rect,
        base_color: tuple[int, int, int],
        hover_color: tuple[int, int, int],
    ) -> None:
        self.text = text
        self.rect = rect
        self.base_color = base_color
        self.hover_color = hover_color

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, hovered: bool) -> None:
        draw_panel(surface, self.rect, self.hover_color if hovered else self.base_color, shadow_offset=8, radius=20)
        draw_text(surface, font, self.text, settings.TEXT_DARK if self.base_color != settings.BUTTON_SECONDARY else settings.TEXT_LIGHT, self.rect.center, center=True)


class Game:
    """Encapsulates the whole Rat Swat Game lifecycle."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.screen = pygame.display.set_mode(settings.SCREEN_SIZE)
        self.clock = pygame.time.Clock()

        self.background = scale_background(settings.BACKGROUND_PATH, settings.SCREEN_SIZE)
        self.play_area = pygame.Rect(
            settings.PLAY_AREA_MARGIN,
            settings.PLAY_AREA_TOP,
            settings.SCREEN_WIDTH - (settings.PLAY_AREA_MARGIN * 2),
            settings.SCREEN_HEIGHT - settings.PLAY_AREA_TOP - settings.PLAY_AREA_MARGIN,
        )

        self.font_small = create_font(22, bold=True)
        self.font_medium = create_font(30, bold=True)
        self.font_large = create_font(60, bold=True)
        self.font_huge = create_font(82, bold=True)

        self.cursor = Cursor()
        self.rat = Rat(self.play_area)
        self.effects = pygame.sprite.Group()
        self.sounds = SoundManager()
        self.tracker = HandTracker(settings.SCREEN_SIZE)

        self.restart_button = Button(
            "Restart",
            pygame.Rect(settings.SCREEN_WIDTH // 2 - 160, settings.SCREEN_HEIGHT // 2 + 78, 150, 68),
            settings.BUTTON_PRIMARY,
            settings.BUTTON_PRIMARY_HOVER,
        )
        self.exit_button = Button(
            "Exit",
            pygame.Rect(settings.SCREEN_WIDTH // 2 + 10, settings.SCREEN_HEIGHT // 2 + 78, 150, 68),
            settings.BUTTON_SECONDARY,
            settings.BUTTON_SECONDARY_HOVER,
        )

        self.running = True
        self.state = "playing"
        self.score = 0
        self.elapsed_time = 0.0
        self.game_over_sound_played = False

        self.tracker.start()

    def restart(self) -> None:
        self.score = 0
        self.elapsed_time = 0.0
        self.state = "playing"
        self.game_over_sound_played = False
        self.effects.empty()
        self.rat.respawn()

    def run(self) -> None:
        try:
            while self.running:
                dt = min(0.05, self.clock.tick(settings.FPS) / 1000.0)
                self._handle_events()
                self._update(dt)
                self._draw()
                pygame.display.flip()
        finally:
            self.shutdown()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif self.state == "game_over" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._activate_game_over_buttons(event.pos)

    def _update(self, dt: float) -> None:
        tracker_state = self.tracker.get_state()
        cursor_pos = tracker_state["cursor_pos"]
        is_closed = bool(tracker_state["is_closed"])

        self.cursor.update(cursor_pos, is_closed, dt)
        self.effects.update(dt)

        if self.state == "playing":
            self.elapsed_time += dt
            self.rat.update(dt)

            if self.cursor.just_hit and self.rat.can_be_hit:
                cursor_hit_rect = self.cursor.get_hit_rect().inflate(10, 10)
                rat_hit_rect = self.rat.get_hit_rect().inflate(-6, -4)
                if cursor_hit_rect.colliderect(rat_hit_rect):
                    self.score += 1
                    self.rat.trigger_hit()
                    self.effects.add(HitEffect(self.rat.rect.center))
                    self.sounds.play_hit()

            if self.elapsed_time >= settings.GAME_DURATION:
                self.state = "game_over"

        elif self.state == "game_over":
            hovered_button = self._button_under_point(self.cursor.rect.center)
            if hovered_button and self.cursor.just_hit:
                self._activate_game_over_buttons(self.cursor.rect.center)

        if self.state == "game_over" and not self.game_over_sound_played:
            self.sounds.play_game_over()
            self.game_over_sound_played = True

    def _draw(self) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_playfield_glow()

        self.rat.draw(self.screen)
        for effect in self.effects.sprites():
            effect.draw(self.screen)

        self._draw_ui()

        if self.state == "game_over":
            self._draw_game_over()

        self.cursor.draw(self.screen)

    def _draw_playfield_glow(self) -> None:
        glow_surface = pygame.Surface(settings.SCREEN_SIZE, pygame.SRCALPHA)
        pygame.draw.rect(
            glow_surface,
            (255, 255, 255, 34),
            self.play_area,
            border_radius=36,
        )
        pygame.draw.rect(
            glow_surface,
            (68, 54, 44, 110),
            self.play_area,
            width=4,
            border_radius=36,
        )
        self.screen.blit(glow_surface, (0, 0))

    def _draw_ui(self) -> None:
        tracker_state = self.tracker.get_state()
        remaining_time = max(0.0, settings.GAME_DURATION - self.elapsed_time)
        fps_text = f"{self.clock.get_fps():4.1f}"
        webcam_status = "Online" if tracker_state["webcam_ok"] else "Offline"
        hand_status = "Detected" if tracker_state["hand_visible"] else "Searching"

        panels = [
            (pygame.Rect(20, 16, 250, 60), settings.PANEL, f"Score: {self.score}", settings.GOLD),
            (pygame.Rect(286, 16, 250, 60), settings.PANEL, f"Time: {format_seconds(remaining_time)}", settings.RED),
            (pygame.Rect(552, 16, 210, 60), settings.PANEL_ALT, f"FPS: {fps_text}", settings.SKY),
            (pygame.Rect(778, 16, 482, 60), settings.PANEL_ALT, f"Webcam: {webcam_status} | Hand: {hand_status}", settings.GREEN),
        ]

        for rect, color, label, accent in panels:
            draw_panel(self.screen, rect, color, shadow_offset=6, radius=18)
            pygame.draw.circle(self.screen, accent, (rect.left + 26, rect.centery), 8)
            draw_text(self.screen, self.font_small, label, settings.TEXT_DARK, (rect.left + 42, rect.top + 18))

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface(settings.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((15, 17, 24, 155))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(settings.SCREEN_WIDTH // 2 - 245, settings.SCREEN_HEIGHT // 2 - 165, 490, 330)
        draw_panel(self.screen, panel_rect, settings.PANEL, shadow_offset=14, radius=30)

        draw_text(self.screen, self.font_huge, "Time Up!", settings.TEXT_DARK, (panel_rect.centerx, panel_rect.top + 72), center=True)
        draw_text(
            self.screen,
            self.font_large,
            f"Final Score: {self.score}",
            settings.RED,
            (panel_rect.centerx, panel_rect.top + 152),
            center=True,
        )
        draw_text(
            self.screen,
            self.font_small,
            "Pinch/close your hand over a button, or click with the mouse.",
            settings.TEXT_DARK,
            (panel_rect.centerx, panel_rect.top + 208),
            center=True,
        )

        hovered_button = self._button_under_point(self.cursor.rect.center)
        self.restart_button.draw(self.screen, self.font_medium, hovered_button is self.restart_button)
        self.exit_button.draw(self.screen, self.font_medium, hovered_button is self.exit_button)

    def _button_under_point(self, point: tuple[int, int]) -> Button | None:
        if self.restart_button.rect.collidepoint(point):
            return self.restart_button
        if self.exit_button.rect.collidepoint(point):
            return self.exit_button
        return None

    def _activate_game_over_buttons(self, point: tuple[int, int]) -> None:
        if self.restart_button.rect.collidepoint(point):
            self.restart()
        elif self.exit_button.rect.collidepoint(point):
            self.running = False

    def shutdown(self) -> None:
        self.tracker.stop()
        pygame.quit()
