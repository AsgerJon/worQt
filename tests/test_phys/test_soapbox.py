"""
TestSoapbox covers the soapbox ('_soapbox.soapbox'; user, 2026-11-14:
"Here's our first car: rolling down hill picking up speed until it can
complete a loop de loop... steering on front wheel only. breaks on all
four wheels. no drive train") and its tyres on a track's planks
('WHEEL_PIECES'): on a deck of planks it rides as on the ground (to a
millimetre), as built (each wheel's middle to 3 mm in the car's frame);
steered left standing its front wheels turn left 8 to 15 degrees, its
rears not (half a degree); tuned up (camber -2 all round) it stands so
(to half a degree); its brakes hold it on the ramp (a centimetre in a
second); let go it rolls down the ramp over its planks' joints without
a jolt (its tyres' load 0.75 to 0.97 of its weight on the slope), round
the bend into the flat and, its line kept by the driver's hands
('LineKeeper'), round the loop (over its top upside down, its tyres
still pressed, a fifth of its weight or more; at most 6 g) and out onto
the ground beside where it went in, upright, the driver still in the
tub, at 10 m/s or more; braked there it stops. Tolerant throughout:
tyres are chaotic.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Body, BrakeLine, FourthWall, SmallSteps, boxShape
from worQt.phys import conjugate, minus, norm, rotated
from worQt.phys._carcass import TYRE_YARD
from worQt.phys._rig import HUB_HEIGHT, TuneUp, WheelSetup
from worQt.phys._soapbox import CHASSIS, CORNERS, FIRST_CORNER, HOLD
from worQt.phys._soapbox import SEAT, LineKeeper, SoapboxControls
from worQt.phys._soapbox import soapbox

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)
FLAT = ((20.0, 10.0, 0.0), (1.0, 0.0, 0.0, 0.0))


def worldOf() -> SmallSteps:
  """Returns the soapbox's world: small steps on the CPU, greased."""
  return SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')


def ownOf(assembly: object, states: tuple, point: tuple) -> tuple:
  """Returns where 'point' (in the world) is in the car's frame."""
  body, state = assembly.bodies[CHASSIS], states[CHASSIS]
  own = rotated(conjugate(state.turn), minus(point, state.place))
  return tuple(a + b for a, b in zip(own, body.centre))


def wheelsOf(states: tuple) -> list:
  """Returns each wheel's state, in 'CORNERS' order."""
  return [states[FIRST_CORNER + 6 * c + 3] for c in range(len(CORNERS))]


