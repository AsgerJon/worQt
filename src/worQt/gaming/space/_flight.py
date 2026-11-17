"""
Flight moves vessels through a solar system on a device of Warp's (the
GPU in the game, the CPU in the tests): their states taken there,
'_flight_kernels.flown' launched, taken back; then each kept from the
body it is now near. Given the space station, each vessel meets its
solids: the station from the vessel at the frame's start, and which
of its solids could be met within the frame ('NEAR_MARGIN' over the
hull's reach and the frame's closing), however it turns.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import numpy

from ._turns import norm, quaternionOf

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._station import Station
  from ._vessel import Vessel


def preloadedFlight(device: str) -> float:
  """Has the flight's kernel loaded on 'device' (compiled the first
  time, else from Warp's cache) and returns how long it took, s."""
  import warp as wp

  from . import _flight_kernels
  began = time.perf_counter()
  wp.init()
  wp.load_module(_flight_kernels, device)
  return time.perf_counter() - began


#  A solid is near a vessel within the hull's reach, this, and how far
#  they close in the frame, m.
NEAR_MARGIN = 10.0


class Flight:
  """
  Flight moves vessels on 'device' ('flown'): a frame's time in one
  launch. The sky's numbers go to the device once a leap (the system's
  'version'); each vessel's state each frame, its place and velocity in
  two float32s (a big part and the rest: every float64 bit kept), its
  height over the ground worked out here in float64 (the kernel's
  heights are small differences from it). After a launch each vessel is
  handed to the body it is now near ('SolarSystem.anchorFor'). 'lastSteps'
  and 'lastMs' say what the last launch took.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  device: str
  lastSteps: int
  lastMs: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, device: str) -> None:
    import warp as wp

    from . import _flight_kernels
    preloadedFlight(device)
    self.wp, self.kernels, self.device = wp, _flight_kernels, device
    self._sky, self._skyOf = None, None
    self._fleet, self._fleetKey = None, None
    self.lastSteps, self.lastMs = 0, 0.0
    self._near = numpy.zeros(0, numpy.int32)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def flown(self, vessels: tuple, system: SolarSystem, start: float,
            seconds: float, longest: float = math.inf,
            station: Station = None) -> None:
    """The 'flown' method moves 'vessels' 'seconds' s on through
    'system' from its time 'start' (s since its last leap), no step
    longer than 'longest' s, meeting 'station's solids (if given), and
    hands each to the body it is then near."""
    if seconds <= 0.0 or not vessels:
      return
    began = time.perf_counter()
    wp = self.wp
    sky = self._skyFor(system)
    fleet = self._fleetOf(vessels, system)
    self._stationFor(fleet, vessels, system, station, start, seconds)
    wp.launch(self.kernels.flown, len(vessels), [
      sky, fleet, float(start), float(seconds),
      float(min(longest, 1e30))], [], [], [], self.device)
    self._taken(vessels, fleet)
    for vessel in vessels:
      self._handed(vessel, system, start + seconds)
    self.lastMs = 1e3 * (time.perf_counter() - began)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _skyFor(self, system: SolarSystem) -> object:
    """Returns the sky's numbers on the device, made anew after a
    leap."""
    key = id(system), system.version
    if self._skyOf == key:
      return self._sky
    wp, kernels = self.wp, self.kernels
    sky = kernels.Sky()
    bodies = system.bodies
    sky.count = len(bodies)
    sky.parents = self._sent(system.parents, wp.int32)
    sky.depths = self._sent([b.depth for b in bodies], wp.int32)
    sky.mus = self._sent([b.mu for b in bodies], wp.float32)
    sky.radii = self._sent([b.radius for b in bodies], wp.float32)
    conics = [b.conic for b in bodies]
    sky.axes = self._sent([c.a if c else 0.0 for c in conics],
                          wp.float32)
    sky.es = self._sent([c.e if c else 0.0 for c in conics], wp.float32)
    sky.motions = self._sent([c.motion if c else 0.0 for c in conics],
                             wp.float32)
    sky.anomalies = self._sent([c.anomaly if c else 0.0 for c in conics],
                               wp.float32)
    eye = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    sky.turns = self._sent([c.turn if c else eye for c in conics],
                           wp.mat33)
    sky.spins = self._sent([b.spinVector for b in bodies], wp.vec3)
    tops, starts, steps, logs = [], [], [], []
    for body in bodies:
      air = body.air
      tops.append(air.top if air else 0.0)
      starts.append(len(logs))
      steps.append(air.step if air else 1.0)
      if air:
        logs.extend(air.logs)
    sky.airTops = self._sent(tops, wp.float32)
    sky.airStarts = self._sent(starts, wp.int32)
    sky.airSteps = self._sent(steps, wp.float32)
    sky.airLogs = self._sent(logs or [0.0], wp.float32)
    self._sky, self._skyOf = sky, key
    return sky

  def _fleetOf(self, vessels: tuple, system: SolarSystem) -> object:
    """Returns the vessels on the device: the arrays made once for so
    many vessels in so big a sky (what never changes filled then), the
    rows of what changes copied in each call, all at once."""
    k = self.kernels
    count = len(vessels)
    key = count, len(system.bodies)
    if self._fleetKey != key:
      self._fleet, self._fleetKey = self._fleetMade(count, key[1]), key
    rows = numpy.zeros((count, k.STATE), numpy.float32)
    for row, vessel in zip(rows, vessels):
      place = numpy.array(vessel.place, numpy.float64)
      speed = numpy.array(vessel.velocity, numpy.float64)
      high, fast = place.astype(numpy.float32), speed.astype(numpy.float32)
      row[k.PLACE_HI:k.PLACE_HI + 3] = high
      row[k.PLACE_LO:k.PLACE_LO + 3] = place - high
      row[k.SPEED_HI:k.SPEED_HI + 3] = fast
      row[k.SPEED_LO:k.SPEED_LO + 3] = speed - fast
      row[k.TURN:k.TURN + 4] = _warpQuat(vessel.turn)
      row[k.SPIN:k.SPIN + 3] = vessel.spin
      row[k.HEIGHT] = norm(vessel.place) - system.bodies[
        vessel.anchor].radius
      row[k.PUSH] = vessel.engine.push
      row[k.RCS:k.RCS + 3] = vessel.rcs
      row[k.MATCH_SPIN:k.MATCH_SPIN + 3] = vessel.autopilot.spin
      row[k.STEER:k.STEER + 3] = vessel.steer
      row[k.MODE] = vessel.autopilot.index
      pilot = vessel.autopilot
      row[k.HELD:k.HELD + 4] = _warpQuat(pilot.held)
      row[k.AIM_PITCH] = pilot.pitch
      row[k.AIM_TURN] = pilot.turn
      row[k.AIM_HEADING] = pilot.heading
      row[k.AIM_TRAVEL] = 1.0 if pilot.travel else 0.0
      row[k.ANCHOR] = vessel.anchor
    self._fleet.states.assign(rows)
    return self._fleet

  def _fleetMade(self, count: int, bodies: int) -> object:
    """Returns the fleet's arrays on the device for 'count' vessels in a
    sky of 'bodies' bodies, the creative rocket's own numbers in."""
    wp, kernels, device = self.wp, self.kernels, self.device
    from ._vessel import DRAG, INERTIA, LEGS, MASS, WHEELS
    fleet = kernels.Fleet()
    fleet.states = wp.zeros((count, kernels.STATE), wp.float32, device)
    fleet.masses = self._sent([MASS] * count, wp.float32)
    fleet.inertias = self._sent([INERTIA] * count, wp.vec3)
    fleet.legs = self._sent([leg for _ in range(count) for leg in LEGS],
                            wp.vec3)
    fleet.drags = self._sent([DRAG] * count, wp.vec2)
    fleet.wheels = self._sent([WHEELS] * count, wp.vec3)
    fleet.offsets = wp.zeros(count * bodies * kernels.SLOTS, wp.vec3,
                             device)
    from ._stationsolids import hullBalls, stationSolids
    solids = stationSolids()
    fleet.balls = self._sent(hullBalls(), wp.vec4)
    fleet.solidKinds = self._sent([s[0] for s in solids], wp.int32)
    fleet.solidFrom = self._sent([s[1] for s in solids], wp.vec3)
    fleet.solidTo = self._sent([s[2] for s in solids], wp.vec3)
    fleet.solidRadii = self._sent([s[3] for s in solids], wp.float32)
    fleet.near = wp.zeros(count, wp.int32, device)
    fleet.solidAt = wp.zeros(count, wp.vec3, device)
    fleet.solidSpeed = wp.zeros(count, wp.vec3, device)
    fleet.solidFall = wp.zeros(count, wp.vec3, device)
    fleet.solidTurn = self._sent([(0.0, 0.0, 0.0, 1.0)] * count, wp.quat)
    fleet.solidSpin = wp.zeros(count, wp.vec3, device)
    fleet.stationAt = wp.zeros(count, wp.vec3, device)
    fleet.stationVel = wp.zeros(count, wp.vec3, device)
    self._near = numpy.zeros(count, numpy.int32)
    return fleet

  def _stationFor(self, fleet: object, vessels: tuple,
                  system: SolarSystem, station: Station, start: float,
                  seconds: float) -> None:
    """Tells the kernel where 'station' is from each vessel at 'start'
    and which of its solids it could meet within 'seconds' s (none
    without a station): a vessel's near solids are those its middle is
    within the hull's reach, 'NEAR_MARGIN' and the frame's closing of,
    however the station turns ('sweptDistance')."""
    from ._stationsolids import hullReach, stationSolids, sweptDistance
    near = numpy.zeros(len(vessels), numpy.int32)
    if station is None:
      if self._near.any():
        fleet.near.assign(near)
        self._near = near
      return
    solids = stationSolids()
    at, speeds, falls, turns, spins = [], [], [], [], []
    rounds, rounding = [], []
    rows = station.turnAt(start)
    turn = _warpQuat(quaternionOf(rows))
    axis = tuple(row[2] for row in rows)
    spin = tuple(station.body.spin * a for a in axis)
    parent = system.bodies[station.parent]
    middle, velocity = station.stateAt(start)
    r = norm(middle)
    fall = tuple(-parent.mu * m / r ** 3 for m in middle)
    for k, vessel in enumerate(vessels):
      there, moving = system.relative(station.parent, vessel.anchor,
                                      start)
      offset = tuple(a + m - p for a, m, p in zip(there, middle,
                                                  vessel.place))
      speed = tuple(a + v for a, v in zip(moving, velocity))
      at.append(offset)
      speeds.append(speed)
      rounds.append(tuple(a + m for a, m in zip(there, middle)))
      rounding.append(speed)
      falls.append(fall)
      turns.append(turn)
      spins.append(spin)
      if vessel.docked:
        continue
      own = tuple(-sum(rows[i][j] * offset[i] for i in range(3))
                  for j in range(3))
      closing = norm(tuple(v - s for v, s in zip(vessel.velocity, speed)))
      reach = hullReach() + NEAR_MARGIN + closing * seconds
      for j, solid in enumerate(solids):
        if sweptDistance(solid, own) < reach:
          near[k] |= 1 << j
    fleet.near.assign(near)
    self._near = near
    fleet.solidAt.assign(numpy.asarray(at, numpy.float32))
    fleet.solidSpeed.assign(numpy.asarray(speeds, numpy.float32))
    fleet.solidFall.assign(numpy.asarray(falls, numpy.float32))
    fleet.solidTurn.assign(numpy.asarray(turns, numpy.float32))
    fleet.solidSpin.assign(numpy.asarray(spins, numpy.float32))
    fleet.stationAt.assign(numpy.asarray(rounds, numpy.float32))
    fleet.stationVel.assign(numpy.asarray(rounding, numpy.float32))

  def _taken(self, vessels: tuple, fleet: object) -> None:
    """Takes the vessels' states back from the device, all at once; the
    big parts and rests summed in float64 (every bit kept)."""
    k = self.kernels
    rows = fleet.states.numpy().astype(numpy.float64)
    steps = 0
    for row, vessel in zip(rows, vessels):
      place = row[k.PLACE_HI:k.PLACE_HI + 3] + row[k.PLACE_LO:k.PLACE_LO
                                                    + 3]
      speed = row[k.SPEED_HI:k.SPEED_HI + 3] + row[k.SPEED_LO:k.SPEED_LO
                                                    + 3]
      x, y, z, w = row[k.TURN:k.TURN + 4]
      vessel.placed(vessel.anchor, tuple(place.tolist()),
                    tuple(speed.tolist()), (w, x, y, z),
                    tuple(row[k.SPIN:k.SPIN + 3].tolist()))
      vessel.touching = int(row[k.TOUCHING])
      vessel.bumped = float(row[k.BUMP])
      steps = max(steps, int(row[k.STEPS]))
    self.lastSteps = steps

  def _handed(self, vessel: Vessel, system: SolarSystem,
              t: float) -> None:
    """Hands 'vessel' to the body it is near at time 't': its place and
    velocity then from that body."""
    anchor = system.anchorFor(vessel.anchor, vessel.place, t)
    if anchor == vessel.anchor:
      return
    there, moving = system.relative(anchor, vessel.anchor, t)
    place = tuple(a - b for a, b in zip(vessel.place, there))
    velocity = tuple(a - b for a, b in zip(vessel.velocity, moving))
    vessel.placed(anchor, place, velocity, vessel.turn, vessel.spin)

  def _sent(self, values: object, kind: object) -> object:
    """Returns 'values' as a Warp array of 'kind' on the device."""
    wp = self.wp
    host = numpy.ascontiguousarray(numpy.asarray(values, numpy.float32
                                                 if kind not in (
      wp.int32,) else numpy.int32))
    return wp.array(host, kind, None, None, None, None, self.device)


def _warpQuat(turn: tuple) -> tuple:
  """Returns the quaternion 'turn' (w x y z) in Warp's order (x y z
  w)."""
  w, x, y, z = turn
  return x, y, z, w
