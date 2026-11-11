"""
TestSemiconductors covers diodes, light emitting diodes and transistors,
each in its regions, checked against the hand's own results: a diode
keeps 0.7 V forward and blocks backward; a transistor off, active,
its collector current its gain times its base current, or fully on;
a rectifier passes only the upper halves; two transistors blink in
turn, each off for R C ln((E - 0.7 + swing) / (E - 0.7)); an
amplifier's gain is its collector's resistance over its emitter's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.circuits import Circuit, Diode, Led, Network, Node
from worQt.engineering.circuits import Resistor, Run, Source, Switch
from worQt.engineering.circuits import Transistor, Wire
from worQt.engineering.circuits._examples import amplifier, blinker
from worQt.engineering.circuits._examples import rectifier, switching

from . import CircuitsTest, loop

ON = 0.1  # Ω behind a diode's or a junction's voltage


def biased(base: float) -> Circuit:
  """9 V; 1 kΩ to a transistor's collector, its emitter to the minus
  pole, its base fed through 'base' Ω from the plus pole."""
  nodes = (Node(0.0, 0.0), Node(0.0, 4.0), Node(4.0, 4.0), Node(4.0, 2.0),
           Node(4.0, 0.0), Node(2.0, 1.0))
  return Circuit(nodes, (
    Source(1, 0, 9.0, 0.0, 0.0), Wire(1, 2), Resistor(2, 3, 1000.0),
    Transistor(3, 4, 5, 100.0), Wire(4, 0), Resistor(1, 5, base)))


class TestSemiconductors(CircuitsTest):
  """Tests for 'Diode', 'Led' and 'Transistor', through 'Run'."""

  def test_diode(self) -> None:
    """Forward, a diode keeps 0.7 V, behind a tenth of an ohm: (5 - 0.7)
    / 100.1 A through 100 Ω; turned round it blocks, all 5 V across
    it."""
    run = Run(loop(Source(1, 0, 5.0, 0.0, 0.0), Diode(1, 2, 0.7),
                   Resistor(2, 3, 100.0), Wire(3, 0)))
    self.assertEqual(run.regions[1], 'on')
    self.assertAlmostEqual(run.currents[1], 4.3 / (100.0 + ON), 12)
    run = Run(loop(Source(1, 0, 5.0, 0.0, 0.0), Diode(2, 1, 0.7),
                   Resistor(2, 3, 100.0), Wire(3, 0)))
    self.assertEqual(run.regions[1], 'off')
    self.assertAlmostEqual(run.currents[1], 0.0, 12)
    self.assertAlmostEqual(run.drops[1], -5.0, 12)

  def test_led(self) -> None:
    """A red light emitting diode keeps 2 V: 9 V through 330 Ω gives it
    (9 - 2) / 330.1 A."""
    run = Run(loop(Source(1, 0, 9.0, 0.0, 0.0), Resistor(1, 2, 330.0),
                   Led(2, 3, 2.0, 0.02), Wire(3, 0)))
    self.assertEqual(run.regions[2], 'on')
    self.assertAlmostEqual(run.currents[2], 7.0 / (330.0 + ON), 12)

  def test_active(self) -> None:
    """Fed through 100 kΩ, the base takes (9 - 0.7) / 100000.1 A, the
    collector a hundred times it, 0.7 V left across it: active."""
    run = Run(biased(100000.0))
    base = 8.3 / (100000.0 + ON)
    self.assertEqual(run.regions[3], 'active')
    self.assertAlmostEqual(run.bases[3], base, 14)
    self.assertAlmostEqual(run.currents[3], 100 * base, 8)
    self.assertAlmostEqual(run.drops[3], 9.0 - 1000.0 * 100 * base, 5)
    run.advance(1.0)
    delivered = 9.0 * (run.currents[3] + run.bases[3])
    self.assertAlmostEqual(run.energies.delivered, delivered, 9)
    self.assertAlmostEqual(run.energies.balance, 0.0, 12)

  def test_saturated(self) -> None:
    """Fed through 10 kΩ, a hundred times the base current is more than
    1 kΩ lets through: fully on, 0.2 V across it behind a tenth of an
    ohm, the collector current (9 - 0.2) / 1000.1 A."""
    run = Run(biased(10000.0))
    self.assertEqual(run.regions[3], 'saturated')
    self.assertAlmostEqual(run.currents[3], 8.8 / (1000.0 + ON), 12)
    self.assertLess(run.currents[3], 100 * run.bases[3])

  def test_switch(self) -> None:
    """In the transistor switch, open, the transistor is off and the
    light emitting diode dark; closed, under a milliampere into the base
    lets 20 mA through it."""
    circuit = switching()
    run = Run(circuit)
    self.assertEqual(run.regions[5], 'off')
    self.assertAlmostEqual(run.currents[4], 0.0, 12)
    run = Run(circuit.withPart(7, Switch(2, 8, True)), run)
    self.assertEqual(run.regions[5], 'saturated')
    self.assertAlmostEqual(run.bases[5], 8.3 / (10000.0 + ON), 12)
    self.assertAlmostEqual(run.currents[9], run.bases[5], 12)
    self.assertAlmostEqual(run.currents[4], 6.8 / (330.0 + 2 * ON), 12)

  def test_rectifier(self) -> None:
    """The diode passes the upper halves of 12 V at 50 Hz, peaking at
    (12 - 0.7) 100 / 100.1 V across the load, never below nought."""
    run = Run(rectifier())
    most, least = -1.0, 1.0
    for _ in range(1000):
      run.advance(1 / 50 / 500)
      most = max(most, run.drops[6])
      least = min(least, run.drops[6])
    self.assertAlmostEqual(most, 11.3 * 100.0 / (100.0 + ON), 4)
    self.assertAlmostEqual(least, 0.0, 12)
    self.assertAlmostEqual(run.energies.balance, 0.0, 10)

  def test_blinker(self) -> None:
    """The blinker starts with one transistor fully on and the other
    off, never both active, and turns every R C ln((9 - 0.7 + 6.8) /
    (9 - 0.7)) s, the collector swinging 6.8 V, from 9 V less the
    light emitting diode's 2 V to 0.2 V."""
    run = Run(blinker())
    self.assertEqual(sorted((run.regions[11], run.regions[12])),
                     ['off', 'saturated'])
    self.assertFalse(run.network.unstable())
    turns, last = [], run.regions[11]
    for _ in range(2000):
      run.advance(0.001)
      if run.regions[11] != last:
        turns.append(run.time)
        last = run.regions[11]
    half = 47000.0 * 10e-6 * math.log((8.3 + 6.8) / 8.3)
    self.assertGreater(len(turns), 4)
    for before, after in zip(turns[1:], turns[2:]):
      self.assertLess(abs(after - before - half), 0.01 * half)
    self.assertAlmostEqual(run.energies.balance, 0.0, 10)

  def test_unstable(self) -> None:
    """Both transistors of the blinker active hold at the start, but
    grow of themselves away from it."""
    circuit = blinker()
    regions = [None] * len(circuit.parts)
    regions[6] = regions[8] = 'on'
    regions[11] = regions[12] = 'active'
    self.assertTrue(Network(circuit, (*regions,)).unstable())
    regions[12] = 'off'
    regions[11] = 'saturated'
    self.assertFalse(Network(circuit, (*regions,)).unstable())

  def test_amplifier(self) -> None:
    """Settled, the amplifier is active and its output swings the input's
    0.2 V times (100 / 101) (2.2 kΩ || 10 kΩ) / 470 Ω, the other way
    round."""
    run = Run(amplifier())
    run.advance(1.0)
    self.assertEqual(run.regions[8], 'active')
    most, least, turned = -1.0, 1.0, 0
    for _ in range(400):
      run.advance(1 / 1000 / 200)
      most = max(most, run.drops[12])
      least = min(least, run.drops[12])
      if run.drops[2] > 0.15:
        turned += 1 if run.drops[12] < 0 else 0
    load = 2200.0 * 10000.0 / 12200.0
    gain = 100.0 / 101.0 * load / 470.0
    self.assertLess(abs((most - least) / 0.4 - gain), 0.02 * gain)
    self.assertGreater(turned, 0)

  def test_refused(self) -> None:
    """A region a part cannot be in, or regions not one a part, are
    refused; a transistor joins three nodes apart, of a gain above
    nought."""
    circuit = biased(10000.0)
    with self.assertRaises(ValueError):
      Network(circuit, (None, None, None, 'on', None, None))
    with self.assertRaises(ValueError):
      Network(circuit, (None,))
    with self.assertRaises(ValueError):
      circuit.withPart(3, Transistor(3, 4, 4, 100.0))
    with self.assertRaises(ValueError):
      circuit.withPart(3, Transistor(3, 4, 5, 0.0))
