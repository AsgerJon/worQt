"""
The chips: digital parts, each a 'Chip' of a kind named in 'SPECS', its
inputs read as low or high and its outputs driven low or high, some
remembering bits; the chips on buses of four bits, up to the little
computers and their instruction set, 'ISA', after Intel's 4004.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

LOW, HIGH = 0.0, 5.0  # V a chip drives an output to
THRESHOLD = 2.5  # V an input reads high above, low below
HYSTERESIS = 0.1  # V an input must pass the threshold by to turn


class Spec(NamedTuple):
  """
  Spec is a kind of chip: its 'name'; the 'symbol' drawn in its box, as
  the IEC has it, '&' for AND, '≥1' for OR, '=1' for XOR; whether its
  outputs are 'inverted', a ring drawn at each; the names of its
  'inputs' and its 'outputs'; how many bits it remembers, 'memory'; the
  input that is its clock, -1 for none; 'logic', its outputs from its
  inputs' levels and what it remembers; 'remember', what it remembers
  once its inputs turn from the levels before to those after; and
  'words', what it does. Its inputs and outputs are bits; a chip on
  buses groups them into ports, 'portsIn' and 'portsOut', each a name
  and a width, 1 or 4, the bits of a port of 4 counted up from bit
  nought; without ports, each bit is a port of its own. 'ins' and
  'outs' are the ports either way.
  """

  name: str
  symbol: str
  inverted: bool
  inputs: tuple[str, ...]
  outputs: tuple[str, ...]
  memory: int
  clock: int
  logic: object
  remember: object
  words: str
  portsIn: tuple = ()
  portsOut: tuple = ()

  @property
  def ins(self) -> tuple[tuple[str, int], ...]:
    """The input ports: each a name and a width."""
    return self.portsIn or (*[(name, 1) for name in self.inputs],)

  @property
  def outs(self) -> tuple[tuple[str, int], ...]:
    """The output ports: each a name and a width."""
    return self.portsOut or (*[(name, 1) for name in self.outputs],)

  @property
  def widths(self) -> tuple[int, ...]:
    """The width of each port, the inputs' then the outputs'."""
    return (*[width for _, width in (*self.ins, *self.outs)],)


def _kept(before: tuple, after: tuple, state: tuple) -> tuple:
  """What a chip remembering nothing remembers: nothing."""
  return state


def _gate(name: str, symbol: str, inverted: bool, count: int,
          logic: object, words: str) -> Spec:
  """A gate of 'count' inputs and one output, remembering nothing."""
  inputs = ('A', 'B', 'C', 'D')[:count]
  return Spec(name, symbol, inverted, inputs, ('Q',), 0, -1,
              lambda levels, state: (logic(*levels),), _kept, words)


def _add(levels: tuple, state: tuple) -> tuple:
  """A full adder's sum and carry."""
  total = sum(levels)
  return (total % 2 == 1, total >= 2)


def _add4(levels: tuple, state: tuple) -> tuple:
  """Four bits added to four with a carry in: the four bits of the sum
  and the carry out."""
  a = sum(int(bit) << k for k, bit in enumerate(levels[0:4]))
  b = sum(int(bit) << k for k, bit in enumerate(levels[4:8]))
  total = a + b + int(levels[8])
  return (*[(total >> k) & 1 == 1 for k in range(5)],)


def _latch(before: tuple, after: tuple, state: tuple) -> tuple:
  """An SR latch: set by S, reset by R, R winning, else holding."""
  s, r = after
  if r:
    return (False,)
  if s:
    return (True,)
  return state


def _flip(before: tuple, after: tuple, state: tuple) -> tuple:
  """A D flip-flop: as its clock rises, it takes D as it was."""
  if after[1] and not before[1]:
    return (before[0],)
  return state


def _jk(before: tuple, after: tuple, state: tuple) -> tuple:
  """A JK flip-flop: as its clock rises, J sets, K resets, both
  toggle, neither holds."""
  if not (after[2] and not before[2]):
    return state
  j, k = before[0], before[1]
  q = state[0]
  return ((j and not q) or (not k and q),)


