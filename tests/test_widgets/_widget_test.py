"""
WidgetTest subclasses 'AppTest' from the 'worQt.qtest' package and is the
base class for tests of the 'worQt.widgets' package. Widgets are
'QObject's, so these tests need a running 'QApplication'; 'AppTest'
provides one and runs each class in its own child process under a deadline,
so a hang or segfault becomes a reported status rather than a frozen
terminal.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class WidgetTest(AppTest):
  """
  WidgetTest subclasses 'AppTest' and is the base class for tests of the
  'worQt.widgets' package.
  """
