"""
TestSuperQuests covers the super quests: each is solved by its own
solution, built only of what was granted before it, on its test bench,
which sets its inputs itself; a carry rippled through is right but too
deep for the look-ahead; a wrong gate never passes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Chip, Node, Wire
from worQt.engineering.quests import MAIN, SUPER, Tester, bench, depthOf

from . import QuestsTest, play


def _grown(circuit, *parts):
  """'circuit' with 'parts' added."""
  return circuit.withParts(*circuit.parts, *parts)


class TestSuperQuests(QuestsTest):
  """Tests for the super quests."""

  def test_solved(self) -> None:
    """Each super quest's solution passes its test bench."""
    for quest in SUPER:
      goal = quest.newGoal()
      self.assertIsInstance(goal, Tester)
      run = play(quest.solution(quest.circuit()), goal, 0.02, 30.0)
      self.assertTrue(goal.reached, '%s: %s' % (quest.name,
                                                goal.words(run)))

  def test_bench(self) -> None:
    """A bench has its inputs and probes named, its pins named, a
    supply only when asked; the bench sets its inputs itself."""
    given = bench(('A', 'B'), ('Q',), True)
    circuit = given.circuit
    self.assertEqual([circuit.label(i) for i in given.inputs], ['A', 'B'])
    self.assertEqual([circuit.label(i) for i in given.outputs], ['Q'])
    for name in ('A', 'B', 'Q', 'G0', '+0'):
      self.assertIn(name, given.pins)
    self.assertNotIn('+0', bench(('A',), ('Q',), False).pins)
    quest = SUPER[1]
    goal = quest.newGoal()
    run = play(quest.circuit(), goal, 0.02, 0.6)
    levels = [run.circuit.parts[i].high for i in given.inputs]
    self.assertNotEqual(levels, [False, False])

  def test_ripple(self) -> None:
    """Carries rippled one by one are right, but C4 reads through 8
    chips, too deep: the look-ahead is not reached."""
    quest = SUPER[6]
    given = bench(('G0', 'G1', 'G2', 'G3', 'P0', 'P1', 'P2', 'P3', 'C0'),
                  ('C1', 'C2', 'C3', 'C4'), False)
    circuit = given.circuit
    nodes, parts = [*circuit.nodes], [*circuit.parts]
    carry = given.pins['C0']
    for k in range(4):
      product, total = len(nodes), len(nodes) + 1
      nodes += [Node(60.0 + k, 60.0), Node(60.0 + k, 61.0)]
      parts.append(Chip('AND', (given.pins['P%d' % k], carry, product)))
      parts.append(Chip('OR', (given.pins['G%d' % k], product, total)))
      parts.append(Wire(total, given.pins['C%d' % (k + 1)]))
      carry = total
    rippled = type(circuit)((*nodes,), (*parts,))
    self.assertEqual(depthOf(rippled, given.outputs), 8.0)
    goal = quest.newGoal()
    run = play(rippled, goal, 0.02, 12.0)
    self.assertFalse(goal.reached)
    self.assertIn('8 chips', goal.words(run))

  def test_wrong_gate(self) -> None:
    """An OR where an XOR is asked for fails at A 1, B 1."""
    quest = SUPER[4]
    given = bench(('A', 'B'), ('Q',), False)
    wrong = _grown(given.circuit, Chip('OR', (given.pins['A'],
                                              given.pins['B'],
                                              given.pins['Q'])))
    goal = quest.newGoal()
    run = play(wrong, goal, 0.02, 3.0)
    self.assertFalse(goal.reached)
    self.assertIn('A 1, B 1', goal.words(run))

  def test_granted(self) -> None:
    """The super quests come after the first eight, and grant the gates
    and chips the solutions after them build with."""
    self.assertEqual(len(MAIN), 8)
    granted = [kind for quest in SUPER for kind in quest.reward]
    for name in ('NOT', 'NAND', 'NOR', 'AND', 'OR', 'XOR', 'FA', 'ADD4',
                 'SR', 'DFF', 'JKFF', 'SRAM'):
      self.assertIn(name, granted)