def _address(levels: tuple) -> int:
  """The address the first two inputs give."""
  return int(levels[0]) + 2 * int(levels[1])


def _ram(before: tuple, after: tuple, state: tuple) -> tuple:
  """Four bits of memory: while WE is high, D is written at the
  address."""
  if not after[3]:
    return state
  bits = [*state]
  bits[_address(after)] = after[2]
  return (*bits,)


def _pair(levels: tuple, state: tuple) -> tuple:
  """What remembers one bit shows: Q and not Q."""
  return (state[0], not state[0])


SPECS = {spec.name: spec for spec in (
  _gate('NOT', '1', True, 1, lambda a: not a,
        'Q is high when A is low, and low when it is high.'),
  _gate('AND', '&', False, 2, lambda a, b: a and b,
        'Q is high when A and B both are.'),
  _gate('OR', '≥1', False, 2, lambda a, b: a or b,
        'Q is high when A or B, or both, are.'),
  _gate('NAND', '&', True, 2, lambda a, b: not (a and b),
        'Q is low only when A and B both are high.'),
  _gate('NOR', '≥1', True, 2, lambda a, b: not (a or b),
        'Q is high only when A and B both are low.'),
  _gate('XOR', '=1', False, 2, lambda a, b: a != b,
        'Q is high when A and B differ.'),
  Spec('FA', 'Σ', False, ('A', 'B', 'Ci'), ('S', 'Co'), 0, -1, _add,
       _kept, 'Adds A, B and the carry in: S the sum, Co the carry.'),
  Spec('ADD4', 'Σ4', False,
       ('A0', 'A1', 'A2', 'A3', 'B0', 'B1', 'B2', 'B3', 'C0'),
       ('S0', 'S1', 'S2', 'S3', 'C4'), 0, -1, _add4, _kept,
       'Adds two numbers of four bits and a carry, the carries looked '
       'ahead.'),
  Spec('SR', 'SR', False, ('S', 'R'), ('Q', 'Q̄'), 1, -1, _pair, _latch,
       'S sets Q high, R resets it low; with neither, Q holds.'),
  Spec('DFF', 'D', False, ('D', 'C'), ('Q', 'Q̄'), 1, 1, _pair, _flip,
       'As the clock C rises, Q takes D; otherwise Q holds.'),
  Spec('JKFF', 'JK', False, ('J', 'K', 'C'), ('Q', 'Q̄'), 1, 2, _pair,
       _jk, 'As the clock C rises: J sets Q, K resets it, both toggle '
            'it, neither holds it.'),
  Spec('SRAM', 'RAM', False, ('A0', 'A1', 'D', 'WE'), ('Q',), 4, -1,
       lambda levels, state: (state[_address(levels)],), _ram,
       'Four bits of memory: Q reads the bit at the address A1 A0; while '
       'WE is high, D is written there.'),
)}


def _number(bits: tuple) -> int:
  """The number 'bits' make, bit nought first."""
  return sum(int(bit) << k for k, bit in enumerate(bits))


def _bits(number: int, count: int) -> tuple[bool, ...]:
  """The 'count' bits of 'number', bit nought first."""
  return (*[(number >> k) & 1 == 1 for k in range(count)],)


def _four(name: str) -> tuple[str, ...]:
  """The names of the four bits of the port 'name'."""
  return (*['%s%d' % (name, k) for k in range(4)],)


def _alu(levels: tuple, state: tuple) -> tuple:
  """A plus B, or A less B, A plus not B plus one: the sum, the carry
  out, high for no borrow, and whether the sum is nought."""
  a, b = _number(levels[0:4]), _number(levels[4:8])
  total = a + ((~b & 15) + 1 if levels[8] else b)
  return (*_bits(total & 15, 4), total > 15, total & 15 == 0)


