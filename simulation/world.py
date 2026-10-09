"""Simulation World coordinating physics steps, track boundaries, and vehicle entities."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

from core.constants import DEFAULT_DT
from core.math2d import LineSegment, Vector2D
from physics.collisions import check_vehicle_barrier_collision
from simulation.car import Car
from simulation.track import Track


class World:
    """
    Headless coordinator of the simulation. Holds the track geometry,
    active cars, advances deterministic fixed-timestep physics, and handles
    lap progression and boundary enforcement.
    Strictly decoupled from rendering libraries (zero Pygame).
    """

    def __init__(
        self,
        track: Track,
        cars: Optional[List[Car]] = None,
        dt: float = DEFAULT_DT,
    ) -> None:
        self.track = track
        self.cars: List[Car] = list(cars) if cars is not None else []
        self.dt = dt
        self.time: float = 0.0
        self.tick_count: int = 0

    @classmethod
    def create_default(cls, track: Optional[Track] = None) -> World:
        """Creates a simulation world with a single default player car."""
        trk = track if track is not None else Track.create_monaco_test_circuit()
        player_car = Car.create(
            car_id=0,
            driver_name="Player",
            driver_code="PLY",
            spawn_pos=trk.spawn_position,
            spawn_heading=trk.spawn_heading,
        )
        return cls(track=trk, cars=[player_car])

    @property
    def player_car(self) -> Optional[Car]:
        """Returns the primary (player) car if available."""
        return self.cars[0] if self.cars else None

    def add_car(self, car: Car) -> None:
        """Adds a car entity to the simulation."""
        self.cars.append(car)

    def get_car(self, car_id: int) -> Optional[Car]:
        """Finds and returns car by ID."""
        for car in self.cars:
            if car.id == car_id:
                return car
        return None

    def step(
        self,
        controls: Optional[Union[Tuple[float, float], Dict[int, Tuple[float, float]]]] = None,
    ) -> None:
        """
        Advances the simulation world by one tick (dt).
        
        :param controls: Either a tuple of (throttle, steer) for the primary car,
                         or a dict mapping car_id -> (throttle, steer).
        """
        # Parse control inputs
        ctrl_map: Dict[int, Tuple[float, float]] = {}
        if isinstance(controls, tuple) and self.cars:
            ctrl_map[self.cars[0].id] = controls
        elif isinstance(controls, dict):
            ctrl_map = controls

        for car in self.cars:
            if not car.is_running():
                continue

            throttle, steer = ctrl_map.get(car.id, (0.0, 0.0))
            prev_pos = car.position

            # 1. Advance vehicle physics
            car.step(throttle, steer, self.dt)

            # 2. Check collision against track barriers
            collided, _ = check_vehicle_barrier_collision(
                car.state, self.track, prev_pos, car.config
            )
            if collided:
                continue

            # 3. Checkpoint and Lap Progression
            move_seg = LineSegment(prev_pos, car.position)
            self._update_car_lap_progression(car, move_seg)

        self.time += self.dt
        self.tick_count += 1

    def _update_car_lap_progression(self, car: Car, move_seg: LineSegment) -> None:
        """Evaluates checkpoint gating and lap completions."""
        total_cps = len(self.track.checkpoints)

        # Check next checkpoint in order
        if total_cps > 0:
            next_cp_idx = car.last_checkpoint_index + 1
            if next_cp_idx < total_cps:
                next_cp = self.track.checkpoints[next_cp_idx]
                if next_cp.intersect(move_seg) is not None:
                    car.last_checkpoint_index = next_cp_idx

        # Check start/finish line crossing
        fl_hit = self.track.finish_line.intersect(move_seg)
        if fl_hit is not None:
            # Require having passed all checkpoints if checkpoints exist
            valid_lap = (total_cps == 0) or (car.last_checkpoint_index >= total_cps - 1)
            if valid_lap:
                if car.lap_time > 1.0:  # Prevent immediate double trigger on spawn line
                    if car.best_lap_time is None or car.lap_time < car.best_lap_time:
                        car.best_lap_time = car.lap_time
                    car.current_lap += 1
                    car.last_checkpoint_index = -1
                    car.lap_distance = 0.0
                    car.lap_time = 0.0

    def reset(self) -> None:
        """Resets all cars to spawn positions and restarts world timer."""
        for i, car in enumerate(self.cars):
            if i < len(self.track.grid_slots):
                spawn_pos, spawn_h = self.track.grid_slots[i]
            else:
                spawn_pos = self.track.spawn_position
                spawn_h = self.track.spawn_heading
            car.reset(spawn_pos, spawn_h)

        self.time = 0.0
        self.tick_count = 0
