"""
The 'worQt.engineering.springs' package is a system of masses joined by
springs and dampers, swinging in space under gravity, in m, kg, N and
s, z up. It needs no Qt; 'worQt.engineering.springs.gui' shows it.

- Point, Spring, Damper: the parts: a mass at a point, moving along
  the axes it may, pinned along none; a spring and a dashpot between
  two points.
- SpringMassDamper: a component, a rod from one point to another,
  rigid but for its length, a spring and a damper inside it, fixed in
  direction, hinged or free to turn about its base.
- System: the parts together, under gravity, the points guided: the
  forces, the energies, the stiffness, where it comes to rest and how
  it swings about it.
- Motion, Energies, Sample: a system moving, stepped through time; its
  energies; how it was at a time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._parts import Point, Spring, Damper, SpringMassDamper
from ._system import System
from ._motion import Motion, Energies, Sample

__all__ = (
  'Point',
  'Spring',
  'Damper',
  'SpringMassDamper',
  'System',
  'Motion',
  'Energies',
  'Sample',
)
