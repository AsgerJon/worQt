"""
TestKnocks covers what Asger meets turning him (user, 2026-11-18: "You
Spin me Round (Like a Record)"; '_cabin_kernels.walked'): what he meets
pushes him where it meets him, so walking into a slab at his forehead
knocks his head back (a thud) and he stands up straight again; floating
weightless his head meeting a block sets him spinning, his push and
twist summed with the vessel's none (momentum and its moment kept);
standing, a block swung into his shoulder at speed knocks him down,
and he gets up again; standing on a solid, it takes his weight
('CabinWorld.struck': what moves it, an elevator's cage, is pushed by
it).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._crewman import HEFT, LOW, MIDDLE, MOMENTS, TALL
from worQt.gaming.space._launchtower import GROUND
from worQt.gaming.space._turns import cross, dot

from . import FRAME, SpaceTest

#  Where on the pad's open ground he is tried (his soles), m.
ARENA = (12.0, 12.0, GROUND)


def _box(low: tuple, high: tuple, velocity: tuple) -> tuple:
  """Returns a solid from corner 'low' to 'high' (from 'ARENA') moving
  'velocity'."""
  low = tuple(a + b for a, b in zip(ARENA, low))
  high = tuple(a + b for a, b in zip(ARENA, high))
  return (tuple(0.5 * (a + b) for a, b in zip(low, high)),
          tuple(0.5 * (b - a) for a, b in zip(low, high)),
          (1.0, 0.0, 0.0, 0.0), velocity)


def _held(crewman: object) -> tuple:
  """Returns his momentum (N s) and its moment about the vessel's middle
  with his spin's (N m s)."""
  up = crewman.up
  spin = crewman.spin
  along = dot(spin, up)
  across = tuple(s - along * u for s, u in zip(spin, up))
  own = tuple(MOMENTS[0] * a + MOMENTS[2] * along * u
              for a, u in zip(across, up))
  push = tuple(HEFT * v for v in crewman.velocity)
  return push, tuple(o + c for o, c in zip(own, cross(crewman.middle,
                                                      push)))


