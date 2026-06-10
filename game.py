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
import cv2
import numpy as np


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
        # manage multiple rats
        self.rats = pygame.sprite.Group()
        self.total_spawned = 0
        self.total_killed = 0
        self.spawn_timer = 0.0
        self.won = False
        # level/menu
        self.level = 1
        self.level_buttons: list[Button] = []
        self.start_button: Button | None = None
        self.level_total = settings.LEVELS[self.level]["total_rats"]
        self.current_speed_multiplier = settings.LEVELS[self.level]["speed_multiplier"]
        self.spawn_interval = settings.LEVELS[self.level]["spawn_interval"]
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
        self.state = "menu"
        self.score = 0
        self.elapsed_time = 0.0
        self.game_over_sound_played = False

        self.tracker.start()
        self._create_menu()

    def restart(self) -> None:
        self.score = 0
        self.elapsed_time = 0.0
        self.state = "playing"
        self.game_over_sound_played = False
        self.effects.empty()
        self.rats.empty()
        self.total_spawned = 0
        self.total_killed = 0
        self.spawn_timer = 0.0
        self.won = False
        self._spawn_rat()

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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "game_over":
                    self._activate_game_over_buttons(event.pos)
                elif self.state == "menu":
                    self._activate_menu_button(event.pos)

    def _update(self, dt: float) -> None:
        tracker_state = self.tracker.get_state()
        cursor_pos = tracker_state["cursor_pos"]
        is_closed = bool(tracker_state["is_closed"])

        self.cursor.update(cursor_pos, is_closed, dt)
        self.effects.update(dt)

        if self.state == "playing":
            self.elapsed_time += dt

            # update all rats
            self.rats.update(dt)

            # spawn new rats over time until we reach the configured total for the selected level
            if self.total_spawned < self.level_total:
                self.spawn_timer += dt
                if self.spawn_timer >= self.spawn_interval:
                    self.spawn_timer = 0.0
                    self._spawn_rat()

            # process hits against any rat
            if self.cursor.just_hit:
                cursor_hit_rect = self.cursor.get_hit_rect().inflate(10, 10)
                for rat in list(self.rats.sprites()):
                    if not rat.can_be_hit:
                        continue
                    rat_hit_rect = rat.get_hit_rect().inflate(-6, -4)
                    if cursor_hit_rect.colliderect(rat_hit_rect):
                        self.score += 1
                        self.rats.remove(rat)
                        self.total_killed += 1
                        self.effects.add(HitEffect(rat.rect.center))
                        self.sounds.play_hit()

            # time-up game over
            if self.elapsed_time >= settings.GAME_DURATION:
                self.state = "game_over"

            # win when enough rats have been eliminated
            if self.total_killed >= self.level_total:
                # advance to next level automatically if available
                if self.level < 3:
                    self.level += 1
                    # apply new level settings
                    self.level_total = settings.LEVELS[self.level]["total_rats"]
                    self.current_speed_multiplier = settings.LEVELS[self.level]["speed_multiplier"]
                    self.spawn_interval = settings.LEVELS[self.level]["spawn_interval"]
                    # reset counters and continue playing at next level
                    self.total_spawned = 0
                    self.total_killed = 0
                    self.spawn_timer = 0.0
                    self.score = 0
                    self.elapsed_time = 0.0
                    self.rats.empty()
                    self._create_menu()
                    self._spawn_rat()
                else:
                    self.state = "game_over"
                    self.won = True

        elif self.state == "game_over":
            hovered_button = self._button_under_point(self.cursor.rect.center)
            if hovered_button and self.cursor.just_hit:
                self._activate_game_over_buttons(self.cursor.rect.center)
        elif self.state == "menu":
            hovered_button = self._button_under_point(self.cursor.rect.center)
            if hovered_button and self.cursor.just_hit:
                self._activate_menu_button(self.cursor.rect.center)

        if self.state == "game_over" and not self.game_over_sound_played:
            self.sounds.play_game_over()
            self.game_over_sound_played = True

    def _draw(self) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_playfield_glow()

        # draw camera preview (small) in corner if available
        try:
            frame = self.tracker.get_latest_preview()
            if frame is not None:
                # convert BGR->RGB for pygame
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                surf = pygame.image.frombuffer(rgb.tobytes(), (w, h), "RGB")
                target_w, target_h = settings.CAMERA_PREVIEW_SIZE
                preview_surf = pygame.transform.smoothscale(surf, (target_w, target_h))
                margin = settings.CAMERA_PREVIEW_MARGIN
                corner = settings.CAMERA_PREVIEW_CORNER
                if corner == "topleft":
                    pos = (margin, margin)
                elif corner == "bottomleft":
                    pos = (margin, settings.SCREEN_HEIGHT - target_h - margin)
                else:
                    pos = (settings.SCREEN_WIDTH - target_w - margin, margin)
                # draw rounded panel behind preview
                panel_rect = pygame.Rect(pos[0] - 6, pos[1] - 6, target_w + 12, target_h + 12)
                draw_panel(self.screen, panel_rect, settings.PANEL_ALT, shadow_offset=6, radius=12)
                self.screen.blit(preview_surf, pos)
        except Exception:
            # ignore preview rendering errors
            pass

        for rat in self.rats.sprites():
            rat.draw(self.screen)
        for effect in self.effects.sprites():
            effect.draw(self.screen)

        self._draw_ui()

        if self.state == "game_over":
            self._draw_game_over()
        elif self.state == "menu":
            self._draw_menu()

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

        title_text = "You Win!" if getattr(self, "won", False) else "Time Up!"
        draw_text(self.screen, self.font_huge, title_text, settings.TEXT_DARK, (panel_rect.centerx, panel_rect.top + 72), center=True)
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
            "Pinch/close your hand over a button",
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

    def _create_menu(self) -> None:
        # create level select buttons and start button
        btn_w = 160
        btn_h = 64
        spacing = 24
        total_width = btn_w * 3 + spacing * 2
        left = settings.SCREEN_WIDTH // 2 - total_width // 2
        y = settings.SCREEN_HEIGHT // 2 - 60

        self.level_buttons = []
        for i in range(1, 4):
            rect = pygame.Rect(left + (i - 1) * (btn_w + spacing), y, btn_w, btn_h)
            btn = Button(f"Level {i}", rect, settings.BUTTON_PRIMARY if i == self.level else settings.BUTTON_SECONDARY, settings.BUTTON_PRIMARY_HOVER if i == self.level else settings.BUTTON_SECONDARY_HOVER)
            self.level_buttons.append(btn)

        self.start_button = Button("Start", pygame.Rect(settings.SCREEN_WIDTH // 2 - 80, y + btn_h + 28, 160, 64), settings.BUTTON_PRIMARY, settings.BUTTON_PRIMARY_HOVER)

    def _draw_menu(self) -> None:
        panel_rect = pygame.Rect(settings.SCREEN_WIDTH // 2 - 280, settings.SCREEN_HEIGHT // 2 - 180, 560, 360)
        draw_panel(self.screen, panel_rect, settings.PANEL, shadow_offset=14, radius=30)
        draw_text(self.screen, self.font_huge, "Select Level", settings.TEXT_DARK, (panel_rect.centerx, panel_rect.top + 64), center=True)

        for btn in self.level_buttons:
            hovered = btn.rect.collidepoint(self.cursor.rect.center)
            btn.draw(self.screen, self.font_medium, hovered)

        hovered = self.start_button.rect.collidepoint(self.cursor.rect.center)
        self.start_button.draw(self.screen, self.font_medium, hovered)

    def _button_under_point(self, point: tuple[int, int]) -> Button | None:
        # override to include menu buttons when in game_over/menu
        if self.state == "menu":
            for btn in self.level_buttons:
                if btn.rect.collidepoint(point):
                    return btn
            if self.start_button and self.start_button.rect.collidepoint(point):
                return self.start_button

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

    def _activate_menu_button(self, point: tuple[int, int]) -> None:
        # handle level selection and start
        for idx, btn in enumerate(self.level_buttons, start=1):
            if btn.rect.collidepoint(point):
                self.level = idx
                # apply level settings
                self.level_total = settings.LEVELS[self.level]["total_rats"]
                self.current_speed_multiplier = settings.LEVELS[self.level]["speed_multiplier"]
                self.spawn_interval = settings.LEVELS[self.level]["spawn_interval"]
                # refresh menu look
                self._create_menu()
                return

        if self.start_button and self.start_button.rect.collidepoint(point):
            # begin the game at selected level
            self.total_spawned = 0
            self.total_killed = 0
            self.spawn_timer = 0.0
            self.score = 0
            self.elapsed_time = 0.0
            self.won = False
            self.state = "playing"
            self.rats.empty()
            self._spawn_rat()

    def _spawn_rat(self) -> None:
        """Create and add a new Rat to the playfield if under the total limit."""
        if self.total_spawned >= self.level_total:
            return
        rat = Rat(self.play_area, speed_multiplier=self.current_speed_multiplier)
        self.rats.add(rat)
        self.total_spawned += 1

    def shutdown(self) -> None:
        self.tracker.stop()
        pygame.quit()
