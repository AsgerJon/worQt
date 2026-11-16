"""
TestHotbar covers the avatar's hotbar ('Hotbar'): nine slots, empty but
for what is put in them; the slot in hand selected by number or
scrolled round the ends; a tool put away (letting go) when another slot
is taken; slots past the ninth refused.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox import SLOTS, GravityGun, Hotbar

from . import SandboxTest


class TestHotbar(SandboxTest):
  """Tests for the hotbar."""

  def test_slots(self) -> None:
    """Nine slots, empty; the gravity gun put in the first is in hand."""
    hotbar = Hotbar()
    self.assertEqual(SLOTS, 9)
    self.assertEqual(hotbar.names(), [''] * 9)
    self.assertIsNone(hotbar.tool())
    gun = GravityGun()
    hotbar.put(0, gun)
    self.assertIs(hotbar.tool(), gun)
    self.assertEqual(hotbar.names()[0], 'Gravity gun')

  def test_select(self) -> None:
    """Another slot taken puts the tool in hand away; scrolling wraps
    round both ends."""
    hotbar, gun = Hotbar(), GravityGun()
    hotbar.put(0, gun)
    gun.held = 5
    hotbar.select(3)
    self.assertIsNone(gun.held)
    self.assertIsNone(hotbar.tool())
    hotbar.scrolled(6)
    self.assertEqual(hotbar.selected, 0)
    hotbar.scrolled(-1)
    self.assertEqual(hotbar.selected, 8)

  def test_refused(self) -> None:
    """Slots past the ends are refused."""
    hotbar = Hotbar()
    with self.assertRaises(IndexError):
      hotbar.select(9)
    with self.assertRaises(IndexError):
      hotbar.put(-1, None)
