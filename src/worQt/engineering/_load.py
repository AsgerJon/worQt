"""
Load applies a force to a disk, spread over a stretch of one of its
edges.
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
from ._numbers import formatNumber, parseNumber

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Self


class Load(EdgeStretch):
  """
  Load applies a force 'F' to a disk, in kN, spread evenly over a
  stretch of one of its edges: the set side of the boundary condition.
  A point load is a short stretch, as wide as what it bears on; a line
  load is a long one. 'intensity' is the force per metre of the stretch.

  Its line in a disk's text names the edge and the stretch, then the
  force after 'F', x before y: 'load top 0 6 F 0 -1200' presses 1200 kN
  down along the whole top of a 6 m disk.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __load_force__: tuple[float, float] | None = None

  #  Virtual Variables
  fx: Field[float] = Field()
  fy: Field[float] = Field()
  intensity: Field[tuple[float, float]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getForce(self, ) -> tuple[float, float]:
    if self.__load_force__ is None:
      raise MissingVariable(self, '__load_force__', tuple)
    return self.__load_force__

  @fx.GET
  def _getFx(self, ) -> float:
    """The 'fx' getter returns the force along x, in kN."""
    return self._getForce()[0]

  @fy.GET
  def _getFy(self, ) -> float:
    """The 'fy' getter returns the force along y, in kN."""
    return self._getForce()[1]

  @intensity.GET
  def _getIntensity(self, ) -> tuple[float, float]:
    """The 'intensity' getter returns the force per metre of the
    stretch, in kN/m, x before y."""
    return self.fx / self.width, self.fy / self.width

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    """The load's line in a disk's text."""
    force = [formatNumber(self.fx), formatNumber(self.fy)]
    return ' '.join(['load', *self._placeWords(), 'F', *force])

  def __repr__(self, ) -> str:
    return """%s('%s')""" % (type(self).__name__, str(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__init__(other.edge, other.start, other.end, other.fx, other.fy)

  @overload(str)
  def __init__(self, line: str) -> None:
    words = str.split(line)
    if len(words) != 7 or words[0] != 'load' or words[4] != 'F':
      infoSpec = """expected 'load EDGE START END F FX FY', not '%s'"""
      raise ValueError(infoSpec % line)
    edge, start, end = self._readPlace(words)
    fx = parseNumber(words[5], 'force along x')
    fy = parseNumber(words[6], 'force along y')
    self.__init__(edge, start, end, fx, fy)

  @overload(EdgeNum, float, float, float, float)
  def __init__(
      self, edge: EdgeNum, start: float, end: float, fx: float, fy: float,
  ) -> None:
    self._place(edge, start, end)
    self.__load_force__ = (float(fx), float(fy))
