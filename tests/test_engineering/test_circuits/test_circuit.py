"""
TestCircuit covers 'Circuit': the standard circuit; a part's label and
its side among parts in parallel; what it refuses; and its editing:
nodes moved, parts replaced, removed, nodes joined.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Capacitor, Circuit, Lamp, Node
from worQt.engineering.circuits import Resistor, Source, Switch
from worQt.engineering.circuits import Voltmeter, Wire

from . import CircuitsTest, SQUARE, loop


class TestCircuit(CircuitsTest):
  """Tests for 'Circuit'."""

  def test_standard(self) -> None:
    """Made of nothing, it is a battery charging a capacitor through a
    lamp, its switch open, a voltmeter across the capacitor."""
    circuit = Circuit()
    self.assertEqual(len(circuit.nodes), 5)
    self.assertEqual([circuit.label(i) for i in range(6)],
                     ['E1', 'S1', 'H1', 'C1', 'V1', 'W1'])
    self.assertEqual(circuit.parts[1], Switch(1, 2, False))
    self.assertAlmostEqual(circuit.parts[2].resistance, 120.0)

  def test_labels_and_sides(self) -> None:
    """Parts are numbered within their kind; those joining the same
    nodes are drawn straight, then a step aside, either way in turn."""
    circuit = loop(Resistor(1, 2, 1.0), Resistor(2, 1, 2.0),
                   Capacitor(1, 2, 1e-3), Resistor(1, 2, 3.0),
                   Resistor(2, 3, 4.0))
    self.assertEqual([circuit.label(i) for i in range(5)],
                     ['R1', 'R2', 'C1', 'R3', 'R4'])
    self.assertEqual([circuit.side(i) for i in range(5)],
                     [0, 1, -1, 2, 0])
    self.assertEqual(circuit.joined(1), [0, 1, 2, 3])
    self.assertEqual(circuit.at(2.0, 2.0), 2)
    self.assertIsNone(circuit.at(1.0, 1.0))

  def test_refused(self) -> None:
    """Nodes at one place, a part to a node there is not or to its own
    node, and values a part cannot have are refused."""
    with self.assertRaises(ValueError):
      Circuit((Node(0.0, 0.0), Node(0.0, 0.0)), ())
    with self.assertRaises(ValueError):
      loop(Resistor(0, 7, 1.0))
    with self.assertRaises(ValueError):
      loop(Wire(2, 2))
    for part in (Resistor(0, 1, 0.0), Capacitor(0, 1, -1.0),
                 Lamp(0, 1, 6.0, 0.0), Source(0, 1, 5.0, -1.0, 0.0),
                 Source(0, 1, 5.0, 0.0, -1.0)):
      with self.assertRaises(ValueError):
        loop(part)
    with self.assertRaises(ValueError):
      loop((0, 1))

  def test_editing(self) -> None:
    """A node is moved; a part replaced; a part removed keeps its nodes;
    a node removed takes its parts, the indices after it moved down."""
    circuit = loop(Source(1, 0, 4.5, 0.0, 0.0), Resistor(1, 2, 10.0),
                   Wire(2, 3), Wire(3, 0))
    moved = circuit.withNode(2, Node(3.0, 2.0))
    self.assertEqual(moved.nodes[2], Node(3.0, 2.0))
    replaced = circuit.withPart(1, Resistor(1, 2, 20.0))
    self.assertEqual(replaced.parts[1].resistance, 20.0)
    fewer = circuit.withoutPart(1)
    self.assertEqual(len(fewer.parts), 3)
    self.assertEqual(len(fewer.nodes), 4)
    gone = circuit.withoutNode(2)
    self.assertEqual(gone.nodes, (SQUARE[0], SQUARE[1], SQUARE[3]))
    self.assertEqual(gone.parts, (Source(1, 0, 4.5, 0.0, 0.0),
                                  Wire(2, 0)))

  def test_merged(self) -> None:
    """A node joined into another takes its parts with it; the parts
    between the two are gone."""
    circuit = loop(Source(1, 0, 4.5, 0.0, 0.0), Resistor(1, 2, 10.0),
                   Wire(2, 3), Voltmeter(3, 0))
    merged = circuit.merged(0, 3)
    self.assertEqual(len(merged.nodes), 3)
    self.assertEqual(merged.parts, (Source(1, 0, 4.5, 0.0, 0.0),
                                    Resistor(1, 2, 10.0), Wire(2, 0)))
    self.assertIs(circuit.merged(1, 1), circuit)
