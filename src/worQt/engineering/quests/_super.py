"""
The super quests: logic built on a test bench, from transistors up,
each granting what was built as a chip of its own.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ..circuits import Bit, Chip, Circuit, Clock, Node, Probe, Resistor
from ..circuits import SPECS, Source, Transistor, Wire
from ._goals import table

#  The supply a bench of transistors has, in V
SUPPLY = 5.0


class Bench(NamedTuple):
  """
  Bench is a test bench: its 'circuit', the logic inputs down a ground
  bus on the left and the probes down one on the right, and a supply of
  5 V along the top when it has one; its named nodes, 'pins': each
  input's and output's by its name, the ground taps 'G0' to 'G2' and
  the supply's '+0' to '+2'; and the parts of its 'inputs' and its
  'outputs', in their order.
  """

  circuit: Circuit
  pins: dict
  inputs: tuple
  outputs: tuple


def bench(inputs: tuple[str, ...], outputs: tuple[str, ...],
          supply: bool) -> Bench:
  """The 'bench' function returns a test bench of the logic inputs named
  'inputs', the probes named 'outputs', and a supply if 'supply'."""
  rows = max(len(inputs), len(outputs))
  top = 2 * rows + 2
  nodes, parts, pins = [], [], {}

  def node(x: float, y: float) -> int:
    nodes.append(Node(float(x), float(y)))
    return len(nodes) - 1

  left, right = node(-6, 0), node(14, 0)
  taps = [node(x, 0) for x in (0, 4, 8)]
  if supply:
    minus, plus = node(-8, 0), node(-8, top)
    rails = [node(x, top) for x in (0, 4, 8)]
    parts.append(Source(plus, minus, SUPPLY, 0.0, 0.0))
    parts.append(Wire(minus, left))
    for a, b in zip([plus, *rails[:-1]], rails):
      parts.append(Wire(a, b))
    pins.update({'+%d' % k: rail for k, rail in enumerate(rails)})
  for a, b in zip([left, *taps], [*taps, right]):
    parts.append(Wire(a, b))
  pins.update({'G%d' % k: tap for k, tap in enumerate(taps)})
  inputsAt, outputsAt = [], []
  below = left
  for k, name in enumerate(inputs):
    y = 2 * (len(inputs) - k)
    minus = node(-6, y)
    pins[name] = node(-4, y)
    parts.append(Wire(below, minus))
    below = minus
    inputsAt.append(len(parts))
    parts.append(Bit(pins[name], minus, False, name))
  below = right
  for k, name in enumerate(outputs):
    y = 2 * (len(outputs) - k)
    minus = node(14, y)
    pins[name] = node(12, y)
    parts.append(Wire(below, minus))
    below = minus
    outputsAt.append(len(parts))
    parts.append(Probe(pins[name], minus, name))
  if not supply:
    order = [*inputsAt, *[i for i in range(len(parts))
                          if i not in inputsAt]]
    moved = {old: new for new, old in enumerate(order)}
    parts = [parts[i] for i in order]
    inputsAt = [moved[i] for i in inputsAt]
    outputsAt = [moved[i] for i in outputsAt]
  return Bench(Circuit((*nodes,), (*parts,)), pins, (*inputsAt,),
               (*outputsAt,))


class _Builder:
  """Builds a solution on a bench: parts added, new nodes far off."""

  def __init__(self, given: Bench) -> None:
    self.pins = given.pins
    self.nodes = [*given.circuit.nodes]
    self.parts = [*given.circuit.parts]

  def node(self, ) -> int:
    """A new node, apart from the rest."""
    count = len(self.nodes)
    self.nodes.append(Node(40.0 + count % 20, 40.0 + count // 20))
    return count

  def at(self, name: object) -> int:
    """The node of 'name', a bench's pin, or a node already."""
    return self.pins[name] if isinstance(name, str) else name

  def add(self, part: tuple) -> None:
    """Adds 'part'."""
    self.parts.append(part)

  def chip(self, kind: str, *inputs: object) -> int | tuple:
    """Adds a chip of 'kind' reading 'inputs', its outputs on new nodes:
    returns the one, or all of them."""
    outputs = [self.node() for _ in range(_outputs(kind))]
    pins = (*[self.at(name) for name in inputs], *outputs)
    self.parts.append(Chip(kind, pins))
    return outputs[0] if len(outputs) == 1 else (*outputs,)

  def wire(self, a: object, b: object) -> None:
    """Joins 'a' and 'b' by a wire."""
    self.parts.append(Wire(self.at(a), self.at(b)))

  def circuit(self, ) -> Circuit:
    """The circuit built."""
    return Circuit((*self.nodes,), (*self.parts,))


