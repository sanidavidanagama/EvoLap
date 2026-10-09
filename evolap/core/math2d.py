"""2D Vector and Line Segment geometric primitives for EvoLap."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from evolap.core.constants import EPSILON


@dataclass(frozen=True, slots=True)
class Vector2D:
    """Immutable 2D Cartesian vector."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vector2D) -> Vector2D:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float | int) -> Vector2D:
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float | int) -> Vector2D:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float | int) -> Vector2D:
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if abs(scalar) < EPSILON:
            raise ZeroDivisionError("Cannot divide Vector2D by zero.")
        return Vector2D(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vector2D:
        return Vector2D(-self.x, -self.y)

    def __abs__(self) -> float:
        return self.magnitude()

    def magnitude(self) -> float:
        """Returns the Euclidean norm (length) of the vector."""
        return math.hypot(self.x, self.y)

    def magnitude_squared(self) -> float:
        """Returns the squared Euclidean norm of the vector."""
        return self.x * self.x + self.y * self.y

    @property
    def length(self) -> float:
        """Alias for magnitude."""
        return self.magnitude()

    @property
    def length_squared(self) -> float:
        """Alias for magnitude_squared."""
        return self.magnitude_squared()

    def dot(self, other: Vector2D) -> float:
        """Calculates the dot (scalar) product with another vector."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector2D) -> float:
        """Calculates 2D cross product (perp-dot product): self.x * other.y - self.y * other.x."""
        return self.x * other.y - self.y * other.x

    def normalize(self) -> Vector2D:
        """Returns a unit vector in the same direction, or Vector2D(0, 0) if magnitude is near zero."""
        mag = self.magnitude()
        if mag < EPSILON:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / mag, self.y / mag)

    def distance_to(self, other: Vector2D) -> float:
        """Calculates Euclidean distance to another point/vector."""
        return (self - other).magnitude()

    def distance_squared_to(self, other: Vector2D) -> float:
        """Calculates squared Euclidean distance to another point/vector."""
        return (self - other).magnitude_squared()

    def angle(self) -> float:
        """Returns the angle of the vector in radians relative to positive x-axis [-pi, pi]."""
        return math.atan2(self.y, self.x)

    def rotate(self, angle_rad: float) -> Vector2D:
        """Rotates the vector counter-clockwise by angle_rad radians."""
        cos_theta = math.cos(angle_rad)
        sin_theta = math.sin(angle_rad)
        return Vector2D(
            self.x * cos_theta - self.y * sin_theta,
            self.x * sin_theta + self.y * cos_theta,
        )

    def perpendicular(self) -> Vector2D:
        """Returns a 90-degree counter-clockwise perpendicular vector (-y, x)."""
        return Vector2D(-self.y, self.x)

    def lerp(self, other: Vector2D, t: float) -> Vector2D:
        """Linearly interpolates between self and other by factor t."""
        return Vector2D(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )

    def to_tuple(self) -> Tuple[float, float]:
        """Converts the vector to a float tuple (x, y)."""
        return (self.x, self.y)

    def is_close(self, other: Vector2D, rel_tol: float = 1e-7, abs_tol: float = 1e-9) -> bool:
        """Checks if two vectors are approximately equal within tolerances."""
        return math.isclose(self.x, other.x, rel_tol=rel_tol, abs_tol=abs_tol) and math.isclose(
            self.y, other.y, rel_tol=rel_tol, abs_tol=abs_tol
        )

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float]) -> Vector2D:
        """Creates a Vector2D from a (x, y) tuple."""
        return cls(float(coords[0]), float(coords[1]))

    @classmethod
    def from_angle(cls, angle_rad: float, length: float = 1.0) -> Vector2D:
        """Creates a Vector2D from a given angle and length."""
        return cls(math.cos(angle_rad) * length, math.sin(angle_rad) * length)


@dataclass(frozen=True, slots=True)
class LineSegment:
    """Immutable 2D line segment between start and end vectors."""

    start: Vector2D
    end: Vector2D

    def vector(self) -> Vector2D:
        """Returns displacement vector from start to end (end - start)."""
        return self.end - self.start

    def length(self) -> float:
        """Returns Euclidean length of the segment."""
        return self.vector().magnitude()

    def length_squared(self) -> float:
        """Returns squared Euclidean length of the segment."""
        return self.vector().magnitude_squared()

    def direction(self) -> Vector2D:
        """Returns normalized direction unit vector from start to end."""
        return self.vector().normalize()

    def midpoint(self) -> Vector2D:
        """Returns midpoint of the segment."""
        return Vector2D(
            (self.start.x + self.end.x) * 0.5,
            (self.start.y + self.end.y) * 0.5,
        )

    def normal(self) -> Vector2D:
        """Returns normalized perpendicular vector (left-hand normal)."""
        return self.vector().perpendicular().normalize()

    def intersect(self, other: LineSegment) -> Optional[Vector2D]:
        """
        Determines if this segment intersects another segment.
        Returns the intersection point as Vector2D if intersecting, else None.
        """
        p = self.start
        r = self.vector()
        q = other.start
        s = other.vector()

        r_cross_s = r.cross(s)
        q_minus_p = q - p

        # If r_cross_s is nearly 0, segments are parallel or collinear
        if abs(r_cross_s) < EPSILON:
            return None

        t = q_minus_p.cross(s) / r_cross_s
        u = q_minus_p.cross(r) / r_cross_s

        # Within bounds [0, 1] considering floating point precision
        if -EPSILON <= t <= 1.0 + EPSILON and -EPSILON <= u <= 1.0 + EPSILON:
            clamped_t = max(0.0, min(1.0, t))
            return p + r * clamped_t

        return None

    def intersect_ray(
        self, ray_origin: Vector2D, ray_direction: Vector2D
    ) -> Optional[Tuple[Vector2D, float]]:
        """
        Calculates intersection with a ray originating at ray_origin in direction ray_direction.
        Returns (intersection_point, distance) if intersecting where distance >= 0, else None.
        """
        p = ray_origin
        r = ray_direction
        q = self.start
        s = self.vector()

        r_cross_s = r.cross(s)
        if abs(r_cross_s) < EPSILON:
            return None

        q_minus_p = q - p
        t = q_minus_p.cross(s) / r_cross_s  # Ray parameter: must be >= 0
        u = q_minus_p.cross(r) / r_cross_s  # Segment parameter: must be in [0, 1]

        if t >= -EPSILON and -EPSILON <= u <= 1.0 + EPSILON:
            dist = max(0.0, t)
            intersection_point = p + r * dist
            return (intersection_point, dist)

        return None

    def closest_point(self, point: Vector2D) -> Vector2D:
        """Returns the closest point on the line segment to the given point."""
        v = self.vector()
        len_sq = v.magnitude_squared()
        if len_sq < EPSILON:
            return self.start

        t = (point - self.start).dot(v) / len_sq
        clamped_t = max(0.0, min(1.0, t))
        return self.start + v * clamped_t

    def distance_to_point(self, point: Vector2D) -> float:
        """Calculates the minimum distance from the given point to the line segment."""
        closest = self.closest_point(point)
        return (point - closest).magnitude()
