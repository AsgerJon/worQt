"""
TestSmallSteps covers 'SmallSteps', the world stepped in small steps,
its touches kept as rules, all at once, in float32 (user, 2026-11-13:
"we don't need a 'good' solution, we need one that my RTX 5060 is
'good at solving'!", then "build it"): a steel ball let go in a groove
of two steel plates stays put; let go on a steel ramp of 20 degrees it
rolls down as rolling has it (5/7 of g sin 20, its touch not
slipping), however short the steps (places kept as a place and a
shift: float32 alone lost 1.9 % of the way at 0.06 ms steps); five oak
blocks stacked on the floor, each turned 45 degrees on the one under
it, stand, sunk a little (each touch fixing its own depth, each body
taking their average: the weight held by a sink as long as the steps
squared), settled, not creeping; five stacked true, edge on edge,
stand too (each point pushed out through the face it went in through,
not the side it lies on); the car's bearing ('walkingBearing'), in
steps of 'SMALL_BEARING', runs as the springs' world runs it (its
motor up to speed, the gears at their ratio, the balls rolling) and
the shrunk walker walks through its shaft; with its floating bearing a
cylindrical roller bearing (NU, full complement: 'roller'), the
rollers roll between their ribs, the shaft runs up to speed and the
walker walks through; in the void ('voidBearing') the walker walks from
the platform they start on up the ramp, through the shaft and out onto
the platform behind it; and, where there is a GPU, the ramp and the
tower run there as on the CPU.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import SmallSteps, Walker, ballInGroove, ballOnRamp
from worQt.phys import conjugate, cross, dot, groundAt, minus, norm
from worQt.phys import product, rotated, rotorSpinOf, runMotor, scaled
from worQt.phys import rearHub, rollerOf, twistedTower, voidBearing
from worQt.phys import walkingBearing
from worQt.phys._compiled import gpuDevice
from worQt.phys._hub import FIRST_HUB_BALL, HUB_ANGLE, HUB_BALL, HUB_BALLS
from worQt.phys._hub import HUB_GREASE
from worQt.phys._hub import HUB_MIDDLE, HUB_PITCH, HUB_ROWS, hubAxis
from worQt.phys._hub import hubOrbitShare
from worQt.phys._turned import pressesOf
from worQt.phys._scenes import CAR_MIDDLE, CAR_PITCH, FIRST_BALL
from worQt.phys._scenes import FIRST_ROLLER, GEAR_TEETH, NU_HOUSED
from worQt.phys._scenes import CAR_MOTOR_CAN, ROLLER, ROLLERS
from worQt.phys._scenes import STILL_ROLLER
from worQt.phys._scenes import MOTOR_FREE, MOTOR_STALL, PINION_TEETH
from worQt.phys._scenes import PROOF_BALL, RAMP_ANGLE, RAMP_START
from worQt.phys._scenes import RING_UPRIGHT, SHAFT_BACK, SHAFT_INSIDE
from worQt.phys._scenes import SMALL_BEARING, WALKER, YARD_GROUND

from . import PhysTest

FRAME = 1.0 / 60.0
ALONG = (0.0, math.cos(RAMP_ANGLE), math.sin(RAMP_ANGLE))
OUT = (0.0, -math.sin(RAMP_ANGLE), math.cos(RAMP_ANGLE))
SHRUNK = 0.032 / 1.75
STEP = 0.002
AXLE = rotated(RING_UPRIGHT, (0.0, 0.0, 1.0))
#  Rolling on both races: the balls go round at this share of the inner
#  ring's speed.
SHARE = 0.5 * (1.0 - 0.00635 / 0.032 * math.cos(math.radians(30.0)))


def ran(world: SmallSteps, scene: tuple, seconds: float) -> list:
  """The 'ran' function returns how 'scene' (an assembly and its
  states) stands at each whole frame of 'seconds' stepped in 'world',
  a frame (1/60 s) a call, from its start."""
  assembly, states = scene
  out = [states]
  for k in range(round(seconds / FRAME)):
    states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    out.append(states)
  return out


def orbitOf(state: object) -> float:
  """The 'orbitOf' function returns how fast 'state' goes round the
  bearings' axle, rad/s (its reach from the axle square to it)."""
  away = minus(state.place, CAR_MIDDLE)
  away = minus(away, scaled(AXLE, dot(away, AXLE)))
  return dot(cross(away, state.velocity), AXLE) / dot(away, away)


