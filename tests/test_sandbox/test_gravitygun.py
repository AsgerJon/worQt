"""
TestGravityGun covers the first tool ('GravityGun') in the avatar's
hands on the island: it points at a ball before the eyes, pulls
it in on the right button and holds it before the eyes, carries it as
the avatar walks, drops it on the right button again, punts it along
the look at 12 m/s (a yeet; a punt of what is only pointed at counts
as a punt), the gun jabbed forward for a moment; it hums idle, then
holding; held, a ball sits nearer than 0.8 m; the wheel moves only
what is held; the world's own bodies (the island) are never
pointed at.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.sandbox import ITEMS, GravityGun
from worQt.gaming.sandbox._avatar import PUNCH, THRUST
from worQt.gaming.sandbox._gravitygun import LOWEST, PUNT_SPEED

from . import SandboxTest
from ._islandworld import TOP


class TestGravityGun(SandboxTest):
  """Tests for the gravity gun (seconds)."""

  def aimed(self, ) -> tuple:
    """Returns the world, the avatar, the gun in its hands and a ball 3 m
    before it on the island, the avatar looking at the ball."""
    world, avatar = self.islandWorld()
    gun = GravityGun()
    avatar.hotbar.put(0, gun)
    self.ran(world, 0.3)
    ball = ITEMS[0].spawned(world, (0.0, 3.5, TOP + 0.15))
    self.ran(world, 0.5)
    eye, _ = avatar.eyes(world.states[avatar.index])
    at = world.states[ball].place
    avatar.pitch = math.atan2(at[2] - eye[2], at[0] - eye[0])
    self.ran(world, 0.05)
    return world, avatar, gun, ball

  def test_holds(self) -> None:
    """Pointed at, pulled in and held before the eyes, about its hold's
    length out along the look; humming idle, then holding."""
    world, avatar, gun, ball = self.aimed()
    self.assertEqual(gun.pointed, ball)
    self.assertEqual(gun.humming, 1)
    gun.pressed('right')
    self.ran(world, 1.5)
    self.assertEqual(gun.held, ball)
    self.assertEqual(gun.humming, 2)
    eye, _ = avatar.eyes(world.states[avatar.index])
    out = math.dist(eye, world.states[ball].place)
    hold = gun.grabber.holdOf(world.assembly.bodies[ball])
    self.assertAlmostEqual(out, hold, None, None, 0.1)

  def test_carries(self) -> None:
    """Held, it goes along as the avatar walks; dropped, it falls."""
    world, avatar, gun, ball = self.aimed()
    gun.pressed('right')
    self.ran(world, 1.5)
    avatar.held = frozenset(('w',))
    self.ran(world, 0.5)
    avatar.held = frozenset()
    gap = world.states[ball].place[0] - world.states[avatar.index].place[0]
    hold = gun.grabber.holdOf(world.assembly.bodies[ball])
    self.assertLess(hold, 0.8)
    self.assertAlmostEqual(gap, hold * math.cos(LOWEST), None, None, 0.2)
    gun.pressed('right')
    self.ran(world, 1.0)
    self.assertIsNone(gun.held)
    self.assertAlmostEqual(world.states[ball].place[2], TOP + 0.15, 2)

  def test_punts(self) -> None:
    """A punt sends what is held off along the look at 'PUNT_SPEED' and
    lets it go."""
    world, avatar, gun, ball = self.aimed()
    gun.pressed('right')
    self.ran(world, 1.5)
    before = world.states[ball].velocity
    gun.pressed('left')
    self.ran(world, 1.0 / 60.0)
    self.assertIsNone(gun.held)
    after = world.states[ball].velocity
    gained = math.sqrt(sum((a - b) ** 2 for a, b in zip(after, before)))
    self.assertAlmostEqual(gained, PUNT_SPEED, None, None, 0.5)
    self.assertEqual((gun.yeets, gun.punts), (1, 0))
    punched = gun.punched
    self.assertIsNotNone(punched)
    self.assertAlmostEqual(avatar.thrust(gun, punched + 0.5 * PUNCH),
                           THRUST, 9)
    self.assertEqual(avatar.thrust(gun, punched + PUNCH), 0.0)

  def test_punt_counted(self) -> None:
    """A punt of what is pointed at (not held) counts as a punt, not a
    yeet."""
    world, avatar, gun, ball = self.aimed()
    gun.pressed('left')
    self.ran(world, 1.0 / 60.0)
    self.assertEqual((gun.yeets, gun.punts), (0, 1))
    self.assertGreater(abs(world.states[ball].velocity[0]), 1.0)

  def test_wheel(self) -> None:
    """The wheel moves the hold only while holding."""
    world, avatar, gun, ball = self.aimed()
    self.assertFalse(gun.wheeled(1.0))
    gun.pressed('right')
    self.ran(world, 1.5)
    self.assertTrue(gun.wheeled(2.0))
    self.assertEqual(gun.further, 0.5)

  def test_world_not_grabbed(self) -> None:
    """Looking straight down at the island, nothing is pointed at."""
    world, avatar = self.islandWorld()
    gun = GravityGun()
    avatar.hotbar.put(0, gun)
    avatar.pitch = -1.4
    self.ran(world, 0.2)
    self.assertIsNone(gun.pointed)
