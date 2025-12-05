"""
BaseImage provides a base class for image types supporting file I/O and
conversion between PyTorch tensors, QImage, and QPixmap representations.
Subclasses extend this foundation to implement format-specific or
device-specific behavior while preserving a consistent interface for image
access and transformation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np
import torch
from PySide6.QtCore import QSize, QSizeF
from PySide6.QtGui import QImage, QPixmap

from torch import float32 as F32
from torch import float64 as F64
from torch import uint8 as U8
from torch import complex64 as C64
from torch import complex128 as C128
from torch import Tensor

from PIL import Image, UnidentifiedImageError
from torchvision.transforms.functional import to_pil_image
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt
from worktoy.work_io import FidGen, validateAvailablePath

from ...desQt import Etc

if TYPE_CHECKING:  # pragma: no cover
  dataTypes = U8, F32, F64, C64, C128


class BaseImage(BaseObject):
  """
  BaseImage provides a base class for image types supporting file I/O and
  conversion between PyTorch tensors, QImage, and QPixmap representations.
  Subclasses extend this foundation to implement format-specific or
  device-specific behavior while preserving a consistent interface for image
  access and transformation.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()

  #  Fallback Variables
  _fidGen = FidGen(extension='bmp', )

  #  Private Variables
  __image_path__ = None
  __image_tensor__ = None

  #  Public Variables
  imgPath = Field()
  data = Field()

  #  Virtual Variables
  size = Field()
  width = Field()
  height = Field()
  qSize = Field()
  qSizeF = Field()
  qImage = Field()
  qPixmap = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createImagePath(self, **kwargs) -> None:
    fileName = self._fidGen.nextName
    dirPath = os.path.join(self.etc, 'resources', 'temp', )
    imgPath = os.path.join(dirPath, fileName)
    try:
      imgPath = validateAvailablePath(os.path.join(dirPath, fileName))
    except FileExistsError as fileExistsError:
      recursionLimit = kwargs.get('_recursionLimit', 10)
      if recursionLimit:
        return self._createImagePath(_recursionLimit=recursionLimit - 1, )
      raise RecursionError from fileExistsError
    else:
      self.__image_path__ = imgPath

  @imgPath.GET
  def _getImagePath(self, **kwargs) -> str:
    if self.__image_path__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createImagePath()
      return self._getImagePath(_recursion=True, )
    return self.__image_path__

  def _getFallbackPath(self, ) -> str:
    """
    Getter-function for the path to the fallback image in the 'etc' folder.
    """
    return os.path.join(self.etc, 'resources', 'images', 'fallback.png')

  def _createPilImage(self, ) -> None:
    f = type('_', (), dict(close=lambda *_: None))
    try:
      f = open(self.imgPath, 'rb')
    except Exception as exception:
      raise exception
    else:
      img = Image.open(f).convert('RGBA')
    finally:
      f.close()

  def _createImageTensor(self, **kwargs) -> None:
    """
    Loads the image at imgPath or the provided _imgPath keyword as RGB
    and converts it to a torch tensor of shape (C, H, W). If the file is
    missing or invalid, a fallback image is loaded recursively and saved
    to the original path. Raises RecursionError if fallback also fails,
    and RuntimeError on permission issues. Closes all resources manually.
    """
    f = None
    img = None
    try:
      p = kwargs.get('_imgPath', self.imgPath)
      f = open(p, 'rb')
      img = Image.open(f).convert('RGB')
    except (FileNotFoundError, UnidentifiedImageError) as exception:
      if kwargs.get('_recursion', False):
        raise RecursionError from exception
      fb = self._getFallbackPath()
      self._createImageTensor(_imgPath=fb, _recursion=True, )
    except PermissionError as exception:
      infoSpec = """Insufficient permissions to read image file at '%s'!"""
      info = textFmt(infoSpec % kwargs.get('_imgPath', self.imgPath))
      raise RuntimeError(info) from exception
    else:
      if kwargs.get('_recursion', False):
        img.save(self.imgPath)
      data = torch.as_tensor(np.array(img))
      data = data.permute((2, 0, 1))
      data = data.to(F32) / 255.0
    finally:
      if f is not None:
        f.close()
      if img is not None:
        img.close()

  @data.GET
  def _getImageTensor(self, **kwargs) -> Tensor:
    if self.__image_tensor__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createImageTensor()
      return self._getImageTensor(_recursion=True, )
    return self.__image_tensor__

  @size.GET
  def _getSize(self, **kwargs) -> tuple[int, int]:
    data = self.data
    _, height, width = data.shape
    return width, height

  @width.GET
  def _getWidth(self, **kwargs) -> int:
    return self.size[0]

  @height.GET
  def _getHeight(self, **kwargs) -> int:
    return self.size[1]

  @qSize.GET
  def _getQSize(self, **kwargs) -> QSize:
    return QSize(self.width, self.height)

  @qSizeF.GET
  def _getQSizeF(self, **kwargs) -> QSizeF:
    return QSize.toSizeF(self.qSize)

  @qImage.GET
  def _getQImage(self, **kwargs) -> QImage:
    pilImg = to_pil_image(self.data)
    return Image.Image.toqimage(pilImg)

  @qPixmap.GET
  def _getQPixmap(self, **kwargs) -> QPixmap:
    pilImg = to_pil_image(self.data)
    return Image.Image.toqpixmap(pilImg)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
