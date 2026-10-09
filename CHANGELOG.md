# Changelog

All notable changes to the **EvoLap** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.1] — 2026-10-09

### Added

- **Speed-Dependent Steering Kinematics (`physics/steering.py`)**:
  - `SteeringConfig`: Tunable physical parameters governing dynamic wheel deflection, aerodynamic downforce grip limits, rack resistance build-up rates, and self-aligning torque centering.
  - `SteeringModel`: Kinematic steering engine implementing realistic Formula 1 handling:
    - **Low-speed maneuvering**: Full $0.50\text{ rad}$ ($\sim 28.6^\circ$) steering lock available below $30\text{ km/h}$ for hairpins, chicanes, and tight technical sections.
    - **Aerodynamic high-speed stability**: Maximum front wheel angle continuously constrained by the aerodynamic lateral grip envelope ($a_{\text{lat}} \le 5.2\text{ G}$), tapering to $\sim 1.2^\circ$ at $340\text{ km/h}$. Full $\pm 1.0$ input at top speed produces stable micro-adjustments rather than violent snap oversteer.
    - **Aerodynamic rack resistance**: Dynamic build-up rate scaling inversely with dynamic pressure ($q \propto v^2$), transitioning from fast, agile response ($3.8\text{ rad/s}$) at low speed to progressive, heavily-weighted resistance ($1.6\text{ rad/s}$) at top speed.
    - **Self-aligning torque**: Rapid auto-centering ($5.6\text{ rad/s}$) when steering keys are released, instantly stabilizing the car on corner exits.

### Changed

- **Vehicle Dynamics Integration (`physics/dynamics.py`)**:
  - Updated `VehicleConfig` to incorporate `SteeringConfig`.
  - Refactored `VehicleDynamics.step()` to delegate lateral wheel deflection and rate limiting to `SteeringModel`, maintaining 100% headless determinism and zero Pygame dependencies.
- **Control Input Priority (`simulation/controls.py`, `main.py`)**:
  - Implemented `resolve_control_inputs()` enforcing strict braking precedence over accelerator. If accelerator (`W` / `Up`) and brake (`SPACE` / `S` / `Down`) are held simultaneously, active braking strictly supersedes throttle.

---

## [0.1.0] — 2026-10-09

### Added

- **Core Math Engine (`core/`)**:
  - `Vector2D`: Immutable 2D vector class supporting addition, subtraction, dot product, scalar multiplication, magnitude, distance, normalization, rotation, angle calculation, and perpendicular vectors.
  - `LineSegment`: 2D segment with intersection detection (`intersect`), ray intersection (`intersect_ray`), length, midpoint, and normal calculation.
  - Unit test suite covering all vector math operations, edge cases, collinear segments, parallel lines, and raycasts.

- **Track Representation & Storage (`simulation/track.py`, `storage/tracks/`)**:
  - `Track`: Encapsulates inner/outer barrier boundaries, closed-loop line segments, start/finish line, checkpoints, and starting grid slots.
  - `Track.load(name_or_path)`: Factory to load circuits by name or file path from `storage/tracks/`.
  - `storage/tracks/apex_valley.json`: Grand Prix circuit featuring high-speed straights, left-hand sweepers, an infield chicane, and right-hand technical turns with **zero barrier self-intersections or overlaps** (FIA $\ge 120\text{ px}$ width standard $\approx 17\text{ m}$, 7.0 px/m scale).
  - Raycasting engine against arbitrary barrier geometries for future sensor integration.

- **Vehicle Physics Dynamics (`physics/`)**:
  - `VehicleDynamics`: Longitudinal and lateral kinematics matching realistic Formula 1 scale and resistance:
    - Gradual throttle build-up and top speed calibrated to $340.0\text{ km/h}$.
    - Natural engine drag and rolling resistance deceleration.
    - Reverse gear disabled (`speed >= 0.0`); active braking deceleration via Spacebar / Down / S.
    - Lateral steering response with centering return rate and angular damping.
  - `check_vehicle_barrier_collision`: Oriented bounding box (OBB) 4-segment collision detection against all inner and outer track barrier segments.
  - Collision state handling: Transition to `status = "Out"` on impact, with position frozen and velocity zeroed.

- **Simulation Coordinator (`simulation/`)**:
  - `Car`: Vehicle simulation entity with position, heading, velocity, steer angle, lap counter, lap distance, lap timing, and state resets.
  - `World`: Headless coordinator advancing fixed-timestep ($\Delta t = 1/60\text{ s}$) physics, handling single and multi-car entity collections, lap triggers, and boundary enforcement.
  - **Zero Pygame in Headless Layers**: Strictly verified 100% headless execution with zero display or Pygame dependencies across `core`, `physics`, and `simulation`.

- **Renderer & Cameras (`rendering/`)**:
  - `Renderer`: Pygame-based visual observer with lush green terrain and mower striping, asphalt track surface, 3D Armco barrier rails, and dashed centerline.
  - `Camera`: Coordinate transformation supporting world-to-screen and screen-to-world:
    - **Full-Track Camera**: Auto-fits entire circuit within the viewport.
    - **Follow Camera**: Smoothly tracks the vehicle with velocity lookahead offset, scaled to frame approximately 6 car lengths for high situational awareness.
  - `CarRenderer`: Top-down F1 chassis with steerable front wheels, rear wing, driver cockpit, and team colors.

- **Game Application & Manual Driving (`main.py`)**:
  - Fullscreen display (`F11` toggle).
  - Keyboard driving controls:
    - `W` / `Up Arrow`: Accelerate (capped at $340\text{ km/h}$)
    - `SPACE` / `S` / `Down Arrow`: Active Brake
    - `A` / `Left Arrow`: Steer Left
    - `D` / `Right Arrow`: Steer Right
    - `C`: Toggle Camera Mode (Follow $\leftrightarrow$ Full Track)
    - `R`: Reset Vehicle to Start Line
    - `ESC`: Exit Simulation

- **Testing & Verification**:
  - Reorganized test suite under `tests/core/`, `tests/physics/`, `tests/simulation/`, and `tests/rendering/` (47 passing tests).
  - Deterministic headless physics verification script (`tests/physics/verify_physics_headless.py`).
