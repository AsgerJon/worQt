"""
Support sets displacements of a disk over a stretch of one of its edges.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import MissingVariable

from ._edge_num import EdgeNum
from ._edge_stretch import EdgeStretch

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Self


class Support(EdgeStretch):
  """
  Support sets displacements of a disk over a stretch of one of its
  edges, the way a bearing does. It sets the displacement along 'x', along
  'y' or both, the set side of the boundary condition; the reactions,
  'R', are what an analysis induces and are never stored here.

  Its line in a disk's text names the edge, the stretch and what it
  sets, in that order: 'support bottom 0 0.3 y' bears a disk's bottom
  left corner vertically, 'support bottom 5.7 6 x y' holds its bottom
  right corner both ways.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __support_sets__: tuple[bool, bool] | None = None

  #  Virtual Variables
  setsX: Field[bool] = Field()
  setsY: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getSets(self, ) -> tuple[bool, bool]:
    if self.__support_sets__ is None:
      raise MissingVariable(self, '__support_sets__', tuple)
    return self.__support_sets__

  @setsX.GET
  def _getSetsX(self, ) -> bool:
    """The 'setsX' getter tells whether the support sets the displacement
    along x."""
    return self._getSets()[0]

  @setsY.GET
  def _getSetsY(self, ) -> bool:
    """The 'setsY' getter tells whether the support sets the displacement
    along y."""
    return self._getSets()[1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    """The support's line in a disk's text."""
    sets = ['x'] if self.setsX else []
    sets += ['y'] if self.setsY else []
    return ' '.join(['support', *self._placeWords(), *sets])

  def __repr__(self, ) -> str:
    return """%s('%s')""" % (type(self).__name__, str(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__init__(
      other.edge, other.start, other.end, other.setsX,
      other.setsY
      )

  @overload(str)
  def __init__(self, line: str) -> None:
    words = str.split(line)
    if len(words) < 4 or words[0] != 'support':
      infoSpec = """expected 'support EDGE START END x y', not '%s'"""
      raise ValueError(infoSpec % line)
    edge, start, end = self._readPlace(words)
    sets = words[4:]
    for word in sets:
      if word not in ('x', 'y') or sets.count(word) > 1:
        infoSpec = """a support sets 'x', 'y' or both, once each: '%s'"""
        raise ValueError(infoSpec % line)
    self.__init__(edge, start, end, 'x' in sets, 'y' in sets)

  @overload(EdgeNum, float, float, bool, bool)
  def __init__(
      self, edge: EdgeNum, start: float, end: float, setsX: bool,
      setsY: bool,
  ) -> None:
    if not (setsX or setsY):
      raise ValueError("""a support sets 'x', 'y' or both""")
    self._place(edge, start, end)
    self.__support_sets__ = (bool(setsX), bool(setsY))
