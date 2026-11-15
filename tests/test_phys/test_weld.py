"""
TestWeld covers 'Weld', any number of bodies made one rigid body: two
boxes welded as an L move as the L made whole does, tumbling in the air
and tossed onto the ground, each part's bristles its own; welded, the
parts keep as they lie to each other; welded moving apart they are
jerked together, momentum and angular momentum kept, energy lost; a
steel head welded to a rod hung by a tie swings at the period by hand,
the tie holding both; welds sharing a body weld all their parts; a weld
of one body is that body alone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Assembly, Body, Ground, State
from worQt.phys import Tie, Weld, World, boxShape, conjugate, cross
from worQt.phys import minus, norm, normalised, plus, product, rotated
from worQt.phys import turnAbout

from . import PhysTest, lShape

LYING = Body.of(boxShape(1.0, 0.2, 0.2), 1000.0)
STANDING = Body.of(boxShape(0.2, 0.2, 0.6), 1000.0)
WHOLE = Body.of(lShape(), 1000.0)
WELDED = Assembly((LYING, STANDING), (Weld((0, 1)),))
MIDDLES = ((0.0, 0.0, 0.0), (0.4, 0.0, 0.4))
SPACE = World((0.0, 0.0, 0.0), 1e-3)
TUMBLING = State((0.0, 0.0, 2.0), normalised((0.9, 0.2, -0.3, 0.4)),
                 (1.0, 0.0, 4.0), (3.0, -6.0, 2.0))


def partsOf(whole: State) -> tuple[State, State]:
  """The 'partsOf' function returns the two boxes as parts of the L in
  'whole', each moving with it."""
  parts = []
  for middle in MIDDLES:
    arm = rotated(whole.turn, minus(middle, WHOLE.centre))
    parts.append(State(plus(whole.place, arm), whole.turn,
                       plus(whole.velocity, cross(whole.spin, arm)),
                       whole.spin))
  return parts[0], parts[1]


def momentaOf(bodies: tuple, states: tuple) -> tuple:
  """The 'momentaOf' function returns the momentum of 'bodies' in
  'states' and their angular momentum about the origin."""
  momentum, angular = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
  for body, state in zip(bodies, states):
    momentum = plus(momentum, body.momentumOf(state))
    about = cross(state.place, body.momentumOf(state))
    angular = plus(angular, plus(body.angularMomentumOf(state), about))
  return momentum, angular


class TestWeld(PhysTest):
  """Tests for 'Weld'."""

  def test_as_one(self) -> None:
    """Two boxes welded as an L move as the L made whole: tumbling in
    the air, and tossed onto the ground till it rests, each box's
    bristles on its own corners."""
    world = World()
    whole = world.advanced(WHOLE, TUMBLING, 2.0)
    parts = world.advancedAll(WELDED, partsOf(TUMBLING), 2.0)
    for part, middle in zip(parts, MIDDLES):
      self.assertNear(part.place, WHOLE.placeOf(whole, middle), 1e-12)
      self.assertSameTurn(part.turn, whole.turn, 1e-12)
    ground = World((0.0, 0.0, -9.81), 1e-3, Ground())
    toss = State((0.0, 0.0, 1.0), normalised((0.9, 0.2, -0.3, 0.4)),
                 (1.0, 0.5, 2.0), (3.0, -6.0, 2.0))
    whole = ground.advanced(WHOLE, toss, 6.0)
    parts = ground.advancedAll(WELDED, partsOf(toss), 6.0)
    self.assertLess(norm(whole.velocity), 1e-6)
    for part, middle in zip(parts, MIDDLES):
      self.assertNear(part.place, WHOLE.placeOf(whole, middle), 1e-9)
      self.assertLess(norm(part.velocity), 1e-6)
      self.assertTrue(part.bristles)
      for point, _, _ in part.bristles:
        self.assertLess(point, 8)

  def test_kept_together(self) -> None:
    """Welded parts tumbling keep as they lie to each other, however
    often they are stepped on."""
    states = partsOf(TUMBLING)
    apart = rotated(conjugate(states[0].turn),
                    minus(states[1].place, states[0].place))
    turned = product(conjugate(states[0].turn), states[1].turn)
    for _ in range(200):
      states = SPACE.advancedAll(WELDED, states, 0.01)
      now = rotated(conjugate(states[0].turn),
                    minus(states[1].place, states[0].place))
      self.assertNear(now, apart, 1e-12)
      self.assertSameTurn(product(conjugate(states[0].turn),
                                  states[1].turn), turned, 1e-12)

  def test_snap(self) -> None:
    """Two boxes welded moving and spinning apart are jerked together
    at once: their momentum and angular momentum kept, energy lost, both
    moving as one after."""
    apart = (State(ORIGIN, UNTURNED, (1.0, 0.0, 0.0), (0.0, 0.0, 2.0)),
             State((0.6, 0.0, 0.4), UNTURNED, (-1.0, 0.5, 0.0),
                   (5.0, 0.0, 0.0)))
    bodies = (LYING, STANDING)
    before = momentaOf(bodies, apart)
    energy = SPACE.energyOfAll(WELDED, apart)
    after = SPACE.advancedAll(WELDED, apart, 1.0)
    self.assertNear(momentaOf(bodies, after), before, 1e-11)
    self.assertLess(SPACE.energyOfAll(WELDED, after), 0.5 * energy)
    self.assertNear(after[0].spin, after[1].spin, 1e-14)

  def test_hammer(self) -> None:
    """A steel head welded to the end of a rod hung by its other end
    from a tie swings, 20 degrees, at the period by hand, and still,
    the tie holds both."""
    rod = Body.of(boxShape(1.0, 0.02, 0.02), 1000.0)
    head = Body.of(boxShape(0.1, 0.1, 0.1), 7800.0)
    hammer = Assembly((rod, head), (Tie(0, (0.5, 0.0, 0.0), None, ORIGIN),
                                    Weld((0, 1))))
    upright = turnAbout((0.0, 1.0, 0.0), -0.5 * math.pi)
    hanging = (State((0.0, 0.0, -0.5), upright),
               State((0.0, 0.0, -1.05), UNTURNED))
    mass = rod.mass + head.mass
    self.assertNear(SPACE.pullsOf(hammer, hanging), ((0.0, 0.0, 0.0),),
                    1e-12)
    self.assertNear(World().pullsOf(hammer, hanging),
                    ((0.0, 0.0, mass * 9.81),), 1e-11)
    away = (rod.mass * 0.5 + head.mass * 1.05) / mass
    about = (rod.inertia[1][1] + rod.mass * 0.25 + head.inertia[1][1]
             + head.mass * 1.05 ** 2)
    small = 2.0 * math.pi * math.sqrt(about / (mass * 9.81 * away))
    a, b = 1.0, math.cos(math.radians(10.0))
    for _ in range(40):
      a, b = 0.5 * (a + b), math.sqrt(a * b)
    swung = turnAbout((0.0, 1.0, 0.0), math.radians(20.0))
    states = tuple(State(rotated(swung, state.place),
                         product(swung, state.turn)) for state in hanging)
    crossings, before = [], None
    for step in range(5000):
      states = World().advancedAll(hammer, states, 0.001)
      middle = states[1].place
      swing = math.atan2(middle[0], -middle[2])
      if before is not None and before < 0.0 <= swing:
        crossings.append(0.001 * (step + before / (before - swing)))
      before = swing
    self.assertGreaterEqual(len(crossings), 2)
    for start, end in zip(crossings, crossings[1:]):
      self.assertLess(abs((end - start) / (small / a) - 1.0), 2e-6)

  def test_groups(self) -> None:
    """Welds sharing a body weld all their parts, spinning as one; a
    weld of one body leaves it as it is alone."""
    cube = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
    three = Assembly((LYING, STANDING, cube),
                     (Weld((0, 1)), Weld((1, 2))))
    states = (State(ORIGIN, UNTURNED, (1.0, 0.0, 0.0), (0.0, 0.0, 2.0)),
              State((0.6, 0.0, 0.4), UNTURNED, ORIGIN, (5.0, 0.0, 0.0)),
              State((0.0, 0.5, 0.0)))
    after = SPACE.advancedAll(three, states, 0.5)
    self.assertNear(after[1].spin, after[0].spin, 1e-14)
    self.assertNear(after[2].spin, after[0].spin, 1e-14)
    alone = Assembly((LYING,), (Weld((0,)),))
    self.assertEqual(SPACE.advancedAll(alone, (TUMBLING,), 1.0),
                     (SPACE.advanced(LYING, TUMBLING, 1.0),))
