"""
TestMixinNoApp covers the one 'MixinBase' branch the application-backed
'RunMixinBase' cannot reach: reading 'app' when no 'QApplication' is
running. 'MixinBase' is not itself a 'QObject', so it can be constructed
without an application; its 'app' getter then raises 'RuntimeError'. This
runs as a plain 'BaseTest' in the in-process runner, which has no running
application.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication
from worktoy.work_test import BaseTest

from worQt.mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestMixinNoApp(BaseTest):
  """The 'MixinBase.app' getter without a running application."""

  def test_app_without_running_application(self) -> None:
    """Reading 'app' with no 'QApplication' raises 'RuntimeError'."""
    if QApplication.instance() is not None:  # pragma: no cover
      self.skipTest('a QApplication is running in this process')
    with self.assertRaises(RuntimeError):
      _ = MixinBase().app
