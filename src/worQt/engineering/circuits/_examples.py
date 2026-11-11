"""
The examples: small circuits to start from, each with a word on what
to do with it and the speed to watch it at.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ._circuit import Circuit
from ._parts import Ammeter, Capacitor, Coil, Diode, Lamp, Led, Node
from ._parts import Resistor, Source, Switch, Transistor, Voltmeter, Wire


class Example(NamedTuple):
  """
  Example is a small circuit to start from: its 'name', a 'hint' on what
  to do with it, the 'speed' to watch it at, against real time, how
  many seconds to run it before it is shown, 'settle', so it shows
  settled, and how to make it, 'make'.
  """

  name: str
  hint: str
  speed: float
  settle: float
  make: object

  def circuit(self) -> Circuit:
    """The example's circuit, made anew."""
    return self.make()


def _nodes(*points: tuple[float, float]) -> tuple[Node, ...]:
  """Nodes at 'points'."""
  return (*[Node(float(x), float(y)) for x, y in points],)


def charging() -> Circuit:
  """A battery charging a capacitor through a lamp, once its switch is
  closed, a voltmeter across the capacitor: the standard circuit."""
  return Circuit()


def lamps() -> Circuit:
  """A battery of 6 V lighting two lamps of 6 V in series, in the middle,
  and one alone, at the right; an ammeter reads what the battery
  gives."""
  nodes = _nodes((0, 0), (0, 4), (4, 4), (4, 2), (4, 0), (8, 4), (8, 0))
  return Circuit(nodes, (
    Source(1, 0, 6.0, 0.0, 0.0), Ammeter(1, 2), Lamp(2, 3, 6.0, 0.3),
    Lamp(3, 4, 6.0, 0.3), Wire(2, 5), Lamp(5, 6, 6.0, 0.3), Wire(6, 4),
    Wire(4, 0)))


def internal() -> Circuit:
  """A flat battery of 4.5 V with 1.5 Ω inside it, a voltmeter at its
  poles, an ammeter, a load of 7.5 Ω, and a second load to switch in
  beside it."""
  nodes = _nodes((0, 0), (0, 4), (4, 4), (4, 0), (8, 4), (8, 0))
  return Circuit(nodes, (
    Source(1, 0, 4.5, 0.0, 1.5), Voltmeter(1, 0), Ammeter(1, 2),
    Resistor(2, 3, 7.5), Switch(2, 4, False), Resistor(4, 5, 7.5),
    Wire(5, 3), Wire(3, 0)))


def oscillating() -> Circuit:
  """A capacitor of 100 µF charged by a battery of 5 V, to be switched
  onto a coil of 0.1 H with 0.5 Ω: a circuit swinging at 50 Hz,
  dying away."""
  nodes = _nodes((0, 0), (0, 4), (4, 4), (4, 0), (8, 4), (8, 2), (8, 0))
  return Circuit(nodes, (
    Source(1, 0, 5.0, 0.0, 0.0), Switch(1, 2, True),
    Capacitor(2, 3, 100e-6), Wire(3, 0), Switch(2, 4, False),
    Coil(4, 5, 0.1), Resistor(5, 6, 0.5), Wire(6, 3)))


def rectifier() -> Circuit:
  """12 V at 50 Hz through a diode to a load of 100 Ω, a voltmeter across
  it, and a capacitor of 1000 µF to switch in to smooth it."""
  nodes = _nodes((0, 0), (0, 4), (4, 4), (4, 2), (4, 0), (8, 4), (8, 0))
  return Circuit(nodes, (
    Source(1, 0, 12.0, 50.0, 0.0), Diode(1, 2, 0.7), Switch(2, 3, False),
    Capacitor(3, 4, 1e-3), Wire(2, 5), Resistor(5, 6, 100.0),
    Voltmeter(5, 6), Wire(6, 4), Wire(4, 0)))


def switching() -> Circuit:
  """A transistor switching a light emitting diode: 9 V; closing the
  switch sends a small current into the base through 10 kΩ, an ammeter
  reading it, and lets a far greater one through 330 Ω and the diode
  into the collector."""
  nodes = _nodes((0, 0), (0, 6), (4, 6), (8, 6), (8, 4), (8, 2), (8, 0),
                 (6, 1), (4, 4), (4, 1))
  return Circuit(nodes, (
    Source(1, 0, 9.0, 0.0, 0.0), Wire(1, 2), Wire(2, 3),
    Resistor(3, 4, 330.0), Led(4, 5, 2.0, 0.02),
    Transistor(5, 6, 7, 100.0), Wire(6, 0), Switch(2, 8, False),
    Resistor(8, 9, 10000.0), Ammeter(9, 7)))


