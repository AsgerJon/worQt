"""
SandboxTest is the base class for the tests of 'worQt.gaming.sandbox': it
subclasses 'BaseTest', adding the island's world (the void and one
island, on the CPU) with an avatar entered ('islandWorld') and stepping
a world a frame at a time ('ran').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.gaming.sandbox import EARTH_GRAVITY, PERSON, Avatar
from worQt.gaming.sandbox import Universe

from ._islandworld import IslandWorld

#  A frame, s.
FRAME = 1.0 / 60.0


class SandboxTest(BaseTest):
  """SandboxTest is the base class for the tests of the sandbox."""

  def islandWorld(self, ) -> tuple:
    """Returns the island's world and an avatar entered in it."""
    world = IslandWorld(Universe(EARTH_GRAVITY))
    avatar = Avatar(PERSON)
    avatar.enter(world)
    return world, avatar

  def ran(self, world: object, seconds: float) -> None:
    """Steps 'world' on 'seconds', a frame at a time."""
    for _ in range(int(round(seconds / FRAME))):
      world.advanced(FRAME)
