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

from PySide6.QtCore import QMargins
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._rect import Rect
from ._size import Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


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

  @overload(Rect)
  def __radd__(self, rect: Rect) -> Rect:
    """'rect + insets' grows the rect outward by the insets."""
    return Rect(rect.left - self.left, rect.top - self.top,
                rect.right + self.right, rect.bottom + self.bottom)

  @overload(Rect)
  def __rsub__(self, rect: Rect) -> Rect:
    """'rect - insets' shrinks the rect inward by the insets."""
    return Rect(rect.left + self.left, rect.top + self.top,
                rect.right - self.right, rect.bottom - self.bottom)

  @overload(Size)
  def __radd__(self, size: Size) -> Size:
    return Size(self.left + size.width + self.right,
                self.top + size.height + self.bottom)

  @overload(Size)
  def __rsub__(self, size: Size) -> Size:
    return Size(size.width - self.left - self.right,
                size.height - self.top - self.bottom)

  @overload(THIS)
  def __add__(self, other: Self) -> Self:
    return InSets(self.left + other.left, self.top + other.top,
                  self.right + other.right, self.bottom + other.bottom)

  @overload(THIS)
  def __sub__(self, other: Self) -> Self:
    return InSets(self.left - other.left, self.top - other.top,
                  self.right - other.right, self.bottom - other.bottom)

  def __str__(self) -> str:
    return 'InSets(%d, %d, %d, %d)' % (
        self.left, self.top, self.right, self.bottom)

  __repr__ = __str__
