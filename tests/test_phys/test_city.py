"""
TestCity covers the real car in town (user, 2026-11-15: uncannyball's
lap of central Copenhagen, its files in 'previews/tracks'): a road laid
along a line read from its OpenCRG file ('_crg.readCrg': a circle
written here, its rows on it, its heights as written), laid onto a
regular terrain ('crgTerrain': on the road within a centimetre, its
slope the ground's), as a course ('_course.CrgCourse': a point's place
along and right of the middle and back, to a centimetre), drawn in its
photographs ('gui._meshes.crgMesh': each stretch's picture up it, its
foot where the stretch begins, its left edge the road's leftmost
column; the road on the terrain; none where the file holds no ground,
none where scenery covers it, 'crgBase' likewise); and, where the lap's
files are ('_city.cityHere', not in git), the scenery's ground under
the road where the terrain has it ('sceneryBox' round the start), the
town's walls clear of the road's middle line ('cityWall'), and the
city racer ('CityDriver') pulling away and keeping to its line between
them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os
import tempfile

import numpy

from worQt.phys import BrakeLine, FourthWall, SmallSteps
from worQt.phys._course import CrgCourse
from worQt.phys._crg import CrgTrack, crgTerrain, readCrg
from worQt.phys._drivetrain import DrivetrainControls, drivetrainWorked
from worQt.phys._realcar import Antilock, CORNERS, RealCarControls
from worQt.phys._rig import TuneUp, WheelSetup

from . import PhysTest

#  The circle written: its radius and rows, how many heights across,
#  their spacing, m.
RADIUS, ROWS, COLUMNS, SPACING = 50.0, 786, 21, 0.5


def _heightOf(x: float, y: float) -> float:
  """The circle's ground: a gentle tilt and a bump (m)."""
  return 2.0 + 0.01 * x + 0.3 * math.sin(0.05 * y)


def _written(folder: str) -> str:
  """Writes a closed circle of road anticlockwise as OpenCRG into
  'folder', returns its path: its rows every 2 pi R / ROWS m, its
  heights '_heightOf' where each lies."""
  step = 2.0 * math.pi * RADIUS / ROWS
  half = 0.5 * (COLUMNS - 1) * SPACING
  head = '\n'.join((
    'A circle for a test.',
    '$ROAD_CRG',
    'REFERENCE_LINE_START_U   = 0.0',
    'REFERENCE_LINE_END_U     = %r' % (ROWS * step),
    'REFERENCE_LINE_INCREMENT = %r' % step,
    'LONG_SECTION_V_RIGHT     = %r' % -half,
    'LONG_SECTION_V_LEFT      = %r' % half,
    'LONG_SECTION_V_INCREMENT = %r' % SPACING,
    'REFERENCE_LINE_START_X   = %r' % RADIUS,
    'REFERENCE_LINE_START_Y   = 0.0',
    '$KD_DEFINITION',
    'D:reference line phi,rad')) + '\n' + '\n'.join(
    'D:long section %d,m' % (k + 1) for k in range(COLUMNS))
  head += '\n$$$$$$$$\n'
  table = numpy.zeros((ROWS + 1, COLUMNS + 1), '>f4')
  turn = 2.0 * math.pi / ROWS
  across = numpy.linspace(-half, half, COLUMNS)
  for k in range(ROWS + 1):
    angle = k * turn
    table[k, 0] = 0.5 * math.pi + (k - 0.5) * turn
    for j, v in enumerate(across):
      r = RADIUS - v
      table[k, j + 1] = _heightOf(r * math.cos(angle), r * math.sin(angle))
  path = os.path.join(folder, 'circle.crg')
  with open(path, 'wb') as file:
    file.write(head.encode('latin-1'))
    file.write(table.tobytes())
  return path


