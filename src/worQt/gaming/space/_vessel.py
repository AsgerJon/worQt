"""
Vessel is a rocket in the solar system (user, 2026-11-16: "let's start
with a 'creative' rocket with inf fuel"): one rigid body, its engine,
its reaction wheels, its autopilot, its legs; where it is, kept from
the body it is near.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._aerospike import MAGIC_ISP, Aerospike
from ._autopilot import Autopilot
from ._conic import Conic
from ._turns import cross, matrixBack, matrixTimes, norm, quaternionOf
from ._turns import rotated, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem

#  The creative rocket, its own axes z along it, nose up, its middle its
#  centre of mass: its mass (kg; its fuel never runs out, so it never
#  changes), how far its centre is over its feet (m), its parts from the
#  feet up (m: the aerospike's plug, the tank, the capsule) and its
#  radius (m).
MASS = 20e3
CENTRE = 7.0
PLUG = (0.6, 2.0)
TANK = (2.0, 13.0)
CAPSULE = (13.0, 16.0)
RADIUS = 1.25
#  Its moments of inertia about its own x, y, z, kg m²: a solid
#  cylinder its length.
LONG = CAPSULE[1]
INERTIA = (MASS * (3.0 * RADIUS * RADIUS + LONG * LONG) / 12.0,
           MASS * (3.0 * RADIUS * RADIUS + LONG * LONG) / 12.0,
           0.5 * MASS * RADIUS * RADIUS)
#  Its four legs' feet, its own axes (m from its centre), 'SPREAD' m out.
SPREAD = 2.2
LEGS = ((SPREAD, 0.0, -CENTRE), (0.0, SPREAD, -CENTRE),
        (-SPREAD, 0.0, -CENTRE), (0.0, -SPREAD, -CENTRE))
#  Its drag coefficient times area, m²: along it (its nose's cone) and
#  across it (a cylinder side on).
DRAG = (0.4 * math.pi * RADIUS * RADIUS, 1.0 * 2.0 * RADIUS * LONG)
#  Its engine: 1.5 g of lift on Terra's pad (the spec), the magic fuel's
#  specific impulse.
THRUST = 1.5 * MASS * 9.82
#  Its reaction wheels' most torque about its own x, y, z, N m: magic,
#  creative ones, a quarter turn in about four seconds.
WHEELS = (150e3, 150e3, 30e3)
#  How far its legs give standing (the legs' stiffness is the kernel's:
#  'LEG_STIFF'), m.
SAG = 0.0049


class Vessel:
  """
  Vessel holds a rocket: its body ('MASS', 'INERTIA', 'LEGS', 'DRAG'),
  its 'engine' (an 'Aerospike'), its reaction wheels ('WHEELS', worked
  by the keys, 'steer': pitch, yaw, roll, each from minus one to one,
  else by its 'autopilot'). Where it is: the body it is kept from
  ('anchor', its index in the solar system: user, "Each vehicle is
  stored as the planet it's near"), its 'place' and 'velocity' from that
  body's middle (m, m/s, the ecliptic's axes, which turn with nothing),
  its 'turn' (w x y z, its own axes to the ecliptic's) and 'spin' (rad/s,
  its own axes); how many of its legs stand on the ground ('touching').
  The flight's kernel moves it ('Flight').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  engine: Aerospike
  autopilot: Autopilot
  steer: tuple
  anchor: int
  place: tuple
  velocity: tuple
  turn: tuple
  spin: tuple
  touching: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.engine = Aerospike(THRUST, MAGIC_ISP)
    self.autopilot = Autopilot()
    self.steer, self.anchor, self.touching = (0.0, 0.0, 0.0), 0, 0
    self.place, self.velocity = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self.turn, self.spin = (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def nose(self, ) -> tuple:
    """The 'nose' property is the way its nose points, a unit vector in
    the ecliptic's axes."""
    return rotated(self.turn, (0.0, 0.0, 1.0))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def placed(self, anchor: int, place: tuple, velocity: tuple,
             turn: tuple, spin: tuple) -> None:
    """The 'placed' method puts the vessel at 'place' moving at
    'velocity' (from body 'anchor', m and m/s), turned by 'turn' and
    spinning at 'spin' (its own axes, rad/s)."""
    size = math.sqrt(sum(x * x for x in turn))
    self.anchor = int(anchor)
    self.place = tuple(float(x) for x in place)
    self.velocity = tuple(float(x) for x in velocity)
    self.turn = tuple(float(x) / size for x in turn)
    self.spin = tuple(float(x) for x in spin)

  def stood(self, system: SolarSystem, anchor: int, latitude: float,
            longitude: float, t: float) -> None:
    """The 'stood' method stands the vessel upright on its legs on body
    'anchor' at 'latitude' and 'longitude' (deg) at time 't', at rest on
    its turning ground: its own x east, y north."""
    body = system.bodies[anchor]
    turn = body.turnAt(t)
    lat, lon = math.radians(latitude), math.radians(longitude)
    up = matrixTimes(turn, (math.cos(lat) * math.cos(lon),
                            math.cos(lat) * math.sin(lon), math.sin(lat)))
    east = unit(cross(body.pole, up))
    north = cross(up, east)
    rows = tuple((east[k], north[k], up[k]) for k in range(3))
    spin = body.spinVector
    place = tuple((body.radius + CENTRE - SAG) * x for x in up)
    self.placed(anchor, place, cross(spin, place), quaternionOf(rows),
                matrixBack(rows, spin))

  def steered(self, pitch: float, yaw: float, roll: float) -> None:
    """The 'steered' method sets the keys on the reaction wheels (each
    from minus one to one); let go while holding, the autopilot holds
    the turn the vessel has then (the spec: "While you steer it lets
    go, and it locks the new orientation when you release")."""
    was = any(self.steer)
    self.steer = tuple(max(-1.0, min(1.0, float(x)))
                       for x in (pitch, yaw, roll))
    if was and not any(self.steer) and self.autopilot.mode == 'hold':
      self.autopilot.engaged('hold', self.turn)

  def heightOver(self, system: SolarSystem) -> float:
    """The 'heightOver' method returns how high its centre is over its
    anchor's ground, m."""
    return norm(self.place) - system.bodies[self.anchor].radius

  def groundVelocity(self, system: SolarSystem) -> tuple:
    """The 'groundVelocity' method returns its velocity over its
    anchor's turning ground (and air), m/s."""
    spin = system.bodies[self.anchor].spinVector
    moving = cross(spin, self.place)
    return tuple(a - b for a, b in zip(self.velocity, moving))

  def conicOf(self, system: SolarSystem) -> Conic | None:
    """The 'conicOf' method returns the path it coasts on round its
    anchor, its anchor pulling alone (the moons nudge it off), its time
    nought now; None when it has none (still, or falling straight
    down: no turning about the anchor at all)."""
    try:
      return Conic.fromState(system.bodies[self.anchor].mu, self.place,
                             self.velocity)
    except ValueError:
      return None
