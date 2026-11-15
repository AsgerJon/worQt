"""
TestSteering covers the steering wheel ('SteeringWheel') the keys turn
and, through it, the car: a key held turns the wheel its way at 180
degrees a second, no further than 135; let go it comes back at 270 a
second and stops straight; a key against the way it lies turns it back
no slower than letting go; the column asks the wheel's share of the
column's lock. Driven: a short turn let go, the car goes straight
again; the handbrake locks the rear wheels on their knuckles at once
and, with a little steering at 15 m/s, swings the car round where the
steering alone turns it a little; and at 'LIVE' fidelity (what a Qt
window steps at: half the steps, the ground met at the hull's corners)
the car brakes, turns and is swung round by the handbrake as at 'FULL'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import FULL, LIVE, Fidelity, State, carBuilt, carWorld
from worQt.phys import dot, drive, minus, rotated, speedOf, steer
from worQt.phys._car import STEER_LOCK, handbrake
from worQt.phys._steering import BACK, PUSH, WHEEL_LOCK, SteeringWheel

from . import PhysTest

CAR = carBuilt(0.5)
RADIUS = 0.316
FRAME = 1.0 / 60.0


def moving(speed: float) -> tuple:
  """The 'moving' function returns the car as built, going 'speed' m/s
  forward, its wheels rolling with it."""
  out = []
  for index, state in enumerate(CAR.states):
    spin = (0.0, speed / RADIUS, 0.0) if index in CAR.wheels else (
      state.spin)
    out.append(State(state.place, state.turn, (speed, 0.0, 0.0), spin))
  return tuple(out)


def headingOf(states: tuple) -> float:
  """The 'headingOf' function returns which way the car faces, deg."""
  ahead = rotated(states[CAR.chassis].turn, (1.0, 0.0, 0.0))
  return math.degrees(math.atan2(ahead[1], ahead[0]))


def driven(states: tuple, seconds: float, keys: object,
           fidelity: Fidelity = FULL) -> tuple:
  """The 'driven' function returns the car's 'states' driven on for
  'seconds', a frame at a time, the keys at each time as 'keys' says
  (steering, throttle, handbrake): the steering turning the wheel, the
  hands the column after it, the pedals and the handbrake straight to
  the car, in a world as faithful as 'fidelity' says; and the car's yaw
  rates on the way, rad/s."""
  world, wheel, yaws = carWorld(fidelity), SteeringWheel(), []
  for frame in range(int(round(seconds / FRAME))):
    steering, throttle, pulled = keys(frame * FRAME)
    wheel.turned(steering, FRAME)
    steer(CAR, wheel.column)
    drive(CAR, states, throttle, FRAME)
    handbrake(CAR, pulled)
    states = world.advancedAll(CAR.assembly, states, FRAME)
    yaws.append(states[CAR.chassis].spin[2])
  steer(CAR, 0.0)
  drive(CAR, CAR.states, 0.0, FRAME)
  return states, yaws


class TestSteering(PhysTest):
  """Tests for the steering wheel and the car driven through it."""

  #  The springs' world's car, stepped in its world's one thread: minutes
  #  a class (killed at the harness's 30 s, the user's run of 2026-11-14).
  __time_out__ = 3600.0

  def test_pushes(self) -> None:
    """A quarter second of the left key, a frame at a time, turns the
    wheel 45 degrees left; of the right key, 45 right."""
    for steering in (1, -1):
      wheel = SteeringWheel()
      for _ in range(15):
        wheel.turned(steering, FRAME)
      self.assertNear(wheel.angle, steering * math.radians(45.0), 1e-12)

  def test_lock(self) -> None:
    """Held two seconds, the wheel stops at 135 degrees, the column
    asked to its lock."""
    wheel = SteeringWheel()
    for _ in range(120):
      wheel.turned(-1, FRAME)
    self.assertEqual(wheel.angle, -WHEEL_LOCK)
    self.assertEqual(math.radians(135.0), WHEEL_LOCK)
    self.assertNear(wheel.column, -STEER_LOCK, 1e-12)

  def test_returns(self) -> None:
    """Let go at either lock, the wheel is halfway back a quarter second
    later and straight (exactly, not past) half a second later."""
    for lock in (WHEEL_LOCK, -WHEEL_LOCK):
      wheel = SteeringWheel()
      wheel.angle = lock
      for _ in range(15):
        wheel.turned(0, FRAME)
      self.assertNear(wheel.angle, 0.5 * lock, 1e-12)
      for _ in range(30):
        wheel.turned(0, FRAME)
      self.assertEqual(wheel.angle, 0.0)

  def test_against(self) -> None:
    """A key held against the way the wheel lies turns it back as fast
    as letting go would (faster than it pushes), then on at its push
    once past straight."""
    self.assertGreater(BACK, PUSH)
    wheel = SteeringWheel()
    wheel.angle = math.radians(90.0)
    wheel.turned(-1, FRAME)
    self.assertNear(wheel.angle, math.radians(90.0) - BACK * FRAME, 1e-12)
    wheel.angle = -0.5 * PUSH * FRAME
    wheel.turned(-1, FRAME)
    self.assertNear(wheel.angle, -1.5 * PUSH * FRAME, 1e-12)

  def test_column(self) -> None:
    """The column asks the wheel's share of the column's lock."""
    wheel = SteeringWheel()
    for angle in (WHEEL_LOCK, -0.5 * WHEEL_LOCK, 0.1):
      wheel.angle = angle
      self.assertNear(wheel.column, angle / WHEEL_LOCK * STEER_LOCK, 1e-15)

  def test_straightens(self) -> None:
    """At 25 m/s a fifth of a second's press turns the car a little (3
    to 20 degrees; 8.4 when measured) and, the key let go, the wheel
    comes back and the car goes straight again: turning under 0.05
    rad/s over its last half second (0.004)."""
    states, yaws = driven(moving(25.0), 3.5,
                          lambda t: (1 if t < 0.2 else 0, 0, False))
    self.assertGreater(headingOf(states), 3.0)
    self.assertLess(headingOf(states), 20.0)
    for yaw in yaws[-30:]:
      self.assertLess(abs(yaw), 0.05)

  def test_handbrake(self) -> None:
    """Pulled at 15 m/s, the handbrake has the rear wheels' rims all but
    still on their knuckles within a third of a second, the front ones
    rolling on; with the wheel turned left for 0.3 s (54 degrees) and
    the handbrake tapped for 0.3 s, the car swings round past 90
    degrees (153 when measured), where the steering alone turns it
    under 45 (13)."""
    states = driven(moving(15.0), 0.3, lambda t: (0, 0, True))[0]
    rims = []
    for wheel, knuckle in zip(CAR.wheels, CAR.knuckles):
      axle = rotated(states[wheel].turn, (0.0, 0.0, 1.0))
      rims.append(RADIUS * abs(dot(minus(states[wheel].spin,
                                         states[knuckle].spin), axle)))
    for rim in rims[2:]:
      self.assertLess(rim, 0.5)
    for rim in rims[:2]:
      self.assertGreater(rim, 10.0)
    for pulled, least, most in ((True, 90.0, 180.0), (False, 0.0, 45.0)):
      states = driven(moving(15.0), 3.0,
                      lambda t: (1 if t < 0.3 else 0, 0,
                                 pulled and 0.3 < t < 0.6))[0]
      self.assertGreater(headingOf(states), least)
      self.assertLess(headingOf(states), most)

  def test_live(self) -> None:
    """At 'LIVE' fidelity the car, braked from 25 m/s for 1.5 s, turned
    by a 0.3 s press at 30 m/s and driven on to 2 s, or swung round by
    the handbrake at 15 m/s, ends as at 'FULL': its speed within 0.1
    m/s, its heading within a degree, where it is within 10 cm (when
    measured: 0.06 m/s, 0.1 degree, 3 cm at worst)."""
    for speed, seconds, keys in (
            (25.0, 1.5, lambda t: (0, -1, False)),
            (30.0, 2.0, lambda t: (1 if t < 0.3 else 0, 0, False)),
            (15.0, 3.0, lambda t: (1 if t < 0.5 else 0, 0,
                                   0.3 < t < 0.6))):
      full, live = (driven(moving(speed), seconds, keys, fidelity)[0]
                    for fidelity in (FULL, LIVE))
      self.assertNear(speedOf(CAR, live), speedOf(CAR, full), 0.1)
      apart = headingOf(live) - headingOf(full)
      self.assertLess(abs((apart + 180.0) % 360.0 - 180.0), 1.0)
      self.assertNear(live[CAR.chassis].place, full[CAR.chassis].place,
                      0.1)

  def test_moved(self) -> None:
    """A hand on the wheel (the mouse) turns it where it is, and it
    stays there (only a key's 'turned' brings it back): turned 50
    degrees left it is at 50; turned on past either lock it stops
    there."""
    wheel = SteeringWheel()
    wheel.moved(math.radians(50.0))
    self.assertNear(wheel.angle, math.radians(50.0), 1e-12)
    wheel.moved(math.radians(200.0))
    self.assertEqual(wheel.angle, WHEEL_LOCK)
    wheel.moved(-3.0 * WHEEL_LOCK)
    self.assertEqual(wheel.angle, -WHEEL_LOCK)
