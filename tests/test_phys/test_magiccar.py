"""
TestMagicCar covers the stand-in car ('_magiccar.magicCar'; user,
2026-11-15: "Create a copy of the car where you replace our physical
parts with the equivalences at higher abstraction levels", "selectable
defaulting to the new cheaper one", "automatic transmission bro...
fake in other words. audible only"), each stand-in held to the car of
parts it stands in for ('_realcar.realCar'), both run alike: lumped, it
weighs what the car of parts does, its middle where that one's is, of
eleven bodies and no gears, rack or links; standing, each wheel is
where the car of parts' stands (3 mm); loaded from 0.6 g to 1.4 g each
axle's wheels rise as far (a fifth); pushed sideways at half a g it
rolls as far (a third); its front wheels turn as far for the steering
wheel (0.3 degree), its rears hold their toe; braked at 8 and 16 bar it
slows as hard (a tenth); its automatic pulls away and shifts up through
the gears (its revolutions between idling and the limiter), brakes with
the engine let off, revs free in neutral, backs in reverse; the city
racer drives it round town as it drives the car of parts (250 m in 25 s,
on the road, never stranded); and it steps at least half again as fast.
Tolerant: tyres are chaotic.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os
import time

from worQt.phys import BrakeLine, FourthWall, SmallSteps, State
from worQt.phys import conjugate, minus, rotated, scaled
from worQt.phys import _magiccar, _realcar
from worQt.phys._assembly import GearMesh, RackAndPinion
from worQt.phys._automatic import AutomaticDrive
from worQt.phys._carcass import TYRE_YARD
from worQt.phys._drivetrain import IDLE, REDLINE, DrivetrainControls
from worQt.phys._drivetrain import drivetrainWorked, readingOf
from worQt.phys._realcar import CORNERS, FOOT, Antilock, RealCarControls
from worQt.phys._rig import HUB_HEIGHT, TuneUp, WheelSetup

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)
CARS = ('magic', 'parts')


def carOf(kind: str) -> list:
  """Returns a car of 'kind' ('magic', the stand-in; 'parts', the car of
  parts) as built on the yard, still: [controls, assembly, states, its
  wheels, the clock]."""
  tune = TuneUp((WheelSetup(),) * len(CORNERS))
  if kind == 'magic':
    controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0), tune,
                               AutomaticDrive(),
                               Antilock(_magiccar.WHEELS))
    assembly, states = _magiccar.magicCar(controls)
  else:
    controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0), tune,
                               DrivetrainControls(), Antilock())
    assembly, states = _realcar.realCar(controls)
  return [controls, assembly, states, controls.brakes.wheels, 0.0]


def ran(car: list, seconds: float, gravity: tuple = GRAVITY) -> None:
  """Works and steps 'car' 'seconds' on under 'gravity', a frame at a
  time, its brakes through the anti-lock."""
  controls, assembly = car[0], car[1]
  world = SmallSteps(gravity, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
  for _ in range(round(seconds / FRAME)):
    drivetrainWorked(controls.drive, car[2], FRAME)
    controls.brakes.worked(controls.line.pressure, assembly, car[2], FRAME)
    car[2] = world.advancedAll(assembly, car[2], FRAME, car[4])
    car[4] += FRAME


def risesOf(car: list) -> list[float]:
  """Returns how far each wheel's middle stands over where it was built
  in the chassis' frame, m ('CORNERS' order)."""
  assembly, states = car[1], car[2]
  chassis, body = states[1], assembly.bodies[1]
  out = []
  for wheel in car[3]:
    own = rotated(conjugate(chassis.turn), minus(states[wheel].place,
                                                 chassis.place))
    out.append(own[2] + body.centre[2] - HUB_HEIGHT)
  return out


def anglesOf(car: list) -> list[float]:
  """Returns how far each wheel is turned left on the chassis, deg."""
  states = car[2]
  chassis, out = states[1], []
  for wheel, (_, side) in zip(car[3], CORNERS):
    axle = rotated(conjugate(chassis.turn), rotated(states[wheel].turn,
                                                    (0.0, 0.0, 1.0)))
    out.append(math.degrees(math.atan2(axle[1], axle[0])) - 90.0 * side)
  return out


def forwardOf(car: list) -> float:
  """Returns how fast the car goes along its chassis' forward, m/s."""
  chassis = car[2][1]
  return rotated(conjugate(chassis.turn), chassis.velocity)[0]


def rollOf(car: list) -> float:
  """Returns how far the chassis leans right, deg."""
  left = rotated(car[2][1].turn, (0.0, 1.0, 0.0))
  return math.degrees(math.asin(left[2]))


