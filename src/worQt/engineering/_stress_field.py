"""
StressField is the stress in a disk of plain, uncracked concrete, found
by OpenSees.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple, TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from worksees import Model, Solver

from ._disk import Disk
from ._edge_num import EdgeNum
from ._edge_stretch import EdgeStretch

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worksees import Result

_TOLERANCE = 1e-9
_KPA = 1000.0  # kN/m2 to the MPa


class CellStress(NamedTuple):
  """
  CellStress is the stress in a cell of a disk's mesh, in MPa, tension
  positive: 'sx' along x, 'sy' along y and 'sxy' the shear, at its
  centre ('x', 'y') in metres. 'major' and 'minor' are the principal
  stresses, and 'angle' is the direction of the major one, in radians
  from x.
  """

  x: float
  y: float
  sx: float
  sy: float
  sxy: float

  @property
  def major(self) -> float:
    """The greater principal stress."""
    return (self.sx + self.sy) / 2 + self._radius()

  @property
  def minor(self) -> float:
    """The lesser principal stress."""
    return (self.sx + self.sy) / 2 - self._radius()

  @property
  def angle(self) -> float:
    """The direction of the greater principal stress, from x."""
    return math.atan2(2 * self.sxy, self.sx - self.sy) / 2

  def _radius(self) -> float:
    """The radius of Mohr's circle."""
    return math.hypot((self.sx - self.sy) / 2, self.sxy)


