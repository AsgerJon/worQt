"""Size encapsulates size objects in a 2D space."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QSizeF, QSize, QRect, QRectF
from worktoy.core.sentinels import THIS

from worktoy.desc import AttriBox, Field

from worktoy.dispatch import overload

from worktoy.mcls import BaseObject

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Iterator


class Size(BaseObject):
  """Size encapsulates size objects in a 2D space."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_width__ = 1.0
  __fallback_height__ = 1.0

  #  Private Variables
  __private_width__ = None
  __private_height__ = None

  #  Public Variables
  width = Field()
  height = Field()

  #  Virtual Variables
  aspectRatio = Field()  # Aspect ratio of the size (width/height)
  QF = Field()  # QSizeF representation of the size
  Q = Field()  # QSize representation of the size

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @width.GET
  def _getWidth(self, **kwargs) -> float:
    """Get the width of the Size."""
    if self.__private_width__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__private_width__ = self.__fallback_width__
      return self._getWidth(_recursion=True)
    return self.__private_width__

  @height.GET
  def _getHeight(self, **kwargs) -> float:
    """Get the height of the Size."""
    if self.__private_height__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__private_height__ = self.__fallback_height__
      return self._getHeight(_recursion=True)
    return self.__private_height__

  @aspectRatio.GET
  def _getAspectRatio(self, **kwargs) -> float:
    """Get the aspect ratio of the Size."""
    if self.width == 0 or self.height == 0:
      raise ZeroDivisionError
    return self.width / self.height

  @QF.GET
  def _getQF(self) -> QSizeF:
    """Get the QSizeF representation of the Size."""
    return QSizeF(self.width, self.height)

  @Q.GET
  def _getQ(self) -> QSize:
    """Get the QSize representation of the Size."""
    return QSizeF.toSize(self.QF, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __rshift__(self, other: Self) -> Self:
    """Returns the largest size not greater than other, having same aspect
    ratio as self. """
    if other.aspectRatio > self.aspectRatio:
      return Size(other.height * self.aspectRatio, other.height)
    return Size(other.width, other.width / self.aspectRatio)

  @overload.fallback
  def __rshift__(self, other: Any) -> NotImplemented:
    return NotImplemented

  @overload(THIS)
  def __lshift__(self, other: Self) -> Self:
    """Returns the smallest size not less than other, having same aspect
    ratio as self. """
    if other.aspectRatio < self.aspectRatio:
      return Size(other.width, other.width / self.aspectRatio)
    return Size(other.height * self.aspectRatio, other.height)

  @overload.fallback
  def __lshift__(self, other: Any) -> NotImplemented:
    return NotImplemented

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    """Initialize Size from another Size."""
    self.__private_width__ = other.width
    self.__private_height__ = other.height

  @overload(float, float)
  def __init__(self, width: float, height: float) -> None:
    self.__private_width__ = float(width)
    self.__private_height__ = float(height)

  @overload(complex)
  def __init__(self, z: complex) -> None:
    self.__private_width__ = float(z.real)
    self.__private_height__ = float(z.imag)

  @overload(QSize)
  def __init__(self, size: QSize) -> None:
    """Initialize Size from a QSize."""
    self.__private_width__ = float(size.width())
    self.__private_height__ = float(size.height())

  @overload(QSizeF)
  def __init__(self, size: QSizeF) -> None:
    """Initialize Size from a QSizeF."""
    self.__private_width__ = float(size.width())
    self.__private_height__ = float(size.height())

  @overload(QRect)
  def __init__(self, rect: QRect) -> None:
    """Initialize Size from a QRect."""
    self.__private_width__ = float(rect.width())
    self.__private_height__ = float(rect.height())

  @overload(QRectF)
  def __init__(self, rect: QRectF) -> None:
    """Initialize Size from a QRectF."""
    self.__private_width__ = float(rect.width())
    self.__private_height__ = float(rect.height())

  @overload(float)
  def __init__(self, value: float) -> None:
    """Initialize Size with a single float value."""
    self.__private_width__ = float(value)
    self.__private_height__ = float(value)

  @overload()
  def __init__(self) -> None:
    """Initialize Size with default values."""
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
