"""Unit tests for speed-dependent steering kinematics and dynamic resistance."""

import math
import pytest

from core.constants import DEFAULT_DT
from core.math2d import Vector2D
from physics.dynamics import VehicleConfig, VehicleDynamics, VehicleState
from physics.steering import SteeringConfig, SteeringModel


class TestSteeringModel:
    def test_low_speed_full_steering_lock(self):
        """At zero or low speed (hairpin maneuvering), full lock is available."""
        cfg = SteeringConfig()

        # Zero speed
        max_angle_0 = SteeringModel.calculate_max_steer_angle(0.0, config=cfg)
        assert max_angle_0 == pytest.approx(cfg.max_steer_angle_low)

        # 20 km/h = 20 / 3.6 * 7.0 px/s ~ 38.9 px/s
        speed_20kmh = (20.0 / 3.6) * 7.0
        max_angle_20 = SteeringModel.calculate_max_steer_angle(speed_20kmh, config=cfg)
        assert max_angle_20 == pytest.approx(cfg.max_steer_angle_low)

    def test_high_speed_steering_constraint(self):
        """At high speeds, steering angle is constrained to prevent snap oversteer."""
        cfg = SteeringConfig()

        # Top speed 340 km/h
        top_speed_px = (340.0 / 3.6) * 7.0
        max_angle_top = SteeringModel.calculate_max_steer_angle(top_speed_px, config=cfg)

        # Must be drastically constrained compared to low-speed lock
        assert max_angle_top < 0.05  # < ~2.9 degrees
        assert max_angle_top >= cfg.min_steer_angle_high  # Above safety micro-adjustment floor

    def test_monotonic_angle_scaling_with_speed(self):
        """Steering lock decreases monotonically as speed increases."""
        cfg = SteeringConfig()
        speeds_kmh = [0, 30, 60, 100, 150, 200, 250, 300, 340]
        angles = []
        for spd in speeds_kmh:
            spd_px = (spd / 3.6) * 7.0
            angle = SteeringModel.calculate_max_steer_angle(spd_px, config=cfg)
            angles.append(angle)

        # Verify each angle is <= previous angle
        for i in range(len(angles) - 1):
            assert angles[i] >= angles[i + 1]

    def test_dynamic_steering_rate_resistance(self):
        """Steering build-up rate is higher at low speed and heavier/damped at high speed."""
        cfg = SteeringConfig()
        top_speed_px = (340.0 / 3.6) * 7.0

        rate_low = SteeringModel.calculate_steer_rate(0.0, max_speed_px_s=top_speed_px, config=cfg)
        rate_high = SteeringModel.calculate_steer_rate(top_speed_px, max_speed_px_s=top_speed_px, config=cfg)

        assert rate_low == pytest.approx(cfg.steer_rate_low)
        assert rate_high == pytest.approx(cfg.steer_rate_high)
        assert rate_low > rate_high

    def test_steering_step_build_up_and_auto_centering(self):
        """Steering builds up gradually towards target and self-centers when released."""
        cfg = SteeringConfig()
        steer = 0.0

        # Apply full right steer (+1.0) at low speed (40 px/s)
        for _ in range(10):
            steer = SteeringModel.step(steer, steer_input=1.0, speed_px_s=40.0, dt=DEFAULT_DT, config=cfg)

        assert steer > 0.0
        assert steer <= cfg.max_steer_angle_low

        # Release steer input (0.0): should center rapidly
        for _ in range(30):
            steer = SteeringModel.step(steer, steer_input=0.0, speed_px_s=40.0, dt=DEFAULT_DT, config=cfg)

        assert steer == pytest.approx(0.0, abs=1e-4)

    def test_vehicle_dynamics_speed_dependent_steering(self):
        """Verify integration with VehicleDynamics at low vs high speeds."""
        veh_cfg = VehicleConfig()

        # Case 1: Low speed (50 px/s) full steer input
        state_low = VehicleState(position=Vector2D(0.0, 0.0), speed=50.0)
        for _ in range(60):
            VehicleDynamics.step(state_low, throttle_input=0.0, steer_input=1.0, dt=DEFAULT_DT, config=veh_cfg)
        assert state_low.steer_angle > 0.30  # High angle available

        # Case 2: High speed (600 px/s) full steer input
        state_high = VehicleState(position=Vector2D(0.0, 0.0), speed=600.0)
        for _ in range(60):
            # Maintain high speed
            VehicleDynamics.step(state_high, throttle_input=1.0, steer_input=1.0, dt=DEFAULT_DT, config=veh_cfg)
            state_high.speed = 600.0
        # High speed steer angle must be constrained to stable micro-adjustment
        assert state_high.steer_angle < 0.05
        assert state_high.steer_angle > 0.0
