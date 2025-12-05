"""
OKLab color space implementation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

from . import AbstractColor

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Never


def _relu(x: float) -> float:
  return 0 if x < 0 else x


class OKLabColor(AbstractColor):
  """
  OKLab color space implementation.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_lightness__ = 0.5
  __fallback_a__ = 1.0
  __fallback_b__ = 1.0

  #  Private Variables
  __light_value__ = None
  __a_value__ = None
  __b_value__ = None

  #  Public Variables
  L: float = Field()
  a: float = Field()
  b: float = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @L.GET  # noqa
  def _getL(self, **kwargs) -> float:
    if self.__light_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__light_value__ = self.__fallback_lightness__
      return self._getL(_recursion=True)
    if isinstance(self.__light_value__, float):
      if 0 <= self.__light_value__ <= 1:
        return self.__light_value__
      infoSpec = """Expected lightness channel to be in range 0-1,
      but received '%f'!"""
      info = infoSpec % self.__light_value__
      raise ValueError(textFmt(info))
    raise TypeException('__light_value__', self.__light_value__, float)

  @a.GET  # noqa
  def _getA(self, **kwargs) -> float:
    if self.__a_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__a_value__ = self.__fallback_a__
      return self._getA(_recursion=True)
    if isinstance(self.__a_value__, float):
      if 0 <= self.__a_value__ <= 1:
        return self.__a_value__
      infoSpec = """Expected 'a' channel to be in range 0-1,
      but received '%f'!"""
      info = infoSpec % self.__a_value__
      raise ValueError(textFmt(info))
    raise TypeException('__a_value__', self.__a_value__, float)

  @b.GET  # noqa
  def _getB(self, **kwargs) -> float:
    if self.__b_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__b_value__ = self.__fallback_b__
      return self._getB(_recursion=True)
    if isinstance(self.__b_value__, float):
      if 0 <= self.__b_value__ <= 1:
        return self.__b_value__
      infoSpec = """Expected 'b' channel to be in range 0-1,
      but received '%f'!"""
      info = infoSpec % self.__b_value__
      raise ValueError(textFmt(info))
    raise TypeException('__b_value__', self.__b_value__, float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getRed(self, **kwargs) -> int:
    """
    Convert to sRGB red channel.
    """
    raise NotImplementedError

  def _getGreen(self, **kwargs) -> int:
    """
    Convert to sRGB green channel.
    """
    raise NotImplementedError

  def _getBlue(self, **kwargs) -> int:
    """
    Convert to sRGB blue channel.
    """
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __mod__(self, other: Self) -> float:
    w = 4 * (self.L * (1 - self.L) * other.L * (1 - other.L)) ** 0.5
    dA, dB = (self.a - other.a) ** 2, (self.b - other.b) ** 2
    d = w ** 2 * (dA + dB)
    return ((self.L - other.L) ** 2 + d) ** 0.5
