"""Unit tests for Camera coordinate transformations and modes."""

import pytest

from core.math2d import Vector2D
from rendering.camera import Camera
from simulation.track import Track


class TestCamera:
    def test_camera_initialization(self):
        cam = Camera(viewport_width=1920, viewport_height=1080)
        assert cam.width == 1920
        assert cam.height == 1080
        assert cam.mode == Camera.MODE_FULL_TRACK

    def test_world_to_screen_and_back(self):
        cam = Camera(viewport_width=1000, viewport_height=600)
        cam.target_pos = Vector2D(500.0, 300.0)
        cam.zoom = 2.0

        # Center of camera should map to center of screen (500, 300)
        center_screen = cam.world_to_screen(Vector2D(500.0, 300.0))
        assert center_screen == (500, 300)

        # Offset in world space: (550, 300) -> screen (500 + 50*2, 300) = (600, 300)
        off_screen = cam.world_to_screen(Vector2D(550.0, 300.0))
        assert off_screen == (600, 300)

        # Reverse mapping: screen_to_world
        world_pt = cam.screen_to_world(600, 300)
        assert world_pt.x == pytest.approx(550.0)
        assert world_pt.y == pytest.approx(300.0)

    def test_fit_track(self):
        track = Track.load("apex_valley")
        cam = Camera(viewport_width=1920, viewport_height=1080)
        cam.fit_track(track)

        assert cam.zoom > 0.0
        assert cam.full_track_zoom > 0.0
        # All track points should fit inside screen bounds
        for p in track.inner_barrier + track.outer_barrier:
            sx, sy = cam.world_to_screen(p)
            assert 0 <= sx <= 1920
            assert 0 <= sy <= 1080

    def test_toggle_mode(self):
        cam = Camera(1920, 1080, mode=Camera.MODE_FULL_TRACK)
        assert cam.toggle_mode() == Camera.MODE_FOLLOW
        assert cam.toggle_mode() == Camera.MODE_FULL_TRACK
