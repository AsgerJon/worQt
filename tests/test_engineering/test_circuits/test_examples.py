"""
TestExamples covers the examples: each is made anew, named once, with a
word on what to do, and runs a while, nothing short-circuited, its
energy kept.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Circuit, EXAMPLES, Run

from . import CircuitsTest


class TestExamples(CircuitsTest):
  """Tests for 'EXAMPLES'."""

  def test_names(self) -> None:
    """There are eight examples, each named once, with a hint and a
    speed above nought."""
    names = [example.name for example in EXAMPLES]
    self.assertEqual(len(names), 8)
    self.assertEqual(len(set(names)), 8)
    for example in EXAMPLES:
      self.assertTrue(example.hint)
      self.assertGreater(example.speed, 0.0)

  def test_runs(self) -> None:
    """Each example is a circuit, made anew each time, which runs a
    tenth of a second at its speed's pace without trouble, its energy
    kept."""
    for example in EXAMPLES:
      circuit = example.circuit()
      self.assertIsInstance(circuit, Circuit)
      self.assertIsNot(circuit, example.circuit())
      run = Run(circuit)
      self.assertEqual(run.network.problem, '', example.name)
      for _ in range(10):
        run.advance(example.speed * 0.01)
      self.assertAlmostEqual(run.energies.balance, 0.0, 9, example.name)
