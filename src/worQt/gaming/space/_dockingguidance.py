"""
DockingGuidance docks the rocket to the space station by itself (user,
2026-11-17: "we include buttons so that a try-hard *could* manually do
the thing. If he hates fun. But where we also provide an automated
system for the rest of. Same with docking"): from within 'REACH' of the
station's port it turns the rocket to match the station (nose down its
axis, turning with it: the autopilot's 'match'), brings the nose by the
docking thrusters to a point 'HOLD_OUT' out on the axis, steady, then
straight in at 'FINAL_SPEED' till the latch catches. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._station import SPIN
from ._turns import norm, unrotated, unit
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._dockingport import DockingPort
  from ._vessel import Vessel

#  The docking thrusters push the rocket this hard, m/s² (each way).
RCS_ACCEL = 0.15
#  It docks from within 'REACH' m of the port, drifting no faster than
#  'DRIFT_MOST' m/s from it.
REACH = 5000.0
DRIFT_MOST = 50.0
#  The final approach starts 'HOLD_OUT' m out on the station's axis,
#  once the nose is within 'READY' (m, m/s, rad, rad/s: off the point,
#  drifting, tilted, turning off the station's); then the nose comes in
#  at 'FINAL_SPEED' m/s, kept on the axis 'CENTRING' a second.
HOLD_OUT = 100.0
READY = (2.0, 0.2, math.radians(2.0), 0.01)
FINAL_SPEED = 0.3
CENTRING = 0.2
#  Closing in it goes no faster than 'APPROACH_FAST' m/s, nor than it can
#  stop braking at 'BRAKE' m/s²; it brings its drift to the speed it
#  wants most of the way in 'SETTLE' s.
APPROACH_FAST = 5.0
BRAKE = 0.08
SETTLE = 2.0
#  It never hurries time (user, 2026-11-17: "Warp should not be
#  automatic!").
#  Its phases.
PHASES = ('off', 'closing', 'final')


class DockingGuidance:
  """
  DockingGuidance flies the rocket into the station's port: its 'phase'
  ('PHASES'; 'on' while not 'off'); 'started' begins (or says why not:
  too far, too fast, docked), 'acted' flies a frame on (the autopilot
  matching, the thrusters pushing), 'stopped' lets go (the thrusters
  quiet; the autopilot as it was left).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  phase: str

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.phase = 'off'

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
    self.phase = 'closing'
    return ''

  def acted(self, vessel: Vessel, port: DockingPort, reading: dict,
            t: float) -> None:
    """The 'acted' method flies a frame on at time 't': the autopilot
    matching the station, the thrusters pushing the nose to the point
    out on the axis, then straight in."""
    if not self.on:
      return
    axis = reading['axis']
    vessel.autopilot.matched(port.turnAt(t), tuple(SPIN * a for a in axis))
    offset, drift = reading['offset'], reading['drift']
    if self.phase == 'closing':
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
      wanted = tuple(-CENTRING * c - FINAL_SPEED * a for c, a in zip(
        across, axis))
    push = tuple((w - d) / SETTLE for w, d in zip(wanted, drift))
    size = norm(push)
    if size > RCS_ACCEL:
      push = tuple(p * RCS_ACCEL / size for p in push)
    vessel.rcs = unrotated(vessel.turn, tuple(MASS * p for p in push))

  def stopped(self, vessel: Vessel) -> None:
    """The 'stopped' method lets the rocket go: its thrusters quiet."""
    self.phase = 'off'
    vessel.rcs = (0.0, 0.0, 0.0)
