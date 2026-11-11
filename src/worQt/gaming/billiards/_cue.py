"""
Cue is the stick, and just another cushion: one that moves, striking a
ball at a point on its face, setting it moving and spinning.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._carom_table import Ball

#  A stroke seen from the shooter, the cue at a speed of one and the ball
#  of radius one: the ball's speed to the right and forward, and its spin
#  about the right, the forward and the up axes.
Stroke = tuple[float, float, float, float, float]


class Cue(NamedTuple):
  """
  Cue is the stick, held level, in mm, g and s, and it is just another
  cushion (the user's): seen from the stick, the ball flies into the
  standing tip and comes off it as off a cushion's nose. The tip pushes
  along the line from the point struck to the ball's middle, a lively
  spring and damper pressed for 'contact' seconds, giving back
  'liveliness' of the speed they met at, never pulling; the chalk holds
  the tip with friction against the slip there, at most 'grip' of the
  push. The point struck is 'top' up from the middle and 'side' to the
  shooter's right, each a share of the radius, as the ball shows its
  face to the cue.

  The stick is 'weight' grams along its length and the ball
  'ballWeight'; sideways and up and down only its end gives, as light
  as 'endMass' grams. So a ball struck off the middle leaves a little
  to the other side of the cue's line, the squirt, the less the lighter
  the end. Struck in the middle the ball leaves along the cue's line,
  (1 + 'liveliness') times the stick's share of the two weights as fast
  as the stick came; struck 2/5 of the radius up it rolls, near enough;
  below, it draws; to the right it spins anticlockwise seen from above,
  right English, and leaves a hair to the left.

  'limit' is how far off the middle, a share of the radius, the chalk
  holds the tip: where the line from the point struck to the middle
  leans 'atan(grip)' off the cue, six tenths of the radius at a 'grip'
  of 0.75 (the user: more spin; Alciatore's half was a grip of 1/sqrt
  3, which the shots inside it barely feel); past it the tip slides
  off, a miscue. 'hitOf' keeps a point within it. 'step' is how finely
  a stroke is followed. A stroke goes as the cue's speed, so it is
  followed once a point at a speed of one and scaled. None of the
  values is known well: they are to be balanced against real strokes.
  """

  weight: float = 510.0
  ballWeight: float = 210.0
  endMass: float = 8.0
  liveliness: float = 0.75
  contact: float = 0.001
  grip: float = 0.75
  step: float = 1e-6

  @property
  def limit(self, ) -> float:
    """The 'limit' property is how far off the middle, a share of the
    radius, the chalk holds the tip: where the line from the point
    struck to the middle leans 'atan(grip)' off the cue."""
    return self.grip / math.sqrt(1.0 + self.grip * self.grip)

  def hitOf(self, top: float, side: float) -> tuple[float, float]:
    """The 'hitOf' method returns the point struck, 'top' and 'side', a
    share of the radius each, drawn in to 'limit' if past it."""
    off = math.hypot(top, side)
    if off <= self.limit:
      return top, side
    return top * self.limit / off, side * self.limit / off

  def strokeOf(self, top: float, side: float) -> Stroke:
    """The 'strokeOf' method returns the ball after the stick strikes
    it at 'top' and 'side' at a speed of one, the ball of radius one,
    seen from the shooter: its speed to the right and forward, and its
    spin about the right, the forward and the up axes."""
    return _strokeOf(self, top, side)

  def centreShare(self, ) -> float:
    """The 'centreShare' method returns how fast a ball struck in the
    middle leaves, a share of the stick's speed."""
    return _strokeOf(self, 0.0, 0.0)[1]

  def squirtOf(self, top: float, side: float) -> float:
    """The 'squirtOf' method returns how far off the cue's line a ball
    struck at 'top' and 'side', drawn in to 'limit', leaves, in degrees,
    to the shooter's right above nought."""
    right, forward = _strokeOf(self, *self.hitOf(top, side))[:2]
    return math.degrees(math.atan2(right, forward))

  def rollHeight(self, ) -> float:
    """The 'rollHeight' method returns how far up the middle, a share of
    the radius, a ball is struck to roll at once: 2/5 for a stick that
    pushes only along its length, a little more as its light end lets
    the push lean down into the slate, as it squirts a ball struck to
    the side."""
    return _rollHeight(self)

  def struck(self, ball: Ball, aimX: float, aimY: float, speed: float,
             top: float, side: float, radius: float) -> Ball:
    """The 'struck' method returns 'ball', of 'radius', struck by the
    stick laid along 'aimX', 'aimY' on the table, at 'top' and 'side'
    off its middle, drawn in to 'limit': the stick as fast as sends a
    ball struck in the middle off at 'speed' mm/s. Struck off the
    middle it leaves slower, and squirts off the stick's line."""
    top, side = self.hitOf(top, side)
    return self._played(ball, aimX, aimY, speed / self.centreShare(),
                        _strokeOf(self, top, side), radius)

  def sent(self, ball: Ball, aimX: float, aimY: float, speed: float,
           top: float, side: float, radius: float) -> Ball:
    """The 'sent' method returns 'ball', of 'radius', struck at 'top'
    and 'side' off its middle, drawn in to 'limit', so that it leaves
    along 'aimX', 'aimY' on the table at 'speed' mm/s, as a player
    aims: the stick laid off that line by the squirt, the other way, as
    fast as it takes."""
    top, side = self.hitOf(top, side)
    stroke = _strokeOf(self, top, side)
    off = math.atan2(stroke[0], stroke[1])
    turnX, turnY = math.cos(off), math.sin(off)
    return self._played(ball, aimX * turnX - aimY * turnY,
                        aimX * turnY + aimY * turnX,
                        speed / math.hypot(stroke[0], stroke[1]), stroke,
                        radius)

  def _played(self, ball: Ball, aimX: float, aimY: float, scale: float,
              stroke: Stroke, radius: float) -> Ball:
    """Returns 'ball', of 'radius', after 'stroke' with the stick laid
    along 'aimX', 'aimY' at 'scale' times a speed of one."""
    length = math.hypot(aimX, aimY)
    fx, fy = aimX / length, aimY / length
    rx, ry = fy, -fx
    right, forward, wr, wf, wz = (scale * value for value in stroke)
    return Ball(ball.name, ball.x, ball.y, ball.turn,
                right * rx + forward * fx, right * ry + forward * fy,
                (wr * rx + wf * fx) / radius, (wr * ry + wf * fy) / radius,
                wz / radius)


@functools.lru_cache(maxsize=64)
def _rollHeight(cue: Cue) -> float:
  """Returns how far up the middle 'cue' strikes a ball to roll at once:
  where the slip under it is nought, found by false position with the
  Illinois turn between the middle and the limit."""

  def slipOf(top: float) -> float:
    """Returns how fast the ball's lowest point slips forward, a share
    of how fast it moves, struck 'top' up."""
    right, forward, wr, wf, wz = _strokeOf(cue, top, 0.0)
    return (forward + wr) / forward

  low, high = 0.0, cue.limit
  lowSlip, highSlip = slipOf(low), slipOf(high)
  if highSlip > 0.0:
    return high
  side = 0
  for _ in range(40):
    top = high - highSlip * (high - low) / (highSlip - lowSlip)
    slip = slipOf(top)
    if abs(slip) < 1e-12:
      return top
    if slip > 0.0:
      low, lowSlip = top, slip
      if side == 1:
        highSlip *= 0.5
      side = 1
    else:
      high, highSlip = top, slip
      if side == -1:
        lowSlip *= 0.5
      side = -1
  return top


@functools.lru_cache(maxsize=4096)
def _strokeOf(cue: Cue, top: float, side: float) -> Stroke:
  """Returns the ball after 'cue' strikes it at 'top' and 'side' at a
  speed of one, followed step by step: the ball of radius one and
  weight one, in the shooter's axes, right, forward and up. The ball's
  press into the slate, or its hop off it, is let go at the end."""
  back = math.sqrt(max(1.0 - top * top - side * side, 0.0))
  point = (side, -back, top)
  normal = (-side, back, -top)
  heavy = cue.weight / cue.ballWeight
  light = cue.endMass / cue.ballWeight
  masses = (light, heavy, light)
  fall = math.log(cue.liveliness)
  ratio = -fall / math.sqrt(math.pi ** 2 + fall ** 2)
  together = heavy / (1.0 + heavy)
  swing = math.pi / (cue.contact * math.sqrt(1.0 - ratio * ratio))
  stiff = together * swing * swing
  damp = 2.0 * ratio * swing * together
  speed, spin, tip = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]
  step, given, pressed = cue.step, 0.0, False
  for _ in range(int(20.0 * cue.contact / step)):
    meet = _pointSpeed(speed, spin, point)
    closing = sum((tip[k] - meet[k]) * normal[k] for k in range(3))
    push = stiff * given + damp * closing if given > 0.0 else 0.0
    if push > 0.0:
      pressed = True
      _pushed(speed, tip, masses, normal, push * step)
      _gripped(speed, spin, tip, masses, point, normal, cue.grip * push
               * step)
    meet = _pointSpeed(speed, spin, point)
    given += sum((tip[k] - meet[k]) * normal[k] for k in range(3)) * step
    if pressed and given <= 0.0:
      break
  return speed[0], speed[1], spin[0], spin[1], spin[2]


