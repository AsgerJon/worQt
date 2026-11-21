"""
TestEKey covers what E does (user, 2026-11-19: "the game is broken again
because the EVERYWHERE IS E TO LADDER!! so no way to sit!"): the
window's own 'SpaceWindow._ePressed' and '_eReleased' on stand-ins.
Where E has something to work (his chair, an elevator's seat, a door, an
input) it works it at once, by the handles or on them too; only where
it has nothing does it start the handles' hold, and a tap there opens
the inventory; away from the handles with nothing, the inventory at
once; the manual and the inventory open, E shuts them first.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import time
from types import SimpleNamespace

from worQt.gaming.space._spacewindow import SpaceWindow

from . import SpaceTest


class TestEKey(SpaceTest):
  """Tests for what E does."""

  def _window(self, usable: bool, near: bool, held: bool) -> tuple:
    """Returns a stand-in for the window as E uses it ('usable': E has
    something to work; 'near': by the handles; 'held': on them) and the
    list of what it was told."""
    told = []
    window = SimpleNamespace(
      _manualOpen=False, _inventoryOpen=False, inside=True, _eSince=None,
      ladder=SimpleNamespace(held=held),
      _usable=lambda: usable,
      _used=lambda back: told.append('used'),
      _ladderNear=lambda: (0, 0.0) if near else None,
      _inventoryOpened=lambda: told.append('inventory'),
      _inventoryShut=lambda: told.append('shut'),
      viewport=SimpleNamespace(holdShown=lambda *_: None))
    return window, told

  def test_used_first(self) -> None:
    """Something to work: worked at once, by the handles, on them or
    neither; no hold started."""
    for near, held in ((False, False), (True, False), (True, True)):
      window, told = self._window(True, near, held)
      SpaceWindow._ePressed(window)
      self.assertEqual(told, ['used'], (near, held))
      self.assertIsNone(window._eSince)

  def test_handles(self) -> None:
    """Nothing to work by the handles or on them: the hold starts, and a
    tap (let go at once) opens the inventory."""
    for near, held in ((True, False), (False, True)):
      window, told = self._window(False, near, held)
      SpaceWindow._ePressed(window)
      self.assertEqual(told, [])
      self.assertIsNotNone(window._eSince)
      SpaceWindow._eReleased(window)
      self.assertEqual(told, ['inventory'])
      self.assertIsNone(window._eSince)

  def test_held_long(self) -> None:
    """Let go after the ring filled (the hold has done its work): no
    inventory."""
    window, told = self._window(False, True, False)
    window._eSince = time.perf_counter() - 2.0
    SpaceWindow._eReleased(window)
    self.assertEqual(told, [])

  def test_nothing(self) -> None:
    """Nothing to work, no handles: the inventory at once; open, E shuts
    it; the manual open, E puts it back."""
    window, told = self._window(False, False, False)
    SpaceWindow._ePressed(window)
    self.assertEqual(told, ['inventory'])
    window, told = self._window(True, True, False)
    window._inventoryOpen = True
    SpaceWindow._ePressed(window)
    self.assertEqual(told, ['shut'])
    window, told = self._window(True, True, False)
    window._manualOpen = True
    SpaceWindow._ePressed(window)
    self.assertEqual(told, [])
    self.assertFalse(window._manualOpen)
