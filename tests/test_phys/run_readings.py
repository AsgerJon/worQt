"""
RunReadings covers the readings' dock window ('_readings'; user,
2026-11-14: "put the text from the statusbars into a dockable window"):
what a window's status line said shown a reading a line (its readings
four spaces apart each on its own, trimmed, its own lines kept); the
dock at the window's right, titled 'Readings', moved or floated but
never closed; its text selectable with the mouse, never focused (the
keys stay the view's).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget

from worQt.phys.gui._readings import Readings, ReadingsDock, readingsOf
from worQt.qtest import WidgetTest


class RunReadings(WidgetTest):
  """Tests for the readings' dock window."""

  def run_lines(self) -> None:
    """A status line's readings, four spaces apart, are a line each,
    trimmed; lines of its own are kept; blank readings dropped."""
    readings = Readings()
    readings.setText('  1.000 s    60 frames a second    walking 0.00 '
                     'm/s\n    engine 788 rpm    gear 1  (keys)    ')
    self.assertEqual(readings.text().split('\n'), [
      '1.000 s', '60 frames a second', 'walking 0.00 m/s',
      'engine 788 rpm', 'gear 1  (keys)'])

  def run_docked(self) -> None:
    """Put on a window, the readings are in its 'Readings' dock at its
    right side, which moves and floats but does not close; they are
    selectable with the mouse and take no focus."""
    window = QMainWindow()
    window.setCentralWidget(QWidget())
    readings = readingsOf(window)
    readings.setText('one    two')
    self.showLive(window)
    dock = window.findChild(QDockWidget)
    self.assertIsInstance(dock, ReadingsDock)
    self.assertIs(dock.widget(), readings)
    self.assertEqual(dock.windowTitle(), 'Readings')
    self.assertEqual(window.dockWidgetArea(dock),
                     Qt.DockWidgetArea.RightDockWidgetArea)
    features = QDockWidget.DockWidgetFeature
    self.assertTrue(dock.features() & features.DockWidgetMovable)
    self.assertTrue(dock.features() & features.DockWidgetFloatable)
    self.assertFalse(dock.features() & features.DockWidgetClosable)
    self.assertTrue(readings.textInteractionFlags()
                    & Qt.TextInteractionFlag.TextSelectableByMouse)
    self.assertEqual(readings.focusPolicy(), Qt.FocusPolicy.NoFocus)
    dock.setFloating(True)
    self.assertTrue(self.waitUntil(lambda: dock.isFloating(), 2000))
    self.assertEqual(readings.text(), 'one\ntwo')
