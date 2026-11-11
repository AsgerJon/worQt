"""
TestGoals covers the goals, each on a small circuit: a lamp glowing
long enough, too bright starting it again; turning on and off; an
ammeter and a voltmeter reading a part; a lamp glowing on after its
switch opens; current one way only; a touch switch; all of several; a
test bench setting inputs itself; how deep a chip's output reads; how
long each lets the circuit run before it must look again.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.circuits import Ammeter, Capacitor, Circuit, Diode
from worQt.engineering.circuits import Lamp, Led, Node, Resistor, Run
from worQt.engineering.circuits import Source, Switch, Voltmeter, Wire
from worQt.engineering.circuits import Bit, Chip, Probe
from worQt.engineering.quests import Afterglow, All, Clocked, Glow
from worQt.engineering.quests import Measures
from worQt.engineering.quests import OneWay, Tester, Toggles, depthOf
from worQt.engineering.quests import glowOf, table

from . import QuestsTest, play

SQUARE = (Node(0.0, 0.0), Node(0.0, 2.0), Node(2.0, 2.0), Node(2.0, 0.0))


def lit(closed: bool) -> Circuit:
  """4.5 V lighting a lamp made for it through a switch."""
  return Circuit(SQUARE, (Source(1, 0, 4.5, 0.0, 0.0),
                          Switch(1, 2, closed), Lamp(2, 3, 4.5, 0.45),
                          Wire(3, 0)))


class TestGoals(QuestsTest):
  """Tests for the goals."""

  def test_glow_of(self) -> None:
    """A lamp glows by the share of its power, a light emitting diode by
    the share of its current, anything else not at all."""
    run = Run(lit(True))
    self.assertAlmostEqual(glowOf(run, 2), 1.0, 12)
    self.assertEqual(glowOf(run, 0), 0.0)
    run = Run(Circuit(SQUARE, (Source(1, 0, 9.0, 0.0, 0.0),
                               Resistor(1, 2, 699.9), Led(2, 3, 2.0, 0.02),
                               Wire(3, 0))))
    self.assertAlmostEqual(glowOf(run, 2), 0.5, 12)

  def test_glow(self) -> None:
    """A lamp lit is reached once it has glowed for its seconds, not
    before; a dark one never."""
    goal = Glow(2, 0.5, 1.0, math.inf)
    run = play(lit(True), goal, 0.02, 0.9)
    self.assertFalse(goal.reached)
    self.assertIn('so far', goal.words(run))
    goal = Glow(2, 0.5, 1.0, math.inf)
    run = play(lit(True), goal, 0.02, 1.2)
    self.assertTrue(goal.reached)
    self.assertAlmostEqual(run.time, 1.0, 9)
    self.assertEqual(goal.words(run), 'Reached!')
    goal = Glow(2, 0.5, 1.0, math.inf)
    play(lit(False), goal, 0.02, 3.0)
    self.assertFalse(goal.reached)

  def test_too_bright(self) -> None:
    """Over its most, a light emitting diode never reaches the goal, and
    the words say it would burn out."""
    circuit = Circuit(SQUARE, (Source(1, 0, 9.0, 0.0, 0.0),
                               Resistor(1, 2, 100.0), Led(2, 3, 2.0, 0.02),
                               Wire(3, 0)))
    goal = Glow(2, 0.5, 1.0, 1.2)
    run = play(circuit, goal, 0.02, 3.0)
    self.assertFalse(goal.reached)
    self.assertIn('burn out', goal.words(run))

  def test_toggles(self) -> None:
    """A lamp switched on, off and on has turned three times."""
    goal = Toggles(2, 3)
    play(lit(False), goal, 0.02, 2.0, (0.2, 1, True), (0.6, 1, False),
         (1.0, 1, True))
    self.assertTrue(goal.reached)
    goal = Toggles(2, 3)
    play(lit(False), goal, 0.02, 2.0, (0.2, 1, True))
    self.assertFalse(goal.reached)

  def test_measures(self) -> None:
    """An ammeter in series and a voltmeter across a resistor measure it;
    the ammeter alone does not."""
    parts = (Source(1, 0, 4.5, 0.0, 1.5), Ammeter(1, 2),
             Resistor(2, 3, 7.5), Wire(3, 0))
    goal = Measures(2, 1.0)
    play(Circuit(SQUARE, parts), goal, 0.02, 2.0)
    self.assertFalse(goal.reached)
    self.assertEqual(goal.found(Run(Circuit(SQUARE, parts))),
                     (True, False))
    goal = Measures(2, 1.0)
    play(Circuit(SQUARE, (*parts, Voltmeter(2, 3))), goal, 0.02, 2.0)
    self.assertTrue(goal.reached)

  def test_afterglow(self) -> None:
    """With 50000 µF across it, the lamp of 45 Ω glows on at a quarter
    or more for 45 Ω 0.05 F ln 2 = 1.56 s after its switch opens; without,
    it goes dark at once, the words saying how soon."""
    circuit = lit(True)
    held = circuit.withParts(*circuit.parts, Capacitor(2, 3, 0.05))
    goal = Afterglow(2, 1, 0.25, 1.0)
    play(held, goal, 0.02, 3.0, (0.5, 1, False))
    self.assertTrue(goal.reached)
    goal = Afterglow(2, 1, 0.25, 1.0)
    run = play(circuit, goal, 0.02, 3.0, (0.5, 1, False))
    self.assertFalse(goal.reached)
    self.assertIn('faded after', goal.words(run))

  def test_one_way(self) -> None:
    """Behind a diode the current through a load flows one way only;
    turned round, it flows back."""
    nodes = SQUARE

    def wave(part) -> Circuit:
      return Circuit(nodes, (Source(1, 0, 12.0, 50.0, 0.0), part,
                             Resistor(2, 3, 100.0), Wire(3, 0)))

    goal = OneWay(2, 0.002, 0.1)
    play(wave(Diode(1, 2, 0.7)), goal, 0.0002, 0.3)
    self.assertTrue(goal.reached)
    goal = OneWay(2, 0.002, 0.1)
    run = play(wave(Diode(2, 1, 0.7)), goal, 0.0002, 0.3)
    self.assertFalse(goal.reached)
    self.assertTrue(goal.turnedBack)
    self.assertIn('turned back', goal.words(run))
    goal = OneWay(2, 0.002, 0.1)
    play(wave(Wire(1, 2)), goal, 0.02, 2.0)
    self.assertFalse(goal.reached)

  def test_all(self) -> None:
    """All is reached once each goal is."""
    goal = All(Glow(2, 0.5, 0.5, math.inf), Toggles(2, 1))
    play(lit(False), goal, 0.02, 0.3, (0.1, 1, True))
    self.assertFalse(goal.reached)
    play(lit(True), goal, 0.02, 1.0)
    self.assertTrue(goal.reached)

  def test_tester(self) -> None:
    """A test bench of a NOT chip sets A itself, row by row, and passes;
    a wire where the chip should be fails, the words saying where."""
    nodes = (Node(0.0, 0.0), Node(0.0, 2.0), Node(4.0, 2.0))
    steps = table(1, lambda a: (not a,))
    self.assertEqual(steps, (((False,), (True,)), ((True,), (False,))))
    good = Circuit(nodes, (Bit(1, 0, False, 'A'), Chip('NOT', (1, 2)),
                           Probe(2, 0, 'Q')))
    goal = Tester((0,), (2,), steps, 0.1, math.inf)
    play(good, goal, 0.02, 2.0)
    self.assertTrue(goal.reached)
    bad = Circuit(nodes, (Bit(1, 0, False, 'A'), Wire(1, 2),
                          Probe(2, 0, 'Q')))
    goal = Tester((0,), (2,), steps, 0.1, math.inf)
    run = play(bad, goal, 0.02, 2.0)
    self.assertFalse(goal.reached)
    self.assertIn('With A 0: read Q 0, not Q 1', goal.words(run))

  def test_depth(self) -> None:
    """Two NOTs in a row read through two chips; straight, through
    none; round a loop, endlessly."""
    nodes = (Node(0.0, 0.0), Node(0.0, 2.0), Node(2.0, 2.0),
             Node(4.0, 2.0))
    parts = (Bit(1, 0, False, 'A'), Chip('NOT', (1, 2)),
             Chip('NOT', (2, 3)), Probe(3, 0, 'Q'))
    circuit = Circuit(nodes, parts)
    self.assertEqual(depthOf(circuit, (3,)), 2.0)
    straight = Circuit(nodes, (Bit(1, 0, False, 'A'), Wire(1, 3),
                               Probe(3, 0, 'Q')))
    self.assertEqual(depthOf(straight, (2,)), 0.0)
    loop = Circuit(nodes, (Chip('NOT', (2, 3)), Chip('NOT', (3, 2)),
                           Probe(3, 0, 'Q')))
    self.assertTrue(math.isinf(depthOf(loop, (2,))))

  def test_longest(self) -> None:
    """A watching goal lets the circuit run as long as it likes; a test
    bench until a hair past its next look; a clock until a hair past its
    next turn; all of them the least."""
    nodes = (Node(0.0, 0.0), Node(0.0, 2.0), Node(4.0, 2.0))
    circuit = Circuit(nodes, (Bit(1, 0, False, 'A'), Chip('NOT', (1, 2)),
                              Probe(2, 0, 'Q')))
    run = Run(circuit)
    glow = Glow(2, 0.5, 0.5, math.inf)
    self.assertTrue(math.isinf(glow.longest(run)))
    tester = Tester((0,), (2,), table(1, lambda a: (not a,)), 0.1,
                    math.inf)
    self.assertTrue(math.isinf(tester.longest(run)))
    tester.drive(run)
    self.assertAlmostEqual(tester.longest(run), 0.1, 6)
    self.assertGreater(tester.longest(run), 0.1)
    clocked = Clocked(0, 2, (1, 0), False, 2, 0.25)
    clocked.drive(run)
    self.assertAlmostEqual(clocked.longest(run), 0.25, 6)
    run.advance(0.3)
    self.assertAlmostEqual(clocked.longest(run), 0.2, 6)
    self.assertAlmostEqual(All(glow, clocked).longest(run), 0.2, 6)
