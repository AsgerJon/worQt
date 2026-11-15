"""
TestTie covers 'Tie', two bodies tied at a point on each by a cord of
no length, and 'World' stepping an 'Assembly' of them: a rod hung by its
end from the world swings at the period by hand (a physical pendulum,
the elliptic integral for its swing), its end staying on the hook, its
energy kept; hung by its middle it stays as it is; the tie pulls the
weight hanging from it, and more as the rod swings through the bottom;
two rods hung end to end swing apart from each other but never part;
two bodies tied at their middles move together, each turning as it
would alone; ties holding nothing, or holding twice, are refused.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import AXES, ORIGIN, UNTURNED, Assembly, Body, State
from worQt.phys import Tie, World, boxShape, cross, minus, norm, rotated
from worQt.phys import turnAbout

from . import PhysTest

WORLD = World()
ROD = Body.of(boxShape(1.0, 0.02, 0.02), 1000.0)
END, OTHER_END = (0.5, 0.0, 0.0), (-0.5, 0.0, 0.0)
HUNG = Assembly((ROD,), (Tie(0, END, None, ORIGIN),))


def hung(swing: float, point: tuple, hook: tuple) -> State:
  """The 'hung' function returns the rod at rest with its 'point' at
  'hook', swung 'swing' radians about y from hanging straight down
  below it."""
  turn = turnAbout((0.0, 1.0, 0.0), swing - 0.5 * math.pi)
  arm = rotated(turn, minus(point, ROD.centre))
  return State(minus(hook, arm), turn, ORIGIN, ORIGIN)


def swingPeriod(swing: float) -> float:
  """The 'swingPeriod' function returns the period of the rod swinging
  'swing' radians either way about its end, by hand: 2 pi sqrt(I / m g
  d), I about the end, d to the middle, times 2 K(sin(swing / 2)) / pi
  (K by the arithmetic-geometric mean)."""
  d = 0.5
  about = ROD.inertia[1][1] + ROD.mass * d * d
  small = 2.0 * math.pi * math.sqrt(about / (ROD.mass * 9.81 * d))
  a, b = 1.0, math.cos(0.5 * swing)
  for _ in range(40):
    a, b = 0.5 * (a + b), math.sqrt(a * b)
  return small / a


class TestTie(PhysTest):
  """Tests for 'Tie' and 'World.advancedAll'."""

  def test_hung_by_end(self) -> None:
    """A rod hung by its end swung 30 degrees swings at the period by
    hand, its end on the hook, its energy kept, in its plane."""
    states = (hung(math.radians(30.0), END, ORIGIN),)
    energy = WORLD.energyOfAll(HUNG, states)
    crossings, before = [], None
    for step in range(6000):
      states = WORLD.advancedAll(HUNG, states, 0.001)
      self.assertLess(norm(ROD.placeOf(states[0], END)), 1e-13)
      self.assertLess(abs(WORLD.energyOfAll(HUNG, states) / energy - 1.0),
                      2e-6)
      middle = states[0].place
      swing = math.atan2(middle[0], -middle[2])
      if before is not None and before < 0.0 <= swing:
        crossings.append(0.001 * (step + before / (before - swing)))
      before = swing
    self.assertGreaterEqual(len(crossings), 3)
    period = swingPeriod(math.radians(30.0))
    for start, end in zip(crossings, crossings[1:]):
      self.assertLess(abs((end - start) / period - 1.0), 2e-6)
    self.assertEqual(states[0].place[1], 0.0)

  def test_hung_by_middle(self) -> None:
    """Hung by its middle a rod held askew stays as it is, the tie
    holding its weight."""
    middle = Assembly((ROD,), (Tie(0, ORIGIN, None, ORIGIN),))
    askew = (hung(math.radians(30.0), ORIGIN, ORIGIN),)
    later = WORLD.advancedAll(middle, askew, 2.0)
    self.assertNear(later[0].place, askew[0].place, 1e-14)
    self.assertSameTurn(later[0].turn, askew[0].turn, 1e-14)
    self.assertNear(WORLD.pullsOf(middle, later),
                    ((0.0, 0.0, ROD.mass * 9.81),), 1e-12)

  def test_pulls(self) -> None:
    """Hanging still, the tie pulls the rod's weight; swinging through
    the bottom at w, its weight and m d w² more, d its end to its
    middle."""
    still = (hung(0.0, END, ORIGIN),)
    self.assertNear(WORLD.pullsOf(HUNG, still),
                    ((0.0, 0.0, ROD.mass * 9.81),), 1e-12)
    spin = (0.0, 3.0, 0.0)
    swinging = State(still[0].place, still[0].turn,
                     cross(spin, still[0].place), spin)
    pull = ROD.mass * 9.81 + ROD.mass * 0.5 * 9.0
    self.assertNear(WORLD.pullsOf(HUNG, (swinging,)),
                    ((0.0, 0.0, pull),), 1e-12)

  def test_double_pendulum(self) -> None:
    """Two rods hung end to end, let go askew, swing every which way,
    their ends never parting, their energy kept; hanging still, the
    upper tie holds both, the lower one."""
    upper = hung(math.radians(60.0), END, ORIGIN)
    joint = ROD.placeOf(upper, OTHER_END)
    states = (upper, hung(math.radians(-30.0), END, joint))
    pair = Assembly((ROD, ROD), (Tie(0, END, None, ORIGIN),
                                 Tie(1, END, 0, OTHER_END)))
    energy = WORLD.energyOfAll(pair, states)
    for _ in range(500):
      states = WORLD.advancedAll(pair, states, 0.01)
      self.assertLess(norm(ROD.placeOf(states[0], END)), 1e-12)
      apart = minus(ROD.placeOf(states[1], END),
                    ROD.placeOf(states[0], OTHER_END))
      self.assertLess(norm(apart), 1e-12)
      self.assertLess(abs(WORLD.energyOfAll(pair, states) - energy), 1e-3)
    upper = hung(0.0, END, ORIGIN)
    still = (upper, hung(0.0, END, ROD.placeOf(upper, OTHER_END)))
    weight = ROD.mass * 9.81
    self.assertNear(WORLD.pullsOf(pair, still),
                    ((0.0, 0.0, 2.0 * weight), (0.0, 0.0, weight)), 1e-12)

  def test_middles(self) -> None:
    """Tied at their middles, out in space, a box and a rod move
    together, each turning as it would alone; set going apart, the tie
    jerks them together at once, their momentum shared."""
    space = World((0.0, 0.0, 0.0), 1e-3)
    box = Body.of(boxShape(0.4, 0.3, 0.2), 1000.0)
    pair = Assembly((box, ROD), (Tie(0, ORIGIN, 1, ORIGIN),))
    states = (State(ORIGIN, UNTURNED, (1.0, 0.0, 0.5), (0.0, 0.0, 4.0)),
              State(ORIGIN, UNTURNED, (1.0, 0.0, 0.5), (7.0, 0.0, 0.0)))
    later = space.advancedAll(pair, states, 2.0)
    self.assertNear(later[0].place, (2.0, 0.0, 1.0), 1e-12)
    self.assertNear(later[1].place, (2.0, 0.0, 1.0), 1e-12)
    self.assertSameTurn(later[0].turn, turnAbout(AXES[2], 8.0), 1e-12)
    self.assertSameTurn(later[1].turn, turnAbout(AXES[0], 14.0), 1e-12)
    apart = (State(ORIGIN, UNTURNED, (2.0, 0.0, 0.0), ORIGIN),
             State(ORIGIN, UNTURNED, ORIGIN, ORIGIN))
    later = space.advancedAll(pair, apart, 0.5)
    shared = 2.0 * box.mass / (box.mass + ROD.mass)
    self.assertNear(later[0].velocity, (shared, 0.0, 0.0), 1e-12)
    self.assertNear(later[1].velocity, (shared, 0.0, 0.0), 1e-12)

  def test_refused(self) -> None:
    """A tie with both ends on the world holds nothing that moves; two
    ties holding the same point hold it twice: both refused."""
    nothing = Assembly((ROD,), (Tie(None, ORIGIN, None, ORIGIN),))
    with self.assertRaises(ValueError):
      WORLD.advancedAll(nothing, (hung(0.0, END, ORIGIN),), 0.01)
    twice = Assembly((ROD,), (Tie(0, END, None, ORIGIN),
                              Tie(0, END, None, ORIGIN)))
    with self.assertRaises(ValueError):
      WORLD.advancedAll(twice, (hung(0.0, END, ORIGIN),), 0.01)
