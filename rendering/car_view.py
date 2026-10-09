"""Car visualizer rendering top-down F1 chassis with articulating steerable wheels."""

from __future__ import annotations

import math
from typing import List, Tuple
import pygame

from core.math2d import Vector2D
from rendering.camera import Camera
from simulation.car import Car


class CarRenderer:
    """
    Renders top-down Formula 1 chassis, wings, cockpit, and articulating front wheels.
    Pure observer: reads car state without modifying physics.
    """

    COLOR_TIRE = (18, 18, 20)           # Deep tire rubber
    COLOR_TIRE_RIM = (75, 80, 90)       # Wheel rim accent
    COLOR_WING = (25, 25, 30)           # Carbon fibre wings
    COLOR_COCKPIT = (15, 15, 18)        # Cockpit cavity & halo
    COLOR_HELMET = (255, 210, 40)       # Driver helmet yellow
    COLOR_CRASH_ALERT = (235, 60, 60)   # Impact highlight

    def __init__(self) -> None:
        pygame.font.init()
        self.font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 12, bold=True)

    def draw(self, surface: pygame.Surface, camera: Camera, car: Car) -> None:
        """Draws the car chassis, wings, and 4 wheels at the transformed camera position."""
        pos = car.position
        heading = car.heading
        steer_angle = car.steer_angle
        cfg = car.config

        # Forward and lateral unit vectors
        fwd = Vector2D.from_angle(heading)
        lat = fwd.perpendicular()

        # F1 Chassis dimensions
        length = cfg.length
        width = cfg.width
        half_l = length * 0.5
        half_w = width * 0.5

        # Check if car is inside screen bounds
        screen_pos = camera.world_to_screen(pos)
        margin = int(camera.scale_length(max(length, width) * 2.0))
        if not (-margin <= screen_pos[0] <= camera.width + margin and -margin <= screen_pos[1] <= camera.height + margin):
            return

        body_color = car.team_color if car.is_running() else (120, 120, 125)

        # 1. Wheels (Rear fixed, Front articulate with steer_angle)
        wheel_l = length * 0.28
        wheel_w = width * 0.22
        front_axle = pos + fwd * (half_l * 0.65)
        rear_axle = pos - fwd * (half_l * 0.65)
        track_half_w = half_w * 0.85

        # Rear wheels (fixed to heading)
        self._draw_wheel(surface, camera, rear_axle + lat * track_half_w, heading, wheel_l, wheel_w)
        self._draw_wheel(surface, camera, rear_axle - lat * track_half_w, heading, wheel_l, wheel_w)

        # Front wheels (articulated by steer_angle relative to heading)
        front_wheel_heading = heading + steer_angle
        self._draw_wheel(surface, camera, front_axle + lat * track_half_w, front_wheel_heading, wheel_l, wheel_w)
        self._draw_wheel(surface, camera, front_axle - lat * track_half_w, front_wheel_heading, wheel_l, wheel_w)

        # 2. Rear Wing
        rw_pos = pos - fwd * (half_l * 0.88)
        self._draw_oriented_box(surface, camera, rw_pos, heading, length * 0.16, width * 0.95, self.COLOR_WING)

        # 3. Front Wing
        fw_pos = pos + fwd * (half_l * 0.92)
        self._draw_oriented_box(surface, camera, fw_pos, heading, length * 0.15, width * 0.95, self.COLOR_WING)

        # 4. Main Body / Sidepods & Tapered Nose
        nose_tip = pos + fwd * half_l
        front_body = pos + fwd * (half_l * 0.4)
        mid_body = pos
        rear_body = pos - fwd * (half_l * 0.75)

        body_poly = [
            camera.world_to_screen(nose_tip),
            camera.world_to_screen(front_body + lat * (half_w * 0.4)),
            camera.world_to_screen(mid_body + lat * (half_w * 0.8)),
            camera.world_to_screen(rear_body + lat * (half_w * 0.65)),
            camera.world_to_screen(rear_body - lat * (half_w * 0.65)),
            camera.world_to_screen(mid_body - lat * (half_w * 0.8)),
            camera.world_to_screen(front_body - lat * (half_w * 0.4)),
        ]
        pygame.draw.polygon(surface, body_color, body_poly)
        pygame.draw.polygon(surface, (15, 15, 18), body_poly, max(1, int(round(camera.scale_length(1.2)))))

        # 5. Cockpit & Driver Helmet
        cockpit_pos = camera.world_to_screen(pos + fwd * (half_l * 0.05))
        cockpit_r = max(2, int(round(camera.scale_length(half_w * 0.35))))
        pygame.draw.circle(surface, self.COLOR_COCKPIT, cockpit_pos, cockpit_r)
        helmet_r = max(1, int(round(camera.scale_length(half_w * 0.2))))
        pygame.draw.circle(surface, self.COLOR_HELMET, cockpit_pos, helmet_r)

        # 6. Status Indicator & Driver Code Label
        if not car.is_running():
            # Crash badge / halo
            pygame.draw.circle(surface, self.COLOR_CRASH_ALERT, screen_pos, max(4, int(camera.scale_length(half_l * 1.2))), 2)

        # Small driver code tag above car
        tag_pos = (screen_pos[0], screen_pos[1] - int(camera.scale_length(half_l * 1.4)))
        tag_surf = self.font.render(car.driver_code, True, (230, 230, 240))
        tag_rect = tag_surf.get_rect(center=tag_pos)
        # Background pill
        bg_rect = tag_rect.inflate(6, 2)
        pygame.draw.rect(surface, (18, 20, 26, 200), bg_rect, border_radius=3)
        surface.blit(tag_surf, tag_rect)

    def _draw_wheel(
        self,
        surface: pygame.Surface,
        camera: Camera,
        pos: Vector2D,
        heading: float,
        length: float,
        width: float,
    ) -> None:
        """Draws an individual articulated tire rotated by heading."""
        self._draw_oriented_box(surface, camera, pos, heading, length, width, self.COLOR_TIRE)
        # Inner rim line
        fwd = Vector2D.from_angle(heading) * (length * 0.25)
        p1 = camera.world_to_screen(pos - fwd)
        p2 = camera.world_to_screen(pos + fwd)
        pygame.draw.line(surface, self.COLOR_TIRE_RIM, p1, p2, max(1, int(round(camera.scale_length(1.0)))))

    def _draw_oriented_box(
        self,
        surface: pygame.Surface,
        camera: Camera,
        pos: Vector2D,
        heading: float,
        length: float,
        width: float,
        color: Tuple[int, int, int],
    ) -> None:
        """Draws a rectangular element rotated by heading."""
        fwd = Vector2D.from_angle(heading)
        lat = fwd.perpendicular()
        hl = length * 0.5
        hw = width * 0.5

        c1 = camera.world_to_screen(pos + fwd * hl + lat * hw)
        c2 = camera.world_to_screen(pos + fwd * hl - lat * hw)
        c3 = camera.world_to_screen(pos - fwd * hl - lat * hw)
        c4 = camera.world_to_screen(pos - fwd * hl + lat * hw)
        pygame.draw.polygon(surface, color, [c1, c2, c3, c4])
