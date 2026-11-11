"""
Lattice3D is a whole cylinder cut into Voronoi cells in space, rigid
bodies held together by springs across the faces they share.
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

_REAL, _BOTTOM, _TOP, _WALL = 0, 1, 2, 3
_STONE = PhaseNum.STONE.index
_MORTAR = PhaseNum.MORTAR.index
_BOND = PhaseNum.BOND.index
_PLATEN = PhaseNum.PLATEN.index


def _unit(rows: torch.Tensor) -> torch.Tensor:
  """Rows of vectors made a unit long."""
  return rows / rows.norm(2, 1, True)


def _tensor(rows: numpy.ndarray) -> torch.Tensor:
  """Rows of an array as a tensor of their own."""
  return torch.from_numpy(numpy.ascontiguousarray(rows))


class Lattice3D(LatticeBase):
  """
  Lattice3D is a whole cylinder, 'radius' and 'height' in mm, its axis
  upright along y, with its 'stones': nodes placed at random through it,
  never nearer than the 'spacing', and the cylinder cut into their
  Voronoi cells, mirrored at its ends and across its round wall so the
  cells end on them. Each cell is a rigid body, moving and turning every
  way; each pair of neighbours is held together across the face they
  share, at the face's centre, by a normal spring and two shear springs,
  as stiff as the material between their nodes over the distance between
  them: stone, mortar, or, where the line between them crosses a stone's
  face, the bond, the stone and the mortar along it in series. The cells
  along the bottom and the top bear on the platens; those along the wall
  are free. 'volumes' are the cells' volumes, and 'facetCorners' the
  corners of each spring's face, in order round it, 'facetCounts' many.

  As in the plane, of Poisson's ratio nought, the lattice is exactly
  uniform; see 'LatticeBase'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __body_moves__ = 6  # movements of a body: six in space

  #  Fallback Variables
  __fallback_trial_density__ = 3.0  # points tried per spacing cubed
  __fallback_mirror_reach__ = 3.0  # spacings in from an edge mirrored
  __fallback_chunk_size__ = 8192  # springs set against the stones at once
  __fallback_face_chunk__ = 20000  # faces ordered round at once

  #  Private Variables
  __lattice_radius__: float | None = None
  __lattice_height__: float | None = None
  __lattice_spacing__: float | None = None
  __lattice_seed__: int | None = None
  __lattice_stones__: tuple | None = None
  __stone_planes__: torch.Tensor | None = None
  __stone_bounds__: torch.Tensor | None = None

  #  Virtual Variables
  radius: Field[float] = Field()
  height: Field[float] = Field()
  spacing: Field[float] = Field()
  seed: Field[int] = Field()
  stones: Field[tuple] = Field()
  stoneFraction: Field[float] = Field()
  platenPoints: Field[torch.Tensor] = Field()
  volumes: Field[torch.Tensor] = Field()
  facetCorners: Field[torch.Tensor] = Field()
  facetCounts: Field[torch.Tensor] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @radius.GET
  def _getRadius(self, ) -> float:
    """The 'radius' getter returns the radius of the cylinder, in mm."""
    if self.__lattice_radius__ is None:
      raise MissingVariable(self, '__lattice_radius__', float)
    return self.__lattice_radius__

  @height.GET
  def _getHeight(self, ) -> float:
    """The 'height' getter returns the height of the cylinder, in mm."""
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
  def _getStones(self, ) -> tuple:
    """The 'stones' getter returns the stones in the cylinder."""
    if self.__lattice_stones__ is None:
      raise MissingVariable(self, '__lattice_stones__', tuple)
    return self.__lattice_stones__

  @stoneFraction.GET
  def _getStoneFraction(self, ) -> float:
    """The 'stoneFraction' getter returns the share of the cylinder the
    stones fill."""
    filled = sum(stone.volume for stone in self.stones)
    return filled / (math.pi * self.radius ** 2 * self.height)

  @platenPoints.GET
  def _getPlatenPoints(self, ) -> torch.Tensor:
    """The 'platenPoints' getter returns where the platens are held,
    the middle of the bottom end and of the top."""
    points = [[0.0, 0.0, 0.0], [0.0, self.height, 0.0]]
    return torch.from_numpy(numpy.array(points))

  @volumes.GET
  def _getVolumes(self, ) -> torch.Tensor:
    """The 'volumes' getter returns the volume of each cell, in mm³."""
    return self._part('volumes')

  @facetCorners.GET
  def _getFacetCorners(self, ) -> torch.Tensor:
    """The 'facetCorners' getter returns the corners of each spring's
    face, in order round it, the last repeated to make up the most any
    face has."""
    return self._part('corners')

  @facetCounts.GET
  def _getFacetCounts(self, ) -> torch.Tensor:
    """The 'facetCounts' getter returns how many corners each spring's
    face has."""
    return self._part('counts')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Cylinder, float)
  def __init__(self, cylinder: Cylinder, spacing: float) -> None:
    self._setLattice(cylinder.radius, cylinder.height, cylinder.stones,
                     spacing, cylinder.seed)

  @overload(float, float, tuple, float, int)
  def __init__(self, *args) -> None:
    self._setLattice(*args)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setLattice(self, radius: float, height: float, stones: tuple,
                  spacing: float, seed: int, ) -> None:
    """Keeps what the lattice is of and builds it."""
    if radius <= 0.0 or height <= 0.0 or spacing <= 0.0:
      raise ValueError('a lattice must be more than nought each way')
    self.__lattice_radius__ = radius
    self.__lattice_height__ = height
    self.__lattice_spacing__ = spacing
    self.__lattice_seed__ = seed
    self.__lattice_stones__ = (*stones,)
    self.__stone_planes__, self.__stone_bounds__ = self._stonePlanes()
    self.__lattice_parts__ = self._build()

  def _stonePlanes(self, ) -> tuple[torch.Tensor, torch.Tensor]:
    """The stones as the planes bounding them where they are, a row of
    nx, ny, nz and c to a face, a point p inside where n . p is less
    than c for every face, those of a stone with fewer faces padded with
    planes nothing is outside of; and the sphere about each."""
    stones = self.stones
    faces = max([4, *[len(stone.normals) for stone in stones]])
    planes = torch.zeros(len(stones), faces, 4).double()
    planes[:, :, 3] = 1.0
    bounds = torch.zeros(len(stones), 4).double()
    for index, stone in enumerate(stones):
      count = len(stone.normals)
      planes[index, :count, :3] = stone.normals
      reach = stone.offsets + stone.normals @ stone.centre
      planes[index, :count, 3] = reach
      bounds[index, :3] = stone.centre
      bounds[index, 3] = stone.outer
    return planes, bounds

  def _placeNodes(self, ) -> numpy.ndarray:
    """Nodes at random through the cylinder, never nearer than the
    spacing: points tried three to a spacing cubed, and of each pair
    nearer than the spacing the one drawn the later number thinned
    away."""
    rng = numpy.random.default_rng(self.seed)
    radius, height, spacing = self.radius, self.height, self.spacing
    density = self.__fallback_trial_density__ / spacing ** 3
    count = rng.poisson(density * 4 * radius ** 2 * height)
    points = numpy.stack([
        (2 * rng.random(count) - 1) * radius,
        rng.random(count) * height,
        (2 * rng.random(count) - 1) * radius,
    ], 1)
    points = points[points[:, 0] ** 2 + points[:, 2] ** 2 <= radius ** 2]
    pairs = cKDTree(points).query_pairs(spacing, 2.0, 0.0, 'ndarray')
    marks = rng.random(len(points))
    later = numpy.where(marks[pairs[:, 0]] > marks[pairs[:, 1]],
                        pairs[:, 0], pairs[:, 1])
    kept = numpy.ones(len(points), bool)
    kept[later] = False
    return points[kept]

  def _mirror(self, points: numpy.ndarray) -> tuple:
    """The nodes with their images across the ends and the wall near
    them: all the points, which node each is of, and across what."""
    radius, height = self.radius, self.height
    reach = self.__fallback_mirror_reach__ * self.spacing
    count = len(points)
    across = numpy.sqrt(points[:, 0] ** 2 + points[:, 2] ** 2)
    nearWall = across > radius - reach
    walled = points.copy()
    stretch = (2 * radius - across[nearWall]) / across[nearWall]
    walled[nearWall, 0] *= stretch
    walled[nearWall, 2] *= stretch
    low, high = points[:, 1] < reach, points[:, 1] > height - reach
    parts = [(points, numpy.arange(count), _REAL)]
    for kind, near, source, flip in ((_BOTTOM, low, points, False),
                                     (_TOP, high, points, True),
                                     (_WALL, nearWall, walled, None)):
      image = source[near].copy()
      if flip is not None:
        image[:, 1] = 2 * height - image[:, 1] if flip else -image[:, 1]
      parts.append((image, numpy.nonzero(near)[0], kind))
    every = numpy.concatenate([part[0] for part in parts])
    owner = numpy.concatenate([part[1] for part in parts])
    kinds = numpy.concatenate([
        numpy.full(len(part[1]), part[2]) for part in parts])
    return every, owner, kinds

  def _build(self, ) -> dict:
    """Builds the cells and the springs."""
    points = self._placeNodes()
    every, owner, kinds = self._mirror(points)
    diagram = Voronoi(every)
    pairs = diagram.ridge_points
    one, two = pairs[:, 0], pairs[:, 1]
    oneReal, twoReal = kinds[one] == _REAL, kinds[two] == _REAL
    inner = oneReal & twoReal
    node = numpy.where(oneReal, one, two)
    image = numpy.where(oneReal, two, one)
    single = oneReal ^ twoReal
    own = single & (owner[image] == node)
    links = own & ((kinds[image] == _BOTTOM) | (kinds[image] == _TOP))
    walls = single & ~links
    kept = numpy.nonzero(inner | links | walls)[0]
    loops = [diagram.ridge_vertices[index] for index in kept.tolist()]
    if any(-1 in loop for loop in loops):
      raise ValueError('the cells do not close')
    nodes = torch.from_numpy(numpy.ascontiguousarray(points))
    every = torch.from_numpy(numpy.ascontiguousarray(every))
    corners = torch.from_numpy(numpy.ascontiguousarray(diagram.vertices))
    toward = every[image[kept]] - every[node[kept]]
    faces = self._faces(corners, loops, _unit(toward))
    where = {'inner': inner[kept], 'links': links[kept],
             'walls': walls[kept]}
    parts = {'nodes': nodes}
    parts.update(self._springs(nodes, every, faces, kept, one, two, node,
                               image, kinds, where))
    return parts

  def _faces(self, corners: torch.Tensor, loops: list,
             normals: torch.Tensor, ) -> dict:
    """The faces of the cells: each face's corners put in order round it,
    its area and its centre; a chunk of faces at a time."""
    counts = torch.tensor([len(loop) for loop in loops])
    widest = int(counts.max())
    flat = torch.tensor([index for loop in loops for index in loop])
    starts = torch.cumsum(counts, 0) - counts
    rows = torch.repeat_interleave(torch.arange(len(loops)), counts)
    cols = torch.arange(len(flat)) - starts[rows]
    table = torch.full((len(loops), widest), -1)
    table[rows, cols] = flat
    table = torch.where(table < 0, table[:, :1], table)
    size = self.__fallback_face_chunk__
    out = {'corners': [], 'areas': [], 'centres': []}
    for start in range(0, len(loops), size):
      chunk = self._faceChunk(corners[table[start:start + size]],
                              counts[start:start + size],
                              normals[start:start + size])
      for key, value in zip(('corners', 'areas', 'centres'), chunk):
        out[key].append(value)
    out = {key: torch.cat(value) for key, value in out.items()}
    out['counts'] = counts
    return out

  @staticmethod
  def _faceChunk(points: torch.Tensor, counts: torch.Tensor,
                 normals: torch.Tensor, ) -> tuple:
    """Faces' corners in order round them, by the angle each makes about
    the face's middle in its plane; then the face's area and centre from
    the triangles its edges make with its middle."""
    valid = torch.arange(points.shape[1])[None] < counts[:, None]
    middle = (points * valid[..., None]).sum(1) / counts[:, None]
    helper = torch.zeros_like(normals)
    helper[:, 0] = 1.0
    sideways = normals[:, 0].abs() > 0.9
    helper[sideways, 0] = 0.0
    helper[sideways, 1] = 1.0
    across = _unit(torch.cross(normals, helper, 1))
    other = torch.cross(normals, across, 1)
    offset = points - middle[:, None]
    angles = torch.atan2((offset * other[:, None]).sum(2),
                         (offset * across[:, None]).sum(2))
    angles = torch.where(valid, angles, angles[:, :1])
    order = torch.argsort(angles, 1)
    points = torch.gather(points, 1, order[..., None].expand(-1, -1, 3))
    after = torch.roll(points, -1, 1)
    spans = torch.cross(points - middle[:, None],
                        after - middle[:, None], 2)
    parts = spans.norm(2, 2) / 2
    areas = parts.sum(1)
    centres = (parts[..., None] * (middle[:, None] + points + after)
               / 3).sum(1) / areas[:, None]
    return points, areas, centres

  def _springs(self, nodes: torch.Tensor, every: torch.Tensor,
               faces: dict, kept: numpy.ndarray, one: numpy.ndarray,
               two: numpy.ndarray, node: numpy.ndarray,
               image: numpy.ndarray, kinds: numpy.ndarray,
               where: dict, ) -> dict:
    """The springs between neighbours, then those on the platens; and
    the cells' volumes from the faces round them."""
    count, height = len(nodes), self.height
    inner, links = where['inner'], where['links']
    walls = where['walls']
    pick = _tensor
    oneInner, twoInner = pick(one[kept][inner]), pick(two[kept][inner])
    bearing = pick(node[kept][links])
    onTop = pick(kinds[image[kept][links]] == _TOP)
    along = nodes[twoInner] - nodes[oneInner]
    reach = along.norm(2, 1)
    linkReach = (nodes[bearing, 1] - onTop.double() * height).abs()
    upward = onTop.double() * 2.0 - 1.0
    linkNormals = torch.zeros(len(bearing), 3).double()
    linkNormals[:, 1] = upward
    first = torch.cat([oneInner, bearing])
    second = torch.cat([twoInner, torch.where(onTop, count + 1, count)])
    order = torch.cat([torch.nonzero(torch.from_numpy(inner))[:, 0],
                       torch.nonzero(torch.from_numpy(links))[:, 0]])
    areas = faces['areas'][order]
    centres = faces['centres'][order]
    distances = torch.cat([reach, linkReach])
    normals = torch.cat([along / reach[:, None], linkNormals])
    phases, shares = self._materials(nodes, oneInner, twoInner, bearing)
    places = torch.cat([nodes, self.platenPoints])
    parts = {
        'first': first, 'second': second, 'centres': centres,
        'faceAreas': areas, 'distances': distances, 'normals': normals,
        'phases': phases, 'shares': shares,
        'corners': faces['corners'][order].float(),
        'counts': faces['counts'][order],
    }
    parts.update(self._rows(places, first, second, centres, normals))
    wallNodes = pick(node[kept][walls])
    wallAreas = faces['areas'][torch.from_numpy(walls)]
    wallReach = (every[pick(image[kept][walls])]
                 - nodes[wallNodes]).norm(2, 1) / 2
    parts.update(self._volumes(parts, count, wallNodes, wallAreas,
                               wallReach))
    return parts

  @staticmethod
  def _rows(places: torch.Tensor, first: torch.Tensor,
            second: torch.Tensor, centres: torch.Tensor,
            normals: torch.Tensor, ) -> dict:
    """How each spring stretches and slides two ways as its bodies move:
    at the face's centre, the second body's movement there less the
    first's, each body turning about its node."""
    helper = torch.zeros_like(normals)
    helper[:, 0] = 1.0
    sideways = normals[:, 0].abs() > 0.9
    helper[sideways, 0] = 0.0
    helper[sideways, 1] = 1.0
    across = _unit(torch.cross(normals, helper, 1))
    other = torch.cross(normals, across, 1)
    armOne = centres - places[first]
    armTwo = centres - places[second]
    rows = []
    for unit in (normals, across, other):
      rows.append(torch.cat([
          -unit, -torch.cross(armOne, unit, 1),
          unit, torch.cross(armTwo, unit, 1),
      ], 1))
    moves = [6 * first + step for step in range(6)]
    moves += [6 * second + step for step in range(6)]
    return {'normalRows': rows[0],
            'shearRows': torch.stack([rows[1], rows[2]], 1),
            'dofs': torch.stack(moves, 1)}

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
    gaps = torch.cdist(points, bounds[:, :3]) - bounds[:, 3]
    pairs = torch.nonzero(gaps < 0)
    point, stone = pairs[:, 0], pairs[:, 1]
    planes = self.__stone_planes__[stone]
    room = planes[..., 3] - (planes[..., :3] * points[point, None]).sum(2)
    out[point[(room > 0).all(1)]] = True
    return out

  def _crossings(self, starts: torch.Tensor, stops: torch.Tensor) -> tuple:
    """
    For each line from 'starts' to 'stops': the share of it inside
    stones, whether both its ends are in one stone, and whether it
    crosses a stone's face. Each line is clipped by the faces of every
    stone whose sphere it comes near, a chunk of lines at a time.
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
      gaps = torch.cdist(middle, bounds[:, :3]) - bounds[:, 3]
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
    are in it: the line clipped by each face of the stone."""
    planes = self.__stone_planes__[stones]
    normals, limits = planes[..., :3], planes[..., 3]
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

  @staticmethod
  def _volumes(parts: dict, count: int, wallNodes: torch.Tensor,
               wallAreas: torch.Tensor, wallReach: torch.Tensor, ) -> dict:
    """The volume of each cell, from the pyramids its faces make with its
    node, and which cells end on an end or the wall."""
    first, second = parts['first'], parts['second']
    areas, distances = parts['faceAreas'], parts['distances']
    linked = second >= count
    inner = ~linked
    volumes = torch.zeros(count).double()
    halves = areas[inner] * distances[inner] / 6
    volumes.index_add_(0, first[inner], halves)
    volumes.index_add_(0, second[inner], halves)
    onPlaten = areas[linked] * distances[linked] / 3
    volumes.index_add_(0, first[linked], onPlaten)
    volumes.index_add_(0, wallNodes, wallAreas * wallReach / 3)
    boundary = torch.zeros(count).bool()
    boundary[first[linked]] = True
    boundary[wallNodes] = True
    return {'volumes': volumes, 'boundary': boundary}
