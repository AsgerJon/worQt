"""
Motion moves the balls on a carom table: over the cloth exactly, and
through their hits on the cushions and on each other step by step.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

import numpy

from ._carom import Carom
from ._carom_table import Ball, CaromTable
from ._cloth import Cloth, turned
from ._cushion import Cushion, softplus

_TOUCH = 1e-6  # mm: nearer than this, a ball touches a cushion or ball
_DOZE = 1e-4  # s: a ball that cannot touch anything for longer sleeps

#  A cushion seen from a ball: how far its middle is from the cushion's
#  nose across the cloth, and the way into the table, across and along.
Side = tuple[float, float, float]

#  The cushions by name, in the order 'sidesOf' gives them: x nought, x
#  the width, y nought, y the length.
CUSHIONS = ('left', 'right', 'foot', 'head')


class Touch(NamedTuple):
  """
  Touch is a contact beginning: 'kind' is 'cushion' or 'ball'; 'first'
  is the ball's name; 'second' is the cushion's name, one of
  'CUSHIONS', or the other ball's. A ball leaving the table will be
  'off', its 'second' empty.
  """

  kind: str
  first: str
  second: str


class Pockets(NamedTuple):
  """
  Pockets are holes drilled into a table at its cushions, as
  keglebillard has them: the cushions cut away over each in a straight
  slot, the corners' slots running 'corner' along each cushion from the
  noses' corner, the long cushions' middles' 'half' either side of the
  middle; the slots' ends, the 'jaws', meeting a ball as the nose does;
  and the holes, 'radius' round about their middles 'holes', each
  taking a ball whose middle comes over it.
  """

  corner: float
  half: float
  holes: tuple
  radius: float


class Glide(NamedTuple):
  """
  Glide is the balls moving on over the cloth, none touching anything,
  from now until the next thing happens: each ball's 'phases' all
  through it; how long it lasts, 'span'; the balls at its end, 'after',
  each one whose phase ends there settled into the next; and the
  contacts beginning there, 'touches', in order.
  """

  phases: tuple
  span: float
  after: tuple
  touches: tuple


class Motion(NamedTuple):
  """
  Motion moves the balls on its 'table', over its 'cloth', off its
  cushions as 'cushion' has them push back, and off each other as
  'carom' has them meet.

  On the cloth each ball moves exactly, phase to phase, as 'Cloth' has
  it, and the next thing to happen is found exactly: a ball's phase
  ending; a ball reaching a cushion's nose, which is 'table.nose' above
  the cloth, so the ball touches it with its middle 'reach' from it; or
  two balls meeting, a root of a quartic, their paths being quadratic.
  Through hits, the balls touching anything are followed step by step,
  the others moving on exactly. A cushion pushes along the line from its
  nose to the ball's middle, so down into the slate as well, with
  friction against the slip along it and up and down it; balls push
  apart along the line between their middles, with friction at the point
  they touch; the slate bears each ball's weight and every push down,
  with friction against the slip there, and the side spin dies the
  faster for it. A ball may touch two cushions in a corner, or a cushion
  and a ball. Once clear, all are back on the cloth. 'glided' and
  'collided' are the two pieces 'played' strings together: a 'Glide'
  on the cloth to the next event, and the steps through hits.

  Not yet: a ball lifted off the slate, which a hard ball with heavy
  top spin can be, flying; and balls frozen together or to a cushion,
  the wedged ones, whose stored push comes from their history.

  With 'pockets', keglebillard's holes ('Pockets'), the cushions are
  open over the slots, the slots' jaws meet a ball as the nose does, and
  'hitTime' finds a ball reaching a jaw too; the holes taking the balls
  are 'KegleMotion's. The steps through hits in plain Python ('Hits'
  not compiled) know no pockets.
  """

  table: CaromTable = CaromTable()
  cloth: Cloth = Cloth()
  cushion: Cushion = Cushion()
  carom: Carom = Carom()
  pockets: Pockets | None = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def reach(self, ) -> float:
    """The 'reach' method returns how far a ball's middle is from a
    cushion's nose, across the cloth, as it touches it."""
    radius, nose = self.table.radius, self.table.nose
    return math.sqrt(radius * radius - (nose - radius) ** 2)

  def sidesOf(self, x: float, y: float) -> tuple[Side, ...]:
    """The 'sidesOf' method returns, for a ball with its middle at 'x',
    'y', each cushion as the ball sees it: how far the ball's middle is
    from its nose across the cloth, and the way into the table."""
    width, length = self.table.width, self.table.length
    return ((x, 1.0, 0.0), (width - x, -1.0, 0.0),
            (y, 0.0, 1.0), (length - y, 0.0, -1.0))

  def contactSides(self, x: float, y: float) -> list:
    """The 'contactSides' method returns, for a ball with its middle at
    'x', 'y', what of the cushions it may touch, each how far its middle
    is from it across the cloth, the way from it to the ball, and the
    cushion's place in 'CUSHIONS': the four noses, but where a pocket's
    slot opens the cushion, and the slots' jaws."""
    sides = self.sidesOf(x, y)
    if self.pockets is None:
      return [(*side, k) for k, side in enumerate(sides)]
    out = [(*side, k) for k, side in enumerate(sides)
           if not self.isOpen(k, x, y)]
    for jx, jy, k in self.jawsOf():
      dx, dy = x - jx, y - jy
      away = math.sqrt(dx * dx + dy * dy)
      if away > 0.0:
        out.append((away, dx / away, dy / away, k))
    return out

  def isOpen(self, side: int, x: float, y: float) -> bool:
    """The 'isOpen' method tells whether cushion 'side', by its place in
    'CUSHIONS', is cut away where a ball with its middle at 'x', 'y'
    would meet it: over a pocket's slot."""
    pockets = self.pockets
    if pockets is None:
      return False
    along, full = (y, self.table.length) if side < 2 else (
      x, self.table.width)
    if along < pockets.corner or along > full - pockets.corner:
      return True
    return side < 2 and abs(along - 0.5 * full) < pockets.half

  def jawsOf(self, ) -> tuple:
    """The 'jawsOf' method returns the slots' jaws, where the cushions
    are cut off over the pockets, each where on the noses' line it is
    and its cushion's place in 'CUSHIONS'; none without pockets."""
    return _jawsOf(self)

  def givenOf(self, ball: Ball) -> float:
    """The 'givenOf' method returns how far the cushion 'ball' presses
    hardest gives, in mm; nought or less when it touches none."""
    return self._given(ball.x, ball.y)

  def pressedOf(self, first: Ball, second: Ball) -> float:
    """The 'pressedOf' method returns how far two balls are pressed
    together, in mm; below nought when apart."""
    apart = math.hypot(second.x - first.x, second.y - first.y)
    return 2.0 * self.table.radius - apart

  def touching(self, ball: Ball) -> bool:
    """The 'touching' method tells whether 'ball' presses a cushion, or
    touches it moving into it."""
    radius, drop = self.table.radius, self.table.radius - self.table.nose
    for away, ix, iy, _ in self.contactSides(ball.x, ball.y):
      given = radius - math.sqrt(away * away + drop * drop)
      if given > 0.0:
        return True
      if given > -_TOUCH and ix * ball.vx + iy * ball.vy < 0.0:
        return True
    return False

  def meeting(self, first: Ball, second: Ball) -> bool:
    """The 'meeting' method tells whether two balls press together, or
    touch moving into each other."""
    pressed = self.pressedOf(first, second)
    if pressed > 0.0:
      return True
    if pressed <= -_TOUCH:
      return False
    dx, dy = second.x - first.x, second.y - first.y
    return dx * (second.vx - first.vx) + dy * (second.vy - first.vy) < 0.0

  def cushionsTouched(self, ball: Ball) -> tuple[int, ...]:
    """The 'cushionsTouched' method returns the cushions, by their
    place in 'CUSHIONS', 'ball' presses, or touches moving into."""
    radius, drop = self.table.radius, self.table.radius - self.table.nose
    out = []
    for away, ix, iy, index in self.contactSides(ball.x, ball.y):
      given = radius - math.sqrt(away * away + drop * drop)
      if index in out:
        continue
      if given > 0.0:
        out.append(index)
      elif given > -_TOUCH and ix * ball.vx + iy * ball.vy < 0.0:
        out.append(index)
    return tuple(sorted(out))

  def touchesOf(self, balls: tuple[Ball, ...]) -> frozenset:
    """The 'touchesOf' method returns the contacts among 'balls' now,
    each a 'Touch'."""
    out = set()
    for ball in balls:
      for index in self.cushionsTouched(ball):
        out.add(Touch('cushion', ball.name, CUSHIONS[index]))
    for i, one in enumerate(balls):
      for other in balls[i + 1:]:
        if self.meeting(one, other):
          out.add(Touch('ball', one.name, other.name))
    return frozenset(out)

  def inContact(self, balls: tuple[Ball, ...]) -> bool:
    """The 'inContact' method tells whether any of 'balls' touches a
    cushion or another ball."""
    if any(self.touching(ball) for ball in balls):
      return True
    count = len(balls)
    return any(self.meeting(balls[i], balls[j]) for i in range(count)
               for j in range(i + 1, count))

  def energyOf(self, balls: tuple[Ball, ...]) -> float:
    """The 'energyOf' method returns the energy of 'balls', in J a
    kilogram of ball: moving, spinning, and stored in the cushions and
    between the balls they press."""
    radius, drop = self.table.radius, self.table.radius - self.table.nose
    power = self.cushion.stiffening + 1.0
    stored = 0.0
    for ball in balls:
      for away, _, _, _ in self.contactSides(ball.x, ball.y):
        given = radius - math.sqrt(away * away + drop * drop)
        if given > 0.0:
          stored += self.cushion.stiffness() * given ** power / power
    for i, first in enumerate(balls):
      for second in balls[i + 1:]:
        stored += self.carom.storedOf(self.pressedOf(first, second))
    moving = sum(self.cloth.energyOf(ball, radius) for ball in balls)
    return moving + 1e-6 * stored

  def hitTime(self, ball: Ball, phase: str, span: float) -> float | None:
    """The 'hitTime' method returns how long until 'ball', in 'phase' on
    the cloth, reaches a cushion's nose, if it does within 'span';
    'None' if it does not."""
    if phase not in ('sliding', 'rolling'):
      return None
    ax, ay = self.cloth.accelerationOf(ball, phase, self.table.radius)
    reach, first = self.reach(), None
    for away, ix, iy in self.sidesOf(ball.x, ball.y):
      gap = away - reach
      if gap <= _TOUCH:
        continue
      time = _firstRoot(0.5 * (ix * ax + iy * ay), ix * ball.vx
                        + iy * ball.vy, gap)
      if time is not None and time <= span:
        first = time if first is None else min(first, time)
    for jx, jy, _ in self.jawsOf():
      time = _pointTime(ball, ax, ay, jx, jy, reach, span)
      if time is not None:
        first = time if first is None else min(first, time)
    return first

  def meetTime(self, first: Ball, second: Ball,
               span: float) -> float | None:
    """The 'meetTime' method returns how long until two balls on the
    cloth meet, if they do within 'span'; 'None' if they do not. Their
    paths are quadratic, so the square of the distance between them is a
    quartic in the time."""
    cloth, radius = self.cloth, self.table.radius
    phases = [cloth.phaseOf(ball, radius) for ball in (first, second)]
    resting = ('spinning', 'still')
    if all(phase in resting for phase in phases):
      return None
    ax1, ay1 = cloth.accelerationOf(first, phases[0], radius)
    ax2, ay2 = cloth.accelerationOf(second, phases[1], radius)
    vx1, vy1 = (0.0, 0.0) if phases[0] in resting else (first.vx,
                                                        first.vy)
    vx2, vy2 = (0.0, 0.0) if phases[1] in resting else (second.vx,
                                                        second.vy)
    cx, cy = second.x - first.x, second.y - first.y
    bx, by = vx2 - vx1, vy2 - vy1
    ax, ay = 0.5 * (ax2 - ax1), 0.5 * (ay2 - ay1)
    reach = 2.0 * radius
    gap = cx * cx + cy * cy - reach * reach
    if gap <= 2.0 * reach * _TOUCH:
      return None
    coefficients = [ax * ax + ay * ay, 2.0 * (ax * bx + ay * by),
                    bx * bx + by * by + 2.0 * (ax * cx + ay * cy),
                    2.0 * (bx * cx + by * cy), gap]
    return _firstQuarticRoot(coefficients, span)

  def advanced(self, balls: tuple[Ball, ...],
               seconds: float) -> tuple[Ball, ...]:
    """The 'advanced' method returns 'balls' as they are 'seconds'
    later: on the cloth exactly, phase to phase, until one reaches a
    cushion or another ball; through the hits step by step; on the
    cloth again once all are clear."""
    return self.played(balls, seconds)[0]

  def played(self, balls: tuple[Ball, ...],
             seconds: float) -> tuple[tuple[Ball, ...], tuple]:
    """The 'played' method returns 'balls' as 'advanced' does, and the
    contacts that began meanwhile, in the order they began, each a
    'Touch' once: one going on as the time begins is not counted
    again, and contacts beginning at the same moment are all
    counted. A contact going on as the time ends has its last step cut
    short to end there, so the balls played in short pieces differ by a
    hair from the balls played at once, which later hits make more of;
    'Recorder' plays a shot at once."""
    balls, passed, log = tuple(balls), 0.0, []
    while passed < seconds:
      left = seconds - passed
      if self.inContact(balls):
        balls, used, touches = self.collided(balls, left, False)
      else:
        glide = self.glided(balls, left)
        balls, used, touches = glide.after, glide.span, glide.touches
      passed += used
      log.extend(touches)
    return balls, tuple(log)

  def glided(self, balls: tuple[Ball, ...], most: float) -> Glide:
    """The 'glided' method returns the 'Glide' of 'balls', touching
    nothing, over the cloth until a ball's phase ends, a ball reaches a
    cushion, or two meet, or for 'most' seconds if none does first."""
    cloth, radius = self.cloth, self.table.radius
    phases = tuple(cloth.phaseOf(ball, radius) for ball in balls)
    ends = [cloth.phaseTime(ball, phase, radius)
            for ball, phase in zip(balls, phases)]
    span = min([most, *ends])
    event = self._nextEvent(balls, phases, span)
    if event is not None:
      span = event
    moved = []
    for ball, phase, end in zip(balls, phases, ends):
      after = cloth.moved(ball, phase, span, radius)
      if event is None and end <= span:
        after = cloth.settled(after, phase, radius)
        if phase == 'rolling':
          after = cloth.rolledBack(ball, after, radius)
      moved.append(after)
    after = tuple(moved)
    touches = () if event is None else tuple(sorted(self.touchesOf(after)))
    return Glide(phases, span, after, touches)

  def collided(self, balls: tuple[Ball, ...], most: float,
               whole: bool) -> tuple[tuple[Ball, ...], float, tuple]:
    """The 'collided' method follows 'balls' through their hits, step
    by step, until all are clear, or for 'most' seconds; the balls
    touching nothing move on exactly meanwhile. Unless the steps are
    'whole', the last is cut short to end at 'most'; whole, it may end
    up to a step past it. Returns the balls, how long it took, and the
    contacts that began meanwhile, in order."""
    return self.hitsOf(balls).run(most, whole)

  def hitsOf(self, balls: tuple[Ball, ...]) -> Hits:
    """The 'hitsOf' method returns 'Hits' following 'balls', touching
    something, through their hits, to be run on as long as asked: the
    steps come out the same however the runs cut them."""
    return Hits(self, balls)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _nextEvent(self, balls: tuple[Ball, ...], phases: tuple,
                 span: float) -> float | None:
    """Returns how long until the first ball reaches a cushion or meets
    another within 'span'; 'None' if none does."""
    first = None
    for ball, phase in zip(balls, phases):
      time = self.hitTime(ball, phase, span)
      if time is not None:
        first = time if first is None else min(first, time)
    for i, one in enumerate(balls):
      for other in balls[i + 1:]:
        time = self.meetTime(one, other, span)
        if time is not None:
          first = time if first is None else min(first, time)
    return first

  def _given(self, x: float, y: float) -> float:
    """Returns how far the cushion a ball with its middle at 'x', 'y'
    presses hardest gives."""
    radius, drop = self.table.radius, self.table.radius - self.table.nose
    out = -math.inf
    for away, _, _, _ in self.contactSides(x, y):
      out = max(out, radius - math.sqrt(away * away + drop * drop))
    return out

  def _fastestOf(self, balls: tuple[Ball, ...]) -> float:
    """Returns how fast, in mm/s, any of 'balls' may move while they
    are followed through their hits: no faster than with all their
    energy, stored in the cushions and between them too, in one ball;
    with room for the steps' small error, and for a roll's end, when the
    felt pushes a ball back out of nothing."""
    energy = 1e6 * self.energyOf(balls)
    back = math.sqrt(2.0 * self.cloth.rollingDecay() * self.cloth.rollBack)
    return 1.05 * math.sqrt(2.0 * energy) + back + 1.0

  def _touchesAmong(self, state: list, awake: list,
                    names: list) -> tuple[set, list, list]:
    """Returns the contacts among the balls 'awake' of 'state' now, each
    a 'Touch' as 'touchesOf' has them, the pairs of balls touching, and
    the balls touching a cushion, as 'meeting' and 'touching' tell."""
    table = self.table
    radius, drop = table.radius, table.radius - table.nose
    width, length = table.width, table.length
    touches, pairs, cushioned = set(), [], []
    for k in awake:
      row = state[k]
      x, y, vx, vy = row[1], row[2], row[4], row[5]
      sides = ((x, 1.0, 0.0), (width - x, -1.0, 0.0), (y, 0.0, 1.0),
               (length - y, 0.0, -1.0))
      found = False
      for side, (away, ix, iy) in enumerate(sides):
        if away >= radius + _TOUCH:
          continue
        given = radius - math.sqrt(away * away + drop * drop)
        if given > 0.0 or (given > -_TOUCH and ix * vx + iy * vy < 0.0):
          touches.add(Touch('cushion', names[k], CUSHIONS[side]))
          found = True
      if found:
        cushioned.append(k)
    for a, i in enumerate(awake):
      one = state[i]
      for j in awake[a + 1:]:
        other = state[j]
        dx, dy = other[1] - one[1], other[2] - one[2]
        pressed = 2.0 * radius - math.hypot(dx, dy)
        if pressed <= -_TOUCH:
          continue
        if pressed > 0.0 or dx * (other[4] - one[4]) + dy * (
            other[5] - one[5]) < 0.0:
          touches.add(Touch('ball', names[i], names[j]))
          pairs.append((i, j))
    return touches, pairs, cushioned

  def _cushionPush(self, row: list, step: float, fixed: _Fixed) -> float:
    """Pushes the ball in 'row' off each cushion it presses for 'step',
    as Mathavan et al. (2010) have a cushion push, the user's squaring
    past where they hold ('Cushion'); returns the cushions' push up on
    it, a kilogram, below nought pressing down."""
    lift = 0.0
    for away, ix, iy in self.sidesOf(row[1], row[2]):
      lift = _nosePushed(row, away, ix, iy, step, fixed, lift)
    return lift

  def _ballPush(self, one: list, other: list, step: float,
                fixed: _Fixed) -> tuple[float, float]:
    """Pushes the balls in rows 'one' and 'other' apart for 'step', with
    friction where they touch; returns the push up on each, a kilogram,
    below nought pressing down."""
    radius, inertia = fixed.radius, fixed.inertia
    dx, dy = other[1] - one[1], other[2] - one[2]
    apart = math.hypot(dx, dy)
    if apart <= 0.0:
      return 0.0, 0.0
    nx, ny = dx / apart, dy / apart
    given = 2.0 * radius - apart
    giving = -((other[4] - one[4]) * nx + (other[5] - one[5]) * ny)
    push = 0.0
    if given > 0.0:
      both = fixed.swingSquared * given + fixed.swingDamping * giving
      push = max(0.5 * both, 0.0)
    one[4] -= push * nx * step
    one[5] -= push * ny * step
    other[4] += push * nx * step
    other[5] += push * ny * step
    if push <= 0.0:
      return 0.0, 0.0
    #  Where they touch: 'one' at a radius along n, 'other' against it.
    rx, ry = radius * nx, radius * ny
    c1x = one[4] - one[8] * ry
    c1y = one[5] + one[8] * rx
    c1z = one[6] * ry - one[7] * rx
    c2x = other[4] + other[8] * ry
    c2y = other[5] - other[8] * rx
    c2z = -other[6] * ry + other[7] * rx
    sx, sy, sz = c1x - c2x, c1y - c2y, c1z - c2z
    normal = sx * nx + sy * ny
    sx, sy = sx - normal * nx, sy - normal * ny
    slip = math.sqrt(sx * sx + sy * sy + sz * sz)
    if slip <= 0.0:
      return 0.0, 0.0
    fall = math.exp(-abs(slip) / fixed.slipScale)
    friction = fixed.fastFriction + fixed.frictionSpread * fall
    size = min(friction * push * step, slip / 7.0)
    jx, jy, jz = -sx / slip * size, -sy / slip * size, -sz / slip * size
    one[4] += jx
    one[5] += jy
    other[4] -= jx
    other[5] -= jy
    one[6] += ry * jz / inertia
    one[7] -= rx * jz / inertia
    one[8] += (rx * jy - ry * jx) / inertia
    other[6] += ry * jz / inertia
    other[7] -= rx * jz / inertia
    other[8] += (rx * jy - ry * jx) / inertia
    return jz / step, -jz / step

  def _slate(self, row: list, lift: float, step: float,
             fixed: _Fixed) -> None:
    """Moves the ball in 'row', touching a cushion or ball, on for
    'step' on the slate: friction against the slip under it, bearing its
    weight less 'lift'; its side spin dying the faster for the load;
    turned as it spins. Set going faster than the felt's push back sets
    a ball rolling back, 'settleSpeed', it is hit again, and will be
    pushed back as its next roll ends; nudged no faster, it is still
    coming to rest, pushed back once only: else a ball rolled back
    into a cushion bounced off it, rolled back into it, and so for ever,
    the felt's push given anew each time out of nothing."""
    radius, inertia, gravity = fixed.radius, fixed.inertia, fixed.gravity
    bearing = max(gravity - lift, 0.0)
    sx, sy = row[4] - radius * row[7], row[5] + radius * row[6]
    slip = math.hypot(sx, sy)
    if slip > 0.0:
      size = min(fixed.sliding * bearing * step, slip / 3.5) / slip
      jx, jy = -sx * size, -sy * size
      row[4] += jx
      row[5] += jy
      row[6] += radius * jy / inertia
      row[7] -= radius * jx / inertia
    spin = fixed.spinDecay * bearing / gravity * step
    row[8] = math.copysign(max(abs(row[8]) - spin, 0.0), row[8])
    row[1] += row[4] * step
    row[2] += row[5] * step
    row[3] = turned(row[3], row[6] * step, row[7] * step, row[8] * step)
    if math.sqrt(row[4] * row[4] + row[5] * row[5]) > fixed.settleSpeed:
      row[9] = False


