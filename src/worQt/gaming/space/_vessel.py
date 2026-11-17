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
from ._autopilot import Autopilot, aimOf
from ._conic import Conic
from ._turns import aboutAxis, cross, dot, matrixBack, matrixTimes, norm
from ._turns import product, quaternionOf, rotated, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem

#  The creative rocket, its own axes z along it, nose up, its middle its
#  centre of mass: how many times its first size it is (user,
#  2026-11-16: "Size is more like four times as large. we'll cheat to
#  make it possible with the engine": 64 m tall, 10 m round, a room for a
#  cabin), its mass (kg, its first one's as dense; its fuel never runs
#  out, so it never changes), how far its centre is over its feet (m),
#  its parts from the feet up (m: the aerospike's plug, the tank, the
#  capsule) and its radius (m).
SIZE = 4.0
MASS = 20e3 * SIZE ** 3
CENTRE = 7.0 * SIZE
PLUG = (0.6 * SIZE, 2.0 * SIZE)
TANK = (2.0 * SIZE, 13.0 * SIZE)
CAPSULE = (13.0 * SIZE, 16.0 * SIZE)
RADIUS = 1.25 * SIZE
#  Its moments of inertia about its own x, y, z, kg m²: a solid
#  cylinder its length.
LONG = CAPSULE[1]
INERTIA = (MASS * (3.0 * RADIUS * RADIUS + LONG * LONG) / 12.0,
           MASS * (3.0 * RADIUS * RADIUS + LONG * LONG) / 12.0,
           0.5 * MASS * RADIUS * RADIUS)
#  Its four legs' feet, its own axes (m from its centre), 'SPREAD' m out.
SPREAD = 2.2 * SIZE
LEGS = ((SPREAD, 0.0, -CENTRE), (0.0, SPREAD, -CENTRE),
        (-SPREAD, 0.0, -CENTRE), (0.0, -SPREAD, -CENTRE))
