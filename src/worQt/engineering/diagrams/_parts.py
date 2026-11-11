"""
The parts of a frame: its 'Node's and 'Member's, its 'Support's, and
its loads, 'PointLoad', 'LineLoad' and 'PointMoment'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

#  What each kind of support holds: along x, along y and turning
_HOLDS = {
  'pin'   : (1, 1, 0),
  'roller': (0, 1, 0),
  'fixed' : (1, 1, 1),
}


class Node(NamedTuple):
  """
  Node is a joint of a frame, at 'x' and 'y' in m, y up, where its
  members meet.
  """

  x: float
  y: float


class Member(NamedTuple):
  """
  Member is a straight member of a frame from the node of index 'first'
  to the node of index 'second', of bending stiffness 'EI' in kNm² and
  axial stiffness 'EA' in kN, which tell only how a frame statically
  indeterminate shares its load. It is joined rigidly to its nodes, but
  at an end hinged, 'startHinge' at its first and 'endHinge' at its
  second, where it takes no moment.

  Along it, 's' runs from its first node to its second; across it, its
  left as it runs is its positive side.
  """

  first: int
  second: int
  EI: float
  EA: float
  startHinge: bool
  endHinge: bool

  def hinged(self, start: bool, end: bool) -> Member:
    """The member hinged at its start and its end as 'start' and 'end'
    say."""
    return Member(self.first, self.second, self.EI, self.EA,
                  True if start else False, True if end else False)


class Support(NamedTuple):
  """
  Support is what holds a frame at the node of index 'node', of a
  'kind': a 'pin' holds it along x and y, a 'roller' along y only, and
  a 'fixed' end holds it turning too. 'holds' says which, along x,
  along y and turning, 1 held and 0 free.
  """

  node: int
  kind: str

  @property
  def holds(self) -> tuple[int, int, int]:
    """What the support holds: along x, along y and turning."""
    return _HOLDS[self.kind]

  @staticmethod
  def kinds() -> tuple[str, ...]:
    """The kinds of support there are."""
    return (*_HOLDS,)


class PointLoad(NamedTuple):
  """
  PointLoad is a force on the member of index 'member', 'at' m along it
  from its first node: 'down' kN pushing down and 'right' kN pushing to
  the right, either below nought the other way.
  """

  member: int
  at: float
  down: float
  right: float

  def movedTo(self, at: float) -> PointLoad:
    """The load 'at' m along its member."""
    return PointLoad(self.member, float(at), self.down, self.right)


class LineLoad(NamedTuple):
  """
  LineLoad is a load spread along the member of index 'member', from
  'start' to 'end' m along it, 'first' kN/m at its start and 'last' kN/m
  at its end, straight between, a metre of the member: 'down' pushing
  down, as weight and snow do, or 'right' pushing to the right, as wind
  does, either below nought the other way.
  """

  member: int
  start: float
  end: float
  first: float
  last: float
  direction: str

  def movedTo(self, at: float) -> LineLoad:
    """The load starting 'at' m along its member, as long."""
    return LineLoad(self.member, float(at),
                    float(at) + self.end - self.start, self.first,
                    self.last, self.direction)

  def intensity(self, s: float) -> float:
    """How hard the load pushes at 's' m along its member, in kN/m."""
    share = (s - self.start) / (self.end - self.start)
    return self.first + (self.last - self.first) * share

  def pushing(self, ) -> tuple[float, float]:
    """The way the load pushes, a unit vector."""
    return (0.0, -1.0) if self.direction == 'down' else (1.0, 0.0)


class PointMoment(NamedTuple):
  """
  PointMoment is a moment on the member of index 'member', 'at' m along
  it from its first node, of 'moment' kNm turning anticlockwise, below
  nought clockwise.
  """

  member: int
  at: float
  moment: float

  def movedTo(self, at: float) -> PointMoment:
    """The moment 'at' m along its member."""
    return PointMoment(self.member, float(at), self.moment)
