"""Track visualizer rendering grass terrain, tarmac, kerbs, F1 barriers, and checkered line."""

from __future__ import annotations

import math
from typing import List, Tuple
import pygame

from core.math2d import LineSegment, Vector2D
from rendering.camera import Camera
from simulation.track import Track


class TrackRenderer:
    """
    Renders circuit surfaces with rich F1 aesthetics:
    - Lush grass terrain with subtle mowing patterns
    - Dark racing tarmac with dashed centerline
    - High-visibility FIA red/white rumble kerbs
    - 3D-styled metallic Armco / TecPro barriers
    - Two-row checkered start/finish line
    """

    COLOR_GRASS_BASE = (42, 85, 42)      # Deep racing grass green
    COLOR_GRASS_STRIPE = (46, 92, 46)    # Alternating mower stripe
    COLOR_RUNOFF_GRAVEL = (185, 160, 110) # Sand/gravel runoff zone
    COLOR_ASPHALT = (34, 37, 44)         # Clean dark charcoal racing tarmac
    COLOR_ASPHALT_LINE = (75, 80, 92)    # Subtle dashed racing centerline
    COLOR_KERB_RED = (225, 35, 40)       # FIA vibrant kerb red
    COLOR_KERB_WHITE = (245, 245, 250)   # Kerb bright white
    COLOR_BARRIER_SHADOW = (15, 20, 18)  # Barrier drop shadow
    COLOR_BARRIER_BASE = (125, 135, 150) # Steel barrier core
    COLOR_BARRIER_RAIL = (195, 205, 220) # Metallic top rail highlight
    COLOR_BARRIER_POST = (70, 75, 85)    # Vertical support post
    COLOR_CHECKER_WHITE = (255, 255, 255)
    COLOR_CHECKER_BLACK = (20, 20, 25)

    def draw(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws all track geometry components into the given surface."""
        # 1. Grass Terrain Background
        self._draw_terrain(surface, camera)

        # 2. Asphalt Surface Ribbon
        self._draw_asphalt(surface, camera, track)

        # 3. Dashed Centerline Guide
        self._draw_centerline(surface, camera, track)

        # 4. Kerbs (Rumble Strips) along barriers
        self._draw_kerbs(surface, camera, track)

        # 5. Outer & Inner F1-Styled Steel Barriers
        self._draw_barriers(surface, camera, track)

        # 6. Checkered Start / Finish Line
        self._draw_finish_line(surface, camera, track)

    def _draw_terrain(self, surface: pygame.Surface, camera: Camera) -> None:
        """Draws natural green lawn with subtle parallel mower striping."""
        surface.fill(self.COLOR_GRASS_BASE)

        # Mower striping aligned with world space
        stripe_w = int(camera.scale_length(120.0))
        if stripe_w > 10:
            start_x = int(round(-camera.target_pos.x * camera.zoom + camera.width * 0.5)) % (stripe_w * 2) - stripe_w * 2
            for x in range(start_x, camera.width + stripe_w * 2, stripe_w * 2):
                pygame.draw.rect(surface, self.COLOR_GRASS_STRIPE, (x, 0, stripe_w, camera.height))

    def _draw_asphalt(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws asphalt quadrilaterals between inner and outer barrier loops."""
        inner = track.inner_barrier
        outer = track.outer_barrier
        n_inner = len(inner)
        n_outer = len(outer)

        if n_inner < 3 or n_outer < 3:
            return

        if n_inner == n_outer:
            margin = 150
            for i in range(n_inner):
                next_i = (i + 1) % n_inner
                p1 = camera.world_to_screen(inner[i])
                p2 = camera.world_to_screen(inner[next_i])
                p3 = camera.world_to_screen(outer[next_i])
                p4 = camera.world_to_screen(outer[i])

                # Viewport culling
                pts = [p1, p2, p3, p4]
                if not any(-margin <= p[0] <= camera.width + margin and -margin <= p[1] <= camera.height + margin for p in pts):
                    continue

                pygame.draw.polygon(surface, self.COLOR_ASPHALT, pts)
        else:
            inner_screen = [camera.world_to_screen(p) for p in inner]
            outer_screen = [camera.world_to_screen(p) for p in outer]
            if len(outer_screen) >= 3:
                pygame.draw.polygon(surface, self.COLOR_ASPHALT, outer_screen)
            if len(inner_screen) >= 3:
                pygame.draw.polygon(surface, self.COLOR_GRASS_BASE, inner_screen)

    def _draw_centerline(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws a dashed centerline guide along the middle of the track."""
        inner = track.inner_barrier
        outer = track.outer_barrier
        n = min(len(inner), len(outer))
        if n < 3:
            return

        dash_width = max(1, int(round(camera.scale_length(1.2))))
        for i in range(0, n, 2):  # Every second segment forms a dash
            next_i = (i + 1) % n
            mid1 = (inner[i] + outer[i]) * 0.5
            mid2 = (inner[next_i] + outer[next_i]) * 0.5

            p1 = camera.world_to_screen(mid1)
            p2 = camera.world_to_screen(mid2)
            pygame.draw.line(surface, self.COLOR_ASPHALT_LINE, p1, p2, dash_width)

    def _draw_kerbs(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws alternating red and white rumble strips along barrier boundaries."""
        kerb_width = max(3, int(round(camera.scale_length(4.5))))

        for loop in (track.inner_barrier, track.outer_barrier):
            n = len(loop)
            for i in range(n):
                p1 = camera.world_to_screen(loop[i])
                p2 = camera.world_to_screen(loop[(i + 1) % n])

                # Alternate color every 2-3 segments for realistic kerb teeth length
                color = self.COLOR_KERB_RED if ((i // 2) % 2 == 0) else self.COLOR_KERB_WHITE
                pygame.draw.line(surface, color, p1, p2, kerb_width)

    def _draw_barriers(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Draws multi-layered 3D Armco / steel barriers with shadow, core, and rail highlight."""
        shadow_thick = max(4, int(round(camera.scale_length(4.0))))
        core_thick = max(3, int(round(camera.scale_length(3.0))))
        rail_thick = max(1, int(round(camera.scale_length(1.5))))

        for i, seg in enumerate(track.barriers):
            p1 = camera.world_to_screen(seg.start)
            p2 = camera.world_to_screen(seg.end)

            # Viewport culling
            if not (-100 <= p1[0] <= camera.width + 100 or -100 <= p2[0] <= camera.width + 100):
                continue

            # Layer 1: Dark drop shadow
            pygame.draw.line(surface, self.COLOR_BARRIER_SHADOW, p1, p2, shadow_thick)
            # Layer 2: Metallic barrier core
            pygame.draw.line(surface, self.COLOR_BARRIER_BASE, p1, p2, core_thick)
            # Layer 3: Top rail highlight
            pygame.draw.line(surface, self.COLOR_BARRIER_RAIL, p1, p2, rail_thick)

            # Barrier posts every 4 segments
            if i % 4 == 0:
                pygame.draw.circle(surface, self.COLOR_BARRIER_POST, p1, max(2, int(camera.scale_length(2.5))))

    def _draw_finish_line(self, surface: pygame.Surface, camera: Camera, track: Track) -> None:
        """Renders high-visibility two-row checkered start/finish line."""
        fl = track.finish_line
        line_len = fl.length()
        if line_len < 1.0:
            return

        num_blocks = 16
        v_step = fl.vector() / num_blocks
        fwd_norm = fl.direction().perpendicular() * 4.5  # World thickness of finish band

        for i in range(num_blocks):
            b_start = fl.start + v_step * i
            b_end = b_start + v_step

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
