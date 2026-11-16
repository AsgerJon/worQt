"""
TestLoopWorld covers the loop's world ('LoopWorld'): it holds its
island (two blocks) and its two tracks, the line and the siding (held
still; drawn by their dress, not their pieces), a buffer stop past the
line's two ends and the siding's, its minecart in the headshunt and a
train on the siding (a powered cart, a cart coupled behind it by a
drawbar) until something is spawned; the avatar enters on the island
before the points; the track is solid, on the far platform and on the
loop's top's outside alike; the points' lever sets the points, the
rail world rolling on both tracks through them; another gravity than
the earth's is refused (its rail world knows only that); the trains
import nothing of the old walk window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from worQt.phys._body import Body, State
from worQt.phys._shape import Sphere
from worQt.phys.rail._stage import DROP, ISLAND_UNDER
from worQt.phys.rail._trackshape import BED_DEEP, BED_TOP

from worQt.gaming.sandbox import EARTH_GRAVITY, MOON_GRAVITY, Universe
from worQt.gaming.sandbox._avatar import SOLES
from worQt.gaming.trains import LoopWorld
from worQt.gaming.trains._layout import loopSpanOf
from worQt.gaming.trains._loopworld import WALKER_AT

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
    """The loop's world starts with its island, its tracks' pieces and
    its buffer stops, all held still, its minecart and its train (the
    powered cart, the cart coupled behind it, the drawbar between); the
    island, the buffers, the carts and the drawbar drawn, the tracks
    drawn by their dress as rails, sleepers and a bed."""
    world = LoopWorld(Universe(EARTH_GRAVITY))
    count = len(world.assembly.bodies)
    moving = {index for vehicle in world.vehicles
              for index in vehicle.bodies}
    self.assertGreater(count, 100)
    self.assertEqual([(v.line, v.powered) for v in world.vehicles],
                     [(0, False), (1, True), (1, False)])
    self.assertEqual(world.still, frozenset(range(count)) - moving)
    lone, powered, coupled = world.vehicles
    wanted = {0: 'grass', 1: 'dirt', 2: 'grass', 3: 'dirt'}
    wanted.update({index: 'buffer' for index in world.buffers})
    for vehicle, look in ((lone, 'cart'), (powered, 'powered'),
                          (coupled, 'cart')):
      wanted[vehicle.frame] = look
      wanted.update({index: 'wheel' for index in vehicle.wheelsets})
    wanted[coupled.bodies[-1]] = 'coupler'
    self.assertEqual(world.drawn, wanted)
    self.assertEqual(len(world.buffers), 3)
    self.assertEqual(set(world.fixtures()),
                     {'rail', 'sleeper', 'grass', 'dirt'})
    self.assertTrue(set(world.fixtures()) <= set(world.LOOKS))
    self.assertTrue(set(world.drawn.values()) <= set(world.LOOKS))

  def test_enters(self) -> None:
    """The avatar enters standing on the island before the points."""
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
    begins, ends = loopSpanOf()
    place, frame = world.track.frameAt(0.5 * (begins + ends))
    self.assertLess(float(frame[2, 2]), -0.99)
    under = float(place[2]) - (BED_TOP - BED_DEEP)
    over = place + ASIDE * frame[:, 1]
    over[2] = under + 1.0
    index = self._dropped(world, over)
    self.ran(world, 1.0)
    self.assertAlmostEqual(world.states[index].place[2], under + RADIUS,
                           None, None, 0.05)

  def test_points(self) -> None:
    """The points' lever, used, sets the points for the siding once the
    hand has thrown it (used again, for the line); the rail world rolls
    on both tracks, through these points."""
    world, _ = self.loopWorld()
    self.ran(world, 0.1)
    self.assertIn(world.pointsLever, world.peeps)
    self.assertEqual(world.solver.tracks, world.tracks)
    self.assertEqual(world.solver.turnouts, (world.points,))
    self.assertFalse(world.points.thrown)
    self.assertEqual(world.pointsLever.prompt(),
                     'Set the points for the siding')
    world.pointsLever.used()
    self.ran(world, 0.4)
    self.assertTrue(world.points.thrown)
    self.assertEqual(world.pointsLever.prompt(),
                     'Set the points for the line')
    world.pointsLever.used()
    self.ran(world, 0.4)
    self.assertFalse(world.points.thrown)

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
