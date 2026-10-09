"""Unit tests and headless verification for simulation Car and World."""

import sys
import pytest

from core.constants import DEFAULT_DT
from core.math2d import LineSegment, Vector2D
from simulation.car import Car
from simulation.track import Track
from simulation.world import World


class TestCar:
    def test_car_initialization(self):
        car = Car.create(
            car_id=1,
            driver_name="Verstappen",
            driver_code="VER",
            spawn_pos=Vector2D(100.0, 200.0),
            spawn_heading=0.5,
            team_color=(10, 20, 100),
        )
        assert car.id == 1
        assert car.driver_name == "Verstappen"
        assert car.driver_code == "VER"
        assert car.team_color == (10, 20, 100)
        assert car.position == Vector2D(100.0, 200.0)
        assert car.heading == 0.5
        assert car.speed == 0.0
        assert car.status == "Running"
        assert car.is_running() is True
        assert car.current_lap == 1
        assert car.lap_time == 0.0

    def test_car_step_and_distance_accumulation(self):
        car = Car.create(spawn_pos=Vector2D(0.0, 0.0), spawn_heading=0.0)
        car.step(throttle_input=1.0, steer_input=0.0, dt=DEFAULT_DT)
        assert car.speed > 0.0
        assert car.total_distance > 0.0
        assert car.lap_distance > 0.0
        assert car.lap_time == pytest.approx(DEFAULT_DT)

    def test_car_crash_and_reset(self):
        car = Car.create(spawn_pos=Vector2D(0.0, 0.0), spawn_heading=0.0)
        car.crash()
        assert car.status == "Out"
        assert car.is_running() is False

        car.reset(Vector2D(50.0, 60.0), 1.0)
        assert car.status == "Running"
        assert car.position == Vector2D(50.0, 60.0)
        assert car.heading == 1.0
        assert car.speed == 0.0
        assert car.current_lap == 1
        assert car.lap_time == 0.0


class TestWorld:
    def test_world_creation(self):
        world = World.create_default()
        assert world.track is not None
        assert len(world.cars) == 1
        assert world.player_car is not None
        assert world.player_car.id == 0
        assert world.time == 0.0
        assert world.tick_count == 0

    def test_world_step_advances_simulation(self):
        world = World.create_default()
        initial_pos = world.player_car.position

        # Accelerate forward for 60 ticks (1 second)
        for _ in range(60):
            world.step(controls=(1.0, 0.0))

        assert world.tick_count == 60
        assert world.time == pytest.approx(1.0)
        assert world.player_car.speed > 100.0
        assert world.player_car.position.x > initial_pos.x
        assert world.player_car.is_running()

    def test_world_barrier_collision_handling(self):
        track = Track.load("apex_valley")
        world = World.create_default(track=track)

        # Move car straight into the barrier at full speed
        # Monaco Turn 1 turns right at x=500. Drive straight past it.
        for _ in range(300):
            world.step(controls=(1.0, 0.0))
            if not world.player_car.is_running():
                break

        assert world.player_car.status == "Out"
        assert world.player_car.speed == 0.0

    def test_world_reset(self):
        world = World.create_default()
        initial_pos = world.player_car.position
        initial_heading = world.player_car.heading
        for _ in range(30):
            world.step(controls=(1.0, 0.0))

        world.reset()
        assert world.time == 0.0
        assert world.tick_count == 0
        assert world.player_car.position == initial_pos
        assert world.player_car.heading == initial_heading
        assert world.player_car.speed == 0.0
        assert world.player_car.status == "Running"

    def test_multi_car_controls(self):
        track = Track.load("apex_valley")
        car1 = Car.create(car_id=1, spawn_pos=track.spawn_position, spawn_heading=0.0)
        car2 = Car.create(car_id=2, spawn_pos=track.spawn_position, spawn_heading=0.0)
        world = World(track=track, cars=[car1, car2])

        # Give car1 full throttle, car2 zero throttle
        world.step(controls={1: (1.0, 0.0), 2: (0.0, 0.0)})
        assert car1.speed > 0.0
        assert car2.speed == 0.0

    def test_zero_pygame_dependency(self):
        """Verifies strictly zero pygame import across core, physics, and simulation in an isolated process."""
        import subprocess

        check_code = (
            "import sys; "
            "import core, physics, simulation; "
            "assert 'pygame' not in sys.modules, f'Pygame was imported by headless layers: {sys.modules.get(\"pygame\")}'"
        )
        res = subprocess.run([sys.executable, "-c", check_code], capture_output=True, text=True)
        assert res.returncode == 0, f"Pygame was imported by headless layers! Error: {res.stderr}"
