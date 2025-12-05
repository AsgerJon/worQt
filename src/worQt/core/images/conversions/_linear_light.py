"""
LinearLight provides a descriptor that returns the linear light version of
the owning rgb image.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor, where
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type

  from .. import BaseRaster

  ImgType: TypeAlias = Type[BaseRaster]
  Image: TypeAlias = BaseRaster


class LinearLight:
  """
  LinearLight provides a descriptor that returns the linear light version of
  the owning rgb image.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __field_owner__ = None
  __field_name__ = None

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
      raise MissingVariable(self, '__field_owner__', type)
    if isinstance(self.__field_owner__, type):
      if TYPE_CHECKING:  # pragma: no cover
        assert issubclass(self.__field_owner__, BaseRaster)
      return self.__field_owner__
    name, value = '__field_owner__', self.__field_owner__
    raise TypeException(name, value, type)

  @name.GET
  def _getName(self, **kwargs) -> str:
    if self.__field_name__ is None:
      raise MissingVariable(self, '__field_name__', str)
    if isinstance(self.__field_name__, str):
      return self.__field_name__
    name, value = '__field_name__', self.__field_name__
    raise TypeException(name, value, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def convert(tensor: Tensor, ) -> Tensor:
    """
    Converts an sRGB tensor to linear light.
    """
    mask = tensor <= 0.04045
    low = tensor / 12.92
    high = ((tensor + 0.055) / 1.055) ** 2.4
    return where(mask, low, high)

  @staticmethod
  def invert(tensor: Tensor) -> Tensor:
    """
    Converts a linear light tensor to sRGB.
    """
    mask = tensor <= 0.0031308
    low = tensor * 12.92
    high = 1.055 * (tensor ** (1 / 2.4)) - 0.055
    return where(mask, low, high)

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
    return self.convert(instance.data)

  def __set__(self, instance: Image, linLight: Tensor, ) -> None:
    rgb = self.invert(linLight)
    setattr(instance, '__raster_tensor__', rgb)
