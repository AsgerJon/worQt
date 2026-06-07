"""
ArrayLike subclasses 'tuple'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeVar, Generic, Iterator

from worktoy.desc import BaseDescriptor, Field
from worktoy.utilities import maybe
from worktoy.waitaminute import MissingVariable

T = TypeVar('T')

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeAlias, Optional, overload, SupportsIndex, Any

  from . import ArrayField

  MaybeField: TypeAlias = Optional[ArrayField | Iterable[T]]


class ArrayLike(tuple, Generic[T]):
  """
  ArrayLike subclasses 'tuple'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __owning_field__: Optional[ArrayField] = None
  __owning_document__: Optional[Any] = None

  #  Public Variables
  owningField: Field[ArrayField] = Field()
  owningDocument: Field[Any] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @owningField.GET
  def _getOwningField(self, ) -> ArrayField:
    if self.__owning_field__ is None:
      from . import ArrayField
      raise MissingVariable(self, '__owning_field__', ArrayField)
    return self.__owning_field__

  @owningDocument.GET
  def _getOwningDocument(self, ) -> Any:
    if self.__owning_document__ is None:
      from . import AbstractDocument
      raise MissingVariable(self, '__owning_document__', AbstractDocument)
    return self.__owning_document__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  PyCharm, WYD?
  # noinspection PyTypeChecker
  def __new__(cls, arg: MaybeField = None, **kwargs) -> Self:
    if isinstance(arg, BaseDescriptor):
      self = super().__new__(cls, ())
      self.__owning_field__ = arg
      return self
    return super().__new__(cls, maybe(arg, ()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  if TYPE_CHECKING:  # pragma: no cover
    # @formatter:off
    @overload
    def __getitem__(self, item: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, item: slice) -> Self: ...
    def __getitem__(self, item: SupportsIndex | slice) -> T | Self: ...
    def __iter__(self, ) -> Iterator[T]: ...
    # @formatter:on

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def append(self, value: T) -> None:
    self.owningField.append(self.owningDocument, value)

  def extend(self, values: Iterable[T]) -> None:
    self.owningField.extend(self.owningDocument, values)