def _register(before: tuple, after: tuple, state: tuple) -> tuple:
  """A register: as its clock rises, it takes D if LD was high."""
  if after[5] and not before[5] and before[4]:
    return (*before[0:4],)
  return state


def _counter(before: tuple, after: tuple, state: tuple) -> tuple:
  """A program counter: as its clock rises, it takes D if LD was high,
  else counts on if EN was, else holds."""
  if not (after[6] and not before[6]):
    return state
  if before[4]:
    return (*before[0:4],)
  if before[5]:
    return _bits((_number(state) + 1) & 15, 4)
  return state


class Instruction(NamedTuple):
  """
  Instruction is an instruction of the little computers, after Intel's
  4004 of 1971, each a word of eight bits: its 'mnemonic'; its opcode,
  'op', the word's high four bits; its 'operand', the low four: 'n' a
  number or an address, 'r' a register, or, for an instruction of a
  group sharing an opcode, the operand naming it; and 'words', what it
  does.
  """

  mnemonic: str
  op: int
  operand: object
  words: str

  @property
  def takes(self) -> bool:
    """Whether the instruction takes an operand: a number, an address or
    a register."""
    return True if self.operand in ('n', 'r') else False


#  The instruction set of the little computers, the 4004's own opcodes
#  and names, each a single word: JCN asks only the carry, ISZ skips a
#  word rather than jumping, and there is no halt, as the 4004 had none:
#  a program ends by jumping to itself
ISA = (
  Instruction('NOP', 0, 0, 'does nothing'),
  Instruction('JCN', 1, 'n', 'jumps to n if C is set'),
  Instruction('JUN', 4, 'n', 'jumps to n'),
  Instruction('JMS', 5, 'n', 'calls n: the next address onto the stack, '
                             'then jumps'),
  Instruction('INC', 6, 'r', 'R r takes R r + 1'),
  Instruction('ISZ', 7, 'r', 'R r takes R r + 1, skipping the next word '
                             'once it is nought'),
  Instruction('ADD', 8, 'r', 'A takes A + R r + C; C the carry'),
  Instruction('SUB', 9, 'r', 'A takes A - R r, less one if C is set; C '
                             'set if nothing was borrowed'),
  Instruction('LD', 10, 'r', 'A takes R r'),
  Instruction('XCH', 11, 'r', 'A and R r change places'),
  Instruction('BBL', 12, 'n', 'returns to the address on the stack, A '
                              'taking n'),
  Instruction('LDM', 13, 'n', 'A takes n'),
  Instruction('WRR', 14, 2, 'OUT takes A'),
  Instruction('CLB', 15, 0, 'A and C take nought'),
  Instruction('CLC', 15, 1, 'C takes nought'),
  Instruction('IAC', 15, 2, 'A takes A + 1; C the carry'),
  Instruction('CMC', 15, 3, 'C flips'),
  Instruction('CMA', 15, 4, 'each bit of A flips'),
  Instruction('RAL', 15, 5, 'A and C turn left, C into bit nought'),
  Instruction('RAR', 15, 6, 'A and C turn right, C into bit three'),
  Instruction('TCC', 15, 7, 'A takes C, and C nought'),
  Instruction('DAC', 15, 8, 'A takes A - 1; C set if nothing was '
                            'borrowed'),
  Instruction('TCS', 15, 9, 'A takes 9, or 10 if C is set; C nought'),
  Instruction('STC', 15, 10, 'C takes one'),
  Instruction('DAA', 15, 11, 'A kept a decimal digit: plus 6 if over 9 '
                             'or if C is set, C then set if it carried'),
  Instruction('KBP', 15, 12, 'A takes which of four keys is down: 1, 2, '
                             '4, 8 give 1 to 4, none 0, more 15'),
)
#  What the first computer carries out, a 4004 of a single register, R0,
#  and no stack; any other word it passes over
FIRST = ('NOP', 'JCN', 'JUN', 'ADD', 'LD', 'XCH', 'LDM', 'WRR')


