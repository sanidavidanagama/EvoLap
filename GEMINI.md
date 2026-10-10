# EvoLap — Agent Development Guide & Constraints (GEMINI.md)

Welcome to **EvoLap**. This document contains mandatory architectural invariants, workflows, and constraints that every agent and contributor must follow.

---

## Active Milestone (Read This First)

- **Currently Developing Milestone**: [`docs/milestones/v0.1.1-smooth-steering.md`](file:///c:/Users/sanid/VS%20Code%20Projects/EvoLap/docs/milestones/v0.1.1-smooth-steering.md)
- **Scope Rule**: Strictly adhere to the checklist in the active milestone document. **Do not implement features belonging to future milestones** (e.g., do not add neural networks, sidebars, or genetic algorithms during v0.1.1).

---

## Documentation Index

Before coding or proposing architectural modifications, consult the relevant documentation:
- **System Architecture**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Engine boundaries, headless decoupling, data flow.
- **Technical Specification**: [`docs/SPEC.md`](docs/SPEC.md) — Neural net architecture, 7-input raycast angles, car physics, UI specs.
- **Version Roadmap**: [`docs/ROADMAP.md`](docs/ROADMAP.md) — High-level milestone trajectory (v0.1.0 to v2.0.0).
- **Milestone Breakdown**: [`docs/milestones/`](docs/milestones/) — Specific task checklists per version.

---

## Core Architectural Invariants

### 1. Simulation is the Single Source of Truth
$$\text{Track Geometry} \to \text{Simulation World} \to \text{Physics Engine} \to \text{Car State} \xrightarrow{\text{reads}} \text{Renderer (Pygame)}$$
- The physics and simulation engines determine physical truth.
- The renderer and UI are strictly **observers**. They read state to draw graphics and must **never** mutate physics or car state.

### 2. Zero Pygame in Headless Layers (Strict Decoupling)
- The following modules must **NEVER import `pygame` or `rendering`**:
  - `core/`
  - `physics/`
  - `simulation/`
  - `neural_engine/`
  - `training/`
- Every simulation step must be executable in a pure console script without launching an OS window or initializing display drivers.

### 3. Neural Engine is an Independent Sub-Product
- Located in `neural_engine/`.
- Designed as a standalone, scalable sub-product with independent semantic subversioning (e.g., `Neural Engine v1.0.0`).
- Operates on pure NumPy for vector math and neural inference.

### 4. Storage Structure Standards
The persistence engine (`storage/`) must strictly preserve three dedicated directories:
- `storage/models/`: Serialized neural network weights and model metadata.
- `storage/tracks/`: Track coordinates, barrier line segments, and checkpoint data. (eg: `tracks/barcelona.json`)
- `storage/training/checkpoints/`: Generational checkpoints, population DNA, and training history logs.

### 5. Vehicle Scale & Physics Invariants
- **Scale Standard**: 7.0 pixels per meter (F1 car length ~38px $\approx 5.4$m, width ~14px $\approx 2.0$m).
- **Track Width Standard**: $\ge 120$px ($\sim 17$m FIA standard) allowing multiple cars to race side-by-side.
- **Speed Limits**: Configurable `top_speed_kmh = 340.0`. Speed must be capped and calibrated to realistic F1 velocity (never exceeding configured top speed).
- **Controls**: Reverse is disabled (speed strictly $\ge 0.0$). Spacebar and Down/S are dedicated to active braking.

---

## Milestone Evolution & Backlog Notes

### Completed in v0.1.1:
- **Smooth Speed-Dependent Steering (F1 Kinematics)**: Full steering lock at low speeds tapering down to micro-adjustments at top speed.
- **Active Brake Priority**: Dedicated braking input strictly prioritized over throttle.
- **Branding & Standalone Build**: Added custom favicon application icons and standalone executable compilation script (`scripts/build.py`).
- **CI Pipeline Streamlining & Release Separation**:
  - Restructured `.github/workflows/ci.yml` into a lightweight, fast Ubuntu test runner (<30s runtime).
  - Added concurrency cancellation (`cancel-in-progress: true`) and doc change filtering (`paths-ignore`).
  - Separated executable compilation into a dedicated tag-triggered `release.yml` (`v*`) to eliminate redundant matrix and Windows runner queue consumption across routine dev pushes and PRs.

### Planned for v0.1.2+:
- **Damage & Impact Degradation System**: Progressive wing/chassis degradation, speed penalties, and collision restitution replacing instantaneous binary elimination (`status = "Out"`).

### Planned for v0.2.0 (Neural Engine & Multi-Car Simulation):
- Multi-car starting grid (F1 zig-zag staggered placement).
- 5-raycast sensor perception vector ($D_1 \dots D_5$) + speed + heading.
- MLP forward pass inference per car per tick (434 weights).
- Standings and Telemetry UI overlays.

---

## Git & Versioning Workflow

### 1. Protected Main Branch
- `main` is protected and represents live, tested, and releasable code.
- **NEVER commit or push code directly to `main`**.
- Staging and Development  environment is `dev`.
- All work must be conducted on feature branches and merged via clean commits / PRs once verified.

### 2. Feature-Based Branch Naming
- Do **NOT** use version numbers in branch names (e.g., avoid `v0.1.0-branch`).
- Use descriptive feature names:
  - Format: `feature/<feature-description>`
  - Example for v0.1.0: `feature/basic-sim`
- If a submilestone requires its own isolated branch due to complexity, branch off the feature branch:
  - Example: `feature/basic-sim/physics-kinematics`

### 3. Version Tracking in `pyproject.toml`
- Update the `version` field in [`pyproject.toml`](/pyproject.toml) whenever a milestone is completed and ready for release.

---

## Verification & Quality Gate

- Before implementing Pygame rendering or integrating UI, write and run a **headless verification script / test** to prove that physics calculations, collision detection, and state transitions work deterministically.
- Always run non-interactive commands with timeouts and appropriate flags.
