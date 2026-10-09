"""Unit tests for simulation.track module."""

from pathlib import Path
import pytest

from core.math2d import LineSegment, Vector2D
from simulation.track import Track, TrackConfig


class TestTrack:
    def test_monaco_test_circuit_creation(self):
        track = Track.create_monaco_test_circuit()
        assert "Monaco" in track.name
        assert len(track.inner_barrier) >= 10
        assert len(track.outer_barrier) >= 10
        assert len(track.inner_segments) == len(track.inner_barrier)
        assert len(track.outer_segments) == len(track.outer_barrier)
        assert len(track.barriers) == len(track.inner_segments) + len(track.outer_segments)

        # Check finish line segment
        assert isinstance(track.finish_line, LineSegment)
        assert track.finish_line.length() > 0.0

        # Check spawn configuration
        assert isinstance(track.spawn_position, Vector2D)
        assert track.spawn_heading == 0.0

        # Check checkpoints
        assert len(track.checkpoints) > 0

    def test_barrier_collision_detection(self):
        track = Track.create_monaco_test_circuit()

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
        track = Track.create_monaco_test_circuit()

        # Raycast from spawn position pointing upward towards the barrier
        origin = track.spawn_position
        up_dir = Vector2D(0.0, 1.0)
        res = track.raycast(origin, up_dir, max_range=200.0)
        assert res is not None
        hit_pt, dist = res
        assert dist > 0.0

    def test_load_apex_valley_json(self):
        json_path = Path("storage/tracks/apex_valley.json")
        assert json_path.exists(), "apex_valley.json must exist in storage/tracks/"

        track = Track.from_json_file(json_path)
        assert track.name == "Apex Valley Circuit"
        assert len(track.inner_barrier) == 540
        assert len(track.outer_barrier) == 540
        assert len(track.inner_segments) == 540
        assert len(track.outer_segments) == 540
        assert len(track.barriers) == 1080
        assert len(track.checkpoints) == 45
        assert len(track.grid_slots) == 20

        # Check spawn position from slot 1
        assert track.spawn_position == Vector2D(762.5, 836.0)

        # Test raycast on Apex Valley
        ray_hit = track.raycast(track.spawn_position, Vector2D(0.0, -1.0), max_range=200.0)
        assert ray_hit is not None
        hit_pt, dist = ray_hit
        assert dist > 0.0
