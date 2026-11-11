"""
The 'tests.test_engineering.test_quests' package contains tests for the
'worQt.engineering.quests' package, the game of circuit quests: the
goals, the quests and the progress, which need no Qt, in plain
'BaseTest' classes; the app's window in 'WidgetTest' classes, the
'run_*.py' / 'Run*' modules.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._quests_test import play, switched, QuestsTest, QuestsWidgetTest

__all__ = (
  'play',
  'switched',
  'QuestsTest',
  'QuestsWidgetTest',
)
