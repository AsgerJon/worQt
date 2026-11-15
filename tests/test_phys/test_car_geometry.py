"""
TestCarGeometry covers the car-tests (user, 2026-11-15: "a sanity check
of the geometries that they don't overlap or anything stupid like
that"): the overlap tool itself ('_overlaps.overlapsOf': two boxes, a
ball in a box, a turned rod through a box, each by hand, within a cube
of the grid a face), then the real car as built ('_realcar.realCar',
its chassis as designed: 'realCarSolids'): no two of its parts that are
not joined share any space (parts that touch, or hang on a spring, cut
into each other there), and the joined share only what their joint's
hardware does, each such sharing named here with its reason and a cap
('DESIGNED'; teeth in mesh within 'MESHED' a pair); and every part of
its chassis lies inside its bodywork but what it declares in the open
(user, 2026-11-15: "at the lower rear of the car are still weird out of
place prisms": its rails' square ends stood out of the tail).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Body, BrakeLine, FourthWall, State, boxShape
from worQt.phys import Assembly
from worQt.phys._drivetrain import DrivetrainControls
from worQt.phys._overlaps import jointsOf, overlapsOf
from worQt.phys._realcar import Antilock, CHASSIS, COLUMN, CORNERS
from worQt.phys._realcar import CORNER_BODIES, HALVES, RACK, SIDES
from worQt.phys._realcar import RealCarControls, realCar, realCarSolids
from worQt.phys._rig import TuneUp, WheelSetup
from worQt.phys._shape import Sphere
from worQt.phys._turned import Turned

from . import PhysTest

#  The most space two parts not joined may share, m³ (four of the
#  grid's cubes: its grain).
APART = 0.5e-6
#  The most two gears in mesh may share, m³ (their teeth's faceting).
MESHED = 2e-6
#  What the real car's joined parts are designed to share, by their
#  roles ('TestCarGeometry.roleOf'): the most, m³ (as measured, a tenth
#  more), and why.
DESIGNED = {
  ('chassis', 'rack'): (211e-6, 'the rack slides in its housing (the '
                                'housing drawn solid)'),
  ('chassis', 'column'): (41e-6, "the column's pinion in the rack's "
                                 'housing, its shaft in its bushes'),
  ('column', 'rack'): (9.7e-6, "the pinion in the rack's teeth (drawn "
                               'solid)'),
  ('rod', 'tube'): (70e-6, "a shock's rod slides in its tube"),
  ('knuckle', 'rod'): (70e-6, "a strut's rod slides in its tube, on "
                              'the upright'),
  ('chassis', 'rod'): (12e-6, "a strut's top in its mount"),
  ('knuckle', 'upper'): (43e-6, 'a ball joint in its socket'),
  ('knuckle', 'lower'): (39e-6, 'a ball joint in its socket'),
  ('lower', 'tube'): (17e-6, "a shock's eye on the wishbone's lug"),
  ('carrier', 'side gear'): (49e-6, "a side gear turning in the "
                                    "carrier's bore"),
  ('carrier', 'spider'): (8.6e-6, "a spider on the carrier's pin"),
  ('gear', 'output'): (17.6e-6, 'a free gear riding on its shaft (its '
                                'bore not drawn)'),
  ('flywheel', 'input'): (6.6e-6, "the clutch's disc on the input "
                                  'shaft')}


def _boxAt(size: tuple, middle: tuple) -> tuple:
  """Returns a steel box of 'size' and its state at 'middle'."""
  return Body.of(boxShape(*size), 7800.0), State(middle)


class TestCarGeometry(PhysTest):
  """Tests for the car's geometry (half a minute)."""

  __time_out__ = 600.0

  def test_boxes(self) -> None:
    """Two 10 cm cubes, 4 cm into each other along x and 3 cm across y,
    share 10 x 4 x 7 cm (within a cube of the grid a face); 1 cm apart,
    nothing."""
    (one, at), (two, there) = (_boxAt((0.1, 0.1, 0.1), (0.0, 0.0, 0.0)),
                               _boxAt((0.1, 0.1, 0.1), (0.06, 0.03, 0.0)))
    found = overlapsOf(Assembly((one, two), ()), (at, there))
    self.assertEqual(len(found), 1)
    self.assertNear(found[0].volume, 0.04 * 0.07 * 0.1, 0.05 * 0.04 * 0.07
                    * 0.1)
    self.assertNear(found[0].middle, (0.03, 0.015, 0.0), 0.003)
    apart = _boxAt((0.1, 0.1, 0.1), (0.11, 0.0, 0.0))
    self.assertEqual(overlapsOf(Assembly((one, apart[0]), ()),
                                (at, apart[1])), ())

  def test_ball_and_rod(self) -> None:
    """A ball of 5 cm radius wholly in a box shares its volume; a turned
    rod (2 cm radius, along the world's x, turned so) through a 6 cm
    thick slab shares pi r^2 x 6 cm (each within 3 %)."""
    ball = Body.of(Sphere(0.05), 7800.0)
    box, at = _boxAt((0.3, 0.3, 0.3), (0.0, 0.0, 0.0))
    found = overlapsOf(Assembly((ball, box), ()), (State((0.02, 0.0, 0.0)),
                                                   at), {}, 0.002)
    self.assertNear(found[0].volume, 4.0 / 3.0 * math.pi * 0.05 ** 3,
                    0.03 * 4.0 / 3.0 * math.pi * 0.05 ** 3)
    rod = Body.of(Turned((('line', (0.0, -0.5), (0.02, -0.5)),
                          ('line', (0.02, -0.5), (0.02, 0.5)),
                          ('line', (0.02, 0.5), (0.0, 0.5)),
                          ('line', (0.0, 0.5), (0.0, -0.5)))), 7800.0)
    half = math.sqrt(0.5)
    slab, there = _boxAt((0.06, 0.4, 0.4), (0.0, 0.0, 0.0))
    found = overlapsOf(Assembly((rod, slab), ()), (
      State((0.0, 0.0, 0.0), (half, 0.0, half, 0.0)), there), {}, 0.002)
    self.assertNear(found[0].volume, math.pi * 0.02 ** 2 * 0.06,
                    0.03 * math.pi * 0.02 ** 2 * 0.06)

  def setUp(self) -> None:
    """The real car as built, still; its parts' roles."""
    self.controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                                    TuneUp((WheelSetup(),) * len(CORNERS)),
                                    DrivetrainControls(), Antilock())
    self.assembly, self.states = realCar(self.controls)

  def roleOf(self, index: int) -> str:
    """Returns what the real car's body 'index' is."""
    layout = self.controls.drive.layout
    if index == CHASSIS:
      return 'chassis'
    if index in (RACK, COLUMN):
      return 'rack' if index == RACK else 'column'
    for corner in CORNER_BODIES:
      for part, at in corner.items():
        if at == index:
          return part
    named = {layout.flywheel: 'flywheel', layout.input: 'input',
             layout.output: 'output', layout.carrier: 'carrier'}
    if index in named:
      return named[index]
    if layout.firstGear <= index < layout.firstGear + 6:
      return 'gear'
    if index in SIDES:
      return 'side gear'
    if index in HALVES:
      return 'half shaft'
    if layout.carrier < index < SIDES[0]:
      return 'spider'
    return 'body %d' % index

  def overlaps(self, ) -> tuple:
    """Returns the real car's parts' overlaps (the walker left out: a
    ball sat in the seat, it is no part of the car)."""
    return overlapsOf(self.assembly, self.states, realCarSolids(),
                      0.005, tuple(range(1, len(self.assembly.bodies))))

  def said(self, overlap: object) -> str:
    """Returns 'overlap' as a line: the two parts, how much, where."""
    return '%s %d / %s %d: %.1f cm3 at (%.3f, %.3f, %.3f) m' % (
      self.roleOf(overlap.first), overlap.first,
      self.roleOf(overlap.second), overlap.second, 1e6 * overlap.volume,
      *overlap.middle)

  def test_apart(self) -> None:
    """No two of the real car's parts that are not joined share more
    than the grid's grain ('APART'): every one that does listed."""
    joints = jointsOf(self.assembly)
    cutting = [self.said(overlap) for overlap in self.overlaps()
               if (overlap.first, overlap.second) not in joints
               and overlap.volume > APART]
    self.assertEqual(cutting, [], '\n'.join(['parts cut into each other:']
                                            + cutting))

  def test_joints(self) -> None:
    """Each two of the real car's joined parts share no more than their
    joint's hardware is designed to ('DESIGNED', by their roles; teeth
    in mesh 'MESHED'): every one that does listed."""
    joints = jointsOf(self.assembly)
    past = []
    for overlap in self.overlaps():
      kinds = joints.get((overlap.first, overlap.second))
      if kinds is None:
        continue
      roles = tuple(sorted((self.roleOf(overlap.first),
                            self.roleOf(overlap.second))))
      most = DESIGNED.get(roles, (None,))[0]
      if most is None and kinds == ('GearMesh',):
        most = MESHED
      if most is None or overlap.volume > most:
        past.append('%s (%s; %s)' % (self.said(overlap), ', '.join(kinds),
                                     'not designed' if most is None else
                                     'designed %.1f cm3' % (1e6 * most)))
    self.assertEqual(past, [], '\n'.join(['joined parts share more than '
                                          'their joint:'] + past))

  def test_inside(self) -> None:
    """Every part of the real car's chassis (its frame's boxes and round
    tubes, its side plates, its tub, the engine's block, the gearbox's
    case, the tank) lies inside its bodywork ('_bodyshell.insideShell':
    each box sampled 6 points a side, each tube 12 along it), but the
    front corners' brackets declared in the open ('ChassisParts.open',
    'openRods'): every one that does not, listed."""
    import numpy
    from worQt.phys._bodyshell import insideShell
    from worQt.phys._realcar import _chassisParts
    parts = _chassisParts()
    out = []
    shapes = (parts.steel + parts.plates + parts.wood + (parts.block,
                                                         parts.tank)
              + parts.case)
    for k, shape in enumerate(shapes):
      points = numpy.array(shape.points)
      low, high = points.min(0), points.max(0)
      grid = numpy.stack(numpy.meshgrid(*[numpy.linspace(a, b, 6) for a, b
                                          in zip(low, high)],
                                        indexing='ij'), -1).reshape(-1, 3)
      if not insideShell(grid).all():
        out.append('box %d from %s to %s' % (k, numpy.round(low, 3),
                                             numpy.round(high, 3)))
    for start, end, _ in parts.rods:
      share = numpy.linspace(0.0, 1.0, 12)[:, None]
      line = numpy.array(start) + share * (numpy.array(end)
                                           - numpy.array(start))
      if not insideShell(line).all():
        out.append('tube from %s to %s' % (start, end))
    self.assertEqual(out, [], '\n'.join(['out of the bodywork:'] + out))
