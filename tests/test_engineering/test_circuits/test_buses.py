"""
TestBuses covers buses of four bits: how many bits each node carries,
inferred through wires, a bus joined to a single wire refused; the
circuit reckoned flat, each bus four nodes; the run showing the number
on each bus; the chips on buses, the adder, the ALU, the register, the
switch, the counter, the decoder, the ROM, and the computer counting
Fibonacci's numbers.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Bit, BusIn, BusProbe, Chip, Circuit
from worQt.engineering.circuits import Node, Probe, Run, SPECS, Wire
from worQt.engineering.circuits import decoded, execute, program, started
from worQt.engineering.circuits import words

from . import CircuitsTest

#  LDM 1; WRR; XCH 0; ADD 0; JCN 6; JUN 1; JUN 6
FIBONACCI = ((13, 1), (14, 2), (11, 0), (8, 0), (1, 6), (4, 1), (4, 6))


def nodes(count: int) -> tuple:
  """'count' nodes in a column."""
  return (*[Node(0.0, float(k)) for k in range(count)],)


def bench(kind: str, contents: tuple = ()) -> Circuit:
  """A chip of 'kind', each input port fed by a bus input or a logic
  input, each output port read by a bus probe or a probe: N1 the
  ground."""
  spec = SPECS[kind]
  ports = (*spec.ins, *spec.outs)
  parts = []
  for k, (name, width) in enumerate(spec.ins):
    made = BusIn(1 + k, 0, 0, name) if width > 1 else Bit(1 + k, 0, False,
                                                            name)
    parts.append(made)
  parts.append(Chip(kind, (*range(1, 1 + len(ports)),), contents))
  for k, (name, width) in enumerate(spec.outs):
    at = 1 + len(spec.ins) + k
    parts.append(BusProbe(at, 0, name) if width > 1 else _probe(at, name))
  return Circuit(nodes(1 + len(ports)), (*parts,))


def _probe(at: int, name: str) -> Probe:
  """A probe at the node of 'at'."""
  return Probe(at, 0, name)


def setting(run: Run, *values: int) -> Run:
  """'run' with its first inputs set to 'values'."""
  circuit = run.circuit
  for index, value in enumerate(values):
    part = circuit.parts[index]
    if isinstance(part, BusIn):
      made = BusIn(part.first, part.second, value, part.name)
    else:
      made = Bit(part.first, part.second, bool(value), part.name)
    circuit = circuit.withPart(index, made)
  return Run(circuit, run)


def read(run: Run) -> tuple:
  """What each output reads: a number off a bus, else 1 or 0."""
  out = []
  for index, part in enumerate(run.circuit.parts):
    if isinstance(part, BusProbe):
      out.append(run.values[part.first])
    elif isinstance(part, Probe):
      out.append(int(run.drops[index] > 2.5))
  return (*out,)


class TestBuses(CircuitsTest):
  """Tests for buses and the chips on them."""

  def test_widths(self) -> None:
    """A node is a bus where a bus port is, or a wire joins it to one; a
    bus joined to a single wire is refused."""
    circuit = Circuit(nodes(4), (BusIn(1, 0, 3, 'A'), Wire(1, 2),
                                 BusProbe(2, 0, 'Q')))
    self.assertEqual(circuit.widths(), (1, 4, 4, 1))
    with self.assertRaises(ValueError):
      Circuit(nodes(4), (BusIn(1, 0, 3, 'A'), Wire(1, 2),
                         Bit(2, 0, True, 'B')))
    with self.assertRaises(ValueError):
      Circuit(nodes(2), (BusIn(1, 0, 16, 'A'),))

  def test_flat(self) -> None:
    """Reckoned, each bus node is four, a wire on a bus four wires, a bus
    input four logic inputs; without buses a circuit is its own."""
    circuit = Circuit(nodes(4), (BusIn(1, 0, 5, 'A'), Wire(1, 2),
                                 BusProbe(2, 0, 'Q')))
    flat = circuit.flat()
    self.assertEqual(len(flat.circuit.nodes), 10)
    self.assertEqual(flat.parts, ((0, 1, 2, 3), (4, 5, 6, 7),
                                  (8, 9, 10, 11)))
    levels = [p.high for p in flat.circuit.parts[0:4]]
    self.assertEqual(levels, [True, False, True, False])
    self.assertEqual(flat.owners[5], 1)
    plain = Circuit(nodes(2), (Bit(1, 0, True, 'A'),))
    self.assertIs(plain.flat().circuit, plain)

  def test_values(self) -> None:
    """A run shows the number on each bus node, and none at a single
    one."""
    circuit = Circuit(nodes(4), (BusIn(1, 0, 11, 'A'), Wire(1, 2),
                                 BusProbe(2, 0, 'Q')))
    run = Run(circuit)
    self.assertEqual(run.values, (None, 11, 11, None))
    self.assertEqual(run.currents[1], 0.0)

  def test_adder_and_alu(self) -> None:
    """Nine and five make fourteen; nine less five, four, no borrow;
    five less five, nought."""
    run = setting(Run(bench('ADDB')), 9, 5, 0)
    self.assertEqual(read(run), (14, 0))
    run = setting(Run(bench('ALU')), 9, 5, 1)
    self.assertEqual(read(run), (4, 1, 0))
    run = setting(run, 5, 5, 1)
    self.assertEqual(read(run), (0, 1, 1))
    run = setting(run, 3, 9, 1)
    self.assertEqual(read(run), (10, 0, 0))

  def test_register_and_counter(self) -> None:
    """A register takes D as its clock rises with LD high; a counter
    counts, holds and loads; each as its inputs were before the clock
    rose."""
    run = Run(bench('REG'))
    for values, q in (((7, 1, 0), 0), ((7, 1, 1), 7), ((3, 0, 0), 7),
                      ((3, 0, 1), 7)):
      run = setting(run, *values)
      self.assertEqual(read(run), (q,))
    run = Run(bench('PC'))
    for values, q in (((0, 0, 1, 0), 0), ((0, 0, 1, 1), 1),
                      ((0, 0, 1, 0), 1), ((0, 0, 1, 1), 2),
                      ((0, 0, 0, 0), 2), ((0, 0, 0, 1), 2),
                      ((9, 1, 0, 0), 2), ((9, 1, 0, 1), 9)):
      run = setting(run, *values)
      self.assertEqual(read(run), (q,))

  def test_switch_and_decoder(self) -> None:
    """A switch passes A or B; a decoder lights the line of its
    number."""
    run = setting(Run(bench('MUX')), 6, 9, 1)
    self.assertEqual(read(run), (9,))
    run = setting(Run(bench('DEC')), 13)
    lines = read(run)
    self.assertEqual(lines.index(1), 13)
    self.assertEqual(sum(lines), 1)

  def test_rom(self) -> None:
    """A ROM gives the word at its address, from its program; its words
    read back; written as their mnemonics."""
    memory = program(((13, 3), (4, 2)))
    self.assertEqual(words(memory)[:3], ((13, 3), (4, 2), (0, 0)))
    run = setting(Run(bench('ROM', memory)), 1)
    self.assertEqual(read(run), (4, 2))
    self.assertEqual(decoded(4, 2).mnemonic, 'JUN')

  def test_execute(self) -> None:
    """Fibonacci's program, carried out word by word on a computer of a
    single register, shows 1, 2, 3, 5, 8 and 13, then jumps to itself at
    6."""
    machine, shown = started(1, 0), []
    for _ in range(60):
      after = execute(*FIBONACCI[machine.pc], machine)
      if after.out != machine.out:
        shown.append(after.out)
      machine = after
    self.assertEqual(shown, [1, 2, 3, 5, 8, 13])
    self.assertEqual(machine.pc, 6)

  def test_computer(self) -> None:
    """The computer as a chip, its ROM beside it, clocked by hand, runs
    Fibonacci's program: OUT shows nought, then 1, 2, 3, 5, 8 and 13,
    staying there."""
    places = nodes(9)
    parts = (Bit(1, 0, False, 'C'),
             Chip('CPU', (1, 2, 3, 4, 5)),
             Chip('ROM', (4, 2, 3), program(FIBONACCI)),
             BusProbe(5, 0, 'OUT'))
    run = Run(Circuit(places, parts))
    shown = []
    for _ in range(60):
      run = setting(run, 1)
      run = setting(run, 0)
      value = run.values[5]
      if not shown or shown[-1] != value:
        shown.append(value)
    self.assertEqual(shown, [0, 1, 2, 3, 5, 8, 13])

  def test_shared_pins(self) -> None:
    """A chip may take one node into two of its pins; joining two of
    its pins keeps it."""
    circuit = Circuit(nodes(3), (Bit(1, 0, True, 'A'),
                                 Chip('AND', (1, 1, 2))))
    self.assertEqual(read(Run(circuit.withParts(
      *circuit.parts, _probe(2, 'Q')))), (1,))
    spread = Circuit(nodes(4), (Bit(1, 0, True, 'A'),
                                Chip('AND', (1, 2, 3))))
    merged = spread.merged(1, 2)
    self.assertEqual(merged.parts[1], Chip('AND', (1, 1, 2)))
