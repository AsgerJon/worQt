"""
CurveWidget subclasses 'PaintedWidget' and shows the stress-strain curve
of a test as it runs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import niceAbove
from .. import UniaxialTest
from . import PaintCurve

class CurveWidget(PaintedWidget):
  """
  CurveWidget subclasses 'PaintedWidget' and shows the stress-strain
  curve of a 'test' as it runs: the strain in per mille along, the
  stress in MPa up, both as positive numbers, crushed or pulled apart.
  The axes reach to round numbers past the curve, never less than a
  concrete's: 3 ‰ and 50 MPa crushed, 0.4 ‰ and 4 MPa pulled apart.
  'toScreen' maps a strain and a stress to the pixel they are plotted
  at.

  It reads off the strength, fc crushed and ft pulled apart, at the
  strain it was reached at, and the stiffness before cracking, E, and
  marks where the strength was reached.
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
  __fallback_curve_color__ = Color(97, 175, 239)
  __fallback_peak_color__ = Color(229, 192, 123)
  __fallback_text_color__ = Color(170, 174, 182)
  __fallback_plot_margins__ = (64.0, 64.0, 28.0, 52.0)  # l, t, r, b
  __fallback_crushed_ends__ = (3.0, 50.0)  # per mille and MPa
  __fallback_pulled_ends__ = (0.4, 4.0)

  #  Private Variables
  __shown_test__: UniaxialTest | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  curveOp = PaintCurve()
  font = AttriBox[WFont](
    GenericFamilyNum.MONO,
    FontWeightNum.NORMAL,
    10,
    Color(170, 174, 182),
  )
  titleFont = AttriBox[WFont](
    GenericFamilyNum.MONO,
    FontWeightNum.BOLD,
    12,
    Color(212, 212, 212),
  )

  #  Virtual Variables
  test: Field[UniaxialTest] = Field()
  axisColor: Field[Color] = Field()
  gridColor: Field[Color] = Field()
  curveColor: Field[Color] = Field()
  peakColor: Field[Color] = Field()
  textColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @test.GET
  def _getTest(self, ) -> UniaxialTest | None:
    """The 'test' getter returns the test shown, or 'None'."""
    return self.__shown_test__

  @axisColor.GET
  def _getAxisColor(self, ) -> Color:
    return self.__fallback_axis_color__

  @gridColor.GET
  def _getGridColor(self, ) -> Color:
    return self.__fallback_grid_color__

  @curveColor.GET
  def _getCurveColor(self, ) -> Color:
    return self.__fallback_curve_color__

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

  @test.SET
  def _setTest(self, test: UniaxialTest) -> None:
    """The 'test' setter shows the curve of 'test'."""
    if not isinstance(test, UniaxialTest):
      raise TypeException('test', test, UniaxialTest)
    self.__shown_test__ = test
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(620, 640)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(320, 260)

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

  def crushing(self, ) -> bool:
    """The 'crushing' method tells whether the test shown crushes, as
    an untested curve is taken to."""
    test = self.test
    return True if test is None or test.direction < 0 else False

  def title(self, ) -> str:
    """The 'title' method names the test."""
    return 'Compression test' if self.crushing() else 'Tension test'

  def plotRect(self, ) -> QRectF:
    """The 'plotRect' method returns where the axes are drawn."""
    left, top, right, bottom = self.__fallback_plot_margins__
    width = max(self.width() - left - right, 1.0)
    height = max(self.height() - top - bottom, 1.0)
    return QRectF(left, top, width, height)

  def axisEnds(self, ) -> tuple[float, float]:
    """The 'axisEnds' method returns where the axes end: the strain in
    per mille and the stress in MPa, round numbers past the curve."""
    if self.crushing():
      strainEnd, stressEnd = self.__fallback_crushed_ends__
    else:
      strainEnd, stressEnd = self.__fallback_pulled_ends__
    test = self.test
    if test is None:
      return strainEnd, stressEnd
    strains = [abs(strain) * 1e3 for strain, _ in test.curve]
    strain = max(strains) if strains else 0.0
    stress = test.strength
    return (max(strainEnd, niceAbove(1.05 * strain)),
            max(stressEnd, niceAbove(1.1 * stress)))

  def axisSteps(self, ) -> tuple[float, float]:
    """The 'axisSteps' method returns how far apart the axes' ticks are,
    a fifth or so of each axis."""
    strainEnd, stressEnd = self.axisEnds()
    return niceAbove(strainEnd / 6), niceAbove(stressEnd / 6)

  def toScreen(self, strain: float, stress: float) -> QPointF:
    """The 'toScreen' method returns the pixel a strain in per mille and
    a stress in MPa are plotted at."""
    box = self.plotRect()
    strainEnd, stressEnd = self.axisEnds()
    x = box.left() + strain / strainEnd * box.width()
    y = box.bottom() - stress / stressEnd * box.height()
    return QPointF(x, y)

  def curvePoints(self, ) -> list[QPointF]:
    """The 'curvePoints' method returns the curve as pixels, a point to
    each strain and stress recorded."""
    test = self.test
    if test is None:
      return []
    return [self.toScreen(abs(strain) * 1e3, abs(stress))
            for strain, stress in test.curve]

  def peakPoint(self, ) -> QPointF | None:
    """The 'peakPoint' method returns where the strength is plotted, or
    'None' before there is any."""
    test = self.test
    if test is None or test.strength <= 0.0:
      return None
    return self.toScreen(test.strengthStrain * 1e3, test.strength)

  def peakText(self, ) -> str:
    """The 'peakText' method reads off the strength: fc crushed, ft
    pulled apart, in MPa, at its strain in per mille."""
    test = self.test
    if test is None or test.strength <= 0.0:
      return ''
    name = 'fc' if self.crushing() else 'ft'
    return '%s = %.3g MPa at %.3g ‰' % (
        name, test.strength, test.strengthStrain * 1e3)

  def stiffnessText(self, ) -> str:
    """The 'stiffnessText' method reads off the stiffness before
    cracking, the test's 'stiffness', in GPa."""
    test = self.test
    if test is None or test.stiffness <= 0.0:
      return ''
    return 'E = %.3g GPa' % (test.stiffness / 1e3)
