"""EvoLap — Formula 1 Simulation and AI Driving Laboratory.
Main entry point assembling Input -> Simulation -> Physics -> State -> Renderer.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pygame

from core.constants import DEFAULT_DT
from rendering.camera import Camera
from rendering.renderer import Renderer
from simulation.car import Car
from simulation.track import Track
from simulation.world import World


def load_circuit() -> Track:
    """Loads Apex Valley circuit if available, otherwise built-in Monaco test circuit."""
    track_path = Path("storage/tracks/apex_valley.json")
    if track_path.exists():
        try:
            return Track.from_json_file(track_path)
        except Exception as e:
            print(f"[WARN] Could not load {track_path}: {e}. Falling back to Monaco.")
    return Track.create_monaco_test_circuit()


def main() -> None:
    # 1. Initialize Circuit and World
    track = load_circuit()
    world = World.create_default(track=track)

    # 2. Initialize Renderer in Fullscreen (Full width with zero background interruption)
    renderer = Renderer(fullscreen=True)

    clock = pygame.time.Clock()
    running = True

    print("=" * 60)
    print("EvoLap v0.1.0 — Basic Simulation & Manual Driving")
    print(f"Loaded Track: {world.track.name}")
    print("Controls:")
    print("  W / Up Arrow    : Accelerate")
    print("  S / Down Arrow  : Brake / Reverse")
    print("  A / Left Arrow  : Steer Left")
    print("  D / Right Arrow : Steer Right")
    print("  C               : Toggle Camera (Follow Cam <-> Full Track)")
    print("  R               : Reset Car")
    print("  T               : Toggle Track (Apex Valley <-> Monaco)")
    print("  F11             : Toggle Fullscreen")
    print("  ESC             : Exit Game")
    print("=" * 60)

    # Alternate track cache
    is_apex = (world.track.name == "Apex Valley Circuit")

    while running:
        dt = DEFAULT_DT

        # 3. Handle Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    renderer.camera.toggle_mode()
                elif event.key == pygame.K_r:
                    world.reset()
                elif event.key == pygame.K_F11:
                    renderer.toggle_fullscreen()
                elif event.key == pygame.K_t:
                    # Switch circuit
                    if is_apex:
                        new_track = Track.create_monaco_test_circuit()
                        is_apex = False
                    else:
                        new_track = load_circuit()
                        is_apex = True
                    world.track = new_track
                    world.reset()
                    renderer._track_fitted = False
            elif event.type == pygame.VIDEORESIZE:
                renderer.handle_resize(event.w, event.h)

        # 4. Read Continuous Keyboard Driving Inputs
        keys = pygame.key.get_pressed()
        throttle = 0.0
        steer = 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            throttle += 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            throttle -= 1.0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            steer -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            steer += 1.0

        # 5. Advance Headless Physics Simulation
        world.step(controls=(throttle, steer))

        # 6. Render Observer Visuals
        renderer.render(world, dt)

        # 7. Cap at 60 FPS
        clock.tick(60)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
