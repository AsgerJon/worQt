"""
TestAutoWarp covers AUTO WARP (user, 2026-11-19: "give the autopilot an
'auto warp' thing. yes i know i said i didn't want that, but we are
ready for it now"): the window's own 'SpaceWindow._autoWarpToggled' and
'_autoWarpKept' on stand-ins, its time a real 'Timekeeper'. Off, time is
left alone; on, whenever WARP TO ACTION may warp (the autopilot waits
for a burn, warp allowed) it warps as WARP TO ACTION does, easing off
before the burn, said once as it starts; while warp may not (Asger not
fed full, say), it waits; toggling says so, and why it cannot warp yet.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from types import SimpleNamespace

from worQt.gaming.space._spacewindow import SpaceWindow
from worQt.gaming.space._timekeeper import WARPS, Timekeeper

from . import SpaceTest


class TestAutoWarp(SpaceTest):
  """Tests for the autopilot's AUTO WARP."""

  def _window(self, on: bool, why: str, burn: float) -> tuple:
    """Returns a stand-in for the window as AUTO WARP uses it ('on': it
    is on; 'why': why WARP TO ACTION may not warp, '' it may; the next
    burn 'burn' s off) and the notes it said."""
    said = []
    keeper = Timekeeper(None)
    keeper.stopAt(burn)
    window = SimpleNamespace(_autoWarp=on, keeper=keeper,
                             _actionWhy=lambda: why, _noteOf=said.append)
    return window, said

  def test_off(self) -> None:
    """Off, time runs as it is."""
    window, said = self._window(False, '', 3600.0)
    SpaceWindow._autoWarpKept(window)
    self.assertEqual(window.keeper.factor, 1)
    self.assertEqual(said, [])

  def test_warps(self) -> None:
    """On, the autopilot waiting an hour for its burn: warped as fast as
    the stop lets it, said once."""
    window, said = self._window(True, '', 3600.0)
    SpaceWindow._autoWarpKept(window)
    self.assertGreater(window.keeper.factor, 1)
    self.assertLessEqual(window.keeper.factor, WARPS[-1])
    self.assertEqual(len(said), 1)
    self.assertTrue(said[0].startswith('Auto warp: the burn in'))
    SpaceWindow._autoWarpKept(window)
    self.assertEqual(len(said), 1)

  def test_waits(self) -> None:
    """On, while warp may not go (Asger not fed full): no warp."""
    window, said = self._window(True, 'Asger must be fed full first',
                                3600.0)
    SpaceWindow._autoWarpKept(window)
    self.assertEqual(window.keeper.factor, 1)
    self.assertEqual(said, [])

  def test_toggled(self) -> None:
    """Toggled on it says so, and why it may not warp yet; off, so."""
    window, said = self._window(False, 'Asger must sit in his chair',
                                3600.0)
    SpaceWindow._autoWarpToggled(window)
    self.assertTrue(window._autoWarp)
    self.assertIn('Auto warp on', said[-1])
    self.assertIn('Asger must sit in his chair', said[-1])
    SpaceWindow._autoWarpToggled(window)
    self.assertFalse(window._autoWarp)
    self.assertEqual(said[-1], 'Auto warp off')
