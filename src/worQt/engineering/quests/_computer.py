"""
The computer quests: buses of four bits, and the parts of a little
computer built on them, each granted once built, up to the computer
itself, a 4004 of a single register, and a program for it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ..circuits import Bit, BusIn, BusProbe, Chip, Circuit, Node, Probe
from ..circuits import Wire, execute, program, started
from ._goals import Clocked, Tester, table
from ._super import Bench, _Builder

#  The program of the computer quest: Fibonacci's numbers until they
#  overflow four bits, then a jump to itself: LDM 1; WRR; XCH 0; ADD 0;
#  JCN 6; JUN 1; JUN 6
FIBONACCI = ((13, 1), (14, 2), (11, 0), (8, 0), (1, 6), (4, 1), (4, 6))
#  The program of the fetch quest: jumps, the last to itself
JUMPS = ((0, 0), (4, 5), (0, 0), (4, 3), (0, 0), (0, 0), (4, 3))
#  A program giving the three times table, the answer of the programmer
#  quest: LDM 3; XCH 0; ADD 0; JCN 6; WRR; JUN 2; JUN 6
TIMES = ((13, 3), (11, 0), (8, 0), (1, 6), (14, 2), (4, 2), (4, 6))


def busBench(inputs: tuple, outputs: tuple, *extra: tuple) -> Bench:
  """The 'busBench' function returns a test bench of the inputs and
  probes 'inputs' and 'outputs', each a name and a width, 1 or 4, down
  a ground bus on the left and on the right; and 'extra' chips, each a
  kind and the places of its pins, new nodes, fixed with it."""
  nodes, parts, pins = [], [], {}

  def node(x: float, y: float) -> int:
    nodes.append(Node(float(x), float(y)))
    return len(nodes) - 1

  left, right = node(-6, 0), node(14, 0)
  taps = [node(x, 0) for x in (0, 4, 8)]
  inputsAt, outputsAt = [], []
  below = left
  for k, (name, width) in enumerate(inputs):
    y = 2 * (len(inputs) - k)
    minus = node(-6, y)
    pins[name] = node(-4, y)
    parts.append(Wire(below, minus))
    below = minus
    inputsAt.append(len(parts))
    if width == 1:
      parts.append(Bit(pins[name], minus, False, name))
    else:
      parts.append(BusIn(pins[name], minus, 0, name))
  below = right
  for k, (name, width) in enumerate(outputs):
    y = 2 * (len(outputs) - k)
    minus = node(14, y)
    pins[name] = node(12, y)
    parts.append(Wire(below, minus))
    below = minus
    outputsAt.append(len(parts))
    if width == 1:
      parts.append(Probe(pins[name], minus, name))
    else:
      parts.append(BusProbe(pins[name], minus, name))
  for a, b in zip([left, *taps], [*taps, right]):
    parts.append(Wire(a, b))
  pins.update({'G%d' % k: tap for k, tap in enumerate(taps)})
  for kind, places, contents, label in extra:
    chipPins = []
    for place in places:
      if isinstance(place, str):
        chipPins.append(pins[place])
      else:
        chipPins.append(node(*place))
    parts.append(Chip(kind, (*chipPins,), contents))
    for k, pin in enumerate(chipPins):
      pins.setdefault('%s.%d' % (label, k), pin)
  order = [*inputsAt, *[i for i in range(len(parts)) if i not in inputsAt]]
  moved = {old: new for new, old in enumerate(order)}
  return Bench(Circuit((*nodes,), (*[parts[i] for i in order],)), pins,
               (*[moved[i] for i in inputsAt],),
               (*[moved[i] for i in outputsAt],))


def _steps(rows: list, logic: object) -> tuple:
  """Steps of a test bench: each of 'rows' its inputs and the outputs
  'logic' gives for them."""
  return (*[((*row,), (*logic(*row),)) for row in rows],)


def _adderRows() -> list:
  """Rows of two numbers and a carry: each number once, a second with
  it, and the edges."""
  rows = [(a, (7 * a + 3) % 16, a % 2) for a in range(16)]
  return rows + [(15, 15, 1), (0, 0, 0), (8, 8, 0), (15, 1, 0)]


def _aluRows() -> list:
  """Rows of two numbers and whether to take away: as the adder's, and
  equal numbers taken away, and a borrow."""
  rows = [(a, (5 * a + 7) % 16, a % 2) for a in range(16)]
  return rows + [(5, 5, 1), (3, 9, 1), (0, 0, 0), (15, 15, 0)]


def _alu(a: int, b: int, sub: int) -> tuple:
  """What the ALU gives: the sum, the carry and whether it is nought."""
  total = a + ((~b & 15) + 1 if sub else b)
  return total & 15, int(total > 15), int(total & 15 == 0)


def _registerSteps() -> tuple:
  """Loading, holding and loading again."""
  rows = [((5, 1, 0), None), ((5, 1, 1), (5,)), ((9, 0, 0), (5,)),
          ((9, 0, 1), (5,)), ((9, 1, 0), (5,)), ((9, 1, 1), (9,)),
          ((3, 0, 0), (9,)), ((3, 1, 0), (9,)), ((3, 1, 1), (3,)),
          ((12, 1, 0), (3,)), ((12, 1, 1), (12,))]
  return (*rows,)


def _counterSteps() -> tuple:
  """Loading nought, counting, holding, loading fourteen and counting
  round past fifteen."""
  rows = [((0, 1, 0, 0), None), ((0, 1, 0, 1), (0,))]
  for count in range(1, 4):
    rows += [((0, 0, 1, 0), None), ((0, 0, 1, 1), (count,))]
  rows += [((0, 0, 0, 0), None), ((0, 0, 0, 1), (3,)),
           ((14, 1, 0, 0), None), ((14, 1, 0, 1), (14,)),
           ((0, 0, 1, 0), None), ((0, 0, 1, 1), (15,)),
           ((0, 0, 1, 0), None), ((0, 0, 1, 1), (0,))]
  return (*rows,)


def _ticks(words: tuple) -> tuple:
  """The addresses the program of 'words' visits, one a tick, from
  nought until it stays at one."""
  machine, seen = started(1, 0), [0]
  for _ in range(40):
    op, arg = words[machine.pc] if machine.pc < len(words) else (0, 0)
    machine = execute(op, arg, machine)
    if machine.pc == seen[-1]:
      break
    seen.append(machine.pc)
  return (*seen,)


def outputs(words: tuple, registers: int, depth: int) -> tuple:
  """The 'outputs' function returns what OUT shows, each change, while
  the program of 'words' runs on a little computer of 'registers'
  registers and a stack 'depth' deep, from nought until it stays as it
  is."""
  machine, seen = started(registers, depth), [0]
  for _ in range(400):
    op, arg = words[machine.pc] if machine.pc < len(words) else (0, 0)
    after = execute(op, arg, machine)
    if after.out != seen[-1]:
      seen.append(after.out)
    if after == machine:
      break
    machine = after
  return (*seen,)


def _split(build: _Builder, bus: object) -> tuple:
  """The four bits of 'bus', split."""
  return build.chip('SPLIT', bus)


def _busSolved(given: Bench) -> Circuit:
  """The bus split into its bits, each to its probe."""
  build = _Builder(given)
  build.wire('N', 'SPLIT.0')
  for k in range(4):
    build.wire('SPLIT.%d' % (k + 1), 'N%d' % k)
  return build.circuit()


def _adderSolved(given: Bench) -> Circuit:
  """The four bits adder between a splitter a bus and a joiner."""
  build = _Builder(given)
  total = build.chip('ADD4', *_split(build, 'A'), *_split(build, 'B'),
                     'Ci')
  build.wire(build.chip('JOIN', *total[:4]), 'S')
  build.wire(total[4], 'Co')
  return build.circuit()


def _aluSolved(given: Bench) -> Circuit:
  """Taking away as adding not B and one: B through XORs with SUB, SUB
  the carry in; Z a NOR of ORs of the sum's bits."""
  build = _Builder(given)
  ch = build.chip
  flipped = [ch('XOR', bit, 'SUB') for bit in _split(build, 'B')]
  total, carry = ch('ADDB', 'A', ch('JOIN', *flipped), 'SUB')
  build.wire(total, 'S')
  build.wire(carry, 'C')
  bits = _split(build, total)
  build.wire(ch('NOR', ch('OR', bits[0], bits[1]),
                ch('OR', bits[2], bits[3])), 'Z')
  return build.circuit()


