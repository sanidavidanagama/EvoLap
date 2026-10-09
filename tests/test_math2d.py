"""Unit tests for evolap.core.math2d module (Vector2D and LineSegment)."""

import math
import pytest

from core.math2d import LineSegment, Vector2D


class TestVector2D:
    def test_initialization_and_properties(self):
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0
        assert v.to_tuple() == (3.0, 4.0)
        assert v.magnitude() == pytest.approx(5.0)
        assert v.length == pytest.approx(5.0)
        assert v.magnitude_squared() == pytest.approx(25.0)
        assert v.length_squared == pytest.approx(25.0)
        assert abs(v) == pytest.approx(5.0)

    def test_default_values(self):
        v = Vector2D()
        assert v.x == 0.0
        assert v.y == 0.0

    def test_from_tuple_and_from_angle(self):
        v1 = Vector2D.from_tuple((1.5, -2.5))
        assert v1.x == 1.5
        assert v1.y == -2.5

        v2 = Vector2D.from_angle(math.pi / 2, length=2.0)
        assert v2.x == pytest.approx(0.0, abs=1e-7)
        assert v2.y == pytest.approx(2.0)

    def test_addition_and_subtraction(self):
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, -1.0)
        sum_v = v1 + v2
        diff_v = v1 - v2
        assert sum_v == Vector2D(4.0, 1.0)
        assert diff_v == Vector2D(-2.0, 3.0)

    def test_scalar_multiplication_and_division(self):
        v = Vector2D(2.0, -3.0)
        assert v * 2 == Vector2D(4.0, -6.0)
        assert 3 * v == Vector2D(6.0, -9.0)
        assert v / 2 == Vector2D(1.0, -1.5)

        with pytest.raises(ZeroDivisionError):
            _ = v / 0.0

    def test_negation(self):
        v = Vector2D(5.0, -7.0)
        assert -v == Vector2D(-5.0, 7.0)

    def test_dot_and_cross_product(self):
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        assert v1.dot(v2) == 0.0
        assert v1.cross(v2) == 1.0  # 1*1 - 0*0 = 1
        assert v2.cross(v1) == -1.0

        v3 = Vector2D(2.0, 3.0)
        v4 = Vector2D(4.0, 5.0)
        assert v3.dot(v4) == 2.0 * 4.0 + 3.0 * 5.0  # 23
        assert v3.cross(v4) == 2.0 * 5.0 - 3.0 * 4.0  # -2

    def test_normalize(self):
        v = Vector2D(3.0, 4.0)
        normalized = v.normalize()
        assert normalized.magnitude() == pytest.approx(1.0)
        assert normalized.x == pytest.approx(0.6)
        assert normalized.y == pytest.approx(0.8)

        # Zero vector normalization should safely return Vector2D(0, 0)
        zero = Vector2D(0.0, 0.0)
        assert zero.normalize() == Vector2D(0.0, 0.0)

    def test_distance(self):
        p1 = Vector2D(0.0, 0.0)
        p2 = Vector2D(3.0, 4.0)
        assert p1.distance_to(p2) == pytest.approx(5.0)
        assert p1.distance_squared_to(p2) == pytest.approx(25.0)

    def test_angle_and_rotation(self):
        v = Vector2D(1.0, 0.0)
        assert v.angle() == pytest.approx(0.0)

        rotated_90 = v.rotate(math.pi / 2)
        assert rotated_90.is_close(Vector2D(0.0, 1.0))
        assert rotated_90.angle() == pytest.approx(math.pi / 2)

        rotated_180 = v.rotate(math.pi)
        assert rotated_180.is_close(Vector2D(-1.0, 0.0))

    def test_perpendicular(self):
        v = Vector2D(1.0, 0.0)
        perp = v.perpendicular()
        assert perp == Vector2D(0.0, 1.0)
        assert v.dot(perp) == 0.0

    def test_lerp(self):
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(10.0, 20.0)
        assert v1.lerp(v2, 0.0) == v1
        assert v1.lerp(v2, 1.0) == v2
        assert v1.lerp(v2, 0.5) == Vector2D(5.0, 10.0)

    def test_is_close(self):
        v1 = Vector2D(1.0000000001, 2.0)
        v2 = Vector2D(1.0, 2.0000000001)
        assert v1.is_close(v2, rel_tol=1e-6)
        assert not v1.is_close(Vector2D(1.1, 2.0))


