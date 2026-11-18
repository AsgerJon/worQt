"""
Flight moves vessels through a solar system on a device of Warp's (the
GPU in the game, the CPU in the tests): their states taken there,
'_flight_kernels.flown' launched, taken back; then each kept from the
body it is now near. Given the space station, each vessel meets its
solids: the station from the vessel at the frame's start, and which
of its solids could be met within the frame ('NEAR_MARGIN' over the
hull's reach and the frame's closing), however it turns; what they
pushed the vessel by pushes the station back ('Station.struck'). The
station may be one of the vessels flown (it is flown as they are).
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
  Flight moves vessels on 'device' ('flown'): a frame's time in one launch.
  The sky's numbers go to the device as its table changes (the system's
  'version', its ephemeris's); each vessel's state each frame, its place and
  velocity in two float32s (a big part and the rest: every float64 bit kept),
  its height over the ground worked out here in float64 (the kernel's heights
  are small differences from it). After a launch each vessel is handed to the
  body it is now near ('SolarSystem.anchorFor'). 'lastSteps' and 'lastMs' say
  what the last launch took.
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
    self._fleet, self._fleetKey, self._dragless = None, None, False
    self.lastSteps, self.lastMs = 0, 0.0
    self._near = numpy.zeros(0, numpy.int32)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def flown(self, vessels: tuple, system: SolarSystem, start: float,
            seconds: float, longest: float = math.inf,
            station: Station = None, dragless: bool = False) -> None:
    """The 'flown' method moves 'vessels' 'seconds' s on through
    'system' from its time 'start' (s since its last leap), no step
    longer than 'longest' s, meeting 'station's solids (if given), the
    air not dragging them if 'dragless' (time warped: user, 2026-11-17,
    "When warp is activated we disregard drag from the atmosphere"), and
    hands each to the body it is then near."""
    if seconds <= 0.0 or not vessels:
      return
    began = time.perf_counter()
    wp = self.wp
    system.coveredTo(start + seconds)
    sky = self._skyFor(system)
    fleet = self._fleetOf(vessels, system)
    self._draggedOrNot(fleet, vessels, bool(dragless))
    self._stationFor(fleet, vessels, system, station, start, seconds)
    wp.launch(self.kernels.flown, len(vessels), [
      sky, fleet, float(start), float(seconds),
      float(min(longest, 1e30))], [], [], [], self.device)
    struck = self._taken(vessels, fleet)
    if station is not None and (any(struck[0]) or any(struck[1])):
      station.struck(*struck)
    for vessel in vessels:
      self._handed(vessel, system, start + seconds)
    self.lastMs = 1e3 * (time.perf_counter() - began)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _skyFor(self, system: SolarSystem) -> object:
    """Returns the sky's numbers on the device, made anew after a
    leap."""
    ephemeris = system.ephemeris
    key = id(system), system.version, ephemeris.version
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
    rows = ephemeris.rows
    sky.table = self._sent(rows.transpose(0, 2, 1, 3).reshape(-1, 3),
                           wp.vec3)
    sky.tableStart = float(ephemeris.start)
    sky.tableRows = int(len(rows))
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
    builds = tuple((v.mass, tuple(v.inertia), tuple(v.legs), tuple(v.drag),
                    tuple(v.attitude)) for v in vessels)
    key = count, len(system.bodies), builds
    if self._fleetKey != key:
      self._fleet = self._fleetMade(vessels, key[1])
      self._fleetKey, self._dragless = key, None
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
      if vessel.latch is not None:
        port, turn, nose = vessel.latch
        row[k.LATCHED] = 1.0
        row[k.LATCH_PORT:k.LATCH_PORT + 3] = port
        row[k.LATCH_TURN:k.LATCH_TURN + 4] = _warpQuat(turn)
        row[k.LATCH_NOSE:k.LATCH_NOSE + 3] = nose
    self._fleet.states.assign(rows)
    return self._fleet

  def _draggedOrNot(self, fleet: object, vessels: tuple,
                    dragless: bool) -> None:
    """Gives the vessels their drag, or none ('dragless'), when that
    changes."""
    if dragless == self._dragless:
      return
    drags = [(0.0, 0.0) if dragless else tuple(v.drag) for v in vessels]
    fleet.drags.assign(numpy.asarray(drags, numpy.float32))
    self._dragless = dragless

  def _fleetMade(self, vessels: tuple, bodies: int) -> object:
    """Returns the fleet's arrays on the device for 'vessels' in a sky
    of 'bodies' bodies, each vessel's own build in (its mass, moments,
    legs, drag, attitude thrusters)."""
    wp, kernels, device = self.wp, self.kernels, self.device
    count = len(vessels)
    fleet = kernels.Fleet()
    fleet.states = wp.zeros((count, kernels.STATE), wp.float32, device)
    fleet.masses = self._sent([v.mass for v in vessels], wp.float32)
    fleet.inertias = self._sent([tuple(v.inertia) for v in vessels],
                                wp.vec3)
    fleet.legs = self._sent([tuple(leg) for v in vessels
                             for leg in v.legs], wp.vec3)
    fleet.drags = self._sent([tuple(v.drag) for v in vessels], wp.vec2)
    fleet.attitude = self._sent([tuple(v.attitude) for v in vessels],
                                wp.vec3)
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
    spin = station.spinAt(start)
    middle, velocity = station.stateAt(start)
    fall = system.pullOn(station.parent, middle, start)
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
      if vessel.docked or vessel is station.body:
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

  def _taken(self, vessels: tuple, fleet: object) -> tuple:
    """Takes the vessels' states back from the device, all at once; the
    big parts and rests summed in float64 (every bit kept); returns what
    their hulls pushed the space station by, summed (N s, and its twist
    about the station's middle, N m s, the ecliptic's axes)."""
    k = self.kernels
    rows = fleet.states.numpy().astype(numpy.float64)
    steps = 0
    struck = numpy.zeros(3)
    twist = numpy.zeros(3)
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
      vessel.felt = tuple(row[k.FELT:k.FELT + 3].tolist())
      vessel.spinning = tuple(row[k.SPINNING:k.SPINNING + 3].tolist())
      steps = max(steps, int(row[k.STEPS]))
      struck += row[k.STRUCK:k.STRUCK + 3]
      twist += row[k.STRUCK_TWIST:k.STRUCK_TWIST + 3]
    self.lastSteps = steps
    return tuple(struck.tolist()), tuple(twist.tolist())

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
