"""
TestCity covers the real car in town (user, 2026-11-15: uncannyball's
lap of central Copenhagen, 'previews/uncannyball_readme.md'): a road
laid along a line read from its OpenCRG file ('_crg.readCrg': a circle
written here, its rows on it, its heights as written), laid onto a
regular terrain ('crgTerrain': on the road within a centimetre, its
slope the ground's), as a
course ('_course.CrgCourse': a point's place along and right of the
middle and back, to a centimetre); and, where the lap's file is
('_city.CITY_TRACK', not in git), the palace square clear of the road
('amalienborg') and the city racer ('CityDriver') pulling away and
keeping to its line.
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
from worQt.phys._crg import crgTerrain, readCrg
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

  def test_square(self) -> None:
    """Where the lap's file is: the palace square's every part stands
    clear of the road's middle by more than 7 m, the statue more than
    25 m (the lap's hairpin round it)."""
    from worQt.phys._city import CITY_TRACK, amalienborg, cityTrack
    if not os.path.isfile(os.path.normpath(CITY_TRACK)):
      self.skipTest('the city lap is not here')
    t = cityTrack()
    mx, my = t.x[:-1], t.y[:-1]
    for key, (length, width, _), (x, y, _), heading in amalienborg():
      c, s = math.cos(heading), math.sin(heading)
      u = numpy.abs((mx - x) * c + (my - y) * s) - 0.5 * length
      v = numpy.abs(-(mx - x) * s + (my - y) * c) - 0.5 * width
      gap = numpy.hypot(numpy.maximum(u, 0.0), numpy.maximum(v, 0.0))
      self.assertGreater(gap.min(), 25.0 if key in ('pedestal', 'bronze')
                         else 7.0, key)

  def test_drives_in_town(self) -> None:
    """Where the lap's file is: the city racer pulls away from the start
    and in 25 s is 250 m round or more, on the road all the while
    (within 4 m of its middle: it is drawn 5 m either side), slipping
    under 15 degrees (it slides the 90 degree corners: tyres are
    chaotic), never stranded."""
    from worQt.phys._city import CITY_TRACK, cityCourse, cityGround
    from worQt.phys._city import realCarInCity
    from worQt.phys._realdriver import CityDriver
    if not os.path.isfile(os.path.normpath(CITY_TRACK)):
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
