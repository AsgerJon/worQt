"""
Lattice is the section through a cylinder's axis cut into Voronoi cells,
rigid bodies held together by springs across the faces they share.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
import torch
from scipy.spatial import Voronoi, cKDTree
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import MissingVariable

from ._cylinder import Cylinder
from ._lattice_base import LatticeBase
from ._phase_num import PhaseNum

_REAL, _BOTTOM, _TOP, _LEFT, _RIGHT, _CORNER = 0, 1, 2, 3, 4, 5
_STONE = PhaseNum.STONE.index
_MORTAR = PhaseNum.MORTAR.index
_BOND = PhaseNum.BOND.index
_PLATEN = PhaseNum.PLATEN.index


def _cross(one: torch.Tensor, two: torch.Tensor) -> torch.Tensor:
  """The cross products of rows of plane vectors."""
  return one[:, 0] * two[:, 1] - one[:, 1] * two[:, 0]


def polygonArea(polygon: torch.Tensor) -> float:
  """The 'polygonArea' function returns the area of a polygon, its
  corners counter-clockwise."""
  x, y = polygon[:, 0], polygon[:, 1]
  turns = x * torch.roll(y, -1, 0) - torch.roll(x, -1, 0) * y
  return 0.5 * turns.sum().item()


class Lattice(LatticeBase):
  """
  Lattice is a section, 'width' by 'height' in mm, x from the axis and y
  up from the bottom, with the 'stones' it cuts, convex polygons, their
  corners counter-clockwise: nodes placed at
  random, never nearer than the 'spacing', and the section cut into
  their Voronoi cells, mirrored at its edges so the cells end exactly on
  them. Each cell is a rigid body, moving along x and y and turning;
  each pair of neighbours is held together across the face they share,
  at the face's centre, by a normal and a shear spring, as stiff as the
  material between their nodes, over the distance between them: stone,
  mortar, or, where the line between them crosses a stone's edge, the
  bond, as stiff as the stone and the mortar along it in series. Stones
  smaller than the spacing are left to the mortar. The cells along the
  bottom and the top bear on the platens, each a rigid body too, by
  springs of the cell's material over the distance to the edge.

  Of Poisson's ratio nought, the shear spring as stiff as the normal
  one, the lattice is exactly uniform: under a uniform strain each face
  carries the stress of the material at that strain, and every cell is
  in equilibrium. 'elasticForces' are the springs' forces at given
  displacements, three to a cell and to a platen, the bottom platen's
  after the cells and the top's last, and 'elasticModulus' the stress
  over the strain the lattice takes between its platens, worked out
  exactly.

  The springs are kept as rows: 'first' and 'second', the nodes they
  join, a platen's being after the cells, the bottom's then the top's;
  'centres', 'lengths' and 'facetEnds' of their faces; 'distances' and
  'normals', from the first node to the second; 'phases', of 'PhaseNum',
  by index; and 'moduli'. 'normalRows' and 'shearRows' are how a spring
  stretches and slides as the six movements, 'dofs', of its two bodies
  go.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_trial_density__ = 4.0  # points tried per spacing squared
  __fallback_mirror_reach__ = 4.0  # spacings in from an edge mirrored
  __fallback_least_stone__ = 1.0  # spacings across a stone shown
  __fallback_chunk_size__ = 4096  # springs set against the stones at once

  #  Private Variables
  __lattice_width__: float | None = None
  __lattice_height__: float | None = None
  __lattice_spacing__: float | None = None
  __lattice_seed__: int | None = None
  __lattice_stones__: tuple[torch.Tensor, ...] | None = None
  __stone_planes__: torch.Tensor | None = None
  __stone_bounds__: torch.Tensor | None = None

  #  Virtual Variables
  width: Field[float] = Field()
  height: Field[float] = Field()
  spacing: Field[float] = Field()
  seed: Field[int] = Field()
  stones: Field[tuple[torch.Tensor, ...]] = Field()
  stoneFraction: Field[float] = Field()
  platenPoints: Field[torch.Tensor] = Field()
  areas: Field[torch.Tensor] = Field()
  lengths: Field[torch.Tensor] = Field()
  facetEnds: Field[torch.Tensor] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @width.GET
  def _getWidth(self, ) -> float:
    """The 'width' getter returns the width of the section, in mm."""
    if self.__lattice_width__ is None:
      raise MissingVariable(self, '__lattice_width__', float)
    return self.__lattice_width__

  @height.GET
  def _getHeight(self, ) -> float:
    """The 'height' getter returns the height of the section, in mm."""
    if self.__lattice_height__ is None:
      raise MissingVariable(self, '__lattice_height__', float)
    return self.__lattice_height__

  @spacing.GET
  def _getSpacing(self, ) -> float:
    """The 'spacing' getter returns the least distance between nodes."""
    if self.__lattice_spacing__ is None:
      raise MissingVariable(self, '__lattice_spacing__', float)
    return self.__lattice_spacing__

  @seed.GET
  def _getSeed(self, ) -> int:
    """The 'seed' getter returns the seed the nodes are placed by."""
    if self.__lattice_seed__ is None:
      raise MissingVariable(self, '__lattice_seed__', int)
    return self.__lattice_seed__

  @stones.GET
  def _getStones(self, ) -> tuple[torch.Tensor, ...]:
    """The 'stones' getter returns the stones the lattice shows, each a
    convex polygon, a row of x and y to a corner: those as large as a
    circle a spacing across, or larger."""
    if self.__lattice_stones__ is None:
      raise MissingVariable(self, '__lattice_stones__', tuple)
    return self.__lattice_stones__

  @stoneFraction.GET
  def _getStoneFraction(self, ) -> float:
    """The 'stoneFraction' getter returns the share of the section the
    stones shown cover."""
    covered = sum(polygonArea(polygon) for polygon in self.stones)
    return covered / (self.width * self.height)

  @platenPoints.GET
  def _getPlatenPoints(self, ) -> torch.Tensor:
    """The 'platenPoints' getter returns where the platens are held,
    the middle of the bottom edge and of the top."""
    return torch.from_numpy(numpy.array([[0.0, 0.0], [0.0, self.height]]))

  @areas.GET
  def _getAreas(self, ) -> torch.Tensor:
    """The 'areas' getter returns the area of each cell, in mm²."""
    return self._part('areas')

  @lengths.GET
  def _getLengths(self, ) -> torch.Tensor:
    """The 'lengths' getter returns the length of each spring's face, in
    mm, its area on the section a millimetre thick."""
    return self._part('lengths')

  @facetEnds.GET
  def _getFacetEnds(self, ) -> torch.Tensor:
    """The 'facetEnds' getter returns the two ends of each spring's
    face."""
    return self._part('ends')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Cylinder, float)
  def __init__(self, cylinder: Cylinder, spacing: float) -> None:
    stones = cylinder.section(0.0)
    self._setLattice(cylinder.diameter, cylinder.height, stones, spacing,
                     cylinder.seed)

  @overload(float, float, tuple, float, int)
  def __init__(self, *args) -> None:
    self._setLattice(*args)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setLattice(self, width: float, height: float, stones: tuple,
                  spacing: float, seed: int, ) -> None:
    """Keeps what the lattice is of and builds it."""
    if width <= 0.0 or height <= 0.0 or spacing <= 0.0:
      raise ValueError('a lattice must be more than nought each way')
    self.__lattice_width__ = width
    self.__lattice_height__ = height
    self.__lattice_spacing__ = spacing
    self.__lattice_seed__ = seed
    least = math.pi * (self.__fallback_least_stone__ * spacing / 2) ** 2
    shown = [stone for stone in stones if polygonArea(stone) >= least]
    self.__lattice_stones__ = (*shown,)
    self.__stone_planes__, self.__stone_bounds__ = self._stonePlanes()
    self.__lattice_parts__ = self._build()

  def _stonePlanes(self, ) -> tuple[torch.Tensor, torch.Tensor]:
    """The stones as the planes bounding them, a row of nx, ny and c to
    an edge, a point p inside where n . p is less than c for every edge;
    those of a stone with fewer edges padded with planes nothing is
    outside of; and the circle about each, its centre and radius."""
    stones = self.stones
    edges = max([3, *[len(stone) for stone in stones]])
    planes = torch.zeros(len(stones), edges, 3).double()
    planes[:, :, 2] = 1.0
    bounds = torch.zeros(len(stones), 3).double()
    for index, stone in enumerate(stones):
      along = torch.roll(stone, -1, 0) - stone
      normals = torch.stack([along[:, 1], -along[:, 0]], 1)
      normals = normals / normals.norm(2, 1, True)
      planes[index, :len(stone), :2] = normals
      planes[index, :len(stone), 2] = (normals * stone).sum(1)
      middle = stone.mean(0)
      bounds[index, :2] = middle
      bounds[index, 2] = (stone - middle).norm(2, 1).max()
    return planes, bounds

  def _placeNodes(self, ) -> numpy.ndarray:
    """
    Nodes at random, never nearer than the spacing: points tried four to
    a spacing squared, and of each pair nearer than the spacing the one
    drawn the later number thinned away.
    """
    rng = numpy.random.default_rng(self.seed)
    width, height, spacing = self.width, self.height, self.spacing
    density = self.__fallback_trial_density__ / spacing ** 2
    count = rng.poisson(density * width * height)
    points = numpy.stack([
        (rng.random(count) - 0.5) * width,
        rng.random(count) * height,
    ], 1)
    pairs = cKDTree(points).query_pairs(spacing, 2.0, 0.0, 'ndarray')
    marks = rng.random(count)
    later = numpy.where(marks[pairs[:, 0]] > marks[pairs[:, 1]],
                        pairs[:, 0], pairs[:, 1])
    kept = numpy.ones(count, bool)
    kept[later] = False
    return points[kept]

  def _mirror(self, points: numpy.ndarray) -> tuple:
    """The nodes with their images across the edges near them: all the
    points, which node each is of, and across which edge."""
    half, height = self.width / 2, self.height
    reach = self.__fallback_mirror_reach__ * self.spacing
    x, y = points[:, 0], points[:, 1]
    count = len(points)
    parts = [(points, numpy.arange(count), _REAL)]
    images = (
        (_BOTTOM, y < reach, numpy.stack([x, -y], 1)),
        (_TOP, y > height - reach, numpy.stack([x, 2 * height - y], 1)),
        (_LEFT, x < reach - half, numpy.stack([-2 * half - x, y], 1)),
        (_RIGHT, x > half - reach, numpy.stack([2 * half - x, y], 1)),
    )
    for kind, near, image in images:
      parts.append((image[near], numpy.nonzero(near)[0], kind))
    for side in (-half, half):
      for edge in (0.0, height):
        near = (abs(x - side) < reach) & (abs(y - edge) < reach)
        image = numpy.stack([2 * side - x, 2 * edge - y], 1)[near]
        parts.append((image, numpy.nonzero(near)[0], _CORNER))
    every = numpy.concatenate([part[0] for part in parts])
    owner = numpy.concatenate([part[1] for part in parts])
    kinds = numpy.concatenate([
        numpy.full(len(part[1]), part[2]) for part in parts])
    return every, owner, kinds

  def _build(self, ) -> dict:
    """Builds the cells and the springs."""
    points = self._placeNodes()
    count = len(points)
    every, owner, kinds = self._mirror(points)
    diagram = Voronoi(every)
    pairs = diagram.ridge_points
    ends = numpy.array(diagram.ridge_vertices)
    corners = diagram.vertices
    one, two = pairs[:, 0], pairs[:, 1]
    inner = (kinds[one] == _REAL) & (kinds[two] == _REAL)
    oneReal = kinds[one] == _REAL
    node = numpy.where(oneReal, one, two)
    image = numpy.where(oneReal, two, one)
    own = (kinds[node] == _REAL) & (owner[image] == node) & ~inner
    links = own & ((kinds[image] == _BOTTOM) | (kinds[image] == _TOP))
    sides = own & ((kinds[image] == _LEFT) | (kinds[image] == _RIGHT))
    kept = inner | links | sides
    if (ends[kept] < 0).any():
      raise ValueError('the cells do not close')
    nodes = torch.from_numpy(numpy.ascontiguousarray(points))
    faces = torch.from_numpy(numpy.stack([
        corners[ends[:, 0]], corners[ends[:, 1]]], 1))
    parts = {'nodes': nodes}
    parts.update(self._springs(
        nodes, faces, torch.from_numpy(one[inner]),
        torch.from_numpy(two[inner]), torch.from_numpy(node[links]),
        torch.from_numpy(kinds[image[links]]), inner, links))
    parts.update(self._cellAreas(
        parts, torch.from_numpy(node[sides]), faces[sides]))
    return parts

  def _springs(self, nodes: torch.Tensor, faces: torch.Tensor,
               one: torch.Tensor, two: torch.Tensor, bearing: torch.Tensor,
               edges: torch.Tensor, inner: numpy.ndarray,
               links: numpy.ndarray, ) -> dict:
    """The springs between neighbours, then those on the platens."""
    count = len(nodes)
    height = self.height
    innerEnds, linkEnds = faces[inner], faces[links]
    along = nodes[two] - nodes[one]
    reach = torch.sqrt((along ** 2).sum(1))
    onTop = edges == _TOP
    edgeY = onTop.double() * height
    linkReach = (nodes[bearing, 1] - edgeY).abs()
    upward = onTop.double() * 2.0 - 1.0
    linkNormals = torch.stack([torch.zeros_like(upward), upward], 1)
    first = torch.cat([one, bearing])
    second = torch.cat([two, torch.where(onTop, count + 1, count)])
    ends = torch.cat([innerEnds, linkEnds])
    centres = ends.mean(1)
    lengths = torch.sqrt(((ends[:, 1] - ends[:, 0]) ** 2).sum(1))
    distances = torch.cat([reach, linkReach])
    normals = torch.cat([along / reach[:, None], linkNormals])
    phases, shares = self._materials(nodes, one, two, bearing)
    places = torch.cat([nodes, self.platenPoints])
    parts = {
        'first': first, 'second': second, 'ends': ends, 'centres': centres,
        'lengths': lengths, 'faceAreas': lengths, 'distances': distances,
        'normals': normals, 'phases': phases, 'shares': shares,
    }
    parts.update(self._rows(places, first, second, centres, normals))
    return parts

  @staticmethod
  def _rows(places: torch.Tensor, first: torch.Tensor,
            second: torch.Tensor, centres: torch.Tensor,
            normals: torch.Tensor, ) -> dict:
    """How each spring stretches and slides as its bodies move: at the
    face's centre, the second body's movement there less the first's,
    each body turning about its node."""
    tangents = torch.stack([-normals[:, 1], normals[:, 0]], 1)
    armOne = centres - places[first]
    armTwo = centres - places[second]
    rows = []
    for unit in (normals, tangents):
      rows.append(torch.stack([
          -unit[:, 0], -unit[:, 1], -_cross(armOne, unit),
          unit[:, 0], unit[:, 1], _cross(armTwo, unit),
      ], 1))
    base = torch.stack([3 * first, 3 * first + 1, 3 * first + 2,
                        3 * second, 3 * second + 1, 3 * second + 2], 1)
    return {'normalRows': rows[0], 'shearRows': rows[1][:, None],
            'dofs': base}

  def _materials(self, nodes: torch.Tensor, one: torch.Tensor,
                 two: torch.Tensor, bearing: torch.Tensor, ) -> tuple:
    """What each spring is of, stone, mortar or the bond, and how much
    of its reach is in stone; on a platen, all of it where the cell's
    node is in a stone."""
    inStone, oneStone, crossing = self._crossings(nodes[one], nodes[two])
    phases = torch.where(oneStone, _STONE,
                         torch.where(crossing, _BOND, _MORTAR))
    shares = torch.where(oneStone, 1.0, torch.clamp(inStone, 0.0, 1.0))
    held = self._insideStones(nodes[bearing]).double()
    linkPhases = torch.full_like(bearing, _PLATEN)
    return (torch.cat([phases, linkPhases]),
            torch.cat([shares.double(), held]))

  def _insideStones(self, points: torch.Tensor) -> torch.Tensor:
    """Which 'points' are inside a stone."""
    out = torch.zeros(len(points)).bool()
    if not self.stones or not len(points):
      return out
    bounds = self.__stone_bounds__
    gaps = torch.cdist(points, bounds[:, :2]) - bounds[:, 2]
    pairs = torch.nonzero(gaps < 0)
    point, stone = pairs[:, 0], pairs[:, 1]
    planes = self.__stone_planes__[stone]
    room = planes[..., 2] - (planes[..., :2] * points[point, None]).sum(2)
    inside = (room > 0).all(1)
    out[point[inside]] = True
    return out

  def _crossings(self, starts: torch.Tensor, stops: torch.Tensor) -> tuple:
    """
    For each line from 'starts' to 'stops': the share of it inside
    stones, whether both its ends are in one stone, and whether it
    crosses a stone's edge. Each line is clipped by the planes of every
    stone whose circle it comes near, a chunk of lines at a time.
    """
    count = len(starts)
    shares = torch.zeros(count).double()
    ones = torch.zeros(count).bool()
    crossings = torch.zeros(count).bool()
    if not self.stones:
      return shares, ones, crossings
    bounds = self.__stone_bounds__
    size = self.__fallback_chunk_size__
    for first in range(0, count, size):
      tail, head = starts[first:first + size], stops[first:first + size]
      middle, along = (tail + head) / 2, head - tail
      reach = along.norm(2, 1) / 2
      gaps = torch.cdist(middle, bounds[:, :2]) - bounds[:, 2]
      pairs = torch.nonzero(gaps < reach[:, None])
      if not len(pairs):
        continue
      line, stone = pairs[:, 0], pairs[:, 1]
      share, both = self._clip(tail[line], along[line], stone)
      which = line + first
      shares.index_add_(0, which, share)
      ones[which[both]] = True
      crossings[which[(share > 0) & ~both]] = True
    return shares, ones, crossings & ~ones

  def _clip(self, tails: torch.Tensor, alongs: torch.Tensor,
            stones: torch.Tensor, ) -> tuple:
    """The share of each line inside its stone, and whether both its ends
    are in it: the line clipped by each plane of the stone, entering
    where it crosses a plane inwards and leaving where it crosses one
    outwards."""
    planes = self.__stone_planes__[stones]
    normals, limits = planes[..., :2], planes[..., 2]
    room = limits - (normals * tails[:, None]).sum(2)
    rate = (normals * alongs[:, None]).sum(2)
    cuts = room / rate
    inwards = torch.where(rate < -1e-15, cuts, -math.inf).amax(1)
    outwards = torch.where(rate > 1e-15, cuts, math.inf).amin(1)
    never = ((rate.abs() <= 1e-15) & (room < 0)).any(1)
    enter = torch.clamp(inwards, 0.0)
    leave = torch.clamp(outwards, None, 1.0)
    share = torch.where(never, 0.0, torch.clamp(leave - enter, 0.0))
    both = (room > 0).all(1) & ((room - rate) > 0).all(1)
    return share, both

  def _cellAreas(self, parts: dict, sideNodes: torch.Tensor,
                 sideFaces: torch.Tensor, ) -> dict:
    """The area of each cell, from the triangles its faces make with its
    node, and which cells end on an edge."""
    count = len(parts['nodes'])
    nodes = parts['nodes']
    first, second = parts['first'], parts['second']
    lengths, distances = parts['lengths'], parts['distances']
    linked = second >= count
    areas = torch.zeros(count).double()
    inner = ~linked
    halfInner = lengths[inner] * distances[inner] / 4
    areas.index_add_(0, first[inner], halfInner)
    areas.index_add_(0, second[inner], halfInner)
    onPlaten = lengths[linked] * distances[linked] / 2
    areas.index_add_(0, first[linked], onPlaten)
    sideLengths = torch.sqrt(
        ((sideFaces[:, 1] - sideFaces[:, 0]) ** 2).sum(1))
    sideReach = self.width / 2 - nodes[sideNodes, 0].abs()
    areas.index_add_(0, sideNodes, sideLengths * sideReach / 2)
    boundary = torch.zeros(count).bool()
    boundary[first[linked]] = True
    boundary[sideNodes] = True
    return {'areas': areas, 'boundary': boundary}
