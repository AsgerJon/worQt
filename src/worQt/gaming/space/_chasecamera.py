"""
ChaseCamera is the flight view's eye (the spec: "the camera follows the
rocket, the mouse circles it and the wheel zooms"): it circles the
vessel kept level with the ground under it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._turns import cross, dot, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  Rad a pixel the mouse moves; how far the wheel takes it a notch; how
#  near and far it may be, m; how far up or down it may look, rad.
TURN = 0.004
ZOOM = 0.85
NEAREST, FURTHEST = 12.0, 2e5
STEEPEST = 1.5


class ChaseCamera:
  """
  ChaseCamera circles a vessel: 'yaw' (rad, round its up from its north
  toward its east), 'pitch' (rad above its horizon) and 'distance' (m),
  its up away from the middle of the body the vessel is kept from, so
  the horizon stays level. It starts west of the vessel, a little high,
  looking east the way a launch goes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  yaw: float
  pitch: float
  distance: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.yaw, self.pitch, self.distance = -0.5 * math.pi, 0.12, 45.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def turned(self, right: float, down: float) -> None:
    """The 'turned' method circles the camera as the mouse moved 'right'
    and 'down' pixels."""
    self.yaw -= TURN * right
    self.pitch = max(-STEEPEST, min(STEEPEST, self.pitch + TURN * down))

  def zoomed(self, notches: float) -> None:
    """The 'zoomed' method brings the camera nearer ('notches' over
    nought) or further."""
    self.distance = max(NEAREST, min(FURTHEST, self.distance
                                     * ZOOM ** notches))

  def eyeOf(self, vessel: Vessel, system: SolarSystem) -> tuple:
    """The 'eyeOf' method returns where the camera is from the vessel
    (m, the ecliptic's axes), the way it looks and its up."""
    up, north, east = horizonOf(vessel.place, system.bodies[
      vessel.anchor].pole)
    level = math.cos(self.pitch)
    way = tuple(level * (math.cos(self.yaw) * n + math.sin(self.yaw) * e)
                + math.sin(self.pitch) * u for n, e, u in zip(north, east,
                                                              up))
    offset = tuple(self.distance * x for x in way)
    return offset, tuple(-x for x in way), up


def horizonOf(place: tuple, pole: tuple) -> tuple:
  """Returns the up, north and east at 'place' (from a body's middle)
  on a body turning about 'pole': unit vectors."""
  up = unit(place)
  north = tuple(p - dot(pole, up) * u for p, u in zip(pole, up))
  if math.sqrt(dot(north, north)) < 1e-9:
    north = (1.0, 0.0, 0.0)
  north = unit(north)
  return up, north, cross(north, up)
