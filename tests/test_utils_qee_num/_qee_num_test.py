"""
QeeNumTest subclasses 'BaseTest' from 'worktoy.work_test' and provides the
base for testing of components from the 'worQt.utils.qee_num' module.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest
from tests import AppLessTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type


class QeeNumTest(AppLessTest):
  """
  QeeNumTest subclasses 'BaseTest' from 'worktoy.work_test' and provides the
  base for testing of components from the 'worQt.utils.qee_num' module.
  """
  pass