class Hits:
  """
  Hits follows balls through their hits, step by step, for its 'motion':
  made of the balls as a contact begins ('Motion.hitsOf'), 'run' steps
  them on for so long, as often as asked, until all are clear, 'over';
  'balls' are the balls now. The steps are whole and the same however
  the runs cut them, so a shot sampled at any rate comes out as played
  at once, to the last digit.

  A ball touching nothing moves on exactly, as the cloth has it. One
  that cannot touch anything for a while sleeps meanwhile, untouched,
  and is moved on exactly, at once, when it wakes: it cannot reach a
  cushion before its phase on the cloth would have it there, nor
  another ball sooner than the two could close the gap between them at
  the most any ball can move, all the energy there is in one ball
  ('Motion._fastestOf'). A ball asked for while it sleeps is reckoned
  from where it fell asleep, and sleeps on.
  """

  __slots__ = ('motion', 'fixed', 'state', 'names', 'fastest', 'going',
               'asleep', 'used', 'over', 'compiled')

  def __init__(self, motion: Motion, balls: tuple[Ball, ...],
               compiled: bool = True) -> None:
    self.compiled = True if compiled else False
    self.motion = motion
    self.fixed = _fixedOf(motion)
    self.state = [list(ball) for ball in balls]
    self.names = [ball.name for ball in balls]
    self.fastest = motion._fastestOf(balls)
    self.going = motion.touchesOf(balls)
    self.asleep = {}
    self.used = 0.0
    self.over = False
    touched = {name for touch in self.going for name in (touch.first,
                                                         touch.second)}
    for k, name in enumerate(self.names):
      if name not in touched:
        self._doze(k, 0.0)

  def balls(self, ) -> tuple[Ball, ...]:
    """The 'balls' method returns the balls now: those asleep reckoned
    from where they fell asleep, left asleep."""
    cloth, radius = self.motion.cloth, self.motion.table.radius
    out = []
    for k, row in enumerate(self.state):
      if k in self.asleep:
        ball, when, _ = self.asleep[k]
        out.append(cloth.advanced(ball, self.used - when, radius))
      else:
        out.append(Ball(*row))
    return tuple(out)

  def run(self, seconds: float,
          whole: bool) -> tuple[tuple[Ball, ...], float, tuple]:
    """The 'run' method steps the balls on through their hits for
    'seconds', or until all are clear, 'over'; unless the steps are
    'whole', the last is cut short to end at 'seconds'; whole, it may
    end up to a step past it. Returns the balls, how long it took, and
    the contacts that began meanwhile, in order."""
    motion, fixed = self.motion, self.fixed
    cloth, radius = motion.cloth, fixed.radius
    state, log, begun = self.state, [], self.used
    while not self.over and self.used - begun < seconds:
      used = self.used
      for k in [k for k, slept in self.asleep.items() if slept[2] <= used]:
        self._wake(k)
      awake = [k for k in range(len(state)) if k not in self.asleep]
      if self.compiled:
        #  The kernel decides each step itself, wherever a run is cut,
        #  so a shot sampled at any rate comes out the same.
        if self._compiledRun(awake, begun, seconds, whole, log):
          continue
        if self.over:
          break
      touches, pairs, cushioned = motion._touchesAmong(state, awake,
                                                       self.names)
      log.extend(sorted(touches - self.going))
      self.going = touches
      if not pairs and not cushioned:
        self.over = True
        break
      fine = fixed.caromStep if pairs else fixed.cushionStep
      step = fine if whole else min(fine, seconds - (used - begun))
      lifts = dict.fromkeys(awake, 0.0)
      for k in cushioned:
        lifts[k] += motion._cushionPush(state[k], step, fixed)
      for i, j in pairs:
        lift, other = motion._ballPush(state[i], state[j], step, fixed)
        lifts[i] += lift
        lifts[j] += other
      pushed = set(cushioned) | {k for pair in pairs for k in pair}
      self.used = used + step
      for k in awake:
        row = state[k]
        if k in pushed:
          motion._slate(row, lifts[k], step, fixed)
          continue
        state[k] = list(cloth.advanced(Ball(*row), step, radius))
        self._doze(k, self.used)
    return self.balls(), self.used - begun, tuple(log)

  def _compiledRun(self, awake: list, begun: float, seconds: float,
                   whole: bool, log: list) -> int:
    """Steps the balls 'awake', each touching something, through their
    hits in the compiled kernel ('_hits_kernels.hitsRun'), the run begun
    at 'begun' going on 'seconds' at most, handing back once all are
    clear, one is free, or a ball asleep is due to wake; logs the
    contacts beginning meanwhile, in order. Returns how many steps it
    took, nought if none."""
    import warp as wp

    from . import _hits_kernels as kernels
    wp.init()
    state, names = self.state, self.names
    rows = [state[k] for k in awake]
    going = []
    for a, k in enumerate(awake):
      bits = 0
      for touch in self.going:
        if touch.kind == 'cushion' and touch.first == names[k]:
          bits |= 1 << CUSHIONS.index(touch.second)
        elif touch.kind == 'ball' and names[k] in (touch.first,
                                                   touch.second):
          other = touch.second if touch.first == names[k] else touch.first
          b = next((b for b, j in enumerate(awake) if names[j] == other),
                   None)
          if b is not None:
            bits |= 1 << (4 + b)
      going.append(bits)
    wake = min((slept[2] for slept in self.asleep.values()),
               default=math.inf)
    arrays = {
      'place': (wp.vec2d, [(row[1], row[2]) for row in rows]),
      'turn': (wp.vec4d, [tuple(row[3]) for row in rows]),
      'speed': (wp.vec2d, [(row[4], row[5]) for row in rows]),
      'spin': (wp.vec3d, [(row[6], row[7], row[8]) for row in rows]),
      'settling': (wp.int32, [1 if row[9] else 0 for row in rows]),
      'going': (wp.int32, going)}
    made = {name: wp.array(values, dtype, None, None, None, None, 'cpu')
            for name, (dtype, values) in arrays.items()}
    events = wp.zeros(256, wp.vec4i, 'cpu')
    out = wp.zeros(4 + len(rows), wp.float64, 'cpu')
    wp.launch(kernels.hitsRun, 1,
              [_rulesOf(self.motion), made['place'], made['turn'],
               made['speed'], made['spin'], made['settling'],
               made['going'], float(begun), float(self.used),
               float(seconds), 1 if whole else 0, float(min(wake, 1e9)),
               100000000, events, out], [], [], [], 'cpu')
    used, steps, clear, logged = (float(value)
                                  for value in out.numpy()[:4])
    got = {name: array.numpy() for name, array in made.items()}
    for a, k in enumerate(awake):
      row = state[k]
      row[1], row[2] = (float(value) for value in got['place'][a])
      row[3] = tuple(float(value) for value in got['turn'][a])
      row[4], row[5] = (float(value) for value in got['speed'][a])
      row[6], row[7], row[8] = (float(value) for value in got['spin'][a])
      row[9] = bool(got['settling'][a])
    groups = {}
    for step, kind, first, second in events.numpy()[:int(logged)]:
      one = names[awake[first]]
      if kind == 0:
        touch = Touch('cushion', one, CUSHIONS[second])
      else:
        touch = Touch('ball', one, names[awake[second]])
      groups.setdefault(int(step), []).append(touch)
    for step in sorted(groups):
      log.extend(sorted(groups[step]))
    touches = set()
    for a, k in enumerate(awake):
      bits = int(got['going'][a])
      for side in range(4):
        if bits >> side & 1:
          touches.add(Touch('cushion', names[k], CUSHIONS[side]))
      for b, j in enumerate(awake):
        if j > k and bits >> (4 + b) & 1:
          touches.add(Touch('ball', names[k], names[j]))
    self.going = touches
    self.used = used
    if clear:
      self.over = True
    return int(steps)

  def _doze(self, k: int, now: float) -> None:
    """Puts ball 'k', touching nothing 'now', to sleep until it might
    touch something, if that is a while away: until its phase on the
    cloth ends, or it reaches a cushion's nose, or another ball could
    reach it, both at 'fastest'. A ball at a cushion stays awake."""
    motion, fastest = self.motion, self.fastest
    cloth, radius = motion.cloth, motion.table.radius
    ball = Ball(*self.state[k])
    reach = motion.reach()
    for away, _, _ in motion.sidesOf(ball.x, ball.y):
      if away - reach <= _TOUCH:
        return
    phase = cloth.phaseOf(ball, radius)
    until = cloth.phaseTime(ball, phase, radius)
    hit = motion.hitTime(ball, phase, until)
    if hit is not None:
      until = hit
    until += now
    for j, row in enumerate(self.state):
      if j == k:
        continue
      x, y, when = row[1], row[2], now
      if j in self.asleep:
        other, when, _ = self.asleep[j]
        x, y = other.x, other.y
      gap = math.hypot(ball.x - x, ball.y - y) - 2.0 * radius
      until = min(until, (gap + fastest * (now + when)) / (2.0 * fastest))
    if until - now > _DOZE:
      self.asleep[k] = (ball, now, until)

  def _wake(self, k: int) -> None:
    """Wakes ball 'k', moving it on exactly from where it fell asleep to
    now."""
    ball, when, _ = self.asleep.pop(k)
    self.state[k] = list(self.motion.cloth.advanced(
      ball, self.used - when, self.motion.table.radius))


