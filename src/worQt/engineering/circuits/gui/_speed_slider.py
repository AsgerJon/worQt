"""
SpeedSlider subclasses 'Slider' and sets how fast the circuit runs,
from a thousandth of real time to ten times it, stop by stop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QLineF, QRectF, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp
from ....utils import Color
from ...gui import Slider

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

#  How fast the circuit may run, against real time: the slider's stops
SPEEDS = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0,
          5.0, 10.0)


def speedText(speed: float) -> str:
  """The 'speedText' function returns 'speed' as the slider shows it:
  '1/100×', '1×', '5×'."""
  if speed >= 1.0:
    return '%d×' % round(speed)
  return '1/%d×' % round(1.0 / speed)


def speedWords(speed: float) -> str:
  """The 'speedWords' function returns 'speed' in words: 'real time',
  '1/100 of real time', '5× real time'."""
  if speed == 1.0:
    return 'real time'
  if speed > 1.0:
    return '%d× real time' % round(speed)
  return '1/%d of real time' % round(1.0 / speed)


def nearestStop(speed: float) -> int:
  """The 'nearestStop' function returns the index of the stop nearest
  'speed', by ratio."""
  ratios = [max(speed / stop, stop / speed) for stop in SPEEDS]
  return ratios.index(min(ratios))


class PaintSpeedStops(AbstractPaintOp):
  """
  PaintSpeedStops subclasses 'AbstractPaintOp' and paints the stops of a
  'SpeedSlider': a notch under the track at each, a longer one at real
  time and at the ends.
  """

  #  Annotations
  widget: SpeedSlider

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the notches."""
    widget = self.widget
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(widget.notchColor.Q, 1.5))
    track = widget.trackRect()
    top = track.bottom() + widget.handleRadius() - 1.0
    last = len(SPEEDS) - 1
    for index, speed in enumerate(SPEEDS):
      x = track.left() + track.width() * index / last
      long = speed == 1.0 or index in (0, last)
      painter.drawLine(QLineF(x, top, x, top + (5.0 if long else 3.0)))
    return rect


class SpeedSlider(Slider):
  """
  SpeedSlider subclasses 'Slider' and sets how fast the circuit runs,
  'speed', one of 'SPEEDS', from a thousandth of real time to ten times
  it, a notch under the track at each; the handle snaps to the stops, a
  click, a drag, a notch of the wheel or an arrow moving it a stop.
  'speedChanged' tells of each new speed.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_wheel_step__ = 1.0 / (len(SPEEDS) - 1)
  __fallback_key_step__ = 1.0 / (len(SPEEDS) - 1)
  __fallback_page_step__ = 3.0 / (len(SPEEDS) - 1)
  __fallback_notch_color__ = Color(130, 134, 142)

  #  Private Variables
  __told_stop__: int = -1

  #  Public Variables
  stopsOp = PaintSpeedStops()

  #  Virtual Variables
  stop: Field[int] = Field()
  speed: Field[float] = Field()
  notchColor: Field[Color] = Field()

  #  Signals
  speedChanged = Signal(float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @stop.GET
  def _getStop(self, ) -> int:
    """The 'stop' getter returns the index of the stop the handle is
    at."""
    return round(self.value * (len(SPEEDS) - 1))

  @speed.GET
  def _getSpeed(self, ) -> float:
    """The 'speed' getter returns the speed the handle is at."""
    return SPEEDS[self.stop]

  @notchColor.GET
  def _getNotchColor(self, ) -> Color:
    return self.__fallback_notch_color__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @speed.SET
  def _setSpeed(self, speed: float) -> None:
    """The 'speed' setter moves the handle to the stop nearest 'speed'."""
    self.value = nearestStop(float(speed)) / (len(SPEEDS) - 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    Slider.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    Slider.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    self.text = 'Speed'
    self.value = SPEEDS.index(1.0) / (len(SPEEDS) - 1)
    self.__told_stop__ = self.stop
    self.valueChanged.connect(self._snap)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def valueText(self, ) -> str:
    """The 'valueText' method says the speed: '1/100×', '1×', '5×'."""
    return speedText(self.speed)

  def valueRect(self, ) -> QRectF:
    """The 'valueRect' method returns where the speed is written, room
    for the widest."""
    metrics = self.font.metrics
    widest = max(metrics.horizontalAdvance(speedText(s)) for s in SPEEDS)
    return self._valueRectOf(float(widest) + 4.0)

  def valueAt(self, x: float) -> float:
    """The 'valueAt' method returns the share of the stop nearest 'x'
    along the track."""
    last = len(SPEEDS) - 1
    return round(Slider.valueAt(self, x) * last) / last

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _snap(self, *_) -> None:
    """Puts the handle on the stop nearest it and tells of a new
    speed."""
    stop = self.stop
    snapped = stop / (len(SPEEDS) - 1)
    if abs(snapped - self.value) > 1e-12:
      self.value = snapped
      return
    if stop != self.__told_stop__:
      self.__told_stop__ = stop
      self.speedChanged.emit(SPEEDS[stop])
