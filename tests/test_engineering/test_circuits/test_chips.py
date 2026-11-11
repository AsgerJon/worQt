"""
TestChips covers the logic parts and the chips: inputs and probes
named; gates' truth tables; an SR latch holding; a D flip-flop taking D
only as its clock rises; a clock driving a JK flip-flop to toggle; the
memory written and read; four bits added; what is refused; and the
energy a chip's outputs deliver kept.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Bit, Chip, Circuit, Clock, Network
from worQt.engineering.circuits import Node, Probe, Resistor, Run, SPECS

from . import CircuitsTest


def nodes(count: int) -> tuple:
  """'count' nodes in a column."""
  return (*[Node(0.0, float(k)) for k in range(count)],)


def bench(kind: str) -> Circuit:
  """A chip of 'kind', each input fed by a logic input, each output read
  by a probe: N1 the ground, then the inputs' nodes, then the
  outputs'."""
  spec = SPECS[kind]
  count = len(spec.inputs) + len(spec.outputs)
  parts = [Bit(1 + k, 0, False, name) for k, name in
           enumerate(spec.inputs)]
  parts.append(Chip(kind, (*range(1, 1 + count),)))
  parts += [Probe(1 + len(spec.inputs) + k, 0, name) for k, name in
            enumerate(spec.outputs)]
  return Circuit(nodes(1 + count), (*parts,))


def setting(run: Run, *levels: int) -> Run:
  """'run' with its first inputs set to 'levels', 1 or 0."""
  circuit = run.circuit
  for index, level in enumerate(levels):
    part = circuit.parts[index]
    circuit = circuit.withPart(index, Bit(part.first, part.second,
                                          bool(level), part.name))
  return Run(circuit, run)


def read(run: Run) -> tuple[int, ...]:
  """What the probes read, 1 or 0."""
  return (*[int(run.drops[i] > 2.5) for i, part in
            enumerate(run.circuit.parts) if isinstance(part, Probe)],)


class TestChips(CircuitsTest):
  """Tests for 'Chip', 'Bit', 'Probe' and 'Clock'."""

  def test_named(self) -> None:
    """Inputs and probes are labelled by their names, chips U1, U2."""
    circuit = bench('NAND')
    self.assertEqual([circuit.label(i) for i in range(4)],
                     ['A', 'B', 'U1', 'Q'])

  def test_gates(self) -> None:
    """Each gate's output follows its truth table, 5 V high and nought
    low, with nothing drawn from it."""
    tables = {
      'AND' : (0, 0, 0, 1), 'OR': (0, 1, 1, 1), 'NAND': (1, 1, 1, 0),
      'NOR' : (1, 0, 0, 0), 'XOR': (0, 1, 1, 0),
    }
    for kind, outputs in tables.items():
      run = Run(bench(kind))
      for row, expected in enumerate(outputs):
        run = setting(run, row >> 1, row & 1)
        self.assertEqual(read(run), (expected,), kind)
      self.assertAlmostEqual(run.drops[3], 5.0 * outputs[-1], 9)
    run = Run(bench('NOT'))
    self.assertEqual(read(run), (1,))
    self.assertEqual(read(setting(run, 1)), (0,))

  def test_latch(self) -> None:
    """S sets, R resets, and with neither the latch holds."""
    run = Run(bench('SR'))
    for levels, q in (((1, 0), 1), ((0, 0), 1), ((0, 1), 0), ((0, 0), 0)):
      run = setting(run, *levels)
      self.assertEqual(read(run), (q, 1 - q))

  def test_flip_flop(self) -> None:
    """Q takes D only as the clock rises."""
    run = Run(bench('DFF'))
    for levels, q in (((1, 0), 0), ((1, 1), 1), ((0, 1), 1), ((0, 0), 1),
                      ((0, 1), 0)):
      run = setting(run, *levels)
      self.assertEqual(read(run)[0], q)

  def test_clock(self) -> None:
    """A clock of 2 Hz, J and K high, toggles a JK flip-flop as it rises,
    every half second from the first half: read between the turns, Q
    is 0, 0, 1, 1, 0, 0, 1, 1."""
    circuit = bench('JKFF')
    clock = circuit.parts[2]
    circuit = circuit.withPart(2, Clock(clock.first, clock.second, 2.0))
    run = setting(Run(circuit), 1, 1)
    run.advance(0.125)
    levels = [read(run)[0]]
    for _ in range(7):
      run.advance(0.25)
      levels.append(read(run)[0])
    self.assertEqual(levels, [0, 0, 1, 1, 0, 0, 1, 1])
    self.assertEqual(run.regions[2], 'low')

  def test_memory(self) -> None:
    """Bits written at four addresses are read back."""
    run = Run(bench('SRAM'))
    for address, bit in enumerate((1, 0, 1, 1)):
      run = setting(run, address & 1, address >> 1, bit, 1)
      run = setting(run, address & 1, address >> 1, bit, 0)
    for address, bit in enumerate((1, 0, 1, 1)):
      run = setting(run, address & 1, address >> 1, 0, 0)
      self.assertEqual(read(run), (bit,))

  def test_adder(self) -> None:
    """Eleven and six and a carry make eighteen."""
    run = Run(bench('ADD4'))
    run = setting(run, 1, 1, 0, 1, 0, 1, 1, 0, 1)
    total = sum(bit << k for k, bit in enumerate(read(run)))
    self.assertEqual(total, 18)

  def test_refused(self) -> None:
    """A chip of no kind, or of too few pins, is refused; a clock ticks
    above nought."""
    with self.assertRaises(ValueError):
      Circuit(nodes(3), (Chip('MUX', (0, 1, 2)),))
    with self.assertRaises(ValueError):
      Circuit(nodes(3), (Chip('NAND', (0, 1)),))
    with self.assertRaises(ValueError):
      Circuit(nodes(2), (Clock(1, 0, 0.0),))

  def test_energy(self) -> None:
    """A gate's output driving 100 Ω delivers 5² / 110 W, behind its
    10 Ω, the energy kept."""
    circuit = bench('NOT')
    circuit = circuit.withParts(*circuit.parts, Resistor(2, 0, 100.0))
    run = Run(circuit)
    self.assertAlmostEqual(run.drops[3], 5.0 * 100.0 / 110.0, 9)
    run.advance(1.0)
    self.assertAlmostEqual(run.energies.heat, 25.0 / 110.0, 9)
    self.assertAlmostEqual(run.energies.balance, 0.0, 12)

  def test_regions(self) -> None:
    """A chip's region is its inputs' levels and its memory; a clock's
    high or low; others are refused."""
    circuit = bench('DFF')
    network = Network(circuit)
    self.assertEqual(network.regions[2], ((False, False), (False,)))
    regions = [*network.regions]
    regions[2] = ((False,), (False,))
    with self.assertRaises(ValueError):
      Network(circuit, (*regions,))