def _nosePushed(row: list, away: float, ix: float, iy: float,
                step: float, fixed: _Fixed, lift: float) -> float:
  """Pushes the ball in 'row' off a cushion's nose 'away' from its middle
  across the cloth, 'ix', 'iy' the way from the nose to the ball, for
  'step': the nose's spring and damper along the line from it to the
  ball's middle as the ball meets it, one Coulomb friction 'grip'
  against the slip at the nose, whichever way (Mathavan et al. 2010),
  and, past where they hold, the user's squaring at the ball's middle;
  returns 'lift' with the nose's push up on it added. The compiled
  'sidePushed' does the same, sum for sum."""
  radius = fixed.radius
  if away >= radius:
    return lift
  apart = math.sqrt(away * away + fixed.drop * fixed.drop)
  given = radius - apart
  if given <= 0.0:
    return lift
  ex, ey, ez = ix * fixed.across, iy * fixed.across, fixed.down
  giving = -away * (ix * row[4] + iy * row[5]) / apart
  spring = fixed.stiffness * given ** fixed.stiffening
  push = max(spring + fixed.damping * giving, 0.0)
  row[4] += push * ex * step
  row[5] += push * ey * step
  lift += push * ez
  if push <= 0.0:
    return lift
  rx, ry, rz = -radius * ex, -radius * ey, -radius * ez
  wx, wy, wz = row[6], row[7], row[8]
  cx = row[4] + wy * rz - wz * ry
  cy = row[5] + wz * rx - wx * rz
  cz = wx * ry - wy * rx
  normal = cx * ex + cy * ey + cz * ez
  sx, sy, sz = cx - normal * ex, cy - normal * ey, cz - normal * ez
  slip = math.sqrt(sx * sx + sy * sy + sz * sz)
  if slip > 0.0:
    size = min(fixed.grip * push * step, slip / 3.5)
    jx, jy, jz = -sx / slip * size, -sy / slip * size, -sz / slip * size
    row[4] += jx
    row[5] += jy
    lift += jz / step
    inertia = fixed.inertia
    row[6] += (ry * jz - rz * jy) / inertia
    row[7] += (rz * jx - rx * jz) / inertia
    row[8] += (rx * jy - ry * jx) / inertia
  if fixed.squaring <= 0.0:
    return lift
  ax, ay = -iy, ix
  along = row[4] * ax + row[5] * ay
  stored = fixed.storingShare * given ** fixed.storing
  comes = math.sqrt(giving * giving + 2.0 * stored) / fixed.across
  over = comes - fixed.squaringFrom
  if over <= 0.0 or along == 0.0:
    return lift
  hard = over * over / (over + fixed.squaringOnset)
  angle = math.atan2(abs(along), comes)
  near = softplus((fixed.squaringBelow - angle) / fixed.squaringWidth)
  share = fixed.squaring * hard * near / fixed.squaringNorm
  size = min(share * push * step, abs(along))
  held = -size if along > 0.0 else size
  row[4] += held * ax
  row[5] += held * ay
  return lift


