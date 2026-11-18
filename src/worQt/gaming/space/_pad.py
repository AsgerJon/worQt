"""
Pad is the launch pad's place on Terra (user, 2026-11-18: "bro, the pad
needs to be there. If Asger took a shit on the ground before launch,
upon return there'd still be a turd on the ground"): Terra's ground at
'_planets.PAD', turning with Terra, its own axes east, north and up, its
place over the ground where the rocket's middle stands on it
('_walkway.PAD_UP': the launch tower, the walkway and the yard are laid
out in these axes, '_launchtower'). What is on it stays there whatever
the rocket does: the pad's world ('_cabinworld.CabinWorld', not
furnished) steps what is out there in its axes, feeling what its ground
feels ('feltOf': Terra's pull and every other body's tide, Terra's
turning), with the rocket where it really stands in it ('rocketIn').
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._planets import PAD
from ._turns import cross, dot, matrixTimes, rotated, unit
from ._vessel import CENTRE, SAG

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  The pad's axes are the ground's (x east, y north, z up) this much
#  higher: where the rocket's middle stands on it, m (the rocket's own
#  axes standing there are the pad's: the tower is laid out in them).
PAD_UP = CENTRE - SAG
_AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class Pad:
  """
  Pad holds where the pad is: on body 'anchor' (Terra) at 'latitude' and
  'longitude' (deg). 'frameAt' says where its axes are at a time (from
  Terra's middle, the ecliptic's axes), 'feltOf' what its ground feels,
  'rocketIn' where the rocket is in its axes and how it moves there (a
  pose: its place, its three axes, its velocity and its spin, the pad's
  axes; 'posesOf' the rocket's and the pad's for a world's rooms).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  anchor: int
  latitude: float
  longitude: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, system: SolarSystem) -> None:
    self.anchor = system.named('Terra')
    self.latitude, self.longitude = float(PAD[0]), float(PAD[1])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def frameAt(self, system: SolarSystem, t: float) -> tuple:
    """The 'frameAt' method returns the pad's axes at time 't': their
    place and velocity from Terra's middle (m, m/s), their three axes
    (east, north, up) and their spin (Terra's, rad/s), the ecliptic's
    axes."""
    body = system.bodies[self.anchor]
    lat, lon = math.radians(self.latitude), math.radians(self.longitude)
    up = matrixTimes(body.turnAt(t), (math.cos(lat) * math.cos(lon),
                                      math.cos(lat) * math.sin(lon),
                                      math.sin(lat)))
    east = unit(cross(body.pole, up))
    north = cross(up, east)
    spin = body.spinVector
    place = tuple((body.radius + PAD_UP) * u for u in up)
    return place, cross(spin, place), (east, north, up), spin

  def feltOf(self, system: SolarSystem, t: float) -> tuple:
    """The 'feltOf' method returns what the pad's ground feels at time
    't', its own axes: its push a kg (m/s²: what holds it up against
    Terra's pull and every other body's tide as it is carried round
    with Terra) and its turning (Terra's, rad/s)."""
    place, _, axes, spin = self.frameAt(system, t)
    pull = system.pullOn(self.anchor, place, t)
    round_ = cross(spin, cross(spin, place))
    felt = tuple(r - p for r, p in zip(round_, pull))
    return _into(axes, felt), _into(axes, spin)

  def rocketIn(self, vessel: Vessel, system: SolarSystem, t: float) -> tuple:
    """The 'rocketIn' method returns where the rocket is in the pad's axes
    at time 't' and how it moves there: its middle's place, its three
    axes (its own x, y and z), its middle's velocity and its spin (each
    as the pad's axes see it); None if it is not on Terra."""
    if vessel.anchor != self.anchor:
      return None
    place, _, axes, spin = self.frameAt(system, t)
    off = tuple(p - o for p, o in zip(vessel.place, place))
    moving = tuple(v - c for v, c in zip(vessel.velocity, cross(
      spin, vessel.place)))
    own = tuple(_into(axes, rotated(vessel.turn, e)) for e in _AXES)
    turning = tuple(s - w for s, w in zip(rotated(vessel.turn,
                                                  vessel.spin), spin))
    return (_into(axes, off), own, _into(axes, moving),
            _into(axes, turning))


def posesOf(rocket: tuple) -> tuple:
  """Returns the rocket's and the pad's places and axes in the rocket's
  axes (the cabin's world: the rocket its own, the pad where 'rocket',
  its pose in the pad's axes, has it from the rocket) and in the pad's
  (the pad's world), each two rows of four: the rocket's, the pad's."""
  place, own = rocket[0], rocket[1]
  padAxes = tuple(tuple(own[k][i] for k in range(3)) for i in range(3))
  padPlace = tuple(-dot(place, own[k]) for k in range(3))
  still = ((0.0, 0.0, 0.0),) + _AXES
  return ((still, (padPlace,) + padAxes),
          ((tuple(place),) + tuple(own), still))


def toPad(rocket: tuple, point: tuple) -> tuple:
  """Returns 'point' (the rocket's own axes) in the pad's, the rocket's
  pose in the pad's axes 'rocket'."""
  place, own = rocket[0], rocket[1]
  return tuple(p + sum(own[k][i] * point[k] for k in range(3))
               for i, p in enumerate(place))


def fromPad(rocket: tuple, point: tuple) -> tuple:
  """Returns 'point' (the pad's axes) in the rocket's own."""
  off = tuple(p - q for p, q in zip(point, rocket[0]))
  return tuple(dot(off, axis) for axis in rocket[1])


def turnedToPad(rocket: tuple, way: tuple) -> tuple:
  """Returns 'way' (a vector, the rocket's own axes) in the pad's."""
  own = rocket[1]
  return tuple(sum(own[k][i] * way[k] for k in range(3))
               for i in range(3))


def turnedFromPad(rocket: tuple, way: tuple) -> tuple:
  """Returns 'way' (a vector, the pad's axes) in the rocket's own."""
  return tuple(dot(way, axis) for axis in rocket[1])


def movingToPad(rocket: tuple, point: tuple, moving: tuple) -> tuple:
  """Returns the velocity of something at 'point' moving 'moving' (the
  rocket's own axes, as the rocket sees it) as the pad sees it."""
  arm = turnedToPad(rocket, point)
  carried = cross(rocket[3], arm)
  return tuple(v + c + m for v, c, m in zip(
    rocket[2], carried, turnedToPad(rocket, moving)))


def movingFromPad(rocket: tuple, point: tuple, moving: tuple) -> tuple:
  """Returns the velocity of something at 'point' moving 'moving' (the
  pad's axes, as the pad sees it) as the rocket sees it."""
  arm = tuple(p - q for p, q in zip(point, rocket[0]))
  carried = cross(rocket[3], arm)
  return turnedFromPad(rocket, tuple(m - v - c for m, v, c in zip(
    moving, rocket[2], carried)))


def _into(axes: tuple, x: tuple) -> tuple:
  """Returns 'x' (the ecliptic's axes) in 'axes' (three, the
  ecliptic's)."""
  return tuple(dot(x, axis) for axis in axes)
