"""
The parts of an electric circuit: its 'Node's, where parts join, and
the parts between them: 'Wire', 'Source', 'Resistor', 'Lamp',
'Capacitor', 'Coil', 'Switch', 'Ammeter', 'Voltmeter', 'Diode', 'Led'
and 'Transistor', this last joining three; the logic parts 'Bit',
'Probe' and 'Clock', and those of a bus of four bits, 'BusIn' and
'BusProbe'; 'ends' and 'withEnds' give and change the nodes a part, or
a chip, joins.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ._chips import Chip


class Node(NamedTuple):
  """
  Node is where parts of a circuit join, at 'x' and 'y' on the grid of
  the drawing, y up; only what is joined to what matters to the
  circuit, never how far apart.
  """

  x: float
  y: float


class Wire(NamedTuple):
  """
  Wire joins the node of index 'first' to the node of index 'second'
  without resistance, so both are at one voltage.
  """

  first: int
  second: int

  letter = 'W'


class Source(NamedTuple):
  """
  Source drives a current, a battery or a power supply, its plus pole at
  the node of index 'first' and its minus pole at 'second': 'voltage' V
  from minus to plus, steady for a 'frequency' of nought, else
  alternating, 'voltage' its peak, so 'voltage' / sqrt(2) its effective
  voltage, starting from nought; 'resistance' Ω is its internal
  resistance, nought for an ideal source.
  """

  first: int
  second: int
  voltage: float
  frequency: float
  resistance: float

  letter = 'E'


class Resistor(NamedTuple):
  """
  Resistor is a resistance of 'resistance' Ω from the node of index
  'first' to the node of index 'second': the current through it is the
  voltage across it over its resistance, Ohm's law.
  """

  first: int
  second: int
  resistance: float

  letter = 'R'


class Lamp(NamedTuple):
  """
  Lamp is a light bulb from the node of index 'first' to the node of
  index 'second', made for 'voltage' V at which it takes 'power' W: a
  resistance of voltage² / power, glowing as much as the power it
  takes, fully at what it is made for.
  """

  first: int
  second: int
  voltage: float
  power: float

  letter = 'H'

  @property
  def resistance(self) -> float:
    """The lamp's resistance, in Ω: voltage² / power."""
    return self.voltage * self.voltage / self.power


class Capacitor(NamedTuple):
  """
  Capacitor is a capacitance of 'capacitance' F from the node of index
  'first' to the node of index 'second': it holds a charge of its
  capacitance times the voltage across it, so the current through it is
  how fast that charge changes.
  """

  first: int
  second: int
  capacitance: float

  letter = 'C'


class Coil(NamedTuple):
  """
  Coil is an inductance of 'inductance' H from the node of index
  'first' to the node of index 'second', without resistance: the
  voltage across it is its inductance times how fast the current
  through it changes.
  """

  first: int
  second: int
  inductance: float

  letter = 'L'


class Switch(NamedTuple):
  """
  Switch joins the node of index 'first' to the node of index 'second'
  as a wire does when 'closed', and not at all when open.
  """

  first: int
  second: int
  closed: bool

  letter = 'S'


class Ammeter(NamedTuple):
  """
  Ammeter reads the current through it, entering at its plus pole, the
  node of index 'first', and leaving at its minus pole, 'second'; it is
  ideal, a wire.
  """

  first: int
  second: int

  letter = 'A'


class Voltmeter(NamedTuple):
  """
  Voltmeter reads the voltage of its plus pole, the node of index
  'first', over its minus pole, 'second'; it is ideal, taking no
  current.
  """

  first: int
  second: int

  letter = 'V'


class Diode(NamedTuple):
  """
  Diode lets current through one way only, from its anode, the node of
  index 'first', to its cathode, 'second', once the voltage across it
  reaches 'voltage' V, about 0.7 V for silicon, which it then keeps;
  the other way it is open.
  """

  first: int
  second: int
  voltage: float

  letter = 'D'


class Led(NamedTuple):
  """
  Led is a light emitting diode from its anode, the node of index
  'first', to its cathode, 'second': a diode letting current through at
  'voltage' V, about 2 V for a red one, glowing fully at 'current' A,
  as it is made for.
  """

  first: int
  second: int
  voltage: float
  current: float

  letter = 'LED'


class Transistor(NamedTuple):
  """
  Transistor is an NPN transistor: its collector the node of index
  'first', its emitter 'second' and its base 'base'. Base to emitter it
  is a diode of 0.7 V; a current into its base lets 'gain' times as
  much into its collector, at most so much as the circuit around it
  gives when it is fully on, 0.2 V from collector to emitter. Without
  a base current it is off, letting nothing through.
  """

  first: int
  second: int
  base: int
  gain: float

  letter = 'Q'


class Bit(NamedTuple):
  """
  Bit is a logic input, 'name': a source of 5 V from its pole at the
  node of index 'first' over its minus at 'second' when 'high', of
  nought when low.
  """

  first: int
  second: int
  high: bool
  name: str

  letter = 'IN'


class Probe(NamedTuple):
  """
  Probe is a logic output, 'name': it reads the node of index 'first'
  over 'second', high above 2.5 V, taking no current, as a voltmeter.
  """

  first: int
  second: int
  name: str

  letter = 'OUT'


class Clock(NamedTuple):
  """
  Clock is a source ticking between 5 V and nought, 'frequency' times a
  second, from its pole at the node of index 'first' over its minus at
  'second': high the first half of each tick, low the second.
  """

  first: int
  second: int
  frequency: float

  letter = 'CLK'


class BusIn(NamedTuple):
  """
  BusIn is a logic input of four bits, 'name': a number, 'value', from
  nought to fifteen, on the bus at the node of index 'first', each bit a
  source of 5 V or nought over the node of index 'second'.
  """

  first: int
  second: int
  value: int
  name: str

  letter = 'BIN'


class BusProbe(NamedTuple):
  """
  BusProbe is a logic output of four bits, 'name': it reads the number
  on the bus at the node of index 'first', each bit over the node of
  index 'second', taking no current.
  """

  first: int
  second: int
  name: str

  letter = 'BOUT'


def ends(part: tuple) -> tuple[int, ...]:
  """The 'ends' function returns the nodes 'part' joins: its first and
  second, a transistor's base too, a chip its pins."""
  if isinstance(part, Chip):
    return (*part.pins,)
  return (*part[:3],) if isinstance(part, Transistor) else (*part[:2],)


def withEnds(part: tuple, nodes: tuple) -> tuple:
  """The 'withEnds' function returns 'part' joining 'nodes' instead, as
  many as it joins."""
  if isinstance(part, Chip):
    return Chip(part.kind, (*nodes,), part.contents)
  count = len(ends(part))
  return type(part)(*nodes, *part[count:])
