"""
Station is the space station (user, 2026-11-17: "We are going to have a
space station in orbit. One that needs no fucking magic for its
gravity. Think 2001: A Space Odyssey"; "1800m"; "have some 300m antennas
sticking out of the station that has RGB lighting"): a wheel turning
once a minute, so its ring's floor pulls one g by its turning alone,
set going round Terra in a circle 'HIGH' m over its equator, its axis
along the pad's zenith as it first passes over (user, 2026-11-17: "have
Terra Prime be oriented such that it passes over the spawn parallel
with it. Making it more visible": seen from the pad the whole wheel,
face on; along Terra's pole it was edge on, a line); from then on
flown (user, 2026-11-18: "PHYSICS MUST BE REAL"). Qt-free; its shape:
'_stationmeshes'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._aerospike import G0
from ._conic import Conic
from ._turns import aboutAxis, cross, norm, product, quaternionOf, rotated
from ._turns import unit, unrotated
from ._vessel import Vessel

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
#  Its mass, kg (most of it in its ring: its moments are a thin ring's
#  'FLOOR_RADIUS' across, the hub, spokes and antennas left out of
#  them); how far its farthest part reaches from its middle (an
#  antenna's tip), m.
MASS = 5e8
REACH = 1200.0
INERTIA = (0.5 * MASS * FLOOR_RADIUS ** 2, 0.5 * MASS * FLOOR_RADIUS ** 2,
           MASS * FLOOR_RADIUS ** 2)


class Station:
  """
  Station holds the space station, flown as the rocket is (user, 2026-11-18:
  "PHYSICS MUST BE REAL"; it was on rails): 'body', a 'Vessel' built as the
  wheel ('MASS', 'INERTIA', no legs, drag, attitude thrusters or engine at
  work), kept from Terra ('parent', its index in the system), turning 'SPIN'
  about its own z (its axis: at first straight over the pad, where it passes
  over first) from its own x, held there by nothing but its own spin (what
  the planets' and moons' pulls twist it by the flight does). Its state is
  the one at time 'at' (s since the last leap: the window sets it after each
  frame, a leap folds it, 'fold'); 'stateAt' and 'turnAt' say where it is and
  how it is turned then, and further on as its path and spin would carry it
  (a coast on Terra's pull alone, the spin as it is: what the guidance plans
  by). 'struck' takes a push and its twist (what the rocket's hull pushed it
  by), 'kickedAt' a push anywhere. Docked, its body is the pair's
  ('_dockingport': their mass and middle) and its own middle is 'offset' from
  the pair's (its own axes; nought undocked). It is one of the system's
  'satellites' (the views draw them).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields, its parts.
  SAVED = ('at', 'offset')
  PARTS = ('body',)

  #  Public Variables
  name: str
  body: Vessel
  parent: int
  at: float
  mu: float
  offset: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, system: SolarSystem, lead: float = LEAD) -> None:
    self.name = 'Terra Prime'
    self.parent = system.named('Terra')
    terra = system.bodies[self.parent]
    self.mu = terra.mu
    rows = terra.turnAt(0.0)
    over = unit(tuple(row[0] for row in rows))
    east = unit(cross(terra.pole, over))
    c, s = math.cos(lead), math.sin(lead)
    up = tuple(c * o + s * e for o, e in zip(over, east))
    ahead = tuple(-s * o + c * e for o, e in zip(over, east))
    far = terra.radius + HIGH
    speed = math.sqrt(terra.mu / far)
    body = Vessel()
    body.mass, body.inertia = MASS, INERTIA
    body.legs = ((0.0, 0.0, 0.0),) * 4
    body.drag, body.attitude = (0.0, 0.0), (0.0, 0.0, 0.0)
    body.placed(self.parent, tuple(far * u for u in up),
                tuple(speed * a for a in ahead), quaternionOf(_tiltOf(over)),
                (0.0, 0.0, SPIN))
    body.felt, body.spinning = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self.body, self.at, self.offset = body, 0.0, (0.0, 0.0, 0.0)
    system.satellites.append(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def conic(self, ) -> Conic:
    """The 'conic' property is the path its middle is on now, as if Terra
    alone pulled it (the map's line)."""
    return Conic.fromState(self.mu, *self._middle())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stateAt(self, t: float) -> tuple:
    """The 'stateAt' method returns where its middle is and how fast it
    moves from Terra at time 't' (s since the last leap): as flown at
    'at', coasted on from there on Terra's pull alone."""
    if abs(t - self.at) < 1e-9:
      return self._middle()
    return self.conic.stateAt(t - self.at)

  def turnAt(self, t: float) -> tuple:
    """The 'turnAt' method returns its turn at time 't': rows taking its
    own axes (z its axis, the docking port's way) to the ecliptic's; on
    from 'at' as its spin turns it."""
    turn = self.body.turn
    spin = rotated(turn, self.body.spin)
    size = norm(spin)
    if size > 0.0 and abs(t - self.at) > 1e-9:
      turn = product(aboutAxis(tuple(s / size for s in spin),
                               size * (t - self.at)), turn)
    return tuple(tuple(rotated(turn, e)[i] for e in _AXES)
                 for i in range(3))

  def spinAt(self, t: float) -> tuple:
    """The 'spinAt' method returns its spin at time 't' (rad/s, the
    ecliptic's axes): as it spins (nothing twists it much)."""
    rows = self.turnAt(t)
    return tuple(sum(rows[i][j] * self.body.spin[j] for j in range(3))
                 for i in range(3))

  def struck(self, push: tuple, twist: tuple) -> None:
    """The 'struck' method gives it the push 'push' (N s) and the twist
    'twist' about its middle (N m s), the ecliptic's axes: what the
    rocket's hull pushed it by over the last frame."""
    self.kickedAt(push, twist, rotated(self.body.turn, self.offset))

  def kickedAt(self, push: tuple, twist: tuple, at: tuple) -> None:
    """The 'kickedAt' method gives its body the push 'push' (N s) and the
    twist 'twist' (N m s) about the point 'at' (m from the body's middle:
    docked, the pair's), the ecliptic's axes."""
    body = self.body
    about = tuple(w + c for w, c in zip(twist, cross(at, push)))
    body.kicked(unrotated(body.turn, push), unrotated(body.turn, about))

  def fold(self, seconds: float) -> None:
    """The 'fold' method carries a leap's 'seconds' s into its time."""
    self.at -= float(seconds)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _middle(self, ) -> tuple:
    """Returns where its own middle is and how fast it moves now (its
    body's middle, docked the pair's, and its 'offset' from that)."""
    body = self.body
    arm = rotated(body.turn, self.offset)
    spin = rotated(body.turn, body.spin)
    return (tuple(p + a for p, a in zip(body.place, arm)),
            tuple(v + c for v, c in zip(body.velocity, cross(spin, arm))))


_AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _tiltOf(pole: tuple) -> tuple:
  """Returns the turn taking its own axes to the ecliptic's: its z to
  'pole', its x to where a plane square to 'pole' crosses the ecliptic
  going north, three rows (as a heavenly body's, '_heavenlybody')."""
  node = (pole[1], -pole[0], 0.0)
  size = math.hypot(node[0], node[1])
  node = (1.0, 0.0, 0.0) if size < 1e-12 else (node[0] / size,
                                                node[1] / size, 0.0)
  side = cross(pole, node)
  return tuple((node[k], side[k], pole[k]) for k in range(3))
