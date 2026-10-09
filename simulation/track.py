"""Track geometry, barrier representation, and coordinate structures for EvoLap."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.constants import DEG_TO_RAD
from core.math2d import LineSegment, Vector2D


@dataclass(frozen=True, slots=True)
class TrackConfig:
    """Track dimensions and visualization scale configuration."""

    track_width: float = 120.0
    scale_pixels_per_meter: float = 7.0


@dataclass(frozen=True, slots=True)
class SpawnConfig:
    """Vehicle spawn configuration and grid slots."""

    finish_line: LineSegment
    forward_heading_rad: float
    spawn_position: Vector2D
    grid_slots: List[Tuple[Vector2D, float]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """Lap timing and progression gate segment."""

    id: int
    line: LineSegment


class Track:
    """
    Physical track geometry representation consisting of inner and outer barrier
    boundaries, start/finish line, checkpoints, and vehicle spawn metadata.
    Strictly decoupled from rendering libraries (zero Pygame).
    """

    def __init__(
        self,
        name: str,
        inner_barrier: List[Vector2D],
        outer_barrier: List[Vector2D],
        finish_line: LineSegment,
        spawn_position: Vector2D,
        spawn_heading: float,
        checkpoints: Optional[List[LineSegment]] = None,
        grid_slots: Optional[List[Tuple[Vector2D, float]]] = None,
        config: Optional[TrackConfig] = None,
    ) -> None:
        self.name = name
        self.inner_barrier = list(inner_barrier)
        self.outer_barrier = list(outer_barrier)
        self.finish_line = finish_line
        self.spawn_position = spawn_position
        self.spawn_heading = spawn_heading  # in radians
        self.checkpoints = list(checkpoints) if checkpoints is not None else []
        self.grid_slots = list(grid_slots) if grid_slots is not None else []
        self.config = config if config is not None else TrackConfig()

        # Precompute closed barrier line segments
        self.inner_segments: List[LineSegment] = self._build_boundary_segments(self.inner_barrier)
        self.outer_segments: List[LineSegment] = self._build_boundary_segments(self.outer_barrier)
        self.barriers: List[LineSegment] = self.inner_segments + self.outer_segments

    @staticmethod
    def _build_boundary_segments(points: List[Vector2D]) -> List[LineSegment]:
        """Constructs consecutive line segments forming a closed loop."""
        if len(points) < 2:
            return []
        segments: List[LineSegment] = []
        n = len(points)
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            segments.append(LineSegment(p1, p2))
        return segments

    def check_collision(self, segment: LineSegment) -> Optional[Vector2D]:
        """
        Tests if the given segment (e.g. car edge or velocity delta) intersects
        any inner or outer barrier segment.
        Returns the first intersection point found, or None.
        """
        for barrier in self.barriers:
            hit = barrier.intersect(segment)
            if hit is not None:
                return hit
        return None

    def raycast(
        self, origin: Vector2D, direction: Vector2D, max_range: float = 1000.0
    ) -> Optional[Tuple[Vector2D, float]]:
        """
        Casts a ray from origin in direction up to max_range against all barrier segments.
        Returns (hit_point, distance) for the closest barrier hit, or None if no hit.
        """
        dir_norm = direction.normalize()
        if dir_norm.magnitude() < 1e-6:
            return None

        closest_hit: Optional[Vector2D] = None
        closest_dist = max_range

        for barrier in self.barriers:
            res = barrier.intersect_ray(origin, dir_norm)
            if res is not None:
                hit_pt, dist = res
                if dist < closest_dist:
                    closest_dist = dist
                    closest_hit = hit_pt

        if closest_hit is not None:
            return (closest_hit, closest_dist)
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Track:
        """Constructs a Track instance from dictionary schema."""
        name = data.get("metadata", {}).get("name", "Circuit")
        cfg_data = data.get("config", {})
        config = TrackConfig(
            track_width=float(cfg_data.get("track_width", 70.0)),
            scale_pixels_per_meter=float(cfg_data.get("scale_pixels_per_meter", 0.45)),
        )

        geom = data.get("geometry", {})
        inner_pts = [Vector2D(float(p[0]), float(p[1])) for p in geom.get("inner_barrier", [])]
        outer_pts = [Vector2D(float(p[0]), float(p[1])) for p in geom.get("outer_barrier", [])]

        spawn_data = data.get("spawn", {})
        fl_data = spawn_data.get("finish_line", {})
        fl_p1 = Vector2D(float(fl_data["p1"][0]), float(fl_data["p1"][1]))
        fl_p2 = Vector2D(float(fl_data["p2"][0]), float(fl_data["p2"][1]))
        finish_line = LineSegment(fl_p1, fl_p2)

        # Forward heading in radians (JSON defines degrees)
        heading_deg = float(spawn_data.get("forward_heading_deg", 0.0))
        heading_rad = heading_deg * DEG_TO_RAD

        # Grid slots & primary spawn
        raw_slots = spawn_data.get("grid_slots", [])
        grid_slots: List[Tuple[Vector2D, float]] = []
        for slot in raw_slots:
            pos = Vector2D(float(slot["pos"][0]), float(slot["pos"][1]))
            h_rad = float(slot.get("heading", heading_deg)) * DEG_TO_RAD
            grid_slots.append((pos, h_rad))

        if grid_slots:
            spawn_pos, spawn_h = grid_slots[0]
        else:
            spawn_pos = finish_line.midpoint()
            spawn_h = heading_rad

        # Checkpoints
        checkpoints: List[LineSegment] = []
        for cp in data.get("checkpoints", []):
            line_pts = cp["line"]
            cp_p1 = Vector2D(float(line_pts[0][0]), float(line_pts[0][1]))
            cp_p2 = Vector2D(float(line_pts[1][0]), float(line_pts[1][1]))
            checkpoints.append(LineSegment(cp_p1, cp_p2))

        return cls(
            name=name,
            inner_barrier=inner_pts,
            outer_barrier=outer_pts,
            finish_line=finish_line,
            spawn_position=spawn_pos,
            spawn_heading=spawn_h,
            checkpoints=checkpoints,
            grid_slots=grid_slots,
            config=config,
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> Track:
        """Loads a Track instance from a JSON file path."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def create_monaco_test_circuit(cls) -> Track:
        """
        Creates a built-in Grand Prix test circuit inspired by technical street circuits
        with chicanes, hairpins, left turns, and right turns.
        Generates a smooth, wide Catmull-Rom spline with zero barrier self-intersections.
        """
        track_width = 120.0
        half_w = track_width * 0.5

        # 11 Key waypoints framing a rich, spacious Grand Prix circuit
        control_points = [
            Vector2D(400.0, 950.0),   # 0: Start of main straight
            Vector2D(900.0, 950.0),   # 1: Mid main straight (Finish line zone)
            Vector2D(1400.0, 950.0),  # 2: End of main straight / Turn 1 braking zone
            Vector2D(1750.0, 800.0),  # 3: Turn 1 sweeping right
            Vector2D(1750.0, 500.0),  # 4: Turn 2 uphill right
            Vector2D(1550.0, 300.0),  # 5: Turn 3 medium left
            Vector2D(1200.0, 200.0),  # 6: Turn 4 left onto back straight
            Vector2D(700.0, 200.0),   # 7: Back straight
            Vector2D(350.0, 300.0),   # 8: Chicane entry
            Vector2D(200.0, 500.0),   # 9: Wide hairpin Turn
            Vector2D(250.0, 750.0),   # 10: Exit onto straight
        ]

        # Interpolate with Catmull-Rom spline for continuous smooth curvature
        n = len(control_points)
        num_per_seg = 25
        spline: List[Vector2D] = []
        for i in range(n):
            p0 = control_points[(i - 1) % n]
            p1 = control_points[i]
            p2 = control_points[(i + 1) % n]
            p3 = control_points[(i + 2) % n]
            for step in range(num_per_seg):
                t = step / num_per_seg
                t2 = t * t
                t3 = t2 * t
                x = 0.5 * ((2.0 * p1.x) + (-p0.x + p2.x) * t + (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2 + (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3)
                y = 0.5 * ((2.0 * p1.y) + (-p0.y + p2.y) * t + (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2 + (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3)
                spline.append(Vector2D(x, y))

        m = len(spline)
        inner_pts: List[Vector2D] = []
        outer_pts: List[Vector2D] = []
        for i in range(m):
            p_prev = spline[(i - 1) % m]
            p_next = spline[(i + 1) % m]
            tangent = (p_next - p_prev).normalize()
            normal = tangent.perpendicular()
            inner_pts.append(spline[i] + normal * half_w)
            outer_pts.append(spline[i] - normal * half_w)

        # Start/Finish line on main straight (around x=900, y=950)
        fl_idx = 25
        finish_line = LineSegment(inner_pts[fl_idx], outer_pts[fl_idx])

        # Primary vehicle spawn on main straight facing forward (+X direction)
        spawn_pos = spline[15]  # Ahead of entry, ~120px behind finish line
        spawn_heading = 0.0

        # Zig-zag grid slots behind finish line
        grid_slots: List[Tuple[Vector2D, float]] = []
        for slot_num in range(20):
            slot_idx = (fl_idx - 3 - slot_num * 2) % m
            slot_center = spline[slot_idx]
            tangent = (spline[(slot_idx + 1) % m] - spline[(slot_idx - 1) % m]).normalize()
            norm = tangent.perpendicular()
            lateral_offset = (half_w * 0.4) * (1.0 if slot_num % 2 == 0 else -1.0)
            slot_pos = slot_center + norm * lateral_offset
            grid_slots.append((slot_pos, tangent.angle()))

        # Checkpoint gates placed around the circuit
        checkpoints: List[LineSegment] = []
        cp_step = m // 16
        for i in range(16):
            idx = (fl_idx + (i + 1) * cp_step) % m
            checkpoints.append(LineSegment(inner_pts[idx], outer_pts[idx]))

        return cls(
            name="Monaco Grand Prix Circuit",
            inner_barrier=inner_pts,
            outer_barrier=outer_pts,
            finish_line=finish_line,
            spawn_position=spawn_pos,
            spawn_heading=spawn_heading,
            checkpoints=checkpoints,
            grid_slots=grid_slots,
            config=TrackConfig(track_width=track_width, scale_pixels_per_meter=7.0),
        )
