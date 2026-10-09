"""Vehicle chassis bounding geometry and track barrier collision detection."""

from __future__ import annotations

from typing import List, Optional, Tuple

from core.math2d import LineSegment, Vector2D
from physics.dynamics import VehicleConfig, VehicleState
from simulation.track import Track


def get_vehicle_corners(
    position: Vector2D,
    heading: float,
    length: float,
    width: float,
) -> Tuple[Vector2D, Vector2D, Vector2D, Vector2D]:
    """
    Computes 4 corner vertices of the vehicle chassis in world coordinates:
    (front_left, front_right, rear_right, rear_left).
    """
    fwd = Vector2D.from_angle(heading)
    lat = fwd.perpendicular()  # Left-pointing normal

    half_len = length * 0.5
    half_wid = width * 0.5

    fl = position + fwd * half_len + lat * half_wid
    fr = position + fwd * half_len - lat * half_wid
    rr = position - fwd * half_len - lat * half_wid
    rl = position - fwd * half_len + lat * half_wid

    return fl, fr, rr, rl


def get_vehicle_bounding_segments(
    position: Vector2D,
    heading: float,
    config: VehicleConfig = VehicleConfig(),
) -> List[LineSegment]:
    """Returns the 4 perimeter line segments forming the vehicle chassis boundary."""
    fl, fr, rr, rl = get_vehicle_corners(position, heading, config.length, config.width)
    return [
        LineSegment(fl, fr),  # Front bumper
        LineSegment(fr, rr),  # Right side
        LineSegment(rr, rl),  # Rear bumper
        LineSegment(rl, fl),  # Left side
    ]


def check_vehicle_barrier_collision(
    state: VehicleState,
    track: Track,
    prev_position: Optional[Vector2D] = None,
    config: Optional[VehicleConfig] = None,
) -> Tuple[bool, Optional[Vector2D]]:
    """
    Checks if the vehicle perimeter or its displacement vector intersects any track barrier.
    If a collision occurs and the vehicle is running, transitions vehicle status to 'Out'.
    
    :param state: Mutable vehicle state.
    :param track: Track containing barrier segments.
    :param prev_position: Optional position before last step (prevents tunneling at high speed).
    :param config: Vehicle dimensions configuration.
    :return: (is_collided, collision_point)
    """
    if not state.is_running():
        return False, None

    cfg = config if config is not None else VehicleConfig()

    # 1. Check displacement vector to prevent tunneling
    if prev_position is not None and prev_position.distance_to(state.position) > 1e-4:
        travel_seg = LineSegment(prev_position, state.position)
        hit = track.check_collision(travel_seg)
        if hit is not None:
            state.crash()
            return True, hit

    # 2. Check 4 perimeter segments of the chassis
    chassis_segs = get_vehicle_bounding_segments(state.position, state.heading, cfg)
    for seg in chassis_segs:
        hit = track.check_collision(seg)
        if hit is not None:
            state.crash()
            return True, hit

    return False, None
