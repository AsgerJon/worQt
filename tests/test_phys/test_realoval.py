"""
TestRealOval covers the real car on the oval (user, 2026-11-15: "park
the old car by inside the grass on the Dover track, put this car there
instead, have an AI driver take the wheel"): the small steps' ground as
a terrain ('groundAt': a box on a 15 degree slope holds, on a 40 degree
one slides at g (sin - grip cos), each resting square on it; and the
ground's grip as Coulomb has it, a box holding just under its angle and
sliding just over it, at that rate: found 2026-11-15, its corners held it
to twice their grip, 'Touches.gripped'); the oval's safety barrier
('wallBeyond': a box and a ball thrown at it off the front straight's
run-off stop at its face, neither through it; one thrown over its top
goes on); the walker standing on a terrain's slope ('Walker.standingOn'
with the ground: on it resting, not 10 cm over it); the near
look's bound on the terrain's bend, '_bendsOf': nought on a plane, the
jump about a crease); the scene ('realCarOnOval': the real car at the
start on its racing driver's line, leaning with the 9 degree banking,
the old car parked in the infield's grass, its every body fixed, the
walker meeting each); and the racing driver ('RealCarRacer'): it pulls
away, shifts up through the gears and holds its line, and laps the oval
from a standing start. Tolerant: tyres are chaotic.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys import Assembly, Body, BrakeLine, FourthWall, Ground
from worQt.phys import SmallSteps, State, boxShape, rotated
from worQt.phys._drivetrain import DrivetrainControls, drivetrainWorked
from worQt.phys._drivetrain import readingOf
from worQt.phys._laps import LapTimer
from worQt.phys._realcar import Antilock, CHASSIS, CORNERS
from worQt.phys._realcar import RealCarControls
from worQt.phys._realdriver import FORWARD, RealCarRacer
from worQt.phys._realoval import PARKED, ovalGround, parkedCar
from worQt.phys._realoval import parkedFirst, realCarOnOval, startOf
from worQt.phys._rig import TuneUp, WheelSetup
from worQt.phys._small_steps import _bendsOf
from worQt.phys._terrain import Terrain, ovalAcross

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)


def _slope(angle: float) -> Terrain:
  """Returns a plane rising along x at 'angle' (rad), 1 m up at x
  nought, 10 m square in half metre cells."""
  rise = math.tan(angle)
  heights = tuple(tuple(1.0 + rise * (-5.0 + 0.5 * i) for _ in range(21))
                  for i in range(21))
  return Terrain((-5.0, -5.0), 0.5, heights)


def _boxOn(angle: float, grip: float) -> tuple:
  """Returns a 20 cm box set on '_slope(angle)' at x nought, square on
  it, and its world (grip 'grip')."""
  box = Body.of(boxShape(0.2, 0.2, 0.2), 500.0)
  up = (-math.sin(angle), 0.0, math.cos(angle))
  centre = tuple(a + 0.1 * u for a, u in zip((0.0, 0.0, 1.0), up))
  turn = (math.cos(-0.5 * angle), 0.0, math.sin(-0.5 * angle), 0.0)
  ground = Ground(1e5, 1.0, grip, 1e5, 100.0, 0.0, _slope(angle))
  world = SmallSteps(GRAVITY, ground, 2.5e-4, 1, 0.0, 'cpu')
  return Assembly((box,), ()), (State(centre, turn),), world


class TestRealOval(PhysTest):
  """Tests for the real car on the oval (a few minutes on the CPU)."""

  __time_out__ = 1800.0

  def test_holds_on_slope(self) -> None:
    """A box on a 15 degree slope gripping 0.5 holds still on it."""
    assembly, states, world = _boxOn(math.radians(15.0), 0.5)
    after = world.advancedAll(assembly, states, 1.0)
    moved = math.dist(after[0].place, states[0].place)
    self.assertLess(moved, 2e-3)
    self.assertLess(math.hypot(*after[0].velocity), 0.02)

  def test_slides_on_slope(self) -> None:
    """A box on a 40 degree slope gripping 0.5 slides down it at g (sin
    less grip cos), square on it."""
    angle = math.radians(40.0)
    assembly, states, world = _boxOn(angle, 0.5)
    after = world.advancedAll(assembly, states, 0.5)
    along = (math.cos(angle), 0.0, math.sin(angle))
    speed = -sum(a * b for a, b in zip(after[0].velocity, along))
    wanted = 9.81 * (math.sin(angle) - 0.5 * math.cos(angle)) * 0.5
    self.assertAlmostEqual(speed / wanted, 1.0, delta=0.1)
    up = rotated(after[0].turn, (0.0, 0.0, 1.0))
    self.assertAlmostEqual(up[0], -math.sin(angle), delta=0.02)

  def test_coulomb(self) -> None:
    """On level ground under gravity leaning, a box gripping 0.5 (and
    0.3) holds still a tenth under the grip's angle and slides a tenth
    over it at g (sin less grip cos)."""
    box = Body.of(boxShape(0.2, 0.2, 0.2), 500.0)
    for grip in (0.5, 0.3):
      limit = math.atan(grip)
      for angle, slides in ((0.9 * limit, False), (1.1 * limit, True)):
        ground = Ground(1e5, 1.0, grip, 1e5, 100.0, 0.0)
        gravity = (9.81 * math.sin(angle), 0.0, -9.81 * math.cos(angle))
        world = SmallSteps(gravity, ground, 2.5e-4, 1, 0.0, 'cpu')
        after = world.advancedAll(Assembly((box,), ()),
                                  (State((0.0, 0.0, 0.1)),), 0.5)
        speed = math.hypot(*after[0].velocity)
        wanted = 9.81 * (math.sin(angle) - grip * math.cos(angle)) * 0.5
        if slides:
          self.assertAlmostEqual(speed / wanted, 1.0, delta=0.05)
        else:
          self.assertLess(speed, 0.01)

  def test_wall(self) -> None:
    """Thrown at the barrier off the front straight's run-off at 6 m/s,
    a 30 cm box and a 30 cm ball stop at its face (13.3 m out), neither
    through it by a centimetre; a ball thrown at it 4 m over the ground
    (over its 1.2 m top, staying over it) goes on past where it stands.
    (The barrier is all beyond its face below its top, as the springs'
    world's: a ball thrown 2 m up cleared the face, then, the ground
    beyond it rising, dropped under its top and was put back at the
    face.)"""
    from worQt.phys import Sphere
    from worQt.phys._terrain import OVAL_WALL_OUT
    terrain = ovalGround().terrain
    world = SmallSteps(GRAVITY, ovalGround(), 2.5e-4, 1, 0.0, 'cpu')
    box = Body.of(boxShape(0.3, 0.3, 0.3), 2000.0)
    ball = Body.of(Sphere(0.15), 2000.0)
    for body, lift, through in ((box, 0.15, False), (ball, 0.15, False),
                                (ball, 4.0, True)):
      y = -OVAL_WALL_OUT + 1.5
      start = State((0.0, y, terrain.heightAt(0.0, y) + lift + 0.01),
                    (1.0, 0.0, 0.0, 0.0), (0.0, -6.0, 0.0))
      after = world.advancedAll(Assembly((body,), ()), (start,), 0.6)
      reach = after[0].place[1] - 0.15
      if through:
        self.assertLess(reach, -OVAL_WALL_OUT - 0.5)
      else:
        self.assertGreater(reach, -OVAL_WALL_OUT - 0.01)
        self.assertGreater(after[0].velocity[1], -0.5)

  def test_stands_on_slope(self) -> None:
    """The walker's ball resting on a 20 degree slope stands on the
    ground there (the point under it on the slope); 10 cm over it, in
    the air."""
    from worQt.phys._scenes import WALKER
    angle = math.radians(20.0)
    ground = Ground(1e5, 1.0, 0.5, 1e5, 100.0, 0.0, _slope(angle))
    body = WALKER.body()
    up = (-math.sin(angle), 0.0, math.cos(angle))
    for over, stands in ((0.0, True), (0.1, False)):
      centre = tuple(a + (WALKER.radius + over) * u
                     for a, u in zip((1.0, 0.0, 1.0 + math.tan(angle)), up))
      on = WALKER.standingOn(Assembly((body,), ()), (State(centre),), 0,
                             ground)
      if stands:
        self.assertIsNotNone(on)
        self.assertIsNone(on[0])
        self.assertAlmostEqual(on[1][2], ground.terrain.heightAt(
          centre[0], centre[1]), delta=1e-9)
      else:
        self.assertIsNone(on)

  def test_bends(self) -> None:
    """The near look's bound on a terrain's bend: nought on a plane; on
    a crease (level, then rising 1 in 2), the jump (0.5) in the cells
    about it, nought further off."""
    plane = numpy.array(_slope(math.radians(20.0)).heights)
    self.assertLess(_bendsOf(plane, 0.5).max(), 1e-9)
    xs = numpy.arange(21) * 0.5
    crease = numpy.repeat(numpy.maximum(0.0, 0.5 * (xs - 5.0))[:, None],
                          21, 1)
    bends = _bendsOf(crease, 0.5)
    self.assertAlmostEqual(float(bends.max()), 0.5, delta=1e-9)
    self.assertAlmostEqual(float(bends[9, 10]), 0.5, delta=1e-9)
    self.assertEqual(float(bends[2, 10]), 0.0)
    self.assertEqual(float(bends[17, 10]), 0.0)

  def test_scene(self) -> None:
    """The real car starts on its driver's line at the start, leaning
    with the 9 degree banking; the old car stands parked in the infield's
    grass, its every body fixed, the walker meeting each with a shape."""
    controls = _controls()
    assembly, states = realCarOnOval(controls)
    car, parked = parkedCar()
    first = parkedFirst()
    self.assertEqual(len(assembly.bodies), first + len(parked))
    self.assertEqual(assembly.fixed, frozenset(
      range(first, len(assembly.bodies))))
    met = {contact.second for contact in assembly.contacts
           if contact.first == 0}
    for k, body in enumerate(car.assembly.bodies):
      if body.shape is not None:
        self.assertIn(first + k, met)
    terrain = ovalGround().terrain
    self.assertEqual(terrain.heightAt(*PARKED), 0.0)
    self.assertLess(ovalAcross(*PARKED)[0], -10.0)
    for wheel in car.wheels:
      self.assertLess(abs(parked[wheel].place[2] - 0.305), 0.01)
    chassis = states[CHASSIS]
    side = rotated(chassis.turn, (0.0, 1.0, 0.0))
    self.assertAlmostEqual(math.degrees(math.asin(side[2])), -9.0,
                           delta=0.3)
    place, _ = startOf()
    self.assertLess(abs(chassis.place[1] - place[1]), 0.3)
    self.assertLess(abs(chassis.place[0] - place[0]), 3.0)

  def test_pulls_away(self) -> None:
    """From the start the driver pulls away in first, shifts up through
    the gears and holds its line: past 25 m/s in 12 s, in third or
    higher, within 2.5 m of its line, slipping under 5 degrees."""
    racer, run = _race()
    gears, worst, off = set(), 0.0, 0.0
    for states in run(12.0):
      gear = readingOf(racer.controls.drive, states).gear
      gears.add(gear)
      if racer.speedOf(states) > 5.0:
        worst = max(worst, abs(racer.slip))
        off = max(off, abs(racer.off))
    self.assertGreater(racer.speedOf(states), 25.0)
    self.assertTrue({'1', '2', '3'} <= gears, gears)
    self.assertGreaterEqual(FORWARD.index(gear), 2)
    self.assertLess(off, 2.5)
    self.assertLess(math.degrees(worst), 5.0)

  def test_laps(self) -> None:
    """From a standing start the driver laps the oval in under 55 s,
    within 3 m of its line all the way, never stranded."""
    racer, run = _race()
    timer, off = LapTimer(0.0), 0.0
    clock = 0.0
    for states in run(70.0):
      clock += FRAME
      chassis = states[CHASSIS]
      timer.seen(chassis.place[0], chassis.place[1], clock)
      off = max(off, abs(racer.off))
      self.assertFalse(racer.stranded)
      if timer.laps:
        break
    self.assertTrue(timer.laps)
    self.assertLess(timer.laps[0], 55.0)
    self.assertLess(off, 3.0)


def _controls() -> RealCarControls:
  """Returns the real car's controls, as built."""
  return RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                         TuneUp((WheelSetup(),) * len(CORNERS)),
                         DrivetrainControls(), Antilock())


def _race() -> tuple:
  """Returns a racing driver at the wheel of the real car at the oval's
  start (the old car parked), and a function running it 'seconds' on, a
  frame at a time, yielding the states after each."""
  controls = _controls()
  assembly, states = realCarOnOval(controls)
  world = SmallSteps(GRAVITY, ovalGround(), STEP, 1, 1e-7, 'cpu')
  racer = RealCarRacer(assembly, controls)

  def run(seconds: float) -> object:
    """Yields the states after each frame for 'seconds'."""
    nonlocal states
    clock = 0.0
    for _ in range(round(seconds / FRAME)):
      racer.take(states, FRAME)
      drivetrainWorked(controls.drive, states, FRAME)
      controls.brakes.worked(controls.line.pressure, assembly, states,
                             FRAME)
      states = world.advancedAll(assembly, states, FRAME, clock)
      clock += FRAME
      yield states

  return racer, run
