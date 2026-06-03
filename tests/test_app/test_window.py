"""
A generic windowed test: opens a top-level widget against a live
'QApplication', keeps it on screen briefly so it actually paints, and
asserts on its realised state.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

from worQt.qtest import AppTest


class TestWindow(AppTest):
  """Opens a top-level window, shows it visibly, and asserts on it."""

  def test_window(self, ) -> None:
    """A shown widget stays visible while the loop pumps, then closes."""
    widget = QWidget()
    widget.setWindowTitle('worQt test window')
    widget.resize(320, 240)
    widget.show()
    widget.raise_()
    widget.activateWindow()
    QTest.qWait(1500)  # dwell so the window actually paints on screen
    self.assertTrue(widget.isVisible())
    self.assertEqual(widget.windowTitle(), 'worQt test window')
    widget.close()
