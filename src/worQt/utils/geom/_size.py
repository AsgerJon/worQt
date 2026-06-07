"""
Size is a plain width/height value type with integer dimensions. A
'BaseObject' with overloaded constructors accepting plain numbers, a 'QSize'
or 'QSizeF', or the size of a 'QRect'/'QRectF' (all strict, so the dispatcher
never coerces a Shiboken type), or another size. Convert out with the 'Q'
('QSize') and 'QF' ('QSizeF') fields.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, QSizeF, QRect, QRectF
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class Size(BaseObject):
  """A width/height pair with integer dimensions."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  width = AttriBox[int](0)
  height = AttriBox[int](0)

  #  Virtual Variables
  area: Field[int] = Field()
  Q: Field[QSize] = Field()
  QF: Field[QSizeF] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @area.GET
  def _getArea(self) -> int:
    return self.width * self.height

  @Q.GET
  def _getQSize(self) -> QSize:
    return QSize(self.width, self.height)

  @QF.GET
  def _getQSizeF(self) -> QSizeF:
    return QSizeF(float(self.width), float(self.height))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, width: int, height: int) -> None:
    self.width, self.height = width, height

  @overload(float, float)
  def __init__(self, width: float, height: float) -> None:
    self.width, self.height = round(width), round(height)

  @overload(QSize, strict=True)
  def __init__(self, size: QSize) -> None:
    self.width, self.height = size.width(), size.height()

  @overload(QSizeF, strict=True)
  def __init__(self, size: QSizeF) -> None:
    self.width, self.height = round(size.width()), round(size.height())

  @overload(QRect, strict=True)
  def __init__(self, rect: QRect) -> None:
    self.width, self.height = rect.width(), rect.height()

  @overload(QRectF, strict=True)
  def __init__(self, rect: QRectF) -> None:
    self.width, self.height = round(rect.width()), round(rect.height())

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.width, self.height = other.width, other.height

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self) -> str:
    return 'Size(%d, %d)' % (self.width, self.height)

  __repr__ = __str__
