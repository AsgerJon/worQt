"""
KeglePin is a keglebillard pin's shape and mass: a solid of revolution
of wood, as Den Danske Billard Union draws it, and what its toppling
needs: its centre of mass, its moments of inertia, and the spheres its
surface is made of for meeting balls, pins and the cloth.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

#  The pin's outline, (height, radius) in mm, from the foot up: the shape
#  and heights read off DDBU's drawing (material rules 2026-27, bilag H),
#  its widths set to the measures written on it, 14 mm across the foot,
#  20 the body, 8 the neck, 13 the head, 120 tall. The body is widest at
#  a ball's middle, so a ball passes between two pins with a third of a
#  mm to spare a side.
PROFILE = ((0.0, 7.00), (2.6, 7.53), (7.5, 8.39), (12.5, 9.05),
           (17.5, 9.48), (22.5, 9.81), (27.6, 9.94), (32.6, 9.88),
           (37.6, 9.65), (42.6, 9.12), (47.6, 8.27), (52.6, 7.07),
           (57.5, 5.74), (62.6, 4.72), (67.5, 4.12), (72.5, 4.05),
           (77.5, 4.72), (82.5, 5.51), (87.5, 6.25), (92.6, 6.51),
           (97.6, 6.51), (102.6, 6.19), (107.6, 5.69), (112.6, 4.83),
           (117.5, 3.34), (120.0, 0.00))


class KeglePin(NamedTuple):
  """
  KeglePin is a keglebillard pin, in mm and g: of wood, 'mass' grams,
  shaped as 'profile', its outline from the foot up, a solid of
  revolution standing on a flat foot, all of it alike throughout. Five
  alike stand in the cross ('KegleTable.pinSpots').

  'radiusAt' gives its radius at a height; 'height' its own; 'foot' the
  radius of the flat foot it stands on; 'centre' how high its centre of
  mass is; 'inertia' its moments of inertia through the centre of mass,
  about its axis and across it; 'tipping' the angle it falls past on
  its foot's edge. 'spheres' gives the spheres along its axis its
  surface is made of, (height, radius), each inside the outline and
  touching it, near enough for meeting balls, pins and the cloth.
  """

  mass: float = 10.5
  profile: tuple = PROFILE

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def height(self, ) -> float:
    """The 'height' method returns how tall the pin is."""
    return self.profile[-1][0]

  def foot(self, ) -> float:
    """The 'foot' method returns the radius of the flat foot the pin
    stands on."""
    return self.profile[0][1]

  def radiusAt(self, height: float) -> float:
    """The 'radiusAt' method returns the pin's radius 'height' above its
    foot, between the outline's points in a straight line; nought off
    the pin."""
    profile = self.profile
    if height < profile[0][0] or height > profile[-1][0]:
      return 0.0
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
      if z0 <= height <= z1:
        if z1 == z0:
          return max(r0, r1)
        return r0 + (r1 - r0) * (height - z0) / (z1 - z0)
    return 0.0

  def centre(self, ) -> float:
    """The 'centre' method returns how high the pin's centre of mass is
    above its foot."""
    return _massOf(self)[1]

  def inertia(self, ) -> tuple[float, float]:
    """The 'inertia' method returns the pin's moments of inertia through
    its centre of mass, in g mm²: about its axis, and across it."""
    _, _, along, across = _massOf(self)
    return along, across

  def tipping(self, ) -> float:
    """The 'tipping' method returns the angle, in radians, the pin
    falls past on its foot's edge: where its centre of mass comes over
    that edge."""
    return math.atan2(self.foot(), self.centre())

  def spheres(self, ) -> tuple[tuple[float, float], ...]:
    """The 'spheres' method returns the spheres along the pin's axis its
    surface is made of, (height, radius): one at each point of the
    outline as wide as the pin is there, set in so it does not stick out
    past the outline either side; from the foot up."""
    return _spheresOf(self)


@functools.lru_cache(maxsize=8)
def _massOf(pin: KeglePin) -> tuple[float, float, float, float]:
  """Returns the volume of 'pin', mm³, how high its centre of mass is,
  and its moments of inertia through it about its axis and across it,
  g mm², the wood alike throughout: summed over thin discs."""
  steps = 2400
  top = pin.height()
  dz = top / steps
  volume = moment = 0.0
  discs = []
  for k in range(steps):
    z = (k + 0.5) * dz
    r = pin.radiusAt(z)
    area = math.pi * r * r
    volume += area * dz
    moment += area * z * dz
    discs.append((z, r, area))
  centre = moment / volume
  density = pin.mass / volume
  along = across = 0.0
  for z, r, area in discs:
    along += 0.5 * area * r * r * dz
    across += (0.25 * area * r * r + area * (z - centre) ** 2) * dz
  return volume, centre, density * along, density * across


@functools.lru_cache(maxsize=8)
def _spheresOf(pin: KeglePin) -> tuple[tuple[float, float], ...]:
  """Returns the spheres of 'pin', (height, radius): at each point of
  the outline but the ends, the largest sphere there that stays inside
  the pin, exactly: as large as the way, in the plane through the axis,
  from its middle on the axis to the nearest piece of the outline, the
  flat foot among them."""
  profile = pin.profile
  pieces = [((0.0, 0.0), profile[0])] + list(zip(profile, profile[1:]))
  out = []
  for z, r in profile:
    size = min(_apart((z, 0.0), start, end) for start, end in pieces)
    if size > 0.5:
      out.append((z, size))
  return tuple(out)


def _apart(point: tuple, start: tuple, end: tuple) -> float:
  """Returns how far 'point' is from the straight piece from 'start' to
  'end', each (height, radius)."""
  (h, r), (h0, r0), (h1, r1) = point, start, end
  dh, dr = h1 - h0, r1 - r0
  length = dh * dh + dr * dr
  share = 0.0
  if length > 0.0:
    share = max(0.0, min(1.0, ((h - h0) * dh + (r - r0) * dr) / length))
  return math.hypot(h - h0 - share * dh, r - r0 - share * dr)
