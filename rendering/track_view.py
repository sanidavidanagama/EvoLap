"""Track visualizer rendering asphalt tarmac, kerbs, barriers, and checkered line."""

from __future__ import annotations

import math
from typing import List, Tuple
import pygame

from core.math2d import LineSegment, Vector2D
from rendering.camera import Camera
from simulation.track import Track


class TrackRenderer:
    """
    Renders circuit surfaces, rumble strips, steel barriers, and checkered line.
    Purely an observer: reads track state without mutating anything.
    """

    COLOR_ASPHALT = (42, 45, 54)         # Sleek dark tarmac
    COLOR_ASPHALT_EDGE = (32, 35, 42)    # Subtle edge shading
    COLOR_KERB_RED = (220, 45, 50)       # Formula 1 vibrant kerb red
    COLOR_KERB_WHITE = (245, 245, 250)   # Kerb bright white
    COLOR_BARRIER = (110, 122, 138)      # Steel barrier wall
    COLOR_BARRIER_OUTLINE = (18, 20, 26) # Dark shadow/outline
    COLOR_CHECKER_WHITE = (255, 255, 255)
    COLOR_CHECKER_BLACK = (20, 20, 25)

    def draw(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws all track geometry components into the given surface."""
        # 1. Asphalt Surface Ribbon
        self._draw_asphalt(surface, camera, track)

        # 2. Kerbs (Rumble Strips) along barriers
        self._draw_kerbs(surface, camera, track)

        # 3. Outer & Inner Barriers
        self._draw_barriers(surface, camera, track)

        # 4. Checkered Start / Finish Line
        self._draw_finish_line(surface, camera, track)

    def _draw_asphalt(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws asphalt quadrilaterals between inner and outer barrier loops."""
        inner = track.inner_barrier
        outer = track.outer_barrier
        n_inner = len(inner)
        n_outer = len(outer)

        if n_inner < 3 or n_outer < 3:
            return

        # If counts match (standard for track builders like Apex Valley and Monaco)
        if n_inner == n_outer:
            for i in range(n_inner):
                next_i = (i + 1) % n_inner
                p1 = camera.world_to_screen(inner[i])
                p2 = camera.world_to_screen(inner[next_i])
                p3 = camera.world_to_screen(outer[next_i])
                p4 = camera.world_to_screen(outer[i])

                # Viewport culling: check if at least one point is reasonably close to screen
                margin = 150
                pts = [p1, p2, p3, p4]
                if not any(-margin <= p[0] <= camera.width + margin and -margin <= p[1] <= camera.height + margin for p in pts):
                    continue

                pygame.draw.polygon(surface, self.COLOR_ASPHALT, pts)
        else:
            # Resampled or general polygon loops
            inner_screen = [camera.world_to_screen(p) for p in inner]
            outer_screen = [camera.world_to_screen(p) for p in outer]
            if len(outer_screen) >= 3:
                pygame.draw.polygon(surface, self.COLOR_ASPHALT, outer_screen)
            if len(inner_screen) >= 3:
                pygame.draw.polygon(surface, (18, 20, 24), inner_screen)

    def _draw_kerbs(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws alternating red and white rumble strips along barrier boundaries."""
        kerb_width = max(2, int(round(camera.scale_length(3.0))))

        for loop in (track.inner_barrier, track.outer_barrier):
            n = len(loop)
            for i in range(n):
                p1 = camera.world_to_screen(loop[i])
                p2 = camera.world_to_screen(loop[(i + 1) % n])

                # Alternate color every segment
                color = self.COLOR_KERB_RED if (i % 2 == 0) else self.COLOR_KERB_WHITE
                pygame.draw.line(surface, color, p1, p2, kerb_width)

    def _draw_barriers(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws steel / armco barriers."""
        barrier_thickness = max(2, int(round(camera.scale_length(2.5))))
        outline_thickness = barrier_thickness + 2

        for seg in track.barriers:
            p1 = camera.world_to_screen(seg.start)
            p2 = camera.world_to_screen(seg.end)

            # Shadow outline
            pygame.draw.line(surface, self.COLOR_BARRIER_OUTLINE, p1, p2, outline_thickness)
            # Core barrier line
            pygame.draw.line(surface, self.COLOR_BARRIER, p1, p2, barrier_thickness)

    def _draw_finish_line(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Renders high-visibility checkered start/finish line."""
        fl = track.finish_line
        p1 = camera.world_to_screen(fl.start)
        p2 = camera.world_to_screen(fl.end)

        line_len = fl.length()
        if line_len < 1.0:
            return

        # Number of checker blocks across track width
        num_blocks = 14
        v_step = fl.vector() / num_blocks
        fwd_norm = fl.direction().perpendicular() * 3.5  # World width of line band

        for i in range(num_blocks):
            b_start = fl.start + v_step * i
            b_end = b_start + v_step

            # 2 alternating rows
            for row in range(2):
                offset_sign = (row - 0.5) * 2.0
                row_offset = fwd_norm * (offset_sign * 0.5)

                c1 = camera.world_to_screen(b_start + row_offset)
                c2 = camera.world_to_screen(b_end + row_offset)
                c3 = camera.world_to_screen(b_end)
                c4 = camera.world_to_screen(b_start)

                is_white = (i + row) % 2 == 0
                color = self.COLOR_CHECKER_WHITE if is_white else self.COLOR_CHECKER_BLACK
                pygame.draw.polygon(surface, color, [c1, c2, c3, c4])
