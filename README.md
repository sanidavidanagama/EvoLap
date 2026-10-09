# EvoLap — Formula 1 Simulation & AI Driving Laboratory

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Engine](https://img.shields.io/badge/physics-headless_deterministic-orange.svg)](#architecture)
[![Renderer](https://img.shields.io/badge/rendering-pygame--ce_2.5.8-green.svg)](https://pyga.me/)
[![Tests](https://img.shields.io/badge/tests-56_passing-brightgreen.svg)](#testing)
[![Version](https://img.shields.io/badge/version-v0.1.1-purple.svg)](pyproject.toml)

**EvoLap** is a modular, high-performance 2D Formula 1 simulation and evolutionary AI driving laboratory. Built on strictly decoupled engines, EvoLap models physical F1 vehicle dynamics, closed-loop track geometries, and real-time visualization, laying the foundation for future autonomous genetic algorithm neural network training.

---

## Current Release: v0.1.1

- **Interactive Manual Driving**: Drive a Formula 1 car around the technical **Apex Valley Circuit**.
- **F1 Kinematics & Powertrain**: Realistic acceleration, rolling friction, aerodynamic air drag, and natural engine braking calibrated to a top speed of **$340.0\text{ km/h}$**.
- **Smooth Speed-Dependent Steering**: Front-wheel steering deflection is dynamically constrained by the aerodynamic lateral grip envelope ($a_{\text{lat}} \le 5.2\text{ G}$) and weighted by aerodynamic rack resistance. Low speeds retain full $28.6^\circ$ steering lock for sharp hairpins; high speeds provide stable micro-adjustments without snap oversteer.
- **Braking Safety Invariant**: Dedicated active braking (Spacebar / S / Down Arrow) strictly supersedes the accelerator when both keys are pressed simultaneously. Reverse gear is disabled (`speed >= 0.0`).
- **Apex Valley Circuit (`storage/tracks/apex_valley.json`)**: Grand Prix circuit with 120px FIA track width standard ($\approx 17\text{ m}$), zero barrier overlap, left/right corners, high-speed straights, an infield chicane, 20 staggered starting grid slots, and 24 lap timing checkpoints.
- **Dual Camera System**: Toggle seamlessly between **Full-Track Camera** (framing entire circuit) and **Follow Camera** (smooth tracking with forward velocity lookahead).
- **Zero Pygame Headless Decoupling**: Physics, math, and simulation layers operate 100% headlessly with zero Pygame dependencies, verified by automated unit tests.
- **Standalone Executable Deployment**: Packaged into a standalone Windows `.exe` for instant launch without requiring Python or terminal setup.

---

## Controls

| Key | Action | Behavior |
| :--- | :--- | :--- |
| **`W`** / **`Up Arrow`** | Accelerate | Smooth longitudinal acceleration (capped at $340\text{ km/h}$) |
| **`SPACE`** / **`S`** / **`Down Arrow`** | Active Brake | Rapid deceleration down to $0.0\text{ km/h}$ (**Strict priority over gas**) |
| **`A`** / **`Left Arrow`** | Steer Left | Dynamic speed-scaled front wheel turning |
| **`D`** / **`Right Arrow`** | Steer Right | Dynamic speed-scaled front wheel turning |
| **`C`** | Toggle Camera | Switch between **Follow Camera** $\longleftrightarrow$ **Full-Track Camera** |
| **`R`** | Reset Vehicle | Teleports vehicle to start line in running state |
| **`F11`** | Fullscreen Toggle | Toggles borderless fullscreen display |
| **`ESC`** | Exit Game | Clean shutdown |

---

## Quickstart & How to Run

### Option 1: Run with `uv` (Recommended for Development)

Prerequisites: Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```powershell
# Clone the repository
git clone https://github.com/sanidavidanagama/EvoLap.git
cd EvoLap

# Run the simulation game directly
uv run main.py
```

### Option 2: Run Standalone Executable (.exe)

You can launch the compiled standalone game without needing Python or uv installed:

```powershell
# Run the built standalone executable
.\dist\EvoLap\EvoLap.exe
```

To build a fresh executable yourself:
```powershell
uv run pyinstaller --noconfirm --onedir --name "EvoLap" --add-data "storage;storage" main.py
```

---

## Project Architecture

EvoLap enforces strict architectural boundaries:

$$\text{Track Geometry} \longrightarrow \text{Simulation World} \longrightarrow \text{Physics Engine} \longrightarrow \text{Car State} \xrightarrow{\text{reads}} \text{Renderer (Pygame)}$$

```
EvoLap/
├── core/                  # Immutable 2D math (Vector2D, LineSegment) - Zero external dependencies
├── physics/               # Vehicle dynamics, kinematic bicycle model, speed steering, collisions
│   ├── dynamics.py        # Longitudinal powertrain, rolling drag, yaw rate, position integration
│   ├── steering.py        # F1 speed-dependent steering limits, rack resistance, auto-centering
│   └── collisions.py      # 4-segment OBB barrier collision detection
├── simulation/            # Simulation state container and headless coordinator
│   ├── track.py           # Track boundaries, barrier loops, checkpoints, Track.load() factory
│   ├── car.py             # Car entity container with lap counters and timing
│   ├── controls.py        # Control input resolution (brake priority invariant)
│   └── world.py           # Fixed-timestep (dt=1/60s) headless simulation coordinator
├── rendering/             # Visual observer layer (Pygame-ce)
│   ├── renderer.py        # Visual frame compositor with grass striping, asphalt, Armco barriers
│   ├── camera.py          # World-to-screen coordinate transforms, Follow & Full-Track modes
│   ├── car_view.py        # Top-down F1 chassis with steerable wheels and wings
│   └── track_view.py      # Asphalt polygon rasterization, kerbs, and barrier rails
├── storage/               # Persistent track data, model weights, and checkpoints
│   └── tracks/            # JSON circuit definitions (e.g. apex_valley.json)
├── tests/                 # Comprehensive test suite mirroring source architecture
│   ├── core/              # Unit tests for Vector2D and LineSegment
│   ├── physics/           # Unit tests for dynamics, steering kinematics, collisions, determinism
│   ├── simulation/        # Unit tests for Track, Car, World, and control priority
│   └── rendering/         # Unit tests for Camera coordinate transformations
├── docs/                  # Architectural specs, milestones, and version roadmap
└── main.py                # Main application loop assembling Input -> World -> Renderer
```

### Key Invariants
1. **Headless Decoupling**: Modules `core/`, `physics/`, `simulation/`, and future `neural_engine/` **never import `pygame` or `rendering`**. Every simulation step can be executed headlessly in high-throughput training batches.
2. **Simulation is Single Source of Truth**: The renderer is strictly an **observer**; it reads state to draw visuals and never mutates physics.

---

## Testing & Quality Gates

The test suite runs with pytest and covers 100% of mathematical, physical, and simulation invariants:

```powershell
# Run all unit tests
uv run pytest

# Run headless deterministic physics verification (0 Pygame imports)
python tests/physics/verify_physics_headless.py
```

All **56 unit tests** verify:
- Vector arithmetic, raycasting, and line intersections.
- Speed-dependent steering deflection, monotonic angle decay, and rack resistance.
- Active braking priority, reverse motion prohibition, and top speed capping ($340\text{ km/h}$).
- Barrier collision detection and transition to `status = "Out"`.
- Isolated headless verification proving zero Pygame imports in backend layers.

---

## Version Roadmap

- [x] **v0.1.0** — Basic Simulation, Manual Driving, Monaco & Apex Valley Tracks, Fullscreen Pygame Visualizer
- [x] **v0.1.1** — Smooth Speed-Dependent Steering (F1 Kinematics), Rack Resistance, Brake Priority
- [ ] **v0.1.2** — Damage & Impact Degradation System (Progressive chassis penalty vs binary elimination)
- [ ] **v0.2.0** — Neural Engine (MLP forward pass, 7-raycast perception, 20 AI cars, standings UI)
- [ ] **v0.3.0** — Evolutionary Genetic Training System (Try-fail-learn generation cycles, visual/headless modes)
- [ ] **v0.4.0** — Main Menu & The Laboratory (Track registry, model archive, generation resume)

---

## License

This project is licensed under the MIT License.
