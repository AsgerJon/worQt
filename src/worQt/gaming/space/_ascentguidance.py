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

from ._aerospike import G0
from ._turns import dot, norm, unit
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._timekeeper import Timekeeper
  from ._vessel import Vessel

#  Its phases, in order.
PHASES = ('off', 'climb', 'turn', 'coast', 'round', 'done')
#  The orbit's heights to be asked, m, a key a step through them (user,
#  2026-11-16: "The orbit input dial should have clearer markings on
#  it": its knob a notch each, marked); the one asked at first.
TARGETS = (120e3, 150e3, 200e3, 250e3, 300e3, 400e3, 500e3, 700e3, 1000e3,
           1500e3, 2000e3)
TARGET = 200e3
#  Straight up to this height, m; then the turn: the pitch over the
#  horizon falls from 90 degrees as the share of the way to 'TURN_END'
#  m to the power 'TURN_SHAPE', to 'TURN_LEAST' (deg) at its end. At the
#  rocket's 4 g (user, 2026-11-16) the turn starts low and slow: begun at
#  1.5 km (290 m/s) its path barely bent in the thick air, and the round
#  burn at the apoapsis had 4.5 km/s to make up (it fell short); tried
#  against the flight (pad to 200 x 199 km).
TURN_START = 150.0
TURN_END = 35e3
TURN_SHAPE = 0.4
TURN_LEAST = 3.0
#  In the thick air the nose keeps within 'AOA_LOW' deg of the path
#  (MechJeb's angle of attack limit: turned across the air the rocket
#  hangs on its own drag), the limit opening to a right angle from
#  'AOA_FROM' m to 'AOA_TO' m up.
AOA_LOW = 10.0
AOA_FROM, AOA_TO = 30e3, 60e3
#  However it turns, the nose stays high enough to climb at least
#  'CLIMB_FAST' m/s near the ground, less with height, nought from
#  'CLIMB_UNTIL' m: its push up beats the pull less the curve's relief
#  (v² / r of its speed along the horizon), and makes up a shortfall in
#  the climb at 'CLIMB_GAIN' a second (the rocket's push never grows:
#  a turn that lets its path sag sends it into the ground, one too slow
#  up drags it through the thick air for minutes).
CLIMB_FAST = 400.0
CLIMB_UNTIL = 80e3
CLIMB_GAIN = 0.1
#  The compass heading of the launch: east, with the ground's turning.
LAUNCH_HEADING = 90.0
#  Coasting in the air, the drag lowers the apoapsis: it is topped up to
#  the target only while it falls faster than 'FALL_FAST' m a second (its
#  fall eased over 'FALL_EASE' s; user, 2026-11-17: "the auto pilot
#  should not give tiny engine bursts to keep the AP at an exact value.
#  As long as AP is not dropping quickly because of atmospheric drag, we
#  just accept ending at a slightly lower AP because of loss to drag"),
#  and the round burn rounds the orbit at the apoapsis reached. The
#  round burn starts half its time before the apoapsis; a warp of his
#  stops 'WARP_LEAD' s before that (user, 2026-11-17: "Warp should not be
#  automatic!": it never warps itself).
FALL_FAST = 100.0
FALL_EASE = 1.0
#  A top up pushes no harder than this, g, and only with Asger in his
#  chair (user, 2026-11-17: "'top up' bursts ... should be limited to 1g
#  AND require Asger to be seated").
TOP_UP = 1.0
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
  burn) and stops a warp before the round burn. 'phase' says where it
  is (one of 'PHASES'); 'rounding' the height the round burn rounds the
  orbit at (the apoapsis reached: under the target by what the air took
  coasting); off, it leaves the vessel alone. Any key on the vessel
  takes it off (the window's: you take the controls).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('target', 'phase', 'rounding', '_fall', '_last', '_topping')

  #  Public Variables
  target: float
  phase: str
  rounding: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.target, self.phase, self.rounding = TARGET, 'off', TARGET
    self._fall, self._last, self._topping = 0.0, None, False

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
    self.rounding, self._topping = self.target, False
    self._fall, self._last = 0.0, None
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
    """The 'targeted' method moves the orbit's height asked 'steps' of
    'TARGETS' up (down when below nought), kept within them."""
    self.target = TARGETS[max(0, min(len(TARGETS) - 1,
                                     self.notch() + steps))]

  def notch(self, ) -> int:
    """The 'notch' method returns which of 'TARGETS' is asked (the
    nearest)."""
    return min(range(len(TARGETS)),
               key=lambda k: abs(TARGETS[k] - self.target))

  def acted(self, vessel: Vessel, system: SolarSystem,
            keeper: Timekeeper, seated: bool = True) -> None:
    """The 'acted' method flies the vessel a frame on: sets its throttle,
    its autopilot, and stops a warp, as its phase asks (coasting in the
    air it tops up the apoapsis only with Asger 'seated')."""
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
      self._coasted(vessel, system, keeper, body, height, seated)
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
    push = vessel.engine.most / MASS
    return math.asin(max(-1.0, min(1.0, wanted / push)))

  def _apoapsis(self, vessel: Vessel, system: SolarSystem) -> float:
    """Returns the vessel's apoapsis over its anchor's ground, m (nought
    with no path, past escaping 'math.inf')."""
    conic = vessel.conicOf(system)
    if conic is None:
      return 0.0
    return conic.apoapsis - system.bodies[vessel.anchor].radius

  def _coasted(self, vessel: Vessel, system: SolarSystem,
               keeper: Timekeeper, body: object, height: float,
               seated: bool) -> None:
    """Coasts to the round burn: the nose along the path; in the air the
    apoapsis topped up only while the drag drops it fast; above it, a
    warp stopped before the burn's start; the burn started half its time
    before the apoapsis."""
    pilot, engine = vessel.autopilot, vessel.engine
    pilot.engaged('prograde', vessel.turn)
    air = body.air
    inAir = air is not None and height < air.top
    apoapsis = self._apoapsis(vessel, system)
    if inAir:
      fall = self._falling(apoapsis, keeper.elapsed)
      self._topping = seated and apoapsis < self.target and (
        self._topping or fall > FALL_FAST)
      engine.throttled(TOP_UP * G0 * MASS / engine.thrust
                       if self._topping else 0.0)
      return
    engine.throttled(0.0)
    conic = vessel.conicOf(system)
    if conic is None or not conic.closed:
      return
    left = conic.timeToApoapsis(0.0) - 0.5 * self._burnTime(vessel, system)
    if left <= 0.0 or left > 0.5 * conic.period:
      keeper.realtime()
      self.phase, self.rounding = 'round', apoapsis
      return
    if left > WARP_LEAD + 1.0:
      keeper.stopAt(left - WARP_LEAD)
    else:
      keeper.realtime()

  def _falling(self, apoapsis: float, now: float) -> float:
    """Returns how fast the apoapsis falls ('apoapsis' at time 'now'),
    m/s, eased over 'FALL_EASE' s."""
    last, self._last = self._last, (apoapsis, now)
    if last is None or now <= last[1]:
      return self._fall
    seconds = now - last[1]
    share = 1.0 - math.exp(-seconds / FALL_EASE)
    self._fall += share * ((last[0] - apoapsis) / seconds - self._fall)
    return self._fall

  def _rounded(self, vessel: Vessel, system: SolarSystem,
               body: object) -> None:
    """Burns level along the path to the round orbit's speed, easing off
    at the end; done once the periapsis has come up to the height it
    rounds at (or the apoapsis has risen past it)."""
    pilot, engine = vessel.autopilot, vessel.engine
    pilot.aimedAt(0.0, 0.0, pilot.heading, True)
    conic = vessel.conicOf(system)
    periapsis = conic.periapsis - body.radius if conic else -body.radius
    apoapsis = self._apoapsis(vessel, system)
    if periapsis >= self.rounding - ROUNDED or (
        apoapsis > self.rounding + OVERSHOT):
      engine.throttled(0.0)
      pilot.engaged('prograde', vessel.turn)
      self.phase = 'done'
      return
    left = self._speedLeft(vessel, system)
    most = engine.most / MASS
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
      vessel.engine.most / MASS)
