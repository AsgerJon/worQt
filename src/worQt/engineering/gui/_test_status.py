"""
TestStatus subclasses 'PaintedWidget' and is the strip along the bottom
of the window saying what is going on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, QTimer
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ...paint_ops import AbstractPaintOp, PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter
  from ...utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
#  The states the strip knows, each with the colour of its dot
_MODES = {
  'idle'    : Color(110, 114, 122),
  'casting' : Color(97, 175, 239),
  'running' : Color(152, 195, 121),
  'paused'  : Color(229, 192, 123),
  'finished': Color(198, 120, 221),
}
_MOVING = ('running', 'casting')


class PaintTestStatus(AbstractPaintOp):
  """
  PaintTestStatus subclasses 'AbstractPaintOp' and paints a 'TestStatus':
  its divider along the top, the dot, what is going on in words and the
  details; while moving, a striped bar along its right, the stripes
  shifted a little each frame.
  """

  #  Annotations
  widget: TestStatus

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the strip."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(widget.dividerColor.solidPen)
    painter.drawLine(QPointF(0.0, 0.5), QPointF(float(widget.width()), 0.5))
    middle = widget.height() / 2
    painter.setPen(self.emptyPen)
    painter.setBrush(widget.dotColor.fillBrush)
    painter.drawEllipse(QPointF(16.0, middle), 5.0, 5.0)
    painter.setBrush(self.emptyBrush)
    painter.setFont(widget.boldFont)
    painter.setPen(widget.boldFont.color.Q)
    named = widget.boldFont.metrics.horizontalAdvance(widget.text)
    painter.drawText(
      QRectF(30.0, 0.0, named + 4.0, widget.height()),
      _LEFT, widget.text
      )
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    bar = widget.barRect()
    left = 30.0 + named + 18.0
    room = (bar.left() if widget.moving else widget.width()) - left - 12.0
    painter.drawText(
      QRectF(left, 0.0, max(room, 0.0), widget.height()),
      _LEFT, widget.details
      )
    if widget.moving:
      self._paintBar(painter, bar)
    return rect

  def _paintBar(self, painter: WPainter, bar: QRectF) -> None:
    """The striped bar, its stripes shifted by the frame."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.setBrush(widget.trackColor.fillBrush)
    painter.drawRoundedRect(bar, 3.0, 3.0)
    painter.save()
    painter.setClipRect(bar)
    stripe = QColor(widget.dotColor.Q)
    painter.setBrush(stripe)
    width = 12.0
    shift = (widget.frame * 2.0) % (2 * width)
    x = bar.left() - 2 * width + shift
    while x < bar.right():
      painter.drawPolygon(
          QPolygonF(
              [
                QPointF(x, bar.bottom()), QPointF(x + width / 2, bar.top()),
                QPointF(x + width, bar.top()),
                QPointF(x + width / 2, bar.bottom()),
              ]
          )
      )
      x += 2 * width
    painter.restore()
    painter.setBrush(self.emptyBrush)


class TestStatus(PaintedWidget):
  """
  TestStatus subclasses 'PaintedWidget' and is the strip along the bottom
  of the window saying what is going on: a dot in the colour of the
  state, what is going on in words, 'text', and the 'details'. The
  states, 'mode', are 'idle', 'casting', 'running', 'paused' and
  'finished'; while casting or running, a striped bar along its right
  keeps moving, 'frame' by frame, so work going on cannot be taken for
  work stopped. 'showState' shows a state.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_divider_color__ = Color(58, 61, 65)
  __fallback_track_color__ = Color(52, 55, 60)
  __fallback_frame_ms__ = 60  # milliseconds between frames of the bar
  __fallback_bar_width__ = 180.0  # pixels

  #  Private Variables
  __status_mode__: str = 'idle'
  __status_text__: str = ''
  __status_details__: str = ''
  __status_frame__: int = 0

  #  Public Variables
  boxModelOp = PaintBoxModel()
  statusOp = PaintTestStatus()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )
  boldFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      10,
      Color(230, 230, 230),
  )
  frameTimer = AttriBox[QTimer](THIS)

  #  Virtual Variables
  mode: Field[str] = Field()
  text: Field[str] = Field()
  details: Field[str] = Field()
  frame: Field[int] = Field()
  moving: Field[bool] = Field()
  dotColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  trackColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mode.GET
  def _getMode(self, ) -> str:
    """The 'mode' getter returns the state shown."""
    return self.__status_mode__

  @text.GET
  def _getText(self, ) -> str:
    """The 'text' getter returns what is going on, in words."""
    return self.__status_text__

  @details.GET
  def _getDetails(self, ) -> str:
    """The 'details' getter returns the details of what is going on."""
    return self.__status_details__

  @frame.GET
  def _getFrame(self, ) -> int:
    """The 'frame' getter returns how many frames the bar has moved."""
    return self.__status_frame__

  @moving.GET
  def _getMoving(self, ) -> bool:
    """The 'moving' getter tells whether the bar is moving: while
    casting or running."""
    return True if self.mode in _MOVING else False

  @dotColor.GET
  def _getDotColor(self, ) -> Color:
    return _MODES[self.mode]

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  @trackColor.GET
  def _getTrackColor(self, ) -> Color:
    return self.__fallback_track_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(600, self.font.metrics.height() + 16)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(200, self.sizeHint().height())

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
    self.frameTimer.setInterval(self.__fallback_frame_ms__)
    self.frameTimer.timeout.connect(self._nextFrame)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showState(self, mode: str, text: str, details: str) -> None:
    """The 'showState' method shows the state 'mode', what is going on in
    words, 'text', and its 'details'; the bar moves while casting or
    running."""
    if mode not in _MODES:
      raise ValueError('no such state: %s' % mode)
    self.__status_mode__ = mode
    self.__status_text__ = text
    self.__status_details__ = details
    if self.moving and not self.frameTimer.isActive():
      self.frameTimer.start()
    if not self.moving:
      self.frameTimer.stop()
    self.update()

  def barRect(self, ) -> QRectF:
    """The 'barRect' method returns where the moving bar is drawn, along
    the right."""
    width = self.__fallback_bar_width__
    height = 8.0
    return QRectF(
      self.width() - width - 14.0,
      (self.height() - height) / 2, width, height
      )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _nextFrame(self, ) -> None:
    """Moves the bar on a frame."""
    self.__status_frame__ += 1
    self.update()