def _outputs(kind: str) -> int:
  """How many output ports a chip of 'kind' has."""
  return len(SPECS[kind].outs)


def _switch(build: _Builder, inner: object, base: object) -> int:
  """A transistor fed into its base from 'base' through 10 kΩ, its
  collector at 'inner'; returns its emitter's node, new."""
  joint, emitter = build.node(), build.node()
  build.add(Resistor(build.at(base), joint, 10000.0))
  build.add(Transistor(build.at(inner), emitter, joint, 100.0))
  return emitter


def _notOf(given: Bench) -> Circuit:
  """An inverter: a transistor pulling Q down, 1 kΩ up to the supply."""
  build = _Builder(given)
  build.add(Resistor(build.at('+1'), build.at('Q'), 1000.0))
  build.wire(_switch(build, 'Q', 'A'), 'G1')
  return build.circuit()


def _nandOf(given: Bench) -> Circuit:
  """Two transistors in series pulling Q down."""
  build = _Builder(given)
  build.add(Resistor(build.at('+1'), build.at('Q'), 1000.0))
  middle = _switch(build, 'Q', 'A')
  build.wire(_switch(build, middle, 'B'), 'G1')
  return build.circuit()


def _norOf(given: Bench) -> Circuit:
  """Two transistors side by side pulling Q down."""
  build = _Builder(given)
  build.add(Resistor(build.at('+1'), build.at('Q'), 1000.0))
  build.wire(_switch(build, 'Q', 'A'), 'G1')
  build.wire(_switch(build, 'Q', 'B'), 'G1')
  return build.circuit()


def _andOrOf(given: Bench) -> Circuit:
  """AND as NOT NAND, OR as NOT NOR."""
  build = _Builder(given)
  build.wire(build.chip('NOT', build.chip('NAND', 'A', 'B')), 'X')
  build.wire(build.chip('NOT', build.chip('NOR', 'A', 'B')), 'Y')
  return build.circuit()


def _xorOf(given: Bench) -> Circuit:
  """XOR of four NANDs."""
  build = _Builder(given)
  both = build.chip('NAND', 'A', 'B')
  left = build.chip('NAND', 'A', both)
  right = build.chip('NAND', 'B', both)
  build.wire(build.chip('NAND', left, right), 'Q')
  return build.circuit()


def _adderOf(given: Bench) -> Circuit:
  """A full adder: two XORs for the sum, two ANDs and an OR for the
  carry."""
  build = _Builder(given)
  half = build.chip('XOR', 'A', 'B')
  build.wire(build.chip('XOR', half, 'Ci'), 'S')
  first = build.chip('AND', 'A', 'B')
  second = build.chip('AND', half, 'Ci')
  build.wire(build.chip('OR', first, second), 'Co')
  return build.circuit()


def _lookAheadOf(given: Bench) -> Circuit:
  """The carries of four bits looked ahead, each a sum of products, no
  deeper than six gates."""
  build = _Builder(given)
  ch = build.chip
  c1 = ch('OR', 'G0', ch('AND', 'P0', 'C0'))
  p10 = ch('AND', 'P1', 'P0')
  c2 = ch('OR', 'G1', ch('OR', ch('AND', 'P1', 'G0'),
                         ch('AND', p10, 'C0')))
  p21 = ch('AND', 'P2', 'P1')
  p210 = ch('AND', p21, 'P0')
  c3 = ch('OR', ch('OR', 'G2', ch('AND', 'P2', 'G1')),
          ch('OR', ch('AND', p21, 'G0'), ch('AND', p210, 'C0')))
  p32 = ch('AND', 'P3', 'P2')
  p321 = ch('AND', p32, 'P1')
  p3210 = ch('AND', p32, p10)
  c4 = ch('OR', ch('OR', ch('OR', 'G3', ch('AND', 'P3', 'G2')),
                   ch('OR', ch('AND', p32, 'G1'), ch('AND', p321, 'G0'))),
          ch('AND', p3210, 'C0'))
  for node, name in zip((c1, c2, c3, c4), ('C1', 'C2', 'C3', 'C4')):
    build.wire(node, name)
  return build.circuit()


def _latchOf(given: Bench) -> Circuit:
  """An SR latch of two NORs crossed."""
  build = _Builder(given)
  q, bar = build.node(), build.node()
  build.add(Chip('NOR', (build.at('R'), bar, q)))
  build.add(Chip('NOR', (build.at('S'), q, bar)))
  build.wire(q, 'Q')
  return build.circuit()


