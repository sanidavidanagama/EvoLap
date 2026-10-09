"""Unit tests and headless verification for physics dynamics and collisions."""

import math
import pytest

from core.constants import DEFAULT_DT
from core.math2d import Vector2D
from physics.collisions import (
    check_vehicle_barrier_collision,
    get_vehicle_bounding_segments,
    get_vehicle_corners,
)
from physics.dynamics import VehicleConfig, VehicleDynamics, VehicleState
from simulation.track import Track


class TestVehiclePhysics:
    def test_forward_acceleration(self):
        state = VehicleState(position=Vector2D(0.0, 0.0), heading=0.0)
        assert state.speed == 0.0

        # Step forward with full throttle for 30 ticks (0.5s)
        for _ in range(30):
            VehicleDynamics.step(state, throttle_input=1.0, steer_input=0.0, dt=DEFAULT_DT)

        assert state.speed > 50.0
        assert state.position.x > 0.0
        assert state.position.y == pytest.approx(0.0, abs=1e-4)
        assert state.is_running()

    def test_engine_braking_and_stopping(self):
        # Start at speed 100 px/s with no throttle
        state = VehicleState(position=Vector2D(0.0, 0.0), heading=0.0, speed=100.0)

        # Release throttle: engine drag and rolling resistance should slow car down
        for _ in range(120):  # 2.0 seconds
            VehicleDynamics.step(state, throttle_input=0.0, steer_input=0.0, dt=DEFAULT_DT)

        assert state.speed == 0.0
        assert state.velocity.magnitude() == 0.0

    def test_active_braking(self):
        state = VehicleState(position=Vector2D(0.0, 0.0), heading=0.0, speed=200.0)

        # Active braking with -1.0 throttle input
        for _ in range(30):  # 0.5s
            VehicleDynamics.step(state, throttle_input=-1.0, steer_input=0.0, dt=DEFAULT_DT)

        # Speed should decrease much faster than off-throttle drag
        assert state.speed < 50.0

    def test_reverse_motion(self):
        state = VehicleState(position=Vector2D(0.0, 0.0), heading=0.0, speed=0.0)

        # Apply reverse throttle from standstill
        for _ in range(30):
            VehicleDynamics.step(state, throttle_input=-1.0, steer_input=0.0, dt=DEFAULT_DT)

        assert state.speed < 0.0
        assert state.position.x < 0.0

    def test_steering_build_up_and_auto_centering(self):
        state = VehicleState(position=Vector2D(0.0, 0.0), heading=0.0)
        cfg = VehicleConfig()

        # Turn right (+1.0)
        VehicleDynamics.step(state, throttle_input=0.5, steer_input=1.0, dt=DEFAULT_DT, config=cfg)
        assert state.steer_angle > 0.0
        assert state.steer_angle <= cfg.max_steer_angle

        # Hold right for 30 ticks to reach max steer angle
        for _ in range(30):
            VehicleDynamics.step(state, throttle_input=0.5, steer_input=1.0, dt=DEFAULT_DT, config=cfg)
        assert state.steer_angle == pytest.approx(cfg.max_steer_angle, abs=1e-3)

        # Release steer input -> auto centers
        for _ in range(30):
            VehicleDynamics.step(state, throttle_input=0.5, steer_input=0.0, dt=DEFAULT_DT, config=cfg)
        assert state.steer_angle == pytest.approx(0.0, abs=1e-3)

    def test_turning_changes_heading(self):
        state = VehicleState(position=Vector2D(0.0, 0.0), heading=0.0, speed=100.0)

        # Drive forward while steering right
        for _ in range(30):
            VehicleDynamics.step(state, throttle_input=1.0, steer_input=1.0, dt=DEFAULT_DT)

        # Heading should have turned clockwise / positive angle
        assert state.heading > 0.0
        assert state.position.y != 0.0

    def test_chassis_bounding_geometry(self):
        pos = Vector2D(100.0, 100.0)
        heading = 0.0  # pointing +X
        fl, fr, rr, rl = get_vehicle_corners(pos, heading, length=40.0, width=20.0)

        # Heading 0: front is +X, lateral left is +Y
        assert fl == Vector2D(120.0, 110.0)
        assert fr == Vector2D(120.0, 90.0)
        assert rr == Vector2D(80.0, 90.0)
        assert rl == Vector2D(80.0, 110.0)

        segs = get_vehicle_bounding_segments(pos, heading, VehicleConfig(length=40.0, width=20.0))
        assert len(segs) == 4

    def test_barrier_collision_and_crash_transition(self):
        track = Track.create_monaco_test_circuit()
        # Place car directly intersecting inner barrier
        barrier_pt = track.inner_segments[0].midpoint()
        state = VehicleState(position=barrier_pt, heading=0.0, speed=50.0)
        assert state.is_running()

        collided, hit = check_vehicle_barrier_collision(state, track)
        assert collided is True
        assert hit is not None
        assert state.status == "Out"
        assert state.speed == 0.0
        assert state.is_running() is False

        # Further updates while 'Out' must not move the car
        pos_before = state.position
        VehicleDynamics.step(state, throttle_input=1.0, steer_input=0.0, dt=DEFAULT_DT)
        assert state.position == pos_before

    def test_reset_logic(self):
        state = VehicleState(position=Vector2D(500.0, 500.0), heading=1.5, speed=200.0)
        state.crash()
        assert state.status == "Out"

        spawn_pos = Vector2D(250.0, 700.0)
        spawn_heading = 0.0
        state.reset(spawn_pos, spawn_heading)

        assert state.status == "Running"
        assert state.position == spawn_pos
        assert state.heading == spawn_heading
        assert state.speed == 0.0
        assert state.velocity == Vector2D(0.0, 0.0)
        assert state.steer_angle == 0.0

    def test_headless_simulation_determinism(self):
        """Simulates identical control sequences and verifies 100% deterministic bit-exact outputs."""
        track = Track.create_monaco_test_circuit()

        def run_sim():
            state = VehicleState(position=track.spawn_position, heading=track.spawn_heading)
            for i in range(120):
                throttle = 0.8 if i < 60 else 0.0
                steer = 0.1 if 20 < i < 50 else 0.0
                VehicleDynamics.step(state, throttle, steer, DEFAULT_DT)
            return state

        run1 = run_sim()
        run2 = run_sim()

        assert run1.is_running()
        assert run1.position == run2.position
        assert run1.heading == run2.heading
        assert run1.speed == run2.speed
        assert run1.velocity == run2.velocity
