"""
EuclideanObject provides the base class for math objects representing points,
rectangles, vectors, and similar geometric entities.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ... import Eps
from . import EuclidianMetaclass

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Self, Optional, Type, Iterator
  from typing import overload as underload

  NotImplementedType: TypeAlias = Type[NotImplemented]
  SelfIfImplemented: TypeAlias = Union[Self, NotImplementedType]

  Identifier: TypeAlias = Union[int, str, slice]
  Int = Union[int, tuple[int, ...]]


class EuclideanObject(metaclass=EuclidianMetaclass):
  """
  EuclideanObject provides the base class for math objects representing
  points, rectangles, vectors, and similar geometric entities.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  eps = Eps()

  #  Annotations
  if TYPE_CHECKING:  # pragma: no cover
    @underload
    def __add__(self, other: Self) -> Self: ...

    @underload
    def __add__(self, other: float) -> Self: ...

    def __add__(self, other: int) -> Self: ...

    @underload
    def __sub__(self, other: Self) -> Self: ...

    @underload
    def __sub__(self, other: float) -> Self: ...

    def __sub__(self, other: int) -> Self: ...

    @underload
    def __mul__(self, other: float) -> Self: ...

    @underload
    def __mul__(self, other: float) -> Self: ...

    def __mul__(self, other: int) -> Self: ...

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _resolveOther(cls, other: Self) -> SelfIfImplemented:
    if isinstance(other, cls):
      return other
    try:
      out = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return out

  def __abs__(self, ) -> float:
    out = 0
    for dim in self.getDimensions():
      out += getattr(self, dim.fieldName) ** 2
    return out ** 0.5

  def __bool__(self, ) -> bool:
    return True if abs(self) > self.eps else False

  def __eq__(self, other: Self) -> bool:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    for dim in self.getDimensions():
      left = getattr(self, dim.fieldName)
      right = getattr(other, dim.fieldName)
      if abs(left - right) > self.eps:
        return False
    return True
