"""Camera system supporting Full-Track overview and Follow-Cam modes."""

from __future__ import annotations

import math
from typing import Optional, Tuple

from core.constants import DEFAULT_DT
from core.math2d import Vector2D
from simulation.track import Track


class Camera:
    """
    Manages viewport transformations from world space to screen coordinates.
    Supports:
      1. Full-Track Mode: Fixed framing showing the entire circuit.
      2. Follow Mode: Smooth lerp tracking active car with forward lookahead offset,
         scaled to frame a generous multi-car race area (~6 car scale).
    """

    MODE_FULL_TRACK = "full_track"
    MODE_FOLLOW = "follow"

    def __init__(
        self,
        viewport_width: int,
        viewport_height: int,
        mode: str = MODE_FULL_TRACK,
        follow_zoom: float = 1.9,
    ) -> None:
        self.width = viewport_width
        self.height = viewport_height
        self.mode = mode

        # World coordinates focused at screen center
        self.target_pos: Vector2D = Vector2D(0.0, 0.0)
        self.zoom: float = 1.0

        # Follow camera parameters
        self.follow_zoom: float = follow_zoom
        self.full_track_zoom: float = 1.0
        self.full_track_center: Vector2D = Vector2D(0.0, 0.0)
        self.lookahead_distance: float = 85.0  # World units ahead of car
        self.lerp_speed: float = 6.5           # Positional smoothing rate

    def resize(self, width: int, height: int) -> None:
        """Updates viewport dimensions."""
        self.width = max(1, width)
        self.height = max(1, height)

    def fit_track(self, track: Track, margin: float = 70.0) -> None:
        """
        Calculates bounding box of all track points and sets Full-Track
        center and zoom to frame the circuit comfortably with margins.
        """
        all_pts = track.inner_barrier + track.outer_barrier
        if not all_pts:
            return

        min_x = min(p.x for p in all_pts)
        max_x = max(p.x for p in all_pts)
        min_y = min(p.y for p in all_pts)
        max_y = max(p.y for p in all_pts)

        track_w = max_x - min_x
        track_h = max_y - min_y

        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        self.full_track_center = Vector2D(center_x, center_y)

        avail_w = max(100.0, self.width - margin * 2.0)
        avail_h = max(100.0, self.height - margin * 2.0)

        zoom_x = avail_w / max(1.0, track_w)
        zoom_y = avail_h / max(1.0, track_h)
        self.full_track_zoom = min(zoom_x, zoom_y)

        if self.mode == self.MODE_FULL_TRACK:
            self.zoom = self.full_track_zoom
            self.target_pos = self.full_track_center

    def update(
        self,
        car_pos: Vector2D,
        car_heading: float,
        dt: float = DEFAULT_DT,
    ) -> None:
        """Updates camera position and zoom according to active mode."""
        if self.mode == self.MODE_FULL_TRACK:
            # Snap or smooth to track overview
            self.target_pos = self.target_pos.lerp(self.full_track_center, min(1.0, 8.0 * dt))
            self.zoom += (self.full_track_zoom - self.zoom) * min(1.0, 8.0 * dt)
        elif self.mode == self.MODE_FOLLOW:
            # Lookahead offset along vehicle heading
            fwd = Vector2D.from_angle(car_heading)
            desired_pos = car_pos + fwd * self.lookahead_distance

            # Smoothly interpolate position towards desired target
            self.target_pos = self.target_pos.lerp(desired_pos, min(1.0, self.lerp_speed * dt))
            # Smoothly interpolate zoom
            self.zoom += (self.follow_zoom - self.zoom) * min(1.0, 6.0 * dt)

    def toggle_mode(self) -> str:
        """Toggles between Full-Track and Follow camera modes."""
        if self.mode == self.MODE_FULL_TRACK:
            self.mode = self.MODE_FOLLOW
        else:
            self.mode = self.MODE_FULL_TRACK
        return self.mode

    def world_to_screen(self, world_pos: Vector2D) -> Tuple[int, int]:
        """Converts world coordinate Vector2D to integer screen pixel (sx, sy)."""
        screen_x = (world_pos.x - self.target_pos.x) * self.zoom + (self.width * 0.5)
        screen_y = (world_pos.y - self.target_pos.y) * self.zoom + (self.height * 0.5)
        return int(round(screen_x)), int(round(screen_y))

    def screen_to_world(self, screen_x: float, screen_y: float) -> Vector2D:
        """Converts screen pixel (sx, sy) to world coordinate Vector2D."""
        world_x = (screen_x - (self.width * 0.5)) / max(1e-5, self.zoom) + self.target_pos.x
        world_y = (screen_y - (self.height * 0.5)) / max(1e-5, self.zoom) + self.target_pos.y
        return Vector2D(world_x, world_y)

    def scale_length(self, length: float) -> float:
        """Scales a world length to screen pixels."""
        return length * self.zoom
