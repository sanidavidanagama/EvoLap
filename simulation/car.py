"""Car entity container managing vehicle state, lap metrics, and driver metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from core.constants import DEFAULT_DT
from core.math2d import Vector2D
from physics.dynamics import VehicleConfig, VehicleDynamics, VehicleState


@dataclass
class Car:
    """
    Physical vehicle entity combining physics state, configuration,
    lap timing / progression metrics, and driver metadata.
    Zero Pygame dependency.
    """

    id: int = 0
    driver_name: str = "Player"
    driver_code: str = "PLY"
    team_color: Tuple[int, int, int] = (220, 30, 30)  # Default F1 red
    state: VehicleState = field(default_factory=lambda: VehicleState(position=Vector2D(0.0, 0.0)))
    config: VehicleConfig = field(default_factory=VehicleConfig)

    # Lap progression and timing
    current_lap: int = 1
    total_distance: float = 0.0
    lap_distance: float = 0.0
    last_checkpoint_index: int = -1
    lap_time: float = 0.0
    best_lap_time: Optional[float] = None

    @classmethod
    def create(
        cls,
        car_id: int = 0,
        driver_name: str = "Player",
        driver_code: str = "PLY",
        spawn_pos: Optional[Vector2D] = None,
        spawn_heading: float = 0.0,
        team_color: Tuple[int, int, int] = (220, 30, 30),
        config: Optional[VehicleConfig] = None,
    ) -> Car:
        """Convenience factory method to instantiate a car at a specific spawn transform."""
        pos = spawn_pos if spawn_pos is not None else Vector2D(0.0, 0.0)
        state = VehicleState(position=pos, heading=spawn_heading)
        cfg = config if config is not None else VehicleConfig()
        return cls(
            id=car_id,
            driver_name=driver_name,
            driver_code=driver_code,
            team_color=team_color,
            state=state,
            config=cfg,
        )

    @property
    def position(self) -> Vector2D:
        return self.state.position

    @property
    def heading(self) -> float:
        return self.state.heading

    @property
    def speed(self) -> float:
        return self.state.speed

    @property
    def velocity(self) -> Vector2D:
        return self.state.velocity

    @property
    def steer_angle(self) -> float:
        return self.state.steer_angle

    @property
    def status(self) -> str:
        return self.state.status

    def is_running(self) -> bool:
        return self.state.is_running()

    def step(self, throttle_input: float, steer_input: float, dt: float = DEFAULT_DT) -> None:
        """Advances vehicle dynamics for this car by dt."""
        VehicleDynamics.step(self.state, throttle_input, steer_input, dt, self.config)
        dist_moved = abs(self.state.speed) * dt
        self.total_distance += dist_moved
        self.lap_distance += dist_moved
        self.lap_time += dt

    def crash(self) -> None:
        """Transitions car to crashed state."""
        self.state.crash()

    def reset(self, spawn_position: Vector2D, spawn_heading: float) -> None:
        """Resets physical state and lap tracking metrics."""
        self.state.reset(spawn_position, spawn_heading)
        self.current_lap = 1
        self.total_distance = 0.0
        self.lap_distance = 0.0
        self.last_checkpoint_index = -1
        self.lap_time = 0.0
