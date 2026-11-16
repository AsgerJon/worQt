"""
Flight moves vessels through a solar system on a device of Warp's (the
GPU in the game, the CPU in the tests): their states taken there,
'_flight_kernels.flown' launched, taken back; then each kept from the
body it is now near.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import numpy

from ._turns import norm

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def flown(self, vessels: tuple, system: SolarSystem, start: float,
            seconds: float, longest: float = math.inf) -> None:
    """The 'flown' method moves 'vessels' 'seconds' s on through
    'system' from its time 'start' (s since its last leap), no step
    longer than 'longest' s, and hands each to the body it is then near.
    """
    if seconds <= 0.0 or not vessels:
      return
    began = time.perf_counter()
    wp = self.wp
    sky = self._skyFor(system)
    fleet = self._fleetOf(vessels, system)
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
    return fleet

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
