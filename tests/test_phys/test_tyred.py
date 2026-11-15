"""
TestTyred covers the wheel on a tyre as its air makes it ('_tyred': the
user's "unidirectional spring working parallel to the plane of the
wheel with whatever the fuck stiffness the current air pressure
demands"). The spring is 2 pi p sqrt(R a): 2.3 bar on a 205/55 R16, 260
kN/m (real ones 200-300), twice the pressure twice as stiff. The wheel
is one body of 16.2 kg, its moment about its axle about 0.95 kg m² (a
real 16 in wheel and tyre's 0.8-1.1). Standing, it sinks its weight
over the spring (0.6 mm, to 0.1 mm); nudged, it stays standing on its
tread's width (its spring two, at the tread's edges); tipped 30 degrees,
past them, it falls over and lies at rest on its sidewall within 2 s.
Rolled at 3 m/s it rolls on, slowing as its rolling resistance (0.015)
slows a wheel, 0.015 g / (1 + I / m R²): 0.093 m/s a second (to a
hundredth), turning as fast as it rolls (within 2 %); rolled leaning 20
degrees it stands up and slows alike (it once rolled round on its edge
for ever, losing nothing: "my tyre won't stop eulering"). Dropped 0.5
m it bounces back, slower by its damping (restitution between a half and four
fifths: 0.63; its sidewalls' probes, 5 cm balls 11.5 mm off the ground
when it stood, once met the ground under its 2 cm squash and left it
0.19). Two wheels rolled into each other meet tyre to tyre (their
middles no nearer than two tyres' radii, less 2 cm, while upright). A
wheel given is one body more, with its tyre, touching the walker and
the first. Its sidewalls carry its maker's lettering (Soufflé), twice
round, upright, reading clockwise from either side.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import SmallSteps, State, product, rotated, turnAbout
from worQt.phys._carcass import TYRE_PRESSURE, TYRE_YARD, WHEEL_UPRIGHT
from worQt.phys._scenes import WALKER
from worQt.phys._tyred import _placed, _yardOf, tyreOf, tyredBody
from worQt.phys._tyred import tyredGiven, wheelYard

from . import PhysTest

STEP, FRAME = 5e-4, 1.0 / 60.0
GRAVITY = (0.0, 0.0, -9.81)
RADIUS = tyreOf(1, TYRE_PRESSURE).radius


def _yard(*wheels: State) -> tuple:
  """Returns the yard with the walker far off and 'wheels'."""
  walker = State((-5.0, 0.0, WALKER.radius))
  return _yardOf((WALKER.body(),) + (tyredBody(),) * len(wheels),
                 (walker,) + wheels)


def _run(assembly: object, states: tuple, seconds: float) -> tuple:
  """Returns 'states' 'seconds' on in the yard, a frame at a time."""
  world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 0.0, 'cpu')
  for k in range(round(seconds / FRAME)):
    states = world.advancedAll(assembly, states, FRAME, k * FRAME)
  return states


def _rolling(place: tuple, speed: float) -> State:
  """Returns a wheel upright at 'place' rolling along x at 'speed'."""
  wheel = _placed(place, WHEEL_UPRIGHT, (speed, 0.0, 0.0))
  return State(wheel.place, wheel.turn, wheel.velocity,
               (0.0, speed / RADIUS, 0.0))


def _tilt(state: State) -> float:
  """Returns how far a wheel's axle is from level, degrees."""
  return math.degrees(math.asin(min(1.0, abs(rotated(
    state.turn, (0.0, 0.0, 1.0))[2]))))


