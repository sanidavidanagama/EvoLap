"""Smooth speed-dependent steering kinematics and dynamic resistance for EvoLap."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SteeringConfig:
    """
    Configuration parameters for speed-dependent steering response,
    aerodynamic loading, and auto-centering torque.
    """

    max_steer_angle_low: float = 0.50     # Full lock at low speeds (~28.6 deg)
    min_steer_angle_high: float = 0.02    # Minimum steering deflection floor at top speed (~1.15 deg)
    base_mechanical_g: float = 2.5        # Mechanical tire grip component (G)
    aero_downforce_g: float = 2.7         # Aerodynamic downforce grip component at top speed (G)
    steer_rate_low: float = 3.8           # Fast steering response at low speed (rad/s)
    steer_rate_high: float = 1.6          # Heavily-weighted steering build-up under high downforce (rad/s)
    steer_return_rate: float = 5.6        # Self-aligning torque centering rate (rad/s)


class SteeringModel:
    """
    Computes speed-dependent steering limits, aerodynamic rack resistance,
    and progressive steering integration adhering to Formula 1 kinematics.
    Strictly decoupled from rendering libraries (zero Pygame).
    """

    @staticmethod
    def calculate_max_steer_angle(
        speed_px_s: float,
        wheelbase_px: float = 26.0,
        scale_px_per_m: float = 7.0,
        max_speed_px_s: float = 661.1,
        config: Optional[SteeringConfig] = None,
    ) -> float:
        """
        Calculates the maximum front-wheel deflection angle permitted at current speed.
        
        At low speeds (v < 30 km/h), full lock is available for hairpins and slow maneuvers.
        At high speeds, the maximum angle is constrained by the aerodynamic lateral grip
        envelope (mechanical grip + speed-squared downforce), producing stable micro-adjustments
        and preventing snap oversteer.
        """
        cfg = config if config is not None else SteeringConfig()

        if scale_px_per_m <= 0.0 or wheelbase_px <= 0.0:
            return cfg.max_steer_angle_low

        v_ms = abs(speed_px_s) / scale_px_per_m
        if v_ms < 1.0:
            return cfg.max_steer_angle_low

        wheelbase_m = wheelbase_px / scale_px_per_m
        speed_ratio = min(1.0, abs(speed_px_s) / max(1.0, max_speed_px_s))

        # Effective lateral acceleration envelope (mechanical grip + aero downforce)
        total_grip_g = cfg.base_mechanical_g + cfg.aero_downforce_g * (speed_ratio ** 2)
        total_grip_ms2 = total_grip_g * 9.80665

        # Maximum steering angle from lateral acceleration: a_lat = (v^2 / L) * tan(delta)
        tan_delta = (total_grip_ms2 * wheelbase_m) / (v_ms ** 2)
        kinematic_limit = math.atan(tan_delta)

        # Smoothly clamp between high-speed floor and low-speed physical lock
        return max(cfg.min_steer_angle_high, min(cfg.max_steer_angle_low, kinematic_limit))

    @staticmethod
    def calculate_steer_rate(
        speed_px_s: float,
        max_speed_px_s: float = 661.1,
        config: Optional[SteeringConfig] = None,
    ) -> float:
        """
        Calculates dynamic steering rate (wheel turn speed / rack resistance).
        At low speeds, wheels deflect rapidly. Under high aerodynamic pressure,
        steering is progressively weighted and smooth.
        """
        cfg = config if config is not None else SteeringConfig()
        speed_ratio = min(1.0, abs(speed_px_s) / max(1.0, max_speed_px_s))
        # Aerodynamic dynamic pressure scales with speed^2
        weighting = speed_ratio ** 1.5
        return cfg.steer_rate_low - (cfg.steer_rate_low - cfg.steer_rate_high) * weighting

    @staticmethod
    def step(
        current_steer: float,
        steer_input: float,
        speed_px_s: float,
        dt: float,
        wheelbase_px: float = 26.0,
        scale_px_per_m: float = 7.0,
        max_speed_px_s: float = 661.1,
        config: Optional[SteeringConfig] = None,
    ) -> float:
        """
        Advances the front-wheel steer angle by dt applying speed-dependent limits,
        dynamic build-up rate, and auto-centering return torque.
        
        :param current_steer: Current steer angle in radians.
        :param steer_input: Raw steer input in [-1.0, +1.0] (negative = left, positive = right).
        :param speed_px_s: Current longitudinal vehicle speed in px/s.
        :param dt: Time delta in seconds.
        :param wheelbase_px: Wheelbase distance in pixels.
        :param scale_px_per_m: Scale in pixels per meter.
        :param max_speed_px_s: Maximum forward speed in px/s.
        :param config: Steering configuration parameters.
        :return: Updated front wheel steer angle in radians.
        """
        if dt <= 0.0:
            return current_steer

        cfg = config if config is not None else SteeringConfig()
        clamped_input = max(-1.0, min(1.0, steer_input))

        # 1. Compute dynamic maximum steering deflection for current speed
        max_angle = SteeringModel.calculate_max_steer_angle(
            speed_px_s=speed_px_s,
            wheelbase_px=wheelbase_px,
            scale_px_per_m=scale_px_per_m,
            max_speed_px_s=max_speed_px_s,
            config=cfg,
        )

        target_steer = clamped_input * max_angle

        # 2. Apply dynamic build-up rate or self-centering return
        if abs(clamped_input) > 0.01:
            steer_rate = SteeringModel.calculate_steer_rate(
                speed_px_s=speed_px_s,
                max_speed_px_s=max_speed_px_s,
                config=cfg,
            )
            diff = target_steer - current_steer
            max_step = steer_rate * dt
            if abs(diff) <= max_step:
                new_steer = target_steer
            else:
                new_steer = current_steer + math.copysign(max_step, diff)
        else:
            # Self-aligning torque centering when input is released
            max_return = cfg.steer_return_rate * dt
            if abs(current_steer) <= max_return:
                new_steer = 0.0
            else:
                new_steer = current_steer - math.copysign(max_return, current_steer)

        # 3. Dynamic clamp to prevent overshooting speed-dependent boundary
        return max(-max_angle, min(max_angle, new_steer))