def _pointSpeed(speed: list, spin: list, point: tuple) -> list:
  """Returns how fast the ball's 'point' moves, its middle at 'speed'
  and spinning at 'spin'."""
  return [speed[0] + spin[1] * point[2] - spin[2] * point[1],
          speed[1] + spin[2] * point[0] - spin[0] * point[2],
          speed[2] + spin[0] * point[1] - spin[1] * point[0]]


def _pushed(speed: list, tip: list, masses: tuple, normal: tuple,
            impulse: float) -> None:
  """Pushes the ball along 'normal' and the tip back, by 'impulse'."""
  for k in range(3):
    speed[k] += impulse * normal[k]
    tip[k] -= impulse * normal[k] / masses[k]


def _gripped(speed: list, spin: list, tip: list, masses: tuple,
             point: tuple, normal: tuple, most: float) -> None:
  """Holds the ball's 'point' to the tip by friction, an impulse of at
  most 'most': against the slip across 'normal', no more than stops
  it."""
  meet = _pointSpeed(speed, spin, point)
  slip = [meet[k] - tip[k] for k in range(3)]
  across = sum(slip[k] * normal[k] for k in range(3))
  slip = [slip[k] - across * normal[k] for k in range(3)]
  size = math.sqrt(sum(value * value for value in slip))
  if size <= 0.0:
    return
  way = [value / size for value in slip]
  give = 3.5 + sum(way[k] * way[k] / masses[k] for k in range(3))
  held = min(most, size / give)
  jx, jy, jz = (-held * value for value in way)
  for k, j in enumerate((jx, jy, jz)):
    speed[k] += j
    tip[k] -= j / masses[k]
  spin[0] += (point[1] * jz - point[2] * jy) / 0.4
  spin[1] += (point[2] * jx - point[0] * jz) / 0.4
  spin[2] += (point[0] * jy - point[1] * jx) / 0.4
