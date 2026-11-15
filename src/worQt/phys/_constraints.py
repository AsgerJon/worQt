"""
ConstraintSolver keeps what ties and actuators hold, tied points
together and actuated rods at their lengths, working out how hard each
pulls or pushes, as hard as it takes and no harder; and with them the
dampers' pushes, which depend on how the others make the bodies move:
all of an assembly's together.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._vectors import AXES, Matrix, Vector
from ._vectors import applied, cross, dot, matrixOf, minus, norm, plus
from ._vectors import scaled, solved, transposed

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Actuator, Damper, Tie

#  Rules kept to within this, m; tries to keep them, at most.
_CLOSE = 1e-13
_TRIES = 50


class ConstraintSolver:
  """
  ConstraintSolver keeps 'ties' and 'actuators', and pushes by
  'dampers', on the bodies 'movers' (the world's stepping's '_Moving',
  in the order of the assembly's bodies). Each holds a point on its
  first body and one on its second (or the world, which nothing moves)
  by rules: a tie three, its points together along each axis; an
  actuator one, its points its stroke's length apart. A damper is a
  rule of its own kind: its push what it gives for how fast it
  lengthens, on average over a half step. Each pulls along its own
  way: a tie's along its axis, an actuator's or a damper's along its
  rod, from its second end to its first.
  """

  def __init__(self, ties: tuple[Tie, ...], actuators: tuple[Actuator, ...],
               dampers: tuple[Damper, ...], movers: list) -> None:
    self.links = []
    for kind, links in (('tie', ties), ('actuator', actuators),
                        ('damper', dampers)):
      for link in links:
        ends = []
        for index, point, sign in ((link.first, link.firstPoint, 1.0),
                                   (link.second, link.secondPoint, -1.0)):
          if index is None:
            ends.append((None, point, sign))
          else:
            mover = movers[index]
            ends.append((mover, mover.inward(point), sign))
        self.links.append((tuple(ends), kind, link))
    self.rows = []
    for at, (_, kind, _) in enumerate(self.links):
      if kind == 'tie':
        self.rows.extend((at, axis) for axis in range(3))
      else:
        self.rows.append((at, None))
    involved = {}
    for ends, _, _ in self.links:
      for mover, _, _ in ends:
        if mover is not None:
          involved[id(mover)] = mover
    self.involved = list(involved.values())
    self.before = [0.0] * len(self.rows)

  def kindOf(self, row: int) -> str:
    """The 'kindOf' method returns the kind of rule 'row' is: 'tie',
    'actuator' or 'damper'."""
    return self.links[self.rows[row][0]][1]

  def remember(self, ) -> None:
    """The 'remember' method notes how fast each rule moves now, before
    a half step's kicks (the dampers' pushes are on the average of
    that and how fast they move after)."""
    self.before = self.rowSpeeds(self.armsNow(), self.waysNow())

  def rowSpeeds(self, arms: list[tuple], ways: list[Vector]) -> list:
    """The 'rowSpeeds' method returns how fast each rule moves along its
    way: its first end's velocity less its second's."""
    speeds = []
    for (link, _), way in zip(self.rows, ways):
      ends = self.links[link][0]
      first, second = (self.velocityAt(end, arm)
                       for end, arm in zip(ends, arms[link]))
      speeds.append(dot(way, minus(first, second)))
    return speeds

  def dampedRow(self, row: int, coupling: list, speeds: list,
                h: float) -> tuple[list[float], float]:
    """The 'dampedRow' method returns damper rule 'row's row of the
    system kept over half of 'h' and what it is kept at: its push, along
    its way, J = -(h/2) c (before + after) / 2, after = now + its row of
    'coupling' times the pushes."""
    share = 0.25 * h * self.links[self.rows[row][0]][2].damping
    line = [share * x for x in coupling[row]]
    line[row] += 1.0
    return line, -share * (self.before[row] + speeds[row])

  def pulled(self, h: float, time: float) -> None:
    """The 'pulled' method gives the bodies the pulls over a step of
    'h' s ending at 'time': just what keeps each rule once the bodies
    are moved and turned freely for the step (SHAKE: pulls tried, the
    rules' misses after the step measured, the pulls bettered by how
    much a pull now moves them, till they are kept), the dampers' first
    half pushes found with them."""
    arms, ways = self.armsNow(), self.waysNow()
    coupling = self.coupling(arms, ways)
    speeds = self.rowSpeeds(arms, ways)
    damped = [i for i in range(len(self.rows))
              if self.kindOf(i) == 'damper']
    impulses = [0.0] * len(self.rows)
    for tried in range(_TRIES):
      misses = self.missesAfter(impulses, arms, ways, h, time)
      if max(abs(miss) for miss in misses) <= _CLOSE and (
          tried or not damped):
        break
      matrix = [list(row) for row in coupling]
      right = [-miss / h for miss in misses]
      for i in damped:
        matrix[i], kept = self.dampedRow(i, coupling, speeds, h)
        right[i] = kept - sum(a * b for a, b in zip(matrix[i], impulses))
      better = solved(matrix, right)
      impulses = [a + b for a, b in zip(impulses, better)]
    self.push(impulses, arms, ways)

  def steadied(self, h: float, time: float) -> None:
    """The 'steadied' method gives the bodies the pulls, at once, that
    keep each rule moving as it must at 'time' (tied points alike, an
    actuator's ends parting at its stroke's rate: RATTLE's second half),
    and the dampers' second half pushes of the step of 'h' s, found
    with them."""
    arms, ways = self.armsNow(), self.waysNow()
    coupling = self.coupling(arms, ways)
    speeds = self.rowSpeeds(arms, ways)
    matrix, right = [list(row) for row in coupling], []
    for i, (link, _) in enumerate(self.rows):
      kind, data = self.links[link][1], self.links[link][2]
      if kind == 'damper':
        matrix[i], kept = self.dampedRow(i, coupling, speeds, h)
        right.append(kept)
        continue
      rate = data.stroke.at(time)[1] if kind == 'actuator' else 0.0
      right.append(rate - speeds[i])
    self.push(solved(matrix, right), arms, ways)

  def holds(self, besides: dict, time: float) -> list[float]:
    """The 'holds' method returns how hard each rule pulls, N, along
    its way, as the bodies are and move now at 'time': what keeps each
    rule's acceleration as it must, the bodies pushed besides by
    gravity, the ground and 'besides' (force and torque keyed by the
    body's 'id')."""
    arms, ways = self.armsNow(), self.waysNow()
    speeding = {}
    for mover in self.involved:
      force, torque = mover.forces()
      more = besides.get(id(mover), ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
      force, torque = plus(force, more[0]), plus(torque, more[1])
      spin = mover.spin()
      momentum = applied(matrixOf(mover.turn), mover.momentum)
      turning = applied(mover.softness(), minus(torque,
                                                cross(spin, momentum)))
      speeding[id(mover)] = (scaled(force, 1.0 / mover.mass), turning,
                             spin)
    missing = []
    for (link, row), way in zip(self.rows, ways):
      ends, kind, data = self.links[link]
      stroke = data.stroke if kind == 'actuator' else None
      speeds = []
      for (mover, _, _), arm in zip(ends, arms[link]):
        if mover is None:
          speeds.append((0.0, 0.0, 0.0))
          continue
        moving, turning, spin = speeding[id(mover)]
        swinging = cross(spin, cross(spin, arm))
        speeds.append(plus(plus(moving, cross(turning, arm)), swinging))
      must = 0.0
      if stroke is not None:
        first, second = (self.velocityAt(end, arm)
                         for end, arm in zip(ends, arms[link]))
        apart = minus(second, first)
        length = norm(minus(*self.pointsNow(link)[::-1]))
        across = dot(apart, apart) - dot(way, apart) ** 2
        must = stroke.at(time)[2] - across / length
      missing.append(dot(way, minus(speeds[0], speeds[1])) - must)
    return solved(self.coupling(arms, ways), [-x for x in missing])

  def pullsAndPushes(self, besides: dict, time: float) -> tuple:
    """The 'pullsAndPushes' method returns each tie's pull on its first
    body (N, in the world) and how hard each actuator pushes its ends
    apart (N), as 'holds' has them."""
    held = self.holds(besides, time)
    pulls, pushes, at = [], [], 0
    for _, kind, _ in self.links:
      if kind == 'tie':
        pulls.append((held[at], held[at + 1], held[at + 2]))
        at += 3
      else:
        pushes.append(held[at])
        at += 1
    return tuple(pulls), tuple(pushes)

  def pointsNow(self, link: int) -> tuple[Vector, Vector]:
    """The 'pointsNow' method returns where link 'link's two points are
    in the world now."""
    points = []
    for mover, arm, _ in self.links[link][0]:
      if mover is None:
        points.append(arm)
      else:
        points.append(plus(mover.place, mover.outward(arm)))
    return points[0], points[1]

  def armsNow(self, ) -> list[tuple]:
    """The 'armsNow' method returns each link's ends' arms from their
    bodies' centres in the world as the bodies are now (None at the
    world)."""
    return [tuple(None if mover is None else mover.outward(arm)
                  for mover, arm, _ in ends) for ends, _, _ in self.links]

  def waysNow(self, ) -> list[Vector]:
    """The 'waysNow' method returns the way each rule pulls its first
    body, in the world as the bodies are now: a tie's along its axis, an
    actuator's or a damper's from its second end to its first (pushing
    apart)."""
    ways = []
    for link, row in self.rows:
      if row is not None:
        ways.append(AXES[row])
        continue
      first, second = self.pointsNow(link)
      apart = minus(first, second)
      length = norm(apart)
      ways.append(scaled(apart, 1.0 / length) if length else (0.0,) * 3)
    return ways

  def velocityAt(self, end: tuple, arm: Vector) -> Vector:
    """The 'velocityAt' method returns how fast a link's 'end' moves, at
    'arm' from its body's centre."""
    mover = end[0]
    if mover is None:
      return 0.0, 0.0, 0.0
    return plus(mover.velocity, cross(mover.spin(), arm))

  def coupling(self, arms: list[tuple], ways: list[Vector]) -> list:
    """The 'coupling' method returns how much each rule moves for each
    rule's pull, per N s, the bodies turned as 'arms' say: a pull on a
    body at one point moves another point of it by the pull over its
    mass and, turning it, by its arm across the turn the pull's twist
    gives (rules sharing no body, nought)."""
    size = len(self.rows)
    matrix = [[0.0] * size for _ in range(size)]
    soft = {id(mover): mover.softness() for mover in self.involved}
    for i, ((linkI, _), wayI) in enumerate(zip(self.rows, ways)):
      for j, ((linkJ, _), wayJ) in enumerate(zip(self.rows, ways)):
        total = 0.0
        for (mover, _, signI), armI in zip(self.links[linkI][0],
                                           arms[linkI]):
          if mover is None:
            continue
          for (other, _, signJ), armJ in zip(self.links[linkJ][0],
                                             arms[linkJ]):
            if other is not mover:
              continue
            moved = pointMoved(mover.mass, soft[id(mover)], armI, armJ,
                               wayJ)
            total += signI * signJ * dot(wayI, moved)
        matrix[i][j] = total
    return matrix

  def impulsesOf(self, impulses: list[float],
                 ways: list[Vector]) -> list[Vector]:
    """The 'impulsesOf' method returns each link's impulse on its first
    body, its rules' 'impulses' along their 'ways' added up."""
    out = [(0.0, 0.0, 0.0)] * len(self.links)
    for (link, _), impulse, way in zip(self.rows, impulses, ways):
      out[link] = plus(out[link], scaled(way, impulse))
    return out

  def missesAfter(self, impulses: list[float], arms: list[tuple],
                  ways: list[Vector], h: float, time: float) -> list:
    """The 'missesAfter' method returns how far each rule would miss,
    the bodies given 'impulses' (N s, along the rules' 'ways', on each
    link's first body) at 'arms' and moved freely for 'h' s to 'time':
    a tie's points apart along its axis, an actuator's ends further
    apart than its stroke's length (a damper, nought: it has none)."""
    trial = {id(mover): (mover.velocity, mover.momentum)
             for mover in self.involved}
    given = self.impulsesOf(impulses, ways)
    for (ends, _, _), linkArms, impulse in zip(self.links, arms, given):
      for (mover, _, sign), arm in zip(ends, linkArms):
        if mover is None:
          continue
        velocity, momentum = trial[id(mover)]
        signed = scaled(impulse, sign)
        velocity = plus(velocity, scaled(signed, 1.0 / mover.mass))
        twist = applied(transposed(matrixOf(mover.turn)),
                        cross(arm, signed))
        trial[id(mover)] = (velocity, plus(momentum, twist))
    moved = {}
    for mover in self.involved:
      velocity, momentum = trial[id(mover)]
      place, turn, _ = mover.drifted(velocity, momentum, h)
      moved[id(mover)] = (place, matrixOf(turn))
    misses = []
    for link, row in self.rows:
      points = []
      for mover, arm, _ in self.links[link][0]:
        if mover is None:
          points.append(arm)
          continue
        place, turning = moved[id(mover)]
        points.append(plus(place, applied(turning, arm)))
      kind = self.links[link][1]
      if kind == 'tie':
        misses.append(points[0][row] - points[1][row])
      elif kind == 'actuator':
        length = self.links[link][2].stroke.at(time)[0]
        misses.append(norm(minus(points[0], points[1])) - length)
      else:
        misses.append(0.0)
    return misses

  def push(self, impulses: list[float], arms: list[tuple],
           ways: list[Vector]) -> None:
    """The 'push' method gives the bodies 'impulses' (along the rules'
    'ways', on each link's first body, its second the other way) at
    'arms', each booked under its link's kind."""
    given = self.impulsesOf(impulses, ways)
    for (ends, kind, _), linkArms, impulse in zip(self.links, arms, given):
      for (mover, _, sign), arm in zip(ends, linkArms):
        if mover is not None:
          mover.pushed(scaled(impulse, sign), arm, kind)


def pointMoved(mass: float, soft: Matrix, at: Vector, by: Vector,
               impulse: Vector) -> Vector:
  """The 'pointMoved' function returns how much faster a body's point
  at arm 'at' from its centre moves for 'impulse' given it at arm 'by':
  the impulse over its 'mass', and the turn its twist gives (through
  'soft', the inverse of its inertia in the world) across the arm."""
  twist = applied(soft, cross(by, impulse))
  return minus(scaled(impulse, 1.0 / mass), cross(at, twist))