def decoded(op: int, arg: int) -> Instruction:
  """The 'decoded' function returns the instruction the word of opcode
  'op' and operand 'arg' is; a word that is none passes as NOP."""
  for instruction in ISA:
    if instruction.op == op:
      if instruction.takes or instruction.operand == arg:
        return instruction
  return ISA[0]


class Machine(NamedTuple):
  """
  Machine is what a little computer holds: its accumulator 'a', its
  carry 'c', its 'registers', its program counter 'pc', the addresses on
  its 'stack', the top first, and what it shows, 'out'.
  """

  a: int
  c: bool
  registers: tuple
  pc: int
  stack: tuple
  out: int


def started(registers: int, depth: int) -> Machine:
  """The 'started' function returns a little computer of 'registers'
  registers and a stack 'depth' deep, as it is switched on: all
  nought."""
  return Machine(0, False, (0,) * registers, 0, (0,) * depth, 0)


def _group(name: str, a: int, c: bool) -> tuple[int, bool]:
  """A and C after the instruction of the accumulator group 'name'."""
  if name in ('CLB', 'TCC', 'TCS'):
    first = {'CLB': 0, 'TCC': int(c), 'TCS': 10 if c else 9}[name]
    return first, False
  if name in ('CLC', 'STC', 'CMC'):
    return a, {'CLC': False, 'STC': True, 'CMC': not c}[name]
  if name in ('IAC', 'DAC'):
    if name == 'IAC':
      return (a + 1) & 15, a == 15
    return (a - 1) & 15, a != 0
  if name == 'CMA':
    return ~a & 15, c
  if name == 'RAL':
    return ((a << 1) | int(c)) & 15, a >= 8
  if name == 'RAR':
    return (a >> 1) | (int(c) << 3), a & 1 == 1
  if name == 'DAA' and (a > 9 or c):
    return (a + 6) & 15, True if a + 6 > 15 else c
  if name == 'KBP':
    return {0: 0, 1: 1, 2: 2, 4: 3, 8: 4}.get(a, 15), c
  return a, c


def execute(op: int, arg: int, machine: Machine) -> Machine:
  """The 'execute' function returns 'machine' after the word of opcode
  'op' and operand 'arg', its counter on to the next word unless it
  jumped or skipped one. A machine of fewer registers than the operand
  names takes it round them; one of no stack passes over JMS and BBL."""
  a, c, registers, pc, stack, out = machine
  name = decoded(op, arg).mnemonic
  after = (pc + 1) & 15
  held = [*registers]
  r = arg % len(held) if held else 0
  if name == 'JCN' and c or name == 'JUN':
    after = arg
  elif name == 'JMS' and stack:
    stack, after = (after, *stack[:-1]), arg
  elif name == 'BBL' and stack:
    after, stack, a = stack[0], (*stack[1:], stack[-1]), arg
  elif name in ('INC', 'ISZ') and held:
    held[r] = (held[r] + 1) & 15
    if name == 'ISZ' and held[r] == 0:
      after = (pc + 2) & 15
  elif name in ('ADD', 'SUB') and held:
    other = held[r] if name == 'ADD' else ~held[r] & 15
    total = a + other + int(c if name == 'ADD' else not c)
    a, c = total & 15, total > 15
  elif name in ('LD', 'XCH') and held:
    a, held[r] = held[r], (a if name == 'XCH' else held[r])
  elif name == 'LDM':
    a = arg
  elif name == 'WRR':
    out = a
  elif op == 15:
    a, c = _group(name, a, c)
  return Machine(a, True if c else False, (*held,), after, stack, out)


def _machineOf(state: tuple, registers: int, depth: int) -> Machine:
  """The little computer of 'registers' registers and a stack 'depth'
  deep remembered in 'state': A, C, the registers, the counter, the
  stack and OUT, in turn."""
  fours = [_number(state[at:at + 4]) for at in range(5, len(state), 4)]
  return Machine(_number(state[0:4]), state[4], (*fours[:registers],),
                 fours[registers], (*fours[registers + 1:-1],), fours[-1])


