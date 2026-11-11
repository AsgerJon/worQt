"""
RunCylinderView covers 'CylinderView', the whole cylinder seen from the
side, to scale, turned about its axis by dragging: its paste, solid or
clear, the stones in it, the platens above and below, and once it is
tested the cracks through it, seen through the paste as the stones are,
the deeper the fainter.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF

from worQt.engineering.meso import CompressionTest, Grading, Lattice3D
from worQt.engineering.meso import TensionTest
from worQt.engineering.meso import WholeCylinder
from worQt.engineering.meso.gui import CylinderView

from . import MesoWidgetTest


class RunCylinderView(MesoWidgetTest):
  """Tests for 'CylinderView'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.cylinder = WholeCylinder(30.0, 60.0, Grading.fuller(8.0, 0.5), 7)
    cls.lattice = Lattice3D(cls.cylinder, 2.0)
    cls.tested = TensionTest(cls.lattice)
    cls.tested.run()
    cls.crushed = CompressionTest(cls.lattice)
    cls.crushed.run()

  def openView(self) -> CylinderView:
    """A view of the cylinder, shown live."""
    view = CylinderView()
    view.resize(320, 520)
    self.showLive(view)
    view.cylinder = self.cylinder
    view.lattice = self.lattice
    return view

  def run_draws_to_scale(self) -> None:
    """The cylinder is drawn to scale, as large as fits; seen square on,
    its bottom left where x is minus the radius and y nought, its top
    right where x is the radius and y its height."""
    view = self.openView()
    box = view.viewRect()
    self.assertAlmostEqual(box.height() / box.width(), 2.0, delta=0.01)
    self.assertTrue(QRectF(view.rect()).contains(box))
    corner = view.toScreen(-15.0, 0.0, 0.0)
    self.assertAlmostEqual(corner.x(), box.left())
    self.assertAlmostEqual(corner.y(), box.bottom())
    corner = view.toScreen(15.0, 60.0, 0.0)
    self.assertAlmostEqual(corner.x(), box.right())
    self.assertAlmostEqual(corner.y(), box.top())

  def run_turned(self) -> None:
    """Turned a quarter, what was nearest is at the right: a drag to the
    right turns it so, and the view keeps the turn when let go."""
    view = self.openView()
    view.turn = math.pi / 2
    point = view.toScreen(0.0, 0.0, -15.0)
    self.assertAlmostEqual(point.x(), view.viewRect().right())
    view.turn = 0.0
    middle = QPointF(view.width() / 2, view.height() / 2)
    self.press(view, middle)
    self.move(view, middle + QPointF(60.0, 0.0))
    self.release(view, middle + QPointF(60.0, 0.0))
    self.assertGreater(view.turn, 0.0)
    self.assertFalse(view.dragging)

  def run_the_paste_layers(self) -> None:
    """The paste is drawn in layers, the deepest first, each as wide as
    the round cylinder is at its depth: those through the middle as wide
    as it, those at its back and front narrower. Solid, each hides all
    behind it; clear, none hides anything."""
    view = self.openView()
    layers = view.pasteLayers()
    widths = [rect.width() for rect, _ in layers]
    self.assertAlmostEqual(max(widths), view.viewRect().width())
    self.assertLess(widths[0], max(widths))
    self.assertLess(widths[-1], max(widths))
    self.assertEqual({alpha for _, alpha in layers}, {1.0})
    view.pasteOpacity = 0.0
    self.assertEqual({alpha for _, alpha in view.pasteLayers()}, {0.0})

  def run_the_cracks(self) -> None:
    """Untested, nothing is cracked; pulled apart, the faces that opened
    show as cracks, each in the cylinder's outline, each in a layer."""
    view = self.openView()
    self.assertEqual(view.crackPolygons(), [])
    view.test = self.tested
    cracks = view.crackPolygons()
    self.assertGreater(len(cracks), 0)
    box = view.viewRect().adjusted(-2.0, -2.0, 2.0, 2.0)
    count = len(view.pasteLayers())
    for polygon, width, layer in cracks:
      self.assertTrue(box.contains(polygon.boundingRect()))
      self.assertGreater(width, 0.0)
      self.assertIn(layer, range(count))

  def run_the_sliding_cracks(self) -> None:
    """Crushed, the faces that slid show as cracks too, not only those
    that opened: every face given more than a micrometre either way."""
    view = self.openView()
    view.test = self.crushed
    given = (self.crushed.crackSizes > 1e-3) & (
        self.lattice.phases != 3)
    opened = (self.crushed.openings > 1e-3) & (self.lattice.phases != 3)
    self.assertGreater(int(given.sum()), int(opened.sum()))
    self.assertEqual(len(view.crackPolygons()), int(given.sum()))

  def run_seeing_through(self) -> None:
    """Clear paste shows what solid paste hides; it paints either way,
    and turned."""
    view = self.openView()
    view.test = self.tested
    solid = view.grab().toImage()
    view.pasteOpacity = 0.0
    clear = view.grab().toImage()
    self.assertNotEqual(solid, clear)
    view.turn = 1.0
    self.assertFalse(view.grab().isNull())
