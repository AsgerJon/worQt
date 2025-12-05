"""
BaseDim provides a base for multi-dimensional classes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Callable, Iterator


class BaseDim(BaseObject):
  """
  BaseDim provides a base for multi-dimensional classes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_value__ = 0

  #  Private Variables
  __dim_values__ = None

  #  Public Variables
  values = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @values.GET
  def _getValues(self, **kwargs) -> tuple[int, ...]:
    if self.__dim_values__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      values = [self.__fallback_value__, ] * len(self)
      self.__dim_values__ = (*values,)
      return self._getValues(_recursion=True)
    return self.__dim_values__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __len__(self, ) -> int:
    raise NotImplementedError

  def __iter__(self, **kwargs) -> Iterator[int]:
    yield from self.values

  def __eq__(self, other: Any) -> bool:
    cls = type(self)
    if cls is not type(other):
      return NotImplemented
    for selfValue, otherValue in zip(self, other):
      if abs(selfValue - otherValue) > 1e-06:
        return False
    return True

  def __ne__(self, other: Any) -> bool:
    cls = type(self)
    if cls is not type(other):
      return NotImplemented
    for selfValue, otherValue in zip(self, other):
      if abs(selfValue - otherValue) > 1e-06:
        return True
    return False

  def __hash__(self, ) -> int:
    return hash(self.values)

  def __getitem__(self, identifier: Any) -> int:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    raise TypeException('identifier', identifier, int, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload()
  def __init__(self, ) -> None:
    pass

  @overload(tuple)
  def __init__(self, values: tuple[int, ...]) -> None:
    self.__dim_values__ = values

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__dim_values__ = other.values

  @overload.fallback
  def __init__(self, *args, **kwargs) -> None:
    self.__dim_values__ = args

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _resolveOther(self, other: Any) -> Self:
    cls = type(self)
    if cls is type(other):
      return other
    try:
      other = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return other

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _resolveKey(self, key: str) -> int:
    """
    Subclasses may implement this method to resolve a string key to an
    element in the dimensional values. If not implemented, a TypeError is
    raised.
    """
    infoSpec = """'%s' object does not support 'str' indexing, 
    but received key '%s'!"""
    clsName = type(self).__name__
    info = textFmt(infoSpec % (clsName, key))
    raise TypeError(info)

  def _resolveIndex(self, index: int) -> int:
    """
    Integer indexing is implemented by default with support for negative
    indices such that -1 refers to the last element, -2 to the second last,
    and so forth.
    """
    if index < 0:
      return self._resolveIndex(len(self) + index)
    if index < len(self):
      return self.values[index]
    raise IndexError(index)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
