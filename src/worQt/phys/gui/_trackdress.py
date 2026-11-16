"""
TrackDress draws a railway track along its ribbon ('rail.Ribbon'): the
quads 'rail._trackshape.trackQuads' makes, made once, the same quads
handed back every frame (nothing moves).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ..rail._trackshape import BED_TOP, GAUGE, trackQuads

__all__ = ('BED_TOP', 'GAUGE', 'TrackDress', 'trackQuads')


class TrackDress:
  """
  TrackDress draws the track along 'ribbon' ('trackQuads'), made the
  first time it is asked, the same quads every frame after.
  """

  around = None

  def __init__(self, ribbon: object) -> None:
    self.ribbon, self.made = ribbon, None

  def quads(self, states: tuple) -> dict:
    """The 'quads' method returns the track's quads by key (the states
    move none of it)."""
    if self.made is None:
      self.made = trackQuads(self.ribbon)
    return self.made
