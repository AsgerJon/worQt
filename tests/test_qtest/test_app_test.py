"""
TestAppTestNoApp covers the one 'AppTest' path reachable without a running
'QApplication': the 'app' accessor raising when no application exists. It
runs in-process under a plain 'BaseTest', where no 'QApplication' has been
created.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException

from worQt.qtest import AppTest

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Probe(AppTest):
  """A trivial 'AppTest' used only to reach the 'app' accessor."""

  def test_noop(self) -> None:
    pass


class TestAppTestNoApp(QTestTest):
  """Tests the 'AppTest.app' accessor with no running application."""

  def test_app_without_application_raises(self) -> None:
    """Reading 'app' with no running 'QApplication' raises."""
    with self.assertRaises(TypeException):
      _Probe('test_noop')._getApp()
