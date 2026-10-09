# EvoLap Technical Specification (SPEC.md)

This document contains the core technical specifications and domain rules for the EvoLap project.

---

## 1. System Overview

EvoLap is a modular 2D Formula 1 simulation and AI driving laboratory built with Python.
- Simulation and physics calculations operate completely headless.
- Visualization and interactive control are handled via Pygame (pygame-ce).
- The vehicle is controlled either manually (keyboard) or via an autonomous Neural Engine.
- Tracks are composed of line segments with asphalt surfaces, kerbs, and tyre barriers.

---

## 2. Neural Engine Specifications

The **Neural Engine** is an independent, scalable sub-product within EvoLap with its own subversioning scheme (e.g., `NeuralEngine v1.0.0`). It encapsulates perception (sensors), network topology, and inference.

### 2.1 Topology (v1.0.0 Architecture)
- **Total Weights**: 434
  - **Layer 1 (Dense)**: 7 inputs $\times$ 16 hidden units + 16 biases = 128 parameters
  - **Layer 2 (Dense)**: 16 hidden units $\times$ 16 hidden units + 16 biases = 272 parameters
  - **Output Layer (Dense)**: 16 hidden units $\times$ 2 outputs + 2 biases = 34 parameters
  - **Total**: $128 + 272 + 34 = 434$
- **Activation Function**: `tanh` on all hidden and output layers.
- **Inference Library**: Pure NumPy (zero Pygame dependency).

### 2.2 Input Vector ($7$ Features, $120^\circ$ Sensor Coverage)
The input vector feeds normalized local perceptions:
1. `D1`: Raycast distance to track boundary at $-60^\circ$ relative to car heading.
2. `D2`: Raycast distance to track boundary at $-30^\circ$ relative to car heading.
3. `D3`: Raycast distance to track boundary at $0^\circ$ (straight ahead).
4. `D4`: Raycast distance to track boundary at $+30^\circ$ relative to car heading.
5. `D5`: Raycast distance to track boundary at $+60^\circ$ relative to car heading.
6. `S`: Current vehicle speed (km/h).
7. `T`: Current car heading angle relative to track tangent or reference heading (degrees).

### 2.3 Output Vector ($2$ Actions)
The network outputs continuous control values in range $[-1.0, +1.0]$:
1. `f` (Throttle / Brake):
   - $+1.0$: Full acceleration / gas.
   - $-1.0$: Full braking.
2. `g` (Steering):
   - $-1.0$: Full left steer.
   - $+1.0$: Full right steer.

---

## 3. Training & Genetic Algorithm Specifications

- **Population Size**: 20 drivers/cars running concurrently in the same simulation.
- **Starting Grid**: Zig-zag F1-style grid behind the start/finish line.
- **Inheritance & Evolution Loop**:
  1. Initialization: All 20 agents initialized with randomized weights.
  2. Trial: Agents drive until crashed or target lap completed.
  3. Fitness Evaluation: Distance along racing line / track progress + lap completion bonus.
  4. Selection: Best-performing agent's DNA is preserved as the parent generation.
  5. Mutation: Parent DNA is duplicated across 20 slots and perturbed with random Gaussian nudges.
  6. Next Generation: Increments generation counter ($Gen_0 \to Gen_1 \to \dots$).

---

## 4. Vehicle & Physics Specifications

- **Control Response**: Gradual inputs rather than instantaneous step changes.
  - Throttle gradually builds acceleration.
  - Releasing throttle introduces engine braking / gradual deceleration.
  - Steering response applies angular acceleration / turning rate with tire friction limits.
- **Wheel Articulation**: Top-down visual representation shows front tires rotating in the steer direction.
- **Collision Detection**:
  - Car bounding geometry checked against track barrier line segments.
  - Collision triggers `Out` state (crash), disabling movement while keeping the car visible.

---

## 5. Camera & Interface Specifications

### 5.1 Camera Modes
1. **Full-Track Camera**:
   - Fixed framing displaying the entire circuit.
   - Cars move within the view; no camera tracking.
2. **Follow Camera**:
   - Dynamically tracks the current P1 leader (or active player car).
   - Keeps the car near screen center with forward offset.
   - Smooth interpolation (lerp).

### 5.2 UI Layout
- **Left Sidebar (Leaderboard)**:
  - Transparent overlay listing standings:
    - Position (1–20)
    - Logo (Random 2-color vertical split badge)
    - Driver Code (VER, HAM, ALO, etc.)
    - Current Lap (e.g., Lap 1)
    - Status (`Running`, `Out`)
- **Right Sidebar (Telemetry / Generation Info)**:
  - Current Generation number
  - Total cars initialized
  - Active running cars count
  - Camera toggle button (Full-Track $\leftrightarrow$ Follow-Cam)

### 5.3 Manual Controls
- `Up Arrow` / `W`: Accelerate
- `Down Arrow` / `S`: Brake / Reverse
- `Left Arrow` / `A`: Steer Left
- `Right Arrow` / `D`: Steer Right
- `C`: Switch camera mode
- `R`: Reset car (manual mode)
