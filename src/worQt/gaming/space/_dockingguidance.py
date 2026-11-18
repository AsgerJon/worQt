"""
DockingGuidance docks the rocket to the space station by itself (user,
2026-11-17: "we include buttons so that a try-hard *could* manually do
the thing. If he hates fun. But where we also provide an automated
system for the rest of. Same with docking"): from within 'REACH' of the
station's port it turns the rocket to match the station (nose down its
axis, turning with it: the autopilot's 'match'), brings the nose by the
docking thrusters to a point 'HOLD_OUT' out on the axis, steady, then
straight in at 'FINAL_SPEED' till the latch catches. Beside or behind
the station it goes round first ('routeOf': the rendezvous leaves the
rocket 2 km along the station's path, on whatever side of its axis
that is; the user's let's play, 2026-11-18, straight at the point from
behind: the rocket backed into the hub's foot at 18.5 m/s and stayed
pressed to it). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._dockingport import NOSE_PORT
from ._stationmeshes import portTip
from ._stationsolids import CAPSULE, CYLINDER, TORUS, hullBalls
from ._stationsolids import stationSolids
from ._turns import cross, dot, norm, unrotated, unit
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._dockingport import DockingPort
  from ._vessel import Vessel

#  The docking thrusters push the rocket this hard by hand, m/s² (each
#  way); the automatic docking's push its own, harder (user, 2026-11-17:
#  "the "closing" phase can be very slow ... I know this is realistic and
#  safe but also boring af. So adjust the autodocking thing to use a high
#  speed when closing in").
RCS_ACCEL = 0.15
GUIDED_ACCEL = 1.0
#  It docks from within 'REACH' m of the port, drifting no faster than
#  'DRIFT_MOST' m/s from it.
REACH = 5000.0
DRIFT_MOST = 50.0
#  The final approach starts 'HOLD_OUT' m out on the station's axis,
#  once the nose is within 'READY' (m, m/s, rad, rad/s: off the point,
#  drifting, tilted, turning off the station's); then the nose comes in
#  no faster than 'FINAL_FAST' m/s nor than it can slow braking at
#  'FINAL_BRAKE' m/s² to 'FINAL_SPEED' m/s 'FINAL_NEAR' m out (user,
#  2026-11-17: "DOCK: FINAL is moving so slooooooooow": it crept the
#  whole 100 m at 0.3 m/s), kept on the axis 'CENTRING' a second, its
#  drift brought to the speed it wants most of the way in
#  'FINAL_SETTLE' s (braking, its drift lags the speed wanted by the
#  braking times this: the latch takes no more than 1 m/s).
HOLD_OUT = 100.0
READY = (2.0, 0.2, math.radians(2.0), 0.01)
FINAL_FAST = 5.0
FINAL_BRAKE = 0.3
FINAL_SPEED = 0.3
FINAL_NEAR = 2.0
FINAL_SETTLE = 1.0
CENTRING = 0.2
#  Closing in it goes no faster than 'APPROACH_FAST' m/s, nor than it can
#  stop braking at 'BRAKE' m/s²; it brings its drift to the speed it
#  wants most of the way in 'SETTLE' s.
APPROACH_FAST = 30.0
BRAKE = 0.5
SETTLE = 2.0
#  It never hurries time (user, 2026-11-17: "Warp should not be
#  automatic!").
#  Going round, it keeps 'ROUND_MARGIN' m clear of all the station sweeps
#  as it turns (its wheel, spokes and antennas a disc, its hub, port and
#  the antenna behind it on the axis) and passes each corner of its way
#  within 'ROUND_NEAR' m.
ROUND_MARGIN = 50.0
ROUND_NEAR = 20.0
#  Its phases.
PHASES = ('off', 'round', 'closing', 'final')


def _reaches() -> tuple:
  """Returns how far the station's solids reach from its axis, how far
  up it (its own z), how far the disc its wheel, spokes and antennas
  sweep reaches either side of its middle; how far the rocket's hull
  reaches from its axis, and up the station's axis from its nose (its
  nose down the axis: its body above it). All m."""
  out = top = disc = 0.0
  hub = 0.0
  for kind, a, b, radius in stationSolids():
    if kind == TORUS:
      reach, high, low = a[0] + radius, radius, radius
    elif kind == CYLINDER:
      reach, high, low = radius, max(a[2], b[2]) + radius, min(
        a[2], b[2]) - radius
      hub = max(hub, radius)
    else:
      reach = max(math.hypot(a[0], a[1]), math.hypot(b[0], b[1])) + radius
      high, low = max(a[2], b[2]) + radius, min(a[2], b[2]) - radius
    out, top = max(out, reach), max(top, high)
    if kind != CYLINDER and reach > radius + 1e-6:
      disc = max(disc, high, -low)
  balls = hullBalls()
  wide = max(math.hypot(x, y) + r for x, y, _, r in balls)
  up = NOSE_PORT[2] - min(z - r for _, _, z, r in balls)
  return out, top, disc, wide, up


STATION_OUT, STATION_TOP, DISC, ROCKET_WIDE, ROCKET_UP = _reaches()
#  The way round, its nose from the port's tip ('along' the station's
#  axis): out to 'ROUND_OUT' m from the axis; the front, where the way in
#  is clear ('FRONT'); below everything ('BELOW').
PORT_TOP = portTip()[2]
ROUND_OUT = STATION_OUT + ROCKET_WIDE + ROUND_MARGIN
FRONT = STATION_TOP - PORT_TOP + ROUND_MARGIN
BELOW = -DISC - ROCKET_UP - ROUND_MARGIN - PORT_TOP


def routeOf(out: float, along: float) -> tuple:
  """Returns the way round to the point 'HOLD_OUT' out on the axis for
  the rocket's nose 'out' m from the station's axis and 'along' m up it
  from the port's tip (its body above it, matched): the corners on the
  way, each (out, along), the point itself not among them; none from
  the front (the way in clear). Out past what the station sweeps, the
  way goes up the outside; below it, out under it first; overlapping its
  disc beside it, down out of it first; over the disc, straight up."""
  if along >= FRONT:
    return ()
  if out >= ROUND_OUT:
    return ((out, HOLD_OUT),)
  if along > -DISC - PORT_TOP:
    return ((out, HOLD_OUT),)
  if along > BELOW:
    return ((out, BELOW), (ROUND_OUT, BELOW), (ROUND_OUT, HOLD_OUT))
  return ((ROUND_OUT, BELOW), (ROUND_OUT, HOLD_OUT))


class DockingGuidance:
  """
  DockingGuidance flies the rocket into the station's port: its 'phase'
  ('PHASES'; 'on' while not 'off'), the corners still to pass going
  round ('route', 'routeOf') off the axis toward 'outward' (a unit
  vector square to the station's axis, the ecliptic's axes, where the
  rocket was as it started); 'started' begins (or says why not:
  too far, too fast, docked), 'acted' flies a frame on (the autopilot
  matching, the thrusters pushing), 'stopped' lets go (the thrusters
  quiet; the autopilot as it was left).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('phase', 'route', 'outward')

  #  Public Variables
  phase: str
  route: tuple
  outward: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.phase, self.route, self.outward = 'off', (), (1.0, 0.0, 0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def on(self, ) -> bool:
    """The 'on' property is whether it flies the rocket."""
    return self.phase != 'off'

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def started(self, vessel: Vessel, port: DockingPort, reading: dict,
              t: float) -> str:
    """The 'started' method begins docking 'vessel' at time 't' (its
    nose standing to the port as 'reading' says); returns why it cannot
    ('' it docks): docked already, too far, drifting too fast."""
    if vessel.docked:
      return 'docked already'
    if reading['distance'] > REACH:
      return 'Terra Prime is %.0f km off (within %.0f km)' % (
        reading['distance'] / 1e3, REACH / 1e3)
    drift = norm(reading['drift'])
    if drift > DRIFT_MOST:
      return 'drifting %.0f m/s from it (within %.0f)' % (drift,
                                                           DRIFT_MOST)
    port.aligned(vessel, t)
    axis, offset, along = reading['axis'], reading['offset'], reading[
      'along']
    across = tuple(o - along * a for o, a in zip(offset, axis))
    if norm(across) < 1.0:
      across = cross(axis, (1.0, 0.0, 0.0))
      if norm(across) < 0.1:
        across = cross(axis, (0.0, 1.0, 0.0))
    self.outward = unit(across)
    self.route = routeOf(reading['across'], along)
    self.phase = 'round' if self.route else 'closing'
    return ''

  def acted(self, vessel: Vessel, port: DockingPort, reading: dict,
            t: float) -> None:
    """The 'acted' method flies a frame on at time 't': the autopilot
    matching the station, the thrusters pushing the nose to the point
    out on the axis, then straight in."""
    if not self.on:
      return
    axis = reading['axis']
    vessel.autopilot.matched(port.turnAt(t), reading['spin'])
    offset, drift = reading['offset'], reading['drift']
    if self.phase == 'round':
      out, along = self.route[0]
      error = tuple(o - out * w - along * a for o, w, a in zip(
        offset, self.outward, axis))
      far = norm(error)
      if far < ROUND_NEAR:
        self.route = self.route[1:]
        if not self.route:
          self.phase = 'closing'
      fast = min(APPROACH_FAST, math.sqrt(2.0 * BRAKE * far))
      wanted = tuple(-fast * e for e in unit(error)) if far > 1e-6 else (
        0.0, 0.0, 0.0)
    elif self.phase == 'closing':
      error = tuple(o - HOLD_OUT * a for o, a in zip(offset, axis))
      far = norm(error)
      fast = min(APPROACH_FAST, math.sqrt(2.0 * BRAKE * far))
      wanted = tuple(-fast * e for e in unit(error)) if far > 1e-6 else (
        0.0, 0.0, 0.0)
      near, slow, tilt, turning = READY
      if (far < near and norm(drift) < slow and reading['tilt'] < tilt
              and reading['turning'] < turning):
        self.phase = 'final'
    else:
      along = reading['along']
      across = tuple(o - along * a for o, a in zip(offset, axis))
      speed = max(FINAL_SPEED, min(FINAL_FAST, math.sqrt(
        2.0 * FINAL_BRAKE * max(0.0, along - FINAL_NEAR))))
      wanted = tuple(-CENTRING * c - speed * a for c, a in zip(
        across, axis))
    settle = FINAL_SETTLE if self.phase == 'final' else SETTLE
    push = tuple((w - d) / settle for w, d in zip(wanted, drift))
    size = norm(push)
    if size > GUIDED_ACCEL:
      push = tuple(p * GUIDED_ACCEL / size for p in push)
    vessel.rcs = unrotated(vessel.turn, tuple(MASS * p for p in push))

  def stopped(self, vessel: Vessel) -> None:
    """The 'stopped' method lets the rocket go: its thrusters quiet."""
    self.phase, self.route = 'off', ()
    vessel.rcs = (0.0, 0.0, 0.0)
