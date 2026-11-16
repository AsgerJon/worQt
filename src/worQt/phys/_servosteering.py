"""
The stand-in car's steering and toe (user, 2026-11-15: "replace our
physical parts with the equivalences at higher abstraction levels"):
no rack, tie rods or toe links among its connections; each corner's
carrier turned about its slide on the chassis by a servo (a 'TurnPoint'
toward a fourth wall point of its own, '_magiccar'), its angle worked
out here each frame: the front ones as the car of parts' rack turned
its knuckles for the angle the hands ask of the steering wheel
('STEERED', measured), every wheel's toe as its tune-up sets it, the
rear's toe in as the car of parts stands ('REAR_TOE').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  The car of parts' steering, standing on the yard (scratch
#  magic/reference.py, 2026-11-15): the angle the hands ask of the
#  steering wheel, rad (the column follows it to 0.3 %), and the inner
#  and the outer front wheel's on the road, deg (left and right turns
#  averaged: turning right they read 0.2 deg apart either way; ~3.8 deg
#  a radian, a hair quicker further out, a tenth of a degree's Ackermann
#  at 11 deg); past the last, as the last two.
STEERED = ((0.0, 0.0, 0.0), (0.5, 1.770, 1.699), (1.5, 5.513, 5.377),
           (3.0, 11.298, 11.193), (4.5, 17.170, 17.030))
#  Each rear wheel's toe in standing on the car of parts, rad (its toe
#  link's 'TOE_IN' less what its load turns out: ~0.1 deg in each).
REAR_TOE = math.radians(0.1)


def steeredOf(asked: float) -> tuple[float, float]:
  """The 'steeredOf' function returns the left and the right front
  wheel's angles on the road, rad (left counted up), for the hands
  asking 'asked' rad of the steering wheel ('STEERED': the inner wheel
  the one the car turns toward)."""
  far = abs(asked)
  rows = STEERED
  low, high = rows[-2], rows[-1]
  for first, second in zip(rows, rows[1:]):
    if far <= second[0]:
      low, high = first, second
      break
  share = (far - low[0]) / (high[0] - low[0])
  inner = math.radians(low[1] + (high[1] - low[1]) * share)
  outer = math.radians(low[2] + (high[2] - low[2]) * share)
  if asked >= 0.0:
    return inner, outer
  return -outer, -inner


class ServoSteering:
  """
  ServoSteering works the stand-in car's four carriers' servos
  ('walls', in 'CORNERS' order: front left, front right, rear left,
  rear right; each the 'FourthWall' its carrier's 'TurnPoint' turns it
  about its slide toward, left counted up): the front ones toward the
  angle the steering wheel's hands ask ('wall', a 'FourthWall':
  'steeredOf'), each wheel by its toe
  ('toes', rad, the tune-up's: its front turned in toward the car's
  middle counted up; the rear ones' past 'REAR_TOE'), each over the
  cosine of how far its slide leans from upright ('leans', rad: a turn
  about it heads the wheel by that share).
  """

  __slots__ = ('walls', 'wall', 'toes', 'leans')

  def __init__(self, walls: tuple, wall: object, toes: tuple,
               leans: tuple) -> None:
    self.walls, self.wall = tuple(walls), wall
    self.toes, self.leans = tuple(toes), tuple(leans)

  def worked(self, seconds: float) -> None:
    """The 'worked' method sets each servo's angle for the next
    'seconds' (the hands' angle as it is now)."""
    left, right = steeredOf(self.wall.value)
    headings = (left, right, 0.0, 0.0)
    sides = (1.0, -1.0, 1.0, -1.0)
    for k, servo in enumerate(self.walls):
      toe = self.toes[k] + (REAR_TOE if k >= 2 else 0.0)
      heading = headings[k] - sides[k] * toe
      servo.value = heading / math.cos(self.leans[k])