#  Its drag coefficient times area, m²: along it (its nose's cone) and
#  across it (a cylinder side on).
DRAG = (0.4 * math.pi * RADIUS * RADIUS, 1.0 * 2.0 * RADIUS * LONG)
#  Its engine: 4 g of lift on Terra's pad (user, 2026-11-16: "1.5g aint
#  cutting it! i have not achieved an orbit yet, it's too slow. Try 4g";
#  magic: no engine of its size lifts it so), the magic fuel's specific
#  impulse.
THRUST = 4.0 * MASS * 9.82
#  Its reaction wheels' most torque about its own x, y, z, N m: magic,
#  creative ones, a quarter turn in about four seconds whatever its size
#  (its inertia grows as its size's fifth power).
WHEELS = (150e3 * SIZE ** 5, 150e3 * SIZE ** 5, 30e3 * SIZE ** 5)
#  How far its legs give standing (the legs' stiffness is the kernel's:
#  'LEG_STIFF'), m.
SAG = 0.0049
#  Going this fast over the horizon, m/s, a vessel has a path for the aim
#  to follow (before, its aim keeps a compass heading: on the pad, east).
TRAVEL_SPEED = 20.0


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
  Its docking thrusters push it 'rcs' (N, its own axes: user,
  2026-11-17, docking); 'docked' to the space station it rides with it
  (moved by it, not by the flight); 'bumped' how fast it last hit the
  station (m/s into it, the last frame; nought: it did not). The
  flight's kernel moves it ('Flight').
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
  rcs: tuple
  docked: bool
  bumped: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.engine = Aerospike(THRUST, MAGIC_ISP)
    self.autopilot = Autopilot()
    self.steer, self.anchor, self.touching = (0.0, 0.0, 0.0), 0, 0
    self.place, self.velocity = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self.turn, self.spin = (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self.rcs, self.docked, self.bumped = (0.0, 0.0, 0.0), False, 0.0

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

  def carried(self, system: SolarSystem, seconds: float) -> None:
    """The 'carried' method moves the vessel 'seconds' s on as it rests
    on its anchor's turning ground (user, 2026-11-17: a night slept on
    the pad): its place, velocity and turn round the body's pole with
    it, its own spin as it was."""
    body = system.bodies[self.anchor]
    turn = aboutAxis(body.pole, body.spin * seconds)
    self.placed(self.anchor, rotated(turn, self.place),
                rotated(turn, self.velocity), product(turn, self.turn),
                self.spin)

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

  def pathOf(self, system: SolarSystem) -> tuple:
    """The 'pathOf' method returns the velocity its autopilot's path
    is: over the ground (and the air) in the air, the orbit's above
    it."""
    air = system.bodies[self.anchor].air
    if air is not None and self.heightOver(system) < air.top:
      return self.groundVelocity(system)
    return self.velocity

  def aimDirection(self, system: SolarSystem) -> tuple:
    """The 'aimDirection' method returns where the aim mode points now
    (a unit vector), as the kernel reckons it."""
    pilot = self.autopilot
    return aimOf(self.place, self.pathOf(system), system.bodies[
      self.anchor].spinVector, pilot.pitch, pilot.turn, pilot.heading,
                 pilot.travel)

  def noseAngles(self, system: SolarSystem) -> tuple:
    """The 'noseAngles' method returns its nose's pitch over the horizon
    and its compass heading (from north toward east), rad."""
    up, north, east = self._horizon(system)
    nose = self.nose
    return (math.asin(max(-1.0, min(1.0, dot(nose, up)))),
            math.atan2(dot(nose, east), dot(nose, north)) % (2.0 * math.pi))

  def aimNudged(self, system: SolarSystem, pitch: float,
                turn: float) -> None:
    """The 'aimNudged' method moves the aim 'pitch' rad up and 'turn' rad
    right (off the path; before there is one, round the compass); not
    aiming yet, it aims first where the nose points (the user: "roll-
    insensitive controls that work only in the parallel of travel")."""
    pilot = self.autopilot
    if pilot.mode != 'aim':
      self._aimSeeded(system)
    if pilot.travel:
      pilot.aimedAt(pilot.pitch + pitch, pilot.turn + turn, pilot.heading,
                    True)
    else:
      pilot.aimedAt(pilot.pitch + pitch, 0.0, pilot.heading + turn, False)

  def aimKept(self, system: SolarSystem) -> None:
    """The 'aimKept' method lets the aim follow the path once there is
    one (going 'TRAVEL_SPEED' over the horizon): the compass heading it
    kept is taken up into the path, the aim not moving."""
    pilot = self.autopilot
    if pilot.mode != 'aim' or pilot.travel:
      return
    if self._flatPath(system) is None:
      return
    aim = self.aimDirection(system)
    pitch, turn = self._anglesOnPath(system, aim)
    pilot.aimedAt(pitch, turn, pilot.heading, True)

  def _aimSeeded(self, system: SolarSystem) -> None:
    """Aims the autopilot where the nose points: along the path if it
    has one, else on the compass (straight up: east)."""
    nose = self.nose
    if self._flatPath(system) is not None:
      pitch, turn = self._anglesOnPath(system, nose)
      self.autopilot.aimedAt(pitch, turn, 0.5 * math.pi, True)
      return
    pitch, heading = self.noseAngles(system)
    if pitch > 1.55:
      heading = 0.5 * math.pi
    self.autopilot.aimedAt(pitch, 0.0, heading, False)

  def _anglesOnPath(self, system: SolarSystem, way: tuple) -> tuple:
    """Returns the pitch over the horizon and the turn off the path of
    the unit 'way', rad (the aim mode's)."""
    up = unit(self.place)
    flat = self._flatPath(system)
    right = cross(flat, up)
    turn = math.asin(max(-1.0, min(1.0, dot(way, right))))
    return math.atan2(dot(way, up), dot(way, flat)), turn

  def _flatPath(self, system: SolarSystem) -> tuple | None:
    """Returns the way of its path over the horizon (a unit vector);
    None going slower than 'TRAVEL_SPEED' over it."""
    up = unit(self.place)
    path = self.pathOf(system)
    along = dot(path, up)
    flat = tuple(a - along * b for a, b in zip(path, up))
    if norm(flat) < TRAVEL_SPEED:
      return None
    return unit(flat)

  def _horizon(self, system: SolarSystem) -> tuple:
    """Returns the up, north and east where it is (unit vectors)."""
    up = unit(self.place)
    spin = system.bodies[self.anchor].spinVector
    axis = unit(spin) if norm(spin) > 1e-12 else (0.0, 0.0, 1.0)
    east = cross(axis, up)
    if norm(east) < 1e-6:
      east = cross((1.0, 0.0, 0.0), up)
    east = unit(east)
    return up, cross(up, east), east
