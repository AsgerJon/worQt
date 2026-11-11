"""
RunCurveWidget covers 'CurveWidget', the stress-strain curve of a test
as it runs: strain in per mille along, stress in MPa up, both as
positive numbers, the axes reaching past the curve, and the strength
read off it: fc crushed, ft pulled apart.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.meso import CompressionTest, TensionTest
from worQt.engineering.meso.gui import CurveWidget

from . import MesoWidgetTest, smallLattice


class RunCurveWidget(MesoWidgetTest):
  """Tests for 'CurveWidget'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    lattice = smallLattice(7)
    cls.tension = TensionTest(lattice)
    cls.tension.run()
    cls.compression = CompressionTest(lattice)
    cls.compression.run()

  def openWidget(self) -> CurveWidget:
    """A widget the size of a window's half, shown live."""
    widget = CurveWidget()
    widget.resize(560, 420)
    self.showLive(widget)
    return widget

  def run_nothing_to_show(self) -> None:
    """With no test it shows empty axes and reads off nothing."""
    widget = self.openWidget()
    self.assertEqual(widget.peakText(), '')
    self.assertEqual(widget.curvePoints(), [])
    self.assertFalse(widget.grab().isNull())

  def run_the_axes(self) -> None:
    """Nought is at the bottom left of the plot, the axes' ends at its
    top right, and the axes reach past the whole curve."""
    widget = self.openWidget()
    widget.test = self.compression
    box = widget.plotRect()
    strainEnd, stressEnd = widget.axisEnds()
    origin = widget.toScreen(0.0, 0.0)
    self.assertAlmostEqual(origin.x(), box.left())
    self.assertAlmostEqual(origin.y(), box.bottom())
    corner = widget.toScreen(strainEnd, stressEnd)
    self.assertAlmostEqual(corner.x(), box.right())
    self.assertAlmostEqual(corner.y(), box.top())
    self.assertGreaterEqual(stressEnd, self.compression.strength)
    self.assertGreaterEqual(strainEnd, abs(self.compression.strain) * 1e3)

  def run_the_curve(self) -> None:
    """The curve is a point for each strain and stress recorded, every
    one in the plot."""
    widget = self.openWidget()
    widget.test = self.compression
    points = widget.curvePoints()
    self.assertEqual(len(points), len(self.compression.curve))
    box = widget.plotRect().adjusted(-1.0, -1.0, 1.0, 1.0)
    for point in points:
      self.assertTrue(box.contains(point))
    self.assertFalse(widget.grab().isNull())

  def run_the_strength(self) -> None:
    """Crushed, it reads off fc, pulled apart ft, each in MPa at its
    strain in per mille."""
    widget = self.openWidget()
    widget.test = self.compression
    text = widget.peakText()
    self.assertTrue(text.startswith('fc = '))
    self.assertIn(' MPa at ', text)
    self.assertTrue(text.endswith(' ‰'))
    widget.test = self.tension
    self.assertTrue(widget.peakText().startswith('ft = '))
