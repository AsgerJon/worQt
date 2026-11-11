"""
RunIngredientPanel covers 'IngredientPanel', the sliders setting what the
stones, the paste and the bond between them are: how stiff, how strong
and how tough, and the paste's cohesion and friction. They start at the
lattice's own materials, each material is what its sliders show, and
they can be locked while a test runs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.meso import LatticeBase
from worQt.engineering.meso.gui import IngredientPanel

from . import MesoWidgetTest


class RunIngredientPanel(MesoWidgetTest):
  """Tests for 'IngredientPanel'."""

  def openPanel(self) -> IngredientPanel:
    """A panel, shown live."""
    panel = IngredientPanel()
    panel.resize(panel.sizeHint())
    self.showLive(panel)
    return panel

  def run_starts_at_the_lattice(self) -> None:
    """The sliders start at the lattice's own stone, mortar and bond."""
    panel = self.openPanel()
    stone, mortar, bond = panel.materials()
    self.assertEqual(stone, LatticeBase.__fallback_stone_material__)
    self.assertEqual(mortar, LatticeBase.__fallback_mortar_material__)
    self.assertEqual(bond, LatticeBase.__fallback_bond_material__)
    self.assertEqual(panel.headings(), ('Stone', 'Paste', 'Bond'))
    self.assertEqual(len(panel.sliders()), 10)
    self.assertFalse(panel.grab().isNull())

  def run_a_slider_sets_its_material(self) -> None:
    """A slider moved sets its material to what it shows, and the panel
    tells of it."""
    panel = self.openPanel()
    spy = self.spy(panel.materialsChanged)
    panel.pasteTension.quantity = 6.0
    self.assertEqual(panel.materials()[1].tension, 6.0)
    self.assertGreater(spy.count, 0)
    panel.stoneStiffness.quantity = 50.0
    self.assertEqual(panel.materials()[0].stiffness, 50000.0)
    panel.bondToughness.quantity = 40.0
    self.assertAlmostEqual(panel.materials()[2].toughness, 0.04)

  def run_locked(self) -> None:
    """Locked, every slider is greyed out; unlocked, none is."""
    panel = self.openPanel()
    panel.setLocked(True)
    self.assertFalse(any(slider.isEnabled() for slider in panel.sliders()))
    panel.setLocked(False)
    self.assertTrue(all(slider.isEnabled() for slider in panel.sliders()))
