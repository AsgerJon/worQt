"""
TestBooks covers 'Books', the energy a run gains and loses line by line,
'Stored', the energy held at a moment, and 'Grease', random shaking:
what is held, with the heat, less the work, stays what was held at the
start, close enough (the stepping's own error, a hair that shrinks as
the step squared): nothing booked tumbling freely; the dampers' heat,
the ground's (a quarter for half the step), the actuators' work, the
snap of a weld; ideal ties do no work; the grease's work explains the
energy it shakes in, and it shakes as much however fine the steps,
the same for the same seed, a run cut on its steps the same as whole.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Actuator, Assembly, Body, Books
from worQt.phys import Damper, Grease, Ground, SineStroke, Spring, State
from worQt.phys import Tie, Weld, World, boxShape, minus, normalised
from worQt.phys import rotated, turnAbout

from . import PhysTest, lShape

WORLD = World()
SPACE = World((0.0, 0.0, 0.0), 1e-3)
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
TOP = (0.0, 0.0, 0.1)
SAG = BLOCK.mass * 9.81 / 800.0
HUNG = Assembly((BLOCK,), (Spring(None, ORIGIN, 0, TOP, 800.0, 1.0),))
DAMPED = Assembly((BLOCK,), (Spring(None, ORIGIN, 0, TOP, 800.0, 1.0),
                             Damper(None, ORIGIN, 0, TOP, 16.0)))


def missing(world: World, assembly: Assembly, states: tuple,
            seconds: float, piece: float) -> tuple:
  """The 'missing' function runs 'assembly' from 'states' for 'seconds'
  in pieces of 'piece', and returns the most the books missed by (what
  is held, with the heat, less the work, against what was held at the
  start), the books, and the states at the end."""
  held = world.storedOf(assembly, states).total()
  books, worst, time = Books(), 0.0, 0.0
  for _ in range(round(seconds / piece)):
    states, books = world.booked(assembly, states, piece, time, books)
    time += piece
    now = world.storedOf(assembly, states).total()
    worst = max(worst, abs(now + books.heat() - books.work() - held))
  return worst, books, states


class TestBooks(PhysTest):
  """Tests for 'Books', 'Stored' and 'Grease'."""

  def test_free(self) -> None:
    """An L tumbling freely books nothing, and holds what it held."""
    body = Body.of(lShape(), 1000.0)
    toss = (State((0.0, 0.0, 2.0), normalised((0.9, 0.2, -0.3, 0.4)),
                  (1.0, 0.0, 4.0), (3.0, -6.0, 2.0)),)
    worst, books, _ = missing(WORLD, Assembly((body,)), toss, 2.0, 0.1)
    self.assertEqual(books, Books())
    self.assertLess(worst, 1e-6 * 2000.0)

  def test_dampers(self) -> None:
    """A block bobbing on a spring and a damper loses to the damper's
    heat what it loses, but for a hair; nothing else is booked."""
    start = (State((0.0, 0.0, -1.1)),)
    worst, books, states = missing(WORLD, DAMPED, start, 4.0, 0.01)
    self.assertGreater(books.dampers, 3.8)
    self.assertLess(worst, 2e-4)
    self.assertEqual(Books(books.ground, 0.0, *books[2:]), Books())

  def test_ground(self) -> None:
    """A box dropped flat loses to the ground's heat what it loses, but
    for a hair that shrinks as the step squared."""
    drop = (State((0.0, 0.0, 0.6)),)
    box = Assembly((Body.of(boxShape(0.4, 0.3, 0.2), 1000.0),))
    misses = []
    for step in (2e-4, 1e-4):
      world = World((0.0, 0.0, -9.81), step, Ground())
      worst, books, _ = missing(world, box, drop, 2.0, 0.5)
      self.assertGreater(books.ground, 100.0)
      self.assertLess(worst, 1e-3 * books.ground)
      misses.append(worst)
    self.assertGreater(misses[0] / misses[1], 3.0)
    self.assertLess(misses[0] / misses[1], 5.0)

  def test_actuators(self) -> None:
    """A shaker's actuator puts in what the damper takes out and the
    block and the springs come to hold, but for a hair."""
    base = Body.of(boxShape(0.1, 0.1, 0.1), 1000.0)
    stroke = SineStroke(0.5, 0.01, 10.0 / (2.0 * math.pi))
    shaker = Assembly((base, BLOCK), (Actuator(None, ORIGIN, 0, ORIGIN,
                                               stroke),
                                      Spring(0, ORIGIN, 1, ORIGIN, 800.0,
                                             0.5),
                                      Damper(0, ORIGIN, 1, ORIGIN, 16.0)))
    start = (State((0.0, 0.0, -0.5)), State((0.0, 0.0, -1.0 - SAG)))
    worst, books, _ = missing(WORLD, shaker, start, 4.0, 0.01)
    self.assertGreater(books.actuators, 5.0)
    self.assertGreater(books.dampers, 5.0)
    self.assertLess(worst, 1e-2)

  def test_ties(self) -> None:
    """Two rods swinging end to end on ties: the ties do no work but
    for a hair, and the books balance."""
    rod = Body.of(boxShape(1.0, 0.02, 0.02), 1000.0)
    end, other = (0.5, 0.0, 0.0), (-0.5, 0.0, 0.0)

    def hung(swing: float, hook: tuple) -> State:
      """Returns a rod hung by its end from 'hook', swung 'swing'."""
      turn = turnAbout((0.0, 1.0, 0.0), swing - 0.5 * math.pi)
      return State(minus(hook, rotated(turn, end)), turn)

    upper = hung(math.radians(60.0), ORIGIN)
    states = (upper, hung(math.radians(-30.0), rod.placeOf(upper, other)))
    pair = Assembly((rod, rod), (Tie(0, end, None, ORIGIN),
                                 Tie(1, end, 0, other)))
    worst, books, _ = missing(WORLD, pair, states, 3.0, 0.01)
    self.assertLess(abs(books.ties), 1e-4)
    self.assertLess(worst, 1e-3)

  def test_snap(self) -> None:
    """Two boxes welded moving apart: the snap books the energy lost."""
    lying = Body.of(boxShape(1.0, 0.2, 0.2), 1000.0)
    standing = Body.of(boxShape(0.2, 0.2, 0.6), 1000.0)
    welded = Assembly((lying, standing), (Weld((0, 1)),))
    apart = (State(ORIGIN, UNTURNED, (1.0, 0.0, 0.0), (0.0, 0.0, 2.0)),
             State((0.6, 0.0, 0.4), UNTURNED, (-1.0, 0.5, 0.0),
                   (5.0, 0.0, 0.0)))
    worst, books, _ = missing(SPACE, welded, apart, 1.0, 0.1)
    self.assertGreater(books.snaps, 20.0)
    self.assertLess(worst, 1e-5)

  def test_grease_booked(self) -> None:
    """A block hung still on a spring, greased, takes in energy: the
    grease's work explains it, but for a hair (a slow random walk, its
    mass times shake² times the root of the time and the step, here
    about 3 mJ)."""
    greased = World((0.0, 0.0, -9.81), 1e-3, None, Grease(0.05, 0.05, 1))
    still = (State((0.0, 0.0, -1.1 - SAG)),)
    worst, books, _ = missing(greased, HUNG, still, 20.0, 0.1)
    self.assertGreater(books.grease, 0.1)
    self.assertLess(worst, 0.01)

  def test_grease_spread(self) -> None:
    """A hundred cubes greased out in space for a second spread their
    velocities and spins as the shaking says, shake² and spin² a second
    either way, however fine the steps."""
    cubes = Assembly(tuple([BLOCK] * 100))
    for step in (1e-3, 5e-4):
      world = World((0.0, 0.0, 0.0), step, None, Grease(0.3, 0.2, 7))
      states = world.advancedAll(cubes, tuple(State() for _ in range(100)),
                                 1.0)
      moving = [x for state in states for x in state.velocity]
      turning = [x for state in states for x in state.spin]
      spread = sum(x * x for x in moving) / len(moving)
      spun = sum(x * x for x in turning) / len(turning)
      self.assertLess(abs(spread / 0.09 - 1.0), 0.3)
      self.assertLess(abs(spun / 0.04 - 1.0), 0.3)

  def test_grease_repeats(self) -> None:
    """Greased, a run is the same for the same seed and differs for
    another; cut into pieces on its steps, it is the run whole."""
    start = (State((0.0, 0.0, -1.1)),)
    runs = []
    for seed in (3, 3, 4):
      world = World((0.0, 0.0, -9.81), 1e-3, None, Grease(0.05, 0.05, seed))
      runs.append(world.advancedAll(DAMPED, start, 1.0))
    self.assertEqual(runs[0], runs[1])
    self.assertNotEqual(runs[0], runs[2])
    world = World((0.0, 0.0, -9.81), 1e-3, None, Grease(0.05, 0.05, 3))
    pieces = world.advancedAll(DAMPED, world.advancedAll(DAMPED, start, 0.4,
                                                         0.0), 0.6, 0.4)
    self.assertNear(pieces, runs[0], 1e-12)
