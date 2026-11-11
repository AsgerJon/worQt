"""
Cloth is the felt a ball moves on, and moves a single ball over it,
exactly, from one change of its motion to the next.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._carom_table import Ball, Turn

STILL_SPEED = 1e-6  # mm/s: slower slips and speeds are none
_TURN_STEP = 1.0 / 500.0  # s: the longest step turning the dots

#  A ball's motion at a moment within a phase: x, y, vx, vy, wx, wy.
Moment = tuple[float, float, float, float, float, float]


class Cloth(NamedTuple):
  """
  Cloth is the felt of a table, in mm and s, as the user, who plays, has
  it: a ball touches it in a small dent, moves and turns against it, and
  the friction pushes back. Its 'sliding' friction acts against the slip
  of the ball's lowest point while that slips; once it does not, the
  ball rolls, and the felt, squeezed ahead of the ball and slow to come
  back behind it, pushes a little ahead of the lowest point: 'rolling'
  is that offset over the radius, and slows a rolling ball by 5/7 of it
  times 'gravity'. Side spin twists the dent's contact, a disc 'patch'
  across, and dies against the sliding friction there. A ball left
  spinning in place, not moving (the user), spins down so no faster than
  in about three seconds: steadily as the patch has it while the spin is
  above what the patch would stop in 'spinTail' s, then fading by e each
  'spinTail' s, still once under 'spinStop' rad/s; a spin of 2 rad/s, a
  turn every three seconds, lasts three ('spinningAt',
  'spinningTime'). It depends on the spin alone, so the moments it is
  reckoned from never change it.

  'advanced' moves a single ball on, exactly: while it slides, its slip
  keeps its direction and dies at 7/2 the sliding friction times
  gravity, after which it rolls, slowing steadily to rest; its side spin
  dies steadily all the while and never bends its path. As a roll ends,
  the felt, pressed ahead of the ball, pushes it back: it rolls back
  'rollBack' mm, once, slowing as a roll does ('rolledBack'), as the
  user sees a ball settle a tiny angle back. Each phase is
  solved in closed form ('motionAt', 'spinAt', 'phaseTime'), and the
  moments the phases change are found exactly ('settled'), so the ball
  can neither tremble nor creep at rest. Only its 'turn', which the
  physics need not know, is stepped, finely, for the dots ('moved').
  The cloth knows no cushions and no other balls; 'Motion' adds them.
  """

  #  Fitted 2026-11-07 to the break as a Korean guide draws it (japong.com).
  sliding: float = 0.2134
  rolling: float = 0.01
  patch: float = 2.027
  gravity: float = 9810.0
  rollBack: float = 1.5
  spinTail: float = 1.0
  spinStop: float = 0.095

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def slipOf(self, ball: Ball, radius: float) -> tuple[float, float]:
    """The 'slipOf' method returns how fast the lowest point of 'ball',
    of 'radius', slides over the cloth, across and along, in mm/s."""
    return ball.vx - radius * ball.wy, ball.vy + radius * ball.wx

  def phaseOf(self, ball: Ball, radius: float) -> str:
    """The 'phaseOf' method returns what 'ball' is doing: 'sliding',
    'rolling', 'spinning' in place or 'still'."""
    if math.hypot(*self.slipOf(ball, radius)) > STILL_SPEED:
      return 'sliding'
    if math.hypot(ball.vx, ball.vy) > STILL_SPEED:
      return 'rolling'
    if abs(ball.wz) > STILL_SPEED / radius:
      return 'spinning'
    return 'still'

  def spinDecay(self, radius: float) -> float:
    """The 'spinDecay' method returns how fast side spin dies, in
    rad/s², the patch's friction, two thirds of its radius out, over
    the ball's moment of inertia."""
    torque = 2.0 / 3.0 * self.sliding * self.gravity * self.patch
    return torque / (0.4 * radius * radius)

  def rollingDecay(self, ) -> float:
    """The 'rollingDecay' method returns how fast a rolling ball slows,
    in mm/s²."""
    return 5.0 / 7.0 * self.rolling * self.gravity

  def energyOf(self, ball: Ball, radius: float) -> float:
    """The 'energyOf' method returns the energy of motion of 'ball', of
    'radius', in J a kilogram: moving and spinning."""
    spin = ball.wx * ball.wx + ball.wy * ball.wy + ball.wz * ball.wz
    moving = ball.vx * ball.vx + ball.vy * ball.vy
    return 0.5e-6 * (moving + 0.4 * radius * radius * spin)

  def phaseTime(self, ball: Ball, phase: str, radius: float) -> float:
    """The 'phaseTime' method returns how long 'ball' stays in 'phase':
    sliding until its slip is gone, rolling until it rests, spinning in
    place until its side spin dies; still, for ever."""
    if phase == 'sliding' and self.sliding > 0.0:
      slip = math.hypot(*self.slipOf(ball, radius))
      return 2.0 * slip / (7.0 * self.sliding * self.gravity)
    if phase == 'rolling' and self.rolling > 0.0:
      return math.hypot(ball.vx, ball.vy) / self.rollingDecay()
    if phase == 'spinning':
      return self.spinningTime(abs(ball.wz), radius)
    return math.inf

  def accelerationOf(self, ball: Ball, phase: str,
                     radius: float) -> tuple[float, float]:
    """The 'accelerationOf' method returns how 'ball' speeds up in
    'phase', across and along, in mm/s², the same all through it."""
    if phase == 'sliding':
      sx, sy = self.slipOf(ball, radius)
      slip = math.hypot(sx, sy)
      push = self.sliding * self.gravity
      return -push * sx / slip, -push * sy / slip
    if phase == 'rolling':
      speed = math.hypot(ball.vx, ball.vy)
      slow = self.rollingDecay()
      return -slow * ball.vx / speed, -slow * ball.vy / speed
    return 0.0, 0.0

  def motionAt(self, ball: Ball, phase: str, time: float,
               radius: float) -> Moment:
    """The 'motionAt' method returns where 'ball' is and how it moves
    and turns, but for its side spin, 'time' into 'phase'."""
    ax, ay = self.accelerationOf(ball, phase, radius)
    x = ball.x + ball.vx * time + 0.5 * ax * time * time
    y = ball.y + ball.vy * time + 0.5 * ay * time * time
    vx, vy = ball.vx + ax * time, ball.vy + ay * time
    if phase == 'sliding':
      turn = 2.5 / radius
      return (x, y, vx, vy, ball.wx + turn * ay * time,
              ball.wy - turn * ax * time)
    if phase == 'rolling':
      return x, y, vx, vy, -vy / radius, vx / radius
    return ball.x, ball.y, 0.0, 0.0, 0.0, 0.0

  def spinAt(self, ball: Ball, time: float, radius: float) -> float:
    """The 'spinAt' method returns the side spin of 'ball' 'time'
    later, dying steadily to nought and staying there."""
    left = max(abs(ball.wz) - self.spinDecay(radius) * time, 0.0)
    return math.copysign(left, ball.wz)

  def spinningTime(self, spin: float, radius: float) -> float:
    """The 'spinningTime' method returns how long a ball spinning in
    place at 'spin' rad/s keeps spinning: steadily down to the knee, as
    the patch has it, then fading till under 'spinStop'."""
    decay = self.spinDecay(radius)
    if decay <= 0.0:
      return math.inf
    if spin <= self.spinStop:
      return 0.0
    knee = max(decay * self.spinTail, self.spinStop)
    if spin <= knee:
      return self.spinTail * math.log(spin / self.spinStop)
    return (spin - knee) / decay + self.spinTail * math.log(
      knee / self.spinStop)

  def spinningAt(self, ball: Ball, time: float, radius: float) -> float:
    """The 'spinningAt' method returns the side spin of 'ball', spinning
    in place, 'time' later: steadily down to the knee, decay times
    'spinTail', then fading by e each 'spinTail' s, nought once under
    'spinStop'."""
    decay = self.spinDecay(radius)
    spin = abs(ball.wz)
    if decay <= 0.0:
      return ball.wz
    knee = max(decay * self.spinTail, self.spinStop)
    if spin > knee:
      steady = (spin - knee) / decay
      if time <= steady:
        return math.copysign(spin - decay * time, ball.wz)
      time, spin = time - steady, knee
    if self.spinTail <= 0.0:
      return 0.0
    left = spin * math.exp(-time / self.spinTail)
    return math.copysign(left, ball.wz) if left > self.spinStop else 0.0

  def moved(self, ball: Ball, phase: str, span: float,
            radius: float) -> Ball:
    """The 'moved' method returns 'ball' moved 'span' on in 'phase', its
    turn stepped finely by the spin at the middle of each step, as long
    as it turns at all."""
    turning = span
    decay = self.spinDecay(radius)
    spun = self.spinningAt if phase == 'spinning' else self.spinAt
    if phase == 'spinning':
      turning = min(span, self.spinningTime(abs(ball.wz), radius))
    elif phase == 'still' and decay > 0.0:
      turning = min(span, abs(ball.wz) / decay)
    count = max(1, math.ceil(turning / _TURN_STEP))
    step = turning / count
    turn = ball.turn
    for k in range(count):
      middle = (k + 0.5) * step
      _, _, _, _, wx, wy = self.motionAt(ball, phase, middle, radius)
      wz = spun(ball, middle, radius)
      turn = turned(turn, wx * step, wy * step, wz * step)
    x, y, vx, vy, wx, wy = self.motionAt(ball, phase, span, radius)
    wz = spun(ball, span, radius)
    return Ball(ball.name, x, y, turn, vx, vy, wx, wy, wz, ball.settling)

  def settled(self, ball: Ball, phase: str, radius: float) -> Ball:
    """The 'settled' method returns 'ball' as the phase after 'phase'
    begins, exactly: rolling once a slide ends, its spin matched to its
    speed; at rest once a roll ends, spinning in place if its side spin
    lasts; still once that spin dies."""
    if phase == 'sliding':
      return Ball(ball.name, ball.x, ball.y, ball.turn, ball.vx, ball.vy,
                  -ball.vy / radius, ball.vx / radius, ball.wz,
                  ball.settling)
    wz = 0.0 if phase == 'spinning' else ball.wz
    return Ball(ball.name, ball.x, ball.y, ball.turn, 0.0, 0.0, 0.0, 0.0,
                wz, ball.settling)

  def rolledBack(self, before: Ball, rested: Ball, radius: float) -> Ball:
    """The 'rolledBack' method returns 'rested', a ball whose roll from
    'before' has just ended, rolling back the way it came, so it comes
    to rest 'rollBack' mm back, slowing as a roll does; as it was if it
    was rolling back already, or the felt gives nothing back."""
    speed = math.hypot(before.vx, before.vy)
    slow = self.rollingDecay()
    if before.settling or self.rollBack <= 0.0 or slow <= 0.0:
      return rested
    if speed <= STILL_SPEED:
      return rested
    back = math.sqrt(2.0 * slow * self.rollBack)
    vx, vy = -back * before.vx / speed, -back * before.vy / speed
    return Ball(rested.name, rested.x, rested.y, rested.turn, vx, vy,
                -vy / radius, vx / radius, rested.wz, True)

  def advanced(self, ball: Ball, seconds: float, radius: float) -> Ball:
    """The 'advanced' method returns 'ball', of 'radius', as it is
    'seconds' later on the cloth: sliding, rolling, spinning in place
    and still, each in closed form, from one change to the next."""
    passed = 0.0
    while passed < seconds:
      phase = self.phaseOf(ball, radius)
      left = seconds - passed
      span = min(left, self.phaseTime(ball, phase, radius))
      moved = self.moved(ball, phase, span, radius)
      if span < left:
        moved = self.settled(moved, phase, radius)
        if phase == 'rolling':
          moved = self.rolledBack(ball, moved, radius)
      ball = moved
      passed += span
    return ball


def turned(turn: Turn, ax: float, ay: float, az: float) -> Turn:
  """The 'turned' function returns 'turn' turned on by the angle 'ax',
  'ay', 'az', a turn about that axis by its length, about the table's
  axes, kept of length one."""
  angle = math.sqrt(ax * ax + ay * ay + az * az)
  if angle < 1e-15:
    return turn
  half = 0.5 * angle
  share = math.sin(half) / angle
  qw, qx, qy, qz = math.cos(half), ax * share, ay * share, az * share
  w, x, y, z = turn
  nw = qw * w - qx * x - qy * y - qz * z
  nx = qw * x + qx * w + qy * z - qz * y
  ny = qw * y - qx * z + qy * w + qz * x
  nz = qw * z + qx * y - qy * x + qz * w
  size = math.sqrt(nw * nw + nx * nx + ny * ny + nz * nz)
  return nw / size, nx / size, ny / size, nz / size
