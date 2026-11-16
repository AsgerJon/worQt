"""
TestLoopWorld covers the loop's world ('LoopWorld'): it holds its
island and its track (held still; the track drawn by its dress, not
its pieces), a buffer stop past either end and its minecart until
something is spawned; the avatar
enters on the island beside the start platform; the track is solid, on
the far platform and on the loop's top's outside alike; another
gravity than the earth's is refused (its rail world knows only that);
the trains import nothing of the old walk window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from worQt.phys._body import Body, State
from worQt.phys._shape import Sphere
from worQt.phys.rail import loopSpan
from worQt.phys.rail._stage import DROP, ISLAND_UNDER, WALKER_AT
from worQt.phys.rail._trackshape import BED_DEEP, BED_TOP

from worQt.gaming.sandbox import EARTH_GRAVITY, MOON_GRAVITY, Universe
from worQt.gaming.sandbox._avatar import SOLES
from worQt.gaming.trains import LoopWorld

from . import TrainsTest

#  The island's top, m; the ball dropped, its radius, m; how far to the
#  left of the track's middle it drops (on the bed, clear of the
#  sleepers), m.
TOP = DROP - ISLAND_UNDER
RADIUS = 0.15
ASIDE = 1.7


class TestLoopWorld(TrainsTest):
  """Tests for the loop's world (seconds)."""

  def test_empty(self) -> None:
    """The loop's world starts with its island and its track's pieces,
    all held still, and its minecart; the island and the cart drawn,
    the track drawn by its dress as rails, sleepers and a bed."""
    world = LoopWorld(Universe(EARTH_GRAVITY))
    count = len(world.assembly.bodies)
    cart = world.vehicles[0].bodies
    self.assertGreater(count, 200)
    self.assertEqual(len(world.vehicles), 1)
    self.assertEqual(world.still, frozenset(range(count)) - set(cart))
    start, end = world.buffers
    self.assertEqual(world.drawn, {0: 'grass', 1: 'dirt', start: 'buffer',
                                   end: 'buffer', cart[0]: 'cart',
                                   cart[1]: 'wheel', cart[2]: 'wheel'})
    self.assertEqual(set(world.fixtures()),
                     {'rail', 'sleeper', 'grass', 'dirt'})
    self.assertTrue(set(world.fixtures()) <= set(world.LOOKS))

  def test_enters(self) -> None:
    """The avatar enters standing on the island beside the start
    platform."""
    world, avatar = self.loopWorld()
    self.ran(world, 0.5)
    place = world.states[avatar.index].place
    for got, wanted in zip(place, (WALKER_AT[0], WALKER_AT[1],
                                   TOP + 0.3)):
      self.assertAlmostEqual(got, wanted, 2)

  def test_platform(self) -> None:
    """A ball dropped a metre onto the far platform (level, nothing over
    it) rests on the track's bed."""
    world, _ = self.loopWorld()
    place, frame = world.track.frameAt(world.track.length - 6.0)
    over = place + ASIDE * frame[:, 1] + 1.0 * frame[:, 2]
    index = self._dropped(world, over)
    self.ran(world, 2.0)
    self.assertAlmostEqual(world.states[index].place[2],
                           float(place[2]) + BED_TOP + RADIUS, 2)

  def test_loop_top(self) -> None:
    """A ball dropped a metre onto the loop's top lands on its outside
    (the bed's underside, turned up there) and stays on it, rolling a
    little down its curve."""
    world, _ = self.loopWorld()
    begins, ends = loopSpan()
    place, frame = world.track.frameAt(0.5 * (begins + ends))
    self.assertLess(float(frame[2, 2]), -0.99)
    under = float(place[2]) - (BED_TOP - BED_DEEP)
    over = place + ASIDE * frame[:, 1]
    over[2] = under + 1.0
    index = self._dropped(world, over)
    self.ran(world, 1.0)
    self.assertAlmostEqual(world.states[index].place[2], under + RADIUS,
                           None, None, 0.05)

  def test_moon_refused(self) -> None:
    """The moon's universe is refused: the rail world knows only the
    earth's gravity."""
    with self.assertRaises(NotImplementedError):
      LoopWorld(Universe(MOON_GRAVITY))

  def test_clean(self) -> None:
    """The trains, window and all, import nothing of the old walk window
    or its views."""
    import worQt.gaming.trains._trainsapp  # noqa: F401
    loaded = [name for name in sys.modules if name.startswith(
      'worQt.phys.gui')]
    self.assertEqual(loaded, [])

  def _dropped(self, world: object, over: object) -> int:
    """Returns the index of a ball spawned still at 'over'."""
    ball = Body.of(Sphere(RADIUS), 700.0)
    state = State(tuple(float(x) for x in over))
    return world.spawned(ball, state, SOLES, 'dirt')
