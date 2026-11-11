"""
TestMachine covers 'Machine', the coin pusher running: empty at first,
the chutes shut; the house pouring its coins in, two heaps every which
way on both levels spreading from wall to wall, then a countdown, the
purse as it was; a drop takes a
coin from the purse down the chute, and none while that chute is busy
or the purse empty; coins slide down the ramps and land lying at the
back of the shelf, behind the coins there; played a while, coins
dropped in turn come out into the tray and back to the purse, nothing
lost, nothing ever below the tray, the total never changing.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools

from worQt.gaming.pusher import Cabinet, Machine, MACHINE, PURSE, TRAY

from . import PusherTest, tiltOf


@functools.cache
def playedMachine() -> tuple[Machine, list]:
  """A machine played 75 s, a coin dropped every half second, left and
  right in turn, and what it held each second: (purse, on the machine,
  in the tray, total, lowest coin)."""
  machine = Machine()
  machine.fill()
  side, books = -1, []
  for frame in range(75 * 60):
    if frame % 30 == 0 and machine.drop(side):
      side = -side
    machine.frame()
    if frame % 60 == 59:
      lowest = float(machine.world.places[machine.world.playing][:, 2].min())
      books.append((machine.purse, machine.onMachine, machine.inTray,
                    machine.total, lowest))
  return machine, books


class TestMachine(PusherTest):
  """Tests for 'Machine'."""

  def test_empty(self) -> None:
    """At first the machine is empty, the purse full, the chutes shut."""
    machine = Machine()
    self.assertEqual(machine.onMachine, 0)
    self.assertEqual(machine.purse, 60)
    self.assertEqual(machine.total, 60)
    self.assertFalse(machine.started)
    self.assertFalse(machine.filling)
    self.assertFalse(machine.drop(-1))
    self.assertEqual(machine.dropped, 0)

  def test_poured(self) -> None:
    """The house pours its coins in, two heaps, filling meanwhile, the
    coins heard clinking; the machine runs while four seconds are counted
    down; then the game is on: coins on both levels and along both side
    walls, lying every which way; the purse as it was, nothing won or
    dropped, the house's spilled coins out of the game."""
    machine = Machine()
    machine.pour()
    self.assertTrue(machine.filling)
    self.assertFalse(machine.drop(1))
    counts, heard = [], 0.0
    while machine.filling:
      machine.frame()
      heard += machine.hits[0]
      if machine.countdown > 0.0:
        counts.append(machine.countdown)
    self.assertGreater(heard, 100)
    self.assertGreater(max(counts), 3.9)
    self.assertLess(min(counts), 0.1)
    self.assertEqual(counts, sorted(counts, reverse=True))
    self.assertTrue(machine.started)
    self.assertFalse(machine.filling)
    cabinet, world = machine.cabinet, machine.world
    self.assertEqual(machine.purse, 60)
    self.assertEqual((machine.won, machine.dropped), (0, 0))
    self.assertGreater(machine.onMachine, 140)
    self.assertEqual(machine.total, machine.purse + machine.onMachine)
    places = world.places[machine.where == MACHINE]
    self.assertTrue((places[:, 2] > cabinet.shelf).any())
    self.assertTrue((places[:, 2] < cabinet.shelf).any())
    near = cabinet.width / 2.0 - 3.0 * cabinet.coin.radius
    self.assertTrue((places[:, 0] > near).any())
    self.assertTrue((places[:, 0] < -near).any())
    rows = set(round(float(y)) for y in places[:, 1])
    self.assertGreater(len(rows), 60)
    tilts = [tiltOf(turn) for turn in world.turns[machine.where == MACHINE]]
    self.assertGreater(sum(tilt > 5.0 for tilt in tilts), 5)

  def test_drop(self) -> None:
    """A drop takes a coin from the purse onto the chute's ramp; the same
    chute takes no other until it is off the ramp, the other side does."""
    machine = Machine(Cabinet(), 3)
    machine.fill()
    before = machine.where
    self.assertTrue(machine.drop(-1))
    self.assertEqual(machine.purse, 2)
    self.assertEqual(machine.dropped, 1)
    moved = (before == PURSE) & (machine.where == MACHINE)
    self.assertEqual(int(moved.sum()), 1)
    self.assertFalse(machine.drop(-1))
    self.assertTrue(machine.drop(1))
    machine.played(2.0)
    self.assertTrue(machine.chuteClear(-1))
    self.assertTrue(machine.drop(-1))
    self.assertFalse(machine.drop(1) and machine.drop(-1))

  def test_lands_lying(self) -> None:
    """Coins sent down the chutes slide down the ramps lying and land
    lying at the back of the shelf, behind the coins there: 1.5 s on,
    none leans more than 30 degrees, each nearer the back wall than the
    pusher's face ever comes."""
    machine = Machine()
    machine.fill()
    dropped = []
    for side in (-1, 1, -1, 1, -1, 1):
      before = machine.where == PURSE
      self.assertTrue(machine.drop(side))
      new = before & (machine.where == MACHINE)
      dropped.append(int(new.nonzero()[0][0]))
      machine.played(0.7)
    machine.played(1.5)
    turns = machine.world.turns
    for index in dropped:
      self.assertLess(tiltOf(turns[index]), 30.0)
      place = machine.world.places[index]
      self.assertLess(place[1], machine.cabinet.retracted - 20.0)

  def test_empty_purse(self) -> None:
    """With the purse empty nothing drops."""
    machine = Machine(Cabinet(), 0)
    machine.fill()
    self.assertFalse(machine.drop(-1))
    self.assertFalse(machine.drop(1))
    self.assertEqual(machine.dropped, 0)

  def test_pays(self) -> None:
    """Played 75 s, coins come out into the tray and back to the purse:
    some won, the purse refilled, the tray emptied of those lying
    still."""
    machine, books = playedMachine()
    self.assertGreater(machine.dropped, 60)
    self.assertGreater(machine.won, 10)
    self.assertGreater(max(purse for purse, *_ in books[-10:]), 0)

  def test_honest(self) -> None:
    """Every second the purse, the machine and the tray hold every coin,
    the total never changing; no coin is ever below the tray's floor;
    every coin won came out over the front edge."""
    machine, books = playedMachine()
    cabinet = machine.cabinet
    for purse, onMachine, inTray, total, lowest in books:
      self.assertEqual(purse + onMachine + inTray, total)
      self.assertEqual(total, books[0][3])
      self.assertGreater(lowest, -cabinet.drop - 1.0)
    world = machine.world
    tray = machine.where == TRAY
    self.assertTrue((world.places[tray][:, 1] > cabinet.front).all())
