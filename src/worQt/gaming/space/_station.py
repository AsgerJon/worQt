"""
Station is the space station (user, 2026-11-17: "We are going to have a
space station in orbit. One that needs no fucking magic for its
gravity. Think 2001: A Space Odyssey"; "1800m"; "have some 300m antennas
sticking out of the station that has RGB lighting"): a wheel turning
once a minute, so its ring's floor pulls one g by its turning alone,
on rails round Terra in a circle 'HIGH' m over its equator, its axis
along Terra's pole (seen from the ground it is a ring). Qt-free; its
shape: '_stationmeshes'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._aerospike import G0
from ._conic import Conic
from ._heavenlybody import HeavenlyBody
from ._turns import cross, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem

#  It turns once a minute; its ring's floor is as far from its axis as
#  makes that pull one g (894 m: 1.8 km across).
SPIN = 2.0 * math.pi / 60.0
FLOOR_RADIUS = G0 / SPIN ** 2
#  Its path: a circle this high over Terra's equator; at time nought
#  this far round (rad, east) from straight over the pad (nought: it is
#  overhead as the game opens).
HIGH = 400e3
LEAD = 0.0
#  Its mass (it pulls nothing all the same: its G M only names it), kg;
#  how far its farthest part reaches from its middle (an antenna's tip),
#  m.
MASS = 5e8
REACH = 1200.0
GRAVITATION = 6.6743e-11


class Station:
  """
  Station holds the space station: 'body', a 'HeavenlyBody' on rails
  round Terra (its parent: 'parent', its index in the system) pulling
  nothing (one of the system's 'satellites', folded with it), turning
  'SPIN' about its own z (its axis, Terra's pole) from its own x; where
  it is from Terra and how fast it moves ('stateAt'), how it is turned
  ('turnAt': rows taking its own axes to the ecliptic's).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  body: HeavenlyBody
  parent: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, system: SolarSystem, lead: float = LEAD) -> None:
    self.parent = system.named('Terra')
    terra = system.bodies[self.parent]
    rows = terra.turnAt(0.0)
    over = unit(tuple(row[0] for row in rows))
    east = unit(cross(terra.pole, over))
    c, s = math.cos(lead), math.sin(lead)
    up = tuple(c * o + s * e for o, e in zip(over, east))
    ahead = tuple(-s * o + c * e for o, e in zip(over, east))
    far = terra.radius + HIGH
    speed = math.sqrt(terra.mu / far)
    conic = Conic.fromState(terra.mu, tuple(far * u for u in up),
                            tuple(speed * a for a in ahead))
    self.body = HeavenlyBody('Terra Prime', terra, GRAVITATION * MASS, REACH,
                             SPIN, terra.pole, 0.0, conic, 'station', None)
    system.satellites.append(self.body)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stateAt(self, t: float) -> tuple:
    """The 'stateAt' method returns where its middle is and how fast it
    moves from Terra at time 't' (s since the last leap)."""
    return self.body.stateAt(t)

  def turnAt(self, t: float) -> tuple:
    """The 'turnAt' method returns its turn at time 't': rows taking its
    own axes (z its axis, the docking port's way) to the ecliptic's."""
    return self.body.turnAt(t)