class _Fixed(NamedTuple):
  """
  _Fixed is what the steps through hits use over and over, worked out
  once for a 'Motion' ('_fixedOf'), each as the cushion, the carom and
  the cloth work it out, so the steps come out the same to the last
  digit: the ball's 'radius', how far its middle is below a cushion's
  nose, 'drop', and its moment of inertia a kilogram, 'inertia'; the
  cushion's 'stiffness', 'damping' and 'stiffening', its 'grip', the
  line from the nose to the ball as it meets it ('across' the cloth and
  'down', shares), its stored energy ('storing' the power,
  'storingShare' the factor), and its squaring ('squaring' a kilogram
  per mm/s past 'squaringFrom', 'squaringOnset', 'squaringBelow' and
  'squaringWidth' in radians, 'squaringNorm' the softplus at no
  angle); the
  carom's spring, 'swingSquared', its damper, 'swingDamping', and its
  friction; the cloth's 'sliding' friction, 'gravity' and 'spinDecay';
  the steps; and how fast the felt sets a ball rolling back as its roll
  ends, 'settleSpeed' ('Cloth.rolledBack').
  """

  radius: float
  drop: float
  inertia: float
  stiffness: float
  damping: float
  stiffening: float
  grip: float
  across: float
  down: float
  storing: float
  storingShare: float
  squaring: float
  squaringFrom: float
  squaringOnset: float
  squaringBelow: float
  squaringWidth: float
  squaringNorm: float
  swingSquared: float
  swingDamping: float
  fastFriction: float
  frictionSpread: float
  slipScale: float
  sliding: float
  gravity: float
  spinDecay: float
  cushionStep: float
  caromStep: float
  settleSpeed: float