def blinker() -> Circuit:
  """Two transistors blinking two light emitting diodes in turn, an
  astable multivibrator: each turned off by the capacitor from the
  other's collector until its base, charging through 47 kΩ, reaches
  0.7 V again, a little under a third of a second with 10 µF."""
  nodes = _nodes(
    (-3, 0), (-3, 10), (1, 10), (3, 10), (9, 10), (11, 10),
    (1, 8), (1, 6), (1, 2), (11, 8), (11, 6), (11, 2),
    (3, 4), (9, 4), (1, 0), (11, 0))
  vcc, ground = 1, 0
  return Circuit(nodes, (
    Source(vcc, ground, 9.0, 0.0, 0.0), Wire(vcc, 2), Wire(2, 3),
    Wire(3, 4), Wire(4, 5),
    Resistor(2, 6, 470.0), Led(6, 7, 2.0, 0.02),
    Resistor(5, 9, 470.0), Led(9, 10, 2.0, 0.02),
    Resistor(3, 12, 47000.0), Resistor(4, 13, 47000.0),
    Transistor(7, 8, 12, 100.0), Transistor(10, 11, 13, 100.0),
    Capacitor(7, 13, 10e-6), Capacitor(10, 12, 10e-6),
    Wire(8, 14), Wire(11, 15), Wire(14, ground), Wire(15, 14)))


def amplifier() -> Circuit:
  """A transistor amplifying 0.2 V at 1 kHz: biased by 47 kΩ and 10 kΩ
  from 9 V, 2.2 kΩ to its collector, 470 Ω from its emitter, the input
  and the output each through 10 µF, the output across 10 kΩ; its gain
  about the collector's resistance over the emitter's."""
  nodes = _nodes((0, 0), (0, 3), (3, 3), (6, 3), (6, 8), (6, 0), (8, 4),
                 (8, 2), (8, 8), (8, 0), (10, 4), (10, 0), (14, 0),
                 (14, 8))
  return Circuit(nodes, (
    Source(13, 12, 9.0, 0.0, 0.0), Source(1, 0, 0.2, 1000.0, 0.0),
    Voltmeter(1, 0), Capacitor(1, 2, 10e-6), Wire(2, 3),
    Resistor(4, 3, 47000.0), Resistor(3, 5, 10000.0),
    Resistor(8, 6, 2200.0), Transistor(6, 7, 3, 100.0),
    Resistor(7, 9, 470.0), Capacitor(6, 10, 10e-6),
    Resistor(10, 11, 10000.0), Voltmeter(10, 11),
    Wire(13, 8), Wire(8, 4), Wire(0, 5), Wire(5, 9), Wire(9, 11),
    Wire(11, 12)))


EXAMPLES = (
  Example('Charging a capacitor',
          'Close S1: the lamp flashes and fades as the capacitor charges, '
          'τ = RC.', 1.0, 0.0, charging),
  Example('Lamps in series and parallel',
          'The two lamps in series share the 6 V and glow faintly; the '
          'lamp alone gets all 6 V.', 1.0, 0.0, lamps),
  Example('Internal resistance',
          'Close S1: the battery gives more current, and its voltage at '
          'the poles drops by R I inside it.', 1.0, 0.0, internal),
  Example('Oscillating circuit',
          'Open S1, then close S2: the capacitor swings its charge back '
          'and forth through the coil at 50 Hz.', 0.01, 0.0,
          oscillating),
  Example('Rectifier',
          'The diode lets only the upper halves through; close S1 to '
          'smooth them with the capacitor.', 0.01, 0.0, rectifier),
  Example('Transistor switch',
          'Close S1: a base current under a milliampere lets 20 mA '
          'through the light emitting diode.', 1.0, 0.0, switching),
  Example('Blinker',
          'Two transistors take turns, each switching the other off for a '
          'while through its capacitor.', 1.0, 0.0, blinker),
  Example('Amplifier',
          'The 0.2 V in comes out about four times as large, turned the '
          'other way round.', 0.001, 1.0, amplifier),
)
