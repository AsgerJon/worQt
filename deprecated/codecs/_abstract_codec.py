"""
AbstractCodec subclasses 'BaseObject' from the 'worktoy.mcls' module and
provides a base class for codecs encoding and decoding.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic, overload

from worktoy.desc import Field
from worktoy.mcls import BaseObject, BaseSpace
from worktoy.utilities import typeCast
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.dispatch import TypeCastException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Union, Optional, Type, TypeAlias

  Bases: TypeAlias = tuple[type, ...]

T = TypeVar('T')


class AbstractCodec(BaseObject, Generic[T]):
  """
  AbstractCodec subclasses 'BaseObject' from the 'worktoy.mcls' module and
  provides a base class for codecs encoding and decoding.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_type__: type = str

  #  Private Variables
  __inner_value__: Optional[T] = None

  #  Public Variables
  valueType: Field[type] = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _classGetValueType(cls, ) -> type:
    """
    Subclasses must override *this* method when specifying the value type.
    """
    return cls.__fallback_type__

  @valueType.GET
  def _getValueType(self, **kwargs) -> type:
    """
    Subclasses should *not* override this method, but should instead
    override the classmethod: '_classGetValueType'.
    """
    return self._classGetValueType()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _cast(self, obj: Any, **kwargs) -> Any:
    """
    This is a helper method subclasses can reimplement to provide more
    particular type casting logic. For example casting 'QPoint' to an
    application specific plane point encapsulation.
    """
    try:
      casted = typeCast(self.valueType, obj, allowInstantiation=True)
    except TypeCastException as typeCastException:
      raise TypeException('obj', obj, self.valueType) from typeCastException
    else:
      return casted

  def _encode(self, obj: Any, **kwargs) -> str:
    """
    This is the method subclasses should override to specify particular
    encoding logic. This default implementation simply passes the object
    received through the type guard and then passes it to the 'str'
    constructor.
    """
    casted = self._cast(obj, **kwargs)
    return str(casted)

  def _decode(self, obj: Any, **kwargs) -> int:
    return self._cast(obj, **kwargs)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, value: Any, **kwargs) -> str:
    """
    This is the public API. Subclass must *not* override this method,
    but should instead override the '_encode' method.
    """
    return self._encode(value, **kwargs)

  def decode(self, raw: str, **kwargs) -> Any:
    """
    This is the public API. Subclass must *not* override this method,
    but should instead override the '_decode' method.
    """
    return self._decode(raw, **kwargs)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, type_: type) -> Type[AbstractCodec]:

    class _Codec(cls, _root=True):
      @classmethod
      def _classGetValueType(cls, ) -> type:
        return type_

    return _Codec

  if TYPE_CHECKING:  # pragma: no cover
    # @formatter:off
    @overload
    def __get__(self, instance: None, owner: type) -> Self: ...
    @overload
    def __get__(self, instance: Any, owner: type) -> T: ...
    def __get__(self, instance: Any, owner: type) -> Union[Self, T]: ...
    # @formatter:on

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
