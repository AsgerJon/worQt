"""
Control is one input on the cockpit's dashboard Asger can work (user,
2026-11-16: "Asger is presented iwth a fully functional diegetic
dashboard"; "*Every* fourtpeep input ... must visibly deform when
activated"): where it is (to be looked at), what it is called, the key
that does the same, the action it asks for, and its FourthPeep (the
switch, key, knob or slide control itself, moving as it is worked).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math


class Control:
  """
  Control holds a control on the dashboard: its 'name' (written on it),
  the 'key' that does what it does (its cap printed by the name), the
  window's 'action' it asks for; where it is: its middle ('centre', m,
  the vessel's own axes), its three axes ('axes': right, up, out of its
  face toward Asger, unit vectors) and half its size along each
  ('half', m); its 'peep' (a FourthPeep of the sandbox's: what moves
  when it is worked). Looked at along a ray ('hitBy') it says how far
  along.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  name: str
  key: str
  action: str
  centre: tuple
  axes: tuple
  half: tuple
  peep: object

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, key: str, action: str, centre: tuple,
               axes: tuple, half: tuple, peep: object) -> None:
    self.name, self.key, self.action, self.peep = name, key, action, peep
    self.centre = tuple(float(x) for x in centre)
    self.axes = tuple(tuple(float(x) for x in axis) for axis in axes)
    self.half = tuple(float(x) for x in half)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hitBy(self, start: tuple, way: tuple) -> float | None:
    """The 'hitBy' method returns how far along the ray from 'start'
    along the unit 'way' (the vessel's own axes) it meets the control's
    box, m; None if it misses."""
    near, far = -math.inf, math.inf
    d = tuple(a - b for a, b in zip(start, self.centre))
    for axis, half in zip(self.axes, self.half):
      at = sum(a * b for a, b in zip(d, axis))
      going = sum(a * b for a, b in zip(way, axis))
      if abs(going) < 1e-12:
        if abs(at) > half:
          return None
        continue
      one, two = (-half - at) / going, (half - at) / going
      near, far = max(near, min(one, two)), min(far, max(one, two))
      if near > far:
        return None
    if far < 0.0:
      return None
    return max(near, 0.0)

  def placeOf(self, right: float, up: float, out: float) -> tuple:
    """The 'placeOf' method returns the point 'right', 'up' and 'out' m
    from its middle along its axes, the vessel's own axes."""
    return tuple(c + right * a + up * b + out * n for c, a, b, n in zip(
      self.centre, *self.axes))
