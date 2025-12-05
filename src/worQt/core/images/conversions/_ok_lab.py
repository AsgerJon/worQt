"""
OKLab provides a descriptor class that returns the OKLab version of
the owning RGB image.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor, zeros_like
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException

from . import LinearLight

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type

  from .. import BaseRaster

  ImgType: TypeAlias = Type[BaseRaster]
  Image: TypeAlias = BaseRaster


class OKLab:
  """
  OKLab provides a descriptor class that returns the OKLab version of
  the owning RGB image.
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
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def convert(tensor: Tensor, ) -> Tensor:
    """
    Converts an sRGB tensor to OKLab.
    """
    linLight = LinearLight.convert(tensor)
    l = 0.4122214708 * linLight[0, :, :]
    l += 0.5363325363 * linLight[1, :, :]
    l += 0.0514459929 * linLight[2, :, :]

    m = 0.2119034982 * linLight[0, :, :]
    m += 0.6806995451 * linLight[1, :, :]
    m += 0.1073969566 * linLight[2, :, :]

    s = 0.0883024619 * linLight[0, :, :]
    s += 0.2817188376 * linLight[1, :, :]
    s += 0.6299787005 * linLight[2, :, :]

    l_ = l.pow(1.0 / 3.0)
    m_ = m.pow(1.0 / 3.0)
    s_ = s.pow(1.0 / 3.0)

    oklab = zeros_like(tensor)

    oklab[0, :, :] = 0.2104542553 * l_
    oklab[0, :, :] += 0.7936177850 * m_
    oklab[0, :, :] -= 0.0040720468 * s_

    oklab[1, :, :] = 1.9779984951 * l_
    oklab[1, :, :] -= 2.4285922050 * m_
    oklab[1, :, :] += 0.4505937099 * s_

    oklab[2, :, :] = 0.0259040371 * l_
    oklab[2, :, :] += 0.7827717662 * m_
    oklab[2, :, :] -= 0.8086757660 * s_

    return oklab

  @staticmethod
  def invert(tensor: Tensor) -> Tensor:
    """
    Converts an OKLab tensor to sRGB.
    """
    l_ = (0.9999999985 * tensor[0, :, :])
    l_ += 0.3963377922 * tensor[1, :, :]
    l_ += 0.2158037581 * tensor[2, :, :]

    m_ = (1.0000000089 * tensor[0, :, :])
    m_ -= 0.1055613423 * tensor[1, :, :]
    m_ -= 0.0638541748 * tensor[2, :, :]

    s_ = (1.0000000547 * tensor[0, :, :])
    s_ -= 0.0894841821 * tensor[1, :, :]
    s_ -= 1.2914855379 * tensor[2, :, :]

    l = l_.pow(3)
    m = m_.pow(3)
    s = s_.pow(3)

    linLight = zeros_like(tensor)

    linLight[0, :, :] = 4.0767416621 * l
    linLight[0, :, :] -= 3.3077115913 * m
    linLight[0, :, :] += 0.2309699292 * s

    linLight[1, :, :] = -1.2684380046 * l
    linLight[1, :, :] += 2.6097574011 * m
    linLight[1, :, :] -= 0.3413193965 * s

    linLight[2, :, :] = -0.0041960863 * l
    linLight[2, :, :] -= 0.7034186147 * m
    linLight[2, :, :] += 1.7076147010 * s

    return LinearLight.invert(linLight)

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

  def __set__(self, instance: Image, oklab: Tensor, ) -> None:
    rgb = self.invert(oklab)
    instance.__raster_tensor__ = rgb
