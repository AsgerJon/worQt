"""
Base classes for tests of the 'worQt.windows' package. The declarative
menu *registration* is class-level (descriptors register their types at
import), so it tests under a plain 'BaseTest'; building the menus, bar and
actions constructs 'QObject's, so that tests under 'WidgetTest' with a
running 'QApplication' and the live-window / gesture surface.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class WindowsTest(BaseTest):
  """Base for the class-level (registration) windows tests."""


class WindowsAppTest(WidgetTest):
  """Base for the 'QObject'-backed windows tests (menus, bar, actions).

  Subclasses 'WidgetTest' so the whole windows suite shares the same
  live-window pattern the widget tests use: 'showLive' renders a window as
  an actually exposed, painted top-level window, and the mouse/keyboard
  gestures deliver events through the application - identical in the
  authentic and headless fallback render modes.
  """
