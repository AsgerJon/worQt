"""Tester classes"""
#  AGPL-3.0 license
#  Copyright (c) 2025-2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

import sys

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self

eps = sys.float_info.epsilon


class Number:
  __fallback_value__ = .0
  __inner_value__ = None

  def __init__(self, *args, ) -> None:
    for arg in args:
      if isinstance(arg, complex):
        if arg.imag ** 2 > eps:
          continue
        self.__inner_value__ = float(arg.real)
        break
      if isinstance(arg, (float, int)):
        self.__inner_value__ = float(arg)
        break
    else:
      self.__inner_value__ = self.__fallback_value__

  def _resolveOther(self, other: Any) -> Self:
    cls = type(self)
    if isinstance(other, cls):
      return other
    try:
      out = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return out

  def __add__(self, other: Self) -> Self:
    print('__add__', self, other)
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return cls(self.__inner_value__ + other.__inner_value__)

  def __radd__(self, other: Self) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self + other

  def __iadd__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    self.__inner_value__ += other.__inner_value__
    return self

  def __neg__(self, ) -> Self:
    cls = type(self)
    return cls(-self.__inner_value__)

  def __sub__(self, other: Self) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self + (-other)

  def __rsub__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return other + (-self)

  def __isub__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    self.__inner_value__ -= other.__inner_value__
    return self

  def __bool__(self, ) -> bool:
    return True if self.__inner_value__ ** 2 > eps else False

  def __invert__(self) -> Self:
    cls = type(self)
    if self:
      return cls(1 / self.__inner_value__)
    raise ZeroDivisionError

  def __complex__(self, ) -> complex:
    return self.__inner_value__ + 0j

  def __float__(self, ) -> float:
    return self.__inner_value__

  def __int__(self, ) -> int:
    return int(round(self.__inner_value__))

  def __eq__(self, other: Any) -> bool:
    cls = type(self)
    if isinstance(other, cls):
      return False if self - other else True
    try:
      out = True if self.__inner_value__ == other else False
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return out

  def __mul__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return cls(self.__inner_value__ * other.__inner_value__)

  def __imul__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    self.__inner_value__ *= other.__inner_value__
    return self

  def __rmul__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self * other

  def __truediv__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if not other:
      raise ZeroDivisionError
    return cls(self.__inner_value__ / other.__inner_value__)

  def __itruediv__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if not other:
      raise ZeroDivisionError
    self.__inner_value__ /= other.__inner_value__
    return self

  def __rtruediv__(self, other: Any) -> Self:
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if not self:
      raise ZeroDivisionError
    return cls(other.__inner_value__ / self.__inner_value__)

  def __str__(self, ) -> str:
    infoSpec = """%s[%s]"""
    name = type(self).__name__
    if float.is_integer(self.__inner_value__):
      value = '%d' % int(self.__inner_value__)
    else:
      value = '%s' % repr(self.__inner_value__)
    return infoSpec % (name, value)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%s)"""
    name = type(self).__name__
    if float.is_integer(self.__inner_value__):
      value = '%d' % int(self.__inner_value__)
    else:
      value = '%s' % repr(self.__inner_value__)
    return infoSpec % (name, value)