def rolling(car: list, speed: float) -> None:
  """Sets 'car', settled, going 'speed' m/s ahead, its wheels rolling so,
  out of gear."""
  car[0].drive.asked = 'N'
  ran(car, 0.5)
  wheels = {wheel: side for wheel, (_, side) in zip(car[3], CORNERS)}
  radius = next(tyre.radius for tyre in car[1].tyres if tyre.body in wheels)
  moving = []
  for k, state in enumerate(car[2]):
    spin = state.spin
    if k in wheels:
      spin = scaled(rotated(state.turn, (0.0, 0.0, 1.0)),
                    wheels[k] * speed / radius)
    moving.append(State(state.place, state.turn, (speed, 0.0, 0.0), spin))
  car[2] = tuple(moving)
  ran(car, 0.3)


class TestMagicCar(PhysTest):
  """Tests for the stand-in car (about two minutes on the CPU)."""

  __time_out__ = 1200.0

  def test_lumped(self) -> None:
    """The stand-in weighs what the car of parts does (to a microgram),
    its middle of mass where that one's is (a micrometre), of eleven
    bodies, no gear, rack or pinion among its connections."""
    cars = {kind: carOf(kind) for kind in CARS}
    weighed = {}
    for kind, car in cars.items():
      bodies, states = car[1].bodies[1:], car[2][1:]
      mass = sum(body.mass for body in bodies)
      middle = tuple(sum(body.mass * state.place[i]
                         for body, state in zip(bodies, states)) / mass
                     for i in range(3))
      weighed[kind] = mass, middle
    self.assertNear(weighed['magic'][0], weighed['parts'][0], 1e-9)
    self.assertNear(weighed['magic'][1], weighed['parts'][1], 1e-6)
    assembly = cars['magic'][1]
    self.assertEqual(len(assembly.bodies), 11)
    self.assertFalse([x for x in assembly.connections
                      if isinstance(x, (GearMesh, RackAndPinion))])

  def test_rides(self) -> None:
    """Settled, each of the stand-in's wheels stands as built (3 mm) and
    where the car of parts' does (3 mm)."""
    rises = {}
    for kind in CARS:
      car = carOf(kind)
      ran(car, 1.0)
      rises[kind] = risesOf(car)
    for magic, parts in zip(rises['magic'], rises['parts']):
      self.assertLess(abs(magic), 0.003)
      self.assertLess(abs(magic - parts), 0.003)

  def test_rates(self) -> None:
    """Loaded from 0.6 g to 1.4 g, each axle's wheels rise on the
    chassis as far as the car of parts' (within a fifth)."""
    travel = {}
    for kind in CARS:
      car = carOf(kind)
      ran(car, 1.0)
      settled = list(car)
      rises = []
      for g in (0.6, 1.4):
        loaded = list(settled)
        ran(loaded, 1.2, (0.0, 0.0, -g * 9.81))
        rises.append(risesOf(loaded))
      travel[kind] = [0.5 * (rises[1][k] - rises[0][k] + rises[1][k + 1]
                             - rises[0][k + 1]) for k in (0, 2)]
    for magic, parts in zip(travel['magic'], travel['parts']):
      self.assertGreater(parts, 0.01)
      self.assertNear(magic, parts, 0.2 * parts)

  def test_roll(self) -> None:
    """Pushed sideways at half a g (gravity tilted), the stand-in leans
    as far as the car of parts (within a third)."""
    leaned = {}
    for kind in CARS:
      car = carOf(kind)
      ran(car, 1.0)
      standing = rollOf(car)
      ran(car, 1.5, (0.0, 0.5 * 9.81, -9.81))
      leaned[kind] = rollOf(car) - standing
    self.assertGreater(abs(leaned['parts']), 0.3)
    self.assertNear(leaned['magic'], leaned['parts'],
                    abs(leaned['parts']) / 3.0)

  def test_steers(self) -> None:
    """Standing, its steering wheel held 1.5 and 3 rad left, the
    stand-in's front wheels turn as far as the car of parts' (0.3
    degree each), its rears no further from their toe than that's."""
    for asked in (1.5, 3.0):
      angles = {}
      for kind in CARS:
        car = carOf(kind)
        ran(car, 0.5)
        car[0].steer.value = asked
        ran(car, 1.0)
        angles[kind] = anglesOf(car)
      with self.subTest(asked=asked):
        for magic, parts in zip(angles['magic'], angles['parts']):
          self.assertNear(magic, parts, 0.3)

  def test_brakes(self) -> None:
    """Braked from 15 m/s at 8 and 16 bar (short of locking), the
    stand-in slows as hard as the car of parts (within a tenth)."""
    for bar in (8.0, 16.0):
      slowed = {}
      for kind in CARS:
        car = carOf(kind)
        rolling(car, 15.0)
        before = forwardOf(car)
        car[0].line.pressure = bar * 1e5
        ran(car, 0.6)
        slowed[kind] = (before - forwardOf(car)) / 0.6
      with self.subTest(bar=bar):
        self.assertGreater(slowed['parts'], 1.0)
        self.assertNear(slowed['magic'], slowed['parts'],
                        0.1 * slowed['parts'])

  def test_automatic(self) -> None:
    """Its automatic, full throttle from standing, pulls the stand-in
    past 20 m/s in 8 s through first, second and third, its revolutions
    between idling and the limiter; let off, it slows with the engine;
    braked to a stop in neutral, the engine revs free, driving nothing;
    in reverse, it backs."""
    car = carOf('magic')
    drive = car[0].drive
    ran(car, 0.5)
    drive.throttle = 1.0
    gears, lowest, highest = set(), REDLINE, 0.0
    for _ in range(16):
      ran(car, 0.5)
      reading = readingOf(drive, car[2])
      gears.add(reading.gear)
      lowest, highest = min(lowest, reading.rpm), max(highest, reading.rpm)
    self.assertGreater(forwardOf(car), 20.0)
    self.assertTrue({'1', '2', '3'} <= gears, gears)
    self.assertGreater(lowest, 0.85 * IDLE)
    self.assertLessEqual(highest, REDLINE)
    going = forwardOf(car)
    drive.throttle = 0.0
    ran(car, 1.0)
    self.assertLess(forwardOf(car), going - 0.2)
    drive.asked = 'N'
    car[0].line.pressure = FOOT
    ran(car, 6.0)
    car[0].line.pressure = 0.0
    drive.throttle = 1.0
    ran(car, 0.5)
    self.assertGreater(readingOf(drive, car[2]).rpm, 3000.0)
    self.assertEqual([shaft.torque for shaft in drive.shafts], [0.0, 0.0])
    self.assertLess(abs(forwardOf(car)), 1.0)
    drive.asked, drive.throttle = 'R', 0.3
    ran(car, 3.0)
    self.assertLess(forwardOf(car), -1.0)

  def test_town(self) -> None:
    """Where the lap's file is: the city racer drives the stand-in round
    town as it drives the car of parts ('test_city.test_drives_in_town':
    in 25 s 250 m round or more, within 4 m of the road's middle,
    slipping under 15 degrees, never stranded)."""
    from worQt.phys._city import CITY_TRACK, cityCourse, cityGround
    from worQt.phys._city import realCarInCity
    from worQt.phys._realdriver import CityDriver
    if not os.path.isfile(os.path.normpath(CITY_TRACK)):
      self.skipTest('the city lap is not here')
    controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                               TuneUp((WheelSetup(),) * len(CORNERS)),
                               AutomaticDrive(), Antilock(_magiccar.WHEELS))
    assembly, states = realCarInCity(controls, _magiccar.magicCar)
    world = SmallSteps(GRAVITY, cityGround(), STEP, 1, 1e-7, 'cpu')
    driver = CityDriver(assembly, controls, cityCourse())
    clock, off, slip = 0.0, 0.0, 0.0
    for _ in range(round(25.0 / FRAME)):
      driver.take(states, FRAME)
      drivetrainWorked(controls.drive, states, FRAME)
      controls.brakes.worked(controls.line.pressure, assembly, states,
                             FRAME)
      states = world.advancedAll(assembly, states, FRAME, clock)
      clock += FRAME
      self.assertFalse(driver.stranded)
      if driver.speedOf(states) > 3.0:
        off = max(off, abs(driver.off))
        slip = max(slip, abs(driver.slip))
    self.assertGreater(driver.along, 250.0)
    self.assertLess(off, 4.0)
    self.assertLess(math.degrees(slip), 15.0)

  def test_cheaper(self) -> None:
    """Idling on the yard a second, the stand-in steps at least half
    again as fast as the car of parts (on the CPU, both alike)."""
    took = {}
    for kind in CARS:
      car = carOf(kind)
      ran(car, 0.2)
      began = time.perf_counter()
      ran(car, 1.0)
      took[kind] = time.perf_counter() - began
    self.assertLess(took['magic'], took['parts'] / 1.5, took)