class TestKnocks(SpaceTest):
  """Tests for knocks turning Asger."""

  #  The cabin's kernels step on the CPU here: minutes.
  __time_out__ = 900.0

  def _arena(self, felt: tuple, boxes: tuple) -> tuple:
    """Returns his cockpit (him up on the open ground at 'ARENA', facing
    x), the world with 'boxes' there and a meter feeling 'felt'."""
    cockpit, meter = Cockpit(), self.stillMeter()
    meter.felt = felt
    world = CabinWorld('cpu')
    cockpit.gotUp()
    world.walked(1)
    world.stationed(False, (), boxes)
    crewman = cockpit.crewman
    crewman.placed((ARENA[0], ARENA[1], ARENA[2] + 0.002 + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    cockpit.yaw, cockpit.pitch = 0.0, 0.0
    return cockpit, world, meter

  def _stepped(self, world: CabinWorld, meter: Accelerometer,
               cockpit: Cockpit, held: set, seconds: float) -> tuple:
    """Steps him 'seconds' s a frame at a time as the window does (his
    body turned, his legs as the keys 'held' ask); returns what he
    pushed the vessel back by, summed (N s, N m s), and how far he leant
    from up at the most (the cosine: the least of his up's z)."""
    crewman = cockpit.crewman
    push, twist, least = [0.0] * 3, [0.0] * 3, 1.0
    for _ in range(max(1, int(round(seconds / FRAME)))):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      cockpit.yaw, cockpit.pitch, back = crewman.righted(
        pull, FRAME, cockpit.yaw, cockpit.pitch)
      want = crewman.wantOf(held, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))
      own, turned = world.asgerPushed
      push = [a + b for a, b in zip(push, own)]
      twist = [a + b + c for a, b, c in zip(twist, turned, back)]
      least = min(least, crewman.up[2])
    return tuple(push), tuple(twist), least

  def test_head(self) -> None:
    """Walking into a slab at his forehead, it thuds and knocks his head
    back; let go, he stands up straight again."""
    over = 0.5 * (LOW + TALL)
    cockpit, world, meter = self._arena((0.0, 0.0, G0), (_box(
      (0.6, -1.0, over), (2.0, 1.0, over + 0.1), (0.0, 0.0, 0.0)),))
    self._stepped(world, meter, cockpit, set(), 0.2)
    crewman = cockpit.crewman
    leant = 1.0
    for _ in range(int(round(0.5 / FRAME))):
      _, _, least = self._stepped(world, meter, cockpit, {'ahead'}, FRAME)
      if crewman.up[0] < 0.0:
        leant = min(leant, least)
    self.assertGreater(world.thuds, 0)
    self.assertLess(leant, 0.995)
    self._stepped(world, meter, cockpit, set(), 3.0)
    self.assertGreater(crewman.up[2], 0.99)
    self.assertFalse(crewman.fallen)

  def test_spun(self) -> None:
    """Floating weightless at 1 m/s into a block at his head's height,
    his head stops and he spins on, head back; the vessel took as much
    push and twist as he did, the other way."""
    cockpit, world, meter = self._arena((0.0, 0.0, 0.0), (_box(
      (0.8, -1.0, 1.4), (1.4, 1.0, 2.6), (0.0, 0.0, 0.0)),))
    crewman = cockpit.crewman
    crewman.placed((ARENA[0], ARENA[1], ARENA[2] + 0.4 + MIDDLE),
                   (1.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    began = _held(crewman)
    push, twist, _ = self._stepped(world, meter, cockpit, set(), 1.0)
    ended = _held(crewman)
    self.assertGreater(world.thuds, 0)
    self.assertLess(crewman.spin[1], -0.3)
    self.assertGreater(crewman.velocity[0], -0.5)
    for k in range(3):
      self.assertLess(abs(push[k] + ended[0][k] - began[0][k]), 0.5)
      self.assertLess(abs(twist[k] + ended[1][k] - began[1][k]), 5.0)

  def test_toppled(self) -> None:
    """Standing, a block coming at 6 m/s into his shoulder knocks him
    down; he gets up again and stands."""
    block = ((-1.5, -0.6, 1.3), (-0.5, 0.6, 2.2))
    cockpit, world, meter = self._arena((0.0, 0.0, G0), (_box(
      *block, (6.0, 0.0, 0.0)),))
    crewman = cockpit.crewman
    self._stepped(world, meter, cockpit, set(), 0.1)
    fell = False
    for k in range(int(round(0.6 / FRAME))):
      t = (k + 1) * FRAME
      world.stationed(False, (), (_box(
        tuple(a + (6.0 * t if i == 0 else 0.0) for i, a in
              enumerate(block[0])),
        tuple(a + (6.0 * t if i == 0 else 0.0) for i, a in
              enumerate(block[1])), (6.0, 0.0, 0.0)),))
      self._stepped(world, meter, cockpit, set(), FRAME)
      fell = fell or crewman.fallen
    world.stationed(False, (), ())
    for _ in range(int(round(2.0 / FRAME))):
      self._stepped(world, meter, cockpit, set(), FRAME)
      fell = fell or crewman.fallen
    self.assertTrue(fell)
    self._stepped(world, meter, cockpit, set(), 6.0)
    self.assertFalse(crewman.fallen)
    self.assertGreater(crewman.up[2], 0.98)
    self.assertIsNotNone(crewman.floor)

  def test_carried(self) -> None:
    """Standing on a solid in one g, it takes his weight: what he pushed
    it by each frame is his mass times g, down."""
    cockpit, world, meter = self._arena((0.0, 0.0, G0), (_box(
      (-1.0, -1.0, -0.3), (1.0, 1.0, 0.3), (0.0, 0.0, 0.0)),))
    crewman = cockpit.crewman
    crewman.placed((ARENA[0], ARENA[1], ARENA[2] + 0.302 + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    self._stepped(world, meter, cockpit, set(), 0.5)
    total = [0.0, 0.0, 0.0]
    frames = 30
    for _ in range(frames):
      self._stepped(world, meter, cockpit, set(), FRAME)
      total = [a + b for a, b in zip(total, world.struck(0, 1)[0])]
    weight = HEFT * G0 * frames * FRAME
    self.assertLess(abs(total[2] + weight), 0.03 * weight)
    self.assertLess(abs(total[0]) + abs(total[1]), 0.01 * weight)
