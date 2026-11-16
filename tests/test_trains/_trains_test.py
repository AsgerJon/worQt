"""
TrainsTest is the base class for the tests of 'worQt.gaming.trains': a
'SandboxTest' (stepping a world a frame at a time: 'ran') adding the
loop's world on the CPU with an avatar entered ('loopWorld') and the
steam train's oval on the CPU ('ovalWorld').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox import EARTH_GRAVITY, PERSON, Avatar, Universe
from worQt.gaming.trains import LoopWorld
from worQt.gaming.trains._ovalworld import OvalWorld

from tests.test_sandbox import SandboxTest


class TrainsTest(SandboxTest):
  """TrainsTest is the base class for the tests of the trains."""

  def loopWorld(self, ) -> tuple:
    """Returns the loop's world on the CPU and an avatar entered in it."""
    world = LoopWorld(Universe(EARTH_GRAVITY))
    world.device = 'cpu'
    avatar = Avatar(PERSON)
    avatar.enter(world)
    return world, avatar

  def ovalWorld(self, ) -> object:
    """Returns the steam train's oval on the CPU (no avatar)."""
    world = OvalWorld(Universe(EARTH_GRAVITY))
    world.device = 'cpu'
    return world
