"""Vehicle dynamics configuration and simulation state for EvoLap."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from core.constants import DEFAULT_DT, EPSILON
from core.math2d import Vector2D


@dataclass(frozen=True, slots=True)
class VehicleConfig:
    """Vehicle physical dimensions, powertrain, and handling parameters."""

    length: float = 38.0              # Chassis length (pixels)
    width: float = 18.0               # Chassis width (pixels)
    wheelbase: float = 28.0           # Effective distance between front/rear axles
    max_forward_speed: float = 550.0  # Max forward speed in px/s (~300 km/h scale)
    max_reverse_speed: float = 120.0  # Max reverse speed in px/s
    acceleration: float = 360.0       # Full throttle longitudinal acceleration (px/s^2)
    braking: float = 580.0            # Full braking deceleration (px/s^2)
    engine_drag: float = 110.0        # Engine braking deceleration when off-throttle
    rolling_resistance: float = 30.0  # Rolling resistance drag
    air_drag_coeff: float = 0.0005    # Aerodynamic drag factor proportional to speed^2
    max_steer_angle: float = 0.52     # ~30 degrees maximum front wheel deflection (radians)
    steer_rate: float = 3.2           # Steer angle build-up rate (rad/s)
    steer_return_rate: float = 5.0    # Steer centering rate when released (rad/s)
    lateral_grip: float = 14.0        # Lateral tire grip friction damping


@dataclass
class VehicleState:
    """Dynamic state container for a simulated vehicle."""

    position: Vector2D
    heading: float = 0.0                                  # Yaw angle in radians (0 = pointing +X)
    speed: float = 0.0                                    # Forward longitudinal speed (px/s)
    velocity: Vector2D = field(default_factory=Vector2D)  # Full 2D velocity vector
    steer_angle: float = 0.0                              # Current front wheel steer angle (radians)
    angular_velocity: float = 0.0                         # Yaw rate (rad/s)
    status: str = "Running"                               # "Running" or "Out"

    def is_running(self) -> bool:
        """Returns True if the vehicle is active and operational."""
        return self.status == "Running"

    def crash(self) -> None:
        """Transitions vehicle to crashed state ('Out') and halts motion."""
        self.status = "Out"
        self.speed = 0.0
        self.velocity = Vector2D(0.0, 0.0)
        self.angular_velocity = 0.0

    def reset(self, spawn_position: Vector2D, spawn_heading: float) -> None:
        """Restores vehicle to operational status at specified spawn transform."""
        self.position = spawn_position
        self.heading = spawn_heading
        self.speed = 0.0
        self.velocity = Vector2D(0.0, 0.0)
        self.steer_angle = 0.0
        self.angular_velocity = 0.0
        self.status = "Running"


class VehicleDynamics:
    """Calculates deterministic vehicle physics transitions without rendering dependencies."""

    @staticmethod
    def step(
        state: VehicleState,
        throttle_input: float,
        steer_input: float,
        dt: float = DEFAULT_DT,
        config: Optional[VehicleConfig] = None,
    ) -> None:
        """
        Advances the vehicle state by dt using longitudinal powertrain and lateral
        kinematic bicycle dynamics.
        
        :param state: Mutable VehicleState to update.
        :param throttle_input: In range [-1.0, +1.0] (+1 = gas, -1 = brake/reverse).
        :param steer_input: In range [-1.0, +1.0] (-1 = steer left, +1 = steer right).
        :param dt: Time delta in seconds.
        :param config: Vehicle configuration parameters.
        """
        if not state.is_running() or dt <= 0.0:
            return

        cfg = config if config is not None else VehicleConfig()

        # 1. Lateral Steering Input & Front-Wheel Dynamics
        clamped_steer_input = max(-1.0, min(1.0, steer_input))
        target_steer = clamped_steer_input * cfg.max_steer_angle

        if abs(clamped_steer_input) > 0.01:
            # Gradual steer build-up towards target angle
            diff = target_steer - state.steer_angle
            max_change = cfg.steer_rate * dt
            if abs(diff) <= max_change:
                state.steer_angle = target_steer
            else:
                state.steer_angle += math.copysign(max_change, diff)
        else:
            # Wheels naturally auto-center when no steering input is applied
            if abs(state.steer_angle) <= cfg.steer_return_rate * dt:
                state.steer_angle = 0.0
            else:
                state.steer_angle -= math.copysign(cfg.steer_return_rate * dt, state.steer_angle)

        state.steer_angle = max(-cfg.max_steer_angle, min(cfg.max_steer_angle, state.steer_angle))

        # 2. Longitudinal Powertrain Dynamics (Throttle, Brake, Engine Drag)
        clamped_throttle = max(-1.0, min(1.0, throttle_input))
        accel = 0.0

        if clamped_throttle > 0.01:
            # Accelerating forward
            accel = clamped_throttle * cfg.acceleration
        elif clamped_throttle < -0.01:
            if state.speed > 5.0:
                # Active braking
                accel = clamped_throttle * cfg.braking
            else:
                # Reverse acceleration (scaled lower than forward drive)
                accel = clamped_throttle * (cfg.acceleration * 0.45)
        else:
            # Off-throttle: apply engine drag and rolling resistance
            if state.speed > EPSILON:
                drag = cfg.engine_drag + cfg.rolling_resistance
                accel = -min(state.speed / dt, drag)
            elif state.speed < -EPSILON:
                drag = cfg.engine_drag + cfg.rolling_resistance
                accel = min(-state.speed / dt, drag)
            else:
                state.speed = 0.0
                accel = 0.0

        # Aerodynamic air drag proportional to v^2
        air_drag = math.copysign(cfg.air_drag_coeff * (state.speed ** 2), state.speed)
        accel -= air_drag

        # Update forward speed and clamp to maximum envelope
        state.speed += accel * dt
        state.speed = max(-cfg.max_reverse_speed, min(cfg.max_forward_speed, state.speed))

        # Snap near-zero speeds to 0 to prevent micro-oscillation
        if abs(clamped_throttle) <= 0.01 and abs(state.speed) < 0.5:
            state.speed = 0.0

        # 3. Kinematic Yaw & Angular Heading Dynamics
        if abs(state.speed) > EPSILON and abs(state.steer_angle) > EPSILON:
            # Angular velocity from kinematic bicycle model: omega = (v / L) * tan(delta)
            state.angular_velocity = (state.speed / cfg.wheelbase) * math.tan(state.steer_angle)
        else:
            state.angular_velocity = 0.0

        state.heading += state.angular_velocity * dt
        # Normalize heading to [-pi, pi]
        state.heading = math.atan2(math.sin(state.heading), math.cos(state.heading))

        # 4. Velocity Vector & Lateral Grip Damping
        forward_vec = Vector2D.from_angle(state.heading)
        lateral_vec = forward_vec.perpendicular()

        # Previous lateral slip velocity
        prev_lateral_speed = state.velocity.dot(lateral_vec)
        # Tire friction damps out lateral drift
        damped_lateral_speed = prev_lateral_speed * max(0.0, 1.0 - cfg.lateral_grip * dt)

        # Composite velocity vector
        state.velocity = forward_vec * state.speed + lateral_vec * damped_lateral_speed

        # 5. Position Translation
        state.position += state.velocity * dt
