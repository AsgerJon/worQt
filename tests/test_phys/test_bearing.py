"""
TestBearing covers the hjulleje at a car's size ('walkingBearing'): two
four-point ball bearings with 12.7 mm steel balls on a 64 mm pitch
circle and PA66 spacer balls between them, carrying a hollow shaft as a
beam on a pin and a roller (user, 2026-11-13: "put a hollow shaft that
is tall enough for the player to walk through. in one end put teeth
outside of the shaft and put a motor with a tooth wheel to drive", then
"let's length the shaft and add the other bearing"): the pinned one's
outer ring held every way in its housing, the roller one's free to
slide along the axle; their inner rings pressed on the shaft; a walker
shrunk to walk through it. Each is as big as a car's (outside 88 mm,
bore 40 mm); no cage, nothing unseen: balls and spacers alternate round
each circle, each touching both rings and its neighbours, and a spacer
always lies between two steel balls; the gear is keyed on the shaft,
the pinion on the motor's output shaft, the motor and the ramp stand on
supports of their own. Run, the motor turns its pinion, the pinion the
gear the other way at the ratio of their teeth, the shaft toward the
speed the motor's free speed gives, and the balls go round at the
share rolling on both races gives, (1 - r/rho cos a) / 2 (the inner
race's contacts are r cos a inside their middles); the spacers slide
without friction. The walker, shorter than the shaft's hole, walks up
the ramp, through the hole on its floor, through both bearings, and
out. Stepped as the walk window steps it (its contacts' steps and the
ground's swing twice the reference's), the motor's run is the same.
'driven' turns a body toward a speed no faster than its torque lets
it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Body, State, Walker, World, boxShape, cross, dot
from worQt.phys import driven, scaled
from worQt.phys import groundAt, minus, norm, rotated, rotorSpinOf
from worQt.phys import runMotor, walkingBearing
from worQt.phys._world import FULL, Fidelity
from worQt.phys._scenes import BEARING_FIDELITY, CAR_INNER, CAR_MIDDLE
from worQt.phys._scenes import CAR_OUTER
from worQt.phys._scenes import CAR_SHAFT, FIRST_BALL, GEAR_TEETH
from worQt.phys._scenes import MOTOR_FREE, MOTOR_LENGTH, MOTOR_STALL
from worQt.phys._scenes import PINION_TEETH
from worQt.phys._scenes import RING_UPRIGHT, SHAFT_BACK, SHAFT_FRONT
from worQt.phys._scenes import SHAFT_INSIDE, STILL, WALKER

from . import PhysTest

SHRUNK = 0.032 / 1.75
STEP = 0.002
AXLE = rotated(RING_UPRIGHT, (0.0, 0.0, 1.0))
#  Rolling on both races: the balls go round at this share of the inner
#  ring's speed (ball radius 6.35 mm on a pitch radius of 32 mm, contact
#  angle 30 deg).
SHARE = 0.5 * (1.0 - 0.00635 / 0.032 * math.cos(math.radians(30.0)))


def orbitOf(state: State) -> float:
  """The 'orbitOf' function returns how fast 'state' goes round the
  bearings' axle, rad/s (its reach from the axle square to it)."""
  away = minus(state.place, CAR_MIDDLE)
  away = minus(away, scaled(AXLE, dot(away, AXLE)))
  return dot(cross(away, state.velocity), AXLE) / dot(away, away)


