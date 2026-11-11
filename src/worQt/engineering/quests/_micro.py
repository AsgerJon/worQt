"""
The microprocessor quests, after Intel's 4004 of 1971, the first
microprocessor: its sixteen registers, its stack and its arithmetic,
each granted once built, then the microprocessor itself, and a program
for it, as for the calculator the 4004 was made for.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ..circuits import Chip, Circuit, Machine, execute, program
from ._computer import ComputerQuest, _computerBench, _clocked, _steps
from ._computer import _tester, busBench, high, low, outputs
from ._computer import programmerBench
from ._super import Bench, _Builder

#  The program of the microprocessor quest: a countdown by threes, the
#  taking away in a subroutine. LDM 3; XCH 1; LDM 15; XCH 2; then LD 2;
#  WRR; JMS 9; JCN 4, round again while nothing was borrowed; JUN 8, the
#  end; the subroutine LD 2; CLC; SUB 1; XCH 2; BBL 0
COUNTDOWN = ((13, 3), (11, 1), (13, 15), (11, 2), (10, 2), (14, 2), (5, 9),
             (1, 4), (4, 8), (10, 2), (15, 1), (9, 1), (11, 2), (12, 0))
#  A program counting a decimal digit, the answer of the calculator
#  quest: IAC; DAA; WRR; JCN 5, once the digit carries; JUN 0; JUN 5
DIGIT = ((15, 2), (15, 11), (14, 2), (1, 5), (4, 0), (4, 5))

_BUS = 4


def _fileSteps() -> tuple:
  """Writing R0 to R3, reading them back, the clock rising with WE low
  writing nothing, and writing R1 anew."""
  values = ((0, 5), (1, 9), (2, 3), (3, 12))
  rows = []
  for r, d in values:
    rows += [((r, d, 1, 0), None), ((r, d, 1, 1), (d,))]
  for r, d in values:
    rows += [((r, 7, 0, 0), (d,)), ((r, 7, 0, 1), (d,))]
  rows += [((1, 6, 1, 0), (9,)), ((1, 6, 1, 1), (6,)),
           ((0, 6, 0, 0), (5,))]
  return (*rows,)


def _stackSteps() -> tuple:
  """Pushing three, taking two away, holding, pushing one and taking it
  away."""
  rows = [((5, 1, 0, 0), None), ((5, 1, 0, 1), (5,)),
          ((9, 1, 0, 0), (5,)), ((9, 1, 0, 1), (9,)),
          ((3, 1, 0, 0), (9,)), ((3, 1, 0, 1), (3,)),
          ((0, 0, 1, 0), (3,)), ((0, 0, 1, 1), (9,)),
          ((0, 0, 1, 0), (9,)), ((0, 0, 1, 1), (5,)),
          ((7, 0, 0, 0), (5,)), ((7, 0, 0, 1), (5,)),
          ((12, 1, 0, 0), (5,)), ((12, 1, 0, 1), (12,)),
          ((0, 0, 1, 0), (12,)), ((0, 0, 1, 1), (5,))]
  return (*rows,)


def _accumulatorRows() -> list:
  """Rows of A, R, the carry in, OP and N: ADD, SUB and others in turn,
  never 15, and the edges of each."""
  rows = [(a, (5 * a + 7) % 16, (a // 2) % 2, (8, 9, 13, 8, 9, 0)[a % 6],
           (3 * a + 1) % 16) for a in range(16)]
  return rows + [(15, 15, 1, 8, 0), (3, 9, 0, 9, 0), (5, 5, 0, 9, 0),
                 (5, 5, 1, 9, 0), (9, 2, 1, 11, 6), (0, 0, 0, 9, 0)]


def _accumulated(a: int, r: int, ci: int, op: int, n: int) -> tuple:
  """What the accumulator gives: on ADD and SUB, A with R and the
  carry; else A and the carry as they are."""
  if op in (8, 9):
    machine = execute(op, 0, Machine(a, ci == 1, (r,), 0, (), 0))
    return machine.a, int(machine.c)
  return a, ci


def _fileSolved(given: Bench) -> Circuit:
  """Four registers, each loading D as C rises where R names it and WE
  is high; Q the one R names, through a tree of switches."""
  build = _Builder(given)
  ch = build.chip
  lines = ch('DEC', 'R')
  held = []
  for k in range(4):
    held.append(build.node())
    build.add(Chip('REG', (build.at('D'), ch('AND', lines[k], 'WE'),
                           build.at('C'), held[-1])))
  first, second, _, _ = ch('SPLIT', 'R')
  build.wire(ch('MUX', ch('MUX', held[0], held[1], first),
                ch('MUX', held[2], held[3], first), second), 'Q')
  return build.circuit()


def _stackSolved(given: Bench) -> Circuit:
  """Three registers, each loading as C rises on PUSH or POP: the one
  above, or D, on a push, the one below on a pop; the last only on a
  push."""
  build = _Builder(given)
  ch = build.chip
  top, middle, bottom = build.node(), build.node(), build.node()
  moving = ch('OR', 'PUSH', 'POP')
  clock = build.at('C')
  build.add(Chip('REG', (ch('MUX', middle, 'D', 'PUSH'), moving, clock,
                         top)))
  build.add(Chip('REG', (ch('MUX', bottom, top, 'PUSH'), moving, clock,
                         middle)))
  build.add(Chip('REG', (middle, build.at('PUSH'), clock, bottom)))
  build.wire(top, 'Q')
  return build.circuit()


def _accumulatorSolved(given: Bench) -> Circuit:
  """ADD and SUB as one adder: R and the carry in each flipped through
  an XOR on SUB; S and CO the adder's on either, else A and CI."""
  build = _Builder(given)
  ch = build.chip
  lines = ch('DEC', 'OP')
  sub = lines[9]
  flipped = [ch('XOR', bit, sub) for bit in ch('SPLIT', 'R')]
  total, carry = ch('ADDB', 'A', ch('JOIN', *flipped),
                    ch('XOR', 'CI', sub))
  doing = ch('OR', lines[8], sub)
  build.wire(ch('MUX', 'A', total, doing), 'S')
  build.wire(ch('OR', ch('AND', doing, carry),
                ch('AND', ch('NOT', doing), 'CI')), 'CO')
  return build.circuit()