@functools.lru_cache(maxsize=32)
def _rulesOf(motion: Motion) -> object:
  """Returns the compiled kernel's 'HitRules' for 'motion', from
  '_fixedOf'."""
  from . import _hits_kernels as kernels
  fixed, table = _fixedOf(motion), motion.table
  rules = kernels.HitRules()
  for name in fixed._fields:
    setattr(rules, name, float(getattr(fixed, name)))
  rules.width, rules.length = float(table.width), float(table.length)
  return rules


@functools.lru_cache(maxsize=32)
def _fixedOf(motion: Motion) -> _Fixed:
  """Returns what the steps through hits of 'motion' use over and
  over, worked out once."""
  table, cushion, carom = motion.table, motion.cushion, motion.carom
  cloth, radius = motion.cloth, table.radius
  swing = carom.frequency()
  drop = radius - table.nose
  storing = cushion.stiffening + 1.0
  below = math.radians(cushion.squaringBelow)
  width = math.radians(cushion.squaringWidth)
  return _Fixed(radius, drop, 0.4 * radius * radius,
                cushion.stiffness(), cushion.damping(), cushion.stiffening,
                cushion.grip, math.sqrt(radius * radius - drop * drop)
                / radius, drop / radius, storing,
                cushion.stiffness() / storing, 0.001 * cushion.squaring,
                cushion.squaringFrom, cushion.squaringOnset, below, width,
                softplus(below / width), swing * swing,
                2.0 * carom._ratio() * swing, carom.fastFriction,
                carom.slowFriction - carom.fastFriction, carom.slipScale,
                cloth.sliding, cloth.gravity, cloth.spinDecay(radius),
                cushion.step, carom.step,
                math.sqrt(2.0 * max(cloth.rollingDecay(), 0.0)
                          * max(cloth.rollBack, 0.0)))