class TestLineSegment:
    def test_properties(self):
        seg = LineSegment(Vector2D(0.0, 0.0), Vector2D(4.0, 3.0))
        assert seg.vector() == Vector2D(4.0, 3.0)
        assert seg.length() == pytest.approx(5.0)
        assert seg.length_squared() == pytest.approx(25.0)
        assert seg.direction().is_close(Vector2D(0.8, 0.6))
        assert seg.midpoint() == Vector2D(2.0, 1.5)

        # Normal vector should be perpendicular and unit length
        normal = seg.normal()
        assert normal.magnitude() == pytest.approx(1.0)
        assert normal.dot(seg.direction()) == pytest.approx(0.0)

    def test_intersection_crossing(self):
        # Two crossing segments forming an X
        seg1 = LineSegment(Vector2D(-2.0, 0.0), Vector2D(2.0, 0.0))
        seg2 = LineSegment(Vector2D(0.0, -2.0), Vector2D(0.0, 2.0))
        pt = seg1.intersect(seg2)
        assert pt is not None
        assert pt.is_close(Vector2D(0.0, 0.0))

    def test_intersection_at_endpoint(self):
        seg1 = LineSegment(Vector2D(0.0, 0.0), Vector2D(2.0, 0.0))
        seg2 = LineSegment(Vector2D(2.0, 0.0), Vector2D(2.0, 2.0))
        pt = seg1.intersect(seg2)
        assert pt is not None
        assert pt.is_close(Vector2D(2.0, 0.0))

    def test_no_intersection_disjoint(self):
        seg1 = LineSegment(Vector2D(0.0, 0.0), Vector2D(2.0, 0.0))
        seg2 = LineSegment(Vector2D(0.0, 1.0), Vector2D(2.0, 1.0))  # Parallel
        assert seg1.intersect(seg2) is None

        seg3 = LineSegment(Vector2D(3.0, 0.0), Vector2D(5.0, 0.0))  # Collinear disjoint
        assert seg1.intersect(seg3) is None

        seg4 = LineSegment(Vector2D(5.0, 5.0), Vector2D(6.0, 6.0))  # Completely separate
        assert seg1.intersect(seg4) is None

    def test_intersect_ray(self):
        seg = LineSegment(Vector2D(5.0, -2.0), Vector2D(5.0, 2.0))

        # Ray pointing directly at segment from origin
        res = seg.intersect_ray(Vector2D(0.0, 0.0), Vector2D(1.0, 0.0))
        assert res is not None
        hit_point, dist = res
        assert hit_point.is_close(Vector2D(5.0, 0.0))
        assert dist == pytest.approx(5.0)

        # Ray pointing away from segment
        res_away = seg.intersect_ray(Vector2D(0.0, 0.0), Vector2D(-1.0, 0.0))
        assert res_away is None

        # Ray parallel to segment
        res_parallel = seg.intersect_ray(Vector2D(0.0, 0.0), Vector2D(0.0, 1.0))
        assert res_parallel is None

    def test_closest_point_and_distance(self):
        seg = LineSegment(Vector2D(0.0, 0.0), Vector2D(10.0, 0.0))

        # Point above middle
        pt_mid = Vector2D(5.0, 3.0)
        assert seg.closest_point(pt_mid) == Vector2D(5.0, 0.0)
        assert seg.distance_to_point(pt_mid) == pytest.approx(3.0)

        # Point beyond start
        pt_before = Vector2D(-2.0, 3.0)
        assert seg.closest_point(pt_before) == Vector2D(0.0, 0.0)
        assert seg.distance_to_point(pt_before) == pytest.approx(math.hypot(2.0, 3.0))

        # Point beyond end
        pt_after = Vector2D(14.0, -3.0)
        assert seg.closest_point(pt_after) == Vector2D(10.0, 0.0)
        assert seg.distance_to_point(pt_after) == pytest.approx(5.0)
