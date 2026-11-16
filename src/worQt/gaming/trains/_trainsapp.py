"""
TrainsApp opens the sandbox on the loop's world.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox import EARTH_GRAVITY, Universe
from worQt.gaming.sandbox._sandboxapp import SandboxApp

from ._loopworld import LoopWorld


class TrainsApp(SandboxApp):
  """
  TrainsApp is the sandbox opened on the loop's world ('LoopWorld'),
  under the earth's universe.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def worldOf(self, ) -> LoopWorld:
    """The 'worldOf' method returns the loop's world under the earth's
    universe."""
    return LoopWorld(Universe(EARTH_GRAVITY))
