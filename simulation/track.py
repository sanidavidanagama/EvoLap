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

    track_width: float = 70.0
    scale_pixels_per_meter: float = 0.45


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
        Creates a built-in test circuit inspired by technical street circuits
        with chicanes, hairpins, left turns, and right turns.
        Allows instant execution without external file dependencies.
        """
        track_width = 60.0

        # Centerline key-waypoints defining a loop with varied turns:
        # Straight -> Turn 1 Right -> Chicane (Left, Right) -> Hairpin Left -> Straight -> Turn 4 Left
        centerline = [
            Vector2D(200.0, 700.0),   # 0: Main straight start
            Vector2D(500.0, 700.0),   # 1: Main straight end / Start Turn 1
            Vector2D(700.0, 600.0),   # 2: Turn 1 (Right sweeper)
            Vector2D(750.0, 450.0),   # 3: Climbing straight
            Vector2D(650.0, 350.0),   # 4: Chicane Left
            Vector2D(700.0, 250.0),   # 5: Chicane Right
            Vector2D(550.0, 150.0),   # 6: Approach to hairpin
            Vector2D(400.0, 150.0),   # 7: Hairpin apex (Tight 180 Left)
            Vector2D(350.0, 250.0),   # 8: Hairpin exit
            Vector2D(350.0, 450.0),   # 9: Downhill straight
            Vector2D(200.0, 550.0),   # 10: Turn left into final straight
        ]

        # Generate inner and outer boundaries by offsetting centerline normals
        n = len(centerline)
        inner_pts: List[Vector2D] = []
        outer_pts: List[Vector2D] = []
        half_w = track_width / 2.0

        for i in range(n):
            prev_pt = centerline[(i - 1) % n]
            curr_pt = centerline[i]
            next_pt = centerline[(i + 1) % n]

            # Forward and incoming tangent vectors
            t1 = (curr_pt - prev_pt).normalize()
            t2 = (next_pt - curr_pt).normalize()
            tangent = (t1 + t2).normalize()
            normal = tangent.perpendicular()  # Points inward/left

            inner_pts.append(curr_pt + normal * half_w)
            outer_pts.append(curr_pt - normal * half_w)

        # Start/finish line on main straight between index 0 and 1
        sf_center = Vector2D(300.0, 700.0)
        sf_inner = sf_center + Vector2D(0.0, half_w)
        sf_outer = sf_center - Vector2D(0.0, half_w)
        finish_line = LineSegment(sf_inner, sf_outer)

        # Spawn position just behind the finish line, facing +X (heading = 0.0)
        spawn_pos = Vector2D(250.0, 700.0)
        spawn_heading = 0.0

        # Construct checkpoints across centerline segments
        checkpoints: List[LineSegment] = []
        for i in range(n):
            cp_pt = centerline[i]
            prev_pt = centerline[(i - 1) % n]
            next_pt = centerline[(i + 1) % n]
            t = (next_pt - prev_pt).normalize()
            norm = t.perpendicular()
            checkpoints.append(
                LineSegment(cp_pt + norm * half_w, cp_pt - norm * half_w)
            )

        return cls(
            name="Monaco Test Circuit",
            inner_barrier=inner_pts,
            outer_barrier=outer_pts,
            finish_line=finish_line,
            spawn_position=spawn_pos,
            spawn_heading=spawn_heading,
            checkpoints=checkpoints,
            config=TrackConfig(track_width=track_width, scale_pixels_per_meter=0.5),
        )
