"""
AbstractField subclasses 'BaseDescriptor' and carries the machinery shared
by every document field: the element type, the per-element encoder/decoder
lookup against the owning document, registration on the document, and the
clone-on-subclass behaviour. Concrete fields ('SingleField', 'MultiField')
add only the value-shape specifics: how a value is held, type-checked, and
encoded or decoded.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from worktoy.waitaminute import MissingVariable, TypeException
from worktoy.desc import Field, BaseDescriptor
from worktoy.mcls import BaseMeta

T = TypeVar('T')

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias, Self, Type, cast

  from . import AbstractDocument

  Encoder: TypeAlias = Callable[[Any, T], str]
  Decoder: TypeAlias = Callable[[Any, str], T]
  DocType: TypeAlias = Type[AbstractDocument]


class AbstractField(BaseDescriptor[T], metaclass=BaseMeta):
  """
  Shared base for document fields.

  Holds the element type and the encoder/decoder contract (each resolved by
  name against the owning document), registers itself on the document, and
  clones per subclass on first access from a subclass owner. Concrete
  subclasses implement '__call__', 'encode', 'decode', '__instance_get__'
  and '__instance_set__' for their value shape.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_value__: Optional[Any] = None

  #  Private Variables
  __value_type__: Optional[type] = None
  __encode_key__: Optional[str] = None
  __decode_key__: Optional[str] = None
  __cached_encoder__: Optional[Encoder] = None
  __cached_decoder__: Optional[Decoder] = None

  #  Public Variables
  valueType: Field[type] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getEncodeKey(self, ) -> str:
    if self.__encode_key__ is None:
      raise MissingVariable(self, '__encode_key__', str)
    if isinstance(self.__encode_key__, str):
      return self.__encode_key__
    raise TypeException('__encode_key__', self.__encode_key__, str)

  def _getDecodeKey(self, ) -> str:
    if self.__decode_key__ is None:
      raise MissingVariable(self, '__decode_key__', str)
    if isinstance(self.__decode_key__, str):
      return self.__decode_key__
    raise TypeException('__decode_key__', self.__decode_key__, str)

  @valueType.GET
  def _getValueType(self, ) -> Type[T]:
    if self.__value_type__ is None:
      raise MissingVariable(self, '__value_type__', type)
    if isinstance(self.__value_type__, type):
      if TYPE_CHECKING:  # pragma: no cover
        return cast(Type[T], self.__value_type__)
      else:
        return self.__value_type__
    raise TypeException('__value_type__', self.__value_type__, type)

  def _cacheEncoderFunction(self, ) -> None:
    owner = self.getFieldOwner()
    key = self._getEncodeKey()
    self.__cached_encoder__ = getattr(owner, key)

  def _getEncoderFunction(self, **kwargs) -> Encoder:
    if self.__cached_encoder__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._cacheEncoderFunction()
      return self._getEncoderFunction(_recursion=True)
    if callable(self.__cached_encoder__):
      return self.__cached_encoder__
    name, value = '__cached_encoder__', self.__cached_encoder__
    raise TypeException(name, value, Callable)

  def _cacheDecoderFunction(self, ) -> None:
    owner = self.getFieldOwner()
    key = self._getDecodeKey()
    self.__cached_decoder__ = getattr(owner, key)

  def _getDecoderFunction(self, **kwargs) -> Decoder:
    if self.__cached_decoder__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._cacheDecoderFunction()
      return self._getDecoderFunction(_recursion=True)
    if callable(self.__cached_decoder__):
      return self.__cached_decoder__
    name, value = '__cached_decoder__', self.__cached_decoder__
    raise TypeException(name, value, Callable)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setEncodeKey(self, value: str, ) -> None:
    if not isinstance(value, str):
      raise TypeException('value', value, str)
    self.__encode_key__ = value

  def _setDecodeKey(self, value: str, ) -> None:
    if not isinstance(value, str):
      raise TypeException('value', value, str)
    self.__decode_key__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DECORATORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setEncoder(self, encoder: Encoder) -> Encoder:
    self._setEncodeKey(encoder.__name__)
    return encoder

  def setDecoder(self, decoder: Decoder) -> Decoder:
    self._setDecodeKey(decoder.__name__)
    return decoder

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, valueType: type) -> Self:
    if not isinstance(valueType, type):
      raise TypeException('valueType', valueType, type)
    self = cls()
    setattr(self, '__value_type__', valueType)
    return self

  def __get__(self, instance: Any, docType: DocType, **kwargs) -> Any:
    owner = self.getFieldOwner()
    if docType is not owner:
      if kwargs.get('_recursion', False):
        raise RecursionError
      clone = self._clone(self)
      name = self.getFieldName()
      if name is None:
        raise MissingVariable(self, '__field_name__', str)
      setattr(docType, name, clone)
      clone.__set_name__(docType, name)
      return clone.__get__(instance, docType, _recursion=True)
    return BaseDescriptor.__get__(self, instance, docType)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _clone(cls, other: Self) -> Self:
    self = cls()
    keys = (
      '__value_type__',
      '__fallback_value__',
      '__encode_key__',
      '__decode_key__'
    )
    for key in keys:
      setattr(self, key, getattr(other, key))
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _notifyChange(self, instance: Any, **kwargs) -> None:
    """Hook fired when this field's value changes on 'document'. A no-op by
    default; a later modification channel (dirty flag, undo stack, change
    signal) connects here."""
