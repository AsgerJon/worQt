"""
TestLevels covers the rocket's three levels (user, 2026-11-19: "Asger
starts at level 0 of the rocket where he has his hygge. We then add an
empty floor in the middle, and a top floor at the top. Now, the top
floor has four doors in each direction"): the hull's outline whole
(the cabin's cone as it was, the head over it, the nose's tip where
the rocket's always was); the
levels stacked, a slab between each two; the four doors on the hull's
steps round, a quarter turn apart, in the top floor's wall round its
middle; a door opens only docked, slides its leaf into the wall and
back (the ladder up the levels: 'test_ladder').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._cabin import STEP
from worQt.gaming.space._levels import CEILING, CONE, DOOR_ANGLES
from worQt.gaming.space._levels import DOOR_HALF_SPAN, DOORS_HIGH, FLOOR
from worQt.gaming.space._levels import HEAD, LEVELS, ROOF
from worQt.gaming.space._levels import SLAB, TIP, TIP_RADIUS, TOP_DOORS
from worQt.gaming.space._levels import hullRadius
from worQt.gaming.space._shaftdoor import HALF_SPAN, MIDDLE_FAR, POCKET
from worQt.gaming.space._shaftdoor import ShaftDoor
from worQt.gaming.space._vessel import CAPSULE, CENTRE, RADIUS

from . import FRAME, SpaceTest


class TestLevels(SpaceTest):
  """Tests for the rocket's three levels and its doors."""

  def test_outline(self) -> None:
    """The hull's outline is whole: the cabin's cone narrowing as it
    always did up to its ceiling, the head's radius from there to its
    roof, the nose's cone to the tip where the rocket's always was."""
    self.assertAlmostEqual(hullRadius(FLOOR), RADIUS, 9)
    self.assertAlmostEqual(hullRadius(CEILING), HEAD, 9)
    self.assertAlmostEqual(hullRadius(CEILING + 1e-9), HEAD, 6)
    self.assertAlmostEqual(hullRadius(ROOF), HEAD, 9)
    self.assertAlmostEqual(hullRadius(TIP), TIP_RADIUS, 9)
    self.assertAlmostEqual(TIP, CAPSULE[1] - CENTRE, 9)
    self.assertAlmostEqual((hullRadius(FLOOR) - hullRadius(FLOOR + 1.0)),
                           CONE, 9)
    self.assertGreater(CEILING - FLOOR, 3.0)

  def test_stacked(self) -> None:
    """Each level's floor is a slab over the one below's ceiling, the
    head's levels as high as a room; the roof a slab over the top's."""
    for (_, below), (above, high) in zip(LEVELS, LEVELS[1:]):
      self.assertAlmostEqual(above - below, SLAB, 9)
      self.assertGreater(high - above, 2.5)
    self.assertAlmostEqual(ROOF - LEVELS[2][1], SLAB, 9)
    self.assertAlmostEqual(DOORS_HIGH, 0.5 * sum(LEVELS[2]), 9)

  def test_doors(self) -> None:
    """The top floor's doors: a quarter turn apart, their edges on the
    hull's steps round, their height within the top floor's, wide and
    high enough for Asger's box."""
    from worQt.gaming.space._crewman import TALL, WIDE
    self.assertEqual(DOOR_ANGLES, (0.0, 90.0, 180.0, 270.0))
    low, high = LEVELS[2]
    for (a0, a1), (z0, z1) in TOP_DOORS:
      self.assertAlmostEqual(a0 / STEP, round(a0 / STEP), 9)
      self.assertAlmostEqual(a1 / STEP, round(a1 / STEP), 9)
      self.assertGreater(z0, low)
      self.assertLess(z1, high)
      self.assertGreater(z1 - z0, TALL)
    wide = 2.0 * (HEAD - 0.05) * math.sin(math.radians(DOOR_HALF_SPAN))
    self.assertGreater(wide, 2.0 * WIDE)

  def test_leaf(self) -> None:
    """A door opens only docked; open it slides its leaf round into the
    wall clear of the opening, shut it slides it back; its leaf's box is
    in the wall at the door."""
    door = ShaftDoor(1)
    self.assertNotEqual(door.opened(False), '')
    self.assertTrue(door.shut)
    middle, half = door.boxOf()[:2]
    self.assertAlmostEqual(math.hypot(middle[0], middle[1]), MIDDLE_FAR, 9)
    self.assertAlmostEqual(math.atan2(middle[1], middle[0]),
                           math.radians(DOOR_ANGLES[1]), 9)
    self.assertAlmostEqual(middle[2], DOORS_HIGH, 9)
    self.assertEqual(door.opened(True), '')
    for _ in range(int(round(4.0 / FRAME))):
      door.moved(FRAME, 0.0, 0.0)
    self.assertAlmostEqual(door.share, 1.0, 6)
    middle = door.boxOf()[0]
    angle = math.atan2(middle[1], middle[0]) - math.radians(DOOR_ANGLES[1])
    self.assertAlmostEqual(angle, POCKET, 6)
    self.assertGreater(angle - HALF_SPAN, HALF_SPAN)
    self.assertEqual(door.closed(), '')
    for _ in range(int(round(4.0 / FRAME))):
      door.moved(FRAME, 0.0, 0.0)
    self.assertTrue(door.shut)
