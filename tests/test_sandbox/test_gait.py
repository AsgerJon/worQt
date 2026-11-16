"""
TestGait covers the view's bobbing ('Gait', 'Avatar.viewed'): standing
still nothing sways; walking at full speed the eyes rise and fall
'RISE' a step and sway 'SWAY' a stride, a stride every 'STRIDE' m; in
the air the swing eases out; where the avatar aims never sways.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox._gait import FULL, RISE, STRIDE, SWAY, Gait

from . import SandboxTest

#  A frame, s.
FRAME = 1.0 / 60.0


class TestGait(SandboxTest):
  """Tests for the view's bobbing."""

  def walked(self, gait: Gait, speed: float, grounded: bool,
             seconds: float) -> list:
    """Returns the offsets met walking 'seconds' at 'speed'."""
    out = []
    for _ in range(int(round(seconds / FRAME))):
      gait.stepped(speed, grounded, FRAME)
      out.append(gait.offset())
    return out

  def test_still(self) -> None:
    """Standing still, nothing sways."""
    offsets = self.walked(Gait(), 0.0, True, 1.0)
    self.assertEqual(max(abs(x) for pair in offsets for x in pair), 0.0)

  def test_walking(self) -> None:
    """At full speed the rise and the sway reach their sizes, a stride
    every 'STRIDE' m."""
    gait = Gait()
    self.walked(gait, FULL, True, 1.0)
    offsets = self.walked(gait, FULL, True, STRIDE / FULL)
    self.assertAlmostEqual(max(up for _, up in offsets), RISE, 3)
    self.assertAlmostEqual(max(side for side, _ in offsets), SWAY, 3)

  def test_air(self) -> None:
    """Off the ground the swing eases out."""
    gait = Gait()
    self.walked(gait, FULL, True, 1.0)
    self.walked(gait, FULL, False, 1.0)
    self.assertLess(gait.swing, 0.01)

  def test_aim_still(self) -> None:
    """Walking sways where the avatar is seen from, never where it
    aims."""
    world, avatar = self.islandWorld()
    avatar.held = frozenset(('w',))
    self.ran(world, 0.5)
    state = world.states[avatar.index]
    for _ in range(10):
      viewed, _, _ = avatar.viewed(state, FRAME)
    aimed, _ = avatar.eyes(state)
    self.assertNotEqual(viewed, aimed)
    self.assertEqual(avatar.eyes(state)[0], aimed)
