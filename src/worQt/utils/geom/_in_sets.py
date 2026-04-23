"""
InSets encapsulates a set of margins for a rectangle.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMargins, QMarginsF, QRect, QRectF, QSize, QSizeF
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute.desc import WriteOnceError

from . import Rect, Size, Point2D

from .euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Self, Optional

  QField: TypeAlias = Union[QMargins, Field]
  QFField: TypeAlias = Union[QMarginsF, Field]
  PointField: TypeAlias = Union[Point2D, Field]
  MaybeBool: TypeAlias = Optional[bool]
  BoolField: TypeAlias = Union[bool, Field]


class InSets(EuclideanObject):
  """
  InSets encapsulates a set of margins for a rectangle.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_frozen__: BoolField = False

  #  Private Variables
  __is_frozen__: MaybeBool = None

  #  Public Variables
  frozen: BoolField = Field()
  left = Dimension(int, 0, 'l', 'left')
  top = Dimension(int, 0, 't', 'top')
  right = Dimension(int, 0, 'r', 'right')
  bottom = Dimension(int, 0, 'b', 'bottom')

  #  Virtual Variables
  Q: QField = Field()
  QF: QFField = Field()
  topLeft: PointField = Field()
  topRight: PointField = Field()
  bottomRight: PointField = Field()
  bottomLeft: PointField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createFrozenFlag(self, ) -> None:
    self.__is_frozen__ = True if self.__fallback_frozen__ else False

  @frozen.GET
  def _getFrozen(self, **kwargs) -> bool:
    if self.__is_frozen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createFrozenFlag()
      return self._getFrozen(_recursion=True)
    return True if self.__is_frozen__ else False

  @topLeft.GET
  def _getTopLeft(self, ) -> Point2D:
    return Point2D(self.left, self.top)

  @topRight.GET
  def _getTopRight(self, ) -> Point2D:
    return Point2D(-self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self, ) -> Point2D:
    return Point2D(-self.right, -self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self, ) -> Point2D:
    return Point2D(self.left, -self.bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @frozen.SET
  def _setFrozen(self, value: bool) -> None:
    if self.__is_frozen__ is not None:
      cls = type(self)
      desc = getattr(cls, 'frozen', )
      raise WriteOnceError(desc, self.__is_frozen__, value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  other - self

  @overload(Rect)
  def __rsub__(self, other: Rect) -> Rect:
    newLeft = other.left + self.left
    newTop = other.top + self.top
    newRight = other.right - self.right
    newBottom = other.bottom - self.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(Size)
  def __rsub__(self, other: Size) -> Size:
    newWidth = other.width - self.left - self.right
    newHeight = other.height - self.top - self.bottom
    return Size(newWidth, newHeight)

  @overload(QRect, strict=True)
  def __rsub__(self, other: QRect) -> QRect:
    return (Rect(other) - self).Q

  @overload(QRectF, strict=True)
  def __rsub__(self, other: QRectF) -> QRectF:
    return (Rect(other) - self).QF

  @overload(QSize, strict=True)
  def __rsub__(self, other: QSize) -> QSize:
    newWidth = other.width() - self.left - self.right
    newHeight = other.height() - self.top - self.bottom
    return QSize(newWidth, newHeight)

  @overload(QSizeF, strict=True)
  def __rsub__(self, other: QSizeF) -> QSizeF:
    newWidth = other.width() - self.left - self.right
    newHeight = other.height() - self.top - self.bottom
    return QSizeF(newWidth, newHeight)

  @overload(QMargins, strict=True)
  def __rsub__(self, other: QMargins) -> QMargins:
    newLeft = other.left() - self.left
    newTop = other.top() - self.top
    newRight = other.right() - self.right
    newBottom = other.bottom() - self.bottom
    return QMargins(newLeft, newTop, newRight, newBottom)

  @overload(QMarginsF, strict=True)
  def __rsub__(self, other: QMarginsF) -> QMarginsF:
    newLeft = other.left() - self.left
    newTop = other.top() - self.top
    newRight = other.right() - self.right
    newBottom = other.bottom() - self.bottom
    return QMarginsF(newLeft, newTop, newRight, newBottom)

  #  self - other

  @overload(THIS)
  def __sub__(self, other: Self) -> Self:
    cls = type(self)
    newLeft = self.left - other.left
    newTop = self.top - other.top
    newRight = self.right - other.right
    newBottom = self.bottom - other.bottom
    return cls(newLeft, newTop, newRight, newBottom)

  @overload(QMargins, strict=True)
  def __sub__(self, other: QMargins) -> Self:
    cls = type(self)
    newLeft = self.left - other.left()
    newTop = self.top - other.top()
    newRight = self.right - other.right()
    newBottom = self.bottom - other.bottom()
    return cls(newLeft, newTop, newRight, newBottom)

  @overload(QMarginsF, strict=True)
  def __sub__(self, other: QMarginsF) -> Self:
    return self - QMarginsF.toMargins(other, )

  #  other + self

  @overload(Rect)
  def __radd__(self, other: Rect) -> Rect:
    newLeft = other.left - self.left
    newTop = other.top - self.top
    newRight = other.right + self.right
    newBottom = other.bottom + self.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(Size)
  def __radd__(self, other: Size) -> Size:
    newWidth = self.left + other.width + self.right
    newHeight = self.top + other.height + self.bottom
    return Size(newWidth, newHeight)

  @overload(QRect, strict=True)
  def __radd__(self, other: QRect) -> QRect:
    return (self + Rect(other)).Q

  @overload(QRectF, strict=True)
  def __radd__(self, other: QRectF) -> QRectF:
    return (self + Rect(other)).QF

  @overload(QSize, strict=True)
  def __radd__(self, other: QSize) -> QSize:
    newWidth = self.left + other.width() + self.right
    newHeight = self.top + other.height() + self.bottom
    return QSize(newWidth, newHeight)

  @overload(QSizeF, strict=True)
  def __radd__(self, other: QSizeF) -> QSizeF:
    newWidth = self.left + other.width() + self.right
    newHeight = self.top + other.height() + self.bottom
    return QSizeF(newWidth, newHeight)

  @overload(QMargins, strict=True)
  def __radd__(self, other: QMargins) -> QMargins:
    newLeft = self.left + other.left()
    newTop = self.top + other.top()
    newRight = self.right + other.right()
    newBottom = self.bottom + other.bottom()
    return QMargins(newLeft, newTop, newRight, newBottom)

  @overload(QMarginsF, strict=True)
  def __radd__(self, other: QMarginsF) -> QMarginsF:
    return (self + QMarginsF.toMargins(other, )).QF

  #  self + other

  @overload(THIS)
  def __add__(self, other: Self) -> Self:
    cls = type(self)
    newLeft = self.left + other.left
    newTop = self.top + other.top
    newRight = self.right + other.right
    newBottom = self.bottom + other.bottom
    return cls(newLeft, newTop, newRight, newBottom)

  @overload(QMargins, strict=True)
  def __add__(self, other: QMargins) -> Self:
    cls = type(self)
    newLeft = self.left + other.left()
    newTop = self.top + other.top()
    newRight = self.right + other.right()
    newBottom = self.bottom + other.bottom()
    return cls(newLeft, newTop, newRight, newBottom)

  @overload(QMarginsF, strict=True)
  def __add__(self, other: QMarginsF) -> Self:
    return self + QMarginsF.toMargins(other, )

  @overload(Rect)
  def __add__(self, other: Rect) -> Rect:
    newLeft = self.left + other.left
    newTop = self.top + other.top
    newRight = self.right + other.right
    newBottom = self.bottom + other.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(QRectF, strict=True)
  @overload(QRect, strict=True)
  def __add__(self, other: QRect) -> Rect:
    return self + Rect(other)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Rect, Rect)
  def __init__(self, inner: Rect, outer: Rect, **kwargs) -> None:
    """
    Creates the insets of the inner rectangle with respect to the outer
    rectangle. The insets are the distances from the sides of the inner
    rectangle to the corresponding sides of the outer rectangle. The
    insets are positive if the inner rectangle is inside the outer
    rectangle.
    """
    newLeft = inner.left - outer.left
    newTop = inner.top - outer.top
    newRight = outer.width - inner.width - newLeft
    newBottom = outer.height - inner.height - newTop
    self.__init__(newLeft, newTop, newRight, newBottom)
    if kwargs:
      self.__init__(**kwargs)

  @overload(QRect, QRect, strict=True)
  @overload(QRectF, QRectF, strict=True)
  @overload(QRect, QRectF, strict=True)
  @overload(QRectF, QRect, strict=True)
  def __init__(self, inner: QRect, outer: QRect, **kwargs) -> None:
    self.__init__(Rect(inner), Rect(outer))
    if kwargs:
      self.__init__(**kwargs)

  @overload(Size, Size)
  def __init__(self, inner: Size, outer: Size, **kwargs) -> None:
    newLeft = (outer.width - inner.width) / 2
    newTop = (outer.height - inner.height) / 2
    newRight = outer.width - inner.width - newLeft
    newBottom = outer.height - inner.height - newTop
    newDims = (newLeft, newTop, newRight, newBottom)
    roundedDims = (*(round(dim) for dim in newDims),)
    self.__init__(*roundedDims, )
    if kwargs:
      self.__init__(**kwargs)

  @overload(QSize, QSize, strict=True)
  @overload(QSizeF, QSizeF, strict=True)
  @overload(QSize, QSizeF, strict=True)
  @overload(QSizeF, QSize, strict=True)
  def __init__(self, inner: QSize, outer: QSize, **kwargs) -> None:
    self.__init__(Size(inner), Size(outer))
    if kwargs:
      self.__init__(**kwargs)

  @overload(int, int)
  def __init__(self, horizontal: int, vertical: int, **kwargs) -> None:
    self.__init__(horizontal, vertical, horizontal, vertical)
    if kwargs:
      self.__init__(**kwargs)

  @overload(int)
  def __init__(self, dim: int, **kwargs) -> None:
    self.__init__(dim, dim, dim, dim)
    if kwargs:
      self.__init__(**kwargs)

  @overload(THIS)
  def __init__(self, other: Self, **kwargs) -> None:
    self.__init__(other.left, other.top, other.right, other.bottom)
    if kwargs:
      self.__init__(**kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    frozenFlag = kwargs.get('frozen', None)
    if frozenFlag is not None:
      self.__is_frozen__ = True if frozenFlag else False
