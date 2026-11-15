"""
TestAxle covers the steering (user, 2026-11-14: "The steering wheel
shall be designated as a point that can receive rotational input
through the fourth wall. From the steering wheel, follow the
traditional and real implementation"): the player's hands
('TurnPoint', a fourth wall point) turn a column on a hinge to the
angle asked, across turns (to a ten-thousandth of a radian), and its
pinion ('RackAndPinion') slides a rack on a sliding joint its pitch
radius a radian (to a hundredth of a millimetre). On the steering bench
('_axle.steeringBench': the column, rack, tie rods, knuckles on their
kingpins, the Soufflé wheels on the ground), the wheel turned at 360
degrees a second: a quarter turn left steers the road wheels left 5.4
and 5.2 degrees (the inner more: Ackermann); full lock (540 degrees)
slides the rack its 75 mm, the inner wheel 44 degrees, the outer 31
(Ackermann's 32, to 2); asked past it, the hands give at their most
against the rack's stop (the wheel under 600 degrees, the rack within
4 mm past its travel); straight again, straight (to a tenth of a
degree). The springs' world
refuses both.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, BrakeLine, FourthWall, Hinge
from worQt.phys import RackAndPinion, Slide, SmallSteps, State, TurnPoint
from worQt.phys import World, boxShape, cylinderShape, rotated
from worQt.phys._axle import KINGPIN_Y, PINION, TRAVEL, WHEELBASE
from worQt.phys._axle import steeringBench
from worQt.phys._carcass import TYRE_YARD

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 2.5e-4
GRAVITY = (0.0, 0.0, -9.81)
RATE = 2.0 * math.pi


def roadAngle(state: State) -> float:
  """The 'roadAngle' function returns how far a knuckle in 'state'
  steers its wheel left of straight ahead (+x), degrees."""
  ahead = rotated(state.turn, (1.0, 0.0, 0.0))
  return math.degrees(math.atan2(ahead[1], ahead[0]))


class TestAxle(PhysTest):
  """Tests for the steering (about 40 s on the CPU)."""

  __time_out__ = 180.0

  def test_rack_and_pinion(self) -> None:
    """The hands turn a column (on a hinge) to 1 rad, then to minus one
    and a half turns, each to a ten-thousandth of a radian; its pinion
    slides the rack (on a sliding joint) its pitch radius a radian, to
    a hundredth of a millimetre; straight again, back."""
    column = Body.of(cylinderShape(0.02, 0.6, 16), 7850.0)
    rack = Body.of(boxShape(0.6, 0.03, 0.03), 7850.0)
    wall = FourthWall(0.0)
    y, x = (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)
    assembly = Assembly((column, rack), (
      Hinge(None, (0.0, 0.0, 1.0), y, 0, (0.0, 0.0, 0.0), y),
      Slide(None, (0.0, 0.0, 0.5), x, 1, (0.0, 0.0, 0.0), x),
      RackAndPinion(0, y, 1, x, None, PINION),
      TurnPoint(0, None, y, wall)))
    world = SmallSteps(GRAVITY, None, STEP, 1, 1e-7, 'cpu')
    states = (State((0.0, 0.0, 1.0)), State((0.0, 0.0, 0.5)))
    clock = 0.0
    for asked in (1.0, -3.0 * math.pi, 0.0):
      wall.value = asked
      for _ in range(60):
        states = world.advancedAll(assembly, states, FRAME, clock)
        clock += FRAME
      turned = world.turnsOf(assembly)[0]
      self.assertNear(turned, asked, 1e-4)
      self.assertNear(states[1].place[0], PINION * asked, 1e-5)

  def test_steers(self) -> None:
    """On the steering bench, the wheel turned at 360 degrees a second:
    a quarter turn left steers the road wheels left 5.4 and 5.2
    degrees (the inner more); full lock slides the rack its travel (to
    a millimetre), the inner wheel 44 degrees, the outer within 2
    degrees of where Ackermann puts it; asked past lock the hands give
    (the wheel short of 600 degrees, the rack within 4 mm past its
    travel); straight again, straight (to a tenth of a degree: the
    tyres' treads, standing, keep a little stretch)."""
    wall = FourthWall(0.0)
    assembly, states = steeringBench(wall, BrakeLine(0.0))
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
    clock = [0.0]

    def turned(asked: float, seconds: float, states: tuple) -> tuple:
      """Returns 'states' after turning the wheel toward 'asked' at
      'RATE' for 'seconds'."""
      for _ in range(round(seconds / FRAME)):
        step = RATE * FRAME
        wall.value += max(-step, min(step, asked - wall.value))
        states = world.advancedAll(assembly, states, FRAME, clock[0])
        clock[0] += FRAME
      return states

    states = turned(0.5 * math.pi, 1.0, states)
    left, right = roadAngle(states[4]), roadAngle(states[5])
    self.assertNear(left, 5.39, 0.1)
    self.assertNear(right, 5.24, 0.1)
    self.assertGreater(left, right)
    states = turned(3.0 * math.pi, 1.5, states)
    self.assertNear(states[3].place[1], -TRAVEL, 1e-3)
    left, right = roadAngle(states[4]), roadAngle(states[5])
    self.assertNear(left, 44.0, 1.0)
    track = 2.0 * KINGPIN_Y
    outer = math.degrees(math.atan(1.0 / (
      1.0 / math.tan(math.radians(left)) + track / WHEELBASE)))
    self.assertNear(right, outer, 2.0)
    states = turned(4.0 * math.pi, 1.0, states)
    self.assertLess(world.turnsOf(assembly)[0], math.radians(600.0))
    self.assertLess(abs(states[3].place[1]), TRAVEL + 4e-3)
    states = turned(0.0, 2.5, states)
    self.assertLess(abs(roadAngle(states[4])), 0.1)
    self.assertLess(abs(roadAngle(states[5])), 0.1)

  def test_springs_refuse(self) -> None:
    """The springs' world refuses a fourth wall point that turns and a
    rack and pinion."""
    column = Body.of(cylinderShape(0.02, 0.6, 16), 7850.0)
    y = (0.0, 1.0, 0.0)
    world = World(GRAVITY, 1e-3, None)
    start = (State((0.0, 0.0, 1.0)), State((0.0, 0.0, 0.5)))
    for connection in (TurnPoint(0, None, y, FourthWall()),
                       RackAndPinion(0, y, 1, y, None, PINION)):
      with self.assertRaises(ValueError):
        world.advancedAll(Assembly((column, column), (connection,)),
                          start, 0.01)
