"""
BaseRaster provides a base for representation and manipulation of raster
images. The inner image is a PyTorch tensor following the (C, H, W) format,
where C is the color channel, H is the height, and W is the width. The
base provides methods for file I/O along with conversions to PIL, QImage,
and QPixmap formats.

The base class leaves constructors and manipulation methods to derived
classes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image
from PySide6.QtGui import QImage, QPixmap
from torch import Tensor
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException, MissingVariable

from .conversions import LinearLight, OKLab
from .functional import tensorToPIL, pilToTensor

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Never, Callable, Any, TypeAlias


class BaseRaster(BaseObject):
  """
  BaseRaster provides a base for representation and manipulation of raster
  images. The inner image is a PyTorch tensor following the (C, H, W) format,
  where C is the color channel, H is the height, and W is the width. The
  base provides methods for file I/O along with conversions to PIL, QImage,
  and QPixmap formats.

  The base class leaves constructors and manipulation methods to derived
  classes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __raster_tensor__ = None

  #  Public Variables

  #  Virtual Variables
  pil = Field()
  qImage = Field()
  qPixmap = Field()
  data = Field()

  #  Conversions
  linLight = LinearLight()
  okLab = OKLab()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @pil.GET
  def _getPil(self, **kwargs) -> Image.Image:
    return tensorToPIL(self.__raster_tensor__)

  @qImage.GET
  def _getQImage(self, **kwargs) -> QImage:
    return QImage.fromData(self.pil)

  @qPixmap.GET
  def _getQPixmap(self, **kwargs) -> QPixmap:
    return QPixmap.fromImage(self.qImage)

  @data.GET
  def _getData(self, **kwargs) -> Any:
    if self.__raster_tensor__ is None:
      raise MissingVariable('__raster_tensor__')
    if not isinstance(self.__raster_tensor__, Tensor):
      name, value = '__raster_tensor__', self.__raster_tensor__
      raise TypeException(name, value, Tensor, )
    if not self.__raster_tensor__.ndim == 3:
      infoSpec = """Expected a 3-dimensional tensor in (C, H, W) format, 
      but received a tensor with shape: '%s'!"""
      shapeSpec = """(%s)"""
      shapes = ', '.join(str(dim) for dim in self.__raster_tensor__.shape)
      shape = shapeSpec % shapes
      info = infoSpec % shape
      raise ValueError(info)
    if self.__raster_tensor__.shape[0] == 3:
      return self.__raster_tensor__
    infoSpec = """Expected raster tensor to have format (C, H, W) with 
    C=3, but received '%d' color channels!"""
    channels = self.__raster_tensor__.shape[0]
    info = infoSpec % channels
    raise ValueError(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def load(self, fid: str, **kwargs) -> None:
    """
    Replaces the inner raster tensor with the image loaded from the given
    file identifier.
    """
    f = None
    try:
      f = open(fid, 'rb')
    except Exception as exception:
      raise exception
    else:
      pilImage = Image.open(f)
      self.__raster_tensor__ = pilToTensor(pilImage)
    finally:
      if hasattr(f, 'close'):
        f.close()

  def save(self, fid: str, **kwargs) -> None:
    """
    Saves the inner raster tensor to the given file identifier.
    """
    f = None
    try:
      f = open(fid, 'wb')
    except Exception as exception:
      raise exception
    else:
      pilImage = tensorToPIL(self.__raster_tensor__)
      pilImage.save(f)
    finally:
      if hasattr(f, 'close'):
        f.close()

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