#  The registers and the depth of the stack of each little computer
_SHAPES = {'CPU': (1, 0), 'MPU': (16, 3)}


def remembered(kind: str, memory: tuple) -> Machine:
  """The 'remembered' function returns the little computer a chip of
  'kind', CPU or MPU, remembers in 'memory'."""
  registers, depth = _SHAPES[kind]
  return _machineOf(memory, registers, depth)


def _bitsOf(machine: Machine) -> tuple:
  """What a little computer remembers of 'machine'."""
  fours = (*machine.registers, machine.pc, *machine.stack, machine.out)
  return (*_bits(machine.a, 4), bool(machine.c),
          *[bit for value in fours for bit in _bits(value, 4)])


def _stepper(registers: int, depth: int, known: tuple) -> object:
  """What a little computer of 'registers' registers and a stack 'depth'
  deep remembers once its inputs turn: as its clock C rises, it carries
  out the word on OP and N as they were, passing over any word not
  'known'."""

  def remember(before: tuple, after: tuple, state: tuple) -> tuple:
    if not (after[0] and not before[0]):
      return state
    op, arg = _number(before[1:5]), _number(before[5:9])
    if decoded(op, arg).mnemonic not in known:
      op, arg = 0, 0
    machine = _machineOf(state, registers, depth)
    return _bitsOf(execute(op, arg, machine))

  return remember


def _shower(registers: int, depth: int) -> object:
  """What a little computer of 'registers' registers and a stack 'depth'
  deep shows: the address it reads its program at, and OUT."""

  def logic(levels: tuple, state: tuple) -> tuple:
    machine = _machineOf(state, registers, depth)
    return (*_bits(machine.pc, 4), *_bits(machine.out, 4))

  return logic


def _accumulate(levels: tuple, state: tuple) -> tuple:
  """The 4004's arithmetic: on OP 8 and 9, A plus or less R and the
  carry; on 15, the accumulator group N names; else A and the carry as
  they are."""
  a, r = _number(levels[0:4]), _number(levels[4:8])
  op, n = _number(levels[9:13]), _number(levels[13:17])
  c = levels[8]
  if op in (8, 9, 15):
    machine = execute(op, n if op == 15 else 0, Machine(a, c, (r,), 0, (),
                                                        0))
    a, c = machine.a, machine.c
  return (*_bits(a, 4), c)


def _file(levels: tuple, state: tuple) -> tuple:
  """Sixteen registers: Q reads the register R names."""
  at = 4 * _number(levels[0:4])
  return (*state[at:at + 4],)


def _filed(before: tuple, after: tuple, state: tuple) -> tuple:
  """Sixteen registers: as the clock C rises, the register R named takes
  D if WE was high."""
  if not (after[9] and not before[9]) or not before[8]:
    return state
  at = 4 * _number(before[0:4])
  bits = [*state]
  bits[at:at + 4] = before[4:8]
  return (*bits,)


def _stacked(before: tuple, after: tuple, state: tuple) -> tuple:
  """A stack three deep: as the clock C rises, PUSH puts D on top, the
  rest down one, the last lost; else POP takes the top away, the rest
  up one, the last kept."""
  if not (after[6] and not before[6]):
    return state
  if before[4]:
    return (*before[0:4], *state[0:8])
  if before[5]:
    return (*state[4:12], *state[8:12])
  return state


def _rom(levels: tuple, state: tuple) -> tuple:
  """A program of sixteen words: the word at the address, its opcode and
  its operand."""
  word = 8 * _number(levels[0:4])
  return (*state[word + 4:word + 8], *state[word:word + 4])


def program(words: tuple) -> tuple[bool, ...]:
  """The 'program' function returns what a ROM remembers of 'words',
  each an opcode and an operand, sixteen at most, the rest NOP."""
  bits = []
  for k in range(16):
    op, arg = words[k] if k < len(words) else (0, 0)
    bits += [*_bits(arg, 4), *_bits(op, 4)]
  return (*bits,)


