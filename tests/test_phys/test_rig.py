"""
TestRig covers the tyre rig ('_rig.tyreRig'; user, 2026-11-14: "An
actuator then presses the arm such as to force the wheel into another
simulated driving road ... We can then observe breaking at different
weights. Further ... 'bumps' in the road"; "the 'belt' could be a flat
disc spinning about the vertical"; "We need steering now ... a two
direction hinge still preventing roll ... the tire can steer its
position on the disc"): a ram ('Ram') pushes its points
apart as hard as its fourth wall point asks (a hung ball rests its
weight and the push over the spring's rate lower, to a tenth of a
millimetre); a wheel on a fixed axle rolls on the spinning turntable
as on the ground (its rim at the deck's speed to a percent, its side
force under 2 % of its load, its rolling resistance its load times
0.015 to a tenth);
the corner on its boom rides as built under the ram's 1.5 kN (the
shock's eyes to 3 mm, the load 3.9 to 4.5 kN, all but still), at 10
m/s its
brake at 30 bar pulls 1.8 to 2.4 kN (its pads' 618 N m at the tyre's
rolling radius) while the deck holds its speed to 0.1 m/s, and over
humps at 8 m/s the wheel rises 2 cm and the shock closes a centimetre;
steered left 143 degrees at 8 m/s the wheel rolls 30 to 50 cm in
across the deck, the boom swinging after it on its yoke, the side force
under 0.6 kN, and straight again it rolls back (to 3 cm); tuned up
(1.8 bar, camber -2, toe 0.5 in) it stands so. The springs' world
refuses a ram and humps.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, BrakeLine, Contact, Damper, Drive
from worQt.phys import Fixed, FourthWall, Hinge, Humps, Motor, Ram
from worQt.phys import SmallSteps, Sphere, Spring, State, Tie, World
from worQt.phys import boxShape, minus, norm, plus, rotated, turnAbout
from worQt.phys._brakes import brakedWheel
from worQt.phys._carcass import TYRE_PRESSURE, TYRE_YARD
from worQt.phys._rig import LOAD, PATH, SHOCK_FOOT, SHOCK_TOP, TABLE_TOP
from worQt.phys._rig import RigControls, rigHumps, tableBody, tyreRig
from worQt.phys._rig import TuneUp, WheelSetup
from worQt.phys._rig import TABLE_MOST, TABLE_SERVO, _TYRE_ON_DECK
from worQt.phys._tyred import ROLLING, tyreOf

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)
UP = (0.0, 0.0, 1.0)


def controlsOf() -> RigControls:
  """Returns a rig's controls as the window starts them: the deck still,
  the ram at 'LOAD', no humps, the brake off, the steering straight."""
  return RigControls(Drive(), FourthWall(LOAD), Humps(2), BrakeLine(0.0),
                     FourthWall(0.0))


def deckOf(states: tuple) -> float:
  """Returns how fast the deck runs under the wheel, m/s."""
  return -states[2].spin[2] * PATH


def rimOf(states: tuple) -> float:
  """Returns how fast the wheel's rim runs, m/s: its spin about its
  axle times its axle's height over the deck."""
  wheel = states[7]
  axle = rotated(wheel.turn, (0.0, 0.0, 1.0))
  spin = sum(a * b for a, b in zip(wheel.spin, axle))
  return abs(spin) * (wheel.place[2] - TABLE_TOP)


def shockOf(assembly: Assembly, states: tuple) -> float:
  """Returns how far apart the shock's eyes are, m."""
  bodies = assembly.bodies
  return norm(minus(bodies[9].placeOf(states[9], (0.0, 0.0, 0.0)),
                    bodies[8].placeOf(states[8], (0.0, 0.0, 0.0))))


