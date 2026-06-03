"""
Class-level checks for 'CADApp', the structural-drawing / FEA-modeller
application. These assert its wiring (base class, window and settings class
hooks, export) without constructing a second 'QApplication', so they run
in-process with no Qt event loop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.app import CADApp, AbstractApplication
from worQt.cad import CADSettings
from worQt.window import CADWindow


class TestCADApp(BaseTest):
  """Covers the CAD application's class wiring."""

  def test_subclasses_abstract_application(self, ) -> None:
    """'CADApp' is an 'AbstractApplication'."""
    self.assertTrue(issubclass(CADApp, AbstractApplication))

  def test_window_class_is_cad_window(self, ) -> None:
    """Its 'window' builds a 'CADWindow'."""
    self.assertIs(CADApp.__window_class__, CADWindow)

  def test_settings_class_is_cad_settings(self, ) -> None:
    """Its 'settings' builds a 'CADSettings'."""
    self.assertIs(CADApp.__settings_class__, CADSettings)

  def test_is_exported(self, ) -> None:
    """'CADApp' is exported from the app package."""
    import worQt.app as appPackage
    self.assertIn('CADApp', appPackage.__all__)
