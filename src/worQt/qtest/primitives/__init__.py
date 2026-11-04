"""
The 'worQt.qtest.primitives' subpackage provides the reusable building
blocks for event-based testing, each a dedicated class:

- SignalSpy: records every emission of a signal and its arguments.
- SignalWaiter: blocks the loop until a signal fires or a timeout elapses.
- ConditionWaiter: blocks the loop until a predicate holds or times out.
- LiveWindow: shows a widget as an actually rendered window and waits for
  it to be exposed and painted.

The primitives are mode-agnostic: they hold their Qt internals ('QEventLoop',
'QTimer') and build them at runtime, so they work the same in the authentic
and the headless fallback modes. 'WidgetTest' composes them into the mouse
and keyboard gesture surface.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._signal_spy import SignalSpy
from ._signal_waiter import SignalWaiter
from ._condition_waiter import ConditionWaiter
from ._live_window import LiveWindow

__all__ = (
  'SignalSpy',
  'SignalWaiter',
  'ConditionWaiter',
  'LiveWindow',
)
