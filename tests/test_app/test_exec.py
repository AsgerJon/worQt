"""
A test that relies on the live event loop 'runTest' runs it inside. It
schedules a deferred callback with 'QTimer.singleShot' and confirms the
running loop dispatches it. The test never calls 'exec' itself: 'runTest'
already owns the loop, so a nested 'exec' would be wrong.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QTimer

from worQt.qtest import AppTest


class TestExec(AppTest):
  """Confirms test methods run with a live, pumping event loop."""

  def test_deferred(self, ) -> None:
    """A zero-delay timer fires once the running loop is pumped."""
    fired = {}

    def onFire() -> None:
      fired['ok'] = True

    QTimer.singleShot(0, onFire)
    for _ in range(100):
      if fired.get('ok', False):
        break
      self.app.processEvents()
    self.assertTrue(fired.get('ok', False))