def _registerSolved(given: Bench) -> Circuit:
  """Four D flip-flops clocked when C rises with LD high."""
  build = _Builder(given)
  clock = build.chip('AND', 'C', 'LD')
  held = [build.chip('DFF', bit, clock)[0] for bit in _split(build, 'D')]
  build.wire(build.chip('JOIN', *held), 'Q')
  return build.circuit()


def _muxSolved(given: Bench) -> Circuit:
  """Each bit A AND NOT S, OR B AND S."""
  build = _Builder(given)
  ch = build.chip
  low = ch('NOT', 'S')
  bits = [ch('OR', ch('AND', a, low), ch('AND', b, 'S'))
          for a, b in zip(_split(build, 'A'), _split(build, 'B'))]
  build.wire(ch('JOIN', *bits), 'Q')
  return build.circuit()


def high(build: _Builder) -> int:
  """The 'high' function returns a new node held high: a logic input
  set to one, on the bench's ground."""
  one, ground = build.node(), build.node()
  build.add(Bit(one, ground, True, 'ONE'))
  build.wire(ground, 'G0')
  return one


def low(build: _Builder) -> int:
  """The 'low' function returns a new node held low: a logic input set
  to nought, on the bench's ground."""
  nought, ground = build.node(), build.node()
  build.add(Bit(nought, ground, False, 'LOW'))
  build.wire(ground, 'G0')
  return nought


