"""
BaseScalar provides the base class for image to scalar field mappings.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type

  from .. import BaseRaster

  ImgType: TypeAlias = Type[BaseRaster]
  Image: TypeAlias = BaseRaster


class BaseScalar:
  """
  Scalar provides mappings from image tensors to scalar fields.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __field_owner__ = None
  __field_name__ = None
  __context_image__ = None

  #  Public Variables
  owner = Field()
  name = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @owner.GET
  def _getOwner(self, **kwargs) -> ImgType:
    if self.__field_owner__ is None:
      raise MissingVariable('__field_owner__')
    if isinstance(self.__field_owner__, type):
      if TYPE_CHECKING:  # pragma: no cover
        assert issubclass(self.__field_owner__, BaseRaster)
      return self.__field_owner__
    name, value = '__field_owner__', self.__field_owner__
    raise TypeException(name, value, type)

  @name.GET
  def _getName(self, **kwargs) -> str:
    if self.__field_name__ is None:
      raise MissingVariable('__field_name__')
    if isinstance(self.__field_name__, str):
      return self.__field_name__
    name, value = '__field_name__', self.__field_name__
    raise TypeException(name, value, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: ImgType, name: str, ) -> None:
    """
    Informs the descriptor instance of owning class and the name by which
    it appears in the owner.
    """
    self.__field_owner__ = owner
    self.__field_name__ = name

  def __get__(self, instance: Image, owner: ImgType) -> Any:
    """
    Returns the scalar field tensor mapped from the image tensor of the
    owning image instance.
    """
    if instance is None:
      return self
    return self._apply(instance.data)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _apply(self, operand: Tensor) -> Tensor:
    """
    Subclasses must implement this method. The base expects it to return a
    tensor representing a scalar field having shape (H, W) when given an
    image tensor having shape (3, H, W).
    """
    raise NotImplementedError
