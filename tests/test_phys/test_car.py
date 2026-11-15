"""
TestCar covers the car and what it was made with: a turned solid (a
wheel) meets the road at its circles' lowest points, rolling true and,
spun in place, taking off as its angular momentum about the road says;
a motor twists two bodies against each other (and as a servo holds an
angle, as a brake stops a wheel and never turns it back); a driveshaft
drives its wheel, its housing and the wheel's bearer taking the twist
back, the angular momentum kept, its work booked; a strap only pulls
and a buffer only pushes; the car ('carBuilt') stands level at its
ride height, as high on a road with no grip (its coilovers carry it,
not its tyres' sideways grip), its engine's torque split between its
rear wheels alike (an open differential), coasts straight, drives straight,
steers left as its column is turned left (the inner wheel turned more),
brakes hard without turning or folding a wheel, and is stepped no
finer than 19 us (its rear rods' stiffer rubber sets it); it is
aligned (on slip plates its front wheels toed out 0.15 degrees, its
rear ones in 0.15, all leaning in 0.5; standing and rolling near it),
braking does not steer it (its steering axes meet the ground near the
tyres' middles), the anti-lock brakes it at over 8.5 m/s² from 25 m/s
straight, and on full lock at a walk, driven and braked, the rack's
stops keep its front wheels from folding past lock; at 'LIVE' fidelity
(a window's, four times the steps' length) it launches, brakes and
turns as at the reference.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import CAR_ROAD, ORIGIN, UNTURNED, Assembly, Body, Books
from worQt.phys import Drag, Drive, Motor, Spring, State, World, boxShape
from worQt.phys import camberOf, carBuilt, carWorld, cylinderShape, drive
from worQt.phys import plus, rotated, speedOf, steer, toeOf, turnAbout
from worQt.phys import FULL, LIVE, conjugate, minus
from worQt.phys._car import DRIVEN, POWER_BOOST, RACK, RACK_TRAVEL
from worQt.phys._car import STEER_LOCK, _wheelTurn
from worQt.phys._gearbox import DRIVELINE, FINAL, GEARS, LAUNCH, RPM
from worQt.phys._gearbox import engineTorque

from . import PhysTest

CAR = carBuilt(0.5)
WHEEL = CAR.assembly.bodies[CAR.wheels[0]]
RADIUS = 0.316
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
FRAME = 1.0 / 60.0


def wheelAt(speed: float, spin: float) -> State:
  """The 'wheelAt' function returns a car's wheel standing on the road,
  its axle along y, going 'speed' m/s along x, spun 'spin' rad/s about
  y."""
  turn = _wheelTurn(1)
  sink = WHEEL.mass * 9.81 / (2.0 * CAR_ROAD.stiffness)
  return State(plus((0.0, 0.0, RADIUS - sink), rotated(turn, WHEEL.centre)),
               turn, (speed, 0.0, 0.0), (0.0, spin, 0.0))


def headingOf(state: State) -> float:
  """The 'headingOf' function returns which way 'state' faces, deg."""
  ahead = rotated(state.turn, (1.0, 0.0, 0.0))
  return math.degrees(math.atan2(ahead[1], ahead[0]))


def driven(states: tuple, seconds: float, throttle: float,
           wanted: float) -> tuple:
  """The 'driven' function returns the car's 'states' driven on for
  'seconds', a frame at a time, as 'throttle' and the hands ('wanted'
  rad of column) say."""
  world = carWorld()
  for _ in range(int(round(seconds / FRAME))):
    steer(CAR, wanted)
    drive(CAR, states, throttle, FRAME)
    states = world.advancedAll(CAR.assembly, states, FRAME)
  return states


def moving(speed: float) -> tuple:
  """The 'moving' function returns the car as built, going 'speed' m/s
  forward, its wheels rolling with it."""
  out = []
  for index, state in enumerate(CAR.states):
    spin = (0.0, speed / RADIUS, 0.0) if index in CAR.wheels else (
      state.spin)
    out.append(State(state.place, state.turn, (speed, 0.0, 0.0), spin))
  return tuple(out)


class TestCar(PhysTest):
  """Tests for the car and what it was made with."""

  #  The springs' world's car, stepped in its world's one thread: minutes
  #  a class (killed at the harness's 30 s, the user's run of 2026-11-14).
  __time_out__ = 3600.0

  def test_rolls_true(self) -> None:
    """A wheel rolled along at 8 m/s goes on at 8 m/s, the kernel as the
    plain Python."""
    alone = Assembly((WHEEL,), ())
    gone = []
    for compiled in (False, True):
      world = World((0.0, 0.0, -9.81), 1e-3, CAR_ROAD, None, compiled)
      gone.append(world.advancedAll(alone, (wheelAt(8.0, 8.0 / RADIUS),),
                                    1.0)[0])
    self.assertNear(gone[0].velocity[0], 8.0, 1e-4)
    self.assertNear((gone[0].place, gone[0].velocity),
                    (gone[1].place, gone[1].velocity), 1e-12)

  def test_spun_takes_off(self) -> None:
    """A wheel spun where it stands takes off rolling, its angular
    momentum about the road kept: at its moment over its moment and its
    mass times the radius squared, of its rim's speed."""
    alone = Assembly((WHEEL,), ())
    state = carWorld().advancedAll(alone, (wheelAt(0.0, 10.0),), 1.5)[0]
    axle = rotated(state.turn, (0.0, 0.0, 1.0))
    inertia = WHEEL.inertiaIn(state)
    about = sum(axle[i] * inertia[i][j] * axle[j] for i in range(3)
                for j in range(3))
    wanted = 10.0 * RADIUS * about / (about + WHEEL.mass * RADIUS ** 2)
    self.assertNear(state.velocity[0], wanted, 1e-3)

  def test_motor(self) -> None:
    """A motor of 5 N m between two blocks in space spins them up
    opposite ways, 5 N m times the time over the moment, its work
    booked as an actuator's, the kernel as the plain Python."""
    pair = Assembly((BLOCK, BLOCK), (Motor(0, 1, (0.0, 0.0, 1.0),
                                           Drive(5.0)),))
    start = (State(ORIGIN), State((1.0, 0.0, 0.0)))
    moment = BLOCK.inertia[2][2]
    for compiled in (False, True):
      space = World((0.0, 0.0, 0.0), 1e-3, None, None, compiled)
      states, books = space.booked(pair, start, 2.0, 0.0, Books())
      self.assertNear(states[1].spin[2], 10.0 / moment, 1e-9)
      self.assertNear(states[0].spin[2], -10.0 / moment, 1e-9)
      self.assertNear(books.actuators, 100.0 / moment, 1e-6)

  def test_servo(self) -> None:
    """A motor as a servo turns a block to its target and holds it."""
    drive_ = Drive()
    drive_.stiffness, drive_.damping = 50.0, 4.0
    drive_.most, drive_.target = 100.0, 0.5
    held = Assembly((BLOCK,), (Motor(None, 0, (0.0, 0.0, 1.0), drive_),))
    for compiled in (False, True):
      space = World((0.0, 0.0, 0.0), 1e-3, None, None, compiled)
      state = space.advancedAll(held, (State(ORIGIN),), 3.0)[0]
      angle = 2.0 * math.atan2(state.turn[3], state.turn[0])
      self.assertNear(angle, 0.5, 1e-6)

  def test_brake(self) -> None:
    """A motor as a brake (damping, no stiffness) stops a spinning block
    and never turns it back."""
    brake = Drive()
    brake.damping, brake.most = 50.0, 2.0
    braked = Assembly((BLOCK,), (Motor(None, 0, (0.0, 0.0, 1.0), brake),))
    state = State(ORIGIN, UNTURNED, (0.0, 0.0, 0.0), (0.0, 0.0, 30.0))
    space = World((0.0, 0.0, 0.0), 1e-3)
    for _ in range(30):
      state = space.advancedAll(braked, (state,), 0.1)[0]
      self.assertGreaterEqual(state.spin[2], 0.0)
    self.assertLess(state.spin[2], 1e-6)

  def test_driveshaft(self) -> None:
    """A driveshaft of 40 N m from a block to a disc borne by another
    block, all in space, spins the disc up about its axle, the blocks
    taking the twist back: the three's angular momentum stays nought,
    the work booked is the energy they gained, the kernel as the plain
    Python (to 1e-9: the disc spins at 144 rad/s)."""
    disc = Body.of(cylinderShape(0.3, 0.2, 16), 500.0)
    shaft = Motor(0, 2, (0.0, 1.0, 0.0), Drive(40.0), 1, (0.05, 0.1, 0.0),
                  (0.0, -0.1, 0.0))
    three = Assembly((BLOCK, BLOCK, disc), (shaft,))
    start = (State(ORIGIN), State((0.0, 1.0, 0.1)),
             State((0.1, 1.3, 0.25), turnAbout((0.0, 0.0, 1.0), 0.4)))
    ran = []
    for compiled in (False, True):
      space = World((0.0, 0.0, 0.0), 1e-3, None, None, compiled)
      states, books = space.booked(three, start, 1.0, 0.0, Books())
      held = [sum(body.angularMomentumOf(state)[i]
                  for body, state in zip(three.bodies, states))
              for i in range(3)]
      self.assertNear(held, ORIGIN, 1e-9)
      gained = sum(body.kineticOf(state)
                   for body, state in zip(three.bodies, states))
      self.assertNear(books.actuators, gained, 1e-3 * gained)
      axle = rotated(states[2].turn, (0.0, 1.0, 0.0))
      spin = sum((states[2].spin[i] - states[1].spin[i]) * axle[i]
                 for i in range(3))
      self.assertGreater(spin, 10.0)
      ran.append(states)
    for python, kernel in zip(*ran):
      self.assertNear((python.place, python.turn, python.spin),
                      (kernel.place, kernel.turn, kernel.spin), 1e-9)

  def test_shares(self) -> None:
    """Driven, only the rear wheels are (rear wheel drive: two
    halfshafts), each getting half of what the engine puts through its
    gearbox, alike (an open differential): standing, first gear's at
    the launch revolutions (the clutch slipping); at 40 m/s in fourth,
    the engine's torque at the revolutions the wheels turn it at; the
    brakes let go."""
    self.assertEqual(DRIVEN, (2, 3))
    self.assertEqual(len(CAR.shafts), 2)
    self.assertEqual(len(CAR.links.halfshafts), 2)
    for speed, gear in ((0.0, 1), (40.0, 4)):
      ratio = GEARS[gear - 1] * FINAL
      rpm = speed / RADIUS * ratio * RPM if speed else LAUNCH
      whole = POWER_BOOST * engineTorque(rpm) * ratio * DRIVELINE
      states = moving(speed) if speed else CAR.states
      CAR.gearbox.reset()
      CAR.gearbox.gear = gear
      drive(CAR, states, 1.0, FRAME)
      for shaft in CAR.shafts:
        self.assertNear(abs(shaft.torque), 0.5 * whole, 1e-3 * whole)
      for brake in CAR.brakes:
        self.assertEqual((brake.damping, brake.most), (0.0, 0.0))
    CAR.gearbox.reset()
    drive(CAR, CAR.states, 0.0, FRAME)

  def test_live(self) -> None:
    """At 'LIVE' fidelity (a window's) the car does what it does at the
    reference ('FULL'): a 3 s launch within 0.02 m/s, braked 1.5 s from
    25 m/s within 0.15 m/s (the anti-lock's pulses differ), a 2 s turn
    at 30 m/s within 0.2 degrees of heading."""
    found = []
    for fidelity in (FULL, LIVE):
      car = CAR if fidelity is FULL else carBuilt(0.5, fidelity)
      world, runs = carWorld(fidelity), []
      for speed, throttle, column, seconds in ((0.0, 1.0, 0.0, 3.0),
                                                (25.0, -1.0, 0.0, 1.5),
                                                (30.0, 0.3, 0.08, 2.0)):
        car.gearbox.reset()
        car.gearbox.gear = 3 if speed > 28.0 else 1
        car.antilock[:] = [1.0] * len(car.antilock)
        states = car.states if not speed else tuple(
          State(s.place, s.turn, (speed, 0.0, 0.0),
                (0.0, speed / RADIUS, 0.0) if index in car.wheels
                else s.spin, s.bristles, s.holds, s.rest)
          for index, s in enumerate(car.states))
        for count in range(int(round(seconds / FRAME))):
          steer(car, column)
          drive(car, states, throttle, FRAME)
          states = world.advancedAll(car.assembly, states, FRAME,
                                     count * FRAME)
        ahead = rotated(states[car.chassis].turn, (1.0, 0.0, 0.0))
        runs.append((speedOf(car, states),
                     math.degrees(math.atan2(ahead[1], ahead[0]))))
      steer(car, 0.0)
      car.gearbox.reset()
      drive(car, car.states, 0.0, FRAME)
      found.append(runs)
    (launch, braked, turned), (live, slowed, swung) = found
    self.assertNear(live[0], launch[0], 0.02)
    self.assertNear(slowed[0], braked[0], 0.15)
    self.assertNear(swung[1], turned[1], 0.2)

  def test_strap_and_buffer(self) -> None:
    """A strap pulls stretched and holds nothing squeezed; a buffer
    pushes squeezed and holds nothing stretched."""
    strap = Spring(None, ORIGIN, None, ORIGIN, 100.0, 1.0, 0.0, True,
                   False)
    buffer = Spring(None, ORIGIN, None, ORIGIN, 100.0, 1.0, 0.0, False,
                    True)
    self.assertNear(strap.pullOf(ORIGIN, (0.0, 0.0, 1.5)),
                    (0.0, 0.0, 50.0), 1e-12)
    self.assertNear(strap.pullOf(ORIGIN, (0.0, 0.0, 0.5)), ORIGIN, 0.0)
    self.assertNear(buffer.pullOf(ORIGIN, (0.0, 0.0, 1.5)), ORIGIN, 0.0)
    self.assertNear(buffer.pullOf(ORIGIN, (0.0, 0.0, 0.5)),
                    (0.0, 0.0, -50.0), 1e-12)
    self.assertEqual(strap.storedOf(ORIGIN, (0.0, 0.0, 0.5)), 0.0)

  def test_stands(self) -> None:
    """Built, the car stands level at the height it was built at (its
    chassis' middle within 3 mm), its wheels straight and upright; on a
    road with no grip it stands as high (its coilovers carry it, not its
    tyres' sideways grip)."""
    chassis = CAR.states[CAR.chassis]
    built = CAR.assembly.bodies[CAR.chassis].centre
    self.assertNear(chassis.place[2], built[2], 3e-3)
    self.assertNear(chassis.turn[1], 0.0, 1e-3)
    for corner in range(4):
      self.assertLess(abs(math.degrees(toeOf(CAR, CAR.states, corner))),
                      0.2)
      self.assertLess(abs(math.degrees(camberOf(CAR, CAR.states,
                                                corner))), 0.5)
    slick = World((0.0, 0.0, -9.81), 1e-3, CAR_ROAD._replace(grip=0.0))
    states = slick.advancedAll(CAR.assembly, CAR.states, 1.0)
    self.assertNear(states[CAR.chassis].place[2], chassis.place[2], 5e-3)

  def test_coasts(self) -> None:
    """Let roll at 10 m/s, the car goes on straight, its wheels toed
    under a degree, losing under 0.1 m/s in a second (the air's drag
    takes 0.08: 60 N)."""
    states = driven(moving(10.0), 1.0, 0.0, 0.0)
    self.assertGreater(speedOf(CAR, states), 9.9)
    for corner in range(4):
      self.assertLess(abs(math.degrees(toeOf(CAR, states, corner))), 1.0)

  def test_drives(self) -> None:
    """Driven two seconds from standing, the car is past 7 m/s (11.4
    when measured: rear wheel drive, a small roadster's engine, the
    shafts' traction control holding the rear wheels at their grip),
    going straight, its rear corners not hopping (with traction control
    once a frame, at 1600 N m at the wheels they hopped at 31 Hz and it
    made 5.4)."""
    states = driven(CAR.states, 2.0, 1.0, 0.0)
    self.assertGreater(speedOf(CAR, states), 7.0)
    self.assertLess(abs(headingOf(states[CAR.chassis])), 1.0)

  def test_steers(self) -> None:
    """Its column turned left, the car turns left, its inner (left)
    front wheel turned more than its outer (Ackermann)."""
    states = driven(moving(5.0), 1.0, 0.0, 0.3)
    self.assertGreater(states[CAR.chassis].spin[2], 0.2)
    left, right = toeOf(CAR, states, 0), toeOf(CAR, states, 1)
    self.assertGreater(right, 0.1)
    self.assertGreater(left, right)

  def test_brakes(self) -> None:
    """Braked hard from 10 m/s, the car is under 2 m/s in 1.5 s (over
    5.3 m/s² of braking), straight, every wheel upright on its knuckle
    within 5 degrees (none folded)."""
    states = driven(moving(10.0), 1.5, -1.0, 0.0)
    self.assertLess(abs(speedOf(CAR, states)), 2.0)
    self.assertLess(abs(headingOf(states[CAR.chassis])), 2.0)
    for corner in range(4):
      self.assertLess(abs(math.degrees(camberOf(CAR, states, corner))),
                      5.0)

  def test_step(self) -> None:
    """The car's springs are stepped no finer than 19 us (19.6: the
    rear rods' bushings, 'REAR_ROD', set it; on the front's rubber it
    was 25.6)."""
    self.assertGreater(carWorld().springStepFor(CAR.assembly), 19e-6)

  def test_aligned(self) -> None:
    """On a road without grip (an aligner's slip plates) the front
    wheels toe out 0.15 degrees each, the rear ones in 0.15, every wheel
    leans in 0.5 (each within 0.02; user: "front .15 deg toe out, rear
    .15 deg toe in per wheel"). Standing on the road its tyres hold the
    wheels nearer as built (front 0.04 out, rear 0.19 in); rolling at
    15 m/s for 2 s the fronts' own toe-out pushes them out further on
    their rubber (0.25), the rears stay (0.19): toes within 0.2 of the
    alignment, every wheel leaning in, under a degree and a quarter."""
    slick = World((0.0, 0.0, -9.81), 1e-3, CAR_ROAD._replace(grip=0.0))
    plates = slick.advancedAll(CAR.assembly, CAR.states, 1.0)
    aligned = (-0.15, -0.15, 0.15, 0.15)
    for states, within in ((plates, 0.02), (CAR.states, 0.2),
                           (driven(moving(15.0), 2.0, 0.0, 0.0), 0.2)):
      for corner, side in enumerate((1, -1, 1, -1)):
        toeIn = -side * math.degrees(toeOf(CAR, states, corner))
        self.assertNear(toeIn, aligned[corner], within)
        camber = math.degrees(camberOf(CAR, states, corner))
        if within < 0.1:
          self.assertNear(camber, -0.5, within)
        self.assertLess(camber, 0.0)
        self.assertGreater(camber, -1.25)

  def test_braking_steers_not(self) -> None:
    """Braked hard from 15 m/s, the front wheels point within a degree
    and a quarter of straight at a third, a half and seven tenths of a
    second (its steering axes meet the ground 14 mm inside the tyres'
    middles, its lower wishbones wide at the frame; with 92 mm and
    narrow ones they toed out 2.4 degrees)."""
    for seconds in (0.3, 0.5, 0.7):
      states = driven(moving(15.0), seconds, -1.0, 0.0)
      for corner in range(2):
        self.assertLess(abs(math.degrees(toeOf(CAR, states, corner))),
                        1.25)

  def test_antilock(self) -> None:
    """Braked hard from 25 m/s for 1.5 s, the car is under 12 m/s (over
    8.6 m/s², its wheels let go as they lock), still heading within a
    degree of straight."""
    states = driven(moving(25.0), 1.5, -1.0, 0.0)
    self.assertLess(speedOf(CAR, states), 12.0)
    self.assertLess(abs(headingOf(states[CAR.chassis])), 1.0)

  def test_rack_stops(self) -> None:
    """On full lock at a walk, driven 1.5 s and braked 1 s, either way,
    the rack slides no more than 15 mm past its stops and no front wheel
    turns past 40 degrees (without stops one ran on to 50 and folded
    over its tie rod)."""
    world = carWorld()
    for lock in (STEER_LOCK, -STEER_LOCK):
      states = CAR.states
      for frame in range(int(round(2.5 / FRAME))):
        steer(CAR, lock)
        drive(CAR, states, 1.0 if frame * FRAME < 1.5 else -1.0, FRAME)
        states = world.advancedAll(CAR.assembly, states, FRAME)
        chassis = states[CAR.chassis]
        slid = rotated(conjugate(chassis.turn),
                       minus(states[CAR.rack].place, chassis.place))
        self.assertLess(abs(slid[1] - RACK[1]), RACK_TRAVEL + 0.015)
        for corner in range(2):
          self.assertLess(abs(math.degrees(toeOf(CAR, states, corner))),
                          40.0)
      steer(CAR, 0.0)
      drive(CAR, CAR.states, 0.0, FRAME)

  def test_drag(self) -> None:
    """A 250 kg block let go at 50 m/s in still air, its drag area 1
    m², slows as the drag says (to 50 / (1 + 0.6 x 50 x 5 / 250) =
    31.25 m/s in 5 s, within 1e-4), the heat booked as a damper's what
    it lost, the kernel as the plain Python."""
    block = Body.of(boxShape(1.0, 0.5, 0.5), 1000.0)
    alone = Assembly((block,), (Drag(0, 1.0),))
    start = (State(ORIGIN, UNTURNED, (50.0, 0.0, 0.0)),)
    ran = []
    for compiled in (False, True):
      space = World((0.0, 0.0, 0.0), 1e-3, None, None, compiled)
      states, books = space.booked(alone, start, 5.0, 0.0, Books())
      speed = states[0].velocity[0]
      self.assertNear(speed, 31.25, 31.25e-4)
      lost = 0.5 * block.mass * (50.0 ** 2 - speed ** 2)
      self.assertNear(books.dampers, lost, 1e-6 * lost)
      ran.append(speed)
    self.assertNear(ran[0], ran[1], 1e-9)
