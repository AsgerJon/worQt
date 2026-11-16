"""
TestLocomotive covers the steam train on its oval (user, 2026-11-16: "a
steam locomotive and a bunch of cars being pulled by it. At first we
will have the cylinders moved by the steam just be actuators"): the
oval is closed and the rail world finds it so; the engine, its bogie,
its rods and crossheads, its tender and three coaches stand, each axle
carrying what it was built to (the drivers 20 t, the trailing axle 14,
the bogie's 9, the tender's ~16), every rod on its crank pins; the
valves admit steam the way the gear runs the engine, for the first
'CUTOFF' of a stroke; the regulator opened, the train pulls away ahead
(the rods within 2 cm of their pins under full steam); reversed, it
backs; the brake (a train brake: every vehicle's shoes) slows it; a
tender shoved off its rails is taken off, the world going on, and put
back as it was made; dressed in the model where the model is.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys._poke import poked
from worQt.phys._vectors import rotated

from worQt.gaming.trains._locomotive import CRANKS, CUTOFF, Locomotive
from worQt.gaming.trains._model import MODEL
from worQt.gaming.trains._coach import Coach

from . import TrainsTest

#  What each of the engine's axles carries as built, t (drivers, the
#  trailing axle, the bogie's two, the tender's three), and how near.
AXLES = (20.0, 20.0, 20.0, 14.0, 9.0, 9.0, 16.0, 16.0, 16.0)
NEAR = 0.12


class TestLocomotive(TrainsTest):
  """Tests for the steam train (a few minutes on the CPU)."""

  __time_out__ = 900.0

  def pinsApart(self, world: object) -> float:
    """Returns how far the engine's rods' eyes are from their crank
    pins at most, m."""
    engine, states = world.vehicles[0], world.states
    worst = 0.0
    for pin in engine._pins:
      w = states[pin.wheelset]
      at = numpy.array(w.place) + numpy.array(rotated(w.turn, pin.journal))
      eye = numpy.array(world.assembly.bodies[pin.frame].placeOf(
        states[pin.frame], pin.box))
      worst = max(worst, float(numpy.linalg.norm(at - eye)))
    return worst

  def speedOf(self, world: object) -> float:
    """Returns the engine's speed along its own x (above nought: ahead),
    m/s."""
    engine = world.vehicles[0]
    state = world.states[engine.frame]
    ahead = rotated(state.turn, (1.0, 0.0, 0.0))
    return sum(v * a for v, a in zip(state.velocity, ahead))

  def test_stands(self) -> None:
    """The oval closed; the train stands, each axle carrying what it was
    built to, every rod on its crank pins."""
    world = self.ovalWorld()
    engine = world.vehicles[0]
    self.assertIsInstance(engine, Locomotive)
    self.assertEqual([type(v) for v in world.vehicles[1:]], [Coach] * 3)
    self.assertEqual(engine.train, tuple(world.vehicles[1:]))
    self.ran(world, 1.5)
    self.assertEqual(world.solver.closed, frozenset((0,)))
    self.assertLess(abs(self.speedOf(world)), 0.05)
    rolling = world.solver.rolling
    for index, wanted in zip(engine.wheelsets, AXLES):
      with self.subTest(wheelset=index):
        carried = sum(rolling[index]['loads'].values()) / 9810.0
        self.assertAlmostEqual(carried, wanted, None, None, NEAR * wanted)
    self.assertLess(self.pinsApart(world), 1e-3)

  def test_admits(self) -> None:
    """Ahead, steam pushes a piston its crank's way round (ahead with the
    crank up, back with it down), only for the first 'CUTOFF' of the
    stroke; reversed, the other way; at a dead centre nothing."""
    engine = Locomotive(0.0, 0)
    self.assertEqual(engine.admitted(0.5 * math.pi, 1.0), 1.0)
    self.assertEqual(engine.admitted(-0.5 * math.pi, 1.0), -1.0)
    self.assertEqual(engine.admitted(0.5 * math.pi, -1.0), -1.0)
    self.assertEqual(engine.admitted(0.0, 1.0), 0.0)
    late = math.pi * (1.0 - 0.5 * (1.0 - CUTOFF))
    self.assertEqual(engine.admitted(0.05, 1.0), 0.0)
    self.assertEqual(engine.admitted(math.pi - 0.05, 1.0), 1.0)
    self.assertEqual(sorted(CRANKS), [-1.0, 1.0])
    self.assertGreater(late, 0.5 * math.pi)

  def test_pulls(self) -> None:
    """The regulator opened, the train pulls away ahead (over 0.4 m/s in
    3 s), every rod within 2 cm of its pins."""
    world = self.ovalWorld()
    engine = world.vehicles[0]
    self.ran(world, 0.3)
    engine.regulator.used()
    self.ran(world, 3.0)
    self.assertGreater(self.speedOf(world), 0.4)
    self.assertLess(self.pinsApart(world), 0.02)
    self.assertIn('regulator 100 % ahead', engine.readout(world.states))

  def test_backs(self) -> None:
    """Reversed and opened, it backs."""
    world = self.ovalWorld()
    engine = world.vehicles[0]
    self.ran(world, 0.3)
    engine.reverser.used()
    engine.regulator.used()
    self.ran(world, 3.0)
    self.assertLess(self.speedOf(world), -0.4)
    self.assertIn('reversed', engine.readout(world.states))

  def test_brakes(self) -> None:
    """Rolling at 3 m/s, the brake pulled slows the whole train (every
    coach's shoes too) by over 1.5 m/s in 2 s; released, it rolls on."""
    for pulled in (True, False):
      with self.subTest(pulled=pulled):
        world = self.ovalWorld()
        engine = world.vehicles[0]
        self.ran(world, 0.3)
        states = list(world.states)
        for vehicle in world.vehicles:
          for index in vehicle.bodies:
            state = states[index]
            ahead = rotated(states[engine.frame].turn, (3.0, 0.0, 0.0))
            states[index] = type(state)(state.place, state.turn, ahead,
                                        state.spin)
        world.states = tuple(states)
        self.ran(world, 0.5)
        if pulled:
          engine.brake.used()
        was = self.speedOf(world)
        self.ran(world, 2.0)
        lost = was - self.speedOf(world)
        if pulled:
          self.assertGreater(lost, 1.5)
          self.assertGreater(world.vehicles[1].boxes[0].brake, 0.0)
        else:
          self.assertLess(lost, 0.5)

  def test_derails(self) -> None:
    """The tender shoved sideways off its rails is taken off (its three
    wheelsets free bodies held by springs; the first coach may follow it
    off), the world going on; every vehicle put back, the train is as it
    was made."""
    world = self.ovalWorld()
    engine = world.vehicles[0]
    self.ran(world, 0.3)
    made = world.assembly.connections
    body = world.assembly.bodies[engine.tender]
    states = list(world.states)
    tender = states[engine.tender]
    states[engine.tender] = poked(body, tender, body.placeOf(
      tender, (0.0, 0.0, 2.5)), (0.0, -6.0 * body.mass, 0.0))
    world.states = tuple(states)
    self.ran(world, 2.0)
    self.assertLessEqual(set(engine.wheelsets[6:]), set(engine.off))
    self.assertIsNone(world.trouble)
    for vehicle in world.vehicles:
      vehicle.restored()
      self.assertEqual(vehicle.off, {})
    self.assertEqual(sorted(map(id, world.assembly.connections)),
                     sorted(map(id, made)))

  def test_dressed(self) -> None:
    """Where the model is, the engine's moving bodies are dressed in its
    parts (the engine, the bogie, nine wheelsets, six rods, two
    crossheads, the tender)."""
    if not MODEL.is_file():
      self.skipTest('the model is not here (it is not in git)')
    world = self.ovalWorld()
    self.assertEqual(len(world.dressed), 20)
    for parts in world.dressed.values():
      for rows, indices, look in parts:
        self.assertEqual(rows.shape[1], 6)
        self.assertIn(look, world.looks)