def turnedBy(one: tuple, two: tuple) -> float:
  """The 'turnedBy' function returns how far, rad, the turn 'two' is
  from 'one'."""
  return 2.0 * math.acos(min(1.0, abs(product(two, conjugate(one))[0])))


def hubSpun(speed: float) -> tuple:
  """The 'hubSpun' function returns the rear hub spun to 'speed', rad/s,
  and let turn 1 s in small steps, greased ('HUB_GREASE'): its mean
  speed from 0.5 s on as a share of 'speed', each ball's going round
  as a share of rolling's ('hubOrbitShare'; from 0.5 s on), how far
  any ball strayed from its cage's pocket at worst, rad, and how far
  the hub's middle went at most, m."""
  world = SmallSteps((0.0, 0.0, -9.81), None, SMALL_BEARING, 1,
                     HUB_GREASE)
  assembly, states = rearHub(SHRUNK)
  axis = hubAxis()
  first = states[3]
  states = (states[:3] + (states[3]._replace(spin=scaled(axis, speed)),)
            + states[4:])
  hub, orbits, worst, moved = 0.0, [0.0] * (2 * HUB_BALLS), 0.0, 0.0
  step = 2.0 * math.pi / HUB_BALLS
  for frame in range(500):
    states = world.advancedAll(assembly, states, STEP, STEP * frame)
    moved = max(moved, norm(minus(states[3].place, first.place)))
    if frame >= 250:
      hub += dot(states[3].spin, axis) * STEP
      for j in range(2 * HUB_BALLS):
        ball = states[FIRST_HUB_BALL + j]
        away = minus(ball.place, HUB_MIDDLE)
        away = minus(away, scaled(axis, dot(away, axis)))
        orbits[j] += dot(cross(away, ball.velocity), axis) / dot(
          away, away) * STEP
    for j in range(2 * HUB_BALLS):
      cage = states[4 + j // HUB_BALLS]
      own = rotated(conjugate(cage.turn),
                    minus(states[FIRST_HUB_BALL + j].place, cage.place))
      pocket = -0.5 * math.pi + (j % HUB_BALLS) * step
      off = (math.atan2(own[1], own[0]) - pocket + math.pi) % (
        2.0 * math.pi) - math.pi
      worst = max(worst, abs(off))
  shares = tuple(orbit / (hubOrbitShare() * hub) for orbit in orbits)
  return hub / 0.5 / speed, shares, worst, moved


class TestSmallSteps(PhysTest):
  """Tests for 'SmallSteps' (about 25 s; the first run after the kernels
  change compiles them in it, the CPU's about 10 s, a GPU's, for
  'test_gpu', longer: 30 s killed one mid-compile, 2026-11-13)."""

  __time_out__ = 180.0

  def test_rests_in_groove(self) -> None:
    """Let go touching both plates, the ball sinks in no more than a
    micrometre in a second (0.4 um) and is still, under 0.1 mm/s."""
    frames = ran(SmallSteps(), ballInGroove(), 1.0)
    ball = frames[-1][0]
    self.assertLess(norm(minus(ball.place, frames[0][0].place)), 1e-6)
    self.assertLess(norm(ball.velocity), 1e-4)

  def test_rolls_down_ramp(self) -> None:
    """After 0.5 s the ball has gone 5/7 g sin a t²/2 down the ramp to
    within 0.2 % (0.04 %), its touch slipping under 0.1 mm/s, its middle
    its radius over the face to a micrometre; at 0.125 ms steps alike
    (0.006 %)."""
    want = 0.5 * 5.0 / 7.0 * 9.81 * math.sin(RAMP_ANGLE) * 0.25
    r = PROOF_BALL.shape.radius
    for step in (2.5e-4, 1.25e-4):
      world = SmallSteps((0.0, 0.0, -9.81), None, step)
      ball = ran(world, ballOnRamp(), 0.5)[-1][0]
      went = RAMP_START - dot(ball.place, ALONG)
      self.assertLess(abs(went / want - 1.0), 0.002)
      touch = minus(ball.velocity, cross(ball.spin, tuple(r * x
                                                          for x in OUT)))
      self.assertLess(norm(touch), 1e-4)
      self.assertNear(dot(ball.place, OUT), 0.01 + r, 1e-6)

  def test_tower_stands(self) -> None:
    """Five blocks, each turned 45 degrees on the one under it, after
    2 s: none moved more than 0.2 mm (the top sunk 54 um), none turned
    a milliradian, none moved 5 micrometres in the last second."""
    world = SmallSteps((0.0, 0.0, -9.81), YARD_GROUND)
    frames = ran(world, twistedTower(5), 2.0)
    self.assertTowerStands(frames, 2e-4)

  def test_true_tower_stands(self) -> None:
    """Five blocks stacked true, edge on edge (they sank each into the
    one under it while a point on a side face went out through it),
    after 2 s: none moved more than 0.25 mm (the top sunk 69 um), none
    turned a milliradian, none moved 5 micrometres in the last
    second."""
    world = SmallSteps((0.0, 0.0, -9.81), YARD_GROUND)
    frames = ran(world, twistedTower(5, 0.0), 2.0)
    self.assertTowerStands(frames, 2.5e-4)

  def assertTowerStands(self, frames: list, sunk: float) -> None:
    """Checks the tower in 'frames' (a second's frames at least) as
    'test_tower_stands' says, 'sunk' the most a block may move."""
    first, middle, last = frames[0], frames[len(frames) // 2], frames[-1]
    for one, half, end in zip(first, middle, last):
      self.assertLess(norm(minus(end.place, one.place)), sunk)
      self.assertLess(turnedBy(one.turn, end.turn), 1e-3)
      self.assertLess(norm(minus(end.place, half.place)), 5e-6)

  def test_bearing_rolls(self) -> None:
    """The bearing in steps of 'SMALL_BEARING', its motor run 1 s
    ('runMotor'): from 0.5 s to 1 s the shaft turns at the 2 rad/s its
    motor's free speed gives within 2 % (1.994), no faster; the pinion
    31/16 as far the other way within half a percent (1.00004); the
    steel balls of both bearings go round at the share rolling on both
    races gives within 1 % (1.0006), none nearer another than one and a
    half balls (1.91); the shaft sunk on its balls less than 0.1 mm (17
    um)."""
    world = SmallSteps((0.0, 0.0, -9.81), groundAt(SHRUNK), SMALL_BEARING)
    assembly, states = walkingBearing(SHRUNK)
    first = states
    motor = assembly.motors[0]
    runMotor(motor.drive, MOTOR_STALL, MOTOR_FREE, True)
    balls = range(FIRST_BALL, len(assembly.bodies), 2)
    ring, pinion, orbit, closest = 0.0, 0.0, 0.0, 1.0
    for frame in range(500):
      states = world.advancedAll(assembly, states, STEP, STEP * frame)
      if frame >= 250:
        ring += dot(states[2].spin, AXLE) * STEP
        pinion += rotorSpinOf(motor, states) * STEP
        orbit += sum(orbitOf(states[ball]) for ball in balls) / len(
          balls) * STEP
      for start in (FIRST_BALL, FIRST_BALL + 16):
        some = range(start, start + 16, 2)
        closest = min(closest, min(
          norm(minus(states[one].place, states[other].place))
          for one in some for other in some if one < other))
    speed = -ring / 0.5
    self.assertLess(abs(speed / 2.0 - 1.0), 0.02)
    self.assertLess(speed, 2.0 * 1.002)
    self.assertLess(abs(-pinion / ring / (GEAR_TEETH / PINION_TEETH)
                        - 1.0), 0.005)
    self.assertAlmostEqual(orbit / ring / SHARE, 1.0, 2)
    self.assertGreater(closest, 1.5 * 0.0127)
    self.assertLess(first[2].place[2] - states[2].place[2], 1e-4)

  def test_bearing_walk(self) -> None:
    """Striding on along y at 6 m/s as they feel it ('Walker.strode'),
    the shrunk walker goes up the ramp into the shaft's hole and through
    both bearings, in steps of 'SMALL_BEARING': where they pass the
    pinned one's middle their foot's middle stands its radius over the
    hole's floor to a tenth of a millimetre (3 um under); by 0.9 s they
    are out of its back end (0.77 s)."""
    world = SmallSteps((0.0, 0.0, -9.81), groundAt(SHRUNK), SMALL_BEARING)
    assembly, states = walkingBearing(SHRUNK)
    walker = Walker(WALKER.radius, WALKER.mass, WALKER.eye, 6.0, 12.0,
                    WALKER.legs, WALKER.jump, 20.0, 10.0,
                    60.0).scaled(SHRUNK)
    passed = None
    for frame in range(450):
      states = list(states)
      states[0] = walker.strode(states[0], (0.0, walker.walk, 0.0), STEP)
      states = world.advancedAll(assembly, tuple(states), STEP,
                                 STEP * frame)
      if passed is None and states[0].place[1] > 0.0:
        passed = states[0].place[2]
    floor = CAR_MIDDLE[2] - SHAFT_INSIDE
    self.assertNear(passed, floor + walker.radius, 1e-4)
    self.assertGreater(states[0].place[1], SHAFT_BACK)

  def test_roller_scene(self) -> None:
    """With 'roller', the floating bearing's housing is an NU outer ring
    ('NU_HOUSED') standing still, part of the world as the pinned one's
    ('STILL_ROLLER': no rods hold anything to the world); from
    'FIRST_ROLLER', 'ROLLERS' rollers 11 mm across and as long, their
    middles on the pitch circle, each touching the walker, its outer
    ring, the shaft and its two neighbours, nothing else."""
    assembly, states = walkingBearing(SHRUNK, True)
    self.assertEqual(assembly.fixed, frozenset(STILL_ROLLER))
    self.assertIs(assembly.bodies[8], NU_HOUSED)
    self.assertEqual([leg for leg in assembly.actuators
                      if leg.first is None], [])
    self.assertEqual(len(assembly.bodies), FIRST_ROLLER + ROLLERS)
    for j in range(ROLLERS):
      one = FIRST_ROLLER + j
      self.assertEqual(rollerOf(assembly.bodies[one].shape),
                       (0.5 * ROLLER, 0.5 * ROLLER))
      self.assertAlmostEqual(norm(minus(
        minus(states[one].place, CAR_MIDDLE),
        scaled(AXLE, dot(minus(states[one].place, CAR_MIDDLE), AXLE)))),
        0.5 * CAR_PITCH, 12)
      touching = {contact.first if contact.second == one else
                  contact.second for contact in assembly.contacts
                  if one in (contact.first, contact.second)}
      neighbours = {FIRST_ROLLER + (j - 1) % ROLLERS,
                    FIRST_ROLLER + (j + 1) % ROLLERS}
      self.assertEqual(touching, {0, 8, 2} | neighbours)

  def test_roller_rolls(self) -> None:
    """With 'roller', its motor run 1 s: from 0.5 s to 1 s the shaft
    turns slower than its motor's free 2 rad/s and faster than half that
    (1.338: the full complement's rollers rub each other, their faces
    moving opposite ways where they touch, the drag a cage is for; with
    the velocity pass's sliding grip once capped too low, 1.991); the
    pinion 31/16 as far the other way within half a percent; the pinned
    bearing's balls go round at the share rolling gives within 1 %; the
    rollers at between 0.7 and 1.03 of theirs, (1 - d/D) / 2 (0.81: held
    back by their neighbours, they skid; 1.013 once), none along the
    axle further than its 1 mm from the ribs and their play; the shaft
    sunk on its balls and rollers less than 0.1 mm (8 um)."""
    world = SmallSteps((0.0, 0.0, -9.81), groundAt(SHRUNK), SMALL_BEARING)
    assembly, states = walkingBearing(SHRUNK, True)
    first = states
    motor = assembly.motors[0]
    runMotor(motor.drive, MOTOR_STALL, MOTOR_FREE, True)
    balls = range(FIRST_BALL, FIRST_BALL + 16, 2)
    rollers = range(FIRST_ROLLER, FIRST_ROLLER + ROLLERS)
    ring, pinion, orbit, rolled, along = 0.0, 0.0, 0.0, 0.0, 0.0
    for frame in range(500):
      states = world.advancedAll(assembly, states, STEP, STEP * frame)
      if frame >= 250:
        ring += dot(states[2].spin, AXLE) * STEP
        pinion += rotorSpinOf(motor, states) * STEP
        orbit += sum(orbitOf(states[ball]) for ball in balls) / len(
          balls) * STEP
        rolled += sum(orbitOf(states[one]) for one in rollers) / len(
          rollers) * STEP
      along = max(along, max(abs(dot(minus(states[one].place,
                                           first[one].place), AXLE))
                             for one in rollers))
    speed = -ring / 0.5
    self.assertGreater(speed, 0.5 * 2.0)
    self.assertLess(speed, 2.0 * 1.002)
    self.assertLess(abs(-pinion / ring / (GEAR_TEETH / PINION_TEETH)
                        - 1.0), 0.005)
    self.assertAlmostEqual(orbit / ring / SHARE, 1.0, 2)
    share = 0.5 * (1.0 - ROLLER / CAR_PITCH)
    self.assertGreater(rolled / ring / share, 0.7)
    self.assertLess(rolled / ring / share, 1.03)
    self.assertLess(along, 1.1e-3)
    self.assertLess(first[2].place[2] - states[2].place[2], 1e-4)

  def test_roller_walk(self) -> None:
    """With 'roller', the shrunk walker striding on goes up the ramp,
    through the shaft's hole and both bearings, in steps of
    'SMALL_BEARING': where they pass the pinned one's middle their foot's
    middle stands its radius over the hole's floor to a tenth of a
    millimetre (3 um under); by 0.9 s they are out of its back end
    (0.77 s)."""
    world = SmallSteps((0.0, 0.0, -9.81), groundAt(SHRUNK), SMALL_BEARING)
    assembly, states = walkingBearing(SHRUNK, True)
    walker = Walker(WALKER.radius, WALKER.mass, WALKER.eye, 6.0, 12.0,
                    WALKER.legs, WALKER.jump, 20.0, 10.0,
                    60.0).scaled(SHRUNK)
    passed = None
    for frame in range(450):
      states = list(states)
      states[0] = walker.strode(states[0], (0.0, walker.walk, 0.0), STEP)
      states = world.advancedAll(assembly, tuple(states), STEP,
                                 STEP * frame)
      if passed is None and states[0].place[1] > 0.0:
        passed = states[0].place[2]
    floor = CAR_MIDDLE[2] - SHAFT_INSIDE
    self.assertNear(passed, floor + walker.radius, 1e-4)
    self.assertGreater(states[0].place[1], SHAFT_BACK)

  def test_void(self) -> None:
    """In the void, no ground: the walker starts on the first platform
    (body 7, part of the world, its top at nought), the motor is its can
    alone; striding on along y in steps of 'SMALL_BEARING' they go up
    the ramp, through the shaft's hole and out onto the second platform
    (body 9, its top level with the hole's floor): after 1 s they stand
    on it, their middle their radius over its top (to a tenth of a
    millimetre), past the shaft's back end."""
    assembly, states = voidBearing(SHRUNK)
    self.assertIs(assembly.bodies[4], CAR_MOTOR_CAN)
    self.assertTrue({7, 9} <= assembly.fixed)
    walker = Walker(WALKER.radius, WALKER.mass, WALKER.eye, 6.0, 12.0,
                    WALKER.legs, WALKER.jump, 20.0, 10.0,
                    60.0).scaled(SHRUNK)
    top = max(assembly.bodies[7].placeOf(states[7], point)[2]
              for point in assembly.bodies[7].shape.points)
    self.assertAlmostEqual(top, 0.0, 12)
    world = SmallSteps((0.0, 0.0, -9.81), None, SMALL_BEARING)
    for frame in range(500):
      states = list(states)
      states[0] = walker.strode(states[0], (0.0, walker.walk, 0.0), STEP)
      states = world.advancedAll(assembly, tuple(states), STEP,
                                 STEP * frame)
    floor = CAR_MIDDLE[2] - SHAFT_INSIDE
    self.assertGreater(states[0].place[1], SHAFT_BACK)
    self.assertNear(states[0].place[2], floor + walker.radius, 1e-4)

  def test_hub_scene(self) -> None:
    """The rear hub ('rearHub'): its plate, spindle and platform part of
    the world; every ball (3/8 in, twelve a row) sitting on its two
    raceways exactly, at 35 degrees, leaning apart (the outer touch of
    the outboard row toward the middle), with no play and nothing else
    pressed; each cage's skin at least 0.2 mm off both rings' straight
    faces, in neither (0.238 off their lands)."""
    assembly, states = rearHub(SHRUNK)
    self.assertEqual(assembly.fixed, frozenset((1, 2, 6)))
    self.assertEqual(len(assembly.bodies), FIRST_HUB_BALL + 2 * HUB_BALLS)
    r, rho = 0.5 * HUB_BALL, 0.5 * HUB_PITCH
    lean = math.degrees(HUB_ANGLE)
    for index, sign in ((3, 1.0), (2, -1.0)):
      for middle in (HUB_ROWS, -HUB_ROWS):
        found = pressesOf(assembly.bodies[index].shape.profile, rho,
                          middle, r + 1e-9)
        self.assertEqual(len(found), 1)
        _, nr, nw, depth = found[0]
        self.assertNear(depth, 1e-9, 1e-12)
        angle = math.degrees(math.atan2(nw, -sign * nr))
        self.assertNear(abs(angle), lean, 1e-9)
        self.assertGreater(sign * nw * middle, 0.0)
    nearest = 1.0
    for cage in (4, 5):
      body = assembly.bodies[cage]
      for ring in (2, 3):
        other = assembly.bodies[ring]
        for point, _ in body.shape.skin(0.003):
          own = rotated(conjugate(states[ring].turn), minus(
            body.placeOf(states[cage], point), states[ring].place))
          own = (own[0] + other.centre[0], own[1] + other.centre[1],
                 own[2] + other.centre[2])
          rho, w = math.hypot(own[0], own[1]), own[2]
          for piece in other.shape.profile:
            if piece[0] != 'line':
              continue
            (r0, w0), (r1, w1) = piece[1], piece[2]
            dr, dw = r1 - r0, w1 - w0
            if abs(dr) > 1e-12 and abs(dw) > 1e-12:
              continue
            share = ((rho - r0) * dr + (w - w0) * dw) / (dr * dr + dw * dw)
            if 0.0 <= share <= 1.0:
              length = math.hypot(dr, dw)
              ahead = (rho - r0) * dw / length - (w - w0) * dr / length
              if -1e-3 < ahead < 1e-3:
                nearest = min(nearest, ahead)
    self.assertGreater(nearest, 2e-4)

  def test_hub_finish(self) -> None:
    """The hub unit as drawn ('hubFinishes'): every body but the walker
    in a finish; the hub's and the spindle's runs each one chain, laid
    over their whole profiles (the spindle's axis left out) and over
    the machined wall into the glass; drawn ('finishedRows'), each
    run's triangles wound as its smooth normals face (outward), the
    picture's coordinates with them, their area the solid's mesh's (the
    hub's with the wall's, 2 pi 31 mm x 14 mm), the glass all within
    'FINISH_GLASS' of the axle and nothing else there in the hub but
    the wall."""
    import numpy
    from worQt.phys._hub import FINISH_GLASS, HUB, SPINDLE, hubFinishes
    from worQt.phys.gui._meshes import AXES, SCALE, bodyRows, finishedRows

    def ends(piece: tuple) -> tuple:
      """Returns where a profile's piece starts and ends."""
      if piece[0] == 'line':
        return piece[1], piece[2]
      (cr, cw), radius, a0, a1 = piece[1], piece[2], piece[3], piece[4]
      return ((cr + radius * math.cos(a0), cw + radius * math.sin(a0)),
              (cr + radius * math.cos(a1), cw + radius * math.sin(a1)))

    def length(piece: tuple) -> float:
      """Returns how long a profile's piece is."""
      if piece[0] == 'line':
        return math.dist(piece[1], piece[2])
      return piece[2] * abs(piece[4] - piece[3])

    def area(rows: object) -> float:
      """Returns the area of the triangles in 'rows', cm²."""
      corners = rows[:, :3].reshape(-1, 3, 3)
      return 0.5 * float(numpy.linalg.norm(numpy.cross(
        corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]),
        axis=1).sum())

    assembly, _ = rearHub(SHRUNK)
    finishes = hubFinishes()
    self.assertEqual(set(finishes), set(range(1, len(assembly.bodies))))
    for index, body, wall, axis in ((3, HUB, 0.014, 0.0),
                                    (2, SPINDLE, 0.0, 0.032 + 0.030)):
      self.assertIs(assembly.bodies[index], body)
      runs = finishes[index]
      drawn = 0.0
      for key, pieces in runs:
        for one, two in zip(pieces, pieces[1:]):
          self.assertLess(math.dist(ends(one)[1], ends(two)[0]), 1e-12)
        drawn += sum(length(piece) for piece in pieces)
      whole = sum(length(piece) for piece in body.shape.profile)
      self.assertNear(drawn, whole - axis + wall, 1e-12)
      rows = finishedRows(body, runs, 0.04)
      total = 0.0
      for key, kept in rows.items():
        self.assertEqual(kept.shape[1], 8)
        corners = kept[:, :3].reshape(-1, 3, 3)
        facing = numpy.cross(corners[:, 1] - corners[:, 0],
                             corners[:, 2] - corners[:, 0])
        normals = kept[:, 3:6].reshape(-1, 3, 3).sum(axis=1)
        sizes = numpy.linalg.norm(facing, axis=1)
        real = sizes > 1e-9
        self.assertGreater(float(((facing[real] * normals[real]).sum(
          axis=1) / sizes[real]).min()), 0.99)
        total += area(kept)
        if index == 3:
          own = kept[:, :3] / SCALE @ AXES + numpy.array(body.centre)
          rho = numpy.hypot(own[:, 0], own[:, 1])
          if key == 'glass':
            self.assertLess(float(rho.max()), FINISH_GLASS + 1e-6)
          else:
            self.assertGreater(float(rho.min()), FINISH_GLASS - 1e-6)
      extra = 2.0 * math.pi * (SCALE * FINISH_GLASS) * (SCALE * wall)
      self.assertNear(total, area(bodyRows(body, None)[0]) + extra, 1e-2)

  def test_hub_rests(self) -> None:
    """Let be 1 s in small steps, greased ('HUB_GREASE'), the hub (4.6
    kg on balls of 3.6 g) goes nowhere: within 0.02 mm of where it was
    (5 um; ungreased 55: its balls' touches, each at nought on both
    raceways, fought in step), turned no more than a milliradian
    (0.11; ungreased 0.69). It rocks on its balls by the solver's
    noise, no faster than 0.15 rad/s (0.072; ungreased 0.37), 0.05 on
    the mean (0.025; 0.063): a real unit, preloaded, is still, and
    rigid touches cannot be preloaded (user, 2026-11-14: "we chill out
    with this test"; tried and not kept: Gauss and Seidel's way,
    springy steel, bigger balls, phys CLAUDE.md). Each cage sags onto
    the spindle's land, its middle no further off the axle than its
    0.24 mm from the land, to 10 um (0.239: it rests on the ring, not
    in it; let pass through, 0.33)."""
    world = SmallSteps((0.0, 0.0, -9.81), None, SMALL_BEARING, 1,
                       HUB_GREASE)
    assembly, states = rearHub(SHRUNK)
    axis = hubAxis()
    first, moved, turned, off, spins = states, 0.0, 0.0, 0.0, []
    for frame in range(500):
      states = world.advancedAll(assembly, states, STEP, STEP * frame)
      moved = max(moved, norm(minus(states[3].place, first[3].place)))
      turned = max(turned, turnedBy(first[3].turn, states[3].turn))
      spins.append(norm(states[3].spin))
      for cage in (4, 5):
        away = minus(states[cage].place, HUB_MIDDLE)
        off = max(off, norm(minus(away, scaled(axis, dot(away, axis)))))
    self.assertLess(moved, 2e-5)
    self.assertLess(turned, 1e-3)
    self.assertLess(max(spins), 0.15)
    self.assertLess(sum(spins) / len(spins), 0.05)
    self.assertLess(off, 2.5e-4)

  def test_hub_spins(self) -> None:
    """Spun to 10 rad/s (a walking pace on a car's wheel), greased, the
    hub turns on: from 0.5 s to 1 s at 10 rad/s within a percent
    (0.995: the grease's jostling, a micrometre a step, 8 mm/s, drags it
    a little; ungreased 0.999); every ball goes round at the share
    rolling on both raceways gives, (1 + d cos a / D) / 2, within 10 %
    (0.93 to 0.96: the jostling drags them behind at this pace;
    ungreased 1.005 to 1.026); every ball stays within half a degree of
    its cage's pocket all the while (0.25: the cage goes round with
    them, riding on the spindle's land)."""
    kept, shares, worst, _ = hubSpun(10.0)
    self.assertLess(abs(kept - 1.0), 0.01)
    for share in shares:
      self.assertLess(abs(share - 1.0), 0.1)
    self.assertLess(worst, math.radians(0.5))

  def test_hub_spins_fast(self) -> None:
    """Spun to 220 rad/s (250 km/h on a 205/55 R16, a car's top speed;
    user, 2026-11-14: "an extra harder test at higher speed"), greased,
    the hub turns on: from 0.5 s to 1 s within a percent (0.9987);
    every ball goes round within 3 % of rolling's share (0.986 to
    0.996), stays within 3 degrees of its pocket (2.1), and the hub
    within 0.1 mm of where it was (38 um). Past it the wheel stops
    wheeling ("at what speed this wheel stops wheeling"): the balls
    fall behind (0.91 of rolling at 260 rad/s and at 400, 7 degrees off
    their pockets there), at 700 they leave their pockets, the hub 0.7
    mm off and 6 % slower, at 1500 it flies apart. The step's limit, not
    the bearing's: how fast the balls go round hangs on how far the hub
    turns in a step (ungreased: 1.07 at 140 rad/s, 0.98 at half the
    step; 0.77 at 340, 1.07 at half the step); past about 0.03 rad a
    step (240 rad/s in steps of 'SMALL_BEARING') they skid."""
    kept, shares, worst, moved = hubSpun(220.0)
    self.assertLess(abs(kept - 1.0), 0.01)
    for share in shares:
      self.assertLess(abs(share - 1.0), 0.03)
    self.assertLess(worst, math.radians(3.0))
    self.assertLess(moved, 1e-4)

  def test_gpu(self) -> None:
    """On a GPU, where there is one, the ramp after 0.5 s and the
    tower after 1 s end as on the CPU, to 10 micrometres."""
    device = gpuDevice()
    if device is None:
      self.skipTest('no GPU here')
    for scene, seconds, ground in ((ballOnRamp, 0.5, None),
                                   (twistedTower, 1.0, YARD_GROUND)):
      ends = []
      for where in ('cpu', device):
        world = SmallSteps((0.0, 0.0, -9.81), ground, 2.5e-4, 1, 0.0,
                           where)
        made = scene() if scene is ballOnRamp else scene(5)
        ends.append(ran(world, made, seconds)[-1])
      for one, two in zip(*ends):
        self.assertLess(norm(minus(one.place, two.place)), 1e-5)
