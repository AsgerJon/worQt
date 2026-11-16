"""
TestCoupling covers the buffers and couplings (user, 2026-11-16: "make
trains have collision and all that"): a pair of buffers only pushes,
slack till their heads meet; a screw coupling only pulls, tightened
just short of them; on the oval every front meets every other car's
back and the siding's stop by its buffers, cars coupled are coupled,
any two cars not coupled meet as bodies; the train stands buffer to
buffer, pulls its coaches by their couplings and is pushed into by
them braking (never further than the buffers give); a loose coach
shoved into the next stops on its buffers, the next going on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._assembly import Contact, Spring
from worQt.phys._body import State

from worQt.gaming.trains._coach import COACH_LONG
from worQt.gaming.trains._coupling import BUFFER_LONG, BUFFER_SIDE, CarEnd
from worQt.gaming.trains._coupling import COUPLING_TIGHT, buffersOf
from worQt.gaming.trains._coupling import couplingOf

from . import TrainsTest

#  How far buffers may give at most, m (a buffer's stroke).
STROKE = 0.105


class TestCoupling(TrainsTest):
  """Tests for the buffers and couplings (a few minutes on the CPU)."""

  __time_out__ = 600.0

  def apartOf(self, world: object, front: CarEnd, back: CarEnd) -> float:
    """Returns how far apart the heads of 'front''s and 'back''s left
    buffers are, m (below nought: pressed together)."""
    bodies, states = world.assembly.bodies, world.states
    one = bodies[front.body].placeOf(states[front.body], front.base(1.0))
    two = bodies[back.body].placeOf(states[back.body], back.base(1.0))
    return math.dist(one, two) - 2.0 * BUFFER_LONG

  def test_springs(self) -> None:
    """A pair of buffers pushes only, slack till the heads meet, one a
    side; a coupling pulls only, between the middles, just short."""
    front, back = CarEnd(1, 10.12, 1.0, None), CarEnd(2, -10.12, -1.0, None)
    left, right = buffersOf(front, back)
    for spring, side in ((left, 1.0), (right, -1.0)):
      self.assertFalse(spring.pulls)
      self.assertTrue(spring.pushes)
      self.assertEqual(spring.rest, 2.0 * BUFFER_LONG)
      self.assertEqual(spring.firstPoint[1], side * BUFFER_SIDE)
      self.assertEqual(spring.firstPoint[0], 10.12 - BUFFER_LONG)
      self.assertEqual(spring.secondPoint[0], -10.12 + BUFFER_LONG)
    coupling = couplingOf(front, back)
    self.assertTrue(coupling.pulls)
    self.assertFalse(coupling.pushes)
    self.assertEqual(coupling.firstPoint[1], 0.0)
    self.assertAlmostEqual(coupling.rest,
                           2.0 * BUFFER_LONG - COUPLING_TIGHT, 12)
    self.assertTrue(left.slack(2.0 * BUFFER_LONG + 0.01))
    self.assertFalse(left.slack(2.0 * BUFFER_LONG - 0.01))
    self.assertTrue(coupling.slack(coupling.rest - 0.01))

  def test_ends(self) -> None:
    """Every front meets every other vehicle's back and the stop by a
    pair of buffers; each coach of the train coupled to the car ahead,
    the loose ones to nothing; two cars not coupled meet as bodies, two
    coupled do not."""
    world = self.ovalWorld()
    vehicles = world.vehicles
    self.assertEqual(len(world.buffers),
                     2 * len(vehicles) * len(vehicles))
    couplings = [c for c in world.assembly.connections
                 if isinstance(c, Spring) and not c.pushes]
    self.assertEqual(len(couplings), 3)
    pairs = {(c.first, c.second) for c in couplings}
    ahead = vehicles[0]
    for coach in world.vehicles[1:4]:
      self.assertIn((coach.frame, ahead.back.body), pairs)
      ahead = coach
    touching = {frozenset((c.first, c.second))
                for c in world.assembly.connections
                if isinstance(c, Contact)}
    engine, first, second = vehicles[0], vehicles[1], vehicles[2]
    self.assertNotIn(frozenset((first.frame, engine.tender)), touching)
    self.assertNotIn(frozenset((first.frame, second.frame)), touching)
    self.assertIn(frozenset((second.frame, engine.tender)), touching)
    for loose in world.loose:
      self.assertIn(frozenset((loose.frame, engine.frame)), touching)

  def test_stands(self) -> None:
    """Standing, the train's cars stand buffer to buffer (pressed a few
    millimetres by their couplings), the loose coaches likewise."""
    world = self.ovalWorld()
    self.ran(world, 1.0)
    vehicles = world.vehicles
    for k in (1, 2, 3, 5, 6):
      apart = self.apartOf(world, vehicles[k].front, vehicles[k - 1].back)
      with self.subTest(car=k):
        self.assertLess(abs(apart), 0.005)

  def test_pulls_and_pushes(self) -> None:
    """Pulling away the coaches follow by their couplings (the last
    within 5 cm of where it stood behind the engine); braking from
    3 m/s they press into the car ahead no further than the buffers
    give."""
    world = self.ovalWorld()
    engine, last = world.vehicles[0], world.vehicles[3]
    standing = math.dist(world.states[engine.frame].place,
                         world.states[last.frame].place)
    was = world.states[last.frame].place
    engine.regulator.used()
    self.ran(world, 3.0)
    self.assertGreater(math.dist(world.states[last.frame].place, was),
                       0.2)
    self.assertLess(abs(math.dist(world.states[engine.frame].place,
                                  world.states[last.frame].place)
                        - standing), 0.05)
    engine.regulator.used()
    states = list(world.states)
    for vehicle in world.vehicles[:4]:
      for index in vehicle.bodies:
        state = states[index]
        states[index] = State(state.place, state.turn, (3.0, 0.0, 0.0),
                              state.spin)
    world.states = tuple(states)
    engine.brake.used()
    least = 0.0
    for _ in range(60):
      self.ran(world, 1.0 / 30.0)
      for k in (1, 2, 3):
        least = min(least, self.apartOf(world, world.vehicles[k].front,
                                        world.vehicles[k - 1].back))
    self.assertGreater(least, -STROKE)

  def test_shunted(self) -> None:
    """The last loose coach shoved into the one ahead at 2 m/s: they
    meet on their buffers (never nearer than the buffers give), the one
    shoved slows and the ones ahead go on."""
    world = self.ovalWorld()
    self.ran(world, 0.3)
    first, middle, last = world.loose
    states = list(world.states)
    for index in last.bodies:
      state = states[index]
      states[index] = State(state.place, state.turn, (2.0, 0.0, 0.0),
                            state.spin)
    world.states = tuple(states)
    least = 0.0
    for _ in range(45):
      self.ran(world, 1.0 / 30.0)
      least = min(least, self.apartOf(world, last.front, middle.back),
                  self.apartOf(world, middle.front, first.back))
    self.assertGreater(least, -STROKE)
    self.assertLess(world.states[last.frame].velocity[0], 1.5)
    self.assertGreater(world.states[first.frame].velocity[0], 0.3)
    self.assertGreater(math.dist(world.states[first.frame].place,
                                 world.states[last.frame].place),
                       2.0 * COACH_LONG - 2.0 * STROKE)
