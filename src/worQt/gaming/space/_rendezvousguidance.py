"""
RendezvousGuidance brings the rocket from its orbit round Terra to the
space station, near enough for the automatic docking (user, 2026-11-17:
"we include buttons so that a try-hard *could* manually do the thing.
If he hates fun. But where we also provide an automated system for the
rest of. Same with docking"): the try-hard flies there by the engine,
the autopilot and the warp; AUTO does it all.

It aims at a point 'APART' m from the station along its path (the
station's own state a moment off: a place on its orbit, moving as it
would there), on the side the rocket comes from: ahead of it when the
rocket arrives slower (rising from a lower orbit it drifts back onto
the point), behind when faster; so it overtakes the station mid-way,
far below or above it, never through the wheel (aimed behind from
below, it passed the hub 600 m off). First, if the rocket's orbit is
tilted off the station's, it turns it into the station's plane at the
next crossing.
Then it plans: every departure within 'WAIT_MOST' (a step a share of
the rocket's turn round) against every flight time (shares of the
transfer's turn round), each a coast between two places in a time
(Lambert's problem, 'Transfers' on Warp's device), the cheapest by the
speed it costs to leave and to arrive and the wait; that plan refined
twice, finer. It warps to the burn, turns the nose, burns (the speed to
gain worked out anew each frame from where the rocket is: a burn of
any length lands on the point), coasts warped, its course checked at
halves of the time left and corrected (by the docking thrusters when
small), and at the point matches its speed. Further off than
'HOP_OVER', it hops again (a short transfer); near, it is done: the
automatic docking takes over. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy

from ._conic import Conic
from ._dockingguidance import RCS_ACCEL, REACH
from ._turns import cross, dot, norm, quaternionOf, rotated, unit
from ._turns import unrotated
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._station import Station
  from ._timekeeper import Timekeeper
  from ._transfers import Transfers
  from ._vessel import Vessel

#  It aims 'APART' m from the station along its path.
APART = 2000.0
#  Orbits tilted less than 'PLANE_SAME' rad off the station's are in its
#  plane (a tilt left over costs the transfer a little).
PLANE_SAME = math.radians(0.05)
#  The plan: departures 'DEPARTURES' a turn of the rocket round, within
#  'WAIT_MOST' s; flight times 'FLIGHTS' (shares of the turn round of
#  the transfer between the two orbits' sizes); a second's wait costs
#  'WAIT_PRICE' m/s; no transfer within 'NEAR_HALF' rad of half a turn
#  (its plane unknown) nor dipping under 'FLOOR' m over the ground (or
#  the air's top); refined 'REFINES' times, 'REFINE' cells either side,
#  each a quarter as wide.
DEPARTURES = 16
WAIT_MOST = 2.0 * 86400.0
FLIGHTS = tuple(0.15 + 0.05 * k for k in range(17))
WAIT_PRICE = 1.0 / 3600.0
NEAR_HALF = math.radians(3.0)
FLOOR = 20e3
REFINES = 2
REFINE = 4
#  A burn: the nose turned its way from 'LEAD' s before, the engine lit
#  once within 'ALIGNED' rad of it, at full push eased off over the last
#  'EASE' s of its speed; done within 'DONE' m/s; one under 'RCS_MOST' m/s
#  is the docking thrusters' (eased over 'SETTLE' s).
LEAD = 20.0
ALIGNED = math.radians(3.0)
EASE = 1.0
DONE = 0.1
RCS_MOST = 3.0
SETTLE = 2.0
#  On the way the course is checked at halves of the time left down to
#  'FINAL' s before the point; a miss over 'CORRECT' m/s is corrected.
FINAL = 45.0
CORRECT = 0.2
#  At the point, further than 'HOP_OVER' m from the station it hops: a
#  transfer from 'LEAD' s on, of one of 'HOPS' s; at most 'HOPS_MOST'.
HOP_OVER = 0.6 * REACH
HOPS = (600.0, 900.0, 1200.0, 1500.0, 1800.0)
HOPS_MOST = 3
#  Phasing (the rocket near the station's height: the station comes
#  round too late for any transfer): one burn along the path sets the
#  period that brings the rocket back to where it burnt as the point gets
#  there, after one of up to 'PHASINGS' turns round; the course steered
#  (Lambert's, less than a turn) from 'STEERED' of a turn before.
PHASINGS = 8
STEERED = 0.75
#  Its phases.
PHASES = ('off', 'plane', 'wait', 'burn', 'coast', 'match', 'done')


class RendezvousGuidance:
  """
  RendezvousGuidance flies the rocket to 'station' ('Transfers' its
  sums, 'transfers': given once the device is known): its 'phase'
  ('PHASES'; 'on' while flying); 'started' begins (or says why not),
  'acted' flies a frame on (throttle, docking thrusters, autopilot, the
  warp), 'stopped' lets go. Times are the game's elapsed seconds
  ('depart', 'arrival', 'checked': the next look at the course); 'way'
  the burn planned (m/s); 'reach' the phasing orbit's semi-major axis
  its burn makes for (m; nought: the burn is a transfer's); 'side' the
  point's side of the station (one behind, minus one ahead).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  station: Station
  transfers: Transfers | None
  phase: str
  depart: float
  arrival: float
  checked: float
  way: tuple
  hops: int
  reach: float
  side: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, station: Station) -> None:
    self.station, self.transfers, self.phase = station, None, 'off'
    self.depart = self.arrival = self.checked = 0.0
    self.way, self.hops, self.reach = (0.0, 0.0, 0.0), 0, 0.0
    self.side = 1.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def on(self, ) -> bool:
    """The 'on' property is whether it flies the rocket."""
    return self.phase not in ('off', 'done')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def started(self, vessel: Vessel, system: SolarSystem,
              keeper: Timekeeper) -> str:
    """The 'started' method begins the rendezvous; returns why it cannot
    ('' it flies): not ready, docked, not round the station's planet, not
    in orbit, no transfer found."""
    if self.transfers is None:
      return 'the flight computer is not ready'
    if vessel.docked:
      return 'docked already'
    if vessel.anchor != self.station.parent:
      return 'the station goes round %s: get there first' % (
        system.bodies[self.station.parent].name)
    conic = vessel.conicOf(system)
    if conic is None or not conic.closed:
      return 'not on an orbit'
    if conic.periapsis < self._floor(system):
      return 'not in orbit yet (the periapsis is too low)'
    self.hops = 0
    if self._tilt(vessel, keeper) > PLANE_SAME:
      self.phase = 'plane'
      return self._noded(vessel, system, keeper)
    return self._planned(vessel, system, keeper, None, None)

  def acted(self, vessel: Vessel, system: SolarSystem,
            keeper: Timekeeper) -> None:
    """The 'acted' method flies a frame on as its phase asks."""
    if not self.on:
      return
    if self.phase == 'plane':
      self._planeActed(vessel, system, keeper)
    elif self.phase == 'wait':
      self._waited(vessel, keeper)
    elif self.phase == 'burn':
      self._burnt(vessel, system, keeper)
    elif self.phase == 'coast':
      self._coasted(vessel, system, keeper)
    elif self.phase == 'match':
      self._matched(vessel, system, keeper)

  def stopped(self, vessel: Vessel) -> None:
    """The 'stopped' method lets the rocket go: the engine shut, the
    thrusters quiet (the warp and the autopilot as left)."""
    self.phase = 'off'
    vessel.engine.throttled(0.0)
    vessel.rcs = (0.0, 0.0, 0.0)

  def pointAt(self, t: float) -> tuple:
    """The 'pointAt' method returns the point aimed at, at the system's
    time 't': where it is and how it moves (m, m/s from the station's
    planet): the station's own state 'APART' m of its path off, behind
    or ahead as 'side' says."""
    speed = norm(self.station.stateAt(t)[1])
    return self.station.stateAt(t - self.side * APART / speed)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _floor(self, system: SolarSystem) -> float:
    """Returns the least distance from the planet's middle a path may
    come to: 'FLOOR' over its ground or its air's top, m."""
    body = system.bodies[self.station.parent]
    air = body.air.top if body.air is not None else 0.0
    return body.radius + max(FLOOR, air)

  def _normal(self, keeper: Timekeeper) -> tuple:
    """Returns the station's orbit's normal (the way it turns round)."""
    place, velocity = self.station.stateAt(keeper.now)
    return unit(cross(place, velocity))

  def _tilt(self, vessel: Vessel, keeper: Timekeeper) -> float:
    """Returns how far the rocket's orbit is tilted off the station's,
    rad."""
    turning = unit(cross(vessel.place, vessel.velocity))
    return math.acos(max(-1.0, min(1.0, dot(turning,
                                            self._normal(keeper)))))

  def _local(self, keeper: Timekeeper, at: float) -> float:
    """Returns the system's time of the game's elapsed 'at' s."""
    return keeper.now + at - keeper.elapsed

  def _noded(self, vessel: Vessel, system: SolarSystem,
             keeper: Timekeeper) -> str:
    """Times the plane's burn: where the rocket next crosses the
    station's plane, past 'LEAD' s from now; returns why not ('')."""
    mu = system.bodies[vessel.anchor].mu
    conic = Conic.fromState(mu, vessel.place, vessel.velocity)
    normal = self._normal(keeper)
    period = conic.period
    count = 64
    ts = [LEAD + period * k / count for k in range(count + 1)]
    sides = [dot(conic.stateAt(t)[0], normal) for t in ts]
    for k in range(count):
      if (sides[k] > 0.0) != (sides[k + 1] > 0.0):
        low, high = ts[k], ts[k + 1]
        for _ in range(40):
          middle = 0.5 * (low + high)
          side = dot(conic.stateAt(middle)[0], normal)
          if (side > 0.0) == (sides[k] > 0.0):
            low = middle
          else:
            high = middle
        self.depart = keeper.elapsed + 0.5 * (low + high)
        velocity = conic.stateAt(0.5 * (low + high))[1]
        self.way = self._flattened(velocity, normal)
        return ''
    self.phase = 'off'
    return 'no crossing of the station\'s plane'

  def _flattened(self, velocity: tuple, normal: tuple) -> tuple:
    """Returns the push that turns 'velocity' into the plane of
    'normal', its speed kept, m/s."""
    flat = tuple(v - dot(velocity, normal) * n
                 for v, n in zip(velocity, normal))
    speed = norm(velocity)
    return tuple(speed * f - v for f, v in zip(unit(flat), velocity))

  def _planeActed(self, vessel: Vessel, system: SolarSystem,
                  keeper: Timekeeper) -> None:
    """Warps to the crossing, turns, burns the orbit into the station's
    plane; then plans the transfer."""
    left = self.depart - keeper.elapsed
    if left > LEAD:
      self._warpedTo(vessel, keeper, left - LEAD, self.way)
      return
    keeper.realtime()
    goal = self._flattened(vessel.velocity, self._normal(keeper))
    if left > 0.5 * self._burnTime(vessel, norm(goal)):
      self._pointed(vessel, goal)
      return
    if norm(goal) < DONE or self._tilt(vessel, keeper) < 0.2 * PLANE_SAME:
      self._quiet(vessel)
      if self._planned(vessel, system, keeper, None, None):
        self.phase = 'off'
      return
    self._fired(vessel, goal)

  def _planned(self, vessel: Vessel, system: SolarSystem,
               keeper: Timekeeper, departures: object,
               flights: object) -> str:
    """Plans the transfer ('_plan'), the point on the side the rocket
    comes from (planned again once if it comes from the other); the
    cheapest becomes the plan ('wait'). Returns why there is none
    ('')."""
    best = self._plan(vessel, system, keeper, departures, flights)
    if best is not None and (best[5] < 0.0) != (self.side < 0.0):
      self.side = -self.side
      best = self._plan(vessel, system, keeper, departures, flights)
    if best is None:
      self.phase = 'off'
      return 'no transfer to the station found'
    _, wait, flight, way, self.reach, _ = best
    self.depart = keeper.elapsed + wait
    self.arrival = self.depart + flight
    self.way = way
    self.phase = 'wait'
    return ''

  def _plan(self, vessel: Vessel, system: SolarSystem, keeper: Timekeeper,
            departures: object, flights: object) -> tuple | None:
    """Returns the cheapest plan ('_cheapest', '_phasing'): the
    departures (s from now; None: every step within 'WAIT_MOST', a
    phasing weighed too) against the flight times (s; None: 'FLIGHTS'),
    refined; None if none will do."""
    mu = system.bodies[vessel.anchor].mu
    conic = Conic.fromState(mu, vessel.place, vessel.velocity)
    target = Conic.fromState(mu, *self.pointAt(keeper.now))
    transfer = math.pi * math.sqrt((0.5 * (conic.a + target.a)) ** 3 / mu)
    step = conic.period / DEPARTURES
    if flights is None:
      flights = [2.0 * transfer * share for share in FLIGHTS]
    flightStep = 2.0 * transfer * (FLIGHTS[1] - FLIGHTS[0])
    floor = self._floor(system)
    phasing = self._phasing(conic, keeper, mu, floor) if (
      departures is None) else None
    if departures is None:
      synodic = abs(math.tau / (conic.motion - target.motion)) if abs(
        conic.motion - target.motion) > 1e-12 else math.inf
      most = min(WAIT_MOST, synodic + conic.period)
      departures = [LEAD + step * k for k in range(int(most / step) + 1)]
    best = self._cheapest(conic, keeper, departures, flights, mu, floor)
    for _ in range(REFINES):
      if best is None:
        break
      step, flightStep = 0.25 * step, 0.25 * flightStep
      departures = [max(LEAD, best[1] + step * k)
                    for k in range(-REFINE, REFINE + 1)]
      flights = [max(60.0, best[2] + flightStep * k)
                 for k in range(-REFINE, REFINE + 1)]
      best = self._cheapest(conic, keeper, departures, flights, mu,
                            floor)
    if phasing is not None and (best is None or phasing[0] < best[0]):
      return phasing
    return best

  def _phasing(self, conic: Conic, keeper: Timekeeper, mu: float,
               floor: float) -> tuple | None:
    """Returns the cheapest phasing (its cost, wait, time to the meeting,
    push, the semi-major axis it makes for, how much faster than the
    point it comes back (the push's); the cost both its burns, the
    height still to change at the meeting (a Hohmann transfer's) and the
    wait), None if none will do: the burn 'LEAD' s on along the path,
    the rocket back there after k turns of the new period as the point
    gets there (k up to 'PHASINGS', a turn faster or slower)."""
    place, velocity = conic.stateAt(LEAD)
    there, moving = self.pointAt(keeper.now + LEAD)
    normal = self._normal(keeper)
    ahead = math.atan2(dot(cross(there, place), normal),
                       dot(there, place)) % math.tau
    motion = norm(moving) / norm(there)
    r, speed = norm(place), norm(velocity)
    far = norm(there)
    climb = abs(math.sqrt(mu / r) * (math.sqrt(2.0 * far / (r + far))
                                     - 1.0)) + abs(math.sqrt(mu / far) * (
      1.0 - math.sqrt(2.0 * r / (r + far))))
    best = None
    for k in range(1, PHASINGS + 1):
      for j in (k - 1, k):
        period = (ahead + math.tau * j) / (motion * k)
        if period <= 0.0:
          continue
        a = (mu * (period / math.tau) ** 2) ** (1.0 / 3.0)
        if 2.0 * a - r < floor:
          continue
        push = math.sqrt(mu * (2.0 / r - 1.0 / a)) - speed
        cost = 2.0 * abs(push) + climb + WAIT_PRICE * (LEAD + k * period)
        if best is None or cost < best[0]:
          best = (cost, LEAD, k * period, tuple(
            push * u for u in unit(velocity)), a, push)
    return best

  def _phasingGoal(self, vessel: Vessel, system: SolarSystem) -> tuple:
    """Returns the speed still to gain along the path for the phasing
    orbit's semi-major axis ('reach'), m/s."""
    mu = system.bodies[vessel.anchor].mu
    r = norm(vessel.place)
    wanted = math.sqrt(mu * (2.0 / r - 1.0 / self.reach))
    return tuple(wanted * u - v for u, v in zip(unit(vessel.velocity),
                                                vessel.velocity))

  def _cheapest(self, conic: Conic, keeper: Timekeeper, departures: list,
                flights: list, mu: float, floor: float) -> tuple | None:
    """Returns the cheapest transfer of these (its cost, wait, flight
    time, the push leaving (m/s), nought: no phasing, how much faster
    than the point it arrives along its path (m/s); none coming nearer
    the planet's middle than 'floor' m), None if none will do."""
    starts, speeds, ends, arrivals, waits, times = [], [], [], [], [], []
    for wait in departures:
      place, velocity = conic.stateAt(wait)
      for flight in flights:
        there, moving = self.pointAt(keeper.now + wait + flight)
        starts.append(place)
        speeds.append(velocity)
        ends.append(there)
        arrivals.append(moving)
        waits.append(wait)
        times.append(flight)
    starts, ends = numpy.asarray(starts), numpy.asarray(ends)
    leaving, arriving = self.transfers.solved(
      mu, starts, ends, times, self._normal(keeper))
    pushes = leaving - numpy.asarray(speeds)
    cost = (numpy.linalg.norm(pushes, axis=1) + numpy.linalg.norm(
      numpy.asarray(arrivals) - arriving, axis=1)
            + WAIT_PRICE * numpy.asarray(waits))
    cosine = numpy.einsum('ij,ij->i', starts, ends) / (
      numpy.linalg.norm(starts, axis=1) * numpy.linalg.norm(ends, axis=1))
    half = numpy.abs(numpy.arccos(numpy.clip(cosine, -1.0, 1.0))
                     - math.pi) < NEAR_HALF
    turning = numpy.cross(starts, leaving)
    h2 = numpy.einsum('ij,ij->i', turning, turning)
    energy = 0.5 * numpy.einsum('ij,ij->i', leaving, leaving) - mu / (
      numpy.linalg.norm(starts, axis=1))
    e = numpy.sqrt(numpy.maximum(0.0, 1.0 + 2.0 * energy * h2 / mu ** 2))
    low = h2 / mu / (1.0 + e) < floor
    cost[half | low | ~numpy.isfinite(cost)] = math.inf
    k = int(numpy.argmin(cost))
    if not math.isfinite(cost[k]):
      return None
    moving = numpy.asarray(arrivals[k])
    along = float(numpy.dot(arriving[k] - moving, moving)
                  / numpy.linalg.norm(moving))
    return (float(cost[k]), waits[k], times[k],
            tuple(float(x) for x in pushes[k]), 0.0, along)

  def _goal(self, vessel: Vessel, system: SolarSystem,
            keeper: Timekeeper) -> tuple:
    """Returns the speed still to gain to coast onto the point at the
    arrival, from where the rocket is (m/s)."""
    mu = system.bodies[vessel.anchor].mu
    left = self.arrival - keeper.elapsed
    there = self.pointAt(self._local(keeper, self.arrival))[0]
    leaving, _ = self.transfers.solved(mu, [vessel.place], [there], [left],
                                       self._normal(keeper))
    if not numpy.isfinite(leaving).all():
      return (0.0, 0.0, 0.0)
    return tuple(float(a - b) for a, b in zip(leaving[0], vessel.velocity))

  def _waited(self, vessel: Vessel, keeper: Timekeeper) -> None:
    """Warps to the burn ('LEAD' s before), turns the nose the burn's
    way, starts it half its time before the departure."""
    left = self.depart - keeper.elapsed
    if left > LEAD:
      self._warpedTo(vessel, keeper, left - LEAD, self.way)
      return
    keeper.realtime()
    self._pointed(vessel, self.way)
    if left <= 0.5 * self._burnTime(vessel, norm(self.way)):
      self.phase = 'burn'

  def _burnt(self, vessel: Vessel, system: SolarSystem,
             keeper: Timekeeper) -> None:
    """Burns toward the point (the speed to gain anew each frame) or
    onto the phasing orbit; done, coasts."""
    keeper.realtime()
    goal = self._phasingGoal(vessel, system) if self.reach else (
      self._goal(vessel, system, keeper))
    if norm(goal) < DONE:
      self.reach = 0.0
      self._quiet(vessel)
      self.phase = 'coast'
      self.checked = keeper.elapsed + 0.5 * (self.arrival - keeper.elapsed)
      return
    self._fired(vessel, goal)

  def _coasted(self, vessel: Vessel, system: SolarSystem,
               keeper: Timekeeper) -> None:
    """Coasts warped to each look at the course (a miss corrected; the
    first within 'STEERED' of a turn of the point) and to 'FINAL' s
    before the point, then matches."""
    self._quiet(vessel)
    left = self.arrival - keeper.elapsed
    if left <= FINAL:
      keeper.realtime()
      self.phase = 'match'
      return
    mu = system.bodies[vessel.anchor].mu
    period = Conic.fromState(mu, vessel.place, vessel.velocity).period
    self.checked = min(max(self.checked, self.arrival - STEERED * period),
                       self.arrival - FINAL)
    if keeper.elapsed < self.checked:
      if keeper.aimed is None:
        keeper.aim(self.checked - keeper.elapsed)
      return
    keeper.realtime()
    if norm(self._goal(vessel, system, keeper)) > CORRECT:
      self.phase = 'burn'
      return
    self.checked = keeper.elapsed + 0.5 * left

  def _matched(self, vessel: Vessel, system: SolarSystem,
               keeper: Timekeeper) -> None:
    """At the point, matches its speed (the nose turned its way first,
    the burn started half its time before); then done, or hops again
    when still far from the station."""
    keeper.realtime()
    mu = system.bodies[vessel.anchor].mu
    left = self.arrival - keeper.elapsed
    if left > 0.0:
      conic = Conic.fromState(mu, vessel.place, vessel.velocity)
      coming = conic.stateAt(left)[1]
      moving = self.pointAt(self._local(keeper, self.arrival))[1]
      goal = tuple(a - b for a, b in zip(moving, coming))
      if left > 0.5 * self._burnTime(vessel, norm(goal)):
        self._pointed(vessel, goal)
        return
    moving = self.pointAt(keeper.now)[1]
    goal = tuple(a - b for a, b in zip(moving, vessel.velocity))
    if norm(goal) >= DONE:
      self._fired(vessel, goal)
      return
    self._quiet(vessel)
    middle = self.station.stateAt(keeper.now)[0]
    if math.dist(middle, vessel.place) <= HOP_OVER or (
        self.hops >= HOPS_MOST):
      self.phase = 'done'
      return
    self.hops += 1
    self._planned(vessel, system, keeper, [LEAD], list(HOPS))

  def _warpedTo(self, vessel: Vessel, keeper: Timekeeper, seconds: float,
                way: tuple) -> None:
    """Warps 'seconds' s on (unless warped already), the engine and the
    thrusters quiet, the nose turned 'way'."""
    self._quiet(vessel)
    self._pointed(vessel, way)
    if keeper.aimed is None:
      keeper.aim(seconds)

  def _pointed(self, vessel: Vessel, way: tuple) -> None:
    """Holds the nose 'way' (its roll kept as near as it is)."""
    if norm(way) < 1e-9:
      return
    nose = unit(way)
    side = rotated(vessel.turn, (1.0, 0.0, 0.0))
    side = tuple(s - dot(side, nose) * n for s, n in zip(side, nose))
    if norm(side) < 1e-6:
      side = rotated(vessel.turn, (0.0, 1.0, 0.0))
      side = tuple(s - dot(side, nose) * n for s, n in zip(side, nose))
    side = unit(side)
    up = cross(nose, side)
    vessel.autopilot.engaged('hold', quaternionOf(tuple(
      (side[k], up[k], nose[k]) for k in range(3))))

  def _fired(self, vessel: Vessel, goal: tuple) -> None:
    """Gains 'goal' (m/s): by the docking thrusters when small, else the
    nose turned its way and the engine lit once it points there, eased
    off near the end."""
    size = norm(goal)
    engine = vessel.engine
    if size < RCS_MOST:
      engine.throttled(0.0)
      push = tuple(g / SETTLE for g in goal)
      if size / SETTLE > RCS_ACCEL:
        push = tuple(RCS_ACCEL * g / size for g in goal)
      vessel.rcs = unrotated(vessel.turn, tuple(MASS * p for p in push))
      return
    vessel.rcs = (0.0, 0.0, 0.0)
    self._pointed(vessel, goal)
    nose = rotated(vessel.turn, (0.0, 0.0, 1.0))
    if dot(nose, unit(goal)) < math.cos(ALIGNED):
      engine.throttled(0.0)
      return
    wanted = min(engine.most / MASS, size / EASE)
    engine.throttled(wanted * MASS / engine.thrust)

  def _quiet(self, vessel: Vessel) -> None:
    """Shuts the engine and the thrusters."""
    vessel.engine.throttled(0.0)
    vessel.rcs = (0.0, 0.0, 0.0)

  def _burnTime(self, vessel: Vessel, speed: float) -> float:
    """Returns how long gaining 'speed' m/s takes (the engine at its
    most, or the thrusters for a small one), s."""
    if speed < RCS_MOST:
      return speed / RCS_ACCEL
    return speed / (vessel.engine.most / MASS)
