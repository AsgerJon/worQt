"""
SteeringWheel is the driver's steering wheel as the keys work it (user,
2026-11-12: "an indicator of the current position of the steering
wheel from -135 to 135 degrees. Then A should push the steering wheel
left, D to right. not giving input should pull back to neutral"; the
helper that stood here before is gone). Held, a key turns the wheel
toward its side at 'PUSH', as far as 'WHEEL_LOCK' either way; let go
(or both held) it comes back to straight at 'BACK'; a key held against
the way the wheel lies turns it back no slower than letting go would.
The hands turn the car's column to the wheel's share of its lock
('column': the wheel at 'WHEEL_LOCK' asks the column's 'STEER_LOCK').
The mouse (user, 2026-11-12: "put in mouse control of steering. like
first person walking sim, but where i steer the wheels instead") turns
it where it is ('moved'), and it stays there: a hand on the wheel.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._car import STEER_LOCK

#  How far the wheel turns either way, rad; how fast a key held turns
#  it, and how fast it comes back let go, rad/s (straight to the lock in
#  0.75 s, back from it in 0.5 s).
WHEEL_LOCK = math.radians(135.0)
PUSH, BACK = math.radians(180.0), math.radians(270.0)


class SteeringWheel:
  """
  SteeringWheel holds the wheel's 'angle', rad, left positive, as the
  keys have turned it ('turned'), and the column it asks of the hands
  ('column').
  """

  def __init__(self, ) -> None:
    self.angle = 0.0

  @property
  def column(self, ) -> float:
    """The column's turn the wheel asks, rad, left positive: the wheel's
    share of its lock times the column's."""
    return self.angle * STEER_LOCK / WHEEL_LOCK

  def moved(self, by: float) -> None:
    """The 'moved' method turns the wheel 'by' rad (left up), as a hand
    on it does, within 'WHEEL_LOCK'."""
    self.angle = max(-WHEEL_LOCK, min(WHEEL_LOCK, self.angle + by))

  def turned(self, steering: int, seconds: float) -> None:
    """The 'turned' method turns the wheel for 'seconds' as the steering
    keys ask ('steering' left 1, right -1, else nought): toward the key
    held at 'PUSH' (at 'BACK' should that be quicker and the wheel lie
    the other way), within 'WHEEL_LOCK'; with none, back toward straight
    at 'BACK', stopping there."""
    back = BACK * seconds
    if not steering:
      left = max(0.0, abs(self.angle) - back)
      self.angle = left if self.angle > 0.0 else -left
      return
    step = PUSH * seconds
    if steering * self.angle < 0.0:
      step = max(step, back)
    angle = self.angle + steering * step
    self.angle = max(-WHEEL_LOCK, min(WHEEL_LOCK, angle))