def words(memory: tuple) -> tuple[tuple[int, int], ...]:
  """The 'words' function returns the sixteen words, opcode and operand,
  a ROM remembers in 'memory'."""
  return (*[(_number(memory[8 * k + 4:8 * k + 8]),
             _number(memory[8 * k:8 * k + 4])) for k in range(16)],)


def _busChips() -> tuple[Spec, ...]:
  """The chips on buses."""
  bus = 4
  return (
    Spec('SPLIT', '⇉', False, _four('B'), ('0', '1', '2', '3'), 0, -1,
         lambda levels, state: (*levels,), _kept,
         'Splits a bus into its four bits, bit nought first.',
         (('BUS', bus),), (('0', 1), ('1', 1), ('2', 1), ('3', 1))),
    Spec('JOIN', '⇇', False, ('0', '1', '2', '3'), _four('B'), 0, -1,
         lambda levels, state: (*levels,), _kept,
         'Joins four bits into a bus, bit nought first.',
         (('0', 1), ('1', 1), ('2', 1), ('3', 1)), (('BUS', bus),)),
    Spec('ADDB', 'Σ', False, (*_four('A'), *_four('B'), 'Ci'),
         (*_four('S'), 'Co'), 0, -1, _add4, _kept,
         'Adds two buses and a carry: S the sum, Co the carry.',
         (('A', bus), ('B', bus), ('Ci', 1)), (('S', bus), ('Co', 1))),
    Spec('ALU', 'ALU', False, (*_four('A'), *_four('B'), 'SUB'),
         (*_four('S'), 'C', 'Z'), 0, -1, _alu, _kept,
         'S is A + B, or A - B when SUB is high; C the carry, high for '
         'no borrow when taking away; Z high when S is nought.',
         (('A', bus), ('B', bus), ('SUB', 1)),
         (('S', bus), ('C', 1), ('Z', 1))),
    Spec('REG', 'REG', False, (*_four('D'), 'LD', 'C'), _four('Q'), 4, 5,
         lambda levels, state: (*state,), _register,
         'Four bits: as the clock C rises, Q takes D if LD is high.',
         (('D', bus), ('LD', 1), ('C', 1)), (('Q', bus),)),
    Spec('MUX', 'MUX', False, (*_four('A'), *_four('B'), 'S'),
         _four('Q'), 0, -1,
         lambda levels, state: (*(levels[4:8] if levels[8]
                                  else levels[0:4]),),
         _kept, 'Q is A, or B when S is high.',
         (('A', bus), ('B', bus), ('S', 1)), (('Q', bus),)),
    Spec('PC', 'CTR', False, (*_four('D'), 'LD', 'EN', 'C'), _four('Q'),
         4, 6, lambda levels, state: (*state,), _counter,
         'A program counter: as the clock C rises, Q takes D if LD is '
         'high, else counts on if EN is, else holds.',
         (('D', bus), ('LD', 1), ('EN', 1), ('C', 1)), (('Q', bus),)),
    Spec('DEC', 'DEC', False, _four('A'),
         (*['Y%d' % k for k in range(16)],), 0, -1,
         lambda levels, state: (*[k == _number(levels)
                                  for k in range(16)],),
         _kept, 'One of sixteen: Y n is high where n is on A.',
         (('A', bus),), (*[('Y%d' % k, 1) for k in range(16)],)),
    Spec('ROM', 'ROM', False, _four('A'), (*_four('OP'), *_four('N')),
         128, -1, _rom, _kept,
         'A program of sixteen words: OP and N are the opcode and the '
         'operand of the word at the address A.',
         (('A', bus),), (('OP', bus), ('N', bus))),
    Spec('CPU', 'CPU', False, ('C', *_four('OP'), *_four('N')),
         (*_four('ADR'), *_four('OUT')), 17, 0, _shower(1, 0),
         _stepper(1, 0, FIRST),
         'The first computer, a 4004 of one register: as its clock C '
         'rises it carries out the word on OP and N, reading its program '
         'at ADR.',
         (('C', 1), ('OP', bus), ('N', bus)), (('ADR', bus), ('OUT', bus))),
    Spec('RF', 'RF', False, (*_four('R'), *_four('D'), 'WE', 'C'),
         _four('Q'), 64, 9, _file, _filed,
         'Sixteen registers of four bits: Q reads the register R names; as '
         'the clock C rises, it takes D if WE is high.',
         (('R', bus), ('D', bus), ('WE', 1), ('C', 1)), (('Q', bus),)),
    Spec('STACK', 'STK', False, (*_four('D'), 'PUSH', 'POP', 'C'),
         _four('Q'), 12, 6, lambda levels, state: (*state[0:4],),
         _stacked,
         'A stack three deep, Q its top: as the clock C rises, PUSH puts D '
         'on top, POP takes the top away.',
         (('D', bus), ('PUSH', 1), ('POP', 1), ('C', 1)), (('Q', bus),)),
    Spec('ACC', 'ACC', False,
         (*_four('A'), *_four('R'), 'CI', *_four('OP'), *_four('N')),
         (*_four('S'), 'CO'), 0, -1, _accumulate, _kept,
         'The 4004\'s arithmetic: OP 8, ADD, S = A + R + CI; OP 9, SUB, S = '
         'A - R, less one if CI; OP 15, the accumulator group N names; '
         'else S is A and CO is CI.',
         (('A', bus), ('R', bus), ('CI', 1), ('OP', bus), ('N', bus)),
         (('S', bus), ('CO', 1))),
    Spec('MPU', 'MPU', False, ('C', *_four('OP'), *_four('N')),
         (*_four('ADR'), *_four('OUT')), 89, 0, _shower(16, 3),
         _stepper(16, 3, (*[each.mnemonic for each in ISA],)),
         'A microprocessor after the 4004: A, C, sixteen registers and a '
         'stack three deep; as its clock C rises it carries out the word '
         'on OP and N, reading its program at ADR.',
         (('C', 1), ('OP', bus), ('N', bus)), (('ADR', bus), ('OUT', bus))),
  )


