"""
TensorWidget provides a widget displaying an RGB image representation of
an underlying tensor.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ctypes import c_void_p
import sip

from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize, QRect, Qt
from PySide6.QtGui import QImage, QPainter, QPaintEvent, QBrush, QColor
from PySide6.QtWidgets import QWidget, QSizePolicy
from torch import Tensor
from worktoy.desc import Field
from worktoy.waitaminute import TypeException
import torchvision.transforms.v2.functional as TTF
from torch import float32 as F32
from torch import uint8 as U8
from torch import rand as R
from torch import zeros as Z


class TensorWidget(QWidget):
  """
  A widget that displays an RGB image representation of an underlying tensor.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  # __height_width_colour__ = (1, 2, 0)
  __height_width_colour__ = (0, 1, 2,)
  __img_fmt__ = QImage.Format.Format_RGB888

  #  Fallback Variables
  __fallback_width__ = 320
  __fallback_height__ = 240

  #  Private Variables
  __private_width__ = None
  __private_height__ = None
  __data_tensor__ = None
  __data_buffer__ = None
  __data_image__ = None

  #  Public Variables
  imageWidth = Field()
  imageHeight = Field()
  shape = Field()
  data = Field()
  buffer = Field()
  image = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @imageWidth.GET
  def _getImageWidth(self, **kwargs) -> int:
    if self.__private_width__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__private_width__ = self.__fallback_width__
      return self._getImageWidth(_recursion=True)
    if isinstance(self.__private_width__, int):
      if self.__private_width__ > 0:
        return self.__private_width__
      infoSpec = """Expected positive image width, but received: '%d'!"""
      info = infoSpec % self.__private_width__
      raise ValueError(info)
    raise TypeException('__image_width__', self.__private_width__, int)

  @imageHeight.GET
  def _getImageHeight(self, **kwargs) -> int:
    if self.__private_height__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__private_height__ = self.__fallback_height__
      return self._getImageHeight(_recursion=True)
    if isinstance(self.__private_height__, int):
      if self.__private_height__ > 0:
        return self.__private_height__
      infoSpec = """Expected positive image height, but received: '%d'!"""
      info = infoSpec % self.__private_height__
      raise ValueError(info)
    raise TypeException('__image_height__', self.__private_height__, int)

  @shape.GET
  def _getShape(self, ) -> tuple[int, int, int]:
    shape = [0, 0, 0, ]
    shape[self.__height_width_colour__[0]] = self.imageHeight
    shape[self.__height_width_colour__[1]] = self.imageWidth
    shape[self.__height_width_colour__[2]] = 3
    return (*shape,)  # noqa, pycharm please

  def _createDataTensor(self) -> None:
    self.__data_tensor__ = R(self.shape, dtype=F32)

  @data.GET
  def _getDataTensor(self, **kwargs) -> Tensor:
    if self.__data_tensor__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createDataTensor()
      return self._getDataTensor(_recursion=True)
    if isinstance(self.__data_tensor__, Tensor):
      return self.__data_tensor__
    raise TypeException('__data_tensor__', self.__data_tensor__, Tensor)

  def _createDataBuffer(self) -> None:
    self.__data_buffer__ = Z(self.shape, dtype=U8)

  @buffer.GET
  def _getDataBuffer(self, **kwargs) -> Tensor:
    if self.__data_buffer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createDataBuffer()
      return self._getDataBuffer(_recursion=True)
    if isinstance(self.__data_buffer__, Tensor):
      return self.__data_buffer__
    raise TypeException('__data_buffer__', self.__data_buffer__, Tensor)

  def _createDataImage(self) -> None:
    h = self.imageHeight
    w = self.imageWidth
    fmt = self.__img_fmt__
    ptr = c_void_p(self.buffer.data_ptr())
    self.__data_image__ = QImage(ptr, w, h, 3 * w, fmt)

  def _updateImage(self, ) -> None:
    if self.__data_buffer__ is None:
      self._createDataBuffer()
      return self._updateImage()
    if isinstance(self.__data_tensor__, Tensor):
      self.__data_buffer__.copy_((255 * self.data).clamp(0, 255).to(U8))
    self.update()

  @image.GET
  def _getDataImage(self, **kwargs) -> QImage:
    if self.__data_image__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createDataImage()
      return self._getDataImage(_recursion=True)
    if isinstance(self.__data_image__, QImage):
      return self.__data_image__
    raise TypeException('__data_image__', self.__data_image__, QImage)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, parent: QWidget, width: int, height: int) -> None:
    super().__init__(parent)
    self.__private_width__ = width
    self.__private_height__ = height
    self.setMaximumSize(QSize(16777215, 16777215))
    self.setSizePolicy(
        QSizePolicy.Policy.MinimumExpanding,
        QSizePolicy.Policy.MinimumExpanding,
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def minimumSize(self, ) -> QSize:
    return QSize(self.imageWidth + 32, self.imageHeight + 32)

  def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter()
    painter.begin(self)
    viewRect = painter.viewport()
    brush = QBrush()
    lime = QColor(169, 255, 0)
    brush.setColor(lime)
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    painter.setBrush(brush)
    painter.drawRect(viewRect)
    imgRect = QRect(0, 0, self.imageWidth, self.imageHeight)
    imgRect.moveCenter(viewRect.center())
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.drawImage(imgRect, self.image)
    painter.end()
