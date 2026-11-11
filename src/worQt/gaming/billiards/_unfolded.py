"""
Unfolded is the table unfolded, every cushion a mirror, so a shot runs
on into mirrored copies of the table; English an arc across them, to
help choose how much; and, where the arc meets a ball, a fan of where
the two may go from there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import TYPE_CHECKING, NamedTuple

import numpy

from ._carom_table import Ball, CaromTable, isParked
from ._cloth import Cloth
from ._cue import Cue
from ._motion import Motion

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._recorder import Recording

Place = tuple[float, float]
Path = tuple[Place, ...]
#  A ball along its way: how fast it goes, and how fast its spin alone
#  would roll it the same way, in mm/s; the same when it rolls, less
#  when it slides ahead of its spin, below nought drawing.
State = tuple[float, float]
#  A ball's way as the engine played it, unfolded: at each sample its
#  place on the table unfolded, 'x' and 'y', and its 'State' then.
Way = tuple[tuple[float, float, float, float], ...]


class Crossing(NamedTuple):
  """
  Crossing is where an arc crosses a cushion's line on the table
  unfolded, 'x' across and 'y' along: of a long cushion, 'long', or of a
  short one.
  """

  x: float
  y: float
  long: bool


class Hit(NamedTuple):
  """
  Hit is where the cue ball's arc first meets a ball on the table
  unfolded: the cue ball's middle then, 'x' and 'y'; the way it comes,
  'dx' and 'dy', of length one; the ball met, 'name', its image's middle
  'bx' and 'by'; how far the cue ball has gone, 'travelled', in mm; how
  far left of its way the ball's middle lies, 'offset', in mm, nought
  full, two radii a graze; and how many of the arc's points come before
  it, 'index'.
  """

  x: float
  y: float
  dx: float
  dy: float
  name: str
  bx: float
  by: float
  travelled: float
  offset: float
  index: int


class Fan(NamedTuple):
  """
  Fan is where the balls may go after a hit, three ways each: the aim
  off one standard deviation to the one side, as aimed, and off one to
  the other; each as many points, so the ways between are had by
  drawing between them. 'cue' is the cue ball's, a miss going on past
  the ball; 'struck' the ball met's, a miss its thinnest cut.
  """

  cue: tuple[Path, Path, Path]
  struck: tuple[Path, Path, Path]


class Run(NamedTuple):
  """
  Run is a shot as the engine played it, every ball's way unfolded:
  'rate' samples a second; 'cue', the ball struck; 'ways', each ball's
  name and its 'Way', a sample each, the same count for all; and
  'meets', the times the cue ball met each other ball first, and which,
  in order.
  """

  rate: float
  cue: str
  ways: tuple[tuple[str, Way], ...]
  meets: tuple[tuple[float, str], ...]

  def wayOf(self, name: str) -> Way:
    """The 'wayOf' method returns the way of the ball 'name'."""
    return dict(self.ways)[name]

  def moved(self, name: str) -> bool:
    """The 'moved' method tells whether the ball 'name' moved."""
    return any(speed > 0.0 for _, _, speed, _ in self.wayOf(name))


class Unfolded(NamedTuple):
  """
  Unfolded is the table unfolded, as the user pictures a shot, in mm:
  meeting a cushion is going on into a mirrored copy of the table, so a
  shot is a line on through the copies, each showing the balls mirrored
  as it is. A copy is where a ball's middle can be, the cloth less
  'reach' at each side: a ball touching a cushion has its middle on the
  copy's edge. Copy (0, 0) is the table itself; copy 'i' across and 'j'
  along is mirrored across if 'i' is odd and along if 'j' is; the map
  shows 'across' copies either side across the table and 'along' either
  side along it.

  The cue ball's way (the user: English "a soft curve to either side
  which we then straighten between the cushions") runs straight on the
  cloth, as the shot is sent, and turns only at the cushions' lines, as
  the engine's cushions turn a ball ('kicked'): the part of its way
  across the line kept as 'flatten' of it (a mirror at one), less the
  faster it comes ('flattenSpeed' a m/s) and the more it rolls
  ('flattenRoll' times its roll's share: draw comes off steeper), and
  its English pushing it along the cushion to its right, right English,
  as 'sidePush' times the side times the part across. Mirrored copies
  turn the push round. Fitted 2026-11-10 to 135 single balls the engine
  played (1.5 to 4.5 m/s, 20 to 80 degrees, draw to follow, left to
  right English): the first three cushions met within 32 mm in half the
  shots, 410 in nine of ten; a mirror was 91 and 1090. It is followed
  'step' mm at a time, until it leaves the map or stops.

  Where the arc first meets a ball, 'hitOf', the shot is a fan, 'fanOf':
  the aim is off by 'spread' degrees as one standard deviation, so the
  ball is met further off the middle or nearer by as much times the way
  come; the fan holds the ways as aimed and one standard deviation off
  either side, the ways between drawn between them. Each
  hit, the balls frictionless and alike, sends the ball met along the
  line between the middles, and the cue ball off square to it, curving
  back by its roll until it rolls, as Alciatore has it: (5/7) of the way
  square to the line plus (2/7) of its roll's way, the roll its share of
  rolling as it meets the ball; a miss goes on past. The cue ball's
  ways turn at the cushions as the arc does.

  How far a ball rolls, table by table (the user: a cushion met with
  draw turns the draw to follow, which speeds the ball up after): its
  'State', how fast it goes and how fast its spin alone would roll it,
  starts as struck ('stateOf'). On each table it slides as 'Cloth' has a
  ball slide, its speed and its spin drawing together until it rolls,
  then rolls on, slowing as the cloth slows a rolling ball times
  'slowing' ('rolledOn'). At each cushion's line ('bounced') the part of
  its speed across the line is given back as 'bounce' of it; its spin
  is turned round with the way, so the part of it across the line
  changes sign: draw met square on turns to follow, follow to draw; and
  the cushion keeps 'spinKept' of it and adds 'spinReset' times the speed
  of its own, as much as the ball met it square on. 'stateAfter' follows
  a ball along a way. The arc and the fans' ways end where a ball
  stops; after a hit, the ball met leaves as fast as it is pushed,
  without spin, the cue ball rolling as Alciatore has it.

  Fitted 2026-11-10 to single balls the engine played (100 shots, 0.8
  to 4 m/s, 15 to 90 degrees, struck from heavy draw to full follow):
  the distances within about 5 % (the median), with the cushions of
  the time (two grips, along 0.47 and up and down 0.14); not yet
  refitted to Mathavan et al.'s cushion (2026-11-11).
  """

  #  How many points each of a fan's ways has.
  __ray_points__ = 120

  table: CaromTable = CaromTable()
  across: int = 2
  along: int = 1
  step: float = 10.0
  spread: float = 0.25
  #  Fitted 2026-11-10 to the engine's single balls (see above).
  bounce: float = 0.9
  spinKept: float = 0.4
  spinReset: float = 0.0
  slowing: float = 0.97
  flatten: float = 1.0
  flattenSpeed: float = 0.02
  flattenRoll: float = -0.2
  sidePush: float = 1.4

  def reach(self, ) -> float:
    """The 'reach' method returns how far a ball's middle is from a
    cushion's nose, across the cloth, as it touches it."""
    return _reachOf(self.table)

  def tile(self, ) -> tuple[float, float]:
    """The 'tile' method returns how large a copy is, across and along:
    the cloth less 'reach' at each side."""
    reach = self.reach()
    return self.table.width - 2.0 * reach, self.table.length - 2.0 * reach

  def copies(self, ) -> tuple[tuple[int, int], ...]:
    """The 'copies' method returns the copies the map shows, each its
    'i' across and 'j' along, the table itself (0, 0)."""
    return tuple((i, j) for j in range(-self.along, self.along + 1)
                 for i in range(-self.across, self.across + 1))

  def corners(self, i: int, j: int) -> tuple[float, float, float, float]:
    """The 'corners' method returns the copy 'i' across and 'j' along:
    its least 'x' and 'y' and its most."""
    reach = self.reach()
    across, along = self.tile()
    return (reach + i * across, reach + j * along,
            reach + (i + 1) * across, reach + (j + 1) * along)

  def bounds(self, ) -> tuple[float, float, float, float]:
    """The 'bounds' method returns the map: its least 'x' and 'y' and
    its most."""
    low = self.corners(-self.across, -self.along)
    high = self.corners(self.across, self.along)
    return low[0], low[1], high[2], high[3]

  def imageOf(self, x: float, y: float, i: int, j: int) -> Place:
    """The 'imageOf' method returns where the place 'x' across and 'y'
    along the table shows in the copy 'i' across and 'j' along."""
    reach = self.reach()
    across, along = self.tile()
    u, v = x - reach, y - reach
    if i % 2:
      u = across - u
    if j % 2:
      v = along - v
    return reach + i * across + u, reach + j * along + v

  def kicked(self, hx: float, hy: float, long: bool, state: State,
             side: float, mirrored: bool) -> Place:
    """The 'kicked' method returns the way 'hx', 'hy' on the table
    unfolded as a ball in 'state', struck 'side' to the right, leaves a
    cushion's line, a long cushion's if 'long': the part across kept as
    'flatten' of it, less the faster and the more it rolls, never more
    than a mirror keeps; the English pushing it along the cushion to its
    right, right English, by 'sidePush' times the side times the part
    across, the other way in a 'mirrored' copy."""
    speed, spin = state
    roll = spin / speed if speed > 0.0 else 0.0
    keep = (self.flatten + self.flattenSpeed * speed / 1000.0
            + self.flattenRoll * roll)
    keep = min(1.0, max(0.2, keep))
    if long:
      across, along, way = hx, hy, -math.copysign(1.0, hx)
    else:
      across, along, way = hy, hx, math.copysign(1.0, hy)
    turn = -1.0 if mirrored else 1.0
    along += turn * self.sidePush * side * abs(across) * way
    across *= keep
    if long:
      return _unit(across, along)
    return _unit(along, across)

  def arcOf(self, x: float, y: float, aimX: float, aimY: float,
            side: float, speed: float,
            state: State = None) -> tuple[Place, ...]:
    """The 'arcOf' method returns the cue ball's way from 'x', 'y'
    along the aim 'aimX', 'aimY', for 'side' at 'speed': the arc
    straight between the cushions' lines (the user's un-spline: the
    ball runs straight on the cloth), straight along the aim to the
    first, turning at each as 'kicked' has it; as points 'step' mm apart
    and at each line; until it leaves the map, the last point past its
    edge; set off in 'state', as 'stateOf' gives it, also where the ball
    stops."""
    low = self.bounds()
    longest = 2.0 * ((low[2] - low[0]) + (low[3] - low[1]))
    return self._bentPath(x, y, aimX, aimY, side, speed, longest, True,
                          state)

  def wayOf(self, recording: Recording, name: str) -> Way:
    """The 'wayOf' method returns the ball 'name' of 'recording' as the
    engine played it, unfolded: at each sample its place on the table
    unfolded, 'x' and 'y', how fast it went and how fast its spin alone
    rolled it its way; from each cushion it met on, the rest of its way
    mirrored onto the next copy, as a shot runs on through them."""
    reach = self.reach()
    width, length = self.table.width, self.table.length
    radius = self.table.radius
    met = [(time, touch.second) for time, touch in recording.touches
           if touch.kind == 'cushion' and touch.first == name]
    index = recording.names.index(name)
    fx, ox, fy, oy = 1.0, 0.0, 1.0, 0.0
    taken, out = 0, []
    for k in range(recording.count()):
      time = k / recording.rate
      while taken < len(met) and met[taken][0] <= time:
        fx, ox, fy, oy = _mirrored((fx, ox, fy, oy), met[taken][1], reach,
                                   width, length)
        taken += 1
      ball = recording.ballsAt(time)[index]
      if isParked(ball.x, ball.y):
        break
      speed = math.hypot(ball.vx, ball.vy)
      spin = 0.0
      if speed > 0.0:
        spin = radius * (ball.wy * ball.vx - ball.wx * ball.vy) / speed
      out.append((fx * ball.x + ox, fy * ball.y + oy, speed, spin))
    return tuple(out)

  def runOf(self, recording: Recording) -> Run:
    """The 'runOf' method returns the shot of 'recording' as a 'Run',
    every ball's way unfolded: the ball struck sets off on the table
    itself; a ball set moving by another goes on from the copy it was
    met in, as an image of it there is what was met; each cushion a
    ball meets mirrors the rest of its own way onto the next copy."""
    reach = self.reach()
    width, length = self.table.width, self.table.length
    radius = self.table.radius
    names = recording.names
    struck = [ball.name for ball in recording.struck()]
    cue = struck[0] if struck else names[0]
    frames = {name: (1.0, 0.0, 1.0, 0.0) for name in names}
    placed = set(struck or names[:1])
    events = list(recording.touches)
    taken, meets, ways = 0, [], {name: [] for name in names}
    for k in range(recording.count()):
      time = k / recording.rate
      while taken < len(events) and events[taken][0] <= time:
        when, touch = events[taken]
        taken += 1
        if touch.kind == 'cushion':
          frames[touch.first] = _mirrored(frames[touch.first],
                                          touch.second, reach, width,
                                          length)
          continue
        if touch.kind != 'ball':
          continue
        one, other = touch.first, touch.second
        if one in placed and other not in placed:
          frames[other] = frames[one]
          placed.add(other)
        elif other in placed and one not in placed:
          frames[one] = frames[other]
          placed.add(one)
        if cue in (one, other):
          met = other if one == cue else one
          if met not in [name for _, name in meets]:
            meets.append((when, met))
      for ball in recording.ballsAt(time):
        fx, ox, fy, oy = frames[ball.name]
        speed = math.hypot(ball.vx, ball.vy)
        spin = 0.0
        if speed > 0.0:
          spin = radius * (ball.wy * ball.vx - ball.wx * ball.vy) / speed
        ways[ball.name].append((fx * ball.x + ox, fy * ball.y + oy,
                                speed, spin))
    return Run(recording.rate, cue,
               tuple((name, tuple(ways[name])) for name in names),
               tuple(meets))

  def stateOf(self, top: float, side: float, speed: float) -> State:
    """The 'stateOf' method returns the cue ball sent at 'speed' mm/s,
    struck 'top' up and 'side' right, as it sets off: how fast it goes,
    and how fast its spin alone would roll it the same way."""
    radius = self.table.radius
    ball = Cue().sent(Ball('cue', 0.0, 0.0), 0.0, 1.0, speed, top, side,
                      radius)
    return ball.vy, -ball.wx * radius

  def rolledOn(self, state: State, distance: float) -> tuple[State, float]:
    """The 'rolledOn' method returns a ball in 'state' after going
    'distance' mm on the cloth, sliding until its spin rolls it, then
    rolling, and how far it went: less than 'distance' if it stopped,
    still, on the way."""
    speed, spin = state
    if speed <= 0.0:
      return (0.0, 0.0), 0.0
    slow, grip = self._slow(), _cloth()[1]
    gone = 0.0
    if abs(speed - spin) > 1e-9:
      sign = 1.0 if speed > spin else -1.0
      span = 2.0 * abs(speed - spin) / (7.0 * grip)
      rolling = speed - sign * grip * span
      if rolling <= 0.0:
        span, rolling = speed / grip, 0.0
      slid = speed * span - 0.5 * sign * grip * span * span
      if distance <= slid:
        time = _timeTo(distance, speed, 0.5 * sign * grip)
        return ((speed - sign * grip * time,
                 spin + 2.5 * sign * grip * time), distance)
      if rolling <= 0.0:
        return (0.0, 0.0), slid
      speed = spin = rolling
      distance -= slid
      gone = slid
    left = speed * speed - 2.0 * slow * distance
    if left <= 0.0:
      return (0.0, 0.0), gone + speed * speed / (2.0 * slow)
    rolling = math.sqrt(left)
    return (rolling, rolling), gone + distance

  def bounced(self, state: State, part: float) -> State:
    """The 'bounced' method returns a ball in 'state' as it leaves a
    cushion it met with 'part' of its way across the cushion's line,
    one square on: that part of its speed given back as 'bounce' of it;
    its spin turned round with the way, so the part across changes sign
    (draw met square on turns to follow), 'spinKept' of it kept, and
    'spinReset' times its speed added, as much as it met it square
    on."""
    speed, spin = state
    across = part * part
    speed *= math.sqrt(1.0 - across + self.bounce * self.bounce * across)
    spin = (self.spinKept * spin * (1.0 - 2.0 * across)
            + self.spinReset * speed * across)
    return speed, spin

  def stateAfter(self, points: Path, state: State) -> State:
    """The 'stateAfter' method returns a ball set off in 'state' once it
    has gone along 'points', rolling on the cloth and bounced at each
    cushion's line it meets, as the step arriving at it meets it; still
    if it stopped on the way."""
    reach = self.reach()
    across, along = self.tile()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
      length = math.hypot(x1 - x0, y1 - y0)
      if length <= 0.0:
        continue
      state, gone = self.rolledOn(state, length)
      if gone < length - 1e-6 or state[0] <= 0.0:
        return 0.0, 0.0
      for start, end, size, part in ((x0, x1, across, (x1 - x0) / length),
                                     (y0, y1, along, (y1 - y0) / length)):
        for _ in range(_linesMet(start, end, reach, size)):
          state = self.bounced(state, part)
    return state

  def crossingsOf(self, points: tuple[Place, ...]) -> tuple[Crossing, ...]:
    """The 'crossingsOf' method returns where the path through 'points'
    crosses a cushion's line, in order: each a cushion the shot meets."""
    reach = self.reach()
    across, along = self.tile()
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
      found = []
      for start, end, size, long in ((x0, x1, across, True),
                                     (y0, y1, along, False)):
        first = math.floor((start - reach) / size)
        last = math.floor((end - reach) / size)
        if first == last:
          continue
        line = reach + max(first, last) * size
        share = (line - start) / (end - start)
        found.append((share, long))
      for share, long in sorted(found):
        out.append(Crossing(x0 + share * (x1 - x0), y0 + share * (y1 - y0),
                            long))
    return tuple(out)

  def imagesOf(self, balls: tuple[Ball, ...],
               skip: str) -> tuple[tuple[str, float, float], ...]:
    """The 'imagesOf' method returns every ball of 'balls' but the one
    named 'skip' as it shows in every copy: its name and where."""
    out = []
    for ball in balls:
      if ball.name == skip:
        continue
      for i, j in self.copies():
        out.append((ball.name, *self.imageOf(ball.x, ball.y, i, j)))
    return tuple(out)

  def hitOf(self, points: Path,
            images: tuple[tuple[str, float, float], ...]) -> Hit | None:
    """The 'hitOf' method returns where the cue ball, its middle along
    'points', first meets one of 'images', two radii from its middle;
    'None' if it meets none, or touches one as it sets off."""
    if len(points) < 2 or not images:
      return None
    reach = 2.0 * self.table.radius
    path = numpy.asarray(points, float)
    places = numpy.asarray([(x, y) for _, x, y in images], float)
    apart = numpy.hypot(path[:, None, 0] - places[None, :, 0],
                        path[:, None, 1] - places[None, :, 1])
    near = (apart < reach).any(1)
    if not near.any():
      return None
    k = int(numpy.argmax(near))
    if k == 0:
      return None
    (x0, y0), (x1, y1) = points[k - 1], points[k]
    sx, sy = x1 - x0, y1 - y0
    best = None
    for m in numpy.nonzero(apart[k] < reach)[0]:
      _, bx, by = images[int(m)]
      share = _entry(x0 - bx, y0 - by, sx, sy, reach)
      if best is None or share < best[0]:
        best = (share, int(m))
    share, m = best
    name, bx, by = images[m]
    length = math.hypot(sx, sy)
    dx, dy = sx / length, sy / length
    x, y = x0 + share * sx, y0 + share * sy
    travelled = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in
                    zip(points[:k - 1], points[1:k])) + share * length
    offset = dx * (by - y) - dy * (bx - x)
    return Hit(x, y, dx, dy, name, bx, by, travelled, offset, k)

  def fanOf(self, hit: Hit, state: State, side: float,
            speed: float) -> Fan:
    """The 'fanOf' method returns where the balls may go after 'hit',
    the cue ball in 'state' as it meets the ball, its 'side' and 'speed'
    as sent: three ways each, the ball met one standard deviation of the
    aim's 'spread' over the way come nearer its middle, as aimed, and
    one further off; each way ending where its ball stops."""
    wide = hit.travelled * math.tan(math.radians(self.spread)) + 1.0
    cue, struck = [], []
    for sign in (-1.0, 0.0, 1.0):
      one, other = self._afterHit(hit, hit.offset + sign * wide, state,
                                  side, speed)
      cue.append(one)
      struck.append(other)
    return Fan(tuple(cue), tuple(struck))

  def rayOf(self, x: float, y: float, aimX: float, aimY: float,
            side: float, speed: float, length: float,
            state: State = None) -> Path:
    """The 'rayOf' method returns the way from 'x', 'y' along 'aimX',
    'aimY' for 'side' at 'speed', as 'arcOf' has it, 'length' mm long or
    until it would turn more than half round, the map's edge no end, as
    '__ray_points__' points evenly apart along it whatever its length:
    the fans' ways, drawn between; set off in 'state', ending where the
    ball stops."""
    path = numpy.asarray(self._bentPath(x, y, aimX, aimY, side, speed,
                                        max(length, 0.0), False, state),
                         float)
    steps = numpy.hypot(*numpy.diff(path, axis=0).T)
    runs = numpy.concatenate(([0.0], numpy.cumsum(steps)))
    wanted = numpy.linspace(0.0, runs[-1], self.__ray_points__)
    xs = numpy.interp(wanted, runs, path[:, 0])
    ys = numpy.interp(wanted, runs, path[:, 1])
    return tuple(zip(xs.tolist(), ys.tolist()))

  def _bentPath(self, x: float, y: float, aimX: float, aimY: float,
                side: float, speed: float, length: float, bounded: bool,
                state: State = None) -> Path:
    """Returns the way 'arcOf' describes, 'length' mm at most, ending
    past the map's edge if 'bounded', and, set off in 'state', where the
    ball stops."""
    hx, hy = _unit(aimX, aimY)
    low = self.bounds()
    moving = (speed, speed) if state is None else state
    points, done, met = [(x, y)], 0.0, 0
    while done < length:
      ahead, crossed = self._toLine(x, y, hx, hy)
      run = min(ahead, length - done)
      stopped = False
      if state is not None:
        state, gone = self.rolledOn(state, run)
        stopped = gone < run - 1e-9 or state[0] <= 0.0
        if stopped:
          run = min(run, gone)
        moving = state
      count = int(run // self.step)
      for k in range(1, count + 1):
        px, py = x + k * self.step * hx, y + k * self.step * hy
        if k * self.step < run:
          points.append((px, py))
          if bounded and not _inside(low, px, py):
            return tuple(points)
      x, y = x + run * hx, y + run * hy
      points.append((x, y))
      done += run
      if stopped or (bounded and not _inside(low, x, y)):
        break
      if run < ahead:
        break
      for part, long in crossed:
        hx, hy = self.kicked(hx, hy, long, moving, side, met % 2 == 1)
        if state is not None:
          state = self.bounced(state, part)
          moving = state
        met += 1
    return tuple(points)

  def _slow(self, ) -> float:
    """Returns how fast a rolling ball slows on the map, in mm/s²: the
    cloth's slowing times 'slowing'."""
    return _cloth()[0] * self.slowing

  def _toLine(self, x: float, y: float, hx: float,
              hy: float) -> tuple[float, tuple[tuple[float, bool], ...]]:
    """Returns how far from 'x', 'y' along 'hx', 'hy' the next
    cushion's line is, past one it may be on, and for each line met
    there, two at a corner, the part of the way across it and whether
    it is a long cushion's, one of constant 'x'."""
    reach = self.reach()
    across, along = self.tile()
    found = []
    for place, way, size, long in ((x, hx, across, True),
                                   (y, hy, along, False)):
      if abs(way) < 1e-12:
        continue
      share = (place - reach) / size
      if way > 0.0:
        line = reach + (math.floor(share + 1e-9) + 1.0) * size
      else:
        line = reach + (math.ceil(share - 1e-9) - 1.0) * size
      found.append(((line - place) / way, way, long))
    if not found:
      return math.inf, ()
    out = min(far for far, _, _ in found)
    return out, tuple((way, long) for far, way, long in found
                      if far <= out + 1e-6)

  def _afterHit(self, hit: Hit, offset: float, state: State, side: float,
                speed: float) -> tuple[Path, Path]:
    """Returns the cue ball's way and the ball met's after 'hit' were
    the ball met 'offset' left of the cue ball's way, the cue ball in
    'state' as it meets it: past it on a miss, the ball met then cut its
    thinnest; each ending where its ball stops."""
    met, spin = state
    share = spin / met if met > 0.0 else 0.0
    reach = 2.0 * self.table.radius
    low = self.bounds()
    length = math.hypot(low[2] - low[0], low[3] - low[1])
    lx, ly = -hit.dy, hit.dx
    thinnest = reach * (1.0 - 1e-9)
    sine = max(-thinnest, min(thinnest, offset)) / reach
    cosine = math.sqrt(1.0 - sine * sine)
    nx, ny = cosine * hit.dx + sine * lx, cosine * hit.dy + sine * ly
    struck = self.rayOf(hit.bx, hit.by, nx, ny, 0.0, speed * cosine,
                        length, (met * cosine, 0.0))
    if abs(offset) >= reach:
      shift = hit.offset - offset
      cue = self.rayOf(hit.x + shift * lx, hit.y + shift * ly, hit.dx,
                       hit.dy, side, speed, length, state)
      return cue, struck
    cx, cy = hit.bx - reach * nx, hit.by - reach * ny
    tx, ty = hit.dx - cosine * nx, hit.dy - cosine * ny
    fx = 5.0 / 7.0 * tx + 2.0 / 7.0 * share * hit.dx
    fy = 5.0 / 7.0 * ty + 2.0 / 7.0 * share * hit.dy
    size = math.hypot(fx, fy)
    if size <= 1e-9:
      return ((cx, cy),) * self.__ray_points__, struck
    cue = self.rayOf(cx, cy, fx, fy, side, speed, length,
                     (met * size, met * size))
    return cue, struck


def _mirrored(frame: tuple, cushion: str, reach: float, width: float,
              length: float) -> tuple:
  """Returns the unfolding 'frame', (fx, ox, fy, oy), of a ball after
  it meets 'cushion': the rest of its way mirrored across the cushion's
  line onto the next copy."""
  fx, ox, fy, oy = frame
  if cushion in ('left', 'right'):
    line = reach if cushion == 'left' else width - reach
    return -fx, 2.0 * fx * line + ox, fy, oy
  line = reach if cushion == 'foot' else length - reach
  return fx, ox, -fy, 2.0 * fy * line + oy


def _linesMet(start: float, end: float, reach: float,
              size: float) -> int:
  """Returns how many cushions' lines, at 'reach' and every 'size' on,
  a step from 'start' to 'end' meets: one it sets off on left out, one
  it ends on counted, as the ball meets it arriving; within a hair."""
  hair = 1e-6
  if end > start:
    low, high = start + hair, end + hair
  else:
    low, high = end - hair, start - hair
  first = math.ceil((low - reach) / size)
  last = math.floor((high - reach) / size)
  if end > start and (low - reach) / size == first:
    first += 1
  if end < start and (high - reach) / size == last:
    last -= 1
  return max(last - first + 1, 0)


@functools.lru_cache(maxsize=1)
def _cloth() -> tuple[float, float]:
  """Returns how fast a rolling ball slows and how hard the cloth grips
  a sliding one, its slowing, in mm/s², as 'Cloth' has them, reckoned
  once."""
  cloth = Cloth()
  return cloth.rollingDecay(), cloth.sliding * cloth.gravity


def _timeTo(distance: float, speed: float, slowing: float) -> float:
  """Returns how long a ball setting off at 'speed', its speed falling
  by twice 'slowing' a second (rising, below nought), takes to go
  'distance'."""
  if abs(slowing) < 1e-12:
    return distance / speed
  root = math.sqrt(max(speed * speed - 4.0 * slowing * distance, 0.0))
  return (speed - root) / (2.0 * slowing)


@functools.lru_cache(maxsize=16)
def _reachOf(table: CaromTable) -> float:
  """Returns how far a ball's middle is from a cushion's nose on
  'table' as it touches it, as 'Motion' has it, reckoned once."""
  return Motion(table).reach()


def _unit(x: float, y: float) -> Place:
  """Returns 'x', 'y' made of length one."""
  length = math.hypot(x, y)
  return x / length, y / length


def _inside(low: tuple, x: float, y: float) -> bool:
  """Tells whether 'x', 'y' lies on the map 'low', its least 'x' and
  'y' and its most."""
  return low[0] <= x <= low[2] and low[1] <= y <= low[3]


def _entry(px: float, py: float, sx: float, sy: float,
           reach: float) -> float:
  """Returns how far along the step 'sx', 'sy' from 'px', 'py', off a
  ball's middle and 'reach' or more from it, a share of the step, it
  first comes 'reach' from it; one if it does not within the step."""
  a = sx * sx + sy * sy
  b = 2.0 * (px * sx + py * sy)
  c = px * px + py * py - reach * reach
  disc = b * b - 4.0 * a * c
  if a <= 0.0 or disc < 0.0:
    return 1.0
  return min(max((-b - math.sqrt(disc)) / (2.0 * a), 0.0), 1.0)
