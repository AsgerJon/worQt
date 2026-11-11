"""
EdgeStretch is the base class of what acts over a stretch of one edge of
a disk: supports and loads.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable
from worktoy.waitaminute.keenum import KeeResolveError

from ._edge_num import EdgeNum
from ._numbers import formatNumber, parseNumber, checkStretch


class EdgeStretch(BaseObject):
  """
  EdgeStretch is the base class of what acts over a stretch of one edge
  of a disk: the 'edge', and the 'start' and 'end' of the stretch along
  it, in metres. Along the bottom and the top, positions count from the
  left; along the left and the right, from the bottom. A stretch always
  has a 'width': nothing acts on a disk at a point.

  Its line in a disk's text begins with a keyword naming the subclass,
  then the edge, the start and the end: 'support bottom 0 0.3 ...'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __stretch_edge__: EdgeNum | None = None
  __stretch_start__: float | None = None
  __stretch_end__: float | None = None

  #  Virtual Variables
  edge: Field[EdgeNum] = Field()
  start: Field[float] = Field()
  end: Field[float] = Field()
  width: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @edge.GET
  def _getEdge(self, ) -> EdgeNum:
    """The 'edge' getter returns the edge the stretch is on."""
    if self.__stretch_edge__ is None:
      raise MissingVariable(self, '__stretch_edge__', EdgeNum)
    return self.__stretch_edge__

  @start.GET
  def _getStart(self, ) -> float:
    """The 'start' getter returns where along its edge the stretch
    starts."""
    if self.__stretch_start__ is None:
      raise MissingVariable(self, '__stretch_start__', float)
    return self.__stretch_start__

  @end.GET
  def _getEnd(self, ) -> float:
    """The 'end' getter returns where along its edge the stretch ends."""
    if self.__stretch_end__ is None:
      raise MissingVariable(self, '__stretch_end__', float)
    return self.__stretch_end__

  @width.GET
  def _getWidth(self, ) -> float:
    """The 'width' getter returns how long the stretch is."""
    return self.end - self.start

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _place(self, edge: EdgeNum, start: float, end: float) -> None:
    """Places the stretch on 'edge' from 'start' to 'end'."""
    checkStretch(start, end)
    self.__stretch_edge__ = edge
    self.__stretch_start__ = float(start)
    self.__stretch_end__ = float(end)

  @staticmethod
  def _readPlace(words: list[str]) -> tuple[EdgeNum, float, float]:
    """Reads the edge, the start and the end from the words of a line,
    after its keyword."""
    try:
      edge = EdgeNum(words[1])
    except KeeResolveError as exception:
      infoSpec = """no edge is called '%s'"""
      raise ValueError(infoSpec % words[1]) from exception
    start = parseNumber(words[2], 'start')
    end = parseNumber(words[3], 'end')
    return edge, start, end

  def _placeWords(self, ) -> list[str]:
    """The edge, the start and the end, as they are written in a line."""
    start, end = formatNumber(self.start), formatNumber(self.end)
    return [self.edge.value, start, end]
