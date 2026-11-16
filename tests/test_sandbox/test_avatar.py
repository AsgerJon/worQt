"""
TestAvatar covers the player's body ('Avatar') in the island's world: it
enters standing on the island at the spawn point; walks 6 m/s along
where it looks (turned, the new way), runs 12; jumps 0.8 m, only while
standing; flies (Space twice), rises, and lands with Shift; walked off
the island it falls, and fallen 25 m it is set back where it entered;
respawned (the E menu's 'Respawn') likewise, at once. Posed (its figure
as drawn): its soles under its ball, turned by its yaw, standing still
nothing swinging, striding a leg forward and its arm back, a tool in
hand its right arm held out along its look. A look turned half round
and its pitch turned over points back along its own ('looking', the
view from before it).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.sandbox import GravityGun
from worQt.gaming.sandbox._avatar import FALL, SWING

from . import SandboxTest
from ._islandworld import TOP, WALKER_AT

#  Where the avatar's ball stands entered, m.
STANDS = (WALKER_AT[0], WALKER_AT[1], TOP + 0.3)


class TestAvatar(SandboxTest):
  """Tests for the avatar (seconds)."""

  def test_enters(self) -> None:
    """Entered, it stands still on the island where the world spawns
    it, looking along x."""
    world, avatar = self.islandWorld()
    self.ran(world, 0.5)
    state = world.states[avatar.index]
    for got, wanted in zip(state.place, STANDS):
      self.assertAlmostEqual(got, wanted, 2)
    self.assertEqual(avatar.yaw, 0.0)
    eye, forward = avatar.eyes(state)
    self.assertAlmostEqual(eye[2], state.place[2] - 0.3 + 1.65, 6)
    self.assertEqual(forward, (1.0, 0.0, 0.0))

  def test_walks(self) -> None:
    """W walks it 6 m/s along where it looks; with Shift, 12; its head
    turned a quarter turn left (the mouse moved left), W walks along
    y."""
    world, avatar = self.islandWorld()
    avatar.held = frozenset(('w',))
    self.ran(world, 0.5)
    self.assertAlmostEqual(world.states[avatar.index].velocity[0], 6.0, 1)
    avatar.held = frozenset(('w', 'shift'))
    self.ran(world, 0.3)
    self.assertAlmostEqual(world.states[avatar.index].velocity[0], 12.0, 1)
    avatar.held = frozenset()
    self.ran(world, 0.5)
    avatar.turned(-0.5 * math.pi / 0.0025, 0.0)
    avatar.held = frozenset(('w',))
    self.ran(world, 0.5)
    vx, vy, _ = world.states[avatar.index].velocity
    self.assertAlmostEqual(vx, 0.0, 1)
    self.assertAlmostEqual(vy, 6.0, 1)

  def test_jumps(self) -> None:
    """Space jumps it 0.8 m up, standing; in the air another press does
    nothing."""
    world, avatar = self.islandWorld()
    self.ran(world, 0.3)
    avatar.pressed('space')
    highest = 0.0
    for _ in range(40):
      self.ran(world, 1.0 / 60.0)
      highest = max(highest, world.states[avatar.index].place[2])
    self.assertAlmostEqual(highest - STANDS[2], 0.8, 1)
    self.assertFalse(avatar.flying)

  def test_flies(self) -> None:
    """Space twice flies it; held, it rises 10 m/s; Shift held brings it
    down and lands it, walking again."""
    world, avatar = self.islandWorld()
    avatar.pressed('space')
    avatar.pressed('space')
    self.assertTrue(avatar.flying)
    avatar.held = frozenset(('space',))
    self.ran(world, 0.5)
    began = world.states[avatar.index].place[2]
    self.ran(world, 0.5)
    climbed = world.states[avatar.index].place[2] - began
    self.assertAlmostEqual(climbed, 5.0, 1)
    avatar.held = frozenset(('shift',))
    self.ran(world, 2.0)
    self.assertFalse(avatar.flying)
    self.assertAlmostEqual(world.states[avatar.index].place[2], STANDS[2],
                           1)

  def test_set_back(self) -> None:
    """Walked off the island it falls; fallen 'FALL' m it is set back
    where it entered, still."""
    world, avatar = self.islandWorld()
    avatar.held = frozenset(('d',))
    lowest = STANDS[2]
    for _ in range(8 * 60):
      self.ran(world, 1.0 / 60.0)
      height = world.states[avatar.index].place[2]
      if lowest < STANDS[2] - 20.0 and height > STANDS[2] - 1.0:
        break
      lowest = min(lowest, height)
    self.assertAlmostEqual(lowest, STANDS[2] - FALL, 0)
    state = world.states[avatar.index]
    self.assertAlmostEqual(state.place[0], STANDS[0], 1)
    self.assertAlmostEqual(state.place[2], STANDS[2], 1)

  def test_respawned(self) -> None:
    """Walked off and flying, respawned it is back where it entered,
    still, not flying, looking the way it first looked."""
    world, avatar = self.islandWorld()
    avatar.held = frozenset(('w',))
    self.ran(world, 0.5)
    avatar.held = frozenset()
    avatar.pressed('space')
    avatar.pressed('space')
    avatar.turned(300.0, 50.0)
    self.ran(world, 0.2)
    avatar.respawned()
    self.ran(world, 0.5)
    state = world.states[avatar.index]
    for got, wanted in zip(state.place, STANDS):
      self.assertAlmostEqual(got, wanted, 2)
    self.assertFalse(avatar.flying)
    self.assertEqual((avatar.yaw, avatar.pitch), (0.0, 0.0))

  def test_posed(self) -> None:
    """Its soles under its ball, turned by its yaw; still, nothing
    swings; mid-stride the right leg forward and the right arm back; a
    tool in hand, the right arm held out along the look."""
    world, avatar = self.islandWorld()
    self.ran(world, 0.3)
    state = world.states[avatar.index]
    avatar.yaw = 0.5 * math.pi
    soles, turn, angles = avatar.posed(state)
    for got, wanted in zip(soles, (state.place[0], state.place[1],
                                   state.place[2] - 0.3)):
      self.assertAlmostEqual(got, wanted, 9)
    for got, wanted in zip(turn, (math.cos(0.25 * math.pi), 0.0, 0.0,
                                  math.sin(0.25 * math.pi))):
      self.assertAlmostEqual(got, wanted, 9)
    self.assertEqual(angles[2:], (0.0, 0.0, 0.0, 0.0))
    avatar.gait.swing, avatar.gait.phase = 1.0, 0.5 * math.pi
    _, _, angles = avatar.posed(state)
    self.assertAlmostEqual(angles[4], -SWING, 9)
    self.assertAlmostEqual(angles[2], SWING, 9)
    avatar.hotbar.put(0, GravityGun())
    avatar.pitch = 0.3
    _, _, angles = avatar.posed(state)
    self.assertAlmostEqual(angles[0], -0.3, 9)
    way = (-math.sin(angles[2]), -math.cos(angles[2]))
    self.assertAlmostEqual(way[0], math.cos(0.3), 9)
    self.assertAlmostEqual(way[1], math.sin(0.3), 9)

  def test_looking(self) -> None:
    """Its look is 'looking' at its own yaw and pitch; half round with
    the pitch turned over, straight back against it."""
    world, avatar = self.islandWorld()
    avatar.yaw, avatar.pitch = 0.7, 0.4
    _, forward = avatar.eyes(world.states[avatar.index])
    self.assertEqual(forward, avatar.looking(0.7, 0.4))
    back = avatar.looking(0.7 + math.pi, -0.4)
    for got, wanted in zip(back, forward):
      self.assertAlmostEqual(got, -wanted, 12)

  def test_propelled(self) -> None:
    """It moves itself with W, A, S, D or Space held; Shift alone only
    flying; none held, not."""
    world, avatar = self.islandWorld()
    for held, flying, wanted in ((('w',), False, True),
                                 (('space',), False, True),
                                 (('shift',), False, False),
                                 (('shift',), True, True),
                                 ((), False, False)):
      with self.subTest(held=held, flying=flying):
        avatar.held, avatar.flying = frozenset(held), flying
        self.assertIs(avatar.propelled(), wanted)