SPECS.update({spec.name: spec for spec in _busChips()})


class Chip(NamedTuple):
  """
  Chip is a digital part of the kind 'kind', named in 'SPECS', joining
  its 'pins', its inputs' nodes then its outputs', in the order of its
  spec. Its inputs take no current and read high above 2.5 V, low
  below, each needing to pass by 0.1 V to turn; each output is driven
  to 5 V or nought behind 10 Ω, both from the circuit's ground: the
  minus pole of its first source. 'first' and 'second' are its first
  and last pins.
  """

  kind: str
  pins: tuple
  contents: tuple = ()

  letter = 'U'

  @property
  def spec(self) -> Spec:
    """The chip's kind."""
    return SPECS[self.kind]

  @property
  def first(self) -> int:
    """The chip's first pin."""
    return self.pins[0]

  @property
  def second(self) -> int:
    """The chip's last pin."""
    return self.pins[-1]

  @property
  def flat(self) -> bool:
    """Whether the chip has a pin a bit, as the circuit reckoned has
    it, rather than a pin a port, as it is drawn."""
    spec = self.spec
    return len(self.pins) == len(spec.inputs) + len(spec.outputs)

  @property
  def inputs(self) -> tuple:
    """The nodes of the chip's inputs: a bit's each, or a port's."""
    spec = self.spec
    count = len(spec.inputs) if self.flat else len(spec.ins)
    return self.pins[:count]

  @property
  def outputs(self) -> tuple:
    """The nodes of the chip's outputs: a bit's each, or a port's."""
    spec = self.spec
    count = len(spec.inputs) if self.flat else len(spec.ins)
    return self.pins[count:]
