"""
The 'worQt.tabs' package provides the 'TabBar', a row of tabs to choose
between, painted with worQt's own widgets and paint operations.

- PaintTabBar: the paint operation drawing the tabs.
- TabBar: the widget.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._paint_tab_bar import PaintTabBar
from ._tab_bar import TabBar

__all__ = (
  'PaintTabBar',
  'TabBar',
)
