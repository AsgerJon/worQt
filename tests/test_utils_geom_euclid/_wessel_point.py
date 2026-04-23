"""
WesselPoint implements complex numbers as geometric points in Euclidean
space. The class is named after Caspar Wessel. Wessel was a Norwegian-Danish
mathematician and cartographer who is credited with being one of the first to
represent complex numbers geometrically in the two-dimensional Cartesian
coordinates.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from random import random
from math import atan2
from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload

from worQt.utils.geom.euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Callable, Iterator


class WesselPoint(EuclideanObject):
  """
  WesselPoint implements complex numbers as geometric points in Euclidean
  space. The class is named after Caspar Wessel. Wessel was a
  Norwegian-Danish mathematician and cartographer who is credited with
  being one of the first to represent complex numbers geometrically in the
  two-dimensional Cartesian coordinates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  x = Dimension(float, .0, 'real', )
  y = Dimension(float, .0, 'imaginary', 'imag')

  #  Virtual Variables
  r = Field()
  t = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @r.GET
  def _getR(self, ) -> float:
    return (self.x ** 2 + self.y ** 2) ** 0.5

  @t.GET
  def _getT(self, ) -> float:
    out = atan2(self.y, self.x)
    if isinstance(out, complex):
      return out.real
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __mul__(self, other: Self) -> Self:
    cls = type(self)
    selfComplex = self.x + 1j * self.y
    otherComplex = other.x + 1j * other.y
    resultComplex = selfComplex * otherComplex
    return cls(resultComplex.real, resultComplex.imag)

  @overload(complex)
  def __mul__(self, other: complex) -> Self:
    cls = type(self)
    selfComplex = self.x + 1j * self.y
    resultComplex = selfComplex * other
    return cls(resultComplex.real, resultComplex.imag)

  @overload(complex)
  def __add__(self, other: complex) -> Self:
    cls = type(self)
    return self + cls(other)

  @overload(complex)
  def __sub__(self, other: complex) -> Self:
    cls = type(self)
    return self - cls(other)

  def __invert__(self, ) -> Self:
    return type(self)(self.x, -self.y)

  def __abs__(self, ) -> float:
    sqr = self * ~self
    return sqr.x ** 0.5

  def __str__(self, ) -> str:
    if abs(self.x) > self.eps and abs(self.y) > self.eps:
      sign = '+' if self.y >= 0 else '-'
      infoSpec = """%s %s %sJ"""
      return infoSpec % (self.x, sign, abs(self.y))
    if abs(self.x) > self.eps:
      return str(self.x)
    if abs(self.y) > self.eps:
      return """%sJ""" % self.y
    return '0'

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(complex)
  def __init__(self, z: complex, **kwargs) -> None:
    self.__init__(z.real, z.imag, **kwargs)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def sample(cls, *args, ) -> Self:
    """Provides a sample instance of WesselPoint."""
    a, b, *_ = (*args, 0.0, 1.0)
    minVal, maxVal = min(a, b), max(a, b)
    x = minVal + random() * (maxVal - minVal)
    y = minVal + random() * (maxVal - minVal)
    return cls(x, y)

  @classmethod
  def samples(cls, n: int, *args, ) -> Iterator[Self]:
    """Provides a list of sample instances of WesselPoint."""
    for _ in range(n):
      yield cls.sample(*args)