def _flipOf(given: Bench) -> Circuit:
  """A D flip-flop: a master latch open while the clock is low, a slave
  open while it is high, each an SR latch behind two ANDs."""
  build = _Builder(given)
  ch = build.chip
  low = ch('NOT', 'C')
  master, _ = ch('SR', ch('AND', 'D', low), ch('AND', ch('NOT', 'D'),
                                               low))
  inverse = ch('NOT', master)
  slave, _ = ch('SR', ch('AND', master, 'C'), ch('AND', inverse, 'C'))
  build.wire(slave, 'Q')
  return build.circuit()


def _jkOf(given: Bench) -> Circuit:
  """A JK flip-flop: a D flip-flop fed J and not Q, or not K and Q."""
  build = _Builder(given)
  ch = build.chip
  d = build.node()
  q, bar = ch('DFF', d, 'C')
  feed = ch('OR', ch('AND', 'J', bar), ch('AND', ch('NOT', 'K'), q))
  build.wire(feed, d)
  build.wire(q, 'Q')
  return build.circuit()


def _memoryOf(given: Bench) -> Circuit:
  """Four bits of memory: four D flip-flops, each clocked by WE where the
  address picks it, read back through ANDs and ORs."""
  build = _Builder(given)
  ch = build.chip
  low0, low1 = ch('NOT', 'A0'), ch('NOT', 'A1')
  picks = (ch('AND', low0, low1), ch('AND', 'A0', low1),
           ch('AND', low0, 'A1'), ch('AND', 'A0', 'A1'))
  read = []
  for pick in picks:
    q, _ = ch('DFF', 'D', ch('AND', pick, 'WE'))
    read.append(ch('AND', q, pick))
  build.wire(ch('OR', ch('OR', read[0], read[1]),
                ch('OR', read[2], read[3])), 'Q')
  return build.circuit()


def _steps(*rows: tuple) -> tuple:
  """Steps of a sequence: each row its input levels, 1 and 0, and the
  outputs then, or 'None'."""
  out = []
  for levels, expected in rows:
    wanted = (*[bool(bit) for bit in levels],)
    if expected is not None:
      expected = (*[bool(bit) for bit in expected],)
    out.append((wanted, expected))
  return (*out,)


def _write(address: int, bit: int) -> tuple:
  """The steps writing 'bit' at 'address': set, WE up, WE down."""
  a0, a1 = address & 1, address >> 1
  return (((a0, a1, bit, 0), None), ((a0, a1, bit, 1), None),
          ((a0, a1, bit, 0), None))


def _read(address: int, bit: int) -> tuple:
  """The step reading 'bit' at 'address'."""
  return (((address & 1, address >> 1, 0, 0), (bit,)),)


def _memorySteps() -> tuple:
  """Writing a pattern and reading it back, then the opposite."""
  rows = []
  for pattern in ((1, 0, 1, 1), (0, 1, 0, 0)):
    for address, bit in enumerate(pattern):
      rows += [*_write(address, bit)]
    for address, bit in enumerate(pattern):
      rows += [*_read(address, bit)]
  return _steps(*rows)


class SuperQuest(NamedTuple):
  """
  SuperQuest is a super quest's makings: its name, brief, the names of
  its bench's inputs and outputs, whether it has a supply, its steps,
  how long each waits, how deep it may be, its reward and its
  solution.
  """

  name: str
  brief: str
  inputs: tuple
  outputs: tuple
  supply: bool
  steps: tuple
  wait: float
  most: float
  reward: tuple
  solve: object


