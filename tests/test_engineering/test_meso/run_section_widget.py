"""
RunSectionWidget covers 'SectionWidget', the section through a
cylinder's axis drawn to scale: the mortar, the stones in it, the
platens above and below, and, once it is tested, its cracks, each where
a face has opened.

The paste can be made clear: shown the whole cylinder, the stones behind
the cut then show through it, the deeper the fainter, as light through
that much paste would show them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRectF

from worQt.engineering.meso import Grading, Lattice, TensionTest
from worQt.engineering.meso import WholeCylinder
from worQt.engineering.meso.gui import SectionWidget

from . import MesoWidgetTest, smallLattice


class RunSectionWidget(MesoWidgetTest):
  """Tests for 'SectionWidget'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.lattice = smallLattice(7)
    cls.tested = TensionTest(cls.lattice)
    cls.tested.run()

  def openWidget(self) -> SectionWidget:
    """A widget the size of a window's half, shown live."""
    widget = SectionWidget()
    widget.resize(320, 520)
    self.showLive(widget)
    return widget

  def run_draws_to_scale(self) -> None:
    """The section is drawn to scale, as large as fits, within the
    widget; its bottom left corner where x is -20 mm and y nought, its
    top right where x is 20 mm and y 80 mm."""
    widget = self.openWidget()
    widget.lattice = self.lattice
    box = widget.sectionRect()
    self.assertAlmostEqual(box.height() / box.width(), 2.0, delta=0.01)
    self.assertTrue(QRectF(widget.rect()).contains(box))
    corner = widget.toScreen(-20.0, 0.0)
    self.assertAlmostEqual(corner.x(), box.left())
    self.assertAlmostEqual(corner.y(), box.bottom())
    corner = widget.toScreen(20.0, 80.0)
    self.assertAlmostEqual(corner.x(), box.right())
    self.assertAlmostEqual(corner.y(), box.top())

  def run_nothing_cracked_yet(self) -> None:
    """Untested, or tested but not yet loaded, nothing is cracked."""
    widget = self.openWidget()
    widget.lattice = self.lattice
    self.assertEqual(widget.crackSegments(), [])
    widget.test = TensionTest(self.lattice)
    self.assertIs(widget.lattice, self.lattice)
    self.assertEqual(widget.crackSegments(), [])

  def run_shows_the_cracks(self) -> None:
    """Pulled apart, the cracks show on the faces that opened, all in
    the section."""
    widget = self.openWidget()
    widget.test = self.tested
    segments = widget.crackSegments()
    self.assertGreater(len(segments), 0)
    box = widget.sectionRect().adjusted(-1.0, -1.0, 1.0, 1.0)
    for start, end, width in segments:
      self.assertTrue(box.contains(start))
      self.assertTrue(box.contains(end))
      self.assertGreater(width, 0.0)

  def run_paints(self) -> None:
    """It paints with nothing, with a section and with a tested one."""
    widget = self.openWidget()
    self.assertFalse(widget.grab().isNull())
    widget.lattice = self.lattice
    self.assertFalse(widget.grab().isNull())
    widget.test = self.tested
    self.assertFalse(widget.grab().isNull())

  def openWhole(self) -> SectionWidget:
    """The widget showing a whole small cylinder."""
    widget = self.openWidget()
    whole = WholeCylinder(40.0, 80.0, Grading.fuller(8.0, 0.5), 7)
    widget.cylinder = whole
    widget.lattice = Lattice(whole, 1.0)
    return widget

  def run_solid_paste_at_first(self) -> None:
    """The paste is solid at first, and kept from clear to solid."""
    widget = self.openWidget()
    self.assertEqual(widget.pasteOpacity, 1.0)
    widget.pasteOpacity = 1.7
    self.assertEqual(widget.pasteOpacity, 1.0)
    widget.pasteOpacity = -1.0
    self.assertEqual(widget.pasteOpacity, 0.0)

  def run_the_stones_behind(self) -> None:
    """The stones behind the cut are those with their centres behind it,
    each at the depth its front is at, the deepest first."""
    widget = self.openWhole()
    centres = widget.cylinder.centres
    behind = widget.behindStones()
    self.assertEqual(len(behind), int((centres[:, 2] > 0).sum()))
    fronts = [front for _, front in behind]
    self.assertEqual(fronts, sorted(fronts, reverse=True))
    self.assertGreaterEqual(min(fronts), 0.0)
    for stone, front in behind:
      self.assertAlmostEqual(front, max(stone.corners[:, 2].min().item(),
                                        0.0))

  def run_the_paste_layers(self) -> None:
    """The paste behind the cut is drawn in layers, the deepest first,
    each narrower than the one before it as the round cylinder thins
    towards its back. Solid, the nearest hides all behind it; clear,
    none hides anything; between, each as much as its depth of paste."""
    widget = self.openWhole()
    layers = widget.pasteLayers()
    near, alpha = layers[-1]
    self.assertEqual(alpha, 1.0)
    self.assertAlmostEqual(near.width(), widget.sectionRect().width())
    widths = [rect.width() for rect, _ in layers]
    self.assertEqual(widths, sorted(widths))
    widget.pasteOpacity = 0.0
    self.assertEqual({alpha for _, alpha in widget.pasteLayers()}, {0.0})
    widget.pasteOpacity = 0.5
    alphas = [alpha for _, alpha in widget.pasteLayers()]
    self.assertTrue(all(0.0 < alpha < 1.0 for alpha in alphas))

  def run_seeing_through(self) -> None:
    """Clear paste shows what solid paste hides."""
    widget = self.openWhole()
    solid = widget.grab().toImage()
    widget.pasteOpacity = 0.0
    clear = widget.grab().toImage()
    self.assertNotEqual(solid, clear)
