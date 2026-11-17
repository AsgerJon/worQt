"""
Accelerometer is what the vessel feels (user, 2026-11-17: Asger getting
up and floating round in micro-gravity, "FAFO rules"): its push (thrust,
drag, the ground: everything but gravity, which pulls everything in it
alike), its turning and how fast its turning changes, each in its own
axes; and from them the pull on anything loose in its cabin ('pullAt').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._aerospike import G0
from ._turns import cross, norm, unrotated
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  How fast what it reads follows the vessel (most of the way in), s: the
#  legs on the pad ring, the autopilot's rate loop chatters.
SMOOTH = 0.1


class Accelerometer:
  """
  Accelerometer reads the vessel each frame ('measured'): 'felt', the
  push it feels a kg (m/s², its own axes: its change of velocity less
  gravity's pull: thrust, drag, the ground; on the pad one g up, coasting
  nought), 'turning' (its spin, rad/s, its own axes) and 'speeding' (how
  fast that changes, rad/s²), each eased over 'SMOOTH' s. Warping it
  reads the engine's thrust alone (nothing else pushes then); just handed
  to another body or set back on the pad ('reset'), it keeps what it read
  till it has two frames to read again. It starts as on the pad.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  felt: tuple
  turning: tuple
  speeding: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.felt = (0.0, 0.0, G0)
    self.turning, self.speeding = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self._last = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def measured(self, vessel: Vessel, system: SolarSystem, seconds: float,
               warped: bool) -> None:
    """The 'measured' method reads 'vessel' after it flew 'seconds' s
    of the game's time ('warped': at more than real time)."""
    now = (vessel.anchor, vessel.velocity, vessel.spin)
    last, self._last = self._last, now
    self.turning = tuple(vessel.spin)
    if seconds <= 0.0 or last is None or last[0] != now[0]:
      return
    if warped:
      felt, speeding = (0.0, 0.0, vessel.engine.push / MASS), (0.0, 0.0,
                                                               0.0)
    else:
      body = system.bodies[vessel.anchor]
      place = vessel.place
      far = norm(place)
      pull = tuple(-body.mu * x / far ** 3 for x in place)
      change = tuple((a - b) / seconds for a, b in zip(now[1], last[1]))
      felt = unrotated(vessel.turn, tuple(c - g for c, g in zip(change,
                                                                pull)))
      speeding = tuple((a - b) / seconds for a, b in zip(now[2], last[2]))
    share = 1.0 - math.exp(-seconds / SMOOTH)
    self.felt = _eased(self.felt, felt, share)
    self.speeding = _eased(self.speeding, speeding, share)

  def reset(self, ) -> None:
    """The 'reset' method forgets the last frame (the vessel was set
    somewhere new: its change of velocity then is no push)."""
    self._last = None

  def pullAt(self, place: tuple, velocity: tuple) -> tuple:
    """The 'pullAt' method returns the pull on something loose at
    'place' moving 'velocity' (the vessel's own axes, from its middle),
    m/s²: the vessel's push the other way, its turning's (out from the
    axis it turns about, across the way it moves, and as it turns
    faster)."""
    turning, speeding = self.turning, self.speeding
    out = cross(turning, cross(turning, place))
    sideways = cross(turning, velocity)
    faster = cross(speeding, place)
    return tuple(-f - o - 2.0 * s - a for f, o, s, a in zip(
      self.felt, out, sideways, faster))


def _eased(now: tuple, want: tuple, share: float) -> tuple:
  """Returns 'now' moved 'share' of the way to 'want'."""
  return tuple(a + share * (b - a) for a, b in zip(now, want))
