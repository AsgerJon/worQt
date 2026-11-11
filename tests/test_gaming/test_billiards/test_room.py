"""
TestRoom covers 'Room', the billiard room the game opens in: two tables,
three-cushion's and keglebillard's, side by side inside its walls; a
place inside a wall or a table is moved the least way out, clear of it;
the door is near no table; a player leaving a table stands near it,
facing it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import Room

from . import BilliardsTest

ROOM = Room()


class TestRoom(BilliardsTest):
  """Tests for 'Room'."""

  def test_tables(self) -> None:
    """Both tables stand in the room, apart, inside its walls."""
    carom, kegler = ROOM.tableAt('carom'), ROOM.tableAt('kegler')
    self.assertLess(carom[0], kegler[0])
    self.assertGreater(kegler[0] - carom[0],
                       2.0 * (ROOM.tableHalfWidth + ROOM.keep))
    for x, _ in (carom, kegler):
      self.assertLess(abs(x) + ROOM.tableHalfWidth, ROOM.halfWidth)
    self.assertEqual(ROOM.layout()['tables'], {'carom': carom[0],
                                               'kegler': kegler[0]})

  def test_kept(self) -> None:
    """A place past a wall comes back inside, 'keep' from it; one on a
    table is pushed out the nearest way, 'keep' clear of its rails; one
    clear of all stays."""
    x, z = ROOM.kept(0.0, -1e6)
    self.assertEqual(z, -ROOM.halfLength + ROOM.keep)
    tx, tz = ROOM.tableAt('carom')
    x, z = ROOM.kept(tx + 100.0, tz + 1500.0)
    self.assertAlmostEqual(ROOM.gapTo('carom', x, z), ROOM.keep, 9)
    self.assertAlmostEqual(x, tx + 100.0, 9)
    self.assertEqual(ROOM.kept(0.0, 0.0), (0.0, 0.0))

  def test_near(self) -> None:
    """At the door no table is near; a player leaving a table stands
    near it, facing it."""
    self.assertEqual(ROOM.nearOf(*ROOM.door), '')
    for kind in ROOM.kinds():
      x, z, yaw, _ = ROOM.beside(kind)
      self.assertEqual(ROOM.nearOf(x, z), kind)
      self.assertEqual(ROOM.kept(x, z), (x, z))
      turn = math.radians(yaw)
      fx, fz = -math.sin(turn), -math.cos(turn)
      tx, tz = ROOM.tableAt(kind)
      self.assertGreater(fx * (tx - x) + fz * (tz - z), 0.0)
