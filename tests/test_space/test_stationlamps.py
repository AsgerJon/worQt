"""
TestStationLamps covers the lamps up the rocket's head and in Terra
Prime's cages (user, 2026-11-19: "we must have lamps in the center of
the Terra Prime and in each of the four elevators"; "I can't see it
because of the darkness"; then the three levels): a lamp ring under each
of the head's levels' ceilings, all round, clear of the hatch and the
pole, its light in the level's room; each cage's lamp bar and its light
inside its cage, wherever the cage stands on its run; each a piece of
the cabin's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._dashboard import pieceRows, pieces
from worQt.gaming.space._elevator import DECK_STOP, HUB_STOP, Elevator
from worQt.gaming.space._levels import HATCH, LEVELS
from worQt.gaming.space._stationinterior import LEVEL_INSIDE, roomOf
from worQt.gaming.space._stationinterior import shaftWays
from worQt.gaming.space._stationlamps import cageLampOf, ringAt
from worQt.gaming.space._stationlamps import ringLightAt

from . import SpaceTest

#  The docked rocket's axes in the station's (as the port's own tests
#  have them).
RELATIVE = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))


class TestStationLamps(SpaceTest):
  """Tests for Terra Prime's lamps."""

  def test_rings(self) -> None:
    """Each of the head's levels' lamp rings is under its ceiling, its
    lamps all round, clear of the hatch and in from the wall; its light
    in the level's room."""
    ways = shaftWays(RELATIVE)
    rows = numpy.asarray(pieceRows(('level lamp', 1), {})[0])[:, :3]
    out = numpy.hypot(rows[:, 0], rows[:, 1])
    self.assertTrue((out > HATCH + 0.5).all())
    self.assertTrue((out < LEVEL_INSIDE - 0.5).all())
    angles = numpy.arctan2(rows[:, 1], rows[:, 0])
    self.assertGreater(float(angles.max() - angles.min()), 6.0)
    for level in (1, 2):
      low, high = LEVELS[level]
      top = ringAt(level)[2] + float(rows[:, 2].max())
      self.assertLess(top, high)
      self.assertGreater(top, high - 0.2)
      self.assertEqual(roomOf(ringLightAt(level), ways, ()),
                       'level %d' % level)

  def test_cages(self) -> None:
    """Each cage's lamp bar and light are inside its cage at its hub
    stop, half way and at the deck."""
    for way in shaftWays(RELATIVE):
      elevator = Elevator()
      for floor in (HUB_STOP, 0.5 * (HUB_STOP + DECK_STOP), DECK_STOP):
        elevator.floor = floor
        bar, light = cageLampOf(floor, way)
        self.assertTrue(elevator.holds(way, bar), (way, floor, bar))
        self.assertTrue(elevator.holds(way, light), (way, floor, light))

  def test_pieces(self) -> None:
    """The lamps are the cabin's pieces: the head's two rings and one bar
    a cage."""
    every = pieces(Cockpit().controls)
    self.assertIn(('level lamp', 1), every)
    self.assertIn(('level lamp', 2), every)
    self.assertEqual(sum(1 for kind, _ in every if kind == 'car lamp'),
                     4)
