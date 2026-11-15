"""
TestCarcass covers the cord tyre ('_carcass': a wheel whose tyre is
nothing but cords pulling and air pushing) and the small steps' cord
lines, air and crowds under it. A cord line pulls a stretched piece back
to its length and lets a slack one be; held whole it carries a load
along it at once. The rim is a 16 in alloy wheel of 7 to 9 kg; the tyre
a 205/55 R16 (316.5 mm out, 205 mm across), 8.5 kg. Inflated on a rim
held still it settles at 2.3 bar, its crown 0.5 to 3 mm further out than
moulded, the same all round. Spun in the air a wheel keeps its angular
momentum (the cords pull along their lines as they were at a step's
start, as SHAKE's; pulled along the lines as moved, a tyre at 2.3 bar
lost two thirds of its spin in 0.2 s). Set rolling at 3 m/s it rolls on
(no more than 0.15 m/s lost in a second: a real tyre's rolling
resistance, about 0.01, takes 0.1), turning as fast as it rolls. Set
upright on its tread it falls over and comes to rest on its side
within 3 s (one pass a step let its sidewall chatter and buzz off);
slid lying flat it stops at once (the velocity pass's slowing capped as
an impulse: once capped as a speed, a 20 g node took a fiftieth of its
grip and the wheel slid on as on ice). A wheel given is another 441
bodies, every tyre in the crowd.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ATMOSPHERE, Assembly, Body, CordLine, Crowd, Ground
from worQt.phys import SmallSteps, Sphere, State, rotated
from worQt.phys._carcass import RIM, TREAD_RUBBER, TYRE_ACROSS
from worQt.phys._carcass import TYRE_AROUND, TYRE_MASS, TYRE_PRESSURE
from worQt.phys._carcass import TYRE_YARD, WHEEL_UPRIGHT, inflated
from worQt.phys._carcass import tyreSection, tyreYard, tyredWheel
from worQt.phys._carcass import wheelGiven, wheelsOf
from worQt.phys._carcass import _withWheels
from worQt.phys._scenes import WALKER

from . import PhysTest

STEP, FRAME = 2.5e-4, 1.0 / 60.0
GRAVITY = (0.0, 0.0, -9.81)


def _yardWith(place: tuple, turn: tuple, velocity: tuple,
              spin: tuple = (0.0, 0.0, 0.0)) -> tuple:
  """Returns the yard with the walker far off and one wheel, its rim's
  frame at 'place' turned by 'turn', moving at 'velocity' and spinning
  at 'spin' (its nodes with it), and the wheel (rim, rows)."""
  bodies, wheel, cords = tyredWheel(1, place, turn, velocity)
  rim = wheel[0]
  spun = [State(rim.place, rim.turn, rim.velocity, spin)]
  for state in wheel[1:]:
    arm = tuple(a - b for a, b in zip(state.place, rim.place))
    turning = (spin[1] * arm[2] - spin[2] * arm[1],
               spin[2] * arm[0] - spin[0] * arm[2],
               spin[0] * arm[1] - spin[1] * arm[0])
    spun.append(State(state.place, state.turn, tuple(
      v + w for v, w in zip(state.velocity, turning))))
  walker = State((-5.0, 0.0, WALKER.radius))
  assembly, states = _withWheels((WALKER.body(),) + tuple(bodies),
                                 tuple(cords), (walker,) + tuple(spun))
  return assembly, states, wheelsOf(assembly)[0]


def _run(world: object, assembly: object, states: tuple,
         seconds: float) -> tuple:
  """Returns 'states' 'seconds' on, a frame at a time."""
  for k in range(round(seconds / FRAME)):
    states = world.advancedAll(assembly, states, FRAME, k * FRAME)
  return states


def _kinetic(assembly: object, states: tuple, rim: int,
             rows: tuple) -> float:
  """Returns how much a wheel moves: its rim's and its nodes' kinetic
  energy of moving along (not the rim's turning), J."""
  out = 0.0
  for index in (rim,) + tuple(node for row in rows for node in row):
    v = states[index].velocity
    out += 0.5 * assembly.bodies[index].mass * sum(x * x for x in v)
  return out


class TestCarcass(PhysTest):
  """TestCarcass covers the cord tyre and the cord lines, air and crowds
  of the small steps (on the CPU: about a minute, more the first time,
  which inflates the tyre)."""

  __time_out__ = 300.0

  def test_cord_pulls_only(self) -> None:
    """A cord between two balls pulls them back to its length in a step
    when stretched, each half way (alike), and lets them be when
    slack."""
    ball = Body.of(Sphere(0.01), 1000.0)
    world = SmallSteps((0.0, 0.0, 0.0), None, STEP, 1, 0.0, 'cpu')
    for apart, wanted in ((0.12, 0.1), (0.08, 0.08)):
      line = CordLine(((0, (0.0, 0.0, 0.0)), (1, (0.0, 0.0, 0.0))),
                      (math.inf,), (0.1,))
      assembly = Assembly((ball, ball), (line,))
      states = (State((0.0, 0.0, 0.0)), State((apart, 0.0, 0.0)))
      states = world.advancedAll(assembly, states, STEP)
      self.assertNear(states[1].place[0] - states[0].place[0], wanted,
                      1e-6)
      self.assertNear(states[0].place[0] + states[1].place[0], apart,
                      1e-6)

  def test_rim(self) -> None:
    """The alloy rim weighs as a 16 in one (7 to 9 kg)."""
    self.assertGreater(RIM.mass, 7.0)
    self.assertLess(RIM.mass, 9.0)

  def test_section(self) -> None:
    """The tyre is a 205/55 R16: with its rubber, 316.5 mm out at the
    crown, 205 mm across at its widest (each to a millimetre), the same
    either side; 8.5 kg."""
    section = tyreSection()
    self.assertEqual(len(section), TYRE_ACROSS)
    crown = section[TYRE_ACROSS // 2]
    self.assertNear(crown[0] + TREAD_RUBBER, 0.3165, 1e-3)
    widest = max(abs(w) for _, w in section)
    self.assertNear(2.0 * (widest + 0.007), 0.205, 2e-3)
    for k in range(TYRE_ACROSS):
      one, two = section[k], section[TYRE_ACROSS - 1 - k]
      self.assertNear((one[0], one[1]), (two[0], -two[1]), 1e-12)
    bodies, _, _ = tyredWheel(0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0),
                              (0.0, 0.0, 0.0))
    self.assertNear(sum(body.mass for body in bodies[1:]), TYRE_MASS,
                    1e-9)

  def test_inflated(self) -> None:
    """Inflated, the tyre holds 2.3 bar in about 25 l, its crown 0.5 to
    3 mm further out than moulded, alike all round (to 0.1 mm)."""
    places, gas = inflated()
    self.assertEqual(len(places), TYRE_AROUND)
    volume = gas / (TYRE_PRESSURE + ATMOSPHERE)
    self.assertGreater(volume, 0.022)
    self.assertLess(volume, 0.029)
    middle = TYRE_ACROSS // 2 - 1
    radii = [math.hypot(row[middle][0], row[middle][1]) for row in places]
    grown = sum(radii) / len(radii) - tyreSection()[TYRE_ACROSS // 2][0]
    self.assertGreater(grown, 5e-4)
    self.assertLess(grown, 3e-3)
    self.assertLess(max(radii) - min(radii), 1e-4)

  def test_spin_kept(self) -> None:
    """Spun at 9 rad/s in the air (no gravity, no ground), a wheel keeps
    its angular momentum about its axle to a thousandth for a third of a
    second."""
    world = SmallSteps((0.0, 0.0, 0.0), None, STEP, 2, 0.0, 'cpu')
    assembly, states, (rim, rows) = _yardWith(
      (0.0, 0.0, 2.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
      (0.0, 0.0, 9.0))

    def momentum(states: tuple) -> float:
      """Returns the wheel's angular momentum about the world's z
      through the rim's centre, kg m²/s."""
      middle = states[rim].place
      inertia = RIM.inertia
      axes = [rotated(states[rim].turn, e) for e in
              ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))]
      spin = states[rim].spin
      own = [sum(axes[i][k] * spin[k] for k in range(3)) for i in range(3)]
      held = [sum(inertia[i][j] * own[j] for j in range(3))
              for i in range(3)]
      total = sum(axes[i][2] * held[i] for i in range(3))
      for node in (node for row in rows for node in row):
        at, v = states[node].place, states[node].velocity
        x, y = at[0] - middle[0], at[1] - middle[1]
        total += assembly.bodies[node].mass * (x * v[1] - y * v[0])
      return total

    first = momentum(states)
    states = _run(world, assembly, states, 0.33)
    self.assertNear(momentum(states) / first, 1.0, 1e-3)

  def test_rolls(self) -> None:
    """Set rolling at 3 m/s on the yard, a wheel rolls on a second: no
    more than 0.15 m/s lost, turning as fast as it rolls (within a
    tenth), upright (within 5 degrees), its air at 2.3 bar (within
    0.1)."""
    outer = tyreSection()[TYRE_ACROSS // 2][0] + TREAD_RUBBER
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 2, 0.0, 'cpu')
    assembly, states, (rim, rows) = _yardWith(
      (0.0, 0.0, outer + 0.002), WHEEL_UPRIGHT, (3.0, 0.0, 0.0),
      (0.0, 3.0 / outer, 0.0))
    states = _run(world, assembly, states, 1.0)
    speed = states[rim].velocity[0]
    self.assertGreater(speed, 2.85)
    self.assertNear(states[rim].spin[1] * outer / speed, 1.0, 0.1)
    axle = rotated(states[rim].turn, (0.0, 0.0, 1.0))
    self.assertLess(abs(axle[2]), math.sin(math.radians(5.0)))
    self.assertNear(world.pressuresOf(assembly)[0], TYRE_PRESSURE, 1e4)

  def test_falls_and_rests(self) -> None:
    """Set upright on its tread, a wheel falls over and lies at rest on
    its side within 3 s: its axle upright (within 2 degrees), its
    moving all but gone (under a millijoule)."""
    assembly, states = tyreYard()
    rim, rows = wheelsOf(assembly)[0]
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 2, 0.0, 'cpu')
    states = _run(world, assembly, states, 3.0)
    axle = rotated(states[rim].turn, (0.0, 0.0, 1.0))
    self.assertGreater(abs(axle[2]), math.cos(math.radians(2.0)))
    self.assertLess(_kinetic(assembly, states, rim, rows), 1e-3)

  def test_slides_stops(self) -> None:
    """Slid at 0.5 m/s lying flat on its spokes, a wheel stops within
    half a second (the yard's grip 1.0: in a twentieth)."""
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 2, 0.0, 'cpu')
    assembly, states, (rim, rows) = _yardWith(
      (0.0, 0.0, 0.104), (0.0, 1.0, 0.0, 0.0), (0.5, 0.0, 0.0))
    states = _run(world, assembly, states, 0.5)
    self.assertLess(abs(states[rim].velocity[0]), 0.01)

  def test_given(self) -> None:
    """A wheel given is 441 more bodies (its rim and 40 by 11 nodes),
    its tyre in the crowd beside the first's, each tyre's nodes touching
    the other's rim."""
    assembly, states = tyreYard()
    more, after = wheelGiven(assembly, states, State((0.0, 0.0, 1.5)))
    self.assertEqual(len(more.bodies), len(assembly.bodies) + 441)
    self.assertEqual(len(after), len(more.bodies))
    wheels = wheelsOf(more)
    self.assertEqual(len(wheels), 2)
    crowds = more.crowds
    self.assertEqual(len(crowds), 1)
    self.assertEqual(len(crowds[0].groups), 2)
    self.assertIsInstance(crowds[0], Crowd)
    rims = {rim for rim, _ in wheels}
    touching = [c for c in more.contacts if c.second in rims
                and c.first != 0]
    self.assertEqual(len([c for c in more.contacts if c.first == 0]),
                     2 * 441)
    self.assertEqual(len(touching), 2 * 440)
    self.assertIsInstance(TYRE_YARD, Ground)
