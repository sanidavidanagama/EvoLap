# EvoLap — Agent Development Guide & Constraints (GEMINI.md)

Welcome to **EvoLap**. This document contains mandatory architectural invariants, workflows, and constraints that every agent and contributor must follow.

---

## Active Milestone (Read This First)

- **Currently Developing Milestone**: [`docs/milestones/v0.1.0-basic-simulation.md`](file:///c:/Users/sanid/VS%20Code%20Projects/EvoLap/docs/milestones/v0.1.0-basic-simulation.md)
- **Scope Rule**: Strictly adhere to the checklist in the active milestone document. **Do not implement features belonging to future milestones** (e.g., do not add neural networks, sidebars, or genetic algorithms during v0.1.0).

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
