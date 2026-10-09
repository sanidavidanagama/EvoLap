"""Physics dynamics and collision detection engine for EvoLap."""

from physics.collisions import (
    check_vehicle_barrier_collision,
    get_vehicle_bounding_segments,
    get_vehicle_corners,
)
from physics.dynamics import VehicleConfig, VehicleDynamics, VehicleState
from physics.steering import SteeringConfig, SteeringModel

__all__ = [
    "VehicleConfig",
    "VehicleState",
    "VehicleDynamics",
    "SteeringConfig",
    "SteeringModel",
    "get_vehicle_corners",
    "get_vehicle_bounding_segments",
    "check_vehicle_barrier_collision",
]