def _microSolved(given: Bench) -> Circuit:
  """The microprocessor, one word a tick: the ROM read at the counter,
  its opcode decoded; A loading each tick, from the accumulator unless
  LD or XCH give it R r, or LDM or BBL n; the carry each tick from the
  accumulator; the registers named by n, written on XCH with A, on INC
  and ISZ with R r + 1; OUT on WRR; the counter jumping on JUN, JMS,
  BBL, JCN with the carry, and skipping on ISZ come round to nought;
  the stack pushing on JMS, popping on BBL."""
  build = _Builder(given)
  ch = build.chip
  clock, n = build.at('C'), build.at('ROM.2')
  one, nought = high(build), low(build)
  zero = ch('JOIN', nought, nought, nought, nought)
  y = ch('DEC', 'ROM.1')
  a, held, address = build.node(), build.node(), build.node()
  build.wire(address, 'ROM.0')
  carry = build.node()
  total, over = ch('ACC', a, held, carry, 'ROM.1', n)
  build.add(Chip('DFF', (over, clock, carry, build.node())))
  intoA = ch('MUX', ch('MUX', total, held, ch('OR', y[10], y[11])), n,
             ch('OR', y[12], y[13]))
  build.add(Chip('REG', (intoA, one, clock, a)))
  counting = ch('OR', y[6], y[7])
  more, wrapped = ch('ADDB', held, zero, one)
  build.add(Chip('RF', (n, ch('MUX', a, more, counting),
                        ch('OR', y[11], counting), clock, held)))
  out = build.node()
  build.add(Chip('REG', (a, y[14], clock, out)))
  build.wire(out, 'OUT')
  following, _ = ch('ADDB', address, zero, one)
  after, _ = ch('ADDB', following, zero, one)
  top = ch('STACK', following, y[5], y[12], clock)
  skip = ch('AND', y[7], wrapped)
  target = ch('MUX', ch('MUX', n, top, y[12]), after, skip)
  load = ch('OR', ch('OR', y[4], ch('AND', y[1], carry)),
            ch('OR', ch('OR', y[5], y[12]), skip))
  build.add(Chip('PC', (target, load, one, clock, address)))
  return build.circuit()


