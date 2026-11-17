"""
TestInventory covers what Asger carries (user, 2026-11-17: "Give Asger a
hotbar and an inventory like in minecraft. then one tool is the gravgun,
then give Asger also a telescope, if possible. Finally, put some
commandobars in Asgers inventory"): the gun and the telescope on the
hotbar, the bars in the inventory over it; keys and the wheel choose
what is held; Minecraft's clicks pick stacks up and lay them down, onto
the same kind as far as it stacks, half or one with the right button;
shut, the stack carried goes back; a bar eaten is one fewer and feeds
him; each item has its icon in his hand.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._handitems import heldParts
from worQt.gaming.space._inventory import HOTBAR, ITEMS, SLOTS, Inventory
from worQt.gaming.space._itempictures import ICONS, PIXELS
from worQt.gaming.space._vitals import BAR, FOOD, MUNCHING, Vitals

from . import SpaceTest


class TestInventory(SpaceTest):
  """Tests for Asger's inventory."""

  def test_carried(self) -> None:
    """He begins with the gun held, the telescope beside it and a stack
    of commando bars in the inventory over the hotbar."""
    inventory = Inventory()
    self.assertEqual(len(inventory.slots), SLOTS)
    self.assertEqual(inventory.held, 'gravgun')
    self.assertEqual(inventory.slots[1], ['telescope', 1])
    bars = [s for s in inventory.slots[HOTBAR:] if s is not None]
    self.assertEqual(bars[0][0], 'commando')
    self.assertGreater(bars[0][1], 1)

  def test_chosen(self) -> None:
    """Keys choose a hotbar slot; the wheel goes round it; past the
    hotbar is no slot to choose."""
    inventory = Inventory()
    inventory.chosen(1)
    self.assertEqual(inventory.held, 'telescope')
    inventory.scrolled(-2)
    self.assertEqual(inventory.selected, HOTBAR - 1)
    self.assertIsNone(inventory.held)
    with self.assertRaises(IndexError):
      inventory.chosen(HOTBAR)

  def test_clicked(self) -> None:
    """A click picks the bars up, another lays them on the hotbar; a
    right click takes half, another lays one; laid on their kind they
    stack, no more than a stack; laid on another kind they swap; shut,
    what is carried goes back."""
    inventory = Inventory()
    count = inventory.slots[HOTBAR][1]
    inventory.clicked(HOTBAR, False)
    self.assertEqual(inventory.carried, ['commando', count])
    self.assertIsNone(inventory.slots[HOTBAR])
    inventory.clicked(2, False)
    self.assertEqual(inventory.slots[2], ['commando', count])
    self.assertIsNone(inventory.carried)
    inventory.clicked(2, True)
    self.assertEqual(inventory.carried[1], (count + 1) // 2)
    self.assertEqual(inventory.slots[2][1], count - (count + 1) // 2)
    inventory.clicked(3, True)
    self.assertEqual(inventory.slots[3], ['commando', 1])
    inventory.clicked(2, False)
    most = ITEMS['commando'][1]
    self.assertEqual(inventory.slots[2][1], min(most, count - 1))
    inventory.closed()
    self.assertIsNone(inventory.carried)
    total = sum(s[1] for s in inventory.slots if s is not None
                and s[0] == 'commando')
    self.assertEqual(total, count)
    inventory.clicked(0, False)
    inventory.clicked(1, False)
    self.assertEqual(inventory.slots[1], ['gravgun', 1])
    self.assertEqual(inventory.carried, ['telescope', 1])
    inventory.closed()
    self.assertEqual(inventory.slots[0], ['telescope', 1])

  def test_eaten(self) -> None:
    """A bar held and eaten is one fewer, and feeds him its points once
    eaten; full, he eats none."""
    inventory, vitals = Inventory(), Vitals()
    inventory.clicked(HOTBAR, False)
    inventory.clicked(4, False)
    inventory.chosen(4)
    count = inventory.slots[4][1]
    vitals.food = FOOD - 2.0 * BAR
    self.assertEqual(vitals.munched(), '')
    self.assertTrue(inventory.usedUp())
    self.assertEqual(inventory.slots[4][1], count - 1)
    vitals.lived(MUNCHING + 0.01, 1.0, False)
    self.assertGreater(vitals.food, FOOD - BAR - 0.5)
    vitals.food = FOOD
    self.assertNotEqual(vitals.munched(), '')

  def test_pictures(self) -> None:
    """Every item has its icon ('PIXELS' square) and its meshes in his
    hand."""
    for kind in ITEMS:
      self.assertEqual(len(ICONS[kind]), PIXELS)
      self.assertTrue(heldParts(kind))