class TestBearing(PhysTest):
  """Tests for 'walkingBearing' and 'driven'."""

  def test_size(self) -> None:
    """The rings are a car hub bearing's: outside 88 mm, bore 40 mm,
    18 mm wide; the balls 12.7 mm steel, the spacers 12.2 mm PA66. The
    shaft's hole is 36.3 mm across, the walker (1.75 m tall at full
    size) more than 4 mm shorter; the shaft, both bearings' inner rings
    on it, as heavy as the two rings and the tube are of steel
    (930 g)."""
    assembly, _ = walkingBearing(SHRUNK)
    _, outside, low, high = CAR_OUTER.shape.bounds()
    bore = CAR_INNER.shape.bounds()[0]
    self.assertAlmostEqual(2.0 * outside, 0.0877, 3)
    self.assertAlmostEqual(2.0 * bore, 0.0403, 3)
    self.assertAlmostEqual(high - low, 0.018, 9)
    ball = assembly.bodies[FIRST_BALL]
    spacer = assembly.bodies[FIRST_BALL + 1]
    self.assertAlmostEqual(2.0 * ball.shape.radius, 0.0127, 12)
    self.assertAlmostEqual(2.0 * spacer.shape.radius, 0.0122, 12)
    self.assertAlmostEqual(ball.mass / ball.shape.volume(), 7850.0, 6)
    self.assertAlmostEqual(spacer.mass / spacer.shape.volume(), 1140.0, 6)
    self.assertAlmostEqual(2.0 * SHAFT_INSIDE, 0.0363, 4)
    self.assertGreater(2.0 * SHAFT_INSIDE - 1.75 * SHRUNK, 0.004)
    tube = math.pi * (bore * bore - SHAFT_INSIDE * SHAFT_INSIDE) * (
        SHAFT_FRONT + SHAFT_BACK)
    self.assertAlmostEqual(CAR_SHAFT.mass / (
        7850.0 * (2.0 * CAR_INNER.shape.volume() + tube)), 1.0, 9)

  def test_scene(self) -> None:
    """The shrunk walker; the pinned bearing's housing, the motor, the
    ramp and both pedestals part of the world ('Fixed', 'STILL'); the
    roller bearing's housing on five rods square to the axle from the
    world; the gear keyed on the shaft (a tie and three rods), the
    pinion on the motor's output shaft (a tie and two rods); one motor,
    the motor's on its pinion; no springs (no cage); the gear touching
    the pinion, their teeth with no common factor; from 'FIRST_BALL',
    for each bearing, balls and spacers in turn, eight of each, each
    touching both its rings, its two neighbours and the walker."""
    assembly, _ = walkingBearing(SHRUNK)
    self.assertAlmostEqual(assembly.bodies[0].shape.radius,
                           WALKER.radius * SHRUNK, 12)
    self.assertEqual(assembly.fixed, frozenset(STILL))
    self.assertEqual(sorted(leg.second for leg in assembly.actuators
                            if leg.first is None), [8] * 5)
    self.assertEqual(sorted((rod.first, rod.second)
                            for rod in assembly.actuators
                            if rod.first is not None),
                     [(2, 3)] * 3 + [(4, 5)] * 2)
    self.assertEqual(sorted((tie.first, tie.second)
                            for tie in assembly.ties), [(2, 3), (4, 5)])
    self.assertEqual([(motor.first, motor.second)
                      for motor in assembly.motors], [(4, 5)])
    self.assertEqual(len(assembly.springs), 0)
    self.assertIn((3, 5), {(contact.first, contact.second)
                           for contact in assembly.contacts})
    self.assertEqual(math.gcd(GEAR_TEETH, PINION_TEETH), 1)
    count = 16
    self.assertEqual(len(assembly.bodies) - FIRST_BALL, 2 * count)
    for first, housing in ((FIRST_BALL, 1), (FIRST_BALL + count, 8)):
      for j in range(count):
        one = first + j
        touching = {contact.first if contact.second == one else
                    contact.second for contact in assembly.contacts
                    if one in (contact.first, contact.second)}
        neighbours = {first + (j - 1) % count, first + (j + 1) % count}
        self.assertEqual(touching, {0, housing, 2} | neighbours)
        self.assertEqual(assembly.bodies[one].mass > 0.005, j % 2 == 0)

  def test_solid(self) -> None:
    """The supports are solid where they meet: the outer ring stands in
    its housing (one solid with it, its bore the ring's, 52 mm out), the
    axle 100 mm over the floor (user: "elevate the rings above the
    ground"), the housing's bottom 48 mm up on its pedestal (the foot
    10 mm high, 0.5 mm over the floor), the pedestal's cheeks meeting
    the housing within its wall (no nearer the axle than its 8 mm of
    steel); the motor's pedestal stands 0.5 mm over the floor; the
    pinion's stub reaches the motor's face."""
    assembly, states = walkingBearing(SHRUNK)
    housed, pedestal = assembly.bodies[1], assembly.bodies[7]
    self.assertAlmostEqual(housed.shape.bounds()[0],
                           CAR_OUTER.shape.bounds()[0], 12)
    rim = housed.shape.bounds()[1]
    self.assertAlmostEqual(rim, CAR_OUTER.shape.bounds()[1] + 0.008, 12)
    self.assertAlmostEqual(CAR_MIDDLE[2], 0.1, 12)
    self.assertAlmostEqual(CAR_MIDDLE[2] - rim, 0.0481, 4)
    heights = [point[2] for point in pedestal.shape.points]
    self.assertAlmostEqual(min(heights), 0.0005, 12)
    for x, _, z in pedestal.shape.points:
      if z > 0.0101:
        self.assertGreater(math.hypot(x, z - CAR_MIDDLE[2]),
                           CAR_OUTER.shape.bounds()[1] + 0.0039)
    motor, place = assembly.bodies[4], states[4]
    lowest = min(motor.placeOf(place, point)[2]
                 for point in motor.shape.points)
    self.assertAlmostEqual(lowest, 0.0005, 9)
    pinion, face = assembly.bodies[5], 0.5 * MOTOR_LENGTH
    reach = max(pinion.placeOf(states[5], point)[1]
                for point in pinion.shape.points)
    near = min(motor.placeOf(place, point)[1]
               for point in motor.shape.points
               if abs(point[2] - face) < 1e-12)
    self.assertAlmostEqual(reach, near, 9)

  def test_rolls(self) -> None:
    """Run ('runMotor': its torque worked out at every step), the motor
    turns the shaft, from 0.3 s to 0.6 s, at the 2 rad/s its free speed
    gives within 2 %, no faster (the spacers slide without friction, the
    balls roll: 1.99 rad/s; with the spacers' rubbing it was 1.71 and
    slowing); meanwhile the pinion turns 31/16 as far the other way,
    within half a percent (teeth cannot slip), the steel balls of both
    bearings go round at the share rolling on both races gives within
    1 %, and in each a spacer always lies between two steel balls (none
    nearer another than one and a half balls)."""
    self.assertRolls(FULL)

  def test_rolls_live(self) -> None:
    """Stepped as the walk window steps it ('BEARING_FIDELITY': the
    contacts' steps and the ground's swing twice the reference's), the
    motor's run is as 'test_rolls' has it."""
    self.assertRolls(BEARING_FIDELITY)

  def assertRolls(self, fidelity: Fidelity) -> None:
    """Runs the motor 0.6 s in a world stepped as 'fidelity' says and
    checks the ring, the gears and the balls as 'test_rolls' says."""
    world = World((0.0, 0.0, -9.81), 1e-3, groundAt(SHRUNK), None, True,
                  None, 'cpu', fidelity)
    assembly, states = walkingBearing(SHRUNK)
    motor = assembly.motors[0]
    runMotor(motor.drive, MOTOR_STALL, MOTOR_FREE, True)
    balls = range(FIRST_BALL, len(assembly.bodies), 2)
    ring, pinion, orbit, time, closest = 0.0, 0.0, 0.0, 0.0, 1.0
    for frame in range(300):
      states = world.advancedAll(assembly, states, STEP, time)
      time += STEP
      if frame >= 150:
        ring += dot(states[2].spin, AXLE) * STEP
        pinion += rotorSpinOf(motor, states) * STEP
        orbit += sum(orbitOf(states[ball]) for ball in balls) / len(
          balls) * STEP
      for first in (FIRST_BALL, FIRST_BALL + 16):
        some = range(first, first + 16, 2)
        closest = min(closest, min(
          norm(minus(states[one].place, states[other].place))
          for one in some for other in some if one < other))
    speed = -ring / 0.3
    self.assertLess(abs(speed / 2.0 - 1.0), 0.02)
    self.assertLess(speed, 2.0 * 1.002)
    self.assertLess(abs(-pinion / ring / (GEAR_TEETH / PINION_TEETH)
                        - 1.0), 0.005)
    self.assertAlmostEqual(orbit / ring / SHARE, 1.0, 2)
    self.assertGreater(closest, 1.5 * 0.0127)

  def test_walks_through(self) -> None:
    """Striding on along y at 6 m/s as they feel it (a game's player,
    'Walker.strode') from where they start (the motor still), the
    shrunk walker goes up the ramp into the shaft's hole, through the
    roller bearing and the pinned one: where they pass the pinned one's
    middle their foot's middle stands its radius over the hole's floor
    (to a tenth of a millimetre); by 0.9 s they are out of its back
    end."""
    world = World((0.0, 0.0, -9.81), 1e-3, groundAt(SHRUNK), None, True)
    assembly, states = walkingBearing(SHRUNK)
    walker = Walker(WALKER.radius, WALKER.mass, WALKER.eye, 6.0, 12.0,
                    WALKER.legs, WALKER.jump, 20.0, 10.0,
                    60.0).scaled(SHRUNK)
    passed, time = None, 0.0
    for _ in range(450):
      states = list(states)
      states[0] = walker.strode(states[0], (0.0, walker.walk, 0.0), STEP)
      states = world.advancedAll(assembly, tuple(states), STEP, time)
      time += STEP
      if passed is None and states[0].place[1] > 0.0:
        passed = states[0].place[2]
    floor = CAR_MIDDLE[2] - SHAFT_INSIDE
    self.assertNear(passed, floor + walker.radius, 1e-4)
    self.assertGreater(states[0].place[1], SHAFT_BACK)

  def test_driven(self) -> None:
    """A box turned toward 2 rad/s about the upright by 10 N m speeds
    up by torque x time over its inertia each tenth of a second, then
    turns at 2 rad/s exactly, about the upright only."""
    box = Body.of(boxShape(1.0, 0.5, 0.2), 1000.0)
    up = (0.0, 0.0, 1.0)
    each = 10.0 * 0.1 / box.inertia[2][2]
    state = State((0.0, 0.0, 0.0))
    for k in range(1, 4):
      state = driven(box, state, up, 2.0, 10.0, 0.1)
      self.assertAlmostEqual(state.spin[2], k * each, 12)
    for _ in range(30):
      state = driven(box, state, up, 2.0, 10.0, 0.1)
    self.assertNear(state.spin, (0.0, 0.0, 2.0), 1e-12)
    self.assertNear(state.velocity, (0.0, 0.0, 0.0), 0.0)
    self.assertNear(cross(state.spin, up), (0.0, 0.0, 0.0), 1e-12)
