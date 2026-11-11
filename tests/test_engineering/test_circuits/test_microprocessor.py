"""
TestMicroprocessor covers the instruction set after Intel's 4004: each
word decoded by the 4004's opcodes, its groups by their operands; the
arithmetic with the carry, ADD adding it and SUB borrowing by it; the
accumulator group; jumps on the carry, ISZ skipping, JMS and BBL on the
stack; and the chips of the microprocessor, the register file, the
stack, the accumulator, and the microprocessor itself counting down.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Bit, BusProbe, Chip, Circuit, FIRST
from worQt.engineering.circuits import ISA, Machine, Run, decoded
from worQt.engineering.circuits import execute, program, remembered
from worQt.engineering.circuits import started

from . import CircuitsTest
from .test_buses import bench, nodes, read, setting

#  LDM 3; XCH 1; LDM 15; XCH 2; LD 2; WRR; JMS 9; JCN 4; JUN 8; and the
#  subroutine LD 2; CLC; SUB 1; XCH 2; BBL 0
COUNTDOWN = ((13, 3), (11, 1), (13, 15), (11, 2), (10, 2), (14, 2), (5, 9),
             (1, 4), (4, 8), (10, 2), (15, 1), (9, 1), (11, 2), (12, 0))


def machine(a: int, c: bool, *registers: int) -> Machine:
  """A computer of A 'a', carry 'c' and 'registers', at nought, its
  stack three deep and empty."""
  return Machine(a, c, (*registers,) or (0,), 0, (0, 0, 0), 0)


def group(name: str, a: int, c: bool) -> tuple[int, bool]:
  """A and the carry after the accumulator group's 'name'."""
  op, arg = [(i.op, i.operand) for i in ISA if i.mnemonic == name][0]
  after = execute(op, arg, machine(a, c))
  return after.a, after.c


