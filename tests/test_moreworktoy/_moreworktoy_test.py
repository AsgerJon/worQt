"""
MoreWorktoyTest subclasses 'BaseTest' from the 'worktoy.work_test'
package and is the base class for tests of the 'moreworktoy' package.
Its members are plain Python, so no running 'QApplication' is needed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MoreWorktoyTest(BaseTest):
  """
  MoreWorktoyTest subclasses 'BaseTest' and is the base class for tests
  of the 'moreworktoy' package.
  """
