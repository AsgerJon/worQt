"""
TestNetwork covers 'Network', checked against the hand's own results:
a divider, a source's internal resistance, a capacitor charging, a coil
taking up current, a circuit swinging for ever and one critically
damped, alternating current through a capacitor, the energy kept; a
short circuit refused; an ammeter beside a wire, a voltmeter across an
open switch; a capacitor across a battery and a coil cut off, at once.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.circuits import Ammeter, Capacitor, Circuit, Coil
from worQt.engineering.circuits import Network, Node, Resistor, Run
from worQt.engineering.circuits import Source, Switch, Voltmeter, Wire

from . import CircuitsTest, SQUARE, loop, rlc


class TestNetwork(CircuitsTest):
  """Tests for 'Network', through 'Run'."""

  def test_divider(self) -> None:
    """12 V over 1 kΩ and 2 kΩ in series: 4 mA, 8 V across the 2 kΩ;
    the minus pole is nought volts."""
    run = Run(loop(Source(1, 0, 12.0, 0.0, 0.0), Resistor(1, 2, 1000.0),
                   Resistor(2, 3, 2000.0), Wire(3, 0)))
    self.assertAlmostEqual(run.currents[1], 0.004, 12)
    self.assertAlmostEqual(run.drops[2], 8.0, 9)
    self.assertAlmostEqual(run.voltages[0], 0.0, 12)
    self.assertAlmostEqual(run.voltages[1], 12.0, 9)

  def test_internal_resistance(self) -> None:
    """4.5 V with 1.5 Ω inside, 7.5 Ω outside: 0.5 A, 3.75 V at the
    poles, as the ammeter and the voltmeter read; the current out of the
    plus pole runs from minus to plus inside."""
    run = Run(loop(Source(1, 0, 4.5, 0.0, 1.5), Resistor(1, 2, 7.5),
                   Ammeter(2, 3), Wire(3, 0), Voltmeter(1, 0)))
    self.assertAlmostEqual(run.currents[2], 0.5, 12)
    self.assertAlmostEqual(run.drops[4], 3.75, 12)
    self.assertAlmostEqual(run.drops[0], 3.75, 12)
    self.assertAlmostEqual(run.currents[0], -0.5, 12)

  def test_charging(self) -> None:
    """A capacitor charges through a resistor along E (1 - exp(-t /
    RC)), its one mode the time constant RC; in the end it holds C E² /
    2, as much as was turned to heat."""
    circuit = loop(Source(1, 0, 6.0, 0.0, 0.0), Resistor(1, 2, 470.0),
                   Capacitor(2, 3, 2200e-6), Wire(3, 0))
    tau = 470.0 * 2200e-6
    self.assertEqual(len(Network(circuit).modes()), 1)
    self.assertAlmostEqual(Network(circuit).modes()[0][0], tau, 12)
    run = Run(circuit)
    for _ in range(3):
      run.advance(tau / 3)
    self.assertAlmostEqual(run.drops[2], 6.0 * (1 - math.exp(-1)), 10)
    run.advance(60.0)
    stored = 2200e-6 * 36.0 / 2
    self.assertAlmostEqual(run.energies.stored, stored, 10)
    self.assertAlmostEqual(run.energies.heat, stored, 9)
    self.assertAlmostEqual(run.energies.balance, 0.0, 10)
    self.assertAlmostEqual(run.charges[2], 2200e-6 * 6.0, 10)

  def test_coil(self) -> None:
    """A coil takes up current through a resistor along E / R (1 -
    exp(-t R / L))."""
    run = Run(loop(Source(1, 0, 10.0, 0.0, 0.0), Resistor(1, 2, 5.0),
                   Coil(2, 3, 2.0), Wire(3, 0)))
    self.assertAlmostEqual(run.network.modes()[0][0], 0.4, 12)
    run.advance(0.4)
    self.assertAlmostEqual(run.currents[2], 2.0 * (1 - math.exp(-1)), 10)

  def test_swinging(self) -> None:
    """A capacitor charged to 5 V, switched onto a coil, swings at 1 /
    (2 pi sqrt(LC)) for ever, as much after a hundred swings as at the
    start."""
    nodes = (*SQUARE, Node(4.0, 2.0), Node(4.0, 0.0))
    charging = Circuit(nodes, (
      Source(1, 0, 5.0, 0.0, 0.0), Switch(1, 2, True),
      Capacitor(2, 3, 1e-6), Wire(3, 0), Switch(2, 4, False),
      Coil(4, 5, 1.0), Wire(5, 3)))
    run = Run(charging)
    run.advance(0.01)
    self.assertAlmostEqual(run.drops[2], 5.0, 9)
    swinging = charging.withPart(1, Switch(1, 2, False))
    swinging = swinging.withPart(4, Switch(2, 4, True))
    run = Run(swinging, run)
    (tau, frequency), = run.network.modes()
    self.assertTrue(math.isinf(tau))
    self.assertAlmostEqual(frequency, 1 / (2 * math.pi * 1e-3), 6)
    run.advance(100 / frequency)
    self.assertAlmostEqual(run.drops[2], 5.0, 6)
    run.advance(0.25 / frequency)
    self.assertAlmostEqual(run.drops[2], 0.0, 6)
    self.assertAlmostEqual(abs(run.currents[5]), 5.0 * 1e-3, 8)

  def test_critical(self) -> None:
    """At R = 2 sqrt(L / C) the capacitor charges without overshooting,
    along 1 - (1 + a t) exp(-a t), a = R / 2L."""
    resistance = 2 * math.sqrt(1.0 / 1e-4)
    rate = resistance / 2
    for seconds in (0.005, 0.01, 0.03):
      run = Run(rlc(1.0, resistance, 1.0, 1e-4))
      run.advance(seconds)
      expected = 1 - (1 + rate * seconds) * math.exp(-rate * seconds)
      self.assertAlmostEqual(run.drops[3], expected, 9)

  def test_damped(self) -> None:
    """Below critical damping it swings at sqrt(1 / LC - (R / 2L)²) / 2
    pi, dying away in 2L / R."""
    (tau, frequency), = Network(rlc(1.0, 20.0, 1.0, 1e-4)).modes()
    self.assertAlmostEqual(tau, 0.1, 9)
    expected = math.sqrt(1e4 - 100.0) / (2 * math.pi)
    self.assertAlmostEqual(frequency, expected, 9)

  def test_alternating(self) -> None:
    """10 V at 50 Hz through 100 Ω and 10 µF: once settled, the current
    peaks at U / |Z|, Z = R + 1 / (j w C), and the source starts from
    nought."""
    circuit = loop(Source(1, 0, 10.0, 50.0, 0.0), Resistor(1, 2, 100.0),
                   Capacitor(2, 3, 10e-6), Wire(3, 0))
    run = Run(circuit)
    self.assertAlmostEqual(run.drops[0], 0.0, 12)
    run.advance(1.0)
    turn = 2 * math.pi * 50.0
    size = abs(complex(100.0, -1 / (turn * 10e-6)))
    most = 0.0
    for _ in range(1000):
      run.advance(1 / 50 / 1000)
      most = max(most, abs(run.currents[1]))
    self.assertAlmostEqual(most, 10.0 / size, 6)

  def test_short_circuit(self) -> None:
    """A source's poles joined by wire alone, or two ideal sources side
    by side, is a short circuit: refused, the run holding still; an
    internal resistance mends it."""
    shorted = loop(Source(1, 0, 4.5, 0.0, 0.0), Wire(1, 2), Wire(2, 3),
                   Wire(3, 0))
    network = Network(shorted)
    self.assertIn("E1's poles", network.problem)
    self.assertEqual(network.problemPart, 0)
    run = Run(shorted)
    self.assertEqual(run.advance(1.0), 0.0)
    self.assertEqual(run.time, 0.0)
    pair = Circuit(SQUARE[:2], (Source(1, 0, 5.0, 0.0, 0.0),
                                Source(1, 0, 4.0, 0.0, 0.0)))
    self.assertEqual(Network(pair).problemPart, 1)
    mended = shorted.withPart(0, Source(1, 0, 4.5, 0.0, 0.5))
    self.assertEqual(Network(mended).problem, '')
    self.assertAlmostEqual(Run(mended).currents[1], 9.0, 9)

  def test_meters(self) -> None:
    """An ammeter beside a wire reads nought, the wire taking it all; a
    voltmeter across an open switch reads the source's voltage."""
    beside = loop(Source(1, 0, 6.0, 0.0, 0.0), Resistor(1, 2, 6.0),
                  Wire(2, 3), Ammeter(2, 3), Wire(3, 0))
    run = Run(beside)
    self.assertAlmostEqual(run.currents[3], 0.0, 12)
    self.assertAlmostEqual(run.currents[2], 1.0, 12)
    across = loop(Source(1, 0, 6.0, 0.0, 0.0), Switch(1, 2, False),
                  Voltmeter(1, 2), Resistor(2, 3, 6.0), Wire(3, 0))
    run = Run(across)
    self.assertAlmostEqual(run.drops[2], 6.0, 12)
    self.assertAlmostEqual(run.currents[3], 0.0, 12)

  def test_at_once(self) -> None:
    """A capacitor straight across a battery charges at once, half the
    energy lost; a coil cut off by its switch stops at once, its energy
    turned to heat; neither shows a mode."""
    straight = loop(Source(1, 0, 5.0, 0.0, 0.0), Wire(1, 2),
                    Capacitor(2, 3, 1e-3), Wire(3, 0))
    run = Run(straight)
    self.assertEqual(run.network.modes(), ())
    run.advance(0.02)
    self.assertAlmostEqual(run.drops[2], 5.0, 9)
    self.assertAlmostEqual(run.energies.heat, 1e-3 * 25.0 / 2, 8)
    flowing = loop(Source(1, 0, 10.0, 0.0, 0.0), Resistor(1, 2, 10.0),
                   Coil(2, 3, 1.0), Switch(3, 0, True))
    run = Run(flowing)
    run.advance(10.0)
    self.assertAlmostEqual(run.currents[2], 1.0, 9)
    run = Run(flowing.withPart(3, Switch(3, 0, False)), run)
    self.assertEqual(run.network.modes(), ())
    run.advance(0.02)
    self.assertAlmostEqual(run.currents[2], 0.0, 12)
    self.assertAlmostEqual(run.energies.stored, 0.0, 12)
    self.assertAlmostEqual(run.energies.balance, 0.0, 9)
