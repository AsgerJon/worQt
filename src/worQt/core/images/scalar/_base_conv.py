"""
BaseConv provides a base class for convolution operations on image data.

Properties:
- owner: The image type that owns this convolution operation.
- name: The name of the convolution operation.
- kernel: The convolution kernel used for the operation (must have odd
dimensions).
- stride: The stride of the convolution operation (default is 1).
- dilation: The dilation rate of the convolution operation (default is 1).
- padding: The padding applied to the image before convolution. Default
assumes stride and dilation of 1 and calculates padding to maintain image
size.

The base class *does not* provide a constructor. Subclasses must implement
a constructor that sets the kernel.

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import MissingVariable, TypeException

from ..functional import planeConv

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Never, Callable, Iterator, TypeAlias, Type

  from .. import BaseRaster

  ImgType: TypeAlias = Type[BaseRaster]
  Image: TypeAlias = BaseRaster


class BaseConv:
  """
  BaseConv provides a base class for convolution operations on image data.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __field_owner__ = None
  __field_name__ = None
  __fallback_stride__ = 1
  __fallback_dilation__ = 1

  #  Private Variables
  __stride_steps__ = None
  __dilation_rate__ = None

  #  Public Variables
  owner = Field()
  name = Field()
  stride = Field()
  dilation = Field()

  #  Virtual Variables
  padding = Field()
  kernel = Field()

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

  @stride.GET
  def _getStride(self, **kwargs) -> int:
    return maybe(self.__stride_steps__, self.__fallback_stride__)

  @dilation.GET
  def _getDilation(self, **kwargs) -> int:
    return maybe(self.__dilation_rate__, self.__fallback_dilation__)

  @kernel.GET
  def _getKernel(self, **kwargs) -> Tensor:
    """
    Subclasses must implement this method to specify the convolution
    kernel. Please note that the kernel must have odd dimensions.
    """
    raise NotImplementedError

  @padding.GET
  def _getPadding(self, **kwargs) -> tuple[int, int]:
    """
    Calculates the padding needed to maintain image size after convolution,
    assuming stride and dilation of 1. Subclasses using different stride
    or dilation from 1 must also provide explicit padding.
    """
    if (self.stride - 1) * (self.dilation - 1):  # Bad branch
      infoSpec = """Convolution with stride or dilation different from 1, 
      must provide explicit padding, but found stride: '%d' and dilation: 
      '%d' instead."""
      info = infoSpec % (self.stride, self.dilation)
      raise NotImplementedError(textFmt(info))
    kH, kW = self.kernel.shape[-2:]
    if (kH % 2) ** 2 + (kH % 2) ** 2:
      infoSpec = """Convolution kernel must have odd dimensions, 
      but received (%d, %d) instead."""
      info = infoSpec % (kH, kW)
      raise ValueError(textFmt(info))
    return int(0.5 * kH), int(0.5 * kW)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
    return planeConv(
        instance.data,
        self.kernel,
        stride=self.stride,
        dilation=self.dilation,
        padding=self.padding,
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
