"""Unit tests for simulation.track module."""

from pathlib import Path
import pytest

from core.math2d import LineSegment, Vector2D
from simulation.track import Track, TrackConfig


class TestTrack:
    def test_load_track_by_name_and_file(self):
        track = Track.load("apex_valley")
        assert track.name == "Apex Valley Circuit"
        assert len(track.inner_barrier) == 360
        assert len(track.outer_barrier) == 360
        assert len(track.inner_segments) == 360
        assert len(track.outer_segments) == 360
        assert len(track.barriers) == 720

        # Check finish line segment
        assert isinstance(track.finish_line, LineSegment)
        assert track.finish_line.length() == pytest.approx(120.0, abs=1.0)

        # Check spawn configuration
        assert isinstance(track.spawn_position, Vector2D)
        assert track.spawn_heading == 0.0

        # Check checkpoints & grid slots
        assert len(track.checkpoints) == 24
        assert len(track.grid_slots) == 20

    def test_barrier_collision_detection(self):
        track = Track.load("apex_valley")

        # Pick one inner barrier segment
        barrier = track.inner_segments[0]
        mid = barrier.midpoint()
        normal = barrier.normal()

        # Crossing segment across the barrier
        crossing_seg = LineSegment(mid - normal * 10.0, mid + normal * 10.0)
        hit = track.check_collision(crossing_seg)
        assert hit is not None
        assert hit.distance_to(mid) < 1.0

        # Segment along the track centerline (should not collide with barriers)
        safe_seg = LineSegment(track.spawn_position, track.spawn_position + Vector2D(50.0, 0.0))
        assert track.check_collision(safe_seg) is None

    def test_raycast(self):
        track = Track.load("apex_valley")

        # Raycast from spawn position pointing upward towards the barrier
        origin = track.spawn_position
        up_dir = Vector2D(0.0, 1.0)
        res = track.raycast(origin, up_dir, max_range=200.0)
        assert res is not None
        hit_pt, dist = res
        assert dist > 0.0

    def test_load_apex_valley_json_direct(self):
        json_path = Path("storage/tracks/apex_valley.json")
        assert json_path.exists(), "apex_valley.json must exist in storage/tracks/"

        track = Track.from_json_file(json_path)
        assert track.name == "Apex Valley Circuit"
        assert track.config.track_width == 120.0
        assert track.config.scale_pixels_per_meter == 7.0
        assert len(track.inner_barrier) == 360
        assert len(track.outer_barrier) == 360
        assert len(track.checkpoints) == 24
        assert len(track.grid_slots) == 20

        # Raycast test on Apex Valley
        ray_hit = track.raycast(track.spawn_position, Vector2D(0.0, -1.0), max_range=200.0)
        assert ray_hit is not None
        hit_pt, dist = ray_hit
        assert dist > 0.0
