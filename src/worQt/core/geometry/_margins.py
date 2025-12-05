"""
Margins provides a four element structure defining the margins at left,
top, right and bottom. The intended use is to subtract from or add to
'Rect' or 'Size' objects when calculating layout. Margins objects are not
meaningful on their own, but specifies relative positions between 'Rect'
or 'Size' objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import Self

from PySide6.QtCore import QMargins, QMarginsF
from worktoy.core.sentinels import THIS
from worktoy.desc import Alias, Field
from worktoy.dispatch import overload

from . import FourDim, Rect, Size


class Margins(FourDim):
  """
  Margins provides a four element structure defining the margins at left,
  top, right and bottom. The intended use is to subtract from or add to
  'Rect' or 'Size' objects when calculating layout. Margins objects are not
  meaningful on their own, but specifies relative positions between 'Rect'
  or 'Size' objects.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  left = Alias('v0')
  top = Alias('v1')
  right = Alias('v2')
  bottom = Alias('v3')

  #  Virtual Variables
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQ(self, ) -> QMargins:
    """
    Gets the 'QMargins' representation of the 'Margins' object.
    """
    return QMargins(
        self.left,
        self.top,
        self.right,
        self.bottom,
    )

  @QF.GET
  def _getQF(self, ) -> QMarginsF:
    """
    Gets the 'QMarginsF' representation of the 'Margins' object.
    """
    return QMarginsF(
        float(self.left),
        float(self.top),
        float(self.right),
        float(self.bottom),
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __neg__(self, ) -> Self:
    """
    Creates a new 'Margins' object by negating the margins.
    """
    cls = type(self)
    return cls(
        -self.left,
        -self.top,
        -self.right,
        -self.bottom,
    )

  @overload(THIS)
  def __add__(self, other: Self) -> Self:
    """
    Creates a new 'Margins' object by adding the margins from another
    'Margins' object.
    """
    cls = type(other)
    return cls(
        self.left + other.left,
        self.top + other.top,
        self.right + other.right,
        self.bottom + other.bottom,
    )

  @overload(THIS)
  def __sub__(self, other: Self) -> Self:
    """
    Creates a new 'Margins' object by subtracting the margins from another
    'Margins' object.
    """
    cls = type(other)
    return cls(
        self.left - other.left,
        self.top - other.top,
        self.right - other.right,
        self.bottom - other.bottom,
    )

  @overload(Size)
  def __add__(self, other: Size) -> Size:
    """
    Creates a new 'Size' object by adding the margins to a 'Size' object.
    """
    newWidth = other.width + self.left + self.right
    newHeight = other.height + self.top + self.bottom
    return Size(newWidth, newHeight)

  @overload(Size)
  def __sub__(self, other: Size) -> Size:
    """
    Creates a new 'Size' object by subtracting the margins from a 'Size'
    object.
    """
    newWidth = other.width - self.left - self.right
    newHeight = other.height - self.top - self.bottom
    return Size(newWidth, newHeight)

  @overload(Rect)
  def __add__(self, other: Rect) -> Rect:
    """
    Creates a new 'Rect' object by adding the margins to a 'Rect' object.
    """
    newLeft = other.left - self.left
    newTop = other.top - self.top
    newRight = other.right + self.right
    newBottom = other.bottom + self.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(Rect)
  def __sub__(self, other: Rect) -> Rect:
    """
    Creates a new 'Rect' object by subtracting the margins from a 'Rect'
    object.
    """
    newLeft = other.left + self.left
    newTop = other.top + self.top
    newRight = other.right - self.right
    newBottom = other.bottom - self.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(Size)
  def __rsub__(self, other: Size) -> Size:
    """
    Creates a new 'Size' object by subtracting the margins from a 'Size'
    object.
    """
    newWidth = other.width - self.left - self.right
    newHeight = other.height - self.top - self.bottom
    return Size(newWidth, newHeight)

  @overload(Rect)
  def __rsub__(self, other: Rect) -> Rect:
    """
    Creates a new 'Rect' object by subtracting the margins from a 'Rect'
    object.
    """
    newLeft = other.left + self.left
    newTop = other.top + self.top
    newRight = other.right - self.right
    newBottom = other.bottom - self.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(Size)
  def __radd__(self, other: Size) -> Size:
    """
    Creates a new 'Size' object by adding the margins to a 'Size' object.
    """
    newWidth = other.width + self.left + self.right
    newHeight = other.height + self.top + self.bottom
    return Size(newWidth, newHeight)

  @overload(Rect)
  def __radd__(self, other: Rect) -> Rect:
    """
    Creates a new 'Rect' object by adding the margins to a 'Rect' object.
    """
    newLeft = other.left - self.left
    newTop = other.top - self.top
    newRight = other.right + self.right
    newBottom = other.bottom + self.bottom
    return Rect(newLeft, newTop, newRight, newBottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