class TestMicroprocessor(CircuitsTest):
  """Tests for the instruction set and the microprocessor's chips."""

  def test_decoded(self) -> None:
    """Words are decoded by the 4004's opcodes, its groups by their
    operands; a word that is no instruction passes as NOP; each
    mnemonic is named once; the first computer's are among them."""
    for word, name in (((13, 5), 'LDM'), ((4, 9), 'JUN'), ((1, 3), 'JCN'),
                       ((5, 2), 'JMS'), ((12, 0), 'BBL'), ((7, 4), 'ISZ'),
                       ((14, 2), 'WRR'), ((15, 0), 'CLB'), ((15, 11), 'DAA'),
                       ((14, 3), 'NOP'), ((2, 0), 'NOP'), ((15, 13), 'NOP')):
      self.assertEqual(decoded(*word).mnemonic, name, word)
    names = [instruction.mnemonic for instruction in ISA]
    self.assertEqual(len(names), len(set(names)))
    self.assertTrue(set(FIRST) <= set(names))
    self.assertEqual(decoded(9, 0).operand, 'r')
    self.assertFalse(decoded(15, 2).takes)

  def test_arithmetic(self) -> None:
    """ADD adds the carry in; SUB takes one more away if the carry is
    set, setting it if nothing was borrowed."""
    added = execute(8, 1, machine(9, True, 0, 6))
    self.assertEqual((added.a, added.c), (0, True))
    added = execute(8, 1, machine(2, False, 0, 3))
    self.assertEqual((added.a, added.c), (5, False))
    taken = execute(9, 0, machine(7, False, 3))
    self.assertEqual((taken.a, taken.c), (4, True))
    taken = execute(9, 0, machine(7, True, 3))
    self.assertEqual((taken.a, taken.c), (3, True))
    taken = execute(9, 0, machine(3, False, 7))
    self.assertEqual((taken.a, taken.c), (12, False))

  def test_group(self) -> None:
    """The accumulator group, each by the 4004's own rule."""
    cases = (('CLB', 9, True, 0, False), ('CLC', 9, True, 9, False),
             ('IAC', 15, False, 0, True), ('IAC', 4, True, 5, False),
             ('CMC', 4, True, 4, False), ('CMA', 5, False, 10, False),
             ('RAL', 9, True, 3, True), ('RAR', 9, False, 4, True),
             ('TCC', 7, True, 1, False), ('DAC', 0, True, 15, False),
             ('DAC', 6, False, 5, True), ('TCS', 3, True, 10, False),
             ('TCS', 3, False, 9, False), ('STC', 3, False, 3, True),
             ('DAA', 10, False, 0, True), ('DAA', 5, True, 11, True),
             ('DAA', 7, False, 7, False), ('KBP', 4, False, 3, False),
             ('KBP', 6, False, 15, False))
    for name, a, c, wanted, carried in cases:
      self.assertEqual(group(name, a, c), (wanted, carried),
                       '%s %d %s' % (name, a, c))

  def test_flow(self) -> None:
    """JCN jumps only with the carry set; ISZ skips a word once its
    register comes round to nought; JMS puts the next address on the
    stack and BBL returns to it, A taking its operand."""
    self.assertEqual(execute(1, 9, machine(0, True)).pc, 9)
    self.assertEqual(execute(1, 9, machine(0, False)).pc, 1)
    counted = execute(7, 0, machine(0, False, 14))
    self.assertEqual((counted.registers, counted.pc), ((15,), 1))
    counted = execute(7, 0, Machine(0, False, (15,), 0, (0, 0, 0), 0))
    self.assertEqual((counted.registers, counted.pc), ((0,), 2))
    called = execute(5, 9, Machine(0, False, (0,), 4, (0, 0, 0), 0))
    self.assertEqual((called.pc, called.stack), (9, (5, 0, 0)))
    back = execute(12, 7, called)
    self.assertEqual((back.pc, back.stack, back.a), (5, (0, 0, 0), 7))
    nested = started(16, 3)
    for address in (3, 6, 9, 12):
      nested = execute(5, address, nested)
    self.assertEqual(nested.stack, (10, 7, 4))

  def test_first(self) -> None:
    """The first computer, a chip, passes over what it does not carry
    out: JMS goes on to the next word."""
    places = nodes(6)
    parts = (Bit(1, 0, False, 'C'), Chip('CPU', (1, 2, 3, 4, 5)),
             Chip('ROM', (4, 2, 3), program(((5, 9), (13, 6), (14, 2)))),
             BusProbe(5, 0, 'OUT'))
    run = Run(Circuit(places, parts))
    for _ in range(3):
      run = setting(setting(run, 1), 0)
    self.assertEqual(run.values[5], 6)
    held = remembered('CPU', run.regions[1][1])
    self.assertEqual((held.a, held.pc, held.registers), (6, 3, (0,)))

  def test_register_file(self) -> None:
    """Q reads the register R names; as C rises it takes D if WE is
    high."""
    run = Run(bench('RF'))
    run = setting(setting(run, 3, 9, 1, 0), 3, 9, 1, 1)
    run = setting(setting(run, 5, 2, 1, 0), 5, 2, 1, 1)
    run = setting(setting(run, 5, 7, 0, 0), 5, 7, 0, 1)
    self.assertEqual(read(run), (2,))
    self.assertEqual(read(setting(run, 3, 7, 0, 0)), (9,))
    self.assertEqual(read(setting(run, 4, 7, 0, 0)), (0,))

  def test_stack(self) -> None:
    """As C rises, PUSH puts D on top, POP takes it away; four deep, the
    first is lost."""
    run = Run(bench('STACK'))
    for value in (1, 2, 3, 4):
      run = setting(setting(run, value, 1, 0, 0), value, 1, 0, 1)
    self.assertEqual(read(run), (4,))
    tops = []
    for _ in range(3):
      run = setting(setting(run, 0, 0, 1, 0), 0, 0, 1, 1)
      tops.append(read(run)[0])
    self.assertEqual(tops, [3, 2, 2])

  def test_accumulator(self) -> None:
    """ADD, SUB and the group as 'execute' has them; any other opcode
    leaves A and the carry be."""
    run = Run(bench('ACC'))
    for a, r, ci, op, n in ((9, 6, 1, 8, 0), (3, 7, 0, 9, 0),
                            (10, 0, 0, 15, 11), (5, 2, 1, 13, 4)):
      wanted = (a, ci)
      if op in (8, 9, 15):
        after = execute(op, n if op == 15 else 0,
                        Machine(a, ci == 1, (r,), 0, (), 0))
        wanted = (after.a, int(after.c))
      run = setting(run, a, r, ci, op, n)
      self.assertEqual(read(run), wanted, (a, r, ci, op, n))

  def test_microprocessor(self) -> None:
    """The microprocessor as a chip, its ROM beside it, clocked by hand,
    counts down by threes, its subroutine taking the threes away: OUT
    shows 15, 12, 9, 6, 3 and 0, then stays."""
    places = nodes(6)
    parts = (Bit(1, 0, False, 'C'), Chip('MPU', (1, 2, 3, 4, 5)),
             Chip('ROM', (4, 2, 3), program(COUNTDOWN)),
             BusProbe(5, 0, 'OUT'))
    run = Run(Circuit(places, parts))
    shown = [0]
    for _ in range(70):
      run = setting(setting(run, 1), 0)
      if run.values[5] != shown[-1]:
        shown.append(run.values[5])
    self.assertEqual(shown, [0, 15, 12, 9, 6, 3, 0])
    held = remembered('MPU', run.regions[1][1])
    self.assertEqual((held.pc, held.registers[1], held.registers[2]),
                     (8, 3, 13))
