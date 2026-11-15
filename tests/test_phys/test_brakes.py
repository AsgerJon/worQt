"""
TestBrakes covers the disc brake ('DiscBrake', '_brakes'; user,
2026-11-14: "disc brakes (actual friction applies to discs connected
to wheels)"): the bench's Soufflé wheel with its cast iron disc (5.2 kg,
21.4 kg the two) on a stand, its caliper's pads 112.5 mm out, one 54 mm
piston, friction 0.4: at 2 bar both pads hold 366 N, 41.2 N m. Spun to
20 rad/s and braked it slows at that torque over its moment (to a
thousandth), stops by 0.5 s and stays stopped, its middle still on its
bearing; a motor twisting it with 30 N m is held still, with 60 it turns
it up at the difference over its moment (to a thousandth); its pads off
the disc it coasts on. A free carrier braking the wheel takes all the
wheel's turning loses (angular momentum kept to a ten-thousandth), the
two sharing it. The springs' world refuses it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, BrakeLine, DiscBrake, Drive, Motor
from worQt.phys import SmallSteps, State, Tie, Tyre, World, cross, dot
from worQt.phys import norm
from worQt.phys import minus, plus, rotated, scaled
from worQt.phys._brakes import DISC_AT, DISC_INNER, DISC_OUTER
from worQt.phys._brakes import PAD_RADIUS, benchOf, brakedWheel, discBody
from worQt.phys._carcass import TYRE_YARD, WHEEL_UPRIGHT
from worQt.phys._tyred import tyredBody

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 5e-4
LINE = 2e5
AXLE = rotated(WHEEL_UPRIGHT, (0.0, 0.0, 1.0))


def ran(assembly: Assembly, states: tuple, seconds: float,
        world: SmallSteps = None) -> list:
  """The 'ran' function returns 'states' at each frame of 'seconds' on
  (the first as given), stepped in 'world' (the yard's, by default)."""
  if world is None:
    world = SmallSteps((0.0, 0.0, -9.81), TYRE_YARD, STEP, 1, 0.0, 'cpu')
  out = [states]
  for k in range(round(seconds / FRAME)):
    states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    out.append(states)
  return out


def spun(states: tuple, speed: float) -> tuple:
  """The 'spun' function returns the bench's 'states' with its wheel
  turning at 'speed' rad/s about its axle."""
  wheel = states[2]
  return states[:2] + (State(wheel.place, wheel.turn, wheel.velocity,
                             scaled(AXLE, speed)),)


class TestBrakes(PhysTest):
  """Tests for the disc brake (about 40 s on the CPU)."""

  __time_out__ = 180.0

  def test_disc(self) -> None:
    """The disc weighs 5.2 kg, the wheel with it 21.4 kg; at 2 bar the
    pads hold 2 x 0.4 x 2 bar x one 54 mm piston, 366 N."""
    self.assertNear(discBody().mass, 5.21, 0.01)
    self.assertNear(brakedWheel().mass, tyredBody().mass
                    + discBody().mass, 1e-9)
    assembly, _ = benchOf(BrakeLine(LINE))
    self.assertNear(assembly.brakes[0].force(),
                    2.0 * 0.4 * LINE * math.pi * 0.027 ** 2, 1e-9)
    self.assertNear(assembly.brakes[0].force(), 366.4, 0.1)

  def test_slows(self) -> None:
    """Spun to 20 rad/s and braked at 2 bar (after 0.1 s free), the
    wheel slows at the pads' torque over its moment, to a thousandth
    of where it would be, stops by 0.5 s (0.489) and stays stopped, its
    middle within a hundredth of a millimetre on its bearing."""
    line = BrakeLine(0.0)
    assembly, states = benchOf(line)
    states = ran(assembly, spun(states, 20.0), 0.1)[-1]
    start, first = dot(states[2].spin, AXLE), states[2].place
    line.pressure = LINE
    slowing = assembly.brakes[0].force() * PAD_RADIUS / (
      brakedWheel().inertia[2][2])
    frames = ran(assembly, states, 1.0)
    for k in (6, 12, 21, 26):
      wanted = start - slowing * k * FRAME
      self.assertNear(dot(frames[k][2].spin, AXLE), wanted, 1e-3 * start)
    for k in (30, 45, 60):
      self.assertLess(abs(dot(frames[k][2].spin, AXLE)), 1e-3)
    self.assertLess(norm(minus(frames[-1][2].place, first)), 1e-5)

  def test_holds(self) -> None:
    """A motor twisting the braked wheel (2 bar, 41.2 N m) from still
    with 30 N m is held: it turns no more than a ten-thousandth of a
    radian in 1 s; with 60 N m it turns up at the difference over its
    moment, to a thousandth."""
    for torque, wanted in ((30.0, 0.0), (60.0, None)):
      assembly, states = benchOf(BrakeLine(LINE))
      drive = Drive(torque)
      drive.most = 1e6
      assembly = Assembly(assembly.bodies, assembly.connections + (
        Motor(1, 2, (0.0, 0.0, 1.0), drive),))
      frames = ran(assembly, states, 1.0)
      turned = sum(dot(frame[2].spin, AXLE) for frame in frames) * FRAME
      spin = dot(frames[-1][2].spin, AXLE)
      if wanted is not None:
        self.assertLess(abs(turned), 1e-4)
        self.assertLess(abs(spin), 1e-4)
        continue
      held = assembly.brakes[0].force() * PAD_RADIUS
      speed = (torque - held) / brakedWheel().inertia[2][2]
      self.assertNear(spin, speed, 1e-3 * speed)

  def test_off_disc(self) -> None:
    """Its pads off the disc (its swept ring made to end short of
    them), the wheel coasts on, braked or not."""
    line = BrakeLine(LINE)
    assembly, states = benchOf(line)
    connections = tuple(
      DiscBrake(c.disc, c.caliper, c.middle, c.axle, c.pad, c.inner,
                0.5 * (c.inner + PAD_RADIUS), c.line)
      if isinstance(c, DiscBrake) else c for c in assembly.connections)
    assembly = Assembly(assembly.bodies, connections)
    frames = ran(assembly, spun(states, 20.0), 0.5)
    self.assertNear(dot(frames[-1][2].spin, AXLE), 20.0, 0.01)

  def test_third_law(self) -> None:
    """In the void, the wheel at 20 rad/s braked by a free carrier (a
    second disc on its axle, its caliper's): the carrier takes all the
    wheel loses, angular momentum kept to a ten-thousandth, and in a
    second both turn as one, at what they share (to a thousandth)."""
    wheel, carrier = brakedWheel(), discBody()
    middle = (0.0, 0.0, 1.0)
    states = (State(plus(middle, wheel.centre), (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0), (0.0, 0.0, 20.0)),
              State(plus(middle, carrier.centre)))
    assembly = Assembly((wheel, carrier), (
      Tie(1, (0.0, 0.0, 0.02), 0, (0.0, 0.0, 0.02)),
      Tie(1, (0.0, 0.0, 0.07), 0, (0.0, 0.0, 0.07)),
      DiscBrake(0, 1, (0.0, 0.0, DISC_AT), (0.0, 0.0, 1.0),
                (-PAD_RADIUS, 0.0, DISC_AT), DISC_INNER, DISC_OUTER,
                BrakeLine(LINE))))

    def held(states: tuple) -> tuple:
      """Returns the angular momentum of 'states' about the origin."""
      out = (0.0, 0.0, 0.0)
      for body, state in zip(assembly.bodies, states):
        out = plus(out, plus(body.angularMomentumOf(state), scaled(
          cross(state.place, state.velocity), body.mass)))
      return out

    world = SmallSteps((0.0, 0.0, 0.0), None, STEP, 1, 0.0, 'cpu')
    frames = ran(assembly, states, 1.0, world)
    first = held(states)
    worst = max(norm(minus(held(frame), first)) for frame in frames)
    self.assertLess(worst, 1e-4 * norm(first))
    shared = 20.0 * wheel.inertia[2][2] / (wheel.inertia[2][2]
                                           + carrier.inertia[2][2])
    for state in frames[-1]:
      self.assertNear(state.spin[2], shared, 1e-3 * shared)

  def test_springs_refuse(self) -> None:
    """The springs' world refuses a disc brake (small steps only; the
    bench without its tyre, which it refuses too)."""
    assembly, states = benchOf(BrakeLine(LINE))
    assembly = Assembly(assembly.bodies, tuple(
      c for c in assembly.connections if not isinstance(c, Tyre)))
    world = World((0.0, 0.0, -9.81), 1e-3, TYRE_YARD)
    with self.assertRaises(ValueError):
      world.advancedAll(assembly, states, 0.01)
