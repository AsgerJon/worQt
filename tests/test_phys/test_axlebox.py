"""
TestAxlebox covers a wheelset held in a vehicle's frame ('rail._axlebox',
the rail world trading with its inner world; the spec "Trains: the math
first": the two-axle cart with axleboxes): Palmgren's torque as the
spec's example has it (5.6 N m at 922 rpm under 55 kN, nought standing,
against the turning); a wheelset spun in boxes on a frame held still
slows as its bearings' torque says, braked as its brakes' torque says
too (user, 2026-11-16: the cart's brake lever), in plain Python and
the kernel alike; a cart (a tub on two wheelsets)
set on the level platform stands, each box carrying a quarter of the
tub; let go on the grade it runs onto the level run before the loop
at the closed form's speed for its own k (the wheelsets' spin over the
whole cart's mass); an axlebox on no wheelset is refused. The Warp
kernel ('railRun', user, 2026-11-16: "warp that shit", "float32!")
steps a lone wheelset and the cart as the plain Python (float64)
does, within float32's reach over a second (0.4 mm, 2 mm/s: it lies
~0.05-0.15 mm off), on the CPU and on a GPU where there is one (the
cart's small steps on the device too: every trade there), and its cart
reaches the level run at the closed form's speed too.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import warp as wp

from worQt.phys import Assembly, Body, State
from worQt.phys._shape import boxShape
from worQt.phys._small_steps import THREADS, SmallSteps, preloaded
from worQt.phys._vectors import UNTURNED, turnOf
from worQt.phys.rail import JOURNAL_AT, PALMGREN, Axlebox, RailWorld
from worQt.phys.rail import Ribbon, loopSpan, loopTrack, palmgrenOf
from worQt.phys.rail import straight, wheelsetBody, wheelsetOn
from worQt.phys.rail._axlebox import brakeOf, motorOf
from worQt.phys.rail._wheelset import RADIUS

from . import PhysTest

#  A frame, s; the boxes' stiffness, N/m, and damping, N s/m, each way;
#  half the wheelbase, m; the reference step and trade, s.
FRAME = 1.0 / 60.0
STIFF, DAMPED = (2e6, 2e6, 2e6), (1.3e4, 1.3e4, 1.3e4)
HALF = 0.8
STEP, TRADE = 1e-4, 2e-3


class _Held:
  """A world holding every body still (a frame on a stand)."""

  def advancedAll(self, assembly: object, states: tuple, seconds: float,
                  start: float = 0.0) -> tuple:
    """Returns 'states' where they are, still."""
    return tuple(State(s.place, s.turn) for s in states)


def _tub() -> Body:
  """Returns a steel slab 2.6 x 2.3 x 0.2 m, its underside 0.96 m over
  the rails (its own frame's origin on the rails' top)."""
  return Body.of(boxShape(2.6, 2.3, 0.2).moved((0.0, 0.0, 1.06),
                                               UNTURNED), 1500.0)


def _cart(track: object, along: float) -> tuple:
  """Returns the assembly of a tub on two wheelsets at 'along' m on
  'track', its boxes, and the states standing still."""
  tub, wheels = _tub(), wheelsetBody()
  place, frame = track.frameAt(along)
  rows = tuple(tuple(float(x) for x in row) for row in frame)
  centre = tuple(float(place[i]) + sum(rows[i][j] * tub.centre[j]
                                       for j in range(3))
                 for i in range(3))
  states = (State(centre, turnOf(rows)),
            wheelsetOn(track, along + HALF, 0.0),
            wheelsetOn(track, along - HALF, 0.0))
  boxes = tuple(Axlebox(w, side, 0, (x, side * JOURNAL_AT, RADIUS),
                        STIFF, DAMPED)
                for w, x in ((1, HALF), (2, -HALF))
                for side in (1.0, -1.0))
  return Assembly((tub, wheels, wheels), boxes), boxes, states


class TestAxlebox(PhysTest):
  """Tests for the axlebox and the cart (a minute or so)."""

  #  The cart driven in plain Python and in the kernel besides the rest.
  __time_out__ = 180.0

  def test_palmgren(self) -> None:
    """The spec's example: 1.6 + 4.0 = 5.6 N m at 922 rpm under 55 kN;
    nought standing, against the turning, the slow branch under nu n
    2000."""
    spin = 922.0 * 2.0 * math.pi / 60.0
    self.assertAlmostEqual(palmgrenOf(spin, 55e3, PALMGREN), 5.59,
                           None, None, 0.02)
    self.assertAlmostEqual(palmgrenOf(-spin, 55e3, PALMGREN), -5.59,
                           None, None, 0.02)
    self.assertEqual(palmgrenOf(0.0, 55e3, PALMGREN), 0.0)
    slow = 10.0 * 2.0 * math.pi / 60.0
    f0, f1, _, middle = PALMGREN
    wanted = 1e-3 * (160e-7 * f0 * middle ** 3 + f1 * 1e3 * middle)
    self.assertAlmostEqual(palmgrenOf(slow, 1e3, PALMGREN), wanted, 9)

  def test_spun_in_boxes(self) -> None:
    """Lifted off the rails in boxes on a frame held still, a wheelset
    spun at 50 rad/s slows by its two bearings' torque (each box
    carrying half its weight) to 5 % in 2 s."""
    track = Ribbon((straight(50.0),))
    wheels, frame = wheelsetBody(), _tub()
    lifted = wheelsetOn(track, 25.0, 0.0)
    lifted = State((lifted.place[0], lifted.place[1],
                    lifted.place[2] + 0.3), lifted.turn, (0.0, 0.0, 0.0),
                   (0.0, 50.0, 0.0))
    still = State((25.0, 0.0, 1.06))
    boxes = tuple(Axlebox(1, side, 0, (0.0, side * JOURNAL_AT,
                                       RADIUS + 0.3), STIFF, DAMPED)
                  for side in (1.0, -1.0))
    world = RailWorld(_Held(), track, wheels, STEP, 0.3, TRADE)
    assembly = Assembly((frame, wheels), boxes)
    states = (still, lifted)
    for k in range(round(2.0 / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    load = 0.5 * wheels.mass * 9.81
    spin, h, spinning = 50.0, 1e-3, wheels.inertia[2][2]
    for _ in range(2000):
      spin -= 2.0 * palmgrenOf(spin, load, PALMGREN) / spinning * h
    lost = 50.0 - abs(states[1].spin[1])
    self.assertAlmostEqual(lost, 50.0 - spin, None, None,
                           0.05 * (50.0 - spin))

  def test_braked(self) -> None:
    """Lifted off the rails in boxes on a frame held still, a wheelset
    spun at 30 rad/s with 100 N m on each box's shoes slows as its
    bearings and brakes say, in plain Python and in the kernel (CPU)."""
    track = Ribbon((straight(50.0),))
    wheels, frame = wheelsetBody(), _tub()
    lifted = wheelsetOn(track, 25.0, 0.0)
    lifted = State((lifted.place[0], lifted.place[1],
                    lifted.place[2] + 0.3), lifted.turn, (0.0, 0.0, 0.0),
                   (0.0, 30.0, 0.0))
    still = State((25.0, 0.0, 1.06))
    load = 0.5 * wheels.mass * 9.81
    spin, h, spinning = 30.0, 1e-3, wheels.inertia[2][2]
    for _ in range(1000):
      spin -= 2.0 * (palmgrenOf(spin, load, PALMGREN)
                     + brakeOf(spin, 100.0)) / spinning * h
    for device in (None, 'cpu'):
      with self.subTest(device=device):
        boxes = tuple(Axlebox(1, side, 0, (0.0, side * JOURNAL_AT,
                                           RADIUS + 0.3), STIFF, DAMPED)
                      for side in (1.0, -1.0))
        for box in boxes:
          box.brake = 100.0
        world = RailWorld(_Held(), track, wheels, STEP, 0.3, TRADE,
                          device)
        assembly = Assembly((frame, wheels), boxes)
        states = (still, lifted)
        for k in range(round(1.0 / FRAME)):
          states = world.advancedAll(assembly, states, FRAME, k * FRAME)
        lost = 30.0 - abs(states[1].spin[1])
        self.assertAlmostEqual(lost, 30.0 - spin, None, None,
                               0.03 * (30.0 - spin))

  def test_motor(self) -> None:
    """A motor drives as much as it may within its power: nought driving
    nought; its torque while slow; its power shared over its spin when
    fast; its own way either way round."""
    self.assertEqual(motorOf(10.0, 0.0, 1e3), 0.0)
    self.assertEqual(motorOf(1.0, 300.0, 1e3), 300.0)
    self.assertEqual(motorOf(10.0, 300.0, 1e3), 100.0)
    self.assertEqual(motorOf(-10.0, -300.0, 1e3), -100.0)
    self.assertEqual(motorOf(0.0, 300.0, 1e3), 300.0)
    self.assertEqual(motorOf(10.0, 300.0, 0.0), 300.0)

  def test_driven(self) -> None:
    """Driven from standing on the level, each box's motor at 600 N m
    within 1.5 kW, the cart gains speed as its torque says till its
    power takes over, then as its power does (within 3 %, in plain
    Python and in the kernel, CPU)."""
    track = Ribbon((straight(60.0),))
    preloaded('cpu')
    drive, power, seconds = 600.0, 1500.0, 3.0
    for device in (None, 'cpu'):
      with self.subTest(device=device):
        assembly, boxes, states = _cart(track, 20.0)
        for box in boxes:
          box.drive, box.power = drive, power
        inner = SmallSteps((0.0, 0.0, -9.81), None, 2.5e-4, 1, 0.0, 'cpu',
                           THREADS, False)
        world = RailWorld(inner, track, wheelsetBody(), STEP, 0.3, TRADE,
                          device)
        for k in range(round(seconds / FRAME)):
          states = world.advancedAll(assembly, states, FRAME, k * FRAME)
        wheels = assembly.bodies[1]
        moving = sum(body.mass for body in assembly.bodies) + (
          2.0 * wheels.inertia[2][2] / RADIUS ** 2)
        pulled = 4.0 * drive / RADIUS
        turning = power / drive
        reached = turning * RADIUS
        taken = reached * moving / pulled
        wanted = math.sqrt(reached ** 2 + 2.0 * 4.0 * power * (
          seconds - taken) / moving)
        self.assertAlmostEqual(states[0].velocity[0], wanted, None, None,
                               0.03 * wanted)

  def test_stands(self) -> None:
    """On the level platform the cart stands: still to 2 cm/s after a
    second, each box carrying a quarter of the tub within 1 %."""
    track = loopTrack()
    assembly, boxes, states = _cart(track, 6.0)
    preloaded('cpu')
    inner = SmallSteps((0.0, 0.0, -9.81), None, 2.5e-4, 1, 0.0, 'cpu',
                       THREADS, False)
    world = RailWorld(inner, track, wheelsetBody(), STEP, 0.3, TRADE)
    for k in range(round(1.0 / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    self.assertLess(math.sqrt(sum(v * v for v in states[0].velocity)),
                    0.02)
    quarter = 0.25 * assembly.bodies[0].mass * 9.81
    for box in boxes:
      with self.subTest(side=box.side, wheelset=box.wheelset):
        self.assertAlmostEqual(world.boxLoads[id(box)], quarter, None,
                               None, 0.01 * quarter)

  def test_rolls_down(self) -> None:
    """Let go on the grade the cart runs onto the level run before the
    loop at v² = 2 g dh / (1 + k), dh its centre of mass's drop, k the
    wheelsets' spin inertia over the whole cart's mass (0.23 here),
    within 0.2 %."""
    self.rollsDown(None)

  def test_kernel_rolls_down(self) -> None:
    """So it does stepped by the kernel (on the CPU)."""
    self.rollsDown('cpu')

  def rollsDown(self, device: str) -> None:
    """The cart let go on the grade, stepped on 'device' (None: plain
    Python), runs onto the level run before the loop (5 m before it,
    where nothing curves) at the closed form's speed."""
    track = loopTrack()
    assembly, _, states = _cart(track, 14.0)
    preloaded('cpu')
    inner = SmallSteps((0.0, 0.0, -9.81), None, 2.5e-4, 1, 0.0, 'cpu',
                       THREADS, False)
    world = RailWorld(inner, track, wheelsetBody(), STEP, 0.3, TRADE,
                      device)
    masses = [body.mass for body in assembly.bodies]
    mass, wheels = sum(masses), assembly.bodies[1]
    k = 2.0 * wheels.inertia[2][2] / (mass * RADIUS ** 2)

    def middle(states: tuple, part: str) -> tuple:
      return tuple(sum(m * getattr(state, part)[c]
                       for m, state in zip(masses, states)) / mass
                   for c in range(3))

    top, run = middle(states, 'place')[2], loopSpan()[0] - 5.0
    for i in range(round(9.0 / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, i * FRAME)
      if world.along(states[1].place) > run:
        break
    speed = math.sqrt(sum(x * x for x in middle(states, 'velocity')))
    low = middle(states, 'place')[2]
    wanted = math.sqrt(2.0 * 9.81 * (top - low) / (1.0 + k))
    self.assertGreater(top - low, 25.0)
    self.assertAlmostEqual(speed, wanted, None, None, 0.002 * wanted)

  def kernelAgrees(self, device: str) -> None:
    """A lone wheelset down the grade and the cart standing then rolling
    off, a second each, stepped on 'device' (the cart's small steps there
    too: every trade on the device) as in plain Python (within 0.4 mm,
    2 mm/s: float32 lies ~0.05 mm off for the lone wheelset, ~0.15 mm
    for the cart)."""
    track = loopTrack()
    preloaded('cpu')
    preloaded(device)
    for build in ('lone', 'cart'):
      runs = []
      for where in (None, device):
        if build == 'lone':
          wheels = wheelsetBody()
          assembly, states = Assembly((wheels,), ()), (
            wheelsetOn(track, 13.0, 0.0),)
        else:
          assembly, _, states = _cart(track, 12.5)
        inner = SmallSteps((0.0, 0.0, -9.81), None, 2.5e-4, 1, 0.0,
                           where or 'cpu', THREADS, False)
        world = RailWorld(inner, track, wheelsetBody(), STEP, 0.3, TRADE,
                          where)
        for k in range(round(1.0 / FRAME)):
          states = world.advancedAll(assembly, states, FRAME, k * FRAME)
        runs.append(states)
      for reference, got in zip(*runs):
        with self.subTest(build=build):
          self.assertLess(math.dist(got.place, reference.place), 4e-4)
          self.assertLess(math.dist(got.velocity, reference.velocity),
                          2e-3)

  def test_kernel_cpu(self) -> None:
    """The kernel on the CPU steps as the plain Python does."""
    self.kernelAgrees('cpu')

  def test_kernel_gpu(self) -> None:
    """The kernel on a GPU steps as the plain Python does (where there
    is one)."""
    wp.init()
    if not wp.is_cuda_available():
      self.skipTest('no GPU here')
    self.kernelAgrees('cuda:0')

  def test_refused(self) -> None:
    """A journal on side nought, or a wheelset in its own box, is
    refused; so is a box whose wheelset is no wheelset."""
    with self.assertRaises(ValueError):
      Axlebox(1, 0.0, 0, (0.0, 0.0, 0.0), STIFF, DAMPED)
    with self.assertRaises(ValueError):
      Axlebox(1, 1.0, 1, (0.0, 0.0, 0.0), STIFF, DAMPED)
    track = Ribbon((straight(20.0),))
    world = RailWorld(_Held(), track, wheelsetBody())
    box = Axlebox(1, 1.0, 0, (0.0, 0.0, 0.0), STIFF, DAMPED)
    tub = _tub()
    with self.assertRaises(ValueError):
      world.advancedAll(Assembly((tub, tub), (box,)),
                        (State(), State()), FRAME)
