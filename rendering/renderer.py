"""Master rendering engine managing Pygame display, camera, track, car, and HUD."""

from __future__ import annotations

import math
from typing import Optional, Tuple
import pygame

from core.constants import MPS_TO_KMH
from rendering.camera import Camera
from rendering.car_view import CarRenderer
from rendering.track_view import TrackRenderer
from simulation.world import World


class Renderer:
    """
    Observer visualizer that reads Simulation World state and renders frames to Pygame.
    Strictly zero physical state mutations.
    """

    COLOR_BG = (42, 85, 42)              # Natural racing grass terrain
    COLOR_HUD_TEXT = (235, 238, 245)
    COLOR_HUD_ACCENT = (235, 30, 40)     # F1 Red accent
    COLOR_HUD_BG = (22, 26, 35, 225)

    def __init__(
        self,
        fullscreen: bool = True,
        window_size: Tuple[int, int] = (1600, 900),
    ) -> None:
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("EvoLap — Formula 1 Simulation & AI Driving Laboratory")

        self.fullscreen = fullscreen
        self.window_size = window_size

        if self.fullscreen:
            # Query desktop resolution for true borderless fullscreen
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.FULLSCREEN | pygame.DOUBLEBUF,
            )
        else:
            self.width, self.height = window_size
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.RESIZABLE | pygame.DOUBLEBUF,
            )

        # Rendering sub-components
        self.camera = Camera(self.width, self.height, mode=Camera.MODE_FOLLOW)
        self.track_renderer = TrackRenderer()
        self.car_renderer = CarRenderer()

        # Fonts
        self.font_speed = pygame.font.SysFont("Impact, Segoe UI, Arial", 38)
        self.font_label = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
        self.font_data = pygame.font.SysFont("Consolas, Courier New, monospace", 16, bold=True)
        self.font_hint = pygame.font.SysFont("Segoe UI, Arial", 12)

        self._track_fitted = False

    def toggle_fullscreen(self) -> None:
        """Toggles between fullscreen and resizable window."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.FULLSCREEN | pygame.DOUBLEBUF,
            )
        else:
            self.width, self.height = self.window_size
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.RESIZABLE | pygame.DOUBLEBUF,
            )
        self.camera.resize(self.width, self.height)
        self._track_fitted = False

    def handle_resize(self, width: int, height: int) -> None:
        """Handles window resize events."""
        self.width = max(100, width)
        self.height = max(100, height)
        self.camera.resize(self.width, self.height)
        self._track_fitted = False

    def render(self, world: World, dt: float) -> None:
        """
        Renders a full frame from the given World snapshot.
        Observer pattern: does not mutate physics or car states.
        """
        # Ensure camera fits track initially or upon resize
        if not self._track_fitted:
            self.camera.fit_track(world.track)
            self._track_fitted = True

        # Update camera position according to primary car
        primary_car = world.player_car
        if primary_car is not None:
            self.camera.update(primary_car.position, primary_car.heading, dt)

        # 1. Clear background
        self.screen.fill(self.COLOR_BG)

        # 2. Render Track
        self.track_renderer.draw(self.screen, self.camera, world.track)

        # 3. Render Cars
        for car in world.cars:
            self.car_renderer.draw(self.screen, self.camera, car)

        # 4. Render Telemetry & HUD
        self._draw_hud(world)

        # 5. Flip display buffer
        pygame.display.flip()

    def _draw_hud(self, world: World) -> None:
        """Renders sleek top telemetry bar and controls hint."""
        primary_car = world.player_car
        if primary_car is None:
            return

        # --- Top-Left: Digital Speedometer & Lap Telemetry ---
        hud_w = 260
        hud_h = 105
        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        hud_surf.fill(self.COLOR_HUD_BG)
        pygame.draw.rect(hud_surf, (50, 56, 70), (0, 0, hud_w, hud_h), width=1, border_radius=6)

        # Speed calculation (px/s to km/h scale calibrated with top speed config)
        scale_ppm = max(0.1, world.track.config.scale_pixels_per_meter)
        raw_kmh = (primary_car.speed / scale_ppm) * 3.6
        speed_kmh = min(primary_car.config.top_speed_kmh, max(0.0, raw_kmh))
        speed_text = f"{int(round(speed_kmh))}"
        speed_surf = self.font_speed.render(speed_text, True, (255, 255, 255))
        hud_surf.blit(speed_surf, (16, 12))

        unit_surf = self.font_label.render("KM/H", True, (150, 155, 170))
        hud_surf.blit(unit_surf, (speed_surf.get_width() + 22, 28))

        # Status badge
        is_running = primary_car.is_running()
        status_str = "RUNNING" if is_running else "CRASHED (OUT)"
        status_color = (60, 220, 100) if is_running else (240, 50, 50)
        status_surf = self.font_label.render(status_str, True, status_color)
        hud_surf.blit(status_surf, (16, 60))

        # Lap & Time Info
        lap_str = f"LAP {primary_car.current_lap}  {primary_car.lap_time:.2f}s"
        lap_surf = self.font_data.render(lap_str, True, (210, 215, 230))
        hud_surf.blit(lap_surf, (16, 78))

        self.screen.blit(hud_surf, (20, 20))

        # --- Top-Right: Camera Mode & Track Name ---
        cam_w = 280
        cam_h = 75
        cam_surf = pygame.Surface((cam_w, cam_h), pygame.SRCALPHA)
        cam_surf.fill(self.COLOR_HUD_BG)
        pygame.draw.rect(cam_surf, (50, 56, 70), (0, 0, cam_w, cam_h), width=1, border_radius=6)

        trk_name_surf = self.font_label.render(world.track.name.upper(), True, self.COLOR_HUD_ACCENT)
        cam_surf.blit(trk_name_surf, (16, 12))

        mode_name = "FOLLOW CAM (~6-CAR VIEW)" if self.camera.mode == Camera.MODE_FOLLOW else "FULL CIRCUIT OVERVIEW"
        mode_surf = self.font_data.render(mode_name, True, (230, 235, 245))
        cam_surf.blit(mode_surf, (16, 32))

        hint_toggle = self.font_hint.render("Press 'C' to toggle camera", True, (140, 145, 160))
        cam_surf.blit(hint_toggle, (16, 52))

        self.screen.blit(cam_surf, (self.width - cam_w - 20, 20))

        # --- Bottom-Center: Controls Hint ---
        hint_str = "W/Up: Gas | SPACE / S: Brake | A/D: Steer | C: Camera | R: Reset Car | F11: Fullscreen | ESC: Exit"
        hint_surf = self.font_hint.render(hint_str, True, (160, 165, 180))
        hint_bg = hint_surf.get_rect(center=(self.width // 2, self.height - 24))
        # Draw pill
        pill_rect = hint_bg.inflate(20, 8)
        pill_surf = pygame.Surface((pill_rect.width, pill_rect.height), pygame.SRCALPHA)
        pill_surf.fill((18, 22, 30, 200))
        pygame.draw.rect(pill_surf, (45, 50, 65), (0, 0, pill_rect.width, pill_rect.height), width=1, border_radius=12)
        self.screen.blit(pill_surf, pill_rect)
        self.screen.blit(hint_surf, hint_bg)