class TestTyred(PhysTest):
  """TestTyred covers the wheel on its air's spring (on the CPU)."""

  __time_out__ = 120.0

  def test_stiffness(self) -> None:
    """2.3 bar makes the tyre 260 kN/m (2 pi p sqrt(R a), within a
    kN/m); twice the pressure, twice as stiff."""
    tyre = tyreOf(1, TYRE_PRESSURE)
    wanted = 2.0 * math.pi * TYRE_PRESSURE * math.sqrt(RADIUS * 0.1025)
    self.assertNear(tyre.stiffness, wanted, 1e-6)
    self.assertNear(tyre.stiffness, 2.60e5, 1e3)
    self.assertNear(tyreOf(1, 2.0 * TYRE_PRESSURE).stiffness,
                    2.0 * tyre.stiffness, 1e-6)

  def test_body(self) -> None:
    """The wheel weighs 16.2 kg (rim and tyre), its moment about its
    axle 0.8 to 1.1 kg m²."""
    body = tyredBody()
    self.assertNear(body.mass, 16.22, 0.05)
    self.assertGreater(body.inertia[2][2], 0.8)
    self.assertLess(body.inertia[2][2], 1.1)

  def test_stands(self) -> None:
    """Standing 0.15 s (its first bounces damped, before it tips: its
    rim's mass 14 mm outboard of its tread), the wheel's tread circle is
    its weight over the spring nearer the ground than its radius (to 0.1
    mm), still upright."""
    assembly, states = _yard(_placed((0.0, 0.0, RADIUS), WHEEL_UPRIGHT,
                                     (0.0, 0.0, 0.0)))
    states = _run(assembly, states, 0.15)
    body = tyredBody()
    sink = body.mass * 9.81 / tyreOf(1, TYRE_PRESSURE).stiffness
    middle = states[1].place[2] - rotated(states[1].turn, body.centre)[2]
    self.assertNear(middle, RADIUS - sink, 1e-4)
    self.assertLess(_tilt(states[1]), 2.0)

  def test_rolls(self) -> None:
    """Rolled at 3 m/s, a wheel rolls on a second, slowed as its
    rolling resistance slows it, 0.015 g / (1 + I / m R²) (0.093 m/s a
    second, to 0.01), turning as fast as it rolls (within 2 %)."""
    assembly, states = _yard(_rolling((0.0, 0.0, RADIUS - 6e-4), 3.0))
    states = _run(assembly, states, 1.0)
    speed = math.hypot(states[1].velocity[0], states[1].velocity[1])
    body = tyredBody()
    slowing = 0.015 * 9.81 / (1.0 + body.inertia[2][2] / (
      body.mass * RADIUS * RADIUS))
    self.assertNear(3.0 - speed, slowing, 0.01)
    spin = math.sqrt(sum(x * x for x in states[1].spin))
    self.assertNear(spin * RADIUS / speed, 1.0, 0.02)

  def test_stops_eulering(self) -> None:
    """Rolled at 3 m/s leaning 20 degrees, a wheel does not roll round
    on its edge for ever: after 10 s it is slower than 2.3 m/s (the
    rolling resistance's 0.93 m/s gone), and standing (within 5 degrees)
    or lying (past 80), not rolling round on its edge between. (It once
    stood back up: its pivoting's hold fought the leaning wheel's rolling
    spin's upright part and precessed it upright; with the tread's slip
    law, 2026-11-14, it curves round, slows and falls over, as a real
    rolled tyre does.)"""
    leaned = product(turnAbout((1.0, 0.0, 0.0), math.radians(20.0)),
                     WHEEL_UPRIGHT)
    axle = rotated(leaned, (0.0, 0.0, 1.0))
    wheel = _placed((0.0, 0.0, RADIUS * math.cos(math.radians(20.0))
                     + 0.002), leaned, (3.0, 0.0, 0.0))
    assembly, states = _yard(State(wheel.place, wheel.turn,
                                   wheel.velocity, tuple(
                                     -3.0 / RADIUS * a for a in axle)))
    states = _run(assembly, states, 10.0)
    self.assertLess(math.sqrt(sum(x * x for x in states[1].velocity)),
                    2.3)
    tilt = _tilt(states[1])
    self.assertTrue(tilt < 5.0 or tilt > 80.0)

  def test_bounces(self) -> None:
    """Dropped 0.5 m, a wheel bounces back slower by its damping: its
    first rebound between a half and four fifths of its fall's
    speed."""
    assembly, states = _yard(_placed((0.0, 0.0, RADIUS + 0.5),
                                     WHEEL_UPRIGHT, (0.0, 0.0, 0.0)))
    fastest = 0.0
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 0.0, 'cpu')
    for k in range(30):
      states = world.advancedAll(assembly, states, FRAME, k * FRAME)
      fastest = max(fastest, states[1].velocity[2])
    fall = math.sqrt(2.0 * 9.81 * 0.5)
    self.assertGreater(fastest, 0.5 * fall)
    self.assertLess(fastest, 0.8 * fall)

  def test_stays_upright(self) -> None:
    """Set upright on its tread, nudged (0.3 rad/s about its way
    ahead), a wheel stays standing (within 2 degrees) 2 s: it stands on
    its tread's width ('TREAD'), as a real one does."""
    wheel = _placed((0.0, 0.0, RADIUS), WHEEL_UPRIGHT, (0.0, 0.0, 0.0))
    assembly, states = _yard(State(wheel.place, wheel.turn,
                                   wheel.velocity, (0.3, 0.0, 0.0)))
    states = _run(assembly, states, 2.0)
    self.assertLess(_tilt(states[1]), 2.0)

  def test_lies_flat(self) -> None:
    """Tipped 30 degrees, past its tread's edge, a wheel falls over and
    lies at rest on its sidewall within 2 s."""
    leaned = product(turnAbout((1.0, 0.0, 0.0), math.radians(30.0)),
                     WHEEL_UPRIGHT)
    lift = RADIUS * math.cos(math.radians(30.0)) + 0.06
    assembly, states = _yard(_placed((0.0, 0.0, lift), leaned,
                                     (0.0, 0.0, 0.0)))
    states = _run(assembly, states, 2.0)
    self.assertGreater(_tilt(states[1]), 88.0)
    self.assertLess(math.sqrt(sum(x * x for x in states[1].velocity)),
                    1e-3)

  def test_wheels_meet(self) -> None:
    """Two wheels rolled into each other at 2 m/s meet tyre to tyre:
    while both stand upright (within 10 degrees), their middles are no
    nearer than two radii less 2 cm."""
    assembly, states = _yard(_rolling((0.0, 0.0, RADIUS + 0.001), 2.0),
                             _rolling((1.5, 0.0, RADIUS + 0.001), -2.0))
    world = SmallSteps(GRAVITY, TYRE_YARD, STEP, 1, 0.0, 'cpu')
    nearest = math.inf
    for k in range(24):
      states = world.advancedAll(assembly, states, FRAME, k * FRAME)
      if max(_tilt(states[1]), _tilt(states[2])) < 10.0:
        nearest = min(nearest, math.dist(states[1].place,
                                         states[2].place))
    self.assertGreater(nearest, 2.0 * RADIUS - 0.02)

  def test_lettered(self) -> None:
    """Its sidewalls are lettered by their maker (user, 2026-11-14:
    "brand: Soufflé"): each sidewall's picture runs twice round and
    once across it, upright (its top toward the tread) and reading
    clockwise as seen from the side it faces."""
    import numpy
    from worQt.phys._tyred import SIDEWALL_REPEATS, tyreRuns
    from worQt.phys.gui._meshes import finishedRows
    rows = finishedRows(tyredBody(), tyreRuns(), 0.04)['sidewall']
    self.assertNear(float(rows[:, 6].min()), 0.0, 1e-6)
    self.assertNear(float(rows[:, 6].max()), SIDEWALL_REPEATS, 1e-6)
    self.assertNear(float(rows[:, 7].min()), 0.0, 1e-6)
    self.assertNear(float(rows[:, 7].max()), 1.0, 1e-6)
    x, y = rows[:, 0], -rows[:, 2]
    rho, angle = numpy.hypot(x, y), numpy.arctan2(y, x)
    for facing in (1.0, -1.0):
      mine = facing * rows[:, 4] > 0.0
      upright = numpy.corrcoef(rho[mine], rows[mine, 7])[0, 1]
      self.assertGreater(upright, 0.9)
      first = mine & (angle > 0.2) & (angle < 2.9)
      slope = numpy.polyfit(angle[first], rows[first, 6], 1)[0]
      self.assertNear(slope, -facing * SIDEWALL_REPEATS / (2.0 * math.pi),
                      0.01)

  def test_given(self) -> None:
    """A wheel given is one body more, on its own tyre, touching the
    walker and the first wheel."""
    assembly, states = wheelYard()
    more, after = tyredGiven(assembly, states, State((0.0, 0.0, 1.5)))
    self.assertEqual(len(more.bodies), 3)
    self.assertEqual(len(after), 3)
    self.assertEqual({tyre.body for tyre in more.tyres}, {1, 2})
    pairs = {(c.first, c.second) for c in more.contacts}
    self.assertEqual(pairs, {(0, 1), (0, 2), (1, 2)})
