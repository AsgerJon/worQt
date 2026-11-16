"""
IslandWorld is the world the sandbox's tests stand in: the void and an
island of grass on dirt floating in it, as big as the loop's island,
its top at nought; nothing else until spawned. Its physics is the small
steps on the CPU, under any universe.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.phys._body import Body, State
from worQt.phys._shape import boxShape
from worQt.phys._small_steps import THREADS, SmallSteps, preloaded

from worQt.gaming.sandbox import World

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import Universe

#  The island's top, m; it runs from 'FROM' to 'TO' along x and 'HALF'
#  either side of y nought, m; its grass over its dirt, m; their
#  density, kg/m³; where an avatar enters on it (x, y), m.
TOP = 0.0
FROM, TO, HALF = -6.0, 14.0, 6.0
GRASS, DIRT = 0.3, 2.7
SOIL = 1600.0
WALKER_AT = (-3.0, 3.5)
#  The small steps' longest step, s; fallen below this, m, a body has
#  left the world.
STEP = 2.5e-4
LOWEST = -40.0


class IslandWorld(World):
  """IslandWorld is the void with one island floating in it."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  LOOKS = {'grass': ((86, 128, 54), 0.0, 0.95),
           'dirt': ((112, 84, 58), 0.0, 1.0)}
  lowest = LOWEST

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, universe: Universe) -> None:
    World.__init__(self, universe, None)
    long, wide, middle = TO - FROM, 2.0 * HALF, 0.5 * (FROM + TO)
    self.fixed(Body.of(boxShape(long, wide, GRASS), SOIL),
               State((middle, 0.0, TOP - 0.5 * GRASS)), 'grass')
    self.fixed(Body.of(boxShape(long, wide, DIRT), SOIL),
               State((middle, 0.0, TOP - GRASS - 0.5 * DIRT)), 'dirt')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solverOf(self, ) -> SmallSteps:
    """The 'solverOf' method returns the small steps on the CPU."""
    return SmallSteps(self.universe.gravityVector(), None, STEP, 1, 0.0,
                      'cpu', THREADS, False)

  def spawnPoint(self, ) -> tuple:
    """The 'spawnPoint' method returns where an avatar enters: on the
    island at 'WALKER_AT', looking along x."""
    return (WALKER_AT[0], WALKER_AT[1], TOP), 0.0

  def readied(self, ) -> None:
    """The 'readied' method loads the small steps' kernels for the
    CPU."""
    preloaded('cpu')