class TestRig(PhysTest):
  """Tests for the tyre rig (about three minutes on the CPU)."""

  __time_out__ = 900.0

  def ran(self, world: SmallSteps, assembly: Assembly, states: tuple,
          seconds: float, clock: list) -> tuple:
    """Returns 'states' 'seconds' on, a frame at a time ('clock' its
    time, moved on)."""
    for _ in range(round(seconds / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, clock[0])
      clock[0] += FRAME
    return states

  def test_ram(self) -> None:
    """A 4.1 kg ball hung on a spring (20 kN/m) and damped, a ram from
    above pushing it down 100 N, rests the weight and the push over the
    spring's rate below the spring's rest (to a tenth of a millimetre)."""
    ball = Body.of(Sphere(0.05), 7850.0)
    top, rest, stiff = (0.0, 0.0, 2.0), 0.5, 2e4
    wall = FourthWall(100.0)
    assembly = Assembly((ball,), (
      Spring(None, top, 0, (0.0, 0.0, 0.0), stiff, rest),
      Damper(None, top, 0, (0.0, 0.0, 0.0), 0.4 * math.sqrt(
        stiff * ball.mass)),
      Ram(None, (0.0, 0.0, 3.0), 0, (0.0, 0.0, 0.0), wall)))
    world = SmallSteps(GRAVITY, None, 2.5e-4, 1, 0.0, 'cpu')
    start = (State((0.0, 0.0, top[2] - rest)),)
    held = self.ran(world, assembly, start, 1.5, [0.0])[0]
    wanted = top[2] - rest - (ball.mass * 9.81 + wall.value) / stiff
    self.assertNear(held.place[2], wanted, 1e-4)

  def test_on_turntable(self) -> None:
    """A braked wheel on a fixed axle 12 mm low, on the deck run up to
    20 m/s under it, rolls as on the ground: its rim at the deck's speed
    (to a percent), next to no side force (under 2 % of its load: its
    tread feels the deck's circle, 1 %), the deck pulling it along
    by its rolling resistance (its load times 0.015, to a tenth)."""
    stand = Body.of(boxShape(0.1, 0.1, 0.1), 7850.0)
    wheel = brakedWheel()
    upright = turnAbout((1.0, 0.0, 0.0), -0.5 * math.pi)
    middle = (0.0, -PATH, TABLE_TOP + tyreOf(1, TYRE_PRESSURE).radius
              - 0.012)
    drive = Drive()
    drive.damping, drive.most = TABLE_SERVO, TABLE_MOST
    drive.torque = -TABLE_SERVO * 20.0 / PATH
    hub = tableBody().centre
    connections = [Fixed(0), Hinge(None, hub, UP, 1, hub, UP),
                   Motor(None, 1, UP, drive), tyreOf(2, TYRE_PRESSURE),
                   Contact(2, 1, *_TYRE_ON_DECK)]
    for w in (0.02, 0.07):
      connections.append(Tie(0, (0.0, 0.3 + w, 0.0), 2, (0.0, 0.0, w)))
    assembly = Assembly((stand, tableBody(), wheel), tuple(connections))
    states = (State(plus(middle, (0.0, -0.3, 0.0))), State(hub),
              State(plus(middle, rotated(upright, wheel.centre)), upright))
    world = SmallSteps(GRAVITY, TYRE_YARD, 2.5e-4, 1, 1e-7, 'cpu')
    states = self.ran(world, assembly, states, 3.5, [0.0])
    deck = -states[1].spin[2] * PATH
    self.assertNear(deck, 20.0, 0.05)
    axle = rotated(states[2].turn, (0.0, 0.0, 1.0))
    spin = abs(sum(a * b for a, b in zip(states[2].spin, axle)))
    rim = spin * (states[2].place[2] - TABLE_TOP)
    self.assertNear(rim, deck, 0.01 * deck)
    force = world.tyreForcesOf(assembly)[0]
    self.assertLess(abs(force[1]), 0.02 * force[2])
    pull = -force[0]
    wanted = ROLLING * force[2]
    self.assertNear(pull, wanted, 0.1 * wanted)

  def test_rides(self) -> None:
    """The corner on its boom, the ram at 1.5 kN, rides as built in two
    seconds: its shock's eyes as far apart as built (to 3 mm), the load
    on the tyre 3.9 to 4.5 kN (the boom's 2.4 kN with its steering box,
    the ram's share, the corner's own), the boom all but still (under 5
    mm a second: free to swing on its yoke, on a tread that gives)."""
    controls = controlsOf()
    assembly, states = tyreRig(controls)
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
    states = self.ran(world, assembly, states, 2.0, [0.0])
    self.assertNear(shockOf(assembly, states),
                    norm(minus(SHOCK_TOP, SHOCK_FOOT)), 3e-3)
    load = world.tyreForcesOf(assembly)[0][2]
    self.assertGreater(load, 3900.0)
    self.assertLess(load, 4500.0)
    self.assertLess(norm(states[3].velocity), 5e-3)

  def test_brakes(self) -> None:
    """At 10 m/s its brake at 30 bar pulls 1.8 to 2.4 kN on the tyre
    (the pads' 618 N m at its rolling radius), the deck held to its speed
    (to 0.1 m/s) by its motor."""
    controls = controlsOf()
    assembly, states = tyreRig(controls)
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
    clock = [0.0]
    controls.setSpeed(10.0)
    states = self.ran(world, assembly, states, 2.0, clock)
    self.assertNear(deckOf(states), 10.0, 0.1)
    self.assertNear(rimOf(states), 10.0, 0.15)
    controls.line.pressure = 30e5
    states = self.ran(world, assembly, states, 0.5, clock)
    force = world.tyreForcesOf(assembly)[0]
    self.assertGreater(-force[0], 1800.0)
    self.assertLess(-force[0], 2400.0)
    self.assertNear(deckOf(states), 10.0, 0.1)

  def test_humps(self) -> None:
    """Four humps (3 cm) bolted on, at 8 m/s: over a second and a half
    (looked at every half frame: a hump passes in a twentieth of a
    second) the wheel rises at least 2 cm over its riding height and the
    shock closes at least a centimetre from its riding length."""
    controls = controlsOf()
    assembly, states = tyreRig(controls)
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
    clock = [0.0]
    states = self.ran(world, assembly, states, 1.0, clock)
    riding, length = states[7].place[2], shockOf(assembly, states)
    controls.setSpeed(8.0)
    states = self.ran(world, assembly, states, 1.5, clock)
    controls.humps.humps = rigHumps(4)
    highest, shortest = riding, length
    for _ in range(round(3.0 / FRAME)):
      states = world.advancedAll(assembly, states, 0.5 * FRAME, clock[0])
      clock[0] += 0.5 * FRAME
      highest = max(highest, states[7].place[2])
      shortest = min(shortest, shockOf(assembly, states))
    self.assertGreater(highest - riding, 0.02)
    self.assertGreater(length - shortest, 0.01)

  def test_steers(self) -> None:
    """At 8 m/s the steering wheel turned left 143 degrees (2.5 rad, at
    2 rad/s) steers the wheel in across the deck: in three seconds it
    runs 30 to 50 cm nearer the deck's middle, the boom swung after it,
    its side force under 0.6 kN; straight again, in three seconds it
    runs where it ran (to 3 cm)."""
    controls = controlsOf()
    assembly, states = tyreRig(controls)
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
    clock = [0.0]
    controls.setSpeed(8.0)
    states = self.ran(world, assembly, states, 2.0, clock)

    def outOf(states: tuple) -> float:
      """Returns how far out from the deck's middle the wheel runs."""
      return math.hypot(states[7].place[0], states[7].place[1])

    def steered(asked: float, seconds: float, states: tuple) -> tuple:
      """Returns 'states' after turning the steering wheel toward
      'asked' at 2 rad/s for 'seconds'."""
      wall = controls.steer
      for _ in range(round(seconds / FRAME)):
        step = 2.0 * FRAME
        wall.value += max(-step, min(step, asked - wall.value))
        states = world.advancedAll(assembly, states, FRAME, clock[0])
        clock[0] += FRAME
      return states

    straight = outOf(states)
    states = steered(2.5, 3.0, states)
    self.assertGreater(straight - outOf(states), 0.3)
    self.assertLess(straight - outOf(states), 0.5)
    force = world.tyreForcesOf(assembly)[0]
    self.assertLess(math.hypot(force[0], force[1]), 600.0)
    states = steered(0.0, 3.0, states)
    self.assertNear(outOf(states), straight, 0.03)

  def test_tune(self) -> None:
    """Tuned up (its tyre at 1.8 bar, camber -2 degrees, toe 0.5 in) the
    corner is built so (its ball joints meeting as built) and stands so
    in a second and a half: camber -2 to the rubber's give (0.4
    degrees), toe 0.5 in (to 0.2), its softer tyre pressed 2 to 7 mm
    further in than as built (as built: no camber nor toe, to 0.3 and
    0.15)."""
    heights = []
    for setup, camber, toe in ((WheelSetup(), 0.0, 0.0),
                               (WheelSetup(1.8e5, math.radians(-2.0),
                                           math.radians(0.5)), -2.0, 0.5)):
      controls = RigControls(Drive(), FourthWall(LOAD), Humps(2),
                             BrakeLine(0.0), FourthWall(0.0),
                             TuneUp((setup,)))
      assembly, states = tyreRig(controls)
      world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
      states = self.ran(world, assembly, states, 1.5, [0.0])
      axle = rotated(states[7].turn, (0.0, 0.0, 1.0))
      ahead = rotated(states[6].turn, (1.0, 0.0, 0.0))
      tolerance = (0.3, 0.15) if camber == 0.0 else (0.4, 0.2)
      self.assertNear(math.degrees(math.asin(-axle[2])), camber,
                      tolerance[0])
      self.assertNear(-math.degrees(math.atan2(ahead[1], ahead[0])), toe,
                      tolerance[1])
      heights.append(states[7].place[2])
    self.assertGreater(heights[0] - heights[1], 0.002)
    self.assertLess(heights[0] - heights[1], 0.007)

  def test_springs_refuse(self) -> None:
    """The springs' world refuses a ram and humps."""
    ball = Body.of(Sphere(0.05), 7850.0)
    world = World(GRAVITY, 1e-3, None)
    start = (State((0.0, 0.0, 1.0)),)
    for connection in (Ram(None, (0.0, 0.0, 2.0), 0, (0.0, 0.0, 0.0),
                           FourthWall(1.0)), Humps(0, ())):
      with self.assertRaises(ValueError):
        world.advancedAll(Assembly((ball,), (connection,)), start, 0.01)
