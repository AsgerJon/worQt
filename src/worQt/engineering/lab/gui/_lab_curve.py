"""
LabCurve subclasses 'PaintedWidget' and plots a beam test's force
against the displacements measured, as the test runs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import niceSpan
from .. import BeamExperiment
from ._paint_lab_curve import PaintLabCurve

#  The transducers' colours, in turn
TRANSDUCER_COLORS = (
    Color(97, 175, 239),
    Color(152, 195, 121),
    Color(198, 120, 221),
    Color(86, 182, 194),
    Color(224, 108, 117),
    Color(209, 154, 102),
)


class LabCurve(PaintedWidget):
  """
  LabCurve subclasses 'PaintedWidget' and plots the 'experiment' as it
  runs: the total force of the actuators on the beam in kN up, against
  what each displacement measured reads along, in mm, all up positive:
  the stroke of the actuator the control drives, and each transducer,
  in its own colour, named in the legend above. The axes reach either
  side of nought to round numbers past the curves, never less than
  10 mm and 50 kN long. The peak is marked and read off above,
  what happened to the beam said above and marked on the driven
  actuator's curve, and why the test ended said.
  'toScreen' maps a displacement and a force to the pixel they are
  plotted at.
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
  __fallback_actuator_color__ = Color(220, 220, 220)
  __fallback_peak_color__ = Color(229, 192, 123)
  __fallback_text_color__ = Color(170, 174, 182)
  __fallback_plot_margins__ = (64.0, 74.0, 28.0, 46.0)  # l, t, r, b
  __fallback_least_ends__ = (10.0, 50.0)  # mm and kN

  #  Private Variables
  __plotted_test__: BeamExperiment | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  curveOp = PaintLabCurve()
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
  actuatorColor: Field[Color] = Field()
  peakColor: Field[Color] = Field()
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

  @actuatorColor.GET
  def _getActuatorColor(self, ) -> Color:
    return self.__fallback_actuator_color__

  @peakColor.GET
  def _getPeakColor(self, ) -> Color:
    return self.__fallback_peak_color__

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
    return QSize(900, 320)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(360, 220)

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

  def plotRect(self, ) -> QRectF:
    """The 'plotRect' method returns where the axes are."""
    left, top, right, bottom = self.__fallback_plot_margins__
    width = max(self.width() - left - right, 1.0)
    height = max(self.height() - top - bottom, 1.0)
    return QRectF(left, top, width, height)

  def axes(self, ) -> tuple[tuple[float, float, float], ...]:
    """The 'axes' method returns each axis's ends and step: the
    displacement in mm and the force in kN, round numbers past the
    curves, nought on each; before a test, the way the rig pushes."""
    leastFar, leastForce = self.__fallback_least_ends__
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return (niceSpan(-leastFar, 0.0, leastFar),
              niceSpan(-leastForce, 0.0, leastForce))
    places, forces = [], []
    for reading in experiment.readings:
      places += [reading.stroke, *reading.transducers]
      forces.append(reading.force)
    return (niceSpan(1.05 * min(places), 1.05 * max(places), leastFar),
            niceSpan(1.1 * min(forces), 1.1 * max(forces), leastForce))

  def toScreen(self, displacement: float, force: float) -> QPointF:
    """The 'toScreen' method returns the pixel a displacement in mm and
    a force in kN are plotted at."""
    box = self.plotRect()
    (left, right, _), (bottom, top, _) = self.axes()
    return QPointF(
        box.left() + (displacement - left) / (right - left) * box.width(),
        box.bottom() - (force - bottom) / (top - bottom) * box.height())

  def series(self, ) -> list[tuple[str, Color, list[QPointF]]]:
    """The 'series' method returns each curve: its name, its colour and
    its points, the driven actuator's first, then each transducer's."""
    experiment = self.experiment
    if experiment is None:
      return []
    readings = experiment.readings
    name = 'A%d stroke' % (experiment.rig.driven + 1)
    out = [(name, self.actuatorColor,
            [self.toScreen(0.0, 0.0)]
            + [self.toScreen(r.stroke, r.force) for r in readings])]
    for index in range(len(experiment.rig.transducers)):
      color = TRANSDUCER_COLORS[index % len(TRANSDUCER_COLORS)]
      points = [self.toScreen(0.0, 0.0)]
      points += [self.toScreen(r.transducers[index], r.force)
                 for r in readings]
      out.append(('T%d' % (index + 1), color, points))
    return out

  def peakPoint(self, ) -> QPointF | None:
    """The 'peakPoint' method returns where the peak is plotted on the
    actuator's curve, or 'None' before there is one."""
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return None
    peak = experiment.peak
    return self.toScreen(peak.stroke, peak.force)

  def peakText(self, ) -> str:
    """The 'peakText' method reads the peak off: its total force at the
    driven actuator's stroke."""
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return ''
    peak = experiment.peak
    return 'Peak %.1f kN at %.2f mm' % (peak.force, peak.stroke)

  def eventsText(self, ) -> str:
    """The 'eventsText' method says what happened to the beam, at
    which total force, and why the test ended, if it has."""
    experiment = self.experiment
    if experiment is None:
      return ''
    words = ['%s %.1f kN' % (event.name, event.force)
             for event in experiment.events]
    if experiment.finished:
      words.append('ended: %s' % experiment.ending)
    return ' · '.join(words)

  def eventPoints(self, ) -> list[tuple[str, QPointF]]:
    """The 'eventPoints' method returns what happened to the beam, each
    where it is plotted on the actuator's curve."""
    experiment = self.experiment
    if experiment is None:
      return []
    return [(event.name, self.toScreen(event.stroke, event.force))
            for event in experiment.events]
