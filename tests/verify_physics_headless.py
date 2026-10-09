import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.constants import DEFAULT_DT
from core.math2d import Vector2D
from physics.collisions import check_vehicle_barrier_collision
from physics.dynamics import VehicleDynamics, VehicleState
from simulation.track import Track


def run_headless_simulation():
    print("=" * 60)
    print("EvoLap Headless Physics Verification")
    print("=" * 60)

    track = Track.create_monaco_test_circuit()
    state = VehicleState(position=track.spawn_position, heading=track.spawn_heading)

    print(f"Track: {track.name}")
    print(f"Spawn Pos: ({state.position.x:.1f}, {state.position.y:.1f}), Heading: {state.heading:.2f} rad")
    print(f"Initial Status: {state.status}, Speed: {state.speed:.1f} px/s\n")

    # Phase 1: Full acceleration (1 second = 60 ticks)
    print(">> Phase 1: Accelerating forward (60 ticks @ throttle = 1.0)...")
    for _ in range(60):
        VehicleDynamics.step(state, throttle_input=1.0, steer_input=0.0, dt=DEFAULT_DT)
    print(f"   After 1.0s -> Speed: {state.speed:.1f} px/s, Pos: ({state.position.x:.1f}, {state.position.y:.1f})")
    assert state.speed > 100.0, "Car should have gained speed"

    # Phase 2: Turning right (60 ticks @ throttle = 0.8, steer = 0.5)
    print(">> Phase 2: Steer right through corner (60 ticks @ steer = 0.5)...")
    initial_heading = state.heading
    for _ in range(60):
        VehicleDynamics.step(state, throttle_input=0.8, steer_input=0.5, dt=DEFAULT_DT)
    print(f"   After turn -> Heading: {state.heading:.2f} rad (delta: {state.heading - initial_heading:.2f})")
    assert state.heading != initial_heading, "Heading should have rotated"

    # Phase 3: Off-throttle engine braking to complete stop
    print(">> Phase 3: Off-throttle deceleration / engine braking...")
    speed_before = state.speed
    # Coast for 60 ticks (1s) and check gradual deceleration
    for _ in range(60):
        VehicleDynamics.step(state, throttle_input=0.0, steer_input=0.0, dt=DEFAULT_DT)
    print(f"   After 1s coasting -> Speed: {state.speed:.1f} px/s (down from {speed_before:.1f} px/s)")
    assert state.speed < speed_before, "Car should gradually decelerate under engine drag"

    # Coast until complete stop
    ticks = 0
    while state.speed > 0.0 and ticks < 300:
        VehicleDynamics.step(state, throttle_input=0.0, steer_input=0.0, dt=DEFAULT_DT)
        ticks += 1
    print(f"   Car brought to complete stop after {ticks} additional ticks -> Speed: {state.speed:.1f} px/s")
    assert state.speed == 0.0, "Car should come to a complete stop under engine drag"

    # Phase 4: Barrier collision check
    print(">> Phase 4: Simulating barrier collision & crash transition...")
    state.position = track.inner_segments[0].midpoint()
    collided, hit = check_vehicle_barrier_collision(state, track)
    assert collided and state.status == "Out", "Collision must trigger Out state"
    print(f"   Collision registered at {hit.to_tuple() if hit else 'None'} -> Status: {state.status}")

    # Phase 5: Reset
    print(">> Phase 5: Resetting car...")
    state.reset(track.spawn_position, track.spawn_heading)
    assert state.status == "Running" and state.speed == 0.0, "Reset must restore vehicle"
    print(f"   Vehicle reset successful -> Status: {state.status}, Pos: {state.position.to_tuple()}")

    print("\n[SUCCESS] Headless physics verification passed completely with 0 Pygame dependencies.")


if __name__ == "__main__":
    run_headless_simulation()
