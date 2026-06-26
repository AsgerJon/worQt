"""
UtilsTest subclasses 'BaseTest' from the 'worktoy.work_test' package and
is the base class for tests of the 'worQt.utils' package. The geometry
value types and the alignment enums it covers wrap Qt value classes
('QPoint', 'QSize', 'QRect', 'QColor') rather than 'QObject', so they need
no running 'QApplication' and run in-process.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class UtilsTest(BaseTest):
  """
  UtilsTest subclasses 'BaseTest' from the 'worktoy.work_test' package and
  is the base class for tests of the 'worQt.utils' package.
  """


class UtilsAppTest(AppTest):
  """
  UtilsAppTest is the base for 'worQt.utils' tests that need a running
  'QApplication' - notably 'WFont', which queries 'QFontMetrics'.
  """
