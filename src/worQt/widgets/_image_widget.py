"""
StaticImage provides a widget displaying a static image.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from . import BaseWidget
from ..core.images import BaseImage, TestOp, EdgeDetection
from ..dialogs import LoadFile


class ImageWidget(BaseWidget):
  """
  StaticImage provides a widget displaying a static image, that is, a visual
  representation of a tensor with dimensions width and height along with 3
  color channels.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_image__ = 'ohtani'

  #  Private Variables
  __loaded_images__ = None

  #  Public Variables
  loadingDialog = AttriBox[LoadFile](THIS)
  layoutBox = AttriBox[QHBoxLayout](THIS)
  loadedImages = Field()

  #  Virtual Variables

  #  Signals

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createFallbackImage(self, ) -> None:
    self.__current_image__ = BaseImage('ohtani')

  def _createLoadedImages(self, ) -> None:
    self.__loaded_images__ = [BaseImage(self.__fallback_image__), ]

  @loadedImages.GET
  def _getLoadedImages(self, **kwargs) -> list[BaseImage]:
    if self.__loaded_images__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createLoadedImages()
      return self._getLoadedImages(_recursion=True)
    return self.__loaded_images__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _addLoadedImage(self, image: BaseImage) -> None:
    existing = self._getLoadedImages()
    self.__loaded_images__ = [*existing, image, ]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.loadingDialog.fileSelected.connect(self._loadImage)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def reset(self, ) -> None:
    self.__current_image__ = None
    self.update()

  def blur(self, ) -> None:
    self.__current_image__ = BaseImage(self._blur(self.image.data))

  @Slot(str)
  def _loadImage(self, fid: str) -> None:
    self.__current_image__ = BaseImage(fid)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initLogic(self, ) -> None:
    """
    Connects the 'accepted' signal on the loading dialog to the internal
    image loading method.
    """

  @Slot()
  def load(self, ) -> None:
    """
    This slot opens the loading dialog for loading an image from file.
    """
    self.loadingDialog.show()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def mousePressEvent(self, event: QMouseEvent) -> None:
    if event.button() == Qt.MouseButton.RightButton:
      self.__current_image__ = BaseImage(self.edgeDetect(self.image.data))
      self.update()

  def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter()
    painter.begin(self)
    viewRect = painter.viewport()
    viewWidth, viewHeight = viewRect.width(), viewRect.height()
    imWidth, imHeight = self.image.width, self.image.height
    imgRect = self.image.rect.alignInner(viewRect, self.align)
    painter.drawImage(imgRect.QType, self.image.qImage)
    painter.end()
    if viewWidth * 1.1 < imWidth or viewHeight * 1.1 < imHeight:
      self.image.resize(viewWidth, viewHeight)
