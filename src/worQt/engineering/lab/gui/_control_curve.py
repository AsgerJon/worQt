"""
ControlCurve subclasses 'PaintedWidget' and plots a beam test's control
loop: its command and its feedback against time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, QSize
from PySide6.QtGui import QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import niceAbove, niceSpan
from .. import BeamExperiment

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_CENTER = Qt.AlignmentFlag.AlignCenter
_TICK = 5.0  # pixels: how long a tick is


class PaintControlCurve(AbstractPaintOp):
  """
  PaintControlCurve subclasses 'AbstractPaintOp' and paints a
  'ControlCurve': the title and the error above, the axes with their
  gridlines, ticks and names, the command dashed and the feedback
  solid.
  """

  #  Annotations
  widget: ControlCurve

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the plot."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = widget.plotRect()
    painter.setFont(widget.titleFont)
    painter.setPen(widget.titleFont.color.Q)
    painter.drawText(
      QRectF(box.left(), 6.0, box.width(), 20.0), _LEFT,
      widget.title()
      )
    painter.setFont(widget.font)
    painter.setPen(widget.textColor.Q)
    painter.drawText(
      QRectF(box.left(), 28.0, box.width(), 16.0), _LEFT,
      widget.errorText()
      )
    self._paintAxes(painter)
    command, feedback = widget.curves()
    if len(command) > 1:
      pen = QPen(widget.commandColor.Q, 1.5)
      pen.setStyle(Qt.PenStyle.DashLine)
      painter.setPen(pen)
      painter.drawPolyline(QPolygonF(command))
      painter.setPen(QPen(widget.feedbackColor.Q, 1.8))
      painter.drawPolyline(QPolygonF(feedback))
    return rect

  def _paintAxes(self, painter: WPainter) -> None:
    """The gridlines and ticks, the axes, the reading's through nought,
    and their names."""
    widget = self.widget
    box = widget.plotRect()
    timeEnd, timeStep = widget.timeAxis()
    bottom, top, up = widget.readingAxis()
    grid = QPen(widget.gridColor.Q, 1.0)
    axis = QPen(widget.axisColor.Q, 1.0)
    for index in range(int(round(timeEnd / timeStep)) + 1):
      value = index * timeStep
      x = widget.toScreen(value, 0.0).x()
      painter.setPen(grid)
      painter.drawLine(QLineF(x, box.top(), x, box.bottom()))
      painter.setPen(axis)
      painter.drawLine(QLineF(x, box.bottom(), x, box.bottom() + _TICK))
      label = QRectF(x - 30.0, box.bottom() + _TICK, 60.0, 16.0)
      painter.drawText(label, _CENTER, '%g' % round(value, 6))
    for index in range(int(round((top - bottom) / up)) + 1):
      value = bottom + index * up
      y = widget.toScreen(0.0, value).y()
      painter.setPen(grid)
      painter.drawLine(QLineF(box.left(), y, box.right(), y))
      painter.setPen(axis)
      painter.drawLine(QLineF(box.left() - _TICK, y, box.left(), y))
      label = QRectF(box.left() - 60.0, y - 8.0, 60.0 - 2 * _TICK, 16.0)
      painter.drawText(label, _RIGHT, '%g' % round(value, 6))
    painter.setPen(axis)
    nought = widget.toScreen(0.0, 0.0).y()
    painter.drawLine(QLineF(box.left(), nought, box.right(), nought))
    painter.drawLine(
      QLineF(
        box.left(), box.top(), box.left(),
        box.bottom()
        )
      )
    painter.setPen(widget.textColor.Q)
    under = QRectF(box.left(), box.bottom() + 22.0, box.width(), 16.0)
    painter.drawText(under, _CENTER, 'time s')
    painter.drawText(
      QRectF(4.0, box.top() - 24.0, 56.0, 14.0), _LEFT,
      'mm'
      )


class ControlCurve(PaintedWidget):
  """
  ControlCurve subclasses 'PaintedWidget' and plots the control loop of
  the 'experiment' as it runs: its command, dashed, and its feedback,
  the reading of the transducer it reads, solid, in mm up, up positive
  as the transducer reads, either side of nought, against time in
  seconds along; above, the command and the feedback now, and how
  far apart they are. A loop tuned well keeps the two
  together; one tuned badly lags, overshoots or hunts about the
  command.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_axis_color__ = Color(140, 144, 152)
  __fallback_grid_color__ = Color(48, 50, 55)
  __fallback_command_color__ = Color(220, 220, 220)
  __fallback_feedback_color__ = Color(152, 195, 121)
  __fallback_text_color__ = Color(170, 174, 182)
  __fallback_plot_margins__ = (64.0, 58.0, 28.0, 46.0)  # l, t, r, b
  __fallback_least_ends__ = (60.0, 5.0)  # s and mm

  #  Private Variables
  __plotted_test__: BeamExperiment | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  curveOp = PaintControlCurve()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )
  titleFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      12,
      Color(212, 212, 212),
  )

  #  Virtual Variables
  experiment: Field[BeamExperiment] = Field()
  axisColor: Field[Color] = Field()
  gridColor: Field[Color] = Field()
  commandColor: Field[Color] = Field()
  feedbackColor: Field[Color] = Field()
  textColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @experiment.GET
  def _getExperiment(self, ) -> BeamExperiment | None:
    """The 'experiment' getter returns the test plotted, or 'None'."""
    return self.__plotted_test__

  @axisColor.GET
  def _getAxisColor(self, ) -> Color:
    return self.__fallback_axis_color__

  @gridColor.GET
  def _getGridColor(self, ) -> Color:
    return self.__fallback_grid_color__

  @commandColor.GET
  def _getCommandColor(self, ) -> Color:
    return self.__fallback_command_color__

  @feedbackColor.GET
  def _getFeedbackColor(self, ) -> Color:
    return self.__fallback_feedback_color__

  @textColor.GET
  def _getTextColor(self, ) -> Color:
    return self.__fallback_text_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @experiment.SET
  def _setExperiment(self, experiment: BeamExperiment | None) -> None:
    """The 'experiment' setter plots 'experiment', or nothing for
    'None'."""
    self.__plotted_test__ = experiment
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(440, 320)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(300, 220)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def title(self, ) -> str:
    """The 'title' method names the loop plotted."""
    experiment = self.experiment
    if experiment is None:
      return 'Control'
    rig = experiment.rig
    return 'Control: T%d drives A%d' % (
      rig.control.transducer + 1,
      rig.driven + 1
    )

  def errorText(self, ) -> str:
    """The 'errorText' method says the command and the feedback now, and
    how far apart they are."""
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return 'command dashed, feedback solid'
    latest = experiment.latest
    error = latest.command - latest.feedback
    return 'command %.2f, reads %.2f, error %+.3f mm' % (
      latest.command, latest.feedback, error
    )

  def plotRect(self, ) -> QRectF:
    """The 'plotRect' method returns where the axes are."""
    left, top, right, bottom = self.__fallback_plot_margins__
    width = max(self.width() - left - right, 1.0)
    height = max(self.height() - top - bottom, 1.0)
    return QRectF(left, top, width, height)

  def timeAxis(self, ) -> tuple[float, float]:
    """The 'timeAxis' method returns where the time axis ends, a round
    number of seconds past the curves, and its step."""
    least, _ = self.__fallback_least_ends__
    experiment = self.experiment
    end = least
    if experiment is not None and experiment.readings:
      end = max(least, niceAbove(1.05 * experiment.readings[-1].time))
    return end, niceAbove(end / 6)

  def readingAxis(self, ) -> tuple[float, float, float]:
    """The 'readingAxis' method returns the reading axis's ends and
    step, either side of nought, round numbers past the curves; before a
    test, the way the command ramps."""
    _, least = self.__fallback_least_ends__
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return niceSpan(-least, 0.0, least)
    values = []
    for reading in experiment.readings:
      values += [reading.command, reading.feedback]
    return niceSpan(1.1 * min(values), 1.1 * max(values), least)

  def toScreen(self, time: float, reading: float) -> QPointF:
    """The 'toScreen' method returns the pixel a time in seconds and a
    reading in mm are plotted at."""
    box = self.plotRect()
    end, _ = self.timeAxis()
    bottom, top, _ = self.readingAxis()
    return QPointF(
      box.left() + time / end * box.width(),
      box.bottom() - (reading - bottom) / (top - bottom)
      * box.height()
      )

  def curves(self, ) -> tuple[list[QPointF], list[QPointF]]:
    """The 'curves' method returns the command and the feedback, as
    pixels, from the start."""
    experiment = self.experiment
    if experiment is None:
      return [], []
    start = self.toScreen(0.0, 0.0)
    readings = experiment.readings
    command = [start] + [self.toScreen(r.time, r.command)
                         for r in readings]
    feedback = [start] + [self.toScreen(r.time, r.feedback)
                          for r in readings]
    return command, feedback