def _counterSolved(given: Bench) -> Circuit:
  """A register loading D, or itself plus one where EN is high."""
  build = _Builder(given)
  ch = build.chip
  one = high(build)
  held = build.node()
  more, _ = ch('ADDB', held, build.node(), one)
  feed = ch('MUX', more, 'D', 'LD')
  build.add(Chip('REG', (feed, ch('OR', 'LD', 'EN'), build.at('C'), held)))
  build.wire(held, 'Q')
  return build.circuit()


def _decoderSolved(given: Bench) -> Circuit:
  """Each output an AND of A0 or not, and A1 or not."""
  build = _Builder(given)
  ch = build.chip
  low0, low1 = ch('NOT', 'A0'), ch('NOT', 'A1')
  for k, (a, b) in enumerate(((low0, low1), ('A0', low1), (low0, 'A1'),
                              ('A0', 'A1'))):
    build.wire(ch('AND', a, b), 'Y%d' % k)
  return build.circuit()


def _fetch(build: _Builder) -> tuple:
  """The fetch: the counter addressing the ROM, counting on, its opcode
  decoded, loading N when its LD, a new node, is high. Returns the
  counter's output, the decoder's and LD."""
  ch = build.chip
  address, load = build.node(), build.node()
  build.wire(address, 'ROM.0')
  lines = ch('DEC', 'ROM.1')
  build.add(Chip('PC', (build.at('ROM.2'), load, high(build),
                        build.at('C'), address)))
  return address, lines, load


def _fetchSolved(given: Bench) -> Circuit:
  """The fetch, jumping on JUN, its address to the probe."""
  build = _Builder(given)
  address, lines, load = _fetch(build)
  build.wire(lines[4], load)
  build.wire(address, 'ADR')
  return build.circuit()


def _computerSolved(given: Bench) -> Circuit:
  """The first computer: the fetch; registers A, R0, OUT and the carry,
  each clocked by C; an adder giving A + R0 + C; muxes choosing what A
  takes; jumps on JUN, and on JCN with the carry set."""
  build = _Builder(given)
  ch = build.chip
  _, y, load = _fetch(build)
  a, r0, flags = build.node(), build.node(), build.node()
  carry = ch('SPLIT', flags)[0]
  total, over = ch('ADDB', a, r0, carry)
  fromR0 = ch('OR', y[10], y[11])
  intoA = ch('MUX', ch('MUX', total, r0, fromR0), 'ROM.2', y[13])
  loadA = ch('OR', ch('OR', y[8], fromR0), y[13])
  build.add(Chip('REG', (intoA, loadA, build.at('C'), a)))
  build.add(Chip('REG', (a, y[11], build.at('C'), r0)))
  out = build.node()
  build.add(Chip('REG', (a, y[14], build.at('C'), out)))
  build.wire(out, 'OUT')
  nought = low(build)
  kept = ch('JOIN', over, nought, nought, nought)
  build.add(Chip('REG', (kept, y[8], build.at('C'), flags)))
  build.wire(ch('OR', y[4], ch('AND', y[1], carry)), load)
  return build.circuit()


