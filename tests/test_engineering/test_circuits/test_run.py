"""
TestRun covers 'Run': a circuit runs from nought, switched on; it runs
on in a circuit changed, each capacitor keeping its charge, a new one
empty; its samples are kept while the circuit keeps its nodes and
parts; a node or part removed, the rest are found again by place.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.circuits import Capacitor, Resistor, Run, Source
from worQt.engineering.circuits import Switch, Wire

from . import CircuitsTest, loop


def charger(closed: bool):
  """A battery of 6 V charging 1000 µF through 1 kΩ, its switch closed
  or not."""
  return loop(Source(1, 0, 6.0, 0.0, 0.0), Switch(1, 2, closed),
              Resistor(2, 3, 1000.0), Capacitor(3, 0, 1e-3))


class TestRun(CircuitsTest):
  """Tests for 'Run'."""

  def test_starts(self) -> None:
    """A run starts at nought seconds, every capacitor empty, sampled
    once; each call to 'advance' samples it again."""
    run = Run(charger(True))
    self.assertEqual(run.time, 0.0)
    self.assertEqual(run.held.tolist(), [0.0])
    self.assertEqual(len(run.samples), 1)
    self.assertAlmostEqual(run.currents[2], 0.006, 12)
    self.assertEqual(run.advance(0.5), 0.5)
    self.assertEqual(len(run.samples), 2)
    self.assertEqual(run.latest.time, 0.5)
    self.assertEqual(run.advance(0.0), 0.0)

  def test_switched(self) -> None:
    """Opened, the switch stops the charging, the capacitor holding its
    charge; closed again, it charges on from there."""
    run = Run(charger(True))
    run.advance(1.0)
    charged = 6.0 * (1 - math.exp(-1))
    self.assertAlmostEqual(run.drops[3], charged, 10)
    run = Run(charger(False), run)
    self.assertEqual(run.time, 1.0)
    self.assertEqual(len(run.samples), 3)
    run.advance(5.0)
    self.assertAlmostEqual(run.drops[3], charged, 10)
    self.assertAlmostEqual(run.currents[2], 0.0, 12)
    run = Run(charger(True), run)
    run.advance(1.0)
    self.assertAlmostEqual(run.drops[3], 6.0 * (1 - math.exp(-2)), 10)

  def test_changed(self) -> None:
    """A part added starts empty, the samples begun anew; a part removed
    before a capacitor leaves it its charge, found by its place."""
    run = Run(charger(True))
    run.advance(1.0)
    held = run.drops[3]
    grown = charger(True).withParts(*charger(True).parts,
                                    Capacitor(2, 0, 1e-3))
    run = Run(grown, run)
    self.assertEqual(len(run.samples), 1)
    self.assertAlmostEqual(run.drops[3], held, 10)
    self.assertEqual(run.held.tolist()[1], 0.0)
    shorter = grown.withoutPart(1).withParts(
      *grown.withoutPart(1).parts, Wire(1, 2))
    run = Run(shorter, run)
    index = [type(p) for p in shorter.parts].index(Capacitor)
    self.assertAlmostEqual(run.drops[index], held, 10)
