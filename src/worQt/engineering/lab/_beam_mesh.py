"""
BeamMesh is a beam on its rig as a solid of bricks, its bars and
stirrups steel through them, as OpenSees is given it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from worksees import Model

from ._rc_beam import RCBeam
from ._rig import Rig

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worksees import Result

#  What the elements are asked each step: the bricks' strains, the
#  trusses' strains
QUERIES = (('strains',), ('material', 'strain'))
_POINTS = 8  # integration points of a brick, 6 strains each
_ALONG = 50.0  # mm: the bricks along the beam, at most
_UP = 60.0  # mm: over its height, at most
_ACROSS = 65.0  # mm: across its width, at most
_PLATE = 100.0  # mm: how long an actuator's plate is along the beam
_NEAR = 15.0  # mm: lines nearer than this are one line
_SCATTER = 0.05  # of the tensile strength, either way
_STIRRUP_COVER = 30.0  # mm: a stirrup's corners in from the faces, no bars


def _lines(stops: list[float], length: float, size: float) -> list[float]:
  """The lines from nought to 'length' at 'stops' and between them at
  most 'size' apart, a stop nearer than '_NEAR' to one before it
  dropped."""
  kept = []
  for stop in sorted({0.0, length, *stops}):
    if not kept or stop - kept[-1] >= _NEAR or stop == length:
      kept.append(stop)
  if len(kept) > 2 and kept[-1] - kept[-2] < _NEAR:
    del kept[-2]
  lines = [kept[0]]
  for start, end in zip(kept, kept[1:]):
    count = max(1, math.ceil((end - start) / size - 1e-9))
    lines += [start + (end - start) * n / count
              for n in range(1, count + 1)]
  return lines


def _nearest(lines: list[float], value: float) -> int:
  """The index of the line nearest 'value'."""
  _, index = min((abs(line - value), index)
                 for index, line in enumerate(lines))
  return index


class BeamMesh(BaseObject):
  """
  BeamMesh is an 'RCBeam' on a 'Rig' as a solid, in mm and N, as
  OpenSees is given it: the concrete in eight node bricks ('stdBrick',
  eight points each, the one-point 'SSPbrick' being held stiff by its
  elastic stabilising when the concrete cracks) filling the beam, at
  most 50 mm long, 60 mm high and 65 mm across, of 'ASDConcrete3D' to
  'fcm' in compression
  and its tensile strength in tension, damaging and softening, the
  softening scaled to each brick's size; its tensile strength scatters 5
  % either way from brick to brick, drawn from 'seed', so the beam
  cracks first where it is weakest. The bars run through the bricks'
  nodes as trusses of 'Steel02', each bar on its line along the beam,
  the top bars on the bottom bars' lines across where they are near;
  the stirrups stand on the lines along the beam nearest them, closed
  links of four legs round the outer bars. Nothing is symmetric: the
  whole beam is there, every brick of it.

  Each support holds the underside's line across the beam, so the beam
  turns on it freely, a pin along too, a roller free to slide; a clamp
  holds the whole section every way; the first support holds the beam
  from sliding sideways. The bricks bearing on a support, and those
  under an actuator's plate, are elastic, as bearing pads are, so the
  beam does not crush where it is held or pushed; the readings leave
  them out. Each actuator pushes through a
  plate 100 mm long across the top, its share of a newton spread over
  the plate's nodes, so the load factor is how hard the one driven
  pushes down, at the node in the plate's middle, 'driven'.

  'xs', 'ys' and 'zs' are the lines of the mesh along, up and across;
  'strengths' each brick's tensile strength; 'stirrupPlaces' where the
  stirrups stand. 'read' reads a 'Result' as the instruments and the
  lab see it: 'deflections' along the underside's middle, 'lifts' the
  same up positive, 'transducers', each read between the lines, the
  'cells' of the beam's face, a column of bricks across each, with the
  greatest principal strain in the plane of the face, its direction and
  the least, and the strains of the bottom and the top bars and of each
  stirrup.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __mesh_setup__: tuple[RCBeam, Rig, int] | None = None
  __mesh_lines__: tuple[tuple, tuple, tuple] | None = None
  __mesh_strengths__: tuple[float, ...] = ()
  __mesh_bars__: tuple[list, list, list] | None = None
  __mesh_driven__: int = 0

  #  Virtual Variables
  beam: Field[RCBeam] = Field()
  rig: Field[Rig] = Field()
  xs: Field[tuple[float, ...]] = Field()
  ys: Field[tuple[float, ...]] = Field()
  zs: Field[tuple[float, ...]] = Field()
  strengths: Field[tuple[float, ...]] = Field()
  stirrupPlaces: Field[tuple[float, ...]] = Field()
  brickCount: Field[int] = Field()
  driven: Field[int] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getSetup(self, ) -> tuple[RCBeam, Rig, int]:
    if self.__mesh_setup__ is None:
      raise MissingVariable(self, '__mesh_setup__', tuple)
    return self.__mesh_setup__

  @beam.GET
  def _getBeam(self, ) -> RCBeam:
    """The 'beam' getter returns the beam meshed."""
    return self._getSetup()[0]

  @rig.GET
  def _getRig(self, ) -> Rig:
    """The 'rig' getter returns the rig the beam is on."""
    return self._getSetup()[1]

  @xs.GET
  def _getXs(self, ) -> tuple[float, ...]:
    """The 'xs' getter returns the mesh's lines along the beam."""
    return self.__mesh_lines__[0]

  @ys.GET
  def _getYs(self, ) -> tuple[float, ...]:
    """The 'ys' getter returns the mesh's lines up the beam."""
    return self.__mesh_lines__[1]

  @zs.GET
  def _getZs(self, ) -> tuple[float, ...]:
    """The 'zs' getter returns the mesh's lines across the beam."""
    return self.__mesh_lines__[2]

  @strengths.GET
  def _getStrengths(self, ) -> tuple[float, ...]:
    """The 'strengths' getter returns each brick's tensile strength, in
    MPa, brick by brick along, then up, then across."""
    return self.__mesh_strengths__

  @stirrupPlaces.GET
  def _getStirrupPlaces(self, ) -> tuple[float, ...]:
    """The 'stirrupPlaces' getter returns where the stirrups stand: the
    lines nearest them."""
    return (*[self.xs[i] for i in self._stirrupLines()],)

  @brickCount.GET
  def _getBrickCount(self, ) -> int:
    """The 'brickCount' getter returns how many bricks there are."""
    nx, ny, nz = (len(lines) - 1 for lines in (self.xs, self.ys, self.zs))
    return nx * ny * nz

  @driven.GET
  def _getDriven(self, ) -> int:
    """The 'driven' getter returns the node the driven actuator's plate
    is pushed at, as built by 'model'."""
    return self.__mesh_driven__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(RCBeam, Rig, int)
  def __init__(self, beam: RCBeam, rig: Rig, seed: int) -> None:
    self.__mesh_setup__ = (beam, rig, seed)
    self.__mesh_lines__ = (self._alongLines(), self._upLines(),
                           self._acrossLines())
    scatter = random.Random(seed)
    self.__mesh_strengths__ = (
      *[beam.fctm * (1 + _SCATTER * scatter.uniform(-1, 1))
        for _ in range(self.brickCount)],
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def node(self, i: int, j: int, k: int) -> int:
    """The 'node' method returns the number of the node on the lines 'i'
    along, 'j' up and 'k' across."""
    nx, ny = len(self.xs), len(self.ys)
    return 1 + i + nx * (j + ny * k)

  def cell(self, i: int, j: int) -> int:
    """The 'cell' method returns the index of the cell of the face 'i'
    along and 'j' up, in the reading's 'cells'."""
    return i + (len(self.xs) - 1) * j

  def middle(self, ) -> int:
    """The 'middle' method returns the line across the middle of the
    beam's width, or the one nearest it."""
    return _nearest([*self.zs], self.beam.width / 2)

  def model(self, ) -> Model:
    """The 'model' method returns the beam on its rig as OpenSees is
    given it."""
    model = Model(3, 3)
    for z in self.zs:
      for y in self.ys:
        for x in self.xs:
          model.addNode(x, y, z)
    self._bricks(model)
    bottom, top, stirrups = self._steel(model)
    self.__mesh_bars__ = (bottom, top, stirrups)
    self._supports(model)
    self._actuators(model)
    return model

  def read(self, result: Result) -> dict:
    """The 'read' method returns what 'result' reads as: 'lifts' and
    'deflections' along the underside's middle, the 'stroke' of the
    driven actuator, up positive, the 'cells' of the face and the
    strains of the 'bottomBars', the 'topBars' and the 'stirrups'."""
    moved = result.displacements
    middle = self.middle()
    lifts = (*[moved[self.node(i, 0, middle) - 1][1]
               for i in range(len(self.xs))],)
    bottom, top, stirrups = self.__mesh_bars__
    trusses = result.response(QUERIES[1])
    return {
        'lifts': lifts,
        'deflections': (*[-lift for lift in lifts],),
        'stroke': moved[self.driven - 1][1],
        'cells': self._cells(result.response(QUERIES[0])),
        'bottomBars': self._strains(trusses, bottom),
        'topBars': self._strains(trusses, top),
        'stirrups': self._strains(trusses, stirrups),
    }

  def liftAt(self, x: float, lifts: tuple) -> float:
    """The 'liftAt' method returns how far the underside's middle has
    moved up at 'x', between its lines as a straight line."""
    xs = self.xs
    index = max(0, min(len(xs) - 2, sum(1 for line in xs if line <= x) - 1))
    share = (x - xs[index]) / (xs[index + 1] - xs[index])
    return lifts[index] * (1 - share) + lifts[index + 1] * share

  def bearing(self, i: int, j: int) -> bool:
    """The 'bearing' method tells whether the bricks of the cell 'i'
    along and 'j' up bear on a support or under an actuator's plate,
    elastic, so the beam does not crush where it is held or pushed, as
    a bearing pad's mortar is not let crush."""
    beam, rig, xs = self.beam, self.rig, self.xs
    if j == 0:
      for support in rig.supports:
        line = _nearest([*xs], support.at)
        if i in (line - 1, line) and not support.holds[2]:
          return True
    if j == len(self.ys) - 2:
      for actuator in rig.actuators:
        low = actuator.at - _PLATE / 2
        high = actuator.at + _PLATE / 2
        if xs[i] >= low - 1e-6 and xs[i + 1] <= high + 1e-6:
          return True
    return False

  def cellStrength(self, i: int, j: int) -> float:
    """The 'cellStrength' method returns the least tensile strength of
    the bricks across the cell 'i' along and 'j' up."""
    nx, ny = len(self.xs) - 1, len(self.ys) - 1
    return min(self.strengths[i + nx * (j + ny * k)]
               for k in range(len(self.zs) - 1))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _barPlaces(self, count: int, diameter: float,
                 cover: float) -> list[float]:
    """Where 'count' bars of 'diameter' with 'cover' are across the
    beam."""
    width = self.beam.width
    reach = width / 2 - cover - diameter / 2
    if count == 1:
      return [width / 2]
    return [width / 2 - reach + 2 * reach * n / (count - 1)
            for n in range(count)]

  def _alongLines(self, ) -> tuple[float, ...]:
    """The lines along the beam: at its ends, the supports and the
    actuators and their plates' ends, and the stirrups."""
    beam, rig = self.beam, self.rig
    stops = [support.at for support in rig.supports]
    for actuator in rig.actuators:
      stops += [actuator.at, max(actuator.at - _PLATE / 2, 0.0),
                min(actuator.at + _PLATE / 2, beam.length)]
    lines = _lines(stops, beam.length, _ALONG)
    places = beam.stirrups.places(beam.length)
    extra = [x for x in places
             if min(abs(x - line) for line in lines) > 0.3 * _ALONG]
    if extra:
      lines = _lines([*stops, *extra], beam.length, _ALONG)
    return (*lines,)

  def _rows(self, ) -> tuple[float, float]:
    """How high the bottom and the top rows of steel are: the bars', or
    the stirrups' corners where there are none."""
    beam = self.beam
    bottom = beam.bottom.depth if beam.bottom.count else _STIRRUP_COVER
    top = beam.height - (beam.top.depth if beam.top.count
                         else _STIRRUP_COVER)
    return bottom, top

  def _upLines(self, ) -> tuple[float, ...]:
    """The lines up the beam: at its faces and the rows of steel."""
    return (*_lines([*self._rows()], self.beam.height, _UP),)

  def _acrossPlaces(self, ) -> list[float]:
    """Where the steel is across the beam: the bottom bars, and the
    stirrups' legs where there are none."""
    beam = self.beam
    layer = beam.bottom
    if layer.count:
      return self._barPlaces(layer.count, layer.diameter, layer.cover)
    return [_STIRRUP_COVER, beam.width - _STIRRUP_COVER]

  def _acrossLines(self, ) -> tuple[float, ...]:
    """The lines across the beam: at its faces, the bottom bars, and the
    top bars where they are not near those."""
    beam = self.beam
    stops = self._acrossPlaces()
    layer = beam.top
    if layer.count:
      for z in self._barPlaces(layer.count, layer.diameter, layer.cover):
        if min(abs(z - stop) for stop in stops) > _NEAR:
          stops.append(z)
    return (*_lines(stops, beam.width, _ACROSS),)

  def _bricks(self, model: Model) -> None:
    """Adds the concrete's bricks, each of its own strength."""
    beam = self.beam
    nx, ny, nz = len(self.xs) - 1, len(self.ys) - 1, len(self.zs) - 1
    for k in range(nz):
      for j in range(ny):
        for i in range(nx):
          size = (self.xs[i + 1] - self.xs[i]) * (self.ys[j + 1]
                                                  - self.ys[j])
          tensile = self.strengths[i + nx * (j + ny * k)]
          if self.bearing(i, j):
            concrete = model.add('nDMaterial', 'ElasticIsotropic',
                                 beam.Ecm, 0.2)
          else:
            concrete = model.add('nDMaterial', 'ASDConcrete3D', beam.Ecm,
                                 0.2, '-fc', beam.fcm, '-ft', tensile,
                                 '-tangent', '-autoRegularization',
                                 math.sqrt(size))
          node = self.node
          model.add('element', 'stdBrick', node(i, j, k),
                    node(i + 1, j, k), node(i + 1, j + 1, k),
                    node(i, j + 1, k), node(i, j, k + 1),
                    node(i + 1, j, k + 1), node(i + 1, j + 1, k + 1),
                    node(i, j + 1, k + 1), concrete)

  def _steel(self, model: Model) -> tuple[list, list, list]:
    """Adds the bars and the stirrups as trusses, and returns their
    elements: the bottom and the top bars' by stretch along the beam,
    the stirrups' by stirrup."""
    beam = self.beam
    plastic = beam.epsUk - beam.fy / beam.Es
    ratio = (beam.hardening - 1) * beam.fy / (beam.Es * plastic)
    steel = model.add('uniaxialMaterial', 'Steel02', beam.fy, beam.Es,
                      ratio, 18.0, 0.925, 0.15)
    rows = [_nearest([*self.ys], y) for y in self._rows()]
    bottom = self._bars(model, steel, beam.bottom, rows[0])
    top = self._bars(model, steel, beam.top, rows[1])
    stirrups = []
    if beam.stirrups.diameter:
      places = self._acrossPlaces()
      sides = [_nearest([*self.zs], places[0]),
               _nearest([*self.zs], places[-1])]
      area = beam.stirrups.area / 2
      for i in self._stirrupLines():
        legs = []
        for k in sides:
          for j in range(rows[0], rows[1]):
            legs.append(model.add('element', 'truss', self.node(i, j, k),
                                  self.node(i, j + 1, k), area, steel))
        for j in rows:
          for k in range(sides[0], sides[1]):
            legs.append(model.add('element', 'truss', self.node(i, j, k),
                                  self.node(i, j, k + 1), area, steel))
        stirrups.append(legs)
    return bottom, top, stirrups

  def _bars(self, model: Model, steel: int, layer, row: int) -> list:
    """Adds the bars of 'layer' on the row 'row', and returns their
    elements by stretch along the beam."""
    stretches = [[] for _ in self.xs[1:]]
    if not layer.count:
      return stretches
    area = layer.area / layer.count
    for z in self._barPlaces(layer.count, layer.diameter, layer.cover):
      k = _nearest([*self.zs], z)
      for i in range(len(self.xs) - 1):
        stretches[i].append(model.add('element', 'truss',
                                      self.node(i, row, k),
                                      self.node(i + 1, row, k), area,
                                      steel))
    return stretches

  def _stirrupLines(self, ) -> list[int]:
    """The lines along the beam the stirrups stand on."""
    beam = self.beam
    return [_nearest([*self.xs], x)
            for x in beam.stirrups.places(beam.length)]

  def _supports(self, model: Model) -> None:
    """Holds the underside's line across the beam at each support, so
    it turns freely, a pin along too; a clamp holds the whole section
    every way; and the first support's middle node holds the beam from
    sliding sideways."""
    ny, nz = len(self.ys), len(self.zs)
    for support in self.rig.supports:
      i = _nearest([*self.xs], support.at)
      along, _, turning = support.holds
      for j in range(ny) if turning else range(1):
        for k in range(nz):
          model.fix(self.node(i, j, k), along, 1, 1 if turning else 0)
    first = self.rig.supports[0]
    model.fix(self.node(_nearest([*self.xs], first.at), 0,
                        self.middle()), 0, 0, 1)

  def _actuators(self, model: Model) -> None:
    """Spreads each actuator's share of a newton over its plate's
    nodes, and notes the node the driven one is pushed at."""
    rig = self.rig
    top, nz = len(self.ys) - 1, len(self.zs)
    for index, (actuator, share) in enumerate(zip(rig.actuators,
                                                  rig.shares)):
      low, high = actuator.at - _PLATE / 2, actuator.at + _PLATE / 2
      lines = [i for i, x in enumerate(self.xs)
               if low - 1e-6 <= x <= high + 1e-6]
      plate = [self.node(i, top, k) for i in lines for k in range(nz)]
      for node in plate:
        model.addLoad(node, 0.0, -share / len(plate), 0.0)
      if index == rig.driven:
        middle = _nearest([*self.xs], actuator.at)
        self.__mesh_driven__ = self.node(middle, top, self.middle())

  def _cells(self, strains: tuple) -> tuple[tuple[float, float, float], ...]:
    """Each cell of the face: the greatest principal strain in the plane
    of the face among the bricks across it, the direction it pulls in,
    from along the beam, and the least principal strain among them."""
    nx, ny, nz = len(self.xs) - 1, len(self.ys) - 1, len(self.zs) - 1
    cells = []
    for j in range(ny):
      for i in range(nx):
        most, angle, least = -math.inf, 0.0, math.inf
        for k in range(nz):
          if self.bearing(i, j):
            continue
          points = strains[i + nx * (j + ny * k)]
          along, up, shear = (sum(points[n::6]) / _POINTS
                              for n in (0, 1, 3))
          middle = (along + up) / 2
          radius = math.hypot((along - up) / 2, shear / 2)
          if middle + radius > most:
            most = middle + radius
            angle = math.atan2(shear, along - up) / 2
          least = min(least, middle - radius)
        if most == -math.inf:
          most, least = 0.0, 0.0
        cells.append((most, angle, least))
    return (*cells,)

  @staticmethod
  def _strains(trusses: tuple, groups: list) -> tuple[float, ...]:
    """The greatest strain of each group of trusses, nought for an empty
    group."""
    out = []
    for group in groups:
      values = [trusses[element - 1][0] for element in group
                if trusses[element - 1]]
      out.append(max(values) if values else 0.0)
    return (*out,)
