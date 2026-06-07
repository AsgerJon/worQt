"""
Vector2D is a plane vector with integer components 'x' and 'y', plus its
magnitude ('mag'/'magSqr') and a dot product. A 'BaseObject' with overloaded
constructors: two points (the displacement from the first to the second), a
single point (from the origin), a 'QVector2D', plain numbers, or another
vector.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QVector2D
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._point_2d import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class Vector2D(BaseObject):
  """A plane vector with integer components."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  x = AttriBox[int](0)
  y = AttriBox[int](0)

  #  Virtual Variables
  mag: Field[float] = Field()
  magSqr: Field[int] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @magSqr.GET
  def _getMagSqr(self) -> int:
    return self.x * self.x + self.y * self.y

  @mag.GET
  def _getMag(self) -> float:
    return self.magSqr ** 0.5

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D, Point2D)
  def __init__(self, p: Point2D, q: Point2D) -> None:
    self.x, self.y = q.x - p.x, q.y - p.y

  @overload(Point2D)
  def __init__(self, p: Point2D) -> None:
    self.x, self.y = p.x, p.y

  @overload(int, int)
  def __init__(self, x: int, y: int) -> None:
    self.x, self.y = x, y

  @overload(float, float)
  def __init__(self, x: float, y: float) -> None:
    self.x, self.y = round(x), round(y)

  @overload(QVector2D, strict=True)
  def __init__(self, vector: QVector2D) -> None:
    self.x, self.y = round(vector.x()), round(vector.y())

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.x, self.y = other.x, other.y

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __mul__(self, other: Self) -> int:
    """The dot product of two vectors."""
    return self.x * other.x + self.y * other.y

  def __str__(self) -> str:
    return 'Vector2D(%d, %d)' % (self.x, self.y)

  __repr__ = __str__