@functools.lru_cache(maxsize=32)
def _jawsOf(motion: Motion) -> tuple:
  """Returns the jaws of 'motion's pockets, each (x, y, cushion), the
  slots' ends on the noses' line; none without pockets."""
  pockets = motion.pockets
  if pockets is None:
    return ()
  width, length = motion.table.width, motion.table.length
  corner, half = pockets.corner, pockets.half
  out = []
  for side, x in ((0, 0.0), (1, width)):
    for y in (corner, 0.5 * length - half, 0.5 * length + half,
              length - corner):
      out.append((x, y, side))
  for side, y in ((2, 0.0), (3, length)):
    for x in (corner, width - corner):
      out.append((x, y, side))
  return tuple(out)


def _pointTime(ball: Ball, ax: float, ay: float, x: float, y: float,
               reach: float, span: float) -> float | None:
  """Returns how long until 'ball', set off as it is and speeding up
  'ax', 'ay', comes within 'reach' of 'x', 'y' across the cloth, if it
  does within 'span'; 'None' if it does not, or is that near already.
  Its path is quadratic, so the square of the distance is a quartic in
  the time."""
  px, py = ball.x - x, ball.y - y
  gap = px * px + py * py - reach * reach
  if gap <= 2.0 * reach * _TOUCH:
    return None
  bx, by, hx, hy = ball.vx, ball.vy, 0.5 * ax, 0.5 * ay
  coefficients = [hx * hx + hy * hy, 2.0 * (hx * bx + hy * by),
                  bx * bx + by * by + 2.0 * (hx * px + hy * py),
                  2.0 * (bx * px + by * py), gap]
  return _firstQuarticRoot(coefficients, span)


