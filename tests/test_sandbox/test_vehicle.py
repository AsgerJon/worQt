"""
TestVehicle covers riding ('Vehicle', the avatar's E) on the island's
world, with a bench for a vehicle: within 'REACH' of it ('nearby'), E
seats the avatar (its ball tied in the seat, moving with it, its eyes'
up the bench's); from too far, nothing (nor is it nearby); riding, E
does nothing (the window's menu), Shift or 'leave' lets go, the avatar
standing on the bench where the seat was; a
vehicle in no world has no frame, and takes one rider; respawned, a
rider leaves it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._assembly import Tie
from worQt.phys._body import Body, State
from worQt.phys._shape import boxShape

from worQt.gaming.sandbox import Vehicle
from worQt.gaming.sandbox._avatar import REACH
from worQt.gaming.sandbox._skin import SEATED

from . import SandboxTest
from ._islandworld import TOP

#  How the bench meets things: steel, its edges (and the island's
#  against it) met every 0.1 m (every centimetre of the island's 20 m
#  edges took minutes on the CPU).
STEEL = (1e6, 1.0, 0.5, 1e6, 2e3, 0.1)


class _Bench(Vehicle):
  """A steel bench 1 x 1 x 0.5 m on the island at x 2, its seat on top."""

  seat = (0.0, 0.0, 0.25 + 0.305)

  def placed(self, world: object) -> None:
    """Puts the bench on the island."""
    body = Body.of(boxShape(1.0, 1.0, 0.5), 7850.0)
    index = world.spawned(body, State((2.0, 0.0, TOP + 0.25)), STEEL,
                          'dirt')
    self.world, self.bodies = world, (index,)


class TestVehicle(SandboxTest):
  """Tests for riding a vehicle (seconds)."""

  def benched(self, away: float) -> tuple:
    """Returns the island's world with a bench, and the avatar 'away' m
    behind it, looking at its middle."""
    world, avatar = self.islandWorld()
    bench = _Bench()
    world.addVehicle(bench)
    states = list(world.states)
    states[avatar.index] = State((2.0 - away, 0.0, TOP + 0.3))
    world.states = tuple(states)
    self.ran(world, 0.2)
    eye, _ = avatar.eyes(world.states[avatar.index])
    middle = world.states[bench.frame].place
    avatar.yaw = math.atan2(middle[1] - eye[1], middle[0] - eye[0])
    avatar.pitch = math.atan2(middle[2] - eye[2], math.hypot(
      middle[0] - eye[0], middle[1] - eye[1]))
    return world, avatar, bench

  def test_boards(self) -> None:
    """Near it, E seats it: tied in the seat, moving with it, up the
    bench's."""
    world, avatar, bench = self.benched(2.0)
    self.assertIs(avatar.nearby(), bench)
    avatar.pressed('e')
    self.ran(world, 0.5)
    self.assertIs(avatar.riding, bench)
    self.assertIs(bench.rider, avatar)
    body = world.assembly.bodies[bench.frame]
    seat = body.placeOf(world.states[bench.frame], bench.seat)
    self.assertLess(math.dist(world.states[avatar.index].place, seat),
                    1e-3)
    ties = [c for c in world.assembly.connections if isinstance(c, Tie)]
    self.assertEqual(len(ties), 1)
    for got, wanted in zip(avatar.up(), (0.0, 0.0, 1.0)):
      self.assertAlmostEqual(got, wanted, 3)
    eye, _ = avatar.eyes(world.states[avatar.index])
    self.assertAlmostEqual(eye[2] - seat[2], 1.65 - 0.3, 6)

  def test_too_far(self) -> None:
    """From beyond 'REACH' it is not nearby and E does nothing."""
    world, avatar, bench = self.benched(REACH + 3.0)
    self.assertIsNone(avatar.nearby())
    avatar.pressed('e')
    self.ran(world, 0.2)
    self.assertIsNone(avatar.riding)
    self.assertIsNone(bench.rider)

  def test_leaves(self) -> None:
    """Shift lets go: no tie, standing on the bench."""
    world, avatar, bench = self.benched(2.0)
    avatar.pressed('e')
    self.ran(world, 0.2)
    avatar.pressed('shift')
    self.ran(world, 0.5)
    self.assertIsNone(avatar.riding)
    self.assertIsNone(bench.rider)
    self.assertFalse(any(isinstance(c, Tie)
                         for c in world.assembly.connections))
    self.assertAlmostEqual(world.states[avatar.index].place[2],
                           TOP + 0.5 + 0.3, 1)
    self.assertTrue(avatar.grounded)

  def test_shift_leaves(self) -> None:
    """Riding, E does nothing (the window opens the vehicle's menu);
    Shift leaves, as does 'leave'."""
    world, avatar, bench = self.benched(2.0)
    avatar.pressed('e')
    self.ran(world, 0.2)
    avatar.pressed('e')
    self.ran(world, 0.2)
    self.assertIs(avatar.riding, bench)
    avatar.pressed('shift')
    self.ran(world, 0.2)
    self.assertIsNone(avatar.riding)
    avatar.pressed('e')
    self.ran(world, 0.2)
    self.assertIs(avatar.riding, bench)
    avatar.leave()
    self.ran(world, 0.2)
    self.assertIsNone(avatar.riding)

  def test_one_rider(self) -> None:
    """A vehicle in no world has no frame; it takes one rider."""
    with self.assertRaises(RuntimeError):
      _ = _Bench().frame
    world, avatar, bench = self.benched(2.0)
    avatar.pressed('e')
    self.ran(world, 0.2)
    with self.assertRaises(RuntimeError):
      bench.boarded(avatar, list(world.states))

  def test_respawned(self) -> None:
    """Riding, respawned it leaves the vehicle and is back where it
    entered."""
    world, avatar, bench = self.benched(2.0)
    avatar.pressed('e')
    self.ran(world, 0.2)
    avatar.respawned()
    self.ran(world, 0.5)
    self.assertIsNone(avatar.riding)
    self.assertIsNone(bench.rider)
    self.assertFalse(any(isinstance(c, Tie)
                         for c in world.assembly.connections))
    self.assertAlmostEqual(world.states[avatar.index].place[0],
                           avatar.entered.place[0], 2)

  def test_seated(self) -> None:
    """Riding, its figure sits: its legs ahead, its soles 'SEATED'
    pixels under the seat's ball's lowest point; it never moves itself
    (the vehicle does), whatever keys are held."""
    world, avatar, bench = self.benched(2.0)
    avatar.pressed('e')
    self.ran(world, 0.3)
    state = world.states[avatar.index]
    soles, _, angles = avatar.posed(state)
    self.assertEqual(angles[4:], (-0.5 * math.pi, -0.5 * math.pi))
    avatar.held = frozenset(('w', 'space'))
    self.assertFalse(avatar.propelled())
    self.assertAlmostEqual(soles[2], state.place[2] - 0.3
                           - SEATED * avatar.scale(), 3)
