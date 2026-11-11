"""
Cylinder is a concrete cylinder as it is cast: its stones, placed in the
mould.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._grading import Grading
from ._stone import Stone


class Cylinder(BaseObject):
  """
  Cylinder is a concrete cylinder as it is cast, 'diameter' across and
  'height' high, in mm, its axis upright along y, of an aggregate of the
  'grading' given, 'aggregateFraction' of the concrete by volume. The
  stones from the 'smallest' size modelled up, each a 'Stone' turned at
  random, are placed one by one, largest first, each where a random try
  finds it wholly inside the mould and clear of every stone placed
  before it; what is smaller is in the mortar. The same 'seed' casts the
  same cylinder.

  A stone is inside the mould when all its corners are, the mould and
  the stone both convex. It is clear of another when a plane parts them:
  one of the faces of either, or the plane square to the line between
  their centres; where none of those does, it is taken not to be clear,
  so no two stones ever overlap. The tries are made many at once, as
  tensors.

  Only the 'slab' either side of the section through the axis is cast,
  'slabHalf' deep each way, 1.5 largest sizes or the radius: every stone
  the section can cut, and every stone that could stand in the way of
  one, is in it. 'stones' are the stones where they are and 'centres'
  their centres, z across the section; 'section' cuts them at a depth z,
  as convex polygons. A stone no try finds room for is left out and
  counted, 'skipped'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_aggregate_fraction__ = 0.70  # aggregate, of the concrete
  __fallback_smallest_stone__ = 4.0  # mm: smaller is in the mortar
  __fallback_slab_depth__ = 1.5  # largest sizes, each way of the section
  __fallback_tries__ = 64  # places tried at a time for a stone
  __fallback_rounds__ = 400  # times a stone is tried before it is left

  #  Private Variables
  __cylinder_diameter__: float | None = None
  __cylinder_height__: float | None = None
  __cylinder_grading__: Grading | None = None
  __cylinder_seed__: int | None = None
  __smallest_stone__: float | None = None
  __cast_stones__: tuple[Stone, ...] | None = None
  __cast_centres__: torch.Tensor | None = None
  __skipped_stones__: int = 0

  #  Virtual Variables
  diameter: Field[float] = Field()
  height: Field[float] = Field()
  radius: Field[float] = Field()
  grading: Field[Grading] = Field()
  seed: Field[int] = Field()
  smallest: Field[float] = Field()
  aggregateFraction: Field[float] = Field()
  slabHalf: Field[float] = Field()
  slabVolume: Field[float] = Field()
  stones: Field[tuple[Stone, ...]] = Field()
  centres: Field[torch.Tensor] = Field()
  skipped: Field[int] = Field()
  stoneVolume: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @diameter.GET
  def _getDiameter(self, ) -> float:
    """The 'diameter' getter returns the diameter, in mm."""
    if self.__cylinder_diameter__ is None:
      raise MissingVariable(self, '__cylinder_diameter__', float)
    return self.__cylinder_diameter__

  @height.GET
  def _getHeight(self, ) -> float:
    """The 'height' getter returns the height, in mm."""
    if self.__cylinder_height__ is None:
      raise MissingVariable(self, '__cylinder_height__', float)
    return self.__cylinder_height__

  @radius.GET
  def _getRadius(self, ) -> float:
    """The 'radius' getter returns half the diameter."""
    return self.diameter / 2

  @grading.GET
  def _getGrading(self, ) -> Grading:
    """The 'grading' getter returns the grading of the aggregate."""
    if self.__cylinder_grading__ is None:
      raise MissingVariable(self, '__cylinder_grading__', Grading)
    return self.__cylinder_grading__

  @seed.GET
  def _getSeed(self, ) -> int:
    """The 'seed' getter returns the seed the stones are placed by."""
    if self.__cylinder_seed__ is None:
      raise MissingVariable(self, '__cylinder_seed__', int)
    return self.__cylinder_seed__

  @smallest.GET
  def _getSmallest(self, ) -> float:
    """The 'smallest' getter returns the smallest stone modelled, in
    mm."""
    if self.__smallest_stone__ is None:
      raise MissingVariable(self, '__smallest_stone__', float)
    return self.__smallest_stone__

  @aggregateFraction.GET
  def _getAggregateFraction(self, ) -> float:
    """The 'aggregateFraction' getter returns the share of the concrete,
    by volume, that is aggregate."""
    return self.__fallback_aggregate_fraction__

  @slabHalf.GET
  def _getSlabHalf(self, ) -> float:
    """The 'slabHalf' getter returns how deep the slab is cast each way
    of the section, in mm."""
    depth = self.__fallback_slab_depth__ * self.grading.maxSize
    return min(depth, self.radius)

  @slabVolume.GET
  def _getSlabVolume(self, ) -> float:
    """The 'slabVolume' getter returns the volume of the slab, in mm³:
    the cylinder within 'slabHalf' of the section."""
    half, radius = self.slabHalf, self.radius
    if half >= radius:
      return math.pi * radius ** 2 * self.height
    chord = half * math.sqrt(radius ** 2 - half ** 2)
    area = 2 * (chord + radius ** 2 * math.asin(half / radius))
    return area * self.height

  @stones.GET
  def _getStones(self, ) -> tuple[Stone, ...]:
    """The 'stones' getter returns the stones where they are, cast once,
    when first asked for."""
    if self.__cast_stones__ is None:
      self.__cast_stones__ = self._cast()
      centres = [stone.centre for stone in self.__cast_stones__]
      if centres:
        self.__cast_centres__ = torch.stack(centres)
      else:
        self.__cast_centres__ = torch.zeros(0, 3).double()
    return self.__cast_stones__

  @centres.GET
  def _getCentres(self, ) -> torch.Tensor:
    """The 'centres' getter returns the centres of the stones, a row of
    x, y and z each, in mm."""
    _ = self.stones
    return self.__cast_centres__

  @skipped.GET
  def _getSkipped(self, ) -> int:
    """The 'skipped' getter returns how many stones found no room."""
    _ = self.stones
    return self.__skipped_stones__

  @stoneVolume.GET
  def _getStoneVolume(self, ) -> float:
    """The 'stoneVolume' getter returns the volume of the stones, in
    mm³."""
    return sum(stone.volume for stone in self.stones)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(float, float, Grading, float, int)
  def __init__(self, *args) -> None:
    self._setCast(*args)

  @overload(float, float, Grading, int)
  def __init__(self, diameter: float, height: float, grading: Grading,
               seed: int, ) -> None:
    self._setCast(diameter, height, grading,
                  self.__fallback_smallest_stone__, seed)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def section(self, depth: float) -> tuple[torch.Tensor, ...]:
    """The 'section' method returns the polygons the plane at 'depth', z,
    cuts from the stones, each a row of x and y to a corner, the corners
    counter-clockwise."""
    stones, centres = self.stones, self.centres
    if not stones:
      return ()
    outer = torch.tensor([stone.outer for stone in stones]).double()
    near = torch.nonzero((centres[:, 2] - depth).abs() < outer)
    out = []
    for index in near[:, 0].tolist():
      polygon = stones[index].section(depth)
      if polygon is not None:
        out.append(polygon)
    return (*out,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setCast(self, diameter: float, height: float, grading: Grading,
               smallest: float, seed: int, ) -> None:
    """Keeps what the cylinder is cast of, once it is seen to make
    one."""
    if diameter <= 0.0 or height <= 0.0:
      raise ValueError('a cylinder must be more than nought each way')
    if smallest <= 0.0:
      raise ValueError('the smallest stone must be more than nought')
    self.__cylinder_diameter__ = diameter
    self.__cylinder_height__ = height
    self.__cylinder_grading__ = grading
    self.__smallest_stone__ = smallest
    self.__cylinder_seed__ = seed

  def _cast(self, ) -> tuple[Stone, ...]:
    """Draws the stones and places them, largest first."""
    rng = numpy.random.default_rng(self.seed)
    volume = self.aggregateFraction * self.slabVolume
    sizes = self.grading.sample(rng, volume, self.smallest).tolist()
    shapes = [Stone.random(rng, size) for size in sizes]
    placed = self._packing(shapes)
    out, skipped, count = [], 0, 0
    for shape in shapes:
      spot = self._findRoom(rng, shape, placed, count)
      if spot is None:
        skipped += 1
        continue
      stone = shape.moved(spot)
      self._keep(placed, count, stone)
      out.append(stone)
      count += 1
    self.__skipped_stones__ = skipped
    return (*out,)

  @staticmethod
  def _padded(rows: torch.Tensor, size: int) -> torch.Tensor:
    """'rows' made 'size' long by repeating the first; a repeated corner
    or face changes no stone."""
    extra = size - len(rows)
    return torch.cat([rows, rows[:1].expand(extra, -1)]) if extra else rows

  def _packing(self, shapes: list[Stone]) -> dict:
    """Room for the stones placed, as tensors, the corners and the faces
    of each made as many as the most any has."""
    count = len(shapes)
    corners = max([1, *[len(shape.vertices) for shape in shapes]])
    faces = max([1, *[len(shape.normals) for shape in shapes]])
    return {
        'centres': torch.zeros(count, 3).double(),
        'vertices': torch.zeros(count, corners, 3).double(),
        'normals': torch.zeros(count, faces, 3).double(),
        'outer': torch.zeros(count).double(),
        'inner': torch.zeros(count).double(),
    }

  def _keep(self, placed: dict, index: int, stone: Stone) -> None:
    """Keeps 'stone' among those placed."""
    placed['centres'][index] = stone.centre
    corners = placed['vertices'].shape[1]
    placed['vertices'][index] = self._padded(stone.vertices, corners)
    faces = placed['normals'].shape[1]
    placed['normals'][index] = self._padded(stone.normals, faces)
    placed['outer'][index] = stone.outer
    placed['inner'][index] = stone.inner

  def _findRoom(self, rng: numpy.random.Generator, stone: Stone,
                placed: dict, count: int, ) -> torch.Tensor | None:
    """A centre for 'stone' wholly inside the mould and clear of the
    'count' stones placed, or 'None' if no try finds one."""
    radius, height, half = self.radius, self.height, self.slabHalf
    inner = stone.inner
    spans = torch.tensor([2 * (radius - inner), height - 2 * inner,
                          2 * half]).double()
    starts = torch.tensor([inner - radius, inner, -half]).double()
    tries = self.__fallback_tries__
    for _ in range(self.__fallback_rounds__):
      spots = torch.from_numpy(rng.random((tries, 3))) * spans + starts
      spots = spots[self._inMould(stone, spots)]
      if not len(spots):
        continue
      if count:
        spots = spots[self._clear(stone, spots, placed, count)]
      if len(spots):
        return spots[0]
    return None

  def _inMould(self, stone: Stone, spots: torch.Tensor) -> torch.Tensor:
    """Which 'spots' have every corner of 'stone' inside the mould."""
    corners = spots[:, None, :] + stone.vertices
    x, y, z = corners[..., 0], corners[..., 1], corners[..., 2]
    inside = (x ** 2 + z ** 2 <= self.radius ** 2) & (y >= 0.0)
    return (inside & (y <= self.height)).all(1)

  @staticmethod
  def _clear(stone: Stone, spots: torch.Tensor, placed: dict,
             count: int, ) -> torch.Tensor:
    """
    Which 'spots' leave 'stone' clear of the 'count' stones placed: far
    enough from each, or parted from it by a face of either or by the
    plane square to the line between their centres. Two stones whose
    inner spheres meet overlap.
    """
    centres = placed['centres'][:count]
    gaps = torch.cdist(spots, centres)
    hit = (gaps < stone.inner + placed['inner'][:count]).any(1)
    near = gaps < stone.outer + placed['outer'][:count]
    near &= ~hit[:, None]
    pairs = torch.nonzero(near)
    tried, other = pairs[:, 0], pairs[:, 1]
    if not len(tried):
      return ~hit
    between = centres[other] - spots[tried]
    unit = between / between.norm(2, 1, True)
    axes = torch.cat([stone.normals.expand(len(tried), -1, -1),
                      placed['normals'][other], unit[:, None]], 1)
    mine = axes @ stone.vertices.T
    theirs = torch.bmm(axes, placed['vertices'][other].transpose(1, 2))
    shift = (axes * between[:, None]).sum(2)
    parted = (mine.amax(2) <= theirs.amin(2) + shift)
    parted |= (theirs.amax(2) + shift <= mine.amin(2))
    stuck = (~parted.any(1)).double()
    blocked = torch.zeros(len(spots)).double().index_add_(0, tried, stuck)
    return ~hit & (blocked == 0)


class WholeCylinder(Cylinder):
  """
  WholeCylinder is a 'Cylinder' cast through and through: its slab as
  deep as the cylinder is round, so all of it is there to be seen through
  clear paste. Its section through the axis is cut the same way.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_slab_depth__ = math.inf  # the slab reaches the mould