class TestSoapbox(PhysTest):
  """Tests for the soapbox (about four minutes on the CPU)."""

  __time_out__ = 1500.0

  def ran(self, world: SmallSteps, assembly: object, states: tuple,
          seconds: float, clock: list, each: object = None) -> tuple:
    """Returns 'states' 'seconds' on, a frame at a time ('clock' its
    time, moved on), 'each' (if any) called with them before every
    frame."""
    for _ in range(round(seconds / FRAME)):
      if each is not None:
        each(states)
      states = world.advancedAll(assembly, states, FRAME, clock[0])
      clock[0] += FRAME
    return states

  def test_deck(self) -> None:
    """On a deck of planks half a metre up it rides as on the ground, to
    a millimetre; there each wheel's middle is as built in the car's
    frame, to 3 mm."""
    deck = Body.of(boxShape(8.0, 4.0, 0.06).moved(
      (19.0, 10.0, 0.47), (1.0, 0.0, 0.0, 0.0)), 600.0)
    heights = []
    for start, track in ((FLAT, None),
                         (((20.0, 10.0, 0.5), FLAT[1]), deck)):
      assembly, states = soapbox(SoapboxControls(BrakeLine(0.0),
                                                 FourthWall(0.0)),
                                 start, track)
      states = self.ran(worldOf(), assembly, states, 0.8, [0.0])
      heights.append(states[CHASSIS].place[2] - start[0][2])
      for wheel in wheelsOf(states):
        self.assertNear(ownOf(assembly, states, wheel.place)[2],
                        HUB_HEIGHT, 0.003)
    self.assertNear(heights[0], heights[1], 0.001)

  def test_steers(self) -> None:
    """Standing, its steering wheel held 3 rad left, its front wheels
    turn left 8 to 15 degrees, its rears not (half a degree)."""
    wall = FourthWall(0.0)
    assembly, states = soapbox(SoapboxControls(BrakeLine(0.0), wall),
                               FLAT)
    world, clock = worldOf(), [0.0]
    states = self.ran(world, assembly, states, 0.5, clock)
    wall.value = 3.0
    states = self.ran(world, assembly, states, 1.0, clock)
    for (at, side), wheel in zip(CORNERS, wheelsOf(states)):
      axle = rotated(wheel.turn, (0.0, 0.0, 1.0))
      turned = math.degrees(math.atan2(axle[1], axle[0])) - 90.0 * side
      if at == 0.0:
        self.assertGreater(turned, 8.0)
        self.assertLess(turned, 15.0)
      else:
        self.assertLess(abs(turned), 0.5)

  def test_tune(self) -> None:
    """Tuned up with camber -2 degrees all round it stands so, to half a
    degree."""
    tune = TuneUp(tuple(WheelSetup(2.3e5, math.radians(-2.0), 0.0)
                        for _ in CORNERS))
    assembly, states = soapbox(SoapboxControls(BrakeLine(0.0),
                                               FourthWall(0.0), tune), FLAT)
    states = self.ran(worldOf(), assembly, states, 1.0, [0.0])
    for wheel in wheelsOf(states):
      axle = rotated(wheel.turn, (0.0, 0.0, 1.0))
      self.assertNear(math.degrees(math.asin(-axle[2])), -2.0, 0.5)

  def test_held(self) -> None:
    """Its brakes at 'HOLD' hold it on the ramp: it moves less than a
    centimetre in a second."""
    assembly, states = soapbox(SoapboxControls(BrakeLine(HOLD),
                                               FourthWall(0.0)))
    world, clock = worldOf(), [0.0]
    states = self.ran(world, assembly, states, 0.3, clock)
    was = states[CHASSIS].place
    states = self.ran(world, assembly, states, 1.0, clock)
    self.assertLess(norm(minus(states[CHASSIS].place, was)), 0.01)

  def test_loops(self) -> None:
    """Let go on the ramp, its line kept, it rolls down without a jolt,
    loops the loop and comes out beside it upright, the driver aboard,
    at 10 m/s or more; braked hard there it stops."""
    line, wall = BrakeLine(HOLD), FourthWall(0.0)
    assembly, states = soapbox(SoapboxControls(line, wall))
    world, clock = worldOf(), [0.0]
    weight = 9.81 * sum(body.mass for k, body in enumerate(
      assembly.bodies) if k != 1)
    hands = LineKeeper(wall)
    seen = {'slope': [], 'top': [], 'most': 0.0, 'high': 0.0}

    def each(now: tuple) -> None:
      """Keeps the line and notes the tyres' load."""
      hands.steer(now[CHASSIS], assembly.bodies[CHASSIS], FRAME)
      load = sum(norm(force) for force in world.tyreForcesOf(
        assembly)) / weight
      chassis = now[CHASSIS]
      up = rotated(chassis.turn, (0.0, 0.0, 1.0))
      seen['most'] = max(seen['most'], load)
      if chassis.place[0] > 0.0:
        seen['high'] = max(seen['high'], chassis.place[2])
      if 1.3 < clock[0] < 2.4:
        seen['slope'].append(load)
      if up[2] < -0.8:
        seen['top'].append(load)

    states = self.ran(world, assembly, states, 0.5, clock)
    line.pressure = 0.0
    states = self.ran(world, assembly, states, 7.5, clock, each)
    self.assertGreater(min(seen['slope']), 0.75)
    self.assertLess(max(seen['slope']), 0.97)
    self.assertGreater(seen['high'], 6.0)
    self.assertGreater(len(seen['top']), 3)
    self.assertGreater(min(seen['top']), 0.2)
    self.assertLess(seen['most'], 6.0)
    chassis = states[CHASSIS]
    self.assertGreater(rotated(chassis.turn, (0.0, 0.0, 1.0))[2], 0.95)
    self.assertLess(chassis.place[2], 0.6)
    self.assertGreater(chassis.place[0], 9.0)
    self.assertGreater(chassis.place[1], 1.5)
    self.assertGreater(norm(chassis.velocity), 10.0)
    driver = ownOf(assembly, states, states[0].place)
    self.assertLess(norm(minus(driver, SEAT)), 0.15)
    line.pressure = 50e5
    states = self.ran(world, assembly, states, 3.0, clock, each)
    self.assertLess(norm(states[CHASSIS].velocity), 1.0)
