"""
TestTyreSlip covers the tyre's slip law (user, 2026-11-14: "the tyre
effect is one that is decidedly chaotic. So there testing should be
quite tolerant. I would even suggest some more... well not greasy noise
exactly"): written before the law, on a braked wheel held on a stand
over the turntable ('_rig'), the deck running 10 m/s under it, its axle
12 mm low (about 3 kN on the tyre), tolerant of the road's texture
('SmallSteps' roughness: grip varying along the road, seeded). Rolling
free it keeps the deck's speed (to a percent), no side force (under 2 %
of its load), rolling resistance its load times 0.015 (to a quarter);
yawed (the slip angle) its side force grows about linearly (40 to 120
kN/rad), peaks between 4 and 10 degrees at 0.8 to 1.1 of its grip
times its load and falls 5 to 30 % by 12; held slower than the deck
(braking slip) its pull peaks between 8 and 25 % and, locked, keeps
0.65 to 0.95 of that; yawed at once it builds its side force over a
relaxation length (two thirds of it in 0.15 to 0.5 m rolled); twice
as loaded it grips 5 to 25 % less a newton; braked to its peak it
loses most of its side force (under 0.6 of it: the friction circle);
standing it holds a twist about its upright that, rolling, it lets go;
the road's texture repeats with its seed,
differs with another, varies the side force 2 to 8 % and averages out
over ten metres (to 2 %).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Contact, Drive, Fixed, Hinge
from worQt.phys import Motor, SmallSteps, State, Tie, boxShape, plus
from worQt.phys import product, rotated, turnAbout
from worQt.phys._brakes import brakedWheel
from worQt.phys._carcass import TYRE_PRESSURE, TYRE_YARD
from worQt.phys._rig import PATH, TABLE_MOST, TABLE_SERVO, TABLE_TOP
from worQt.phys._rig import _TYRE_ON_DECK, tableBody
from worQt.phys._small_steps import THREADS
from worQt.phys._tyred import ROLLING, tyreOf

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 2.5e-4
GRAVITY = (0.0, 0.0, -9.81)
UP = (0.0, 0.0, 1.0)
SPEED, DROP = 10.0, 0.012
#  The road's texture the tests step on: grip varying by 3 % (its
#  spread), smooth over 5 cm, its seed.
ROUGH, GRAIN, SEED = 0.03, 0.05, 7


def worldOf(rough: float, seed: int) -> SmallSteps:
  """Returns the small steps' world the tests step in, its road's
  texture 'rough' (a share of grip either way) with seed 'seed'."""
  return SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu', THREADS,
                    True, rough, GRAIN, seed)


def standOf(yaw: float, drop: float, servo: Drive, free: bool) -> tuple:
  """Returns a braked wheel on a stand (body 0, the world's, or free to
  turn about the upright through the patch if 'free'), the turntable
  (1, its motor run up to 'SPEED' under the wheel, already turning) and
  the wheel (2, 'drop' m low, already rolling, yawed 'yaw' rad left of
  the deck's way, its spin held by 'servo' on the stand where it has a
  damping; its axle held at two points 24 cm apart: 5 cm apart, a
  stand free to turn dragged the wheel round too weakly to test its
  pivoting): (assembly, states)."""
  stand = Body.of(boxShape(0.1, 0.1, 0.1), 7850.0)
  wheel = brakedWheel()
  turn = product(turnAbout(UP, yaw), turnAbout((1.0, 0.0, 0.0),
                                               -0.5 * math.pi))
  radius = tyreOf(2, TYRE_PRESSURE).radius
  middle = (0.0, -PATH, TABLE_TOP + radius - drop)
  drive = Drive()
  drive.damping, drive.most = TABLE_SERVO, TABLE_MOST
  drive.torque = -TABLE_SERVO * SPEED / PATH
  hub = tableBody().centre
  axle = rotated(turn, UP)
  standAt = plus(middle, tuple(-0.3 * a for a in axle))
  connections = [Hinge(None, hub, UP, 1, hub, UP), Motor(None, 1, UP, drive),
                 tyreOf(2, TYRE_PRESSURE), Contact(2, 1, *_TYRE_ON_DECK)]
  if free:
    patch = (middle[0], middle[1], TABLE_TOP)
    connections.append(Hinge(None, patch, UP, 0, tuple(
      a - b for a, b in zip(patch, standAt)), UP))
  else:
    connections.append(Fixed(0))
  for w in (-0.12, 0.12):
    connections.append(Tie(0, tuple(a * (0.3 + w) for a in axle), 2,
                           (0.0, 0.0, w)))
  if servo.damping > 0.0:
    connections.append(Motor(0, 2, (0.0, 0.0, 1.0), servo))
  spin = rotated(turn, (0.0, 0.0, SPEED / (radius - drop)))
  assembly = Assembly((stand, tableBody(), wheel), tuple(connections))
  states = (State(standAt),
            State(hub, (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                  (0.0, 0.0, -SPEED / PATH)),
            State(plus(middle, rotated(turn, wheel.centre)), turn,
                  (0.0, 0.0, 0.0), spin))
  return assembly, states


class TestTyreSlip(PhysTest):
  """Tests for the tyre's slip law (a few minutes on the CPU)."""

  __time_out__ = 900.0

  def steady(self, yaw: float, slip: float, drop: float = DROP,
             seconds: float = 2.0) -> tuple:
    """Returns the mean force on the wheel from the deck over the last
    second of 'seconds', yawed 'yaw' rad, its rim held 'slip' slower than
    the deck (nought: rolling free), and the wheel's last state."""
    servo = Drive()
    radius = tyreOf(2, TYRE_PRESSURE).radius - drop
    if slip > 0.0:
      servo.damping, servo.most = 400.0, 5000.0
      servo.torque = servo.damping * (1.0 - slip) * SPEED / radius
    assembly, states = standOf(yaw, drop, servo, False)
    world = worldOf(ROUGH, SEED)
    sums, count, clock = [0.0, 0.0, 0.0], 0, 0.0
    for k in range(round(seconds / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, clock)
      clock += FRAME
      if clock > seconds - 1.0:
        force = world.tyreForcesOf(assembly)[0]
        sums = [a + b for a, b in zip(sums, force)]
        count += 1
    return tuple(a / count for a in sums), states[2]

  def sideShare(self, yaw: float) -> float:
    """Returns the side force over the load, yawed 'yaw' rad, rolling
    free (toward the wheel's left, the deck's middle, positive)."""
    force, _ = self.steady(yaw, 0.0)
    return force[1] / force[2]

  def pullShare(self, slip: float) -> float:
    """Returns the pull along the deck's way over the load, the rim held
    'slip' slower (braking: the deck dragging the wheel back)."""
    force, _ = self.steady(0.0, slip)
    return -force[0] / force[2]

  def test_free(self) -> None:
    """Rolling free it keeps the deck's speed (to a percent), no side
    force (under 2 % of its load), its rolling resistance its load times
    0.015 (to a quarter)."""
    force, wheel = self.steady(0.0, 0.0)
    axle = rotated(wheel.turn, UP)
    rim = abs(sum(a * b for a, b in zip(wheel.spin, axle))) * (
      wheel.place[2] - TABLE_TOP)
    self.assertNear(rim, SPEED, 0.01 * SPEED)
    self.assertLess(abs(force[1]), 0.02 * force[2])
    self.assertNear(-force[0], ROLLING * force[2],
                    0.25 * ROLLING * force[2])

  def test_cornering(self) -> None:
    """Yawed, its side force grows about linearly (40 to 120 kN/rad
    over its first half degree, at its load), peaks between 4 and 10
    degrees at 0.8 to 1.1 of its grip times its load, and falls 5 to 30
    % below that by 12 degrees."""
    degrees = (0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0)
    forces = [self.steady(math.radians(d), 0.0)[0] for d in degrees]
    shares = [f[1] / f[2] for f in forces]
    stiffness = forces[0][1] / math.radians(degrees[0])
    self.assertGreater(stiffness, 40e3)
    self.assertLess(stiffness, 120e3)
    peak = max(shares)
    self.assertGreater(degrees[shares.index(peak)], 3.9)
    self.assertLess(degrees[shares.index(peak)], 10.1)
    grip = TYRE_YARD.grip
    self.assertGreater(peak, 0.8 * grip)
    self.assertLess(peak, 1.1 * grip)
    self.assertGreater(shares[-1], 0.7 * peak)
    self.assertLess(shares[-1], 0.95 * peak)

  def test_braking(self) -> None:
    """Held slower than the deck, its pull peaks between 8 and 25 %
    slip; locked, it keeps 0.65 to 0.95 of that."""
    slips = (0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5)
    shares = [self.pullShare(s) for s in slips]
    peak = max(shares)
    self.assertGreater(slips[shares.index(peak)], 0.07)
    self.assertLess(slips[shares.index(peak)], 0.26)
    locked = self.pullShare(0.999)
    self.assertGreater(locked, 0.65 * peak)
    self.assertLess(locked, 0.95 * peak)

  def test_relaxation(self) -> None:
    """Yawed 2 degrees at once, rolling, it builds its side force over
    its relaxation length: two thirds of its steady force after rolling
    0.15 to 0.5 m."""
    assembly, states = standOf(math.radians(2.0), DROP, Drive(), False)
    world = worldOf(0.0, SEED)
    steady, _ = self.steady(math.radians(2.0), 0.0)
    clock, rolled = 0.0, None
    for _ in range(round(0.2 / (0.1 * FRAME))):
      states = world.advancedAll(assembly, states, 0.1 * FRAME, clock)
      clock += 0.1 * FRAME
      if rolled is None and world.tyreForcesOf(assembly)[0][1] > (
          2.0 / 3.0 * steady[1]):
        rolled = SPEED * clock
    self.assertIsNotNone(rolled)
    self.assertGreater(rolled, 0.15)
    self.assertLess(rolled, 0.5)

  def test_load(self) -> None:
    """Twice as loaded, its peak side force over its load is 5 to 25 %
    less (yawed 8 degrees)."""
    light, _ = self.steady(math.radians(8.0), 0.0, DROP)
    heavy, _ = self.steady(math.radians(8.0), 0.0, 2.0 * DROP)
    lightShare, heavyShare = light[1] / light[2], heavy[1] / heavy[2]
    self.assertGreater(heavy[2], 1.7 * light[2])
    self.assertLess(heavyShare, 0.95 * lightShare)
    self.assertGreater(heavyShare, 0.75 * lightShare)

  def test_friction_circle(self) -> None:
    """Yawed 2 degrees and braked to 15 % slip, it keeps under 0.6 of
    its side force rolling free."""
    free, _ = self.steady(math.radians(2.0), 0.0)
    braked, _ = self.steady(math.radians(2.0), 0.15)
    self.assertLess(braked[1], 0.6 * free[1])

  def test_pivot(self) -> None:
    """On a stand free to turn about the upright through its patch, a
    twist brought up to 30 N m in 0.3 s (a third of its patch's hold:
    stepped on at once, the stand and wheel swinging on the patch's
    twist overshot it and slipped) turns it under 2 degrees in a second
    standing (the deck still), and over 10 rolling at 10 m/s."""
    turned = []
    for rolling in (False, True):
      assembly, states = standOf(0.0, DROP, Drive(), True)
      twist = Drive(0.0)
      twist.most = 100.0
      assembly = Assembly(assembly.bodies, assembly.connections + (
        Motor(None, 0, UP, twist),))
      if not rolling:
        assembly.connections[1].drive.torque = 0.0
        states = (states[0], State(states[1].place), State(
          states[2].place, states[2].turn))
      world = worldOf(0.0, SEED)
      clock = 0.0
      for _ in range(round(1.0 / FRAME)):
        twist.torque = 30.0 * min(1.0, clock / 0.3)
        states = world.advancedAll(assembly, states, FRAME, clock)
        clock += FRAME
      ahead = rotated(states[0].turn, (1.0, 0.0, 0.0))
      turned.append(abs(math.degrees(math.atan2(ahead[1], ahead[0]))))
    self.assertLess(turned[0], 2.0)
    self.assertGreater(turned[1], 10.0)

  def test_texture(self) -> None:
    """The road's texture: the same seed steps alike, another seed
    otherwise; yawed 12 degrees (sliding all through: at 8, where it
    first slides, its force is keenest on its grip), the side force read
    every 60th of a frame (1.7 cm rolled) varies 2 to 8 % about its mean
    (the grip's 3 %, and the patch flickering between holding and
    sliding: chaotic, so tolerant; measured 4.9), and its mean over ten
    metres' rolling is within 2 % of the smooth road's (measured 1.0)."""
    runs = []
    for rough, seed in ((ROUGH, SEED), (ROUGH, SEED), (ROUGH, SEED + 1),
                        (0.0, SEED)):
      assembly, states = standOf(math.radians(12.0), DROP, Drive(), False)
      world = worldOf(rough, seed)
      clock, sides = 0.0, []
      for k in range(round(1.5 / (0.1 * FRAME))):
        states = world.advancedAll(assembly, states, 0.1 * FRAME, clock)
        clock += 0.1 * FRAME
        if clock > 0.5:
          force = world.tyreForcesOf(assembly)[0]
          sides.append(force[1] / force[2])
      runs.append(sides)
    self.assertEqual(runs[0], runs[1])
    self.assertNotEqual(runs[0], runs[2])
    mean = sum(runs[0]) / len(runs[0])
    spread = math.sqrt(sum((s - mean) ** 2 for s in runs[0]) / len(
      runs[0])) / mean
    self.assertGreater(spread, 0.02)
    self.assertLess(spread, 0.08)
    smooth = sum(runs[3]) / len(runs[3])
    self.assertNear(mean, smooth, 0.02 * abs(smooth))