class TestCity(PhysTest):
  """Tests for the real car in town (a minute where the lap is)."""

  __time_out__ = 1200.0

  def setUp(self) -> None:
    """A circle of road written and read."""
    self.folder = tempfile.TemporaryDirectory()
    self.track = readCrg(_written(self.folder.name))

  def tearDown(self) -> None:
    """The circle's folder gone."""
    self.folder.cleanup()

  def test_read(self) -> None:
    """The rows lie on the circle (its chords' polygon, to a
    millimetre), the last on the first; to the left points in, to its
    middle; the heights as written."""
    t = self.track
    self.assertEqual(t.heights.shape, (ROWS + 1, COLUMNS))
    far = numpy.hypot(t.x, t.y)
    self.assertLess(numpy.abs(far - RADIUS).max(), 0.01)
    self.assertLess(math.hypot(t.x[-1] - t.x[0], t.y[-1] - t.y[0]), 1e-6)
    inward = -(t.leftX * t.x + t.leftY * t.y) / far
    self.assertGreater(inward.min(), 0.999)
    self.assertAlmostEqual(float(t.heights[0, COLUMNS // 2]),
                           _heightOf(t.x[0], t.y[0]), delta=0.02)

  def test_terrain(self) -> None:
    """Laid onto a regular grid at 0.5 m (no finer than the file's own
    heights lie: finer, its points miss them), the road's heights are
    held within a centimetre over it; its normal the tilt's."""
    t = self.track
    terrain = crgTerrain(t, 0.5, 2.0)
    worst = 0.0
    for row in range(0, ROWS, 7):
      for column in range(2, COLUMNS - 2):
        x, y = t.placeOf(row, t.across[column])
        worst = max(worst, abs(terrain.heightAt(x, y) - float(
          t.heights[row, column])))
    self.assertLess(worst, 0.01)
    normal = terrain.normalAt(RADIUS, 0.0)
    self.assertAlmostEqual(normal[0], -0.01, delta=0.002)

  def test_course(self) -> None:
    """A point 'out' m right of the middle 'along' m round lies there
    again: to a centimetre, about the circle and at its seam."""
    course = CrgCourse(self.track, 7.0)
    self.assertAlmostEqual(course.length, 2.0 * math.pi * RADIUS,
                           delta=0.05)
    for along in (0.3, 47.0, 150.2, course.length - 0.3):
      for out in (-3.0, 0.0, 2.0):
        x, y, _ = course.at(along, out)
        found, round_ = course.placeOf(x, y)
        self.assertAlmostEqual(found, out, delta=0.01)
        self.assertAlmostEqual(round_, along, delta=0.01)

  def test_photographed(self) -> None:
    """Drawn in two pictures, half the circle each: a mesh each, every
    place on its picture within it, its foot where its stretch begins,
    its top where it ends, its left edge the road's leftmost column;
    the road's corners on the terrain (to a millimetre); a stretch where
    the file holds no ground drawn not at all."""
    from worQt.phys.gui._meshes import CRG_DOWN, SCALE, crgMesh
    t = self.track
    terrain = crgTerrain(t, 0.5, 2.0)
    length = ROWS * t.step
    pictures = ((0.0, 0.5 * length, 'a.jpg'), (0.5 * length, length,
                                                'b.jpg'))
    meshes = crgMesh(t, terrain, pictures)
    self.assertEqual([path for _, _, path in meshes], ['a.jpg', 'b.jpg'])
    for vertices, indices, _ in meshes:
      self.assertGreaterEqual(vertices[:, 6:8].min(), 0.0)
      self.assertLessEqual(vertices[:, 6:8].max(), 1.0)
      self.assertEqual(vertices[:, 7].min(), 0.0)
      self.assertEqual(vertices[:, 7].max(), 1.0)
      self.assertLess(int(indices.max()), len(vertices))
    vertices = meshes[0][0][-len(meshes[0][0]) // len(CRG_DOWN):]
    x, y = vertices[:, 0] / SCALE, -vertices[:, 2] / SCALE
    left = numpy.hypot(x, y) < RADIUS - 4.9
    self.assertLess(vertices[left, 6].max(), 1e-6)
    worst = max(abs(terrain.heightAt(float(a), float(b)) - float(z) / SCALE)
                for a, b, z in zip(x[::5], y[::5], vertices[::5, 1]))
    self.assertLess(worst, 1e-3)
    heights = numpy.array(t.heights)
    heights[:ROWS // 2 + 1] = numpy.nan
    holed = crgMesh(CrgTrack(t.step, t.x, t.y, t.leftX, t.leftY, t.across,
                             heights, t.heading), terrain, pictures)
    self.assertEqual([path for _, _, path in holed], ['b.jpg'])

  def test_hole(self) -> None:
    """Where scenery covers the ground (a square about the start), no
    square of the road's mesh nor of the terrain's lies wholly in it, the
    corners in it of those across its edge lowered under it; elsewhere
    as ever."""
    from worQt.phys.gui._meshes import SCALE, SCENERY_DOWN, crgBase
    from worQt.phys.gui._meshes import crgMesh
    t = self.track
    terrain = crgTerrain(t, 0.5, 2.0)
    hole = (RADIUS - 12.0, -12.0, RADIUS + 12.0, 12.0)
    pictures = ((0.0, ROWS * t.step, 'a.jpg'),)
    whole = crgMesh(t, terrain, pictures)[0]
    vertices, indices, _ = crgMesh(t, terrain, pictures, hole)[0]
    self.assertLess(len(indices), len(whole[1]))
    x, y = vertices[:, 0] / SCALE, -vertices[:, 2] / SCALE
    inside = (x > hole[0]) & (x < hole[2]) & (y > hole[1]) & (y < hole[3])
    self.assertFalse(inside[indices.reshape(-1, 6)].all(1).any())
    lowered = numpy.abs(vertices[:, 1] - whole[0][:, 1]) / SCALE
    self.assertLess(numpy.abs(lowered[inside] - SCENERY_DOWN).max(), 1e-4)
    self.assertLess(lowered[~inside].max(), 1e-6)
    coarse, dropped = crgBase(terrain, t, hole)
    plain, _ = crgBase(terrain, t)
    xs = coarse.origin[0] + coarse.cell * numpy.arange(len(coarse.heights))
    ys = coarse.origin[1] + coarse.cell * numpy.arange(
      len(coarse.heights[0]))
    gx, gy = numpy.meshgrid(xs, ys, indexing='ij')
    inside = (gx > hole[0]) & (gx < hole[2]) & (gy > hole[1]) & (
      gy < hole[3])
    self.assertTrue(dropped[inside].all())
    drop = numpy.asarray(plain.heights) - numpy.asarray(coarse.heights)
    self.assertLess(numpy.abs(drop[inside] - SCENERY_DOWN).max(), 1e-9)
    self.assertLess(numpy.abs(drop[~inside]).max(), 1e-12)

  def test_scenery(self) -> None:
    """Where the lap's files are: the scenery's square holds the lap's
    start; every piece's corners and its picture are there, its places
    on it within it to a hundredth (the ground's pieces overhang their
    64 m squares by half a metre: their pictures' edges drawn on); its
    ground within 2 m of the road's middle stands where the terrain has
    it (99 in 100 within a centimetre)."""
    from scipy.spatial import cKDTree
    from worQt.phys._city import cityGround, cityHere, cityScenery
    from worQt.phys._city import cityTrack, sceneryBox
    if not cityHere():
      self.skipTest('the city lap is not here')
    t = cityTrack()
    x0, y0, x1, y1 = sceneryBox()
    self.assertTrue(x0 < t.x[0] < x1 and y0 < t.y[0] < y1)
    pieces, pictures = cityScenery()
    for piece in pieces:
      self.assertLess(piece.picture, len(pictures))
      self.assertLess(int(piece.triangles.max()), len(piece.xyz))
      self.assertGreater(piece.uv.min(), -0.01)
      self.assertLess(piece.uv.max(), 1.01)
    corners = numpy.concatenate([piece.xyz for piece in pieces
                                 if not piece.both]).astype(numpy.float64)
    far, _ = cKDTree(numpy.stack((t.x, t.y), 1)).query(corners[:, :2])
    near = corners[far < 2.0][::7]
    terrain = cityGround().terrain
    off = numpy.array([z - terrain.heightAt(float(x), float(y))
                       for x, y, z in near])
    self.assertGreater(len(off), 1000)
    self.assertLess(numpy.percentile(numpy.abs(off), 99.0), 0.01)

  def test_walls(self) -> None:
    """Where the lap's files are: the town's walls ('cityWall') keep 2.5
    m or more clear of the road's middle line all the way round (a
    tree over it is overhead), stand where the houses do (a million
    points of the grid and more), as tall as they stand (under 80 m)."""
    from worQt.phys._city import cityGround, cityHere, cityTrack
    if not cityHere():
      self.skipTest('the city lap is not here')
    t = cityTrack()
    wall = cityGround().wall
    worst = max(wall.beyond(float(x), float(y))[0]
                for x, y in zip(t.x[::5], t.y[::5]))
    self.assertLess(worst, -2.5)
    self.assertGreater(int((wall.inside > 0.0).sum()), 1000000)
    self.assertLess(wall.tallest(), 80.0)
    self.assertGreater(wall.tallest(), 20.0)

  def test_drives_in_town(self) -> None:
    """Where the lap's file is: the city racer pulls away from the start
    and in 25 s is 250 m round or more, on the road all the while
    (within 4 m of its middle: it is drawn 5 m either side), slipping
    under 15 degrees (it slides the 90 degree corners: tyres are
    chaotic), never stranded."""
    from worQt.phys._city import cityCourse, cityGround, cityHere
    from worQt.phys._city import realCarInCity
    from worQt.phys._realdriver import CityDriver
    if not cityHere():
      self.skipTest('the city lap is not here')
    controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                               TuneUp((WheelSetup(),) * len(CORNERS)),
                               DrivetrainControls(), Antilock())
    assembly, states = realCarInCity(controls)
    world = SmallSteps((0.0, 0.0, -9.81), cityGround(), 1.25e-4, 1, 1e-7,
                       'cpu')
    driver = CityDriver(assembly, controls, cityCourse())
    frame, clock, off, slip = 1.0 / 60.0, 0.0, 0.0, 0.0
    for _ in range(round(25.0 / frame)):
      driver.take(states, frame)
      drivetrainWorked(controls.drive, states, frame)
      controls.brakes.worked(controls.line.pressure, assembly, states,
                             frame)
      states = world.advancedAll(assembly, states, frame, clock)
      clock += frame
      speed = driver.speedOf(states)
      self.assertFalse(driver.stranded)
      if speed > 3.0:
        off = max(off, abs(driver.off))
        slip = max(slip, abs(driver.slip))
    self.assertGreater(driver.along, 250.0)
    self.assertLess(off, 4.0)
    self.assertLess(math.degrees(slip), 15.0)
