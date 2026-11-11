"""
The 'tests.test_gaming.test_billiards' package contains tests for the
'worQt.gaming.billiards' package, three-cushion carambole: the table,
balls and their motion in plain 'BaseTest' classes, the 3D view in
'WidgetTest' classes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._billiards_test import BilliardsTest, BilliardsWidgetTest
from ._billiards_test import BREAK_AIM, aroundContact, ballAt, breakAim
from ._billiards_test import firstBreak, rolledOn

__all__ = (
  'BilliardsTest',
  'BilliardsWidgetTest',
  'BREAK_AIM',
  'breakAim',
  'aroundContact',
  'ballAt',
  'firstBreak',
  'rolledOn',
)
