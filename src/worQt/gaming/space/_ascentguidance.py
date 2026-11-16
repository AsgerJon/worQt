"""
AscentGuidance flies a vessel from the pad to a round orbit (user,
2026-11-16: "go ahead and get that mechjeb in here", after KSP's
MechJeb): straight up, a gravity turn east, the engine cut once the
apoapsis is high enough, a coast (warped above the air) and the burn
that rounds the orbit there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._turns import dot, norm, unit
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._timekeeper import Timekeeper
  from ._vessel import Vessel

#  Its phases, in order.
PHASES = ('off', 'climb', 'turn', 'coast', 'round', 'done')
#  The orbit's height asked at first, m; how far a key moves it, m; the
#  least and most.
TARGET = 200e3
TARGET_STEP = 10e3
TARGET_LEAST, TARGET_MOST = 120e3, 2000e3
#  Straight up to this height, m; then the turn: the pitch over the
#  horizon falls from 90 degrees as the share of the way to 'TURN_END'
#  m to the power 'TURN_SHAPE', to 'TURN_LEAST' (deg) at its end.
TURN_START = 1500.0
TURN_END = 60e3
TURN_SHAPE = 0.5
TURN_LEAST = 3.0
#  In the thick air the nose keeps within 'AOA_LOW' deg of the path
#  (MechJeb's angle of attack limit: turned across the air the rocket
#  hangs on its own drag), the limit opening to a right angle from
#  'AOA_FROM' m to 'AOA_TO' m up.
AOA_LOW = 5.0
AOA_FROM, AOA_TO = 30e3, 60e3
#  However it turns, the nose stays high enough to climb at least
#  'CLIMB_FAST' m/s near the ground, less with height, nought from
#  'CLIMB_UNTIL' m: its push up beats the pull less the curve's relief
#  (v² / r of its speed along the horizon), and makes up a shortfall in
#  the climb at 'CLIMB_GAIN' a second (the rocket's 1.5 g never grows:
#  a turn that lets its path sag sends it into the ground, one too slow
#  up drags it through the thick air for minutes).
CLIMB_FAST = 400.0
CLIMB_UNTIL = 80e3
CLIMB_GAIN = 0.1
#  The compass heading of the launch: east, with the ground's turning.
LAUNCH_HEADING = 90.0
#  Coasting, the apoapsis is topped up in the air when it sags this far
#  under the target, m; the round burn starts half its time before the
#  apoapsis, and time is warped to 'WARP_LEAD' s before that.
SAGGED = 500.0
WARP_LEAD = 10.0
#  The round burn ends once the periapsis is this near the target (m),
#  or once the apoapsis has risen this far past it; it throttles down
#  for the last 'EASE' s of its speed to gain.
ROUNDED = 1000.0
OVERSHOT = 5000.0
EASE = 2.0
EASIEST = 0.02


class AscentGuidance:
  """
  AscentGuidance flies a vessel to a round orbit 'target' m over its
  anchor's ground: each frame ('acted', before the flight steps) it sets
  the vessel's throttle and its autopilot (the aim mode in the climb and
  the turn, prograde coasting, the aim level along the path in the round
  burn) and warps time to the round burn. 'phase' says where it is (one
  of 'PHASES'); off, it leaves the vessel alone. Any key on the vessel
  takes it off (the window's: you take the controls).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  target: float
  phase: str

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.target, self.phase = TARGET, 'off'

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def on(self, ) -> bool:
    """The 'on' property says whether it flies."""
    return self.phase not in ('off', 'done')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def started(self, vessel: Vessel, system: SolarSystem) -> None:
    """The 'started' method takes the vessel up from where it is: from
    the climb on the ground or low, else from the turn or the coast."""
    height = vessel.heightOver(system)
    if height < TURN_START:
      self.phase = 'climb'
    elif self._apoapsis(vessel, system) < self.target:
      self.phase = 'turn'
    else:
      self.phase = 'coast'

  def stopped(self, vessel: Vessel) -> None:
    """The 'stopped' method lets go: the engine shut, the autopilot
    holding the vessel as it is."""
    if self.on:
      vessel.engine.throttled(0.0)
      vessel.autopilot.engaged('hold', vessel.turn)
    self.phase = 'off'

  def targeted(self, steps: int) -> None:
    """The 'targeted' method moves the orbit's height asked 'steps'
    steps up (down when below nought)."""
    self.target = max(TARGET_LEAST, min(TARGET_MOST, self.target
                                        + steps * TARGET_STEP))

  def acted(self, vessel: Vessel, system: SolarSystem,
            keeper: Timekeeper) -> None:
    """The 'acted' method flies the vessel a frame on: sets its throttle,
    its autopilot, and the time's warp, as its phase asks."""
    if not self.on:
      return
    body = system.bodies[vessel.anchor]
    height = vessel.heightOver(system)
    pilot, engine = vessel.autopilot, vessel.engine
    if self.phase == 'climb':
      pilot.aimedAt(0.5 * math.pi, 0.0, math.radians(LAUNCH_HEADING),
                    False)
      engine.throttled(1.0)
      if height > TURN_START:
        self.phase = 'turn'
    if self.phase == 'turn':
      share = min(1.0, max(0.0, (height - TURN_START)
                           / (TURN_END - TURN_START)))
      pitch = max(math.radians(TURN_LEAST), 0.5 * math.pi * (
        1.0 - share ** TURN_SHAPE))
      pitch = self._withinPath(vessel, system, pitch, height)
      pitch = max(pitch, self._climbing(vessel, system))
      vessel.aimKept(system)
      pilot.aimedAt(pitch, 0.0, math.radians(LAUNCH_HEADING), pilot.travel)
      engine.throttled(1.0)
      if self._apoapsis(vessel, system) >= self.target:
        engine.throttled(0.0)
        self.phase = 'coast'
    if self.phase == 'coast':
      self._coasted(vessel, system, keeper, body, height)
    if self.phase == 'round':
      self._rounded(vessel, system, body)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _withinPath(self, vessel: Vessel, system: SolarSystem,
                  pitch: float, height: float) -> float:
    """Returns 'pitch' kept within the angle of attack's limit of the
    path's own pitch over the horizon (the limit opening with height)."""
    path = vessel.pathOf(system)
    speed = norm(path)
    if speed < 1.0:
      return pitch
    climb = math.asin(max(-1.0, min(1.0, dot(path, unit(vessel.place))
                                    / speed)))
    share = min(1.0, max(0.0, (height - AOA_FROM) / (AOA_TO - AOA_FROM)))
    limit = math.radians(AOA_LOW + share * (90.0 - AOA_LOW))
    return max(climb - limit, min(climb + limit, pitch))

  def _climbing(self, vessel: Vessel, system: SolarSystem) -> float:
    """Returns the least pitch over the horizon at full throttle that
    keeps the vessel climbing as fast as its height asks ('CLIMB_FAST'
    to nought at 'CLIMB_UNTIL'; rad, a right angle when no pitch
    will)."""
    mu = system.bodies[vessel.anchor].mu
    r = norm(vessel.place)
    up = unit(vessel.place)
    climb = dot(vessel.velocity, up)
    level = norm(tuple(a - climb * b for a, b in zip(vessel.velocity, up)))
    least = CLIMB_FAST * max(0.0, 1.0 - (r - system.bodies[
      vessel.anchor].radius) / CLIMB_UNTIL)
    wanted = mu / (r * r) - level * level / r + CLIMB_GAIN * (
      least - climb)
    push = vessel.engine.thrust / MASS
    return math.asin(max(-1.0, min(1.0, wanted / push)))

  def _apoapsis(self, vessel: Vessel, system: SolarSystem) -> float:
    """Returns the vessel's apoapsis over its anchor's ground, m (nought
    with no path, past escaping 'math.inf')."""
    conic = vessel.conicOf(system)
    if conic is None:
      return 0.0
    return conic.apoapsis - system.bodies[vessel.anchor].radius

  def _coasted(self, vessel: Vessel, system: SolarSystem,
               keeper: Timekeeper, body: object, height: float) -> None:
    """Coasts to the round burn: the nose along the path; in the air the
    apoapsis topped up when it sags; above it, time warped to the burn's
    start; the burn started half its time before the apoapsis."""
    pilot, engine = vessel.autopilot, vessel.engine
    pilot.engaged('prograde', vessel.turn)
    air = body.air
    inAir = air is not None and height < air.top
    apoapsis = self._apoapsis(vessel, system)
    if inAir:
      engine.throttled(1.0 if apoapsis < self.target - SAGGED else 0.0)
      return
    engine.throttled(0.0)
    conic = vessel.conicOf(system)
    if conic is None or not conic.closed:
      return
    left = conic.timeToApoapsis(0.0) - 0.5 * self._burnTime(vessel, system)
    if left <= 0.0 or left > 0.5 * conic.period:
      keeper.realtime()
      self.phase = 'round'
      return
    if keeper.aimed is None and left > WARP_LEAD + 1.0:
      keeper.aim(left - WARP_LEAD)

  def _rounded(self, vessel: Vessel, system: SolarSystem,
               body: object) -> None:
    """Burns level along the path to the round orbit's speed, easing off
    at the end; done once the periapsis has come up to the target (or the
    apoapsis has risen past it)."""
    pilot, engine = vessel.autopilot, vessel.engine
    pilot.aimedAt(0.0, 0.0, pilot.heading, True)
    conic = vessel.conicOf(system)
    periapsis = conic.periapsis - body.radius if conic else -body.radius
    apoapsis = self._apoapsis(vessel, system)
    if periapsis >= self.target - ROUNDED or (
        apoapsis > self.target + OVERSHOT):
      engine.throttled(0.0)
      pilot.engaged('prograde', vessel.turn)
      self.phase = 'done'
      return
    left = self._speedLeft(vessel, system)
    most = engine.thrust / MASS
    engine.throttled(max(EASIEST, min(1.0, left / (most * EASE))))

  def _speedLeft(self, vessel: Vessel, system: SolarSystem) -> float:
    """Returns the speed still to gain along the horizon for a round
    orbit where the vessel is, m/s."""
    mu = system.bodies[vessel.anchor].mu
    r = norm(vessel.place)
    up = unit(vessel.place)
    level = tuple(a - dot(vessel.velocity, up) * b
                  for a, b in zip(vessel.velocity, up))
    return max(0.0, math.sqrt(mu / r) - norm(level))

  def _burnTime(self, vessel: Vessel, system: SolarSystem) -> float:
    """Returns how long the round burn at the apoapsis takes at full
    throttle, s."""
    conic = vessel.conicOf(system)
    mu = system.bodies[vessel.anchor].mu
    far = conic.apoapsis
    there = math.sqrt(mu * (2.0 / far - 1.0 / conic.a))
    return max(0.0, math.sqrt(mu / far) - there) / (
      vessel.engine.thrust / MASS)
