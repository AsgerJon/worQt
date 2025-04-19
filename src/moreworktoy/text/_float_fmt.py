"""FloatFmt provides a class formatting float values to an appropriate str
format. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from random import random, gauss

from worktoy.ezdata import EZData
from worktoy.parse import maybe
from worktoy.text import typeMsg

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

from worktoy.attr import Field, AttriBox
from worktoy.mcls import BaseObject
from worktoy.static import overload, THIS

if TYPE_CHECKING:
  from typing import Self


class _Float:
  """_Float provides a class formatting float values to an appropriate str
  format. """

  __mantissa_value__ = None
  __exponent_value__ = None

  def getMantissa(self) -> float:
    """Get the mantissa value."""
    return maybe(self.__mantissa_value__, 0.0)

  def getExponent(self) -> int:
    """Get the exponent value."""
    return maybe(self.__exponent_value__, 0)

  @classmethod
  def _log10ceil(cls, value: float) -> int:
    """Get the log10 value."""
    if not value:
      raise ZeroDivisionError
    if value < 0:
      return cls._log10ceil(-1 * value)
    if value == 1:
      return 0
    if value < 1:
      return -1 * cls._log10ceil(1 / value) + 1
    out = 0
    while value > 10 ** out:
      out += 1
      if out > 64:
        raise RecursionError
    else:
      return out

  def __float__(self, ) -> float:
    """Convert the object to a float."""
    return self.getMantissa() * (10 ** self.getExponent())

  def __int__(self, ) -> int:
    """Convert the object to an int."""
    return int(self.__float__())

  def __bool__(self, ) -> bool:
    """Convert the object to a bool."""
    return bool(self.__float__())

  def __init__(self, value: float) -> None:
    self.__exponent_value__ = self._log10ceil(value)
    self.__mantissa_value__ = value / (10 ** self.__exponent_value__)


class FloatFmt(BaseObject):
  """FloatFmt provides a class formatting float values to an appropriate str
  format. """

  #  fallback values
  __fallback_significant_digits__ = 12
  __fallback_digit_increment__ = 3

  #  private values
  __num_significant_digits__ = None
  __num_digit_increment__ = None

  #  public values
  significantDigits = Field()
  digitIncrement = Field()

  #  Getter functions
  @significantDigits.GET
  def _getSignificantDigits(self) -> int:
    """Get the number of significant digits."""
    if self.__num_significant_digits__ is None:
      return self.__fallback_significant_digits__
    return self.__num_significant_digits__

  @digitIncrement.GET
  def _getDigitIncrement(self) -> int:
    """Get the digit increment."""
    if self.__num_digit_increment__ is None:
      return self.__fallback_digit_increment__
    return self.__num_digit_increment__

  #  Setter functions
  @significantDigits.SET
  def _setSignificantDigits(self, value: int) -> None:
    """Set the number of significant digits."""
    if not isinstance(value, int):
      raise TypeError(typeMsg('value', value, int))
    self.__num_significant_digits__ = value

  @digitIncrement.SET
  def _setDigitIncrement(self, value: int) -> None:
    """Set the digit increment."""
    if not isinstance(value, int):
      raise TypeError(typeMsg('value', value, int))
    self.__num_digit_increment__ = value

  def apply(self, value: float) -> str:
    """Apply the formatting to the value and return the formatted string. """
    floatObject = _Float(value)
    mantissa = floatObject.getMantissa()
    exponent = floatObject.getExponent()
