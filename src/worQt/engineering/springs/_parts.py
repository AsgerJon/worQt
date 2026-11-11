"""
The parts of a system of springs: 'Point', 'Spring', 'Damper' and the
components, so far 'SpringMassDamper'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple


class Point(NamedTuple):
  """
  Point is a mass at a point in space, 'at' (x, y, z) in m, z up, of
  'mass' kg, moving along the axes in 'moves', any of 'xyz': all three
  is free, none is 'pinned' in place, an anchor holding what is on it,
  and one or two is a point on a rail or a table.
  """

  at: tuple[float, float, float]
  mass: float
  moves: str

  @property
  def pinned(self) -> bool:
    """Whether the point is pinned in place, moving along no axis."""
    return False if self.moves else True

  def movedTo(self, at: tuple[float, float, float]) -> Point:
    """The point at 'at'."""
    return Point((*map(float, at),), self.mass, self.moves)

  def moving(self, moves: str) -> Point:
    """The point moving along the axes in 'moves'."""
    return Point(self.at, self.mass, moves)


class Spring(NamedTuple):
  """
  Spring is a spring between the points of index 'first' and 'second',
  of 'stiffness' N/m, pulling them together when longer than its 'rest'
  length, in m, and pushing them apart when shorter, along the line
  between them as it turns.
  """

  first: int
  second: int
  stiffness: float
  rest: float


class Damper(NamedTuple):
  """
  Damper is a dashpot between the points of index 'first' and 'second',
  of 'damping' N s/m, resisting their moving apart or together along
  the line between them, as hard as how fast.
  """

  first: int
  second: int
  damping: float


class SpringMassDamper(NamedTuple):
  """
  SpringMassDamper is a component: a rod from the point of index 'base'
  to the point of index 'tip', whose mass is the mass at its end. Seen
  from outside, it is a rigid body but for its length, which is that of
  the spring of 'stiffness' N/m and 'rest' length in m inside it, beside
  a damper of 'damping' N s/m, nought for none. How it may turn about
  its base, 'turning', says the rest: 'fixed', its direction kept as set
  up, its tip moving only along it, the spring, mass and damper working
  in that one direction; 'hinge', turning about 'axis' only, its tip
  moving in the plane square to it; or 'free', any way. Its base moves
  as its point does.
  """

  base: int
  tip: int
  stiffness: float
  damping: float
  rest: float
  turning: str
  axis: tuple[float, float, float]

  def turned(self, turning: str) -> SpringMassDamper:
    """The component turning as 'turning' says."""
    return SpringMassDamper(*self[:5], turning, self.axis)

  def about(self, axis: tuple[float, float, float]) -> SpringMassDamper:
    """The component hinged about 'axis'."""
    return SpringMassDamper(*self[:6], (*map(float, axis),))
