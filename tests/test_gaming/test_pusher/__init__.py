"""
The 'tests.test_gaming.test_pusher' package contains tests for the
'worQt.gaming.pusher' package, the coin pusher: the coins and the
machine in plain 'BaseTest' classes, the app's widgets in 'WidgetTest'
classes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._pusher_test import PusherTest, PusherWidgetTest
from ._pusher_test import STILL, NOUGHT, FLOOR, BIN
from ._pusher_test import worldOf, tiltOf, onEdge, rained, overlapOf
from ._pusher_test import overlapWith

__all__ = (
  'PusherTest',
  'PusherWidgetTest',
  'STILL',
  'NOUGHT',
  'FLOOR',
  'BIN',
  'worldOf',
  'tiltOf',
  'onEdge',
  'rained',
  'overlapOf',
  'overlapWith',
)
