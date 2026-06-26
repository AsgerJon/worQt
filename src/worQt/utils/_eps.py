"""
Eps exposes sys.float_info.epsilon as a descriptor.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations
import sys
from typing import TYPE_CHECKING, Never

from worktoy.waitaminute.desc import ReadOnlyError, ProtectedError

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any


class Eps:
  """
  Eps exposes sys.float_info.epsilon as a descriptor.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __field_name__ = None
  __field_owner__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: type, name: str) -> None:
    self.__field_name__ = name
    self.__field_owner__ = owner

  def __get__(self, instance: Self, owner: type) -> Any:
    if instance is None:
      return self
    return sys.float_info.epsilon

  def __set__(self, instance: Any, value: Any) -> Never:
    raise ReadOnlyError(instance, self, value)

  def __delete__(self, instance: Any) -> Never:
    try:
      oldValue = self.__get__(instance, type(instance), )
    except Exception as exception:  # pragma: no cover
      raise ProtectedError(instance, self) from exception  # __get__ is total
    else:
      raise ProtectedError(instance, self, oldValue)

  def __str__(self, ) -> str:
    if self.__field_owner__ is None:
      return """sys.float_info.epsilon: %f""" % sys.float_info.epsilon
    infoSpec = """%s.%s: %f"""
    ownerName = self.__field_owner__.__name__
    fieldName = self.__field_name__
    return infoSpec % (ownerName, fieldName, sys.float_info.epsilon)

  def __repr__(self, ) -> str:
    return 'sys.float_info.epsilon'
