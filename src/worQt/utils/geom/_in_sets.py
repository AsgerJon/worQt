"""
InSets is a set of integer edge insets ('left', 'top', 'right', 'bottom') -
margins/borders/paddings. The box model uses it as 'Rect + InSets' (grow the
rect outward by the insets) and 'Rect - InSets' (shrink inward); the same
works for 'Size'. A 'BaseObject' with overloaded constructors: four edges,
horizontal/vertical, a single uniform inset, the insets between an inner and
outer rect (or size), or another 'InSets'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from types import NotImplementedType as NIType

from PySide6.QtCore import QMargins, QSize, QSizeF, QRect, QRectF
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from . import Rect
from . import Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Optional, Union


class InSets(BaseObject):
  """Integer edge insets used for margins, borders and paddings."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  left = AttriBox[int](0)
  top = AttriBox[int](0)
  right = AttriBox[int](0)
  bottom = AttriBox[int](0)

  #  Virtual Variables
  Q: Field[QMargins] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQMargins(self) -> QMargins:
    return QMargins(self.left, self.top, self.right, self.bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)
  def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
    self.left, self.top, self.right, self.bottom = left, top, right, bottom

  @overload(int, int)
  def __init__(self, horizontal: int, vertical: int) -> None:
    self.left = self.right = horizontal
    self.top = self.bottom = vertical

  @overload(int)
  def __init__(self, inset: int) -> None:
    self.left = self.top = self.right = self.bottom = inset

  @overload(Rect, Rect)
  def __init__(self, inner: Rect, outer: Rect) -> None:
    self.left, self.top = inner.left - outer.left, inner.top - outer.top
    self.right = outer.right - inner.right
    self.bottom = outer.bottom - inner.bottom

  @overload(Size, Size)
  def __init__(self, inner: Size, outer: Size) -> None:
    self.left = (outer.width - inner.width) // 2
    self.right = outer.width - inner.width - self.left
    self.top = (outer.height - inner.height) // 2
    self.bottom = outer.height - inner.height - self.top

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.left, self.top = other.left, other.top
    self.right, self.bottom = other.right, other.bottom

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _resolveOther(cls, other: Any) -> Union[Self, NIType]:
    if isinstance(other, cls):
      return other
    try:
      resolved = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return resolved

  #  Mathematical Operators

  def __pos__(self, ) -> Self:
    cls = type(self)
    return cls(self)

  def __neg__(self, ) -> Self:
    cls = type(self)
    return cls(-self.left, -self.top, -self.right, -self.bottom)

  @overload(THIS)
  def __add__(self, other: Self) -> Self:
    cls = type(self)
    left = self.left + other.left
    top = self.top + other.top
    right = self.right + other.right
    bottom = self.bottom + other.bottom
    return cls(left, top, right, bottom)

  @overload(Size)
  def __add__(self, size: Size) -> Size:
    width: int = self.left + size.width + self.right
    height: int = self.top + size.height + self.bottom
    return Size(width, height)

  @overload(Rect)
  def __add__(self, rect: Rect) -> Rect:
    """'insets + rect' grows the rect outward by the insets."""
    left = rect.left - self.left
    top = rect.top - self.top
    right = rect.right + self.right
    bottom = rect.bottom + self.bottom
    return Rect(left, top, right, bottom)

  @overload(QSize)
  @overload(QSizeF)
  def __add__(self, size: Union[QSize, QSizeF]) -> Union[QSize, QSizeF]:
    width = self.left + size.width() + self.right
    height = self.top + size.height() + self.bottom
    return type(size)(width, height)

  @overload(QRect)
  @overload(QRectF)
  def __add__(self, rect: Union[QRect, QRectF]) -> Union[QRect, QRectF]:
    """'insets + rect' grows the rect outward by the insets."""
    left = rect.left() - self.left
    top = rect.top() - self.top
    right = rect.right() + self.right
    bottom = rect.bottom() + self.bottom
    return type(rect)(left, top, right, bottom)

  @overload(int)
  def __add__(self, value: int) -> Self:
    cls = type(self)
    left = self.left + value
    top = self.top + value
    right = self.right + value
    bottom = self.bottom + value
    return cls(left, top, right, bottom)

  def __iadd__(self, other: Any) -> Any:
    try:
      out = self + other
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return out

  def __radd__(self, other: Any) -> Any:
    """'rect + insets' grows the rect outward by the insets."""
    return self + other

  def __sub__(self, other: Any) -> Any:
    resolved = self._resolveOther(other)
    if resolved is NotImplemented:
      return NotImplemented
    return self + (-resolved)

  def __isub__(self, other: Any) -> Union[Self, NIType]:
    resolved = self._resolveOther(other)
    if resolved is NotImplemented:
      return NotImplemented
    return self - resolved

  def __rsub__(self, other: Any) -> Any:
    try:
      out = other + (-self)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return out

  def __str__(self) -> str:
    infoSpec: str = """%s(left=%d, top=%d, right=%d, bottom=%d)"""
    dims = (self.left, self.top, self.right, self.bottom)
    clsName: str = type(self).__name__
    return infoSpec % (clsName, *dims)

  def __repr__(self, ) -> str:
    infoSpec: str = """%s(%d, %d, %d, %d)"""
    dims = (self.left, self.top, self.right, self.bottom)
    clsName: str = type(self).__name__
    return infoSpec % (clsName, *dims)
