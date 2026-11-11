"""
The quests: the line of small puzzles, each a circuit begun, a goal to
reach by adding parts, and the parts it unlocks; then the super quests,
logic on a test bench, each granting what it built as a chip; then the
computer quests, buses up to a little computer and a program for it;
then the microprocessor quests, after Intel's 4004, the final boss.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ..circuits import Ammeter, Capacitor, Circuit, Coil, Diode, Lamp, Led
from ..circuits import Node, Resistor, Source, Switch, Transistor
from ..circuits import Voltmeter, Wire
from ._goals import Afterglow, All, Glow, Goal, Measures, OneWay, Tester
from ._goals import Toggles, Touch
from ._super import SUPERS, SuperQuest, bench
from ._computer import COMPUTERS, ComputerQuest
from ._micro import MICROS

#  The parts every player has from the start
STARTING = (Wire, Source, Lamp)


class Quest(NamedTuple):
  """
  Quest is a small puzzle: its 'name'; its 'brief', the goal in words
  and a nudge; the 'speed' to watch it at, against real time; how to
  make its circuit, 'make', its parts fixed, and its goal, 'goal', each
  anew; the kinds of part reaching it unlocks, 'reward'; one way to
  solve it, 'solution', adding parts to its circuit, switches to be
  worked as the brief says; and how many of its last parts are 'loose',
  the player's to change, the rest fixed.
  """

  name: str
  brief: str
  speed: float
  make: object
  goal: object
  reward: tuple
  solution: object
  loose: int = 0

  def circuit(self) -> Circuit:
    """The quest's circuit as it begins, made anew."""
    return self.make()

  def newGoal(self) -> Goal:
    """The quest's goal, made anew, nothing watched yet."""
    return self.goal()


def _nodes(*points: tuple[float, float]) -> tuple[Node, ...]:
  """Nodes at 'points'."""
  return (*[Node(float(x), float(y)) for x, y in points],)


def _grown(circuit: Circuit, points: tuple, *parts) -> Circuit:
  """'circuit' with nodes at 'points' and 'parts' added."""
  return Circuit((*circuit.nodes, *_nodes(*points)),
                 (*circuit.parts, *parts))


_APART = ((0, 0), (0, 4), (6, 0), (6, 4))


def _firstLight() -> Circuit:
  """A battery of 4.5 V and a lamp made for it, apart."""
  return Circuit(_nodes(*_APART), (Source(1, 0, 4.5, 0.0, 0.0),
                                   Lamp(3, 2, 4.5, 0.45)))


def _onAndOff() -> Circuit:
  """A battery of 4.5 V and a lamp, joined at the bottom only."""
  return Circuit(_nodes(*_APART), (Source(1, 0, 4.5, 0.0, 0.0),
                                   Lamp(3, 2, 4.5, 0.45), Wire(0, 2)))


def _notTooBright() -> Circuit:
  """A battery of 9 V and a red light emitting diode, joined at the
  bottom only."""
  return Circuit(_nodes(*_APART), (Source(1, 0, 9.0, 0.0, 0.0),
                                   Led(3, 2, 2.0, 0.02), Wire(0, 2)))


def _measureIt() -> Circuit:
  """A flat battery, 1.5 Ω inside it, and a resistor of 7.5 Ω, joined at
  the bottom only."""
  return Circuit(_nodes(*_APART), (Source(1, 0, 4.5, 0.0, 1.5),
                                   Resistor(3, 2, 7.5), Wire(0, 2)))


def _afterglow() -> Circuit:
  """A battery of 6 V lighting a lamp through a switch, closed."""
  nodes = _nodes((0, 0), (0, 4), (3, 4), (6, 4), (6, 0))
  return Circuit(nodes, (Source(1, 0, 6.0, 0.0, 0.0), Switch(1, 2, True),
                         Wire(2, 3), Lamp(3, 4, 6.0, 0.3), Wire(4, 0)))


def _oneWay() -> Circuit:
  """12 V alternating at 50 Hz, a gap, and a load of 100 Ω, a voltmeter
  across it."""
  nodes = _nodes((0, 0), (0, 4), (6, 4), (6, 0))
  return Circuit(nodes, (Source(1, 0, 12.0, 50.0, 0.0),
                         Resistor(2, 3, 100.0), Voltmeter(2, 3),
                         Wire(3, 0)))


def _touch() -> Circuit:
  """9 V; a light emitting diode behind 330 Ω, its cathode free; a
  finger, a switch and a megaohm, its end free; a free node at the
  minus pole."""
  nodes = _nodes((0, 0), (0, 8), (3, 8), (8, 8), (8, 6), (8, 4), (3, 6),
                 (3, 4), (8, 0))
  return Circuit(nodes, (
    Source(1, 0, 9.0, 0.0, 0.0), Wire(1, 2), Wire(2, 3),
    Resistor(3, 4, 330.0), Led(4, 5, 2.0, 0.02), Switch(2, 6, False),
    Resistor(6, 7, 1e6), Wire(0, 8)))


def _blinker() -> Circuit:
  """9 V; two light emitting diodes, each behind 470 Ω, their cathodes
  free; nodes free along the plus and the minus."""
  nodes = _nodes((-3, 0), (-3, 10), (1, 10), (3, 10), (9, 10), (11, 10),
                 (1, 8), (1, 6), (11, 8), (11, 6), (1, 0), (11, 0))
  return Circuit(nodes, (
    Source(1, 0, 9.0, 0.0, 0.0), Wire(1, 2), Wire(2, 3), Wire(3, 4),
    Wire(4, 5), Resistor(2, 6, 470.0), Led(6, 7, 2.0, 0.02),
    Resistor(5, 8, 470.0), Led(8, 9, 2.0, 0.02), Wire(0, 10),
    Wire(10, 11)))


