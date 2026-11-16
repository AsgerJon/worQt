"""
The 'worQt.gaming.space' package is space travel (user, 2026-11-16:
"It's time for space travel. No i'm not kidding!"; "basically what
kerbal space program aimed at"): Sol, its nine planets and Terra's two
moons, each a function of time, and rockets flown among them.
- 'HeavenlyBody', 'SolarSystem' (made for a day: 'solarSystemOn'): the
  sky, gravity down its tree alone.
- 'Conic': a path round a puller (an ellipse, or a hyperbola).
- 'Timekeeper': time since the last leap, the leaps, time warp.
- 'Atmosphere', 'Aerospike', 'Autopilot', 'Vessel': the rocket.
- 'Flight': the rocket flown on the GPU, float32 ('_flight_kernels').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._aerospike import Aerospike
from ._atmosphere import Atmosphere
from ._autopilot import Autopilot
from ._conic import Conic
from ._flight import Flight
from ._heavenlybody import HeavenlyBody
from ._planets import solarSystemOn
from ._solarsystem import SolarSystem
from ._timekeeper import Timekeeper
from ._vessel import Vessel

__all__ = (
  'Aerospike',
  'Atmosphere',
  'Autopilot',
  'Conic',
  'Flight',
  'HeavenlyBody',
  'SolarSystem',
  'Timekeeper',
  'Vessel',
  'solarSystemOn',
)
