"""
HeavenlyBody is a star, planet or moon (user, 2026-11-16: "each heavenly
body is a vector of dofs, a vector function in time. other data points
are fixed immutable. so is the texture"): its fixed numbers and look,
how it is turned as a function of time. Where it is the solar system's
flown sky says (user, 2026-11-18: real gravity, '_ephemeris').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._conic import TAU

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._atmosphere import Atmosphere
  from ._conic import Conic


class HeavenlyBody:
  """
  HeavenlyBody holds a heavenly body: its 'name', the body it goes round
  ('parent', None: Sol, the middle of everything) and the path it would
  follow from the last leap if its parent alone pulled it ('conic': at
  first its day's, then as the solar system takes it anew at each leap,
  '_solarsystem'; where it truly is the flown sky says), its G M ('mu',
  m³/s²), 'radius' (m),
  spin ('spin', rad/s about its north 'pole', a unit vector in the
  ecliptic's axes; its own x axis, its prime meridian, 'angle' rad on
  from the node of its equator at time nought), its 'look' (how it is
  painted, by name) and its 'air' (an 'Atmosphere', None: none). Times
  are s since the last leap; 'fold' carries them over into the angles
  at a leap (user: "put in a leap step every 256 steps").
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  name: str
  parent: HeavenlyBody | None
  mu: float
  radius: float
  spin: float
  pole: tuple
  angle: float
  conic: Conic | None
  look: str
  air: Atmosphere | None
  tilt: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, parent: HeavenlyBody | None, mu: float,
               radius: float, spin: float, pole: tuple, angle: float,
               conic: Conic | None, look: str,
               air: Atmosphere | None) -> None:
    if (parent is None) != (conic is None):
      raise ValueError('%s: a body goes round its parent, Sol round '
                       'nothing' % name)
    if mu <= 0.0 or radius <= 0.0:
      raise ValueError('%s: G M %r, radius %r' % (name, mu, radius))
    size = math.sqrt(sum(x * x for x in pole))
    self.name, self.parent, self.conic = name, parent, conic
    self.mu, self.radius, self.spin = float(mu), float(radius), float(spin)
    self.pole = tuple(x / size for x in pole)
    self.angle = float(angle) % TAU
    self.look, self.air = look, air
    self.tilt = _tiltOf(self.pole)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def gravity(self, ) -> float:
    """The 'gravity' property is the pull on its ground, m/s²."""
    return self.mu / (self.radius * self.radius)

  @property
  def spinVector(self, ) -> tuple:
    """The 'spinVector' property is its spin as a vector, rad/s, in the
    ecliptic's axes."""
    return tuple(self.spin * x for x in self.pole)

  @property
  def reach(self, ) -> float:
    """The 'reach' property is how far its pull is the one that matters
    most, m (Laplace's sphere of influence: a vessel within it is kept
    from this body, user: "Each vehicle is stored as the planet it's
    near"); Sol's has no end."""
    if self.parent is None:
      return math.inf
    return self.conic.a * (self.mu / self.parent.mu) ** 0.4

  @property
  def depth(self, ) -> int:
    """The 'depth' property is how many parents up Sol is."""
    return 0 if self.parent is None else 1 + self.parent.depth

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def angleAt(self, t: float) -> float:
    """The 'angleAt' method returns how far it has turned at time 't',
    rad, within one turn."""
    return (self.angle + self.spin * t) % TAU

  def turnAt(self, t: float) -> tuple:
    """The 'turnAt' method returns its turn at time 't': three rows
    taking its own axes (z its pole, x its prime meridian) to the
    ecliptic's."""
    angle = self.angleAt(t)
    cos, sin = math.cos(angle), math.sin(angle)
    return tuple((row[0] * cos + row[1] * sin, -row[0] * sin
                  + row[1] * cos, row[2]) for row in self.tilt)

  def fold(self, seconds: float) -> None:
    """The 'fold' method carries 'seconds' s into its turn's angle: what
    was at time 'seconds' is at time nought."""
    self.angle = self.angleAt(seconds)

  def restored(self, angle: float, pole: tuple) -> None:
    """The 'restored' method turns the body as a saved game had it
    ('_savegame'): 'angle' about 'pole'."""
    size = math.sqrt(sum(x * x for x in pole))
    self.angle = float(angle) % TAU
    self.pole = tuple(float(x) / size for x in pole)
    self.tilt = _tiltOf(self.pole)


def _tiltOf(pole: tuple) -> tuple:
  """Returns the turn taking a body's unturned axes to the ecliptic's:
  its z to 'pole', its x to its equator's node (where its equator
  crosses the ecliptic going north: the equinox, for Terra), three
  rows."""
  node = (pole[1], -pole[0], 0.0)
  size = math.hypot(node[0], node[1])
  node = (1.0, 0.0, 0.0) if size < 1e-12 else (node[0] / size,
                                                node[1] / size, 0.0)
  side = (pole[1] * node[2] - pole[2] * node[1],
          pole[2] * node[0] - pole[0] * node[2],
          pole[0] * node[1] - pole[1] * node[0])
  return tuple((node[k], side[k], pole[k]) for k in range(3))
