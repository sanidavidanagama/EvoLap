"""Core geometric primitives, vector math, and constants."""

from evolap.core.constants import (
    DEFAULT_DT,
    DEG_TO_RAD,
    EPSILON,
    KMH_TO_MPS,
    MPS_TO_KMH,
    RAD_TO_DEG,
)
from evolap.core.math2d import LineSegment, Vector2D

__all__ = [
    "DEFAULT_DT",
    "EPSILON",
    "MPS_TO_KMH",
    "KMH_TO_MPS",
    "RAD_TO_DEG",
    "DEG_TO_RAD",
    "Vector2D",
    "LineSegment",
]
