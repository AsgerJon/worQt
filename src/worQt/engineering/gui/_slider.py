"""
Slider subclasses 'PaintedWidget' and is a slider saying what it sets and
how much.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ...paint_ops import PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget
from ._paint_slider import PaintSlider

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
  from PySide6.QtCore import QEvent

_KEY = Qt.Key


class Slider(PaintedWidget):
  """
  Slider subclasses 'PaintedWidget' and is a slider saying what it sets
  and how much: its name, 'text', on the left; a track filled up to the
  handle; and on the right the share it is at, in per cent. Its 'value'
  is kept from nought to all, and 'valueChanged' tells of each change.

  A click on the track puts the handle there and a drag takes it along;
  the wheel moves it a twentieth at a notch; the arrow keys move it a
  hundredth, Page Up and Page Down a tenth, Home and End to the ends.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_track_color__ = Color(66, 70, 77)
  __fallback_fill_color__ = Color(229, 192, 123)
  __fallback_handle_color__ = Color(212, 212, 212)
  __fallback_hover_handle_color__ = Color(250, 250, 250)
  __fallback_ink_color__ = Color(212, 212, 212)
  __fallback_track_height__ = 4.0  # pixels
  __fallback_handle_radius__ = 7.0  # pixels
  __fallback_gap__ = 10.0  # pixels between the name, track and share
  __fallback_wheel_step__ = 0.05
  __fallback_key_step__ = 0.01
  __fallback_page_step__ = 0.1

  #  Private Variables
  __slider_value__: float = 0.0
  __slider_text__: str = ''
  __label_width__: float = 0.0
  __value_width__: float = 0.0

  #  Public Variables
  boxModelOp = PaintBoxModel()
  sliderOp = PaintSlider()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(212, 212, 212),
  )
  dragging = AttriBox[bool](False)
  hovered = AttriBox[bool](False)

  #  Virtual Variables
  value: Field[float] = Field()
  text: Field[str] = Field()
  trackColor: Field[Color] = Field()
  fillColor: Field[Color] = Field()
  handleColor: Field[Color] = Field()
  inkColor: Field[Color] = Field()

  #  Signals
  valueChanged = Signal(float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @value.GET
  def _getValue(self, ) -> float:
    """The 'value' getter returns the share the slider is at."""
    return self.__slider_value__

  @text.GET
  def _getText(self, ) -> str:
    """The 'text' getter returns the slider's name."""
    return self.__slider_text__

  @trackColor.GET
  def _getTrackColor(self, ) -> Color:
    return self.__fallback_track_color__

  @fillColor.GET
  def _getFillColor(self, ) -> Color:
    return self.__fallback_fill_color__

  @handleColor.GET
  def _getHandleColor(self, ) -> Color:
    if self.hovered or self.dragging:
      return self.__fallback_hover_handle_color__
    return self.__fallback_handle_color__

  @inkColor.GET
  def _getInkColor(self, ) -> Color:
    return self.__fallback_ink_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @value.SET
  def _setValue(self, value: float) -> None:
    """The 'value' setter moves the slider to 'value', kept from nought
    to all, telling of it if it moved."""
    value = min(max(float(value), 0.0), 1.0)
    if value == self.__slider_value__:
      return
    self.__slider_value__ = value
    self.update()
    self.valueChanged.emit(value)

  @text.SET
  def _setText(self, text: str) -> None:
    """The 'text' setter names the slider."""
    if not isinstance(text, str):
      raise TypeException('text', text, str)
    self.__slider_text__ = text
    self.updateGeometry()
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(260, self.font.metrics.height() + 14)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(160, self.font.metrics.height() + 14)

  def enterEvent(self, event: QEvent) -> None:
    self.hovered = True
    self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.hovered = False
    self.update()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A press puts the handle where it is and takes hold of it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return event.ignore()
    self.setFocus()
    self.dragging = True
    self.value = self.valueAt(event.position().x())
    event.accept()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """A drag takes the handle along."""
    if not self.dragging:
      return event.ignore()
    self.value = self.valueAt(event.position().x())
    event.accept()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Letting go leaves the handle where it is."""
    if not self.dragging:
      return event.ignore()
    self.value = self.valueAt(event.position().x())
    self.dragging = False
    self.update()
    event.accept()

  def wheelEvent(self, event: QWheelEvent) -> None:
    """The wheel moves the handle a twentieth at a notch."""
    notches = event.angleDelta().y() / 120
    self.value = self.value + notches * self.__fallback_wheel_step__
    event.accept()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """The arrows move the handle a hundredth, the page keys a tenth,
    Home and End to the ends."""
    step, page = self.__fallback_key_step__, self.__fallback_page_step__
    moves = {
      _KEY.Key_Right : step, _KEY.Key_Up: step,
      _KEY.Key_Left  : -step, _KEY.Key_Down: -step,
      _KEY.Key_PageUp: page, _KEY.Key_PageDown: -page,
    }
    key = event.key()
    if key in moves:
      self.value = self.value + moves[key]
    elif key == _KEY.Key_Home:
      self.value = 0.0
    elif key == _KEY.Key_End:
      self.value = 1.0
    else:
      return PaintedWidget.keyPressEvent(self, event)
    event.accept()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.setCursor(Qt.CursorShape.PointingHandCursor)
    self.setMouseTracking(True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def valueText(self, ) -> str:
    """The 'valueText' method says the share, in per cent."""
    return '%d %%' % round(100 * self.value)

  def setLabelWidth(self, width: float) -> None:
    """The 'setLabelWidth' method gives the name at least 'width'
    pixels, so sliders one above another line up."""
    self.__label_width__ = float(width)
    self.update()

  def textRect(self, ) -> QRectF:
    """The 'textRect' method returns where the name is written, as wide
    as it is or as its label width, whichever is the more."""
    width = self.font.metrics.horizontalAdvance(self.text)
    width = max(float(width), self.__label_width__)
    return QRectF(8.0, 0.0, width, float(self.height()))

  def valueRect(self, ) -> QRectF:
    """The 'valueRect' method returns where the share is written, room
    for all of it."""
    width = self.font.metrics.horizontalAdvance('100 %')
    return self._valueRectOf(float(width))

  def setValueWidth(self, width: float) -> None:
    """The 'setValueWidth' method gives the value shown at least 'width'
    pixels, so sliders one above another line up."""
    self.__value_width__ = float(width)
    self.update()

  def _valueRectOf(self, width: float) -> QRectF:
    """Where a value 'width' wide is written, at the right, at least the
    value width wide."""
    width = max(width, self.__value_width__)
    left = self.width() - 8.0 - width
    return QRectF(left, 0.0, width, float(self.height()))

  def trackRect(self, ) -> QRectF:
    """The 'trackRect' method returns the track, between the name and
    the share, room left at its ends for the handle."""
    gap = self.__fallback_gap__
    radius = self.__fallback_handle_radius__
    named = self.textRect()
    left = named.right() + (gap if self.text else 0.0) + radius
    right = self.valueRect().left() - gap - radius
    height = self.__fallback_track_height__
    middle = self.height() / 2
    width = max(right - left, 1.0)
    return QRectF(left, middle - height / 2, width, height)

  def handleCenter(self, ) -> QPointF:
    """The 'handleCenter' method returns where the handle is."""
    track = self.trackRect()
    x = track.left() + self.value * track.width()
    return QPointF(x, track.center().y())

  def handleRadius(self, ) -> float:
    """The 'handleRadius' method returns how large the handle is."""
    return self.__fallback_handle_radius__

  def valueAt(self, x: float) -> float:
    """The 'valueAt' method returns the share at 'x' along the track,
    kept from nought to all."""
    track = self.trackRect()
    return min(max((x - track.left()) / track.width(), 0.0), 1.0)
