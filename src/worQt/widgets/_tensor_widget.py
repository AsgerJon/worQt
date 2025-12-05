"""
TensorWidget provides a widget displaying an RGB image representation of
an underlying tensor.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
import time
from ctypes import c_void_p

import torch
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSize, QRect, Qt, QTimer
from PySide6.QtGui import QImage, QPainter, QPaintEvent, QBrush, QColor, \
  QMouseEvent
from PySide6.QtWidgets import QWidget, QSizePolicy
from torch import Tensor, cat
from worktoy.desc import Field
from worktoy.utilities import textFmt, maybe
from worktoy.utilities.mathematics import sin, atan2, pi
from worktoy.waitaminute import TypeException
import torchvision.transforms.v2.functional as TTF
import torch.nn.functional as F
from torch import float32 as F32
from torch import float64 as F64
from torch import uint8 as U8
from torch import complex64 as C64
from torch import rand as R
from torch import randn as RN
from torch import zeros as Z
from torch import ones as J

from worQt.desQt import Etc, ImgExtensions

gcd = lambda a, b: gcd(b, a % b) if b else a  # noqa

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, Self


class TensorWidget(QWidget):
  """
  A widget that displays an RGB image representation of an underlying tensor.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  _c = 0
  _moment = None

  #  Class Variables
  etc = Etc()
  imgExt = ImgExtensions()
  __B_C_H_W__ = (0, 1, 2, 3)
  __img_fmt__ = QImage.Format.Format_RGB888
  __timer_interval__ = 20
  __timer_type__ = Qt.TimerType.PreciseTimer

  #  Fallback Variables
  __fallback_width__ = 320
  __fallback_height__ = 240

  #  Private Variables
  __private_width__ = None
  __private_height__ = None
  __data_tensor__ = None
  __data_buffer__ = None
  __data_image__ = None
  __data_timer__ = None

  #  Public Variables
  imageWidth = Field()
  imageHeight = Field()
  shape = Field()
  data = Field()
  buffer = Field()
  image = Field()
  timer = Field()

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
    shape = [0, 0, 0, 0]
    shape[self.__B_C_H_W__[0]] = 1
    shape[self.__B_C_H_W__[1]] = 3
    shape[self.__B_C_H_W__[2]] = self.imageHeight
    shape[self.__B_C_H_W__[3]] = self.imageWidth
    return (*shape,)  # noqa, pycharm please

  @staticmethod
  def _makeComplexGrid(w: int, h: int, *args) -> Tensor:
    """
    Creates a grid of complex numbers representing the complex plane.
    The grid spans from -2 to 1 on the real axis and from 0 to 1 on the
    imaginary axis.
    """
    x0, x1, y0, y1, *_ = [*args, None, None, None, None]
    x0 = maybe(x0, -2.0)
    x1 = maybe(x1, 1.0)
    y0 = 0.0
    y1 = maybe(y1, 1.0)
    rows = torch.arange(w, dtype=F32).view(1, -1).to(C64)
    cols = torch.arange(h // 2, dtype=F32).view(-1, 1).to(C64)
    real = x0 + (x1 - x0) * rows / (w - 1)
    imag = y0 + (y1 - y0) * cols / (h // 2 - 1)
    return real + 1j * imag

  @classmethod
  def _mandelbrotScale(cls, c: Tensor, n: int = None) -> Tensor:
    """
    Applies the Mandelbrot iteration to the complex grid
    """
    out = torch.zeros_like(c)
    for _ in range(maybe(n, 32)):
      out *= out
      out += c
    return out

  @classmethod
  def _mandelbrotSteps(cls, c: Tensor) -> Tensor:
    """
    Applies the Mandelbrot iteration to the complex grid
    """
    out = torch.zeros_like(c).real.to(U8)
    m = torch.zeros_like(c)
    for i in range(255):
      m *= m
      m += c
      out += (m.abs() <= 2).to(U8)
    return out

  def _createDataTensor(self) -> None:
    window = -3.0, 3.0, 0, 3.0
    c = self._makeComplexGrid(self.imageWidth, self.imageHeight, *window, )
    scale8 = torch.exp((self._mandelbrotScale(c, 8).abs() - 2.0) ** 2)
    scale16 = torch.exp((self._mandelbrotScale(c, 16).abs() - 2.0) ** 2)
    scale32 = torch.exp((self._mandelbrotScale(c, 32).abs() - 2.0) ** 2)
    scale64 = torch.exp((self._mandelbrotScale(c, 64).abs() - 2.0) ** 2)
    scale128 = torch.exp((self._mandelbrotScale(c, 128).abs() - 2.0) ** 2)
    steps = self._mandelbrotSteps(c).to(F32)
    oneSteps = torch.ones_like(steps)
    steps = torch.log(steps) / torch.log(2. * oneSteps)
    steps /= steps.max()
    red = 127.5 * steps + 255. * scale16 - 127.5 * scale8
    green = 127.5 * steps + 255. * scale32 - 127.5 * scale8
    blue = 127.5 * steps + 255. * scale64 - 127.5 * scale8
    red = steps * 255.
    green = torch.abs(c)
    green /= green.max()
    green *= 255.
    blue = torch.atan2(green, blue)
    blue += blue.min()
    blue /= blue.max()
    blue *= 255.
    red = red.to(U8).unsqueeze_(0)
    green = green.to(U8).unsqueeze_(0)
    blue = blue.to(U8).unsqueeze_(0)
    lowerHalf = torch.cat([red, green, blue], dim=0)
    upperHalf = torch.flip(lowerHalf, [1])
    full = torch.cat([upperHalf, lowerHalf], dim=1).unsqueeze_(0)
    self.__data_tensor__ = full

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

  def _updateDataImage(self, ) -> None:
    self.__data_image__ = ImageQt(TTF.to_pil_image(self.data[0]))

  @image.GET
  def _getDataImage(self, **kwargs) -> QImage:
    if self.__data_image__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._updateDataImage()
      return self._getDataImage(_recursion=True)
    if isinstance(self.__data_image__, QImage):
      return self.__data_image__
    raise TypeException('__data_image__', self.__data_image__, QImage)

  def _createDataTimer(self, ) -> None:
    self.__data_timer__ = QTimer(self)
    self.__data_timer__.setInterval(self.__timer_interval__)
    self.__data_timer__.setTimerType(self.__timer_type__)
    self.__data_timer__.timeout.connect(self.nextImage)

  @timer.GET
  def _getDataTimer(self, **kwargs) -> QTimer:
    if self.__data_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createDataTimer()
      return self._getDataTimer(_recursion=True)
    if isinstance(self.__data_timer__, QTimer):
      return self.__data_timer__
    raise TypeException('__data_timer__', self.__data_timer__, QTimer)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, parent: QWidget, width: int, height: int) -> None:
    super().__init__(parent)
    self.setMouseTracking(True)
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

  def mousePressEvent(self, event: QMouseEvent) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def nextImage(self) -> None:
    self.rotate(pi / 48)
    self._c += 1
    if self._moment is None:
      self._moment = time.perf_counter_ns()
      return
    now = time.perf_counter_ns()
    if now - self._moment > 1_000_000_000:
      print('Count:', self._c)
      self._moment = now

  def maxPool(self, kernel: int) -> None:
    padding = int(kernel / 2)
    k, s, p = kernel, 1, padding
    self.__data_tensor__ = F.max_pool2d(self.data, k, s, p)
    self.update()

  def avgPool(self, kernel: int) -> None:
    padding = int(kernel / 2)
    k, s, p = kernel, 1, padding
    self.__data_tensor__ = F.avg_pool2d(self.data, k, s, p)
    self.update()

  def rotate(self, angle: float) -> None:
    B, C, H, W = self.data.shape
    cosA = torch.cos(torch.tensor(angle))
    sinA = torch.sin(torch.tensor(angle))

    theta = torch.tensor([
        [cosA, -sinA, 0.0],
        [sinA, cosA, 0.0],
    ], dtype=torch.float32).unsqueeze(0).to(self.data.device)

    grid = F.affine_grid(theta, size=self.data.shape, align_corners=False)
    self.__data_tensor__ = F.grid_sample(
        self.data, grid, align_corners=False
    )
    self.update()

  def getImageFiles(self, ) -> Iterator[str]:
    """
    Returns each file in the image resources directory. Recursive search
    is a planned feature.
    """
    imgDir = os.path.join(self.etc, 'resources', 'images')
    for file in os.listdir(imgDir):
      for ext in self.imgExt:
        if file.endswith(ext):
          yield os.path.join(imgDir, file)

  def openImage(self, fileName: str = None) -> None:
    """Opens the given image file"""
    name = maybe(fileName, '').split('.')[0]
    for fid in self.getImageFiles():
      if fileName is None:
        break
      if name in fid:
        break
    else:
      infoSpec = """Could not find image file '%s' in resources!"""
      info = infoSpec % fileName
      raise FileNotFoundError(info)
    f = type('_', (), dict(close=lambda *__, **_: None))()
    try:
      f = open(fid, 'rb')
    except Exception as exception:
      raise exception
    else:
      img = Image.open(f)
    finally:
      f.close()
    W, H = self.imageWidth, self.imageHeight
    img = img.resize((W, H), Image.Resampling.LANCZOS).convert('RGB')
    self.__data_tensor__ = TTF.pil_to_tensor(img).to(F32) / 255.
    self.update()

  def saveImage(self, fid: str) -> None:
    """Saves the current image to the given file."""
    img = TTF.to_pil_image(self.data[0])
    img.save(fid)
