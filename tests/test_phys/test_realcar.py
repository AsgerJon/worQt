"""
TestRealCar covers the real car ('_realcar.realCar'; user, 2026-11-14:
"continue to assemble the real car"): on the ground it rides as built
(each wheel's middle to 3 mm in the car's frame), still, its engine
idling; put in first (the clutch down, the stick moved, the engine
revved, the clutch let up as a foot does) it drives off forward, the
rear wheels turning through the differential and the half shafts' joints
together as fast as the carrier (their mean to 3 %), and its brakes stop
it; steered left standing, its front wheels turn left, its rears not;
stopped hard from 15 m/s its anti-lock keeps its wheels turning (user,
2026-11-14: "Key_S: disc-brakes with ABS") where without it they lock,
and the handbrake locks its rear wheels at once ("instantly locks
wheels"), its fronts rolling on. Its controls take any share (user,
2026-11-15: "make sure that the car can accept continuous amounts of
throttle, break and turning"): its front wheels turn as far as the
steering wheel is turned, either way; its brakes slow it as hard as the
foot presses (short of locking a wheel); each tenth more throttle in
fourth speeds it up as much more (short of spinning a rear wheel: at
332 kg the car's rear is light). Tolerant: tyres are chaotic.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import BrakeLine, FourthWall, SmallSteps, State
from worQt.phys import conjugate, minus, norm, rotated, scaled
from worQt.phys._carcass import TYRE_YARD
from worQt.phys._drivetrain import DrivetrainControls, drivetrainWorked
from worQt.phys._drivetrain import readingOf, rpmOf, spinAbout
from worQt.phys._realcar import CHASSIS, CORNERS, FOOT, WHEELBASE
from worQt.phys._realcar import WHEELS
from worQt.phys._realcar import Antilock, RealCarControls, realCar
from worQt.phys._rig import HUB_HEIGHT, TuneUp, WheelSetup
from worQt.phys._tyred import tyreOf

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)


class TestRealCar(PhysTest):
  """Tests for the real car (about three minutes on the CPU)."""

  __time_out__ = 1200.0

  def setUp(self) -> None:
    """A real car on the ground, still, idling; its world."""
    self.controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                                    TuneUp((WheelSetup(),) * len(CORNERS)),
                                    DrivetrainControls(), Antilock())
    self.assembly, self.states = realCar(self.controls)
    self.world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 1e-7, 'cpu')
    self.clock = 0.0

  def ran(self, seconds: float, locked: bool = False) -> None:
    """Works and steps the car 'seconds' on, a frame at a time, its
    brakes through the anti-lock (or, 'locked', straight off the foot's
    line)."""
    c = self.controls
    for _ in range(round(seconds / FRAME)):
      drivetrainWorked(c.drive, self.states, FRAME)
      c.brakes.worked(c.line.pressure, self.assembly, self.states, FRAME)
      if locked:
        for line in c.brakes.lines:
          line.pressure = c.line.pressure
      self.states = self.world.advancedAll(self.assembly, self.states,
                                           FRAME, self.clock)
      self.clock += FRAME

  def rolling(self, speed: float) -> None:
    """Sets the car, settled, going 'speed' m/s ahead, its wheels
    rolling so (its drivetrain, in neutral, brought along by its
    gears)."""
    self.ran(0.5)
    wheels = {WHEELS[c]: side
              for c, (_, side) in enumerate(CORNERS)}
    radius = next(tyre.radius for tyre in self.assembly.tyres
                  if tyre.body in wheels)
    moving = []
    for k, state in enumerate(self.states):
      spin = state.spin
      if k in wheels:
        spin = scaled(rotated(state.turn, (0.0, 0.0, 1.0)),
                      wheels[k] * speed / radius)
      moving.append(State(state.place, state.turn, (speed, 0.0, 0.0),
                          spin))
    self.states = tuple(moving)
    self.ran(0.3)

  def forward(self, ) -> float:
    """Returns how fast the car goes along its chassis' forward, m/s."""
    chassis = self.states[CHASSIS]
    return rotated(conjugate(chassis.turn), chassis.velocity)[0]

  def fronts(self, ) -> float:
    """Returns how far the front wheels are turned left on the chassis
    on their mean, degrees."""
    chassis, turned = self.states[CHASSIS], []
    for c, (at, side) in enumerate(CORNERS):
      if at != 0.0:
        continue
      wheel = self.states[WHEELS[c]]
      axle = rotated(conjugate(chassis.turn), rotated(wheel.turn,
                                                      (0.0, 0.0, 1.0)))
      turned.append(math.degrees(math.atan2(axle[1], axle[0]))
                    - 90.0 * side)
    return sum(turned) / len(turned)

  def rims(self, ) -> list[float]:
    """Returns how fast each wheel's tread goes round, as a share of
    how fast the road goes under it (front left, front right, rear left,
    rear right; one where it all but stands)."""
    out = []
    for c in range(len(CORNERS)):
      going, rim = self.controls.brakes.rolling(self.assembly,
                                                self.states, c)
      out.append(rim / going if abs(going) > 0.5 else 1.0)
    return out

  def test_rides(self) -> None:
    """Settled, each wheel's middle is as built in the car's frame (3
    mm), the car has not moved (a centimetre), the engine idles."""
    start = self.states[CHASSIS].place
    self.ran(1.0)
    chassis = self.states[CHASSIS]
    body = self.assembly.bodies[CHASSIS]
    for c in range(len(CORNERS)):
      wheel = self.states[WHEELS[c]]
      own = rotated(conjugate(chassis.turn), minus(wheel.place,
                                                   chassis.place))
      self.assertNear(own[2] + body.centre[2], HUB_HEIGHT, 0.003)
    self.assertLess(norm(minus(chassis.place, start)), 0.01)
    rpm = rpmOf(self.states, self.controls.drive.layout.flywheel)
    self.assertGreater(rpm, 650.0)
    self.assertLess(rpm, 950.0)

  def test_drives(self) -> None:
    """In first, revved and its clutch let up, it drives off forward
    (two metres, 10 km/h or more in two and a half seconds, upright),
    its rear wheels' mean as fast as the carrier (3 %); braked, it
    stops (under 1 km/h in two seconds)."""
    drive = self.controls.drive
    drive.pedal, drive.asked = 1.0, '1'
    for _ in range(10):
      self.ran(0.2)
      if drive.shifter.engaged == '1' and drive.shifter.throw == -1.0:
        break
    self.assertEqual(drive.shifter.engaged, '1')
    start = self.states[CHASSIS].place
    drive.throttle = 0.5
    self.ran(0.4)
    drive.pedal = 0.0
    self.ran(2.5)
    chassis = self.states[CHASSIS]
    self.assertTrue(drive.running)
    self.assertGreater(chassis.place[0] - start[0], 2.0)
    self.assertGreater(3.6 * chassis.velocity[0], 10.0)
    self.assertGreater(rotated(chassis.turn, (0.0, 0.0, 1.0))[2], 0.99)
    read = readingOf(drive, self.states)
    carrier = spinAbout(self.states[drive.layout.carrier],
                        (0.0, 1.0, 0.0)) * tyreOf(1, 2.3e5).radius
    self.assertNear(0.5 * (read.left + read.right), carrier,
                    0.03 * abs(carrier))
    drive.throttle, drive.pedal = 0.0, 1.0
    self.controls.line.pressure = 40e5
    self.ran(2.0)
    self.assertLess(3.6 * norm(self.states[CHASSIS].velocity), 1.0)

  def test_steers(self) -> None:
    """Standing, its steering wheel held 3 rad left, its front wheels
    turn left 8 to 15 degrees, its rears not (half a degree)."""
    self.ran(0.5)
    self.controls.steer.value = 3.0
    self.ran(1.0)
    chassis = self.states[CHASSIS]
    for c, (at, side) in enumerate(CORNERS):
      wheel = self.states[WHEELS[c]]
      axle = rotated(conjugate(chassis.turn), rotated(wheel.turn,
                                                      (0.0, 0.0, 1.0)))
      turned = math.degrees(math.atan2(axle[1], axle[0])) - 90.0 * side
      if at == 0.0:
        self.assertGreater(turned, 8.0)
        self.assertLess(turned, 15.0)
      else:
        self.assertLess(abs(turned), 0.5)

  def test_antilock(self) -> None:
    """Stopped hard from 15 m/s (the foot's 'FOOT'), its wheels keep
    turning (each its rim at least half the road's speed on the mean
    over the first second) and it stops (under 1 km/h) within 2.5 s,
    straight (2 degrees); without the anti-lock, the same foot locks
    every wheel (a tenth of the road's speed)."""
    for locked in (False, True):
      self.setUp()
      self.rolling(15.0)
      self.controls.line.pressure = FOOT
      seen = []
      for _ in range(6):
        self.ran(1.0 / 6.0, locked)
        seen.append(self.rims())
      means = [sum(rims[c] for rims in seen) / len(seen)
               for c in range(len(CORNERS))]
      if locked:
        for mean in means:
          self.assertLess(mean, 0.1)
        continue
      for mean in means:
        self.assertGreater(mean, 0.5)
      self.ran(1.5)
      chassis = self.states[CHASSIS]
      self.assertLess(3.6 * norm(chassis.velocity), 1.0)
      ahead = rotated(chassis.turn, (1.0, 0.0, 0.0))
      self.assertLess(abs(math.degrees(math.atan2(ahead[1], ahead[0]))),
                      2.0)

  def test_handbrake(self) -> None:
    """Going 15 m/s, the handbrake pulled locks the rear wheels at once
    (a tenth of the road's speed within a fifth of a second), the front
    ones rolling on (nine tenths)."""
    self.rolling(15.0)
    self.controls.brakes.pulled = True
    self.ran(0.2)
    rims = self.rims()
    for c, (at, _) in enumerate(CORNERS):
      if at == 0.0:
        self.assertGreater(rims[c], 0.9)
      else:
        self.assertLess(rims[c], 0.1)

  def test_steers_in_shares(self) -> None:
    """Rolling at 5 m/s, its steering wheel held a quarter, a half and
    all of 3 rad left, its front wheels turn as far as it (each over
    its share within 5 % of the others), and as far right as left."""
    turned = {}
    for wheel in (0.75, 1.5, 3.0, -1.5):
      self.setUp()
      self.rolling(5.0)
      self.controls.steer.value = wheel
      self.ran(0.6)
      turned[wheel] = self.fronts()
    rates = [turned[wheel] / wheel for wheel in (0.75, 1.5, 3.0)]
    for rate in rates:
      self.assertGreater(rate, 0.0)
      self.assertNear(rate, rates[-1], 0.05 * rates[-1])
    self.assertNear(-turned[-1.5], turned[1.5], 0.05 * turned[1.5])

  def test_brakes_in_shares(self) -> None:
    """From 15 m/s, the foot pressing 6, 12 and 18 bar (short of locking
    a wheel: the light rear ones lock from about 24), the car slows the
    harder the harder it presses, by as much (over the rolling's own
    slowing, each over its pressure within 10 % of the others)."""
    slowing = {}
    for bar in (0.0, 6.0, 12.0, 18.0):
      self.setUp()
      self.rolling(15.0)
      self.controls.line.pressure = bar * 1e5
      self.ran(0.2)
      before = self.forward()
      self.ran(0.5)
      slowing[bar] = (before - self.forward()) / 0.5
    rates = [(slowing[bar] - slowing[0.0]) / bar for bar in (6.0, 12.0,
                                                             18.0)]
    for rate in rates:
      self.assertGreater(rate, 0.0)
      self.assertNear(rate, rates[-1], 0.1 * rates[-1])

  def test_throttle_in_shares(self) -> None:
    """Rolling at 20 m/s in fourth (in first, at 332 kg, a fifth of the
    throttle already spins a rear wheel), two, three, four and five
    tenths of the throttle speed it up the more the more is open, each
    tenth more by as much more (within 20 % of the mean step: the
    engine's own losses take a fixed share)."""
    speeding = []
    for opened in (0.2, 0.3, 0.4, 0.5):
      self.setUp()
      self.rolling(20.0)
      drive = self.controls.drive
      drive.pedal, drive.asked = 1.0, '4'
      for _ in range(15):
        self.ran(0.2)
        if drive.shifter.engaged == '4':
          break
      self.assertEqual(drive.shifter.engaged, '4')
      drive.throttle = 0.3
      self.ran(0.2)
      drive.pedal = 0.0
      self.ran(0.6)
      drive.throttle = opened
      self.ran(0.3)
      before = self.forward()
      self.ran(0.5)
      speeding.append((self.forward() - before) / 0.5)
    steps = [b - a for a, b in zip(speeding, speeding[1:])]
    mean = sum(steps) / len(steps)
    self.assertGreater(speeding[0], 0.0)
    for step in steps:
      self.assertGreater(step, 0.0)
      self.assertNear(step, mean, 0.2 * mean)

  def test_balanced(self) -> None:
    """With its driver in it, the car's middle of mass lies at its
    wheelbase's middle (a centimetre; user, 2026-11-15: "assume the
    driver weight brings center of gravity back to even between from and
    rear")."""
    mass = sum(body.mass for body in self.assembly.bodies)
    middle = sum(body.mass * state.place[0] for body, state in zip(
      self.assembly.bodies, self.states)) / mass
    self.assertNear(middle, -0.5 * WHEELBASE, 0.01)

  def test_flywheel(self) -> None:
    """The flywheel weighs what the tune-up sets ('TuneUp.flywheel', as
    built 'FLYWHEEL_MASS'), and the lighter it is the faster the engine's
    revs fall (user, 2026-11-15: "If it's too heavy. the engine speed
    falls too slowly"): revved past 4000 in neutral and let go (the
    throttle shut in an eighth of a second), a 6 kg one falls half as
    far again as the 20 kg one in the fifth of a second after (measured:
    about 6000 rpm/s against 1600)."""
    fell = {}
    for kilograms in (6.0, 20.0):
      self.controls = RealCarControls(
        BrakeLine(0.0), FourthWall(0.0), TuneUp(
          (WheelSetup(),) * len(CORNERS), kilograms), DrivetrainControls(),
        Antilock())
      self.assembly, self.states = realCar(self.controls)
      drive = self.controls.drive
      flywheel = drive.layout.flywheel
      self.assertNear(self.assembly.bodies[flywheel].mass, kilograms, 1e-9)
      drive.throttle = 1.0
      for _ in range(40):
        self.ran(0.05)
        if rpmOf(self.states, flywheel) > 4000.0:
          break
      drive.throttle = 0.0
      self.ran(0.15)
      before = rpmOf(self.states, flywheel)
      self.ran(0.2)
      fell[kilograms] = before - rpmOf(self.states, flywheel)
    self.assertGreater(fell[6.0], 1.5 * fell[20.0])
