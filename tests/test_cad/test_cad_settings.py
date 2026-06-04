"""
Exercises 'CADSettings', the drawing app's 'Settings' subclass: its two
tabs, the value types, a save/load round-trip, and - importantly - that its
defaults still match the canvas constants in 'CADWidget' (a drift guard, so
the palette and view defaults stay a single source of truth). All pure: no
'QApplication' is constructed (only 'CADWidget' class attributes are read).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worktoy.work_test import BaseTest

from worQt.cad import CADSettings
from worQt.cad import CADWidget


class TestCADSettings(BaseTest):
  """Covers the drawing app's settings schema and its canvas defaults."""

  def test_two_tabs_and_app_name(self, ) -> None:
    """It is named for the app and carries the colours and defaults tabs."""
    settings = CADSettings()
    self.assertEqual(settings.appName, 'worQtCAD')
    self.assertEqual(settings.names(), ['colours', 'defaults'])

  def test_colours_tab_is_the_palette(self, ) -> None:
    """The colours tab carries every canvas hue as a hex string. It is the
    single source of truth: 'CADWidget' no longer holds colour constants,
    it reads them from here via '_color'."""
    colours = CADSettings().tab('colours')
    expected = {'background', 'grid', 'axes', 'module', 'moduleSelected',
                'node', 'member', 'support', 'load', 'settlement',
                'dimension', 'preview', 'halo'}
    self.assertEqual(set(colours.names()), expected)
    for name in expected:
      self.assertTrue(colours[name].startswith('#'))
      self.assertIs(colours.setting(name).valueType, str)

  def test_defaults_match_canvas_constants(self, ) -> None:
    """Every numeric default equals the matching 'CADWidget' constant."""
    defaults = CADSettings().tab('defaults')
    self.assertEqual(defaults['snapPixels'],
                     getattr(CADWidget, '__snap_px__'))
    self.assertEqual(defaults['pointRadius'],
                     getattr(CADWidget, '__point_radius__'))
    self.assertEqual(defaults['nodeRadius'],
                     getattr(CADWidget, '__node_radius__'))
    self.assertEqual(defaults['perpTolPx'],
                     getattr(CADWidget, '__perp_tol_px__'))
    self.assertEqual(defaults['defaultScale'],
                     getattr(CADWidget, '__default_scale__'))
    self.assertEqual(defaults['minScale'],
                     getattr(CADWidget, '__min_scale__'))
    self.assertEqual(defaults['maxScale'],
                     getattr(CADWidget, '__max_scale__'))

  def test_value_types(self, ) -> None:
    """Colours are str; pixel counts are int; zoom factors are float."""
    settings = CADSettings()
    colours = settings.tab('colours')
    defaults = settings.tab('defaults')
    self.assertIs(colours.setting('grid').valueType, str)
    self.assertIs(defaults.setting('gridTargetPx').valueType, int)
    self.assertIs(defaults.setting('defaultScale').valueType, float)

  def test_round_trip(self, ) -> None:
    """Edited colours and defaults survive a save/load round-trip."""
    settings = CADSettings()
    settings.setPath(os.path.join(tempfile.mkdtemp(), '.worQtCAD.config'))
    settings.tab('colours')['member'] = '#123456'
    settings.tab('defaults')['gridTargetPx'] = 32
    settings.save()
    fresh = CADSettings()
    fresh.setPath(settings.path())
    fresh.load()
    self.assertEqual(fresh.tab('colours')['member'], '#123456')
    self.assertEqual(fresh.tab('defaults')['gridTargetPx'], 32)
