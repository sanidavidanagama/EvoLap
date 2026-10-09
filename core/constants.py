"""Core constants for EvoLap simulation and mathematics."""

import math

# Discrete simulation step: 60 ticks per second (1/60s)
DEFAULT_DT: float = 1.0 / 60.0

# Numerical tolerance for floating-point comparisons
EPSILON: float = 1e-9

# Unit conversion constants
MPS_TO_KMH: float = 3.6
KMH_TO_MPS: float = 1.0 / 3.6
RAD_TO_DEG: float = 180.0 / math.pi
DEG_TO_RAD: float = math.pi / 180.0
