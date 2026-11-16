"""
SteamApp opens the sandbox on the steam train's oval.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox import EARTH_GRAVITY, Universe

from ._ovalworld import OvalWorld
from ._trainsapp import TrainsApp


class SteamApp(TrainsApp):
  """
  SteamApp is the sandbox opened on the steam train's oval
  ('OvalWorld'), under the earth's universe.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def worldOf(self, ) -> OvalWorld:
    """The 'worldOf' method returns the steam train's oval under the
    earth's universe."""
    return OvalWorld(Universe(EARTH_GRAVITY))