def _programmed(given: Bench) -> Circuit:
  """The three times table, written into the ROM, the loose last
  part."""
  circuit = given.circuit
  rom = circuit.parts[-1]
  return circuit.withPart(len(circuit.parts) - 1,
                          Chip('ROM', rom.pins, program(TIMES)))


_ROM_AT = ((2, 6), (6, 7), (6, 5))
_CLOCK = (('C', 1),)


class ComputerQuest(NamedTuple):
  """
  ComputerQuest is a computer quest's makings: its name, brief, bench,
  how to make its goal from the bench, its reward, its solution from the
  bench, and how many of its last parts are loose.
  """

  name: str
  brief: str
  bench: Bench
  goal: object
  reward: tuple
  solve: object
  loose: int


def _tester(steps: tuple, wait: float) -> object:
  """What makes a test bench of 'steps' for a bench."""

  def made(given: Bench) -> Tester:
    return Tester(given.inputs, given.outputs, steps, wait, float('inf'))

  return made


def _clocked(expected: tuple, changes: bool, quiet: int) -> object:
  """What makes a clocked goal for a bench, its clock its first input,
  its probe its first output."""

  def made(given: Bench) -> Clocked:
    return Clocked(given.inputs[0], given.outputs[0], expected, changes,
                   quiet, 0.1)

  return made


def _computerBench(words: tuple, outputs: tuple) -> Bench:
  """A bench of a clock, the probes 'outputs', and a ROM of 'words',
  fixed, its pins free."""
  return busBench(_CLOCK, outputs,
                  ('ROM', _ROM_AT, program(words), 'ROM'))


def programmerBench(kind: str) -> Bench:
  """The 'programmerBench' function returns a bench of a clock, a probe
  of OUT, a computer of 'kind' wired to them, and an empty ROM above it
  wired to it, last and loose."""
  given = busBench(_CLOCK, (('OUT', _BUS),))
  circuit = given.circuit
  nodes, parts = [*circuit.nodes], [*circuit.parts]

  def node(x: float, y: float) -> int:
    nodes.append(Node(float(x), float(y)))
    return len(nodes) - 1

  clock, op, arg = node(3, 4), node(3, 3), node(3, 2)
  address, out = node(9, 4), node(9, 3)
  readA, readOp, readN = node(1, 8), node(5, 9), node(5, 7)
  parts += [Chip(kind, (clock, op, arg, address, out)),
            Wire(given.pins['C'], clock), Wire(out, given.pins['OUT']),
            Wire(address, readA), Wire(readOp, op), Wire(readN, arg),
            Chip('ROM', (readA, readOp, readN), program(()))]
  return Bench(Circuit((*nodes,), (*parts,)), given.pins, given.inputs,
               given.outputs)


