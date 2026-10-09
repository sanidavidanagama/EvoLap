# EvoLap Project Roadmap (ROADMAP.md)

This document outlines the versioned progression and milestones of the EvoLap system.
Each milestone builds upon decoupled engines without requiring future features to be implemented ahead of schedule.

---

## v0.1.0 — Basic Simulation & Manual Driving (Completed - Released)

- **Status**: Completed (2026-10-09)
- **Scope**: Single car, single track, manual keyboard control.
- **Engines Involved**: `core`, `physics`, `simulation`, `rendering`.
- **Capabilities**:
  - 2D vehicle dynamics: position, heading, velocity, acceleration, braking, steering rate, rolling friction.
  - Track geometry representation: asphalt polygon, inner and outer barrier line segments, start/finish line.
  - Boundary collision detection and crash state transition (`Out` / reset).
  - Gradual input filtering (no instantaneous teleporting or speed jumps).
  - Two camera views: Full-Track and Follow Camera with seamless toggle.
  - Headless test proving simulation executes deterministically without Pygame.
- **Explicit Exclusions**: No AI / Neural Engine, no sidebars/leaderboards, no training loops.

---

## v0.2.0 — Neural Engine & Multi-Car Simulation

- **Scope**: 20 AI-controlled cars running concurrently with random weights.
- **Engines Involved**: `neural_engine` (v1.0.0), `simulation`, `rendering`, `ui`.
- **Capabilities**:
  - Grid setup: F1-style zig-zag starting grid.
  - Perception: 5-directional raycast sensors ($D_1 \dots D_5$) + speed and heading.
  - Inference: 434-weight MLP forward pass per car per tick.
  - UI Overlays: Left standings sidebar (20 cars, flags, codes, laps, status) and Right telemetry sidebar.
  - Crash handling: Cars that collide become `Out`, stop moving, and remain rendered on track.
- **Explicit Exclusions**: No inheritance or weight mutations yet.

---

## v0.3.0 — Evolutionary Training System

- **Scope**: Try-fail-learn genetic algorithm with generation cycles.
- **Engines Involved**: `training`, `neural_engine`, `simulation`, `storage`.
- **Capabilities**:
  - Pre-run configuration: Driver count (4–22), target laps (1–100).
  - Fitness evaluation based on track distance and completed laps.
  - Generation rollover: Select best parent DNA, replicate with Gaussian weight nudging.
  - Dual Execution Modes:
    - **Visual Mode**: Real-time Pygame watch mode.
    - **Headless Mode**: Fast, headless training executing thousands of iterations.
  - Storage: Generation checkpoints saved to `storage/training/checkpoints/`.

---

## v0.4.0 — Main Menu & The Laboratory

- **Scope**: Central hub for track management and trained model archives.
- **Engines Involved**: `ui`, `storage`, `training`.
- **Capabilities**:
  - Main navigation: Play, Laboratory, Settings.
  - Track Registry: Dynamic discovery of tracks from `storage/tracks/`.
  - Continuous Training: Resume training on a track from generation $N$ without starting at zero.
  - Model Persistence: Stored models in `storage/models/` with training history.
  - Settings: Driver names, custom liveries/colors, driver codes.

---

## v0.5.0 — Player vs AI Gameplay

- **Scope**: Race against trained neural driver models.
- **Capabilities**:
  - Track selection (from trained tracks).
  - Difficulty selection: Choose which historical generation of AI to race against (e.g., Gen 1, Gen 50, Gen 200).
  - Player controls manual car against trained AI field.

---

## v1.0.0 — First Complete Release

- **Scope**: Polished standalone racing simulation.
- **Capabilities**:
  - 2–4 diverse circuits.
  - AI Skill Tier mapping: Translates raw generations into ranks (Rookie, Novice, Amateur, Pro, Elite, Champion, Legend, Apex).
  - End-of-race flow: Race results, spectate, restart, exit.
  - Full persistence across sessions.

---

## v2.0.0 & Future — Advanced Dynamics & Track Generalization

**Out of initial scope of the project. Could be a future independent product.**

- **Advanced Simulation**: Tire wear, compound choices, temperature, brake fade, track wetness, downforce/drag.
- **Generalization**: Evolving the Neural Engine observation space to learn generalized driving lines across previously unseen circuits.
