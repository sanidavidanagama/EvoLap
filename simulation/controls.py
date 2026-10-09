"""Control input resolution and safety invariants for EvoLap."""

from __future__ import annotations

from typing import Tuple


def resolve_control_inputs(
    is_accelerating: bool,
    is_braking: bool,
    steer_left: bool,
    steer_right: bool,
) -> Tuple[float, float]:
    """
    Resolves raw user or AI boolean input states into normalized (throttle, steer) control values.

    Safety Invariant:
    Active braking strictly supersedes acceleration when both are simultaneously active.
    """
    if is_braking:
        throttle = -1.0  # Active braking takes strict priority over acceleration
    elif is_accelerating:
        throttle = 1.0
    else:
        throttle = 0.0

    steer = 0.0
    if steer_left:
        steer -= 1.0
    if steer_right:
        steer += 1.0

    return (throttle, steer)
