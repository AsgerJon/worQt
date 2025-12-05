"""
BaseImage provides a base for image functionality with instances
defined by a core PyTorch tensor representation of the image. This core
follows the traditional image tensor format of (C, H, W) as color, height
and width dimensions respectively. The base provides file I/O access to
this core QImage/QPixmap/PIL representations.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os

from typing import TYPE_CHECKING

import torch
from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import QSize, QSizeF
from PySide6.QtGui import QImage, QPixmap, QColor
from torch.nn.functional import interpolate
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt
from worktoy.work_io import FidGen

import numpy as np
from torch import Tensor
from torch import float32 as F32
from torch import float64 as F64
from torch import uint8 as U8
from torch import complex64 as C64
from torch import complex128 as C128

from ..geometry import Size, Rect, Point
from ...desQt import Etc, resImage
from .functional import tensorToPIL, pilToTensor

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Never, Callable, Any, TypeAlias

  _ = U8, F32, F64, C64, C128, Tensor, FidGen


class BaseImage(BaseObject):
  """
  BaseImage provides a base for image functionality with instances
  defined by a core PyTorch tensor representation of the image. This core
  follows the traditional image tensor format of (C, H, W) as color, height
  and width dimensions respectively. The base provides file I/O access to
  this core QImage/QPixmap/PIL representations.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()
  images = Etc('resources', 'images')

  #  Fallback Variables

  #  Private Variables
  __image_tensor__ = None
  __source_path__ = None

  #  Public Variables
  data = Field()  # Tensor

  #  Virtual Variables
  pil = Field()
  size = Field()
  rect = Field()
  width = Field()
  height = Field()
  aspect = Field()
  qSize = Field()
  qSizeF = Field()
  qImage = Field()
  qPixmap = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getFallbackPath(self, ) -> str:
    return os.path.join(self.etc, 'resources', 'images', 'fallback.png')

  @data.GET
  def _getData(self, **kwargs) -> Tensor:
    return self.__image_tensor__

  @pil.GET
  def _getPIL(self, **kwargs) -> Image.Image:
    return tensorToPIL(self.__image_tensor__)

  @size.GET
  def _getSize(self, **kwargs) -> tuple[int, int]:
    data = self.data
    _, height, width = data.shape
    out = Size()
    out.__dim_values__ = width, height
    return out

  @rect.GET
  def _getRect(self, **kwargs) -> Rect:
    return Rect(Point(), self.size)

  @width.GET
  def _getWidth(self, **kwargs) -> int:
    return self.size[0]

  @height.GET
  def _getHeight(self, **kwargs) -> int:
    return self.size[1]

  @aspect.GET
  def _getAspect(self, **kwargs) -> float:
    if self.height:
      if self.width:
        return self.width / self.height
      return .0
    raise ZeroDivisionError

  @qSize.GET
  def _getQSize(self, **kwargs) -> QSize:
    return QSize(self.width, self.height)

  @qSizeF.GET
  def _getQSizeF(self, **kwargs) -> QSizeF:
    return QSize.toSizeF(self.qSize)

  @qImage.GET
  def _getQImage(self, **kwargs) -> QImage:
    return Image.Image.toqimage(self.pil)

  @qPixmap.GET
  def _getQPixmap(self, **kwargs) -> QPixmap:
    return Image.Image.toqpixmap(self.pil)

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

  @overload(str)
  def __init__(self, fid: str) -> None:
    res = resImage(fid)
    self.__source_path__ = res
    self.__image_tensor__ = self._diskToTensor(res)

  @overload(Tensor)
  def __init__(self, tensor: Tensor) -> None:
    self.__image_tensor__ = tensor

  @overload(Image.Image)
  def __init__(self, pilImage: Image.Image) -> None:
    self.__image_tensor__ = pilToTensor(pilImage)

  @overload(int, int)
  def __init__(self, width: int, height: int) -> None:
    self.__image_tensor__ = torch.rand((3, height, width), dtype=F32)

  @overload(QSize)
  def __init__(self, qSize: QSize) -> None:
    self.__init__(qSize.width(), qSize.height())

  @overload(QSizeF)
  def __init__(self, qSizeF: QSizeF) -> None:
    self.__init__(QSizeF.toSize(qSizeF))

  @overload(QColor, int, int)
  def __init__(self, qColor: QColor, *args) -> None:
    self.__init__(*args)
    r = qColor.redF() * torch.ones(1, self.height, self.width, dtype=F32)
    g = qColor.greenF() * torch.ones(1, self.height, self.width, dtype=F32)
    b = qColor.blueF() * torch.ones(1, self.height, self.width, dtype=F32)
    self.__image_tensor__ = torch.cat((r, g, b), dim=0)

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def resize(self, *args) -> None:
    self.__image_tensor__ = self._resizeTensor(self.data, Size(*args))

  @staticmethod
  def _resizeTensor(data: Tensor, size: Size) -> Tensor:
    """
    Resizes the image currently loaded into the tensor
    """
    img = data.unsqueeze(0)
    oldSize = Size(img.shape[-2], img.shape[-1], )
    newSize = oldSize.scaleInner(size)
    resized = interpolate(
        img,
        size=(*newSize,),
        mode='bicubic',
        align_corners=False,
    )
    return resized.squeeze(0)

  @staticmethod
  def _diskToTensor(fid: str, **kwargs) -> Tensor:
    """
    Loads the image at the provided file identifier and converts it to
    a torch tensor of shape (C, H, W). Raises FileNotFoundError if the
    file is missing, and RuntimeError on permission issues. Closes all
    resources manually.
    """
    f, img = None, None
    try:
      f = open(fid, 'rb')
      img = Image.open(f).convert('RGB')
    except PermissionError as exception:
      infoSpec = """Insufficient permissions to read image file at '%s'!"""
      info = textFmt(infoSpec % fid)
      raise RuntimeError(info) from exception
    else:
      return pilToTensor(img)
    finally:
      if f is not None:
        f.close()
      if img is not None:
        img.close()

  @staticmethod
  def _tensorToDisk(tensor: Tensor, fid: str, **kwargs) -> None:
    """
    Saves the provided tensor of shape (C, H, W) to the provided file
    identifier. Raises RuntimeError on permission issues. Closes all
    resources manually.
    """
    f = None
    try:
      f = open(fid, 'wb')
    except PermissionError as exception:
      infoSpec = """Insufficient permissions to write image file at '%s'!"""
      info = textFmt(infoSpec % fid)
      raise RuntimeError(info) from exception
    else:
      tensorToPIL(tensor).save(f)
    finally:
      if f is not None:
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
