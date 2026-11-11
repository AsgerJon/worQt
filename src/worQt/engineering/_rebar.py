"""
Rebar is a group of straight reinforcing bars in a disk.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._numbers import formatNumber, parseNumber, checkPositive

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Self


class Rebar(BaseObject):
  """
  Rebar is a group of straight reinforcing bars in a disk: 'count' bars
  of a 'diameter' in mm, running side by side from 'start' to 'end', two
  points of the disk in metres. Its 'area' is that of all the bars, in
  mm², and its 'name' is what a drawing calls it: '4 Ø20'.

  Its line in a disk's text gives the two points, then the count and the
  diameter: 'rebar 0.05 0.06 5.95 0.06 4 20' runs four 20 mm bars along
  the bottom of a 6 m disk, 60 mm up.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __rebar_points__: tuple[float, float, float, float] | None = None
  __rebar_bars__: tuple[int, float] | None = None

  #  Virtual Variables
  start: Field[tuple[float, float]] = Field()
  end: Field[tuple[float, float]] = Field()
  count: Field[int] = Field()
  diameter: Field[float] = Field()
  area: Field[float] = Field()
  name: Field[str] = Field()
  horizontal: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getPoints(self, ) -> tuple[float, float, float, float]:
    if self.__rebar_points__ is None:
      raise MissingVariable(self, '__rebar_points__', tuple)
    return self.__rebar_points__

  def _getBars(self, ) -> tuple[int, float]:
    if self.__rebar_bars__ is None:
      raise MissingVariable(self, '__rebar_bars__', tuple)
    return self.__rebar_bars__

  @start.GET
  def _getStart(self, ) -> tuple[float, float]:
    """The 'start' getter returns where the bars start, in metres."""
    return self._getPoints()[:2]

  @end.GET
  def _getEnd(self, ) -> tuple[float, float]:
    """The 'end' getter returns where the bars end, in metres."""
    return self._getPoints()[2:]

  @count.GET
  def _getCount(self, ) -> int:
    """The 'count' getter returns how many bars there are."""
    return self._getBars()[0]

  @diameter.GET
  def _getDiameter(self, ) -> float:
    """The 'diameter' getter returns the diameter of a bar, in mm."""
    return self._getBars()[1]

  @area.GET
  def _getArea(self, ) -> float:
    """The 'area' getter returns the area of all the bars, in mm²."""
    return self.count * math.pi * self.diameter ** 2 / 4

  @name.GET
  def _getName(self, ) -> str:
    """The 'name' getter returns the bars as a drawing names them."""
    return '%d Ø%s' % (self.count, formatNumber(self.diameter))

  @horizontal.GET
  def _getHorizontal(self, ) -> bool:
    """The 'horizontal' getter tells whether the bars run along x."""
    x1, y1, x2, y2 = self._getPoints()
    return True if abs(y1 - y2) < 1e-9 else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    """The bars' line in a disk's text."""
    points = (formatNumber(value) for value in self._getPoints())
    return 'rebar %s %s %s %s %d %s' % (
      *points, self.count,
      formatNumber(self.diameter)
    )

  def __repr__(self, ) -> str:
    return """%s('%s')""" % (type(self).__name__, str(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__init__(*other.start, *other.end, other.count, other.diameter)

  @overload(str)
  def __init__(self, line: str) -> None:
    words = str.split(line)
    if len(words) != 7 or words[0] != 'rebar':
      infoSpec = """expected 'rebar X1 Y1 X2 Y2 COUNT DIAMETER', not '%s'"""
      raise ValueError(infoSpec % line)
    names = ('x1', 'y1', 'x2', 'y2', 'count', 'diameter')
    x1, y1, x2, y2, count, diameter = (
      parseNumber(word, name) for word, name in zip(words[1:], names)
    )
    if count != int(count):
      raise ValueError("""the count of bars is whole, not %s""" % words[5])
    self.__init__(x1, y1, x2, y2, int(count), diameter)

  @overload(float, float, float, float, int, float)
  def __init__(
      self, x1: float, y1: float, x2: float, y2: float, count: int,
      diameter: float,
  ) -> None:
    if count < 1:
      raise ValueError("""there is at least one bar, not %d""" % count)
    checkPositive('diameter', diameter)
    if math.hypot(x2 - x1, y2 - y1) < 1e-9:
      raise ValueError("""bars run from one point to another""")
    self.__rebar_points__ = (float(x1), float(y1), float(x2), float(y2))
    self.__rebar_bars__ = (int(count), float(diameter))