def _programmedWith(words: tuple) -> object:
  """What writes 'words' into the bench's ROM, its loose last part."""

  def written(given: Bench) -> Circuit:
    circuit = given.circuit
    rom = circuit.parts[-1]
    return circuit.withPart(len(circuit.parts) - 1,
                            Chip('ROM', rom.pins, program(words)))

  return written


MICROS = (
  ComputerQuest(
    'Register file', 'Beside A, Intel\'s 4004 of 1971, the first '
    'microprocessor, kept sixteen registers of four bits, R0 to R15. '
    'Build four, R0 to R3: Q reads the register R names; as the clock C '
    'rises, the register R names takes D, if WE is high. You will be '
    'given all sixteen.',
    busBench((('R', _BUS), ('D', _BUS), ('WE', 1), ('C', 1)),
             (('Q', _BUS),)),
    _tester(_fileSteps(), 0.15), ('RF',), _fileSolved, 0),
  ComputerQuest(
    'Stack', 'JMS calls a subroutine and BBL returns from it: the 4004 '
    'kept the addresses to return to on a stack three deep, Q its top. '
    'As the clock C rises: with PUSH high, D goes on top, the rest down '
    'one, the last lost; else with POP high, the top goes, the rest up '
    'one, the last staying as it was.',
    busBench((('D', _BUS), ('PUSH', 1), ('POP', 1), ('C', 1)),
             (('Q', _BUS),)),
    _tester(_stackSteps(), 0.15), ('STACK',), _stackSolved, 0),
  ComputerQuest(
    'Accumulator', 'The 4004 did its sums in A and its carry. ADD, OP 8: '
    'S = A + R + CI, CO the carry. SUB, OP 9: S = A - R, less one if CI '
    'is set, CO set if nothing was borrowed; the 4004 added NOT R and NOT '
    'CI. Any other OP: S is A and CO is CI, but 15, the accumulator group, '
    'CLB to KBP, named by N: you will be given that with the rest.',
    busBench((('A', _BUS), ('R', _BUS), ('CI', 1), ('OP', _BUS),
              ('N', _BUS)), (('S', _BUS), ('CO', 1))),
    _tester(_steps(_accumulatorRows(), _accumulated), 0.15), ('ACC',),
    _accumulatorSolved, 0),
  ComputerQuest(
    'Microprocessor', 'The final boss: a microprocessor after the 4004, '
    'one word a tick, all clocked by C. A and the carry from the '
    'accumulator; LD and XCH, 10 and 11, give A the register n names, '
    'XCH writing A there; LDM and BBL, 13 and 12, give A n. INC and ISZ, '
    '6 and 7, add one to a register, ISZ skipping a word once it comes '
    'round to nought. WRR, 14: OUT takes A. JUN, 4, jumps; JCN, 1, if the '
    'carry is set; JMS, 5, calls, the next address onto the stack; BBL '
    'returns. The ROM counts down by threes: OUT shows 15, 12, 9, 6, 3, '
    '0.',
    _computerBench(COUNTDOWN, (('OUT', _BUS),)),
    _clocked(outputs(COUNTDOWN, 16, 3), True, 6), ('MPU',), _microSolved,
    0),
  ComputerQuest(
    'Calculator', 'The 4004 was made for a desk calculator, its digits '
    'decimal. Your microprocessor, as a chip, with an empty ROM: program '
    'it to count a decimal digit, OUT showing 1, 2, 3, 4, 5, 6, 7, 8, 9 '
    'and then 0, and stay there. IAC adds one; DAA keeps A a decimal '
    'digit, setting the carry as it comes round.',
    programmerBench('MPU'),
    _clocked(outputs(DIGIT, 16, 3), True, 6), (), _programmedWith(DIGIT),
    1),
)
