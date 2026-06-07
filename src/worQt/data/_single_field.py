"""
SingleField subclasses 'AbstractField' and provides a singularly valued
field in the document.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic

from worktoy.waitaminute import TypeException

from . import AbstractField

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self

T = TypeVar('T')


class SingleField(AbstractField, Generic[T]):
  """
  A field holding a single value of a given type. The value round-trips
  through a document method receiving '(document, value)'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  if TYPE_CHECKING:  # pragma: no cover
    #  Runtime builds the field via the inherited '__class_getitem__'
    #  factory plus '__call__'; this stub only teaches the type checker
    #  that 'SingleField[T](value)' yields a 'SingleField[T]'.
    def __init__(self, value: T) -> None: ...

  def __call__(self, value: T, **kwargs) -> Self:
    if not isinstance(value, self.valueType):
      raise TypeException('value', value, self.valueType)
    setattr(self, '__fallback_value__', value)
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any, value: T, **kwargs) -> str:
    encoder = self._getEncoderFunction()
    return encoder(instance, value)

  def decode(self, instance: Any, value: str, **kwargs) -> Any:
    decoder = self._getDecoderFunction()
    return decoder(instance, value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, instance: Any, owner: type, **kwargs) -> Any:
    pvtName = self.getPrivateName()
    try:
      value = getattr(self.instance, pvtName)
    except AttributeError as attributeError:
      if kwargs.get('_recursion', False):
        raise RecursionError from attributeError
      self.__instance_set__(instance, self.__fallback_value__)
      return self.__instance_get__(instance, owner, _recursion=True)
    else:
      valueType = self._getValueType()
      if isinstance(value, valueType):
        return value
      raise TypeException(pvtName, value, valueType)

  def __instance_set__(self, instance: Any, value: Any, **kwargs) -> None:
    if not isinstance(value, self.valueType):
      raise TypeException('value', value, self.valueType)
    setattr(self.instance, self.getPrivateName(), value)
