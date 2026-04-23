"""
MarginSizes encapsulates margin sizes used by the box model.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

import sys

from PySide6.QtCore import QMarginsF, QMargins
from worktoy.desc import Field
from worktoy.ezdata import EZData
from worktoy.utilities import typeCast
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.dispatch import TypeCastException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Any, Type, TypeAlias, Union, Self

  Ints: TypeAlias = Union[int, tuple[int, ...]]

eps = sys.float_info.epsilon


class _Field:
  __private_name__ = None
  __default_value__ = None

  def __init__(self, pvtName: str, defVal: Any = None) -> None:
    self.__private_name__ = pvtName
    self.__default_value__ = defVal

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    if self.__default_value__ is None:
      return getattr(instance, self.__private_name__, )
    return getattr(instance, self.__private_name__, self.__default_value__)


class _Keys:
  __main_key__ = None
  __key_variants__ = None

  main = _Field('__main_key__', )

  def __init__(self, *args, ) -> None:
    self.__key_variants__ = [arg for arg in args if isinstance(arg, str)]
    if self.__key_variants__:
      self.__main_key__ = self.__key_variants__[0]

  def __contains__(self, key: str) -> bool:
    return True if key in self.__key_variants__ else False

  def __get__(self, instance: Any, owner: type) -> Any:
    return self

  def __iter__(self, ) -> Iterator[str]:
    if self.__key_variants__ is None:
      return
    yield from self.__key_variants__


class _Group:
  __key_groups__ = None

  def __init__(self, *args, ) -> None:
    self.__key_groups__ = [arg for arg in args if isinstance(arg, _Keys)]

  def __iter__(self, ) -> Iterator[_Keys]:
    if self.__key_groups__ is None:
      return
    yield from self.__key_groups__

  def __get__(self, instance: Any, owner: type) -> Any:
    return self


class MarginSizes(EZData, frozen=True):
  """
  MarginSizes encapsulates margin sizes used by the box model.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __left_keys__ = _Keys('left', 'l', ' Left ', ' LEFT ')
  __top_keys__ = _Keys('top', 't', ' Top ', ' TOP ')
  __right_keys__ = _Keys('right', 'r', ' Right ', ' RIGHT ')
  __bottom_keys__ = _Keys('bottom', 'b', ' Bottom ', ' BOTTOM ')
  __key_groups__ = _Group(
    __left_keys__,
    __top_keys__,
    __right_keys__,
    __bottom_keys__
  )

  #  Public Variables
  left = 0
  top = 0
  right = 0
  bottom = 0

  #  Virtual Variables
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQ(self, ) -> QMargins:
    return QMargins(*self, )

  @QF.GET
  def _getQF(self, ) -> QMarginsF:
    return QMarginsF(*self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[int]:
    yield self.left
    yield self.top
    yield self.right
    yield self.bottom

  def __len__(self, ) -> int:
    return 4

  def __bool__(self, ) -> bool:
    return True if any(self) else False

  def __eq__(self, other: Any) -> bool:
    if other is self:
      return True
    otherResolved = self._resolveOther(other)
    if otherResolved is NotImplemented:
      return NotImplemented
    return all(s == o for s, o in zip(self, otherResolved, ))

  def __hash__(self) -> int:
    return hash((*self,))

  def _rollIndex(self, index: int) -> int:
    if index < 0:
      return self._rollIndex(len(self) + index)
    if index < len(self):
      return index
    infoSpec = """Index '%s' is out of range for '%s' objects having 
    length: '%d'!"""
    clsName = type(self).__name__
    info = infoSpec % (index, clsName, len(self),)
    raise IndexError(info)

  def _resolveIndex(self, index: int) -> int:
    return (*self,)[self._rollIndex(index)]

  def _resolveSlice(self, slice_: slice) -> tuple[int, ...]:
    return (*self,)[slice_]

  def _resolveKey(self, key: str, **kwargs) -> int:
    for group in self.__key_groups__:
      if key in group:
        return getattr(self, group.main)
    recursionKey = kwargs.get('_recursionKey', False)
    if recursionKey:
      raise KeyError(recursionKey)
    return self._resolveKey(key.lower(), _recursionKey=key)

  def __getitem__(self, identifier: Any) -> Ints:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, slice):
      return self._resolveSlice(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    name, value = 'identifier', identifier
    raise TypeException(name, value, int, slice, str)

  def __contains__(self, key: str) -> bool:
    if isinstance(key, str):
      try:
        _ = self._resolveKey(key)
      except KeyError:
        return False
      else:
        return True
    return False

  def _resolveOther(self, other: Any) -> Self:
    cls = type(self)
    if isinstance(other, cls):
      return other
    if isinstance(other, (list, tuple,)):
      try:
        out = cls(*other, )
      except (ValueError, TypeError,):
        return NotImplemented
      else:
        return out
    if isinstance(other, dict):
      for group in self.__key_groups__:
        for key in group:
          if key in other:
            if isinstance(other[key], int):
              break
            if isinstance(other[key], float):
              if float.is_integer(other[key]):
                break
            return NotImplemented
        else:
          return NotImplemented
      try:
        out = cls(**other, )
      except (ValueError, TypeError,):
        return NotImplemented
      else:
        return out
    return NotImplemented

  def __add__(self, other: Any) -> Self:
    otherResolved = self._resolveOther(other)
    if otherResolved is NotImplemented:
      return NotImplemented
    cls = type(self)
    return cls(
      self.left + otherResolved.left,
      self.top + otherResolved.top,
      self.right + otherResolved.right,
      self.bottom + otherResolved.bottom,
    )

  def __radd__(self, other: Any) -> Self:
    cls = type(self)
    try:
      otherInt = typeCast(int, other)
    except TypeCastException as typeCastException:
      if typeCastException.type_ is int and typeCastException.arg == other:
        pass
      else:
        raise typeCastException
    else:
      return self + cls(*(4 * [otherInt, ]), )
    other_ = self._resolveOther(other)
    if other_ is NotImplemented:
      return NotImplemented
    return other_ + self

  def __iadd__(self, other: Any) -> Self:  # immutable
    return self + other

  def __neg__(self, ) -> Self:
    cls = type(self)
    return cls(*[-i for i in self], )

  def __sub__(self, other: Any) -> Self:
    return self + (-other)

  def __rsub__(self, other: Any) -> Self:
    return (-self) + other

  def __isub__(self, other: Any) -> Self:  # immutable
    return self - other

  def __mul__(self, other: Any) -> Self:
    """
    The implementation supports scaling. If 'other' is a float, the scaled
    dimensions are rounded to the nearest integer.
    """
    try:
      otherFloat = typeCast(float, other)
    except TypeCastException as typeCastException:
      if typeCastException.type_ is float and typeCastException.arg == other:
        return NotImplemented
      else:
        raise typeCastException
    else:
      cls = type(self)
      return cls(*[round(i * otherFloat) for i in self], )

  def __rmul__(self, other: Any) -> Self:
    return self * other

  def __imul__(self, other: Any) -> Self:  # immutable
    return self * other

  def __truediv__(self, other: Any) -> Self:
    try:
      otherFloat = typeCast(float, other)
    except TypeCastException as typeCastException:
      if typeCastException.type_ is float and typeCastException.arg == other:
        return NotImplemented
      else:
        raise typeCastException
    else:
      if otherFloat ** 2 < eps:
        raise ZeroDivisionError
      cls = type(self)
      return cls(*[round(i / otherFloat) for i in self], )

  def __itruediv__(self, other: Any) -> Self:  # immutable
    return self / other

  def __rtruediv__(self, other: Any) -> Self:
    return NotImplemented

  def __floordiv__(self, other: Any) -> Self:
    return self.__truediv__(other)

  def __ifloordiv__(self, other: Any) -> Self:  # immutable
    return self // other

  def __rfloordiv__(self, other: Any) -> Self:
    return NotImplemented

  def __mod__(self, other: Any) -> Self:
    try:
      otherInt = typeCast(int, other)
    except TypeCastException as typeCastException:
      if typeCastException.type_ is int and typeCastException.arg == other:
        return NotImplemented
      else:
        raise typeCastException
    else:
      if otherInt:
        cls = type(self)
        return cls(*[i % otherInt for i in self], )
      raise ZeroDivisionError

  def __imod__(self, other: Any) -> Self:  # immutable
    return self % other

  def __rmod__(self, other: Any) -> Self:
    return NotImplemented

  def __str__(self, ) -> str:
    infoSpec = """<%s: left=%d, top=%d, right=%d, bottom=%d>"""
    clsName = type(self).__name__
    return infoSpec % (clsName, *self,)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d, %d, %d, %d)"""
    clsName = type(self).__name__
    return infoSpec % (clsName, *self,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
