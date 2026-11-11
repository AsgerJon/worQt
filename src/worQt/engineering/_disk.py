"""
Disk is a rectangular concrete disk, loaded in its own plane.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from ._edge_num import EdgeNum
from ._edge_stretch import EdgeStretch
from ._load import Load
from ._numbers import formatNumber, parseNumber, checkPositive
from ._rebar import Rebar
from ._support import Support

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Self

_FIT_TOLERANCE = 1e-9  # metres a stretch may overshoot its edge by
_MATERIALS = ('fc', 'fy', 'E')  # as the disk line names them, in order


class Disk(BaseObject):
  """
  Disk is a rectangular concrete disk ('skive'), loaded in its own
  plane. It is thin: its 'length' along x and its 'height' along y are
  each at least four times its 'thickness', all in metres, as EN
  1992-1-1 9.6.1 asks of a wall. Its origin is its bottom left corner,
  with y upwards.

  Its materials are 'fc', the compressive strength of its concrete, and
  'fy' and 'E', the yield strength and the modulus of its reinforcement,
  all in MPa: 30, 800 and 200000 when none are given.

  Supports and loads act over stretches of its edges, each assigned in
  turn by 'addSupport' and 'addLoad', and each must fit its edge.

  'str()' of a disk is its text, which a disk reads back: the disk line,
  then its supports, then its loads, one a line:

    disk 6 x 2.7 x 0.3 fc 30 fy 800 E 200000
    support bottom 0 0.3 y
    support bottom 5.7 6 x y
    load top 0 6 F 0 -1200

  The disk line may name its materials in any order, or leave any of
  them out to take its default.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_fc__ = 30.0  # MPa
  __fallback_fy__ = 800.0  # MPa
  __fallback_e_modulus__ = 200000.0  # MPa
  __fallback_thinness__ = 4.0  # least length or height, in thicknesses

  #  Private Variables
  __disk_dims__: tuple[float, float, float] | None = None
  __disk_materials__: tuple[float, float, float] | None = None
  __disk_supports__: list[Support] | None = None
  __disk_loads__: list[Load] | None = None
  __disk_rebars__: list[Rebar] | None = None

  #  Virtual Variables
  length: Field[float] = Field()
  height: Field[float] = Field()
  thickness: Field[float] = Field()
  fc: Field[float] = Field()
  fy: Field[float] = Field()
  E: Field[float] = Field()
  leastSide: Field[float] = Field()
  greatestThickness: Field[float] = Field()
  supports: Field[tuple[Support, ...]] = Field()
  loads: Field[tuple[Load, ...]] = Field()
  rebars: Field[tuple[Rebar, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getDims(self, ) -> tuple[float, float, float]:
    if self.__disk_dims__ is None:
      raise MissingVariable(self, '__disk_dims__', tuple)
    return self.__disk_dims__

  def _getMaterials(self, ) -> tuple[float, float, float]:
    if self.__disk_materials__ is None:
      raise MissingVariable(self, '__disk_materials__', tuple)
    return self.__disk_materials__

  def _supportList(self, ) -> list[Support]:
    if self.__disk_supports__ is None:
      self.__disk_supports__ = []
    return self.__disk_supports__

  def _loadList(self, ) -> list[Load]:
    if self.__disk_loads__ is None:
      self.__disk_loads__ = []
    return self.__disk_loads__

  def _rebarList(self, ) -> list[Rebar]:
    if self.__disk_rebars__ is None:
      self.__disk_rebars__ = []
    return self.__disk_rebars__

  @rebars.GET
  def _getRebars(self, ) -> tuple[Rebar, ...]:
    """The 'rebars' getter returns the reinforcement, in the order it was
    assigned."""
    return (*self._rebarList(),)

  @length.GET
  def _getLength(self, ) -> float:
    """The 'length' getter returns the length along x, in metres."""
    return self._getDims()[0]

  @height.GET
  def _getHeight(self, ) -> float:
    """The 'height' getter returns the height along y, in metres."""
    return self._getDims()[1]

  @thickness.GET
  def _getThickness(self, ) -> float:
    """The 'thickness' getter returns the thickness, in metres."""
    return self._getDims()[2]

  @fc.GET
  def _getFc(self, ) -> float:
    """The 'fc' getter returns the compressive strength of the concrete,
    in MPa."""
    return self._getMaterials()[0]

  @fy.GET
  def _getFy(self, ) -> float:
    """The 'fy' getter returns the yield strength of the reinforcement,
    in MPa."""
    return self._getMaterials()[1]

  @E.GET
  def _getE(self, ) -> float:
    """The 'E' getter returns the modulus of the reinforcement, in
    MPa."""
    return self._getMaterials()[2]

  @leastSide.GET
  def _getLeastSide(self, ) -> float:
    """The 'leastSide' getter returns the least the length or the height
    may be: four thicknesses."""
    return self.__fallback_thinness__ * self.thickness

  @greatestThickness.GET
  def _getGreatestThickness(self, ) -> float:
    """The 'greatestThickness' getter returns the most the thickness may
    be: a quarter of the lesser of the length and the height."""
    return min(self.length, self.height) / self.__fallback_thinness__

  @supports.GET
  def _getSupports(self, ) -> tuple[Support, ...]:
    """The 'supports' getter returns the supports, in the order they
    were assigned."""
    return (*self._supportList(),)

  @loads.GET
  def _getLoads(self, ) -> tuple[Load, ...]:
    """The 'loads' getter returns the loads, in the order they were
    assigned."""
    return (*self._loadList(),)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    """The disk's text: the disk line, its supports, then its loads."""
    dims = (formatNumber(dim) for dim in self._getDims())
    head = 'disk %s x %s x %s' % (*dims,)
    for name, value in zip(_MATERIALS, self._getMaterials()):
      head += ' %s %s' % (name, formatNumber(value))
    lines = [head, *(str(support) for support in self.supports)]
    lines += [str(load) for load in self.loads]
    lines += [str(rebar) for rebar in self.rebars]
    return '\n'.join(lines)

  def __repr__(self, ) -> str:
    return """%s('''%s''')""" % (type(self).__name__, str(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self._build(other._getDims(), other._getMaterials())
    for support in other.supports:
      self.addSupport(support)
    for load in other.loads:
      self.addLoad(load)
    for rebar in other.rebars:
      self.addRebar(rebar)

  @overload(float, float, float, float, float, float)
  def __init__(
      self, length: float, height: float, thickness: float, fc: float,
      fy: float, E: float,
  ) -> None:
    self._build((length, height, thickness), (fc, fy, E))

  @overload(float, float, float)
  def __init__(self, length: float, height: float, thickness: float) -> None:
    self._build((length, height, thickness), self._defaultMaterials())

  @overload(str)
  def __init__(self, text: str) -> None:
    lines = enumerate(str.splitlines(text), 1)
    numbered = [(n, line) for n, line in lines if str.strip(line)]
    if not numbered:
      raise ValueError("""a disk's text starts with its disk line""")
    (number, head), *rest = numbered
    try:
      self._readHead(str.split(head))
    except ValueError as exception:
      message = """line %d: %s""" % (number, exception)
      raise ValueError(message) from exception
    for number, line in rest:
      self._readLine(number, line)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _defaultMaterials(self, ) -> tuple[float, float, float]:
    """The materials of a disk given none: fc, fy and E."""
    return (
      self.__fallback_fc__, self.__fallback_fy__,
      self.__fallback_e_modulus__
    )

  def _build(self, dims: tuple, materials: tuple) -> None:
    """Sets the dimensions and the materials, each checked."""
    names = ('length', 'height', 'thickness')
    length, height, thickness = (
      checkPositive(name, value) for name, value in zip(names, dims)
    )
    self._checkThin(length, height, thickness)
    self.__disk_dims__ = (length, height, thickness)
    self.__disk_materials__ = tuple(
        checkPositive(name, value)
        for name, value in zip(_MATERIALS, materials)
    )

  def _checkThin(
      self, length: float, height: float,
      thickness: float
      ) -> None:
    """Refuses a disk whose length or height is less than four of its
    thicknesses."""
    thinness = self.__fallback_thinness__
    if min(length, height) >= thinness * thickness * (1 - 1e-9):
      return
    dims = ' x '.join(formatNumber(v) for v in (length, height, thickness))
    infoSpec = ("""a disk's length and height are each at least %s """
                """times its thickness, which %s is not""")
    raise ValueError(infoSpec % (formatNumber(thinness), dims))

  def _readHead(self, words: list[str]) -> None:
    """Reads the words of the disk line: 'disk L x H x t', then any of
    'fc FC', 'fy FY' and 'E E'."""
    if len(words) < 6 or words[0] != 'disk' or words[2:5:2] != ['x'] * 2:
      infoSpec = ("""expected 'disk L x H x t', then any of 'fc FC', """
                  """'fy FY' and 'E E', not '%s'""")
      raise ValueError(infoSpec % ' '.join(words))
    dims = (
      parseNumber(words[1], 'length'),
      parseNumber(words[3], 'height'),
      parseNumber(words[5], 'thickness'),
    )
    self._build(dims, self._readMaterials(words[6:]))

  def _readMaterials(self, words: list[str]) -> tuple[float, float, float]:
    """Reads the materials named after the dimensions, taking the default
    for any left out."""
    if len(words) % 2:
      infoSpec = """each material is a name and a value: '%s'"""
      raise ValueError(infoSpec % ' '.join(words))
    values = {}
    for name, word in zip(words[::2], words[1::2]):
      if name not in _MATERIALS:
        infoSpec = """a disk's materials are fc, fy and E, not '%s'"""
        raise ValueError(infoSpec % name)
      if name in values:
        raise ValueError("""'%s' is given twice""" % name)
      values[name] = parseNumber(word, name)
    defaults = dict(zip(_MATERIALS, self._defaultMaterials()))
    return tuple(values.get(name, defaults[name]) for name in _MATERIALS)

  def _readLine(self, number: int, line: str) -> None:
    """Reads a line after the disk line: a support or a load."""
    keyword = str.split(line)[0]
    try:
      if keyword == 'support':
        return self.addSupport(Support(line))
      if keyword == 'load':
        return self.addLoad(Load(line))
      if keyword == 'rebar':
        return self.addRebar(Rebar(line))
    except ValueError as exception:
      message = """line %d: %s""" % (number, exception)
      raise ValueError(message) from exception
    if keyword == 'disk':
      infoSpec = """line %d: a disk's text has one disk line, its first"""
      raise ValueError(infoSpec % number)
    infoSpec = """line %d: expected a support, a load or a rebar, not '%s'"""
    raise ValueError(infoSpec % (number, line))

  def _checkFits(self, stretch: EdgeStretch) -> None:
    """Refuses a stretch that runs past the end of its edge."""
    edgeLength = self.edgeLength(stretch.edge)
    if stretch.end <= edgeLength + _FIT_TOLERANCE:
      return
    infoSpec = """the %s edge is %s m long; '%s' runs past it"""
    edge, length = stretch.edge.value, formatNumber(edgeLength)
    raise ValueError(infoSpec % (edge, length, stretch))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def edgeLength(self, edge: EdgeNum) -> float:
    """The 'edgeLength' method returns how long 'edge' is: the length for
    the bottom and the top, the height for the left and the right."""
    return self.length if edge.horizontal else self.height

  def pointAt(self, edge: EdgeNum, position: float) -> tuple[float, float]:
    """The 'pointAt' method returns the point at 'position' along 'edge',
    counted from the left on the bottom and the top, and from the bottom
    on the left and the right."""
    if edge is EdgeNum.BOTTOM:
      return float(position), 0.0
    if edge is EdgeNum.TOP:
      return float(position), self.height
    if edge is EdgeNum.LEFT:
      return 0.0, float(position)
    return self.length, float(position)

  def addSupport(self, support: Support) -> None:
    """The 'addSupport' method assigns 'support' to the disk, refusing
    one that does not fit its edge."""
    if not isinstance(support, Support):
      raise TypeException('support', support, Support)
    self._checkFits(support)
    self._supportList().append(support)

  def addLoad(self, load: Load) -> None:
    """The 'addLoad' method assigns 'load' to the disk, refusing one that
    does not fit its edge."""
    if not isinstance(load, Load):
      raise TypeException('load', load, Load)
    self._checkFits(load)
    self._loadList().append(load)

  def replaceSupport(self, index: int, support: Support) -> None:
    """The 'replaceSupport' method puts 'support' in the place of the
    support at 'index', refusing one that does not fit its edge."""
    if not isinstance(support, Support):
      raise TypeException('support', support, Support)
    supports = self._supportList()
    if not -len(supports) <= index < len(supports):
      raise IndexError("""no support at %d""" % index)
    self._checkFits(support)
    supports[index] = support

  def removeSupport(self, index: int) -> None:
    """The 'removeSupport' method removes the support at 'index'."""
    supports = self._supportList()
    if not -len(supports) <= index < len(supports):
      raise IndexError("""no support at %d""" % index)
    del supports[index]

  def replaceLoad(self, index: int, load: Load) -> None:
    """The 'replaceLoad' method puts 'load' in the place of the load at
    'index', refusing one that does not fit its edge."""
    if not isinstance(load, Load):
      raise TypeException('load', load, Load)
    loads = self._loadList()
    if not -len(loads) <= index < len(loads):
      raise IndexError("""no load at %d""" % index)
    self._checkFits(load)
    loads[index] = load

  def removeLoad(self, index: int) -> None:
    """The 'removeLoad' method removes the load at 'index'."""
    loads = self._loadList()
    if not -len(loads) <= index < len(loads):
      raise IndexError("""no load at %d""" % index)
    del loads[index]

  def supportRoom(self, index: int) -> tuple[float, float]:
    """The 'supportRoom' method returns the stretch of its edge the
    support at 'index' may move in: up to its neighbours on that edge, or
    the ends of the edge."""
    support = self.supports[index]
    low, high = 0.0, self.edgeLength(support.edge)
    for other, neighbour in enumerate(self.supports):
      if other == index or neighbour.edge is not support.edge:
        continue
      if neighbour.end <= support.start + _FIT_TOLERANCE:
        low = max(low, neighbour.end)
      elif neighbour.start >= support.end - _FIT_TOLERANCE:
        high = min(high, neighbour.start)
    return low, high

  def isFree(
      self, edge: EdgeNum, start: float, end: float,
      skip: int = -1
      ) -> bool:
    """The 'isFree' method tells whether no support but the one at 'skip'
    holds any of 'edge' from 'start' to 'end'."""
    for index, support in enumerate(self.supports):
      if index == skip or support.edge is not edge:
        continue
      if start < support.end - _FIT_TOLERANCE:
        if end > support.start + _FIT_TOLERANCE:
          return False
    return True

  def freeStretch(self, edge: EdgeNum, width: float) -> float | None:
    """The 'freeStretch' method returns where a new support 'width' wide
    could start on 'edge': at its start, else at its end, else at the
    first free place between, in steps of 5 cm; 'None' on a full
    edge."""
    length = self.edgeLength(edge)
    if width > length + _FIT_TOLERANCE:
      return None
    steps = int(round((length - width) / 0.05))
    starts = [0.0, length - width]
    starts += [round(step * 0.05, 9) for step in range(1, steps)]
    for start in starts:
      if self.isFree(edge, start, start + width):
        return round(start, 9)
    return None

  def withMaterials(self, fc: float, fy: float, E: float) -> Disk:
    """The 'withMaterials' method returns a new disk of the same
    dimensions, supports and loads, of the materials given."""
    disk = Disk(self.length, self.height, self.thickness, fc, fy, E)
    for support in self.supports:
      disk.addSupport(support)
    for load in self.loads:
      disk.addLoad(load)
    for rebar in self.rebars:
      disk.addRebar(rebar)
    return disk

  def addRebar(self, rebar: Rebar) -> None:
    """The 'addRebar' method assigns 'rebar' to the disk, refusing bars
    running out of it."""
    if not isinstance(rebar, Rebar):
      raise TypeException('rebar', rebar, Rebar)
    self._checkInside(rebar)
    self._rebarList().append(rebar)

  def replaceRebar(self, index: int, rebar: Rebar) -> None:
    """The 'replaceRebar' method puts 'rebar' in the place of the
    reinforcement at 'index', refusing bars running out of the disk."""
    if not isinstance(rebar, Rebar):
      raise TypeException('rebar', rebar, Rebar)
    rebars = self._rebarList()
    if not -len(rebars) <= index < len(rebars):
      raise IndexError("""no reinforcement at %d""" % index)
    self._checkInside(rebar)
    rebars[index] = rebar

  def removeRebar(self, index: int) -> None:
    """The 'removeRebar' method removes the reinforcement at 'index'."""
    rebars = self._rebarList()
    if not -len(rebars) <= index < len(rebars):
      raise IndexError("""no reinforcement at %d""" % index)
    del rebars[index]

  def _checkInside(self, rebar: Rebar) -> None:
    """Refuses bars running out of the disk."""
    tolerance = _FIT_TOLERANCE
    for x, y in (rebar.start, rebar.end):
      if -tolerance <= x <= self.length + tolerance:
        if -tolerance <= y <= self.height + tolerance:
          continue
      infoSpec = """'%s' runs out of the disk"""
      raise ValueError(infoSpec % rebar)

  def resized(self, length: float, height: float, thickness: float) -> Disk:
    """
    The 'resized' method returns a new disk of the given dimensions and
    the same materials, its supports and loads carried along the way an
    engineer would expect, with the bottom left corner fixed:

    - a stretch along the whole of an edge stretches with it;
    - a stretch at the moving end of an edge rides along with that end,
      as wide as it was;
    - every other stretch stays where it is;
    - a stretch the shrinking edge would leave behind is pushed back to
      its end, as wide as it was or as the edge is.

    A load whose stretch changes width keeps its intensity, so its force
    changes with the width.
    """
    disk = Disk(length, height, thickness, *self._getMaterials())
    for support in self.supports:
      disk.addSupport(self._carried(support, disk))
    for load in self.loads:
      disk.addLoad(self._carried(load, disk))
    for rebar in self.rebars:
      disk.addRebar(self._carriedRebar(rebar, disk))
    return disk

  def _carriedRebar(self, rebar: Rebar, resized: Disk) -> Rebar:
    """'rebar' with each end as far from its nearer edge in 'resized' as
    it was in this disk."""
    points = []
    for x, y in (rebar.start, rebar.end):
      if x > self.length / 2:
        x += resized.length - self.length
      if y > self.height / 2:
        y += resized.height - self.height
      x = min(max(x, 0.0), resized.length)
      y = min(max(y, 0.0), resized.height)
      points += [round(x, 9), round(y, 9)]
    return Rebar(*points, rebar.count, rebar.diameter)

  def _carried(self, stretch: EdgeStretch, resized: Disk) -> EdgeStretch:
    """'stretch' carried onto the edge it is on in 'resized'."""
    old = self.edgeLength(stretch.edge)
    new = resized.edgeLength(stretch.edge)
    start, end = stretch.start, stretch.end
    atNear = True if start <= _FIT_TOLERANCE else False
    atFar = True if end >= old - _FIT_TOLERANCE else False
    if atNear and atFar:
      start, end = 0.0, new
    elif atFar:
      start, end = start + new - old, new
    width = min(end - start, new)
    if end > new:
      start, end = new - width, new
    if start < 0:
      start, end = 0.0, width
    start, end = round(start, 9), round(end, 9)
    if isinstance(stretch, Support):
      return Support(stretch.edge, start, end, stretch.setsX, stretch.setsY)
    factor = (end - start) / stretch.width
    return Load(
      stretch.edge, start, end, stretch.fx * factor,
      stretch.fy * factor
      )
