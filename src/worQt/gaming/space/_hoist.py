"""
A lift's cage on its motor (user, 2026-11-18: "PHYSICS MUST BE REAL"; the
cages were set going at a set speed, whatever they carried and however
hard they were pulled; "The tower lift did feel very wrong"): its
motor pushes it along its shaft toward the speed its run wants
(speeding up at 'accel', at most 'fast', slowing to stop on its stop),
no harder than its most push (its run's slowing fed ahead, as a lift's
drive does: it does not overshoot its stop), against what pulls the
cage and its rider along the shaft (the pad's weight; the station's
turning); standing at a stop its brake holds it. What the motor and the walls
push it by, they push the rest back by (the caller's: '_spacewindow').
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  How soon the motor brings the cage to the speed its run wants, s; its
#  steps, s; within how far of its stop, moving no faster than
#  'SETTLED', its brake takes it, m and m/s.
MOTOR_TIME = 0.3
HOIST_STEP = 1.0 / 240.0
ARRIVED = 0.005
SETTLED = 0.02


def hoisted(floor: float, speed: float, target: float | None,
            seconds: float, along: float, mass: float, most: float,
            accel: float, fast: float) -> tuple:
  """Returns a cage's floor (m along its shaft), its speed and its stop
  (None: standing) 'seconds' s on, and its acceleration along the shaft
  over them (m/s², on the average): its motor pushing it ('mass' kg with
  its rider; no harder than 'most' N) toward the speed its run wants
  (at most 'fast', speeding up and slowing down at 'accel'), pulled
  'along' m/s² along the shaft (its way out or up); standing, its brake
  holds it where it is."""
  if seconds <= 0.0:
    return floor, speed, target, 0.0
  if target is None:
    return floor, 0.0, None, 0.0
  began = speed
  steps = max(1, math.ceil(seconds / HOIST_STEP))
  dt = seconds / steps
  for _ in range(steps):
    left = target - floor
    if abs(left) < ARRIVED and abs(speed) < SETTLED:
      return target, 0.0, None, -began / seconds
    way = 1.0 if left > 0.0 else -1.0
    braking = math.sqrt(2.0 * accel * abs(left))
    wanted = way * min(fast, braking)
    ahead = -way * accel if braking < fast and speed * way > 0.0 else 0.0
    push = mass * (ahead + (wanted - speed) / MOTOR_TIME - along)
    push = max(-most, min(most, push))
    speed += (push / mass + along) * dt
    floor += speed * dt
  return floor, speed, target, (speed - began) / seconds