_BUS = 4
_FOUR = tuple(('N%d' % k, 1) for k in range(4))
COMPUTERS = (
  ComputerQuest(
    'Bus', 'A bus is four wires in one, carrying a number from nought to '
    'fifteen, bit nought the ones, bit three the eights. Join the bus N to '
    'the splitter, and its bits to the probes.',
    busBench((('N', _BUS),), _FOUR,
             ('SPLIT', ((0, 4), (4, 7), (4, 5), (4, 3), (4, 1)), (),
              'SPLIT')),
    _tester(_steps([(n,) for n in range(16)],
                   lambda n: (*[(n >> k) & 1 for k in range(4)],)), 0.15),
    ('SPLIT', 'JOIN', BusIn, BusProbe), _busSolved, 0),
  ComputerQuest(
    'Bus adder', 'Add the buses A and B and the carry Ci: S the sum on a '
    'bus, Co the carry. Split them, add with your adder of four bits, join '
    'the sum.',
    busBench((('A', _BUS), ('B', _BUS), ('Ci', 1)),
             (('S', _BUS), ('Co', 1))),
    _tester(_steps(_adderRows(), lambda a, b, c: (
      (a + b + c) & 15, int(a + b + c > 15))), 0.15),
    ('ADDB',), _adderSolved, 0),
  ComputerQuest(
    'ALU', 'An arithmetic logic unit: S = A + B, or A - B when SUB is '
    'high, as A + NOT B + 1. C is the carry, high for no borrow; Z high '
    'when S is nought.',
    busBench((('A', _BUS), ('B', _BUS), ('SUB', 1)),
             (('S', _BUS), ('C', 1), ('Z', 1))),
    _tester(_steps(_aluRows(), _alu), 0.15), ('ALU',), _aluSolved, 0),
  ComputerQuest(
    'Register', 'Four bits remembered: as the clock C rises, Q takes D, but '
    'only if LD is high; else it holds.',
    busBench((('D', _BUS), ('LD', 1), ('C', 1)), (('Q', _BUS),)),
    _tester(_registerSteps(), 0.15), ('REG',), _registerSolved, 0),
  ComputerQuest(
    'Bus switch', 'A multiplexer: Q is A, or B when S is high, all four '
    'bits at once.',
    busBench((('A', _BUS), ('B', _BUS), ('S', 1)), (('Q', _BUS),)),
    _tester(_steps([(k, 15 - k, k % 2) for k in range(16)],
                   lambda a, b, s: (b if s else a,)), 0.15),
    ('MUX',), _muxSolved, 0),
  ComputerQuest(
    'Program counter', 'As the clock C rises: Q takes D if LD is high, '
    'else counts on by one if EN is, else holds. A register, an adder '
    'giving Q plus one, and a switch between that and D.',
    busBench((('D', _BUS), ('LD', 1), ('EN', 1), ('C', 1)),
             (('Q', _BUS),)),
    _tester(_counterSteps(), 0.15), ('PC',), _counterSolved, 0),
  ComputerQuest(
    'Decoder', 'One of four: Y n high where n is the number A1 A0, the '
    'others low.',
    busBench((('A0', 1), ('A1', 1)), tuple(('Y%d' % k, 1)
                                           for k in range(4))),
    _tester(_steps([(a0, a1) for a1 in (0, 1) for a0 in (0, 1)],
                   lambda a0, a1: (*[int(k == a0 + 2 * a1)
                                     for k in range(4)],)), 0.25),
    ('DEC',), _decoderSolved, 0),
  ComputerQuest(
    'Fetch', 'The ROM holds a program, a word an address: an opcode OP and '
    'an operand N. Let a program counter address it, clocked by C, '
    'counting on; decode OP, and on JUN, 4, load N. ADR shows where it is: '
    '0, 1, 5, 6, 3, and there it stays, jumping to itself.',
    _computerBench(JUMPS, (('ADR', _BUS),)),
    _clocked(_ticks(JUMPS), False, 3), ('ROM',), _fetchSolved, 0),
  ComputerQuest(
    'Computer', 'The first computer, after Intel\'s 4004 of 1971, with a '
    'single register, R0: A, R0, OUT and the carry C, all clocked by C. '
    'LDM n, 13: A takes n. LD, 10: A takes R0; XCH, 11: A and R0 swap. '
    'ADD, 8: A takes A + R0 + C, C the carry. WRR, 14: OUT takes A. JUN n, '
    '4: jumps to n; JCN n, 1: jumps if C. The 4004 had no halt: a program '
    'ends jumping to itself. The ROM counts Fibonacci: OUT shows 1, 2, 3, '
    '5, 8, 13.',
    _computerBench(FIBONACCI, (('OUT', _BUS),)),
    _clocked(outputs(FIBONACCI, 1, 0), True, 6), ('CPU',),
    _computerSolved, 0),
  ComputerQuest(
    'Programmer', 'Your computer, as a chip, with an empty ROM. Program '
    'it: select the ROM and write the words. OUT must show the three '
    'times table, 3, 6, 9, 12, 15, and then stay, the program jumping to '
    'itself.',
    programmerBench('CPU'),
    _clocked(outputs(TIMES, 1, 0), True, 6), (), _programmed, 1),
)
