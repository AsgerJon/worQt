"""
RunTestReport covers 'TestReport', a test's results written to a PDF
file: what the cylinder is, what its lattice is, what it is made of, and
what came out, with the stress-strain curve and the cylinder as drawn;
saying plainly that it is simulated, not measured.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worQt.engineering.meso import Lattice, TensionTest
from worQt.engineering.meso.gui import CurveWidget, SectionWidget
from worQt.engineering.meso.gui import TestReport

from . import MesoWidgetTest, smallCylinder


class RunTestReport(MesoWidgetTest):
  """Tests for 'TestReport'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.cylinder = smallCylinder(7)
    cls.lattice = Lattice(cls.cylinder, 1.0)
    cls.test = TensionTest(cls.lattice)
    cls.test.run()

  def report(self) -> TestReport:
    """The report of the tension test on the small cylinder."""
    return TestReport(self.cylinder, self.lattice, self.test)

  def run_what_it_says(self) -> None:
    """It names the test, and says what the cylinder, the lattice, the
    ingredients and the results are, and that it is simulated."""
    report = self.report()
    self.assertEqual(report.title(), 'Tension test')
    sections = dict(report.sections())
    self.assertEqual(list(sections), ['Specimen', 'Lattice', 'Ingredients',
                                      'Result'])
    specimen = dict(sections['Specimen'])
    self.assertEqual(specimen['Cylinder'], 'Ø40 × 80 mm')
    self.assertIn('8 mm', specimen['Aggregate'])
    result = dict(sections['Result'])
    self.assertTrue(result['Strength'].startswith('ft = '))
    self.assertIn('finished', result['State'])
    self.assertIn('cpu', result['Reckoned on'])
    self.assertIn('simulated', report.note().lower())

  def run_writes_a_pdf(self) -> None:
    """It writes a PDF file, with the curve and the cylinder drawn in
    it."""
    curve = CurveWidget()
    curve.resize(560, 420)
    curve.test = self.test
    view = SectionWidget()
    view.resize(300, 520)
    view.test = self.test
    self.showLive(curve)
    self.showLive(view)
    folder = tempfile.mkdtemp()
    path = os.path.join(folder, 'tension.pdf')
    self.report().write(path, curve, view)
    with open(path, 'rb') as file:
      head = file.read(5)
    self.assertEqual(head, b'%PDF-')
    self.assertGreater(os.path.getsize(path), 5000)