def _firstRoot(a: float, b: float, c: float) -> float | None:
  """Returns the first time after nought that 'a' t² + 'b' t + 'c'
  falls to nought from 'c' above it; 'None' if it never does."""
  if abs(a) < 1e-12:
    return -c / b if b < 0.0 else None
  disc = b * b - 4.0 * a * c
  if disc < 0.0:
    return None
  root = math.sqrt(disc)
  q = -0.5 * (b + math.copysign(root, b))
  times = [t for t in (q / a, c / q if q != 0.0 else -1.0) if t > 0.0]
  return min(times) if times else None


def _firstQuarticRoot(coefficients: list, span: float) -> float | None:
  """Returns the first time in nought to 'span' where the polynomial of
  'coefficients', highest first, its value at nought above nought,
  falls to nought; 'None' if it does not."""
  values = [float(c) for c in coefficients]
  scale = max(abs(c) for c in values)
  while values and abs(values[0]) <= 1e-15 * scale:
    values.pop(0)
  if len(values) < 2:
    return None
  slopes = numpy.polyder(values)
  found = []
  for root in numpy.roots(values):
    if abs(root.imag) > 1e-6 * (1.0 + abs(root.real)):
      continue
    time = float(root.real)
    for _ in range(3):
      slope = float(numpy.polyval(slopes, time))
      if slope == 0.0:
        break
      time -= float(numpy.polyval(values, time)) / slope
    if 0.0 < time <= span and float(numpy.polyval(slopes, time)) <= 0.0:
      found.append(time)
  return min(found) if found else None