def _solvedTouch(circuit: Circuit) -> Circuit:
  """Two transistors, a Darlington pair: the first's emitter feeding the
  second's base, a hundred times a hundred."""
  return _grown(circuit, ((5, 5), (5, 3)),
                Transistor(9, 10, 7, 100.0), Transistor(5, 8, 10, 100.0),
                Wire(9, 5))


def _solvedBlinker(circuit: Circuit) -> Circuit:
  """An astable multivibrator: two transistors, each base fed through
  47 kΩ, each collector to the other's base through 10 µF."""
  return _grown(circuit, ((1, 2), (3, 4), (11, 2), (9, 4)),
                Transistor(7, 12, 13, 100.0), Transistor(9, 14, 15, 100.0),
                Resistor(3, 13, 47000.0), Resistor(4, 15, 47000.0),
                Capacitor(7, 15, 10e-6), Capacitor(9, 13, 10e-6),
                Wire(12, 10), Wire(14, 11))


MAIN = (
  Quest(
    'First light',
    'Light the lamp: join it to the battery with wires. Select two '
    'nodes, Ctrl and a click, then Wire to join them.',
    1.0, _firstLight, lambda: Glow(1, 0.5, 1.0, math.inf), (Switch,),
    lambda c: c.withParts(*c.parts, Wire(1, 3), Wire(0, 2))),
  Quest(
    'On and off',
    'Turn the lamp on, off and on again without pulling wires out: put '
    'a switch in the gap and click it Closed and Open in the panel.',
    1.0, _onAndOff, lambda: Toggles(1, 3), (Resistor,),
    lambda c: c.withParts(*c.parts, Switch(1, 3, False))),
  Quest(
    'Not too bright',
    'Light the diode from 9 V without burning it out: it keeps 2 V and '
    'is made for 20 mA. A resistor takes the rest, R = U / I; set it in '
    'the panel.',
    1.0, _notTooBright, lambda: Glow(1, 0.5, 2.0, 1.2),
    (Ammeter, Voltmeter),
    lambda c: c.withParts(*c.parts, Resistor(1, 3, 350.0))),
  Quest(
    'Measure it',
    'Measure R1: an ammeter in series reads the current through it, a '
    'voltmeter across it the voltage. Then R = U / I.',
    1.0, _measureIt, lambda: Measures(1, 1.0), (Capacitor,),
    lambda c: c.withParts(*c.parts, Ammeter(1, 3), Voltmeter(3, 2))),
  Quest(
    'Afterglow',
    'Keep the lamp glowing at a quarter or more for a second after S1 '
    'is opened. A capacitor holds charge, Q = C U; how large must it '
    'be?',
    1.0, _afterglow, lambda: Afterglow(3, 1, 0.25, 1.0), (Diode,),
    lambda c: c.withParts(*c.parts, Capacitor(3, 4, 0.02))),
  Quest(
    'One way',
    'The source alternates, 12 V at 50 Hz. Make the current through R1 '
    'flow one way only, top to bottom, and plenty of it.',
    0.01, _oneWay, lambda: OneWay(1, 0.002, 0.1), (Transistor,),
    lambda c: c.withParts(*c.parts, Diode(1, 2, 0.7))),
  Quest(
    'Touch switch',
    'S1 and R2 are a finger touching two wires: a megaohm lets only '
    'microamperes through. Make the diode glow while S1 is closed and go '
    'dark when it opens. One transistor gives a hundred times the '
    'current; is that enough?',
    1.0, _touch, lambda: Touch(4, 5, 0.5), (Led,), _solvedTouch),
  Quest(
    'Blinker',
    'Make both diodes blink by themselves, three times each: two '
    'transistors, each switching the other off for a while through a '
    'capacitor.',
    1.0, _blinker, lambda: All(Toggles(6, 6), Toggles(8, 6)), (Coil,),
    _solvedBlinker),
)


def _superQuest(making: SuperQuest) -> Quest:
  """The quest a super quest's makings make: its bench, fixed, its test
  bench the goal."""
  given = bench(making.inputs, making.outputs, making.supply)
  return Quest(
    making.name, making.brief, 1.0, lambda: given.circuit,
    lambda: Tester(given.inputs, given.outputs, making.steps, making.wait,
                   making.most),
    making.reward, lambda circuit: making.solve(given))


def _computerQuest(making: ComputerQuest) -> Quest:
  """The quest a computer quest's makings make: its bench, fixed but its
  loose last parts."""
  given = making.bench
  return Quest(
    making.name, making.brief, 1.0, lambda: given.circuit,
    lambda: making.goal(given), making.reward,
    lambda circuit: making.solve(given), making.loose)


#  The super quests, after the quests: logic, each granting what it built
SUPER = (*map(_superQuest, SUPERS),)
#  The computer quests, after them: buses up to a computer
COMPUTER = (*map(_computerQuest, COMPUTERS),)
#  The microprocessor quests, last: after the 4004, the final boss
MICRO = (*map(_computerQuest, MICROS),)
QUESTS = (*MAIN, *SUPER, *COMPUTER, *MICRO)
