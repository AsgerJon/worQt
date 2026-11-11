"""
The 'worQt.engineering.quests.gui' package plays the circuit quests,
painted with worQt's own widgets and the circuits' own:

- QuestsToolBar: the circuits' buttons, a part's greyed out until it is
  unlocked.
- LogicToolBar, LOGIC_KINDS: the buttons adding logic parts and chips,
  each greyed out until it is granted.
- BusToolBar, BUS_KINDS: the buttons adding the parts of buses and of a
  little computer, each greyed out until it is granted.
- PaintQuestPanel, QuestPanel: the quests, each done, open or shut, the
  one played, its brief and how far it is from its goal.
- QuestsWindow: the parts together, the goal watching the circuit run.
- QuestsApp: the application, run with
  'python -m worQt.engineering.quests'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._quests_tool_bar import QuestsToolBar
from ._logic_tool_bar import LogicToolBar, LOGIC_KINDS
from ._bus_tool_bar import BusToolBar, BUS_KINDS
from ._quest_panel import PaintQuestPanel, QuestPanel
from ._quests_window import QuestsWindow
from ._quests_app import QuestsApp

__all__ = (
  'QuestsToolBar',
  'LogicToolBar',
  'LOGIC_KINDS',
  'BusToolBar',
  'BUS_KINDS',
  'PaintQuestPanel',
  'QuestPanel',
  'QuestsWindow',
  'QuestsApp',
)
