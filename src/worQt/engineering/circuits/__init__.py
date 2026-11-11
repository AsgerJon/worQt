"""
The 'worQt.engineering.circuits' package is electric circuits as
taught at school: sources, resistors, lamps, capacitors, coils,
switches and meters on a grid, joined at nodes, in V, A, Ω, F, H and s,
reckoned exactly as they run. It needs no Qt;
'worQt.engineering.circuits.gui' shows it.

- Node, Wire, Source, Resistor, Lamp, Capacitor, Coil, Switch,
  Ammeter, Voltmeter, Diode, Led, Transistor, Bit, Probe, Clock: the
  nodes and the parts between them; ends, withEnds: the nodes a part
  joins.
- Chip, Spec, SPECS: digital parts, gates, adders, latches, flip-flops
  and memory, and those on buses of four bits up to a microprocessor,
  each of a kind in 'SPECS'; BusIn, BusProbe: a bus's input and probe;
  Instruction, ISA, FIRST, decoded: the little computers' instruction
  set, after Intel's 4004, and what the first computer of them carries
  out; Machine, started, execute, remembered: what a little computer
  holds, what a word does to it, and what a computer chip remembers;
  program, words: a program as a ROM remembers it.
- Flat, BUS: a circuit of buses as it is reckoned, each bus four
  wires.
- Circuit: the parts together.
- Network, REGIONS, regionsOf: the circuit reckoned, each diode and
  transistor in a region: its equations, how it changes, how it settles
  and swings of itself, and when a region fails.
- Run, Energies, Sample: a circuit running, taken on through time;
  where its energy has gone; how it was at a time.
- Example, EXAMPLES: small circuits to start from, with a word on what
  to do with each.
- si, microfarads: values written with the prefix that suits them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._parts import Node, Wire, Source, Resistor, Lamp, Capacitor, Coil
from ._parts import Switch, Ammeter, Voltmeter, Diode, Led, Transistor
from ._parts import Bit, Probe, Clock, BusIn, BusProbe, ends, withEnds
from ._chips import Chip, Spec, SPECS, Instruction, ISA, FIRST, decoded
from ._chips import Machine, started, execute, remembered, program, words
from ._circuit import Circuit, Flat, KINDS, LOGIC, BUS
from ._network import Network, REGIONS, regionsOf
from ._run import Run, Energies, Sample
from ._examples import Example, EXAMPLES
from ._si import si, microfarads

__all__ = (
  'Node',
  'Wire',
  'Source',
  'Resistor',
  'Lamp',
  'Capacitor',
  'Coil',
  'Switch',
  'Ammeter',
  'Voltmeter',
  'Diode',
  'Led',
  'Transistor',
  'Bit',
  'Probe',
  'Clock',
  'BusIn',
  'BusProbe',
  'Chip',
  'Spec',
  'SPECS',
  'Instruction',
  'ISA',
  'FIRST',
  'decoded',
  'Machine',
  'started',
  'execute',
  'remembered',
  'program',
  'words',
  'ends',
  'withEnds',
  'Circuit',
  'KINDS',
  'LOGIC',
  'BUS',
  'Flat',
  'Network',
  'REGIONS',
  'regionsOf',
  'Run',
  'Energies',
  'Sample',
  'Example',
  'EXAMPLES',
  'si',
  'microfarads',
)
