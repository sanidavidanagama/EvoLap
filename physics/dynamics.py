"""Vehicle dynamics configuration and simulation state for EvoLap."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from core.constants import DEFAULT_DT, EPSILON
from core.math2d import Vector2D
from physics.steering import SteeringConfig, SteeringModel


@dataclass(frozen=True, slots=True)
class VehicleConfig:
    """Vehicle physical dimensions, powertrain, and handling parameters."""

    length: float = 38.0              # Chassis length (pixels)
    width: float = 14.0               # Chassis width (pixels, F1 ratio ~2.7:1)
    wheelbase: float = 26.0           # Effective distance between front/rear axles
    top_speed_kmh: float = 340.0      # Maximum forward speed in km/h
    scale_px_per_meter: float = 7.0   # Scale factor (7.0 pixels per meter)
    max_forward_speed: float = 661.1  # Max forward speed in px/s (top_speed_kmh / 3.6 * scale_px_per_meter)
    max_reverse_speed: float = 0.0    # Reverse disabled: minimum speed is 0.0
    acceleration: float = 320.0       # Full throttle longitudinal acceleration (px/s^2)
    braking: float = 620.0            # Full braking deceleration (px/s^2)
    engine_drag: float = 120.0        # Engine braking deceleration when off-throttle
    rolling_resistance: float = 35.0  # Rolling resistance drag
    air_drag_coeff: float = 0.00035   # Aerodynamic drag factor proportional to speed^2
    max_steer_angle: float = 0.50     # Default low-speed maximum front wheel deflection (radians)
    steer_rate: float = 3.8           # Default low-speed steer build-up rate (rad/s)
    steer_return_rate: float = 5.6    # Steer centering rate when released (rad/s)
    lateral_grip: float = 15.0        # Lateral tire grip friction damping
    steering: SteeringConfig = field(default_factory=SteeringConfig)


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
        :param throttle_input: In range [-1.0, +1.0] (+1 = gas, <=0 = brake). Reverse is disabled.
        :param steer_input: In range [-1.0, +1.0] (-1 = steer left, +1 = steer right).
        :param dt: Time delta in seconds.
        :param config: Vehicle configuration parameters.
        """
        if not state.is_running() or dt <= 0.0:
            return

        cfg = config if config is not None else VehicleConfig()

        # 1. Lateral Steering Input & Speed-Dependent Front-Wheel Dynamics
        state.steer_angle = SteeringModel.step(
            current_steer=state.steer_angle,
            steer_input=steer_input,
            speed_px_s=state.speed,
            dt=dt,
            wheelbase_px=cfg.wheelbase,
            scale_px_per_m=cfg.scale_px_per_meter,
            max_speed_px_s=cfg.max_forward_speed,
            config=cfg.steering,
        )

        # 2. Longitudinal Powertrain Dynamics (Throttle, Brake, Engine Drag)
        clamped_throttle = max(-1.0, min(1.0, throttle_input))
        accel = 0.0

        if clamped_throttle > 0.01:
            # Accelerating forward
            accel = clamped_throttle * cfg.acceleration
        elif clamped_throttle < -0.01:
            # Active braking down to 0.0 (reverse is disabled)
            if state.speed > EPSILON:
                accel = -cfg.braking
            else:
                state.speed = 0.0
                accel = 0.0
        else:
            # Off-throttle: apply engine drag and rolling resistance down to 0
            if state.speed > EPSILON:
                drag = cfg.engine_drag + cfg.rolling_resistance
                accel = -min(state.speed / dt, drag)
            else:
                state.speed = 0.0
                accel = 0.0

        # Aerodynamic air drag proportional to v^2 (only opposes forward motion)
        if state.speed > EPSILON:
            air_drag = cfg.air_drag_coeff * (state.speed ** 2)
            accel -= air_drag

        # Update forward speed and clamp to [0.0, max_forward_speed]
        state.speed += accel * dt
        state.speed = max(0.0, min(cfg.max_forward_speed, state.speed))

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