SUPERS = (
  SuperQuest(
    'NOT gate',
    'Build an inverter from a transistor: Q high when A is low, low when '
    'A is high. A transistor pulls Q down to ground; a resistor up to '
    'the supply lifts it when the transistor is off. Feed the base '
    'through a resistor. The bench tests it itself.',
    ('A',), ('Q',), True, table(1, lambda a: (not a,)), 0.25, math.inf,
    ('NOT', Bit, Probe), _notOf),
  SuperQuest(
    'NAND gate',
    'Build a NAND from transistors: Q low only when A and B both are '
    'high. Two transistors in series pull Q down only when both are on.',
    ('A', 'B'), ('Q',), True, table(2, lambda a, b: (not (a and b),)),
    0.25, math.inf, ('NAND',), _nandOf),
  SuperQuest(
    'NOR gate',
    'Build a NOR from transistors: Q high only when A and B both are '
    'low. Two transistors side by side pull Q down when either is on.',
    ('A', 'B'), ('Q',), True, table(2, lambda a, b: (not (a or b),)),
    0.25, math.inf, ('NOR',), _norOf),
  SuperQuest(
    'AND and OR',
    'With your gates as chips: X = A AND B, Y = A OR B. A NOT after a '
    'NAND is an AND.',
    ('A', 'B'), ('X', 'Y'), False,
    table(2, lambda a, b: (a and b, a or b)), 0.25, math.inf,
    ('AND', 'OR'), _andOrOf),
  SuperQuest(
    'XOR gate',
    'Q high when A and B differ. Four NANDs will do it.',
    ('A', 'B'), ('Q',), False, table(2, lambda a, b: (a != b,)), 0.25,
    math.inf, ('XOR',), _xorOf),
  SuperQuest(
    'Full adder',
    'Add A, B and the carry in Ci: S the sum bit, Co the carry out. S is '
    'odd parity, Co high when two or more are.',
    ('A', 'B', 'Ci'), ('S', 'Co'), False,
    table(3, lambda a, b, c: ((a + b + c) % 2 == 1, a + b + c >= 2)),
    0.2, math.inf, ('FA',), _adderOf),
  SuperQuest(
    'Look-ahead carry',
    'Each bit of a sum Generates a carry, G = A AND B, or Propagates one, '
    'P = A XOR B. Find the carries C1 to C4 from the Gs, the Ps and C0 '
    'without waiting for each other: C2 = G1 + P1 G0 + P1 P0 C0, and so '
    'on. No output may pass through more than 6 chips; carried one by '
    'one, C4 would take 8.',
    ('G0', 'G1', 'G2', 'G3', 'P0', 'P1', 'P2', 'P3', 'C0'),
    ('C1', 'C2', 'C3', 'C4'), False,
    table(9, lambda g0, g1, g2, g3, p0, p1, p2, p3, c0: (
      g0 or (p0 and c0),
      g1 or (p1 and g0) or (p1 and p0 and c0),
      g2 or (p2 and g1) or (p2 and p1 and g0) or (p2 and p1 and p0 and c0),
      g3 or (p3 and g2) or (p3 and p2 and g1) or (p3 and p2 and p1 and g0)
      or (p3 and p2 and p1 and p0 and c0))),
    0.02, 6.0, ('ADD4',), _lookAheadOf),
  SuperQuest(
    'SR latch',
    'A memory of one bit: S sets Q high, R resets it low, and with both '
    'low Q holds what it was. Two NORs, each fed by the other.',
    ('S', 'R'), ('Q',), False,
    _steps(((1, 0), (1,)), ((0, 0), (1,)), ((0, 1), (0,)), ((0, 0), (0,))),
    0.25, math.inf, ('SR',), _latchOf),
  SuperQuest(
    'D flip-flop',
    'As the clock C rises, Q takes D; otherwise Q holds. A master latch '
    'open while C is low, a slave open while C is high.',
    ('D', 'C'), ('Q',), False,
    _steps(((1, 0), None), ((1, 1), (1,)), ((0, 1), (1,)), ((0, 0), (1,)),
           ((0, 1), (0,)), ((1, 1), (0,)), ((1, 0), (0,))),
    0.2, math.inf, ('DFF', Clock), _flipOf),
  SuperQuest(
    'JK flip-flop',
    'As the clock C rises: J sets Q, K resets it, both toggle it, neither '
    'holds it. A D flip-flop fed the right D: J AND NOT Q, OR NOT K AND '
    'Q.',
    ('J', 'K', 'C'), ('Q',), False,
    _steps(((1, 0, 0), None), ((1, 0, 1), (1,)), ((0, 0, 0), None),
           ((0, 0, 1), (1,)), ((0, 1, 0), None), ((0, 1, 1), (0,)),
           ((1, 1, 0), None), ((1, 1, 1), (1,)), ((1, 1, 0), None),
           ((1, 1, 1), (0,))),
    0.2, math.inf, ('JKFF',), _jkOf),
  SuperQuest(
    'Memory',
    'Four bits at the addresses A1 A0: while WE pulses high, D is '
    'written at the address; Q reads the bit there. A flip-flop a bit, a '
    'decoder picking which one WE clocks, and gates picking which one Q '
    'reads.',
    ('A0', 'A1', 'D', 'WE'), ('Q',), False, _memorySteps(), 0.15,
    math.inf, ('SRAM',), _memoryOf),
)
