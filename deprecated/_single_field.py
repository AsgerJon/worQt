"""
SingleField subclasses 'AttriBox' from the 'worktoy.desc' module and
provides a single value field in an application document or project.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, Generic

from worktoy.desc import Field, AttriBox
from worktoy.waitaminute import SubclassException, TypeException

from deprecated.codecs import AbstractCodec

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Type, Union, Optional, Self

  from worQt.data import SingleField

  CodecType: TypeAlias = Union[Type[AbstractCodec], AbstractCodec]
  Cls: TypeAlias = Type[SingleField]

T = TypeVar('T')


class SingleField(AttriBox, Generic[T]):
  """
  SingleField subclasses 'AttriBox' from 'worktoy.desc' and provides a
  single value field in an application document or project.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_codec__: Type[AbstractCodec] = AbstractCodec

  #  Private Variables
  __codec_type__: Optional[Type[AbstractCodec]] = None
  __codec_object__: Optional[AbstractCodec] = None

  #  Public Variables
  codecType: Field[Type[AbstractCodec]] = Field()
  codec: Field[CodecType] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @codecType.GET
  def _getCodecType(self, **kwargs) -> Type[AbstractCodec]:
    if self.__codec_type__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__codec_type__ = self.__fallback_codec__
      return self._getCodecType(_recursion=True)
    if not isinstance(self.__codec_type__, type):
      raise TypeException('__codec_type__', self.__codec_type__, type)
    if issubclass(self.__codec_type__, AbstractCodec):
      return self.__codec_type__
    raise SubclassException(self.__codec_type__, AbstractCodec)

  @codec.GET
  def _getCodec(self, **kwargs) -> AbstractCodec:
    if self.__codec_object__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__codec_object__ = self.codecType()
      return self._getCodec(_recursion=True)
    if isinstance(self.__codec_object__, AbstractCodec):
      return self.__codec_object__
    name, value = '__codec_object__', self.__codec_object__,
    raise TypeException(name, value, AbstractCodec)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, codecType: CodecType) -> Self:
    if not isinstance(codecType, type):
      raise TypeException('codecType', codecType, type)
    if issubclass(codecType, AbstractCodec):
      superFunc = AttriBox.__class_getitem__
      superFunc: Callable = getattr(superFunc, '__func__', superFunc)
      self = superFunc(cls, codecType.valueType)
      self.__codec_type__ = codecType
      return self
    raise SubclassException(codecType, AbstractCodec)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  REQUIRED METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
