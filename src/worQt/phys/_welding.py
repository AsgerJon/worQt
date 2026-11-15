"""
Welding makes an assembly's welded bodies one body each, to be moved as
one, and tells each part's state again from the body it is part of.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._assembly import Assembly, Contact, Drag, Fixed, Motor, Weld
from ._body import Body, State
from ._shape import Shape, Sphere
from ._turned import Turned
from ._vectors import ORIGIN, UNTURNED, Quaternion, Vector
from ._vectors import conjugate, cross, dot, minus, normalised, plus
from ._vectors import product
from ._vectors import rotated, scaled
from ._vectors import solved


class Welding:
  """
  Welding is 'assembly' in 'states' with each weld's parts made one
  body: 'joined' the assembly as it moves (each welded body at its
  parts' centre of mass, the others as they were, every connection's
  ends on parts put on the bodies they are part of), 'states' their
  states, 'lost' the kinetic energy the parts' snap together took (none
  when they moved as one already). A welded body's own contact holds
  are let go each time (its skin's points are numbered otherwise than
  its parts'), holds on it carried; its stillness the least of its
  parts'. 'parts' tells, for each body of the
  assembly, the body of 'joined' it is part of, its middle's arm and
  its turn in that body's own frame, and where its shape's points begin
  among that body's.
  """

  def __init__(self, assembly: Assembly, states: tuple[State, ...]) -> None:
    self.parts: list[tuple[int, Vector, Quaternion, int]] = [None] * len(
      assembly.bodies)
    bodies, joinedStates = [], []
    for group in _groupsOf(len(assembly.bodies), assembly.welds):
      at = len(bodies)
      if len(group) == 1:
        index = group[0]
        body = assembly.bodies[index]
        bodies.append(body)
        joinedStates.append(states[index])
        self.parts[index] = (at, None, None, 0)
        continue
      body, state, placed = _weldedOf([assembly.bodies[i] for i in group],
                                      [states[i] for i in group])
      bodies.append(body)
      joinedStates.append(state)
      for index, (arm, turn, first) in zip(group, placed):
        self.parts[index] = (at, arm, turn, first)
    self.original = assembly
    self.leaders = {}
    for index, (at, _, _, _) in enumerate(self.parts):
      self.leaders.setdefault(at, index)
    connections = []
    for connection in assembly.connections:
      if isinstance(connection, Weld):
        continue
      if isinstance(connection, (Motor, Drag)):
        raise ValueError('a motor or a drag on welded bodies is not '
                         'handled yet')
      if isinstance(connection, Fixed):
        connections.append(Fixed(self.parts[connection.body][0]))
        continue
      if isinstance(connection, Contact):
        first = self.parts[connection.first][0]
        second = self.parts[connection.second][0]
        if first != second:
          connections.append(Contact(first, second, *connection[2:]))
        continue
      first = self.endOf(assembly, connection.first, connection.firstPoint)
      second = self.endOf(assembly, connection.second,
                          connection.secondPoint)
      connections.append(type(connection)(*first, *second,
                                          *connection[4:]))
    self.joined = Assembly(tuple(bodies), tuple(connections))
    holds = [[] for _ in bodies]
    rests = [None] * len(bodies)
    for index, state in enumerate(states):
      at, arm, _, _ = self.parts[index]
      rests[at] = state.rest if rests[at] is None else min(rests[at],
                                                           state.rest)
      if arm is not None:
        continue
      for point, other, x, y, z in state.holds:
        on, held = self.endOf(assembly, other, (x, y, z))
        holds[at].append((point, on, *held))
    self.states = tuple(State(*state[:5], tuple(sorted(held)), rest)
                        for state, held, rest in zip(joinedStates, holds,
                                                     rests))
    moving = sum(body.kineticOf(state)
                 for body, state in zip(assembly.bodies, states))
    self.lost = moving - sum(body.kineticOf(state)
                             for body, state in zip(bodies, joinedStates))

  def endOf(self, assembly: Assembly, index: int | None,
            point: Vector) -> tuple[int | None, Vector]:
    """The 'endOf' method returns a tie's end on body 'index' at
    'point' (its own frame) as an end on the body it is part of."""
    if index is None:
      return None, point
    at, arm, turn, _ = self.parts[index]
    if arm is None:
      return at, point
    centre = assembly.bodies[index].centre
    return at, plus(arm, rotated(turn, minus(point, centre)))

  def split(self, states: tuple[State, ...]) -> tuple[State, ...]:
    """The 'split' method returns the state of each body of the
    assembly, the bodies of 'joined' in 'states'."""
    out = []
    for index, (at, arm, turn, first) in enumerate(self.parts):
      whole = states[at]
      body = self.original.bodies[index]
      count = len(body.shape.points) if body.shape is not None else 0
      if arm is None:
        holds = tuple((point, *self.heldOn(other, (x, y, z)))
                      for point, other, x, y, z in whole.holds)
        out.append(State(*whole[:5], holds, whole.rest))
        continue
      bristles = tuple((point - first, x, y)
                       for point, x, y in whole.bristles
                       if first <= point < first + count)
      reach = rotated(whole.turn, arm)
      out.append(State(plus(whole.place, reach), product(whole.turn, turn),
                       plus(whole.velocity, cross(whole.spin, reach)),
                       whole.spin, bristles, (), whole.rest))
    return tuple(out)

  def heldOn(self, at: int, point: Vector) -> tuple:
    """The 'heldOn' method returns a hold on body 'at' of 'joined' at
    'point' (its own frame) as a hold on a body of the assembly: the
    least part it is made of, the point in that part's frame."""
    index = self.leaders[at]
    _, arm, turn, _ = self.parts[index]
    if arm is None:
      return (index, *point)
    centre = self.original.bodies[index].centre
    back = rotated(conjugate(turn), minus(point, arm))
    return (index, *plus(centre, back))


def _groupsOf(count: int, welds: tuple) -> list[list[int]]:
  """The '_groupsOf' function returns 'count' bodies sorted into groups
  welded together, welds sharing a body joined, each group least first,
  the groups in the order of their least."""
  leader = list(range(count))

  def leaderOf(index: int) -> int:
    """Returns the least body welded to 'index' so far."""
    while leader[index] != index:
      index = leader[index]
    return index

  for weld in welds:
    parts = [leaderOf(index) for index in weld.parts]
    least = min(parts, default=None)
    for part in parts:
      leader[part] = least
  groups: dict[int, list[int]] = {}
  for index in range(count):
    groups.setdefault(leaderOf(index), []).append(index)
  return [groups[key] for key in sorted(groups)]


def _weldedOf(bodies: list[Body], states: list[State]) -> tuple:
  """The '_weldedOf' function returns 'bodies' in 'states' welded into
  one: the body (its own frame the world's axes, its middle at the
  parts' centre of mass), its state (momentum and angular momentum
  kept), and each part's middle's arm, turn and first point in it."""
  mass = sum(body.mass for body in bodies)
  centre = scaled(_summed(scaled(state.place, body.mass)
                          for body, state in zip(bodies, states)),
                  1.0 / mass)
  velocity = scaled(_summed(body.momentumOf(state)
                            for body, state in zip(bodies, states)),
                    1.0 / mass)
  inertia = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
  momentum = (0.0, 0.0, 0.0)
  points, faces, bristles, placed = [], [], [], []
  for body, state in zip(bodies, states):
    arm = minus(state.place, centre)
    own = body.inertiaIn(state)
    far = dot(arm, arm)
    for i in range(3):
      for j in range(3):
        inertia[i][j] += own[i][j] + body.mass * ((far if i == j else 0.0)
                                                  - arm[i] * arm[j])
    momentum = plus(momentum, body.angularMomentumOf(state))
    moving = scaled(minus(state.velocity, velocity), body.mass)
    momentum = plus(momentum, cross(arm, moving))
    first, turn = len(points), normalised(state.turn)
    placed.append((arm, turn, first))
    if isinstance(body.shape, (Sphere, Turned)):
      raise ValueError('a ball or a turned solid cannot be welded yet')
    if body.shape is not None:
      for point in body.shape.points:
        points.append(plus(arm, rotated(turn, minus(point, body.centre))))
      faces.extend((i + first, j + first, k + first)
                   for i, j, k in body.shape.faces)
      bristles.extend((point + first, x, y)
                      for point, x, y in state.bristles)
  inertia = tuple(tuple(row) for row in inertia)
  spin = tuple(solved([list(row) for row in inertia], list(momentum)))
  shape = Shape(tuple(points), tuple(faces)) if points else None
  welded = Body(mass, ORIGIN, inertia, shape)
  state = State(centre, UNTURNED, velocity, spin,
                tuple(sorted(bristles)))
  return welded, state, placed


def _summed(vectors) -> Vector:
  """The '_summed' function returns the sum of 'vectors'."""
  total = (0.0, 0.0, 0.0)
  for vector in vectors:
    total = plus(total, vector)
  return total
