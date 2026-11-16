"""
TestTrain covers the loop's train (user, 2026-11-16: "do all the
things": a train, points, a throttle): on the siding a powered
minecart and a minecart coupled behind it by a drawbar (a steel body
on a ball joint at either end, among the coupled cart's bodies), both
standing; the powered cart's throttle and reverser among the world's
levers beside its brake, its menu saying how far it is opened and which
way; a train put on the platform, its throttle opened, pulls its
coupled cart ahead along it, the two staying a coupling apart (the
siding's faces its buffer stop); reversed, the siding's backs the train
out of the siding through the points onto the line behind them; the
points set for the siding, the minecart pushed from the headshunt
through them goes onto the siding.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._assembly import Tie
from worQt.phys._poke import poked

from worQt.gaming.trains import Minecart
from worQt.gaming.trains._layout import EDGE, TOE
from worQt.gaming.trains._minecart import COUPLED, COUPLER_GAP

from . import TrainsTest


class TestTrain(TrainsTest):
  """Tests for the train (a minute or two)."""

  #  The loop world on the CPU, the train driven seconds at a time.
  __time_out__ = 300.0

  def test_coupled(self) -> None:
    """On the siding the powered cart and the cart coupled behind it
    stand, the drawbar between them on two ball joints, a coupling's
    gap long; the powered cart's three levers among the world's."""
    world, _ = self.loopWorld()
    _, powered, coupled = world.vehicles
    bar = coupled.bodies[-1]
    ties = [c for c in world.assembly.connections if isinstance(c, Tie)
            and bar in (c.first, c.second)]
    self.assertEqual({c.second for c in ties},
                     {powered.frame, coupled.frame})
    long = max(p[0] for p in world.assembly.bodies[bar].shape.points) - min(
      p[0] for p in world.assembly.bodies[bar].shape.points)
    self.assertAlmostEqual(long, COUPLER_GAP, 3)
    for lever in (powered.lever, powered.throttle, powered.reverser):
      self.assertIn(lever, world.peeps)
    self.assertIsNone(coupled.throttle)
    self.ran(world, 1.0)
    for vehicle in (powered, coupled):
      speed = math.sqrt(sum(v * v for v in world.states[
        vehicle.frame].velocity))
      self.assertLess(speed, 0.02)
    self.assertIn('throttle 0 % ahead', powered.readout(world.states))

  def apart(self, world: object, cars: tuple) -> float:
    """Returns how far apart the two 'cars'' frames' origins are, m
    (their bodies' own places of nought)."""
    places = [world.assembly.bodies[v.frame].placeOf(world.states[v.frame],
                                                     (0.0, 0.0, 0.0))
              for v in cars]
    return math.dist(*places)

  def test_pulls(self) -> None:
    """A train put on the platform (its powered cart's nose 4 m from the
    edge), its throttle opened, pulls its coupled cart ahead, gaining
    over 1.5 m/s in 3 s, the two a coupling apart (within 5 cm)."""
    world, _ = self.loopWorld()
    powered = Minecart(EDGE - 8.0, 0, True, None)
    world.addVehicle(powered)
    coupled = Minecart(EDGE - 8.0 - COUPLED, 0, False, powered)
    world.addVehicle(coupled)
    self.ran(world, 0.2)
    powered.throttle.used()
    self.ran(world, 3.0)
    for vehicle in (powered, coupled):
      speed = math.sqrt(sum(v * v for v in world.states[
        vehicle.frame].velocity))
      self.assertGreater(speed, 1.5)
    self.assertAlmostEqual(self.apart(world, (powered, coupled)), COUPLED,
                           None, None, 0.05)
    self.assertIn('throttle 100 % ahead', powered.readout(world.states))

  def test_backs_out(self) -> None:
    """Reversed and opened, the train backs out of the siding, through
    the points (set for the line: it trails through them) onto the
    line behind them, every wheelset there, none derailed."""
    world, _ = self.loopWorld()
    _, powered, coupled = world.vehicles
    self.ran(world, 0.2)
    powered.reverser.used()
    powered.throttle.used()
    wheels = powered.wheelsets + coupled.wheelsets
    for _ in range(20):
      self.ran(world, 1.0)
      rolling = world.solver.rolling
      if all(rolling[i]['track'] == 0 and rolling[i]['s'] < TOE - 1.0
             for i in wheels):
        break
    rolling = world.solver.rolling
    self.assertEqual([rolling[i]['track'] for i in wheels], [0] * 4)
    self.assertFalse(world.solver.derailed)
    self.assertFalse(powered.off or coupled.off)
    self.assertIn('reversed', powered.readout(world.states))

  def test_sent_to_siding(self) -> None:
    """The points set for the siding, the minecart pushed from the
    headshunt at ~3 m/s runs through them onto the siding."""
    world, _ = self.loopWorld()
    cart = world.vehicles[0]
    world.pointsLever.used()
    self.ran(world, 0.4)
    self.assertTrue(world.points.thrown)
    states = list(world.states)
    mass = sum(world.assembly.bodies[i].mass for i in cart.bodies)
    body = world.assembly.bodies[cart.frame]
    states[cart.frame] = poked(body, states[cart.frame],
                               states[cart.frame].place,
                               (3.0 * mass, 0.0, 0.0))
    world.states = tuple(states)
    for _ in range(14):
      self.ran(world, 1.0)
      rolling = world.solver.rolling
      if all(rolling[i]['track'] == 1 for i in cart.wheelsets):
        break
    rolling = world.solver.rolling
    self.assertEqual([rolling[i]['track'] for i in cart.wheelsets], [1, 1])
    self.assertFalse(world.solver.derailed)
