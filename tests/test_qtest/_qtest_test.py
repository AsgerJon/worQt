"""
QTestTest is the base for tests of the 'worQt.qtest' harness. The harness
discovery, namespace, metaclass and suite are plain 'BaseObject' machinery
that needs no running 'QApplication', so these tests run in-process under a
plain 'BaseTest'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class QTestTest(BaseTest):
  """Base for the in-process 'worQt.qtest' harness tests."""