class StressField(BaseObject):
  """
  StressField is the stress in a 'Disk' of plain, uncracked concrete,
  linear elastic: the field it carries its loads by before it cracks,
  its bars left out. OpenSees finds it on a mesh of four-node plane
  stress quads, the 'columns' and 'rows' of the mesh at most a
  'divisions'th of the shorter side apart and at the end of every
  support and load; the concrete's modulus 'Ecm' is EN 1992-1-1's
  22 ((fc + 8) / 10)^0.3 GPa, its Poisson's ratio 0.2.

  'cells' are the stresses, a 'CellStress' to each cell, row by row
  from the bottom left; 'reactions' are what each support gives the
  disk, (Rx, Ry) in kN. A disk its supports do not hold, free to slide
  or turn, has no field: 'applicable' is False and 'reason' says why.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_divisions__ = 24  # cells across the shorter side, at least
  __fallback_poisson__ = 0.2

  #  Private Variables
  __field_disk__: Disk | None = None
  __field_lines__: tuple[tuple, tuple] = ((), ())
  __field_cells__: tuple[CellStress, ...] = ()
  __field_reactions__: tuple[tuple[float, float], ...] = ()
  __field_reason__: str = ''

  #  Virtual Variables
  disk: Field[Disk] = Field()
  Ecm: Field[float] = Field()
  columns: Field[tuple[float, ...]] = Field()
  rows: Field[tuple[float, ...]] = Field()
  cells: Field[tuple[CellStress, ...]] = Field()
  reactions: Field[tuple[tuple[float, float], ...]] = Field()
  applicable: Field[bool] = Field()
  reason: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @disk.GET
  def _getDisk(self, ) -> Disk:
    """The 'disk' getter returns the disk the field is in."""
    if self.__field_disk__ is None:
      raise MissingVariable(self, '__field_disk__', Disk)
    return self.__field_disk__

  @Ecm.GET
  def _getEcm(self, ) -> float:
    """The 'Ecm' getter returns the concrete's modulus, in MPa."""
    return 22000.0 * ((self.disk.fc + 8.0) / 10.0) ** 0.3

  @columns.GET
  def _getColumns(self, ) -> tuple[float, ...]:
    """The 'columns' getter returns where the mesh's lines across x are,
    from the left, in metres."""
    return self.__field_lines__[0]

  @rows.GET
  def _getRows(self, ) -> tuple[float, ...]:
    """The 'rows' getter returns where the mesh's lines across y are,
    from the bottom, in metres."""
    return self.__field_lines__[1]

  @cells.GET
  def _getCells(self, ) -> tuple[CellStress, ...]:
    """The 'cells' getter returns the stress in each cell, row by row
    from the bottom left; none where there is no field."""
    return self.__field_cells__

  @reactions.GET
  def _getReactions(self, ) -> tuple[tuple[float, float], ...]:
    """The 'reactions' getter returns what each support gives the disk,
    (Rx, Ry) in kN."""
    return self.__field_reactions__

  @applicable.GET
  def _getApplicable(self, ) -> bool:
    """The 'applicable' getter tells whether the disk has a field: its
    supports hold it."""
    return False if self.__field_reason__ else True

  @reason.GET
  def _getReason(self, ) -> str:
    """The 'reason' getter says why the disk has no field, if it has
    none."""
    return self.__field_reason__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Disk, Solver)
  def __init__(self, disk: Disk, solver: Solver) -> None:
    self.__field_disk__ = disk
    self.__field_lines__ = (
      self._lines(EdgeNum.BOTTOM, EdgeNum.TOP),
      self._lines(EdgeNum.LEFT, EdgeNum.RIGHT)
    )
    self.__field_reason__ = self._unheld()
    if self.applicable:
      self._solve(solver)

  @overload(Disk)
  def __init__(self, disk: Disk) -> None:
    with Solver() as solver:
      self.__init__(disk, solver)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def cellAt(self, column: int, row: int) -> CellStress:
    """The 'cellAt' method returns the stress in the cell right of the
    line 'column' and above the line 'row', both counted from 0."""
    return self.cells[column + row * (len(self.columns) - 1)]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _lines(self, *edges: EdgeNum) -> tuple[float, ...]:
    """The mesh's lines along 'edges': at the ends of every stretch on
    them, and between those at most a division apart."""
    disk = self.disk
    size = min(disk.length, disk.height) / self.__fallback_divisions__
    ends = {0.0, disk.edgeLength(edges[0])}
    for stretch in self._stretches():
      if stretch.edge in edges:
        ends |= {stretch.start, stretch.end}
    ends = sorted(ends)
    lines = [ends[0]]
    for start, end in zip(ends, ends[1:]):
      count = max(1, math.ceil((end - start) / size - _TOLERANCE))
      lines += [start + (end - start) * n / count
                for n in range(1, count + 1)]
    return (*lines,)

  def _stretches(self, ) -> tuple[EdgeStretch, ...]:
    """The supports and the loads."""
    return (*self.disk.supports, *self.disk.loads)

  def _edgeNodes(self, stretch: EdgeStretch) -> list[tuple[int, float]]:
    """The nodes along 'stretch', each with where it is along the edge,
    in order."""
    edge = stretch.edge
    columns, rows = self.columns, self.rows
    across = len(columns)
    if edge.horizontal:
      row = 0 if edge is EdgeNum.BOTTOM else len(rows) - 1
      places = [(1 + i + row * across, x) for i, x in enumerate(columns)]
    else:
      column = 0 if edge is EdgeNum.LEFT else across - 1
      places = [(1 + column + j * across, y) for j, y in enumerate(rows)]
    low, high = stretch.start - _TOLERANCE, stretch.end + _TOLERANCE
    return [(node, at) for node, at in places if low <= at <= high]

  def _unheld(self, ) -> str:
    """Why the supports do not hold the disk, or nothing if they do: they
    must stop it sliding along x and along y and turning."""
    disk = self.disk
    scale = max(disk.length, disk.height)
    sets = []
    for support in disk.supports:
      for node, at in self._edgeNodes(support):
        x, y = disk.pointAt(support.edge, at)
        x, y = (x - disk.length / 2) / scale, (y - disk.height / 2) / scale
        sets += [(1.0, 0.0, -y)] if support.setsX else []
        sets += [(0.0, 1.0, x)] if support.setsY else []
    if not any(row[0] for row in sets):
      return 'nothing holds it along x'
    if not any(row[1] for row in sets):
      return 'nothing holds it along y'
    gram = [[sum(row[a] * row[b] for row in sets) for b in range(3)]
            for a in range(3)]
    if _determinant(gram) < _TOLERANCE * len(sets) ** 3:
      return 'nothing stops it turning'
    return ''

  def _model(self, ) -> Model:
    """The disk as a mesh of plane stress quads, in m and kN."""
    disk = self.disk
    model = Model(2, 2)
    for y in self.rows:
      for x in self.columns:
        model.addNode(x, y)
    concrete = model.add(
      'nDMaterial', 'ElasticIsotropic',
      self.Ecm * _KPA, self.__fallback_poisson__
      )
    across = len(self.columns)
    for j in range(len(self.rows) - 1):
      for i in range(across - 1):
        corner = 1 + i + j * across
        model.add(
          'element', 'quad', corner, corner + 1,
          corner + 1 + across, corner + across, disk.thickness,
          'PlaneStress', concrete
          )
    for support in disk.supports:
      for node, _ in self._edgeNodes(support):
        model.fix(node, int(support.setsX), int(support.setsY))
    for load in disk.loads:
      fx, fy = load.intensity
      places = self._edgeNodes(load)
      for (first, start), (second, end) in zip(places, places[1:]):
        half = (end - start) / 2
        model.addLoad(first, fx * half, fy * half)
        model.addLoad(second, fx * half, fy * half)
    return model

  def _solve(self, solver: Solver) -> None:
    """Solves the mesh and reads the stresses and reactions off."""
    result = solver.solve(self._model(), 'stresses')
    columns, rows = self.columns, self.rows
    cells = []
    answers = iter(result.response('stresses'))
    for j in range(len(rows) - 1):
      for i in range(len(columns) - 1):
        points = next(answers)
        sx, sy, sxy = (sum(points[k::3]) / 4 / _KPA for k in range(3))
        cells.append(
          CellStress(
            (columns[i] + columns[i + 1]) / 2,
            (rows[j] + rows[j + 1]) / 2, sx, sy, sxy
            )
          )
    self.__field_cells__ = (*cells,)
    self.__field_reactions__ = self._reactions(result)

  def _reactions(self, result: Result) -> tuple[tuple[float, float], ...]:
    """What each support gives the disk, each node counted with the
    first support holding it."""
    counted = set()
    reactions = []
    for support in self.disk.supports:
      rx = ry = 0.0
      for node, _ in self._edgeNodes(support):
        if node not in counted:
          counted.add(node)
          fx, fy = result.reaction(node)
          rx, ry = rx + fx, ry + fy
      reactions.append((rx, ry))
    return (*reactions,)


def _determinant(m: list[list[float]]) -> float:
  """The determinant of the 3 x 3 matrix 'm'."""
  return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
          - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
          + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
