"""
BaseBinary provides a base class for binary operations between images.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias, Type

  from . import BaseRaster

  ImgType: TypeAlias = Type[BaseRaster]
  Image: TypeAlias = Optional[BaseRaster]


class BaseBinary:
  """
  BaseBinary provides a base class for binary operations between images.
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
        from . import BaseRaster
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
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

  def __get__(self, instance: Image, owner: ImgType, ) -> Any:
    if instance is None:
      return self

    def apply(other: Image) -> Image:
      leftData = instance.data
      rightData = other.data
      applied = self._apply(leftData, rightData)
      out = owner()
      setattr(out, '__raster_tensor__', applied)
      return out

    return apply

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _apply(self, left: Tensor, right: Tensor) -> Tensor:
    """
    Subclasses must implement this method. The base expects it to perform
    the operation and return the resulting tensor.
    """
    raise NotImplementedError
