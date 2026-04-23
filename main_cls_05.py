"""
breh
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.utilities import textFmt

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, Type, TypeAlias, Self, Never

  MaybeInt: TypeAlias = Optional[int]


class INF(int):
  __num_sign__: MaybeInt = None

  def __new__(cls, value: int = None) -> Self:
    if value is None:
      return 0
    return super().__new__(cls, value)

  def __init__(self, value: int) -> None:
    self.__num_sign__ = 1 if value > 0 else -1

  def __add__(self, other: Any) -> Self:
    cls = type(self)
    if type(other) is cls:
      if self is not other:
        info = """The sum of positive and negative infinity is undefined!"""
        raise ValueError(info)
    return cls(self.__num_sign__)

  def __sub__(self, other: Any) -> Self:
    cls = type(self)
    if type(other) is cls:
      if self is other:
        info = """The difference of positive and positive infinity is 
        undefined!"""
        raise ValueError(textFmt(info))
    return cls(self.__num_sign__)

  def __pos__(self) -> Self:
    return type(self)(self.__num_sign__)

  def __neg__(self, ) -> Self:
    return type(self)(-self.__num_sign__)

  def __mul__(self, other: Any) -> Self:
    cls = type(self)
    if type(other) is cls:
      return cls(self.__num_sign__ * other.__num_sign__)
    return cls(self.__num_sign__ * (1 if other > 0 else -1))

  def __truediv__(self, other: Any) -> Self:
    cls = type(self)
    if type(other) is cls:
      info = """The quotient of infinity and infinity is undefined!"""
      raise ValueError(textFmt(info))
    return self * other

  def __rtruediv__(self, other: Any) -> Self:
    cls = type(self)
    if type(other) is cls:
      info = """The quotient of infinity and infinity is undefined!"""
      raise ValueError(textFmt(info))
    sign = other * self.__num_sign__ / abs(other)
    return sign / float('inf')

  def __mod__(self, other: Any) -> Never:
    raise TypeError("Modulo operation is not defined for infinity!")

  def __rmod__(self, other: Any) -> Self:
    return other / self

  def __eq__(self, other: Any) -> bool:
    return True if self is other else False

  def __le__(self, other: Any) -> bool:
    return True if self.__num_sign__ < 0 else False

  def __ge__(self, other: Any) -> bool:
    return True if self.__num_sign__ > 0 else False

  def __lt__(self, other: Any) -> bool:
    return False if self is other else (self <= other)

  def __gt__(self, other: Any) -> bool:
    return False if self is other else (self >= other)
