"""
Circuit is an electric circuit: nodes on a grid and the parts between
them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from typing import NamedTuple

from ._chips import Chip, SPECS
from ._parts import Ammeter, Bit, BusIn, BusProbe, Capacitor, Clock, Coil
from ._parts import Diode, Lamp, Led, Node, Probe, Resistor, Source
from ._parts import Switch, Transistor, Voltmeter, Wire, ends, withEnds

Part = (Wire | Source | Resistor | Lamp | Capacitor | Coil | Switch
        | Ammeter | Voltmeter | Diode | Led | Transistor | Bit | Probe
        | Clock | BusIn | BusProbe | Chip)
#  Each kind of part, in the order the toolbar has them
KINDS = (Wire, Source, Resistor, Lamp, Capacitor, Coil, Switch, Ammeter,
         Voltmeter, Diode, Led, Transistor)
#  The logic parts, besides the chips
LOGIC = (Bit, Probe, Clock, BusIn, BusProbe)
BUS = 4  # bits a bus carries


class Flat(NamedTuple):
  """
  Flat is a circuit of buses as it is reckoned: 'circuit', every node a
  single wire, each bus node four; the nodes each node of the circuit
  drawn is, 'nodes', one or four; the parts each part is, 'parts'; and
  the part drawn each part reckoned is, 'owners'.
  """

  circuit: object
  nodes: tuple
  parts: tuple
  owners: tuple


class Circuit(BaseObject):
  """
  Circuit is an electric circuit: its 'nodes', each at a point of the
  grid it is drawn on, and its 'parts', each joining two nodes, a
  transistor three, a chip as many as it has pins; parts joining the
  same two nodes are in parallel.
  In V, A, Ω, F, H and s.

  A circuit is made only whole: its nodes apart, each part between two
  nodes there are, of the values it can have: resistances, capacitances,
  inductances and a lamp's rating above nought, a source's internal
  resistance and frequency nought or more. 'label' names a part by its
  letter and number among its kind, as 'R2'; 'joined' gives the parts
  at a node; 'side' says where a part is drawn among those in parallel
  with it.

  'withNodes' and 'withParts' return it with those changed; 'withNode'
  and 'withPart' with one replaced; 'withoutNode' without a node and
  the parts on it, 'withoutPart' without a part, its nodes left, the
  indices after it moved down; 'merged' with one node joined into
  another, the parts between them gone, a chip kept, two of its pins
  then on one node. Made of nothing, it is the
  standard circuit: a battery of 6 V charging a capacitor of 10000 µF
  through a lamp, once its switch is closed, a voltmeter across the
  capacitor.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_nodes__ = (Node(0.0, 0.0), Node(0.0, 4.0), Node(4.0, 4.0),
                        Node(8.0, 4.0), Node(8.0, 0.0))
  __fallback_parts__ = (
    Source(1, 0, 6.0, 0.0, 0.0),
    Switch(1, 2, False),
    Lamp(2, 3, 6.0, 0.3),
    Capacitor(3, 4, 0.01),
    Voltmeter(3, 4),
    Wire(4, 0),
  )

  #  Private Variables
  __circuit_parts__: tuple | None = None
  __circuit_flat__: Flat | None = None
  __circuit_widths__: tuple | None = None

  #  Virtual Variables
  nodes: Field[tuple[Node, ...]] = Field()
  parts: Field[tuple[Part, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParts(self, ) -> tuple:
    if self.__circuit_parts__ is None:
      raise MissingVariable(self, '__circuit_parts__', tuple)
    return self.__circuit_parts__

  @nodes.GET
  def _getNodes(self, ) -> tuple[Node, ...]:
    """The 'nodes' getter returns the nodes, in the order added."""
    return self._getParts()[0]

  @parts.GET
  def _getPartsField(self, ) -> tuple[Part, ...]:
    """The 'parts' getter returns the parts, in the order added."""
    return self._getParts()[1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d nodes, %d parts)"""
    return infoSpec % (type(self).__name__, len(self.nodes),
                       len(self.parts))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(tuple, tuple)
  def __init__(self, nodes: tuple, parts: tuple) -> None:
    nodes = (*[Node(float(n.x), float(n.y)) for n in nodes],)
    parts = (*map(self._cleaned, parts),)
    self._checkNodes(nodes)
    self._checkParts(nodes, parts)
    self.__circuit_parts__ = (nodes, parts)
    self.widths()

  @overload()
  def __init__(self, ) -> None:
    self.__init__(self.__fallback_nodes__, self.__fallback_parts__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def label(self, index: int) -> str:
    """The 'label' method names the part of 'index' by its letter and
    its number among the parts of its kind: 'R2' is the second
    resistor."""
    part = self.parts[index]
    if isinstance(part, (Bit, Probe, BusIn, BusProbe)) and part.name:
      return part.name
    count = sum(1 for other in self.parts[:index + 1]
                if type(other) is type(part))
    return '%s%d' % (part.letter, count)

  def joined(self, node: int) -> list[int]:
    """The 'joined' method returns the parts at the node of index
    'node'."""
    return [i for i, p in enumerate(self.parts)
            if node in ends(p)]

  def side(self, index: int) -> int:
    """The 'side' method returns where the part of 'index' is drawn among
    the parts joining the same two nodes: nought, the first, straight
    between them, then 1, -1, 2, -2 and so on, a step aside to the left
    of the line from the lower node to the higher, or to the right."""
    part = self.parts[index]
    pair = {part.first, part.second}
    rank = sum(1 for other in self.parts[:index]
               if {other.first, other.second} == pair)
    return (rank + 1) // 2 * (1 if rank % 2 else -1)

  def at(self, x: float, y: float) -> int | None:
    """The 'at' method returns the node at 'x' and 'y', or 'None'."""
    for index, node in enumerate(self.nodes):
      if math.hypot(node.x - x, node.y - y) < 1e-6:
        return index
    return None

  def widths(self, ) -> tuple[int, ...]:
    """The 'widths' method returns how many bits each node carries: four
    where a bus port is, or a wire joins it to one, else one. A bus
    joined to a single wire is refused."""
    if self.__circuit_widths__ is None:
      self.__circuit_widths__ = self._widths()
    return self.__circuit_widths__

  def flat(self, ) -> Flat:
    """The 'flat' method returns the circuit as it is reckoned, each bus
    node four nodes, each part on buses its parts on them: a wire four
    wires, a bus input four logic inputs, a bus probe four probes, a
    chip its pins a bit each. A circuit without buses is its own."""
    if self.__circuit_flat__ is None:
      self.__circuit_flat__ = self._flat()
    return self.__circuit_flat__

  def withNodes(self, *nodes: Node) -> Circuit:
    """The 'withNodes' method returns the circuit of 'nodes'."""
    return Circuit(nodes, self.parts)

  def withParts(self, *parts: Part) -> Circuit:
    """The 'withParts' method returns the circuit of 'parts'."""
    return Circuit(self.nodes, parts)

  def withNode(self, index: int, node: Node) -> Circuit:
    """The 'withNode' method returns the circuit with the node of 'index'
    moved to 'node'."""
    nodes = [*self.nodes]
    nodes[index] = node
    return self.withNodes(*nodes)

  def withPart(self, index: int, part: Part) -> Circuit:
    """The 'withPart' method returns the circuit with the part of 'index'
    replaced by 'part'."""
    parts = [*self.parts]
    parts[index] = part
    return self.withParts(*parts)

  def withoutPart(self, index: int) -> Circuit:
    """The 'withoutPart' method returns the circuit without the part of
    'index'; its nodes stay."""
    parts = [p for i, p in enumerate(self.parts) if i != index]
    return self.withParts(*parts)

  def withoutNode(self, index: int) -> Circuit:
    """The 'withoutNode' method returns the circuit without the node of
    'index' and the parts on it."""
    parts = [p for p in self.parts if index not in ends(p)]
    nodes = [n for i, n in enumerate(self.nodes) if i != index]
    return Circuit((*nodes,), (*map(self._renumbered(index), parts),))

  def merged(self, kept: int, gone: int) -> Circuit:
    """The 'merged' method returns the circuit with the node of index
    'gone' joined into the node of index 'kept': the parts on it moved
    to it, those between the two gone."""
    if kept == gone:
      return self
    parts = []
    for part in self.parts:
      joins = [kept if end == gone else end for end in ends(part)]
      if len(set(joins)) == len(joins) or isinstance(part, Chip):
        parts.append(withEnds(part, joins))
    nodes = [n for i, n in enumerate(self.nodes) if i != gone]
    return Circuit((*nodes,), (*map(self._renumbered(gone), parts),))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def portWidths(part: Part) -> tuple:
    """The 'portWidths' method returns how many bits each end of 'part'
    carries, or 'None' for an end a wire joins, whatever it is."""
    if isinstance(part, Chip):
      return (1,) * len(part.pins) if part.flat else part.spec.widths
    if isinstance(part, (BusIn, BusProbe)):
      return BUS, 1
    if isinstance(part, Wire):
      return None, None
    return (1,) * len(ends(part))

  def _widths(self, ) -> tuple[int, ...]:
    """How many bits each node carries, a bus joined to a single wire
    refused."""
    count = len(self.nodes)
    parent = [*range(count)]

    def find(node: int) -> int:
      while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
      return node

    for part in self.parts:
      if isinstance(part, Wire):
        parent[find(part.first)] = find(part.second)
    width = {}
    for part in self.parts:
      for node, wide in zip(ends(part), self.portWidths(part)):
        if wide is None:
          continue
        net = find(node)
        if width.setdefault(net, wide) != wide:
          raise ValueError('N%d joins a bus of four bits to a single '
                           'wire' % (node + 1))
    return (*[width.get(find(node), 1) for node in range(count)],)

  def _flat(self, ) -> Flat:
    """The circuit as it is reckoned."""
    widths = self.widths()
    parts = self.parts
    if all(wide == 1 for wide in widths):
      return Flat(self, (*[(n,) for n in range(len(self.nodes))],),
                  (*[(p,) for p in range(len(parts))],),
                  (*range(len(parts)),))
    nodes, mapped = [], []
    for node, wide in zip(self.nodes, widths):
      start = len(nodes)
      if wide == 1:
        nodes.append(node)
      else:
        nodes += [Node(node.x + 0.01 * (k + 1), node.y + 0.01 * (k + 1))
                  for k in range(wide)]
      mapped.append((*range(start, start + wide),))
    flat, made, owners = [], [], []
    for index, part in enumerate(parts):
      pieces = self._pieces(part, mapped)
      made.append((*range(len(flat), len(flat) + len(pieces)),))
      flat += pieces
      owners += [index] * len(pieces)
    circuit = Circuit((*nodes,), (*flat,))
    return Flat(circuit, (*mapped,), (*made,), (*owners,))

  @staticmethod
  def _pieces(part: Part, mapped: list) -> list:
    """The parts 'part' is when reckoned, its nodes as 'mapped'."""
    if isinstance(part, Wire):
      return [Wire(a, b) for a, b in zip(mapped[part.first],
                                         mapped[part.second])]
    if isinstance(part, BusIn):
      ground = mapped[part.second][0]
      return [Bit(node, ground, (part.value >> k) & 1 == 1,
                  '%s%d' % (part.name, k))
              for k, node in enumerate(mapped[part.first])]
    if isinstance(part, BusProbe):
      ground = mapped[part.second][0]
      return [Probe(node, ground, '%s%d' % (part.name, k))
              for k, node in enumerate(mapped[part.first])]
    if isinstance(part, Chip):
      pins = [node for pin in part.pins for node in mapped[pin]]
      return [Chip(part.kind, (*pins,), part.contents)]
    return [withEnds(part, [mapped[end][0] for end in ends(part)])]

  @staticmethod
  def _renumbered(gone: int) -> object:
    """What renumbers a part's nodes once the node of index 'gone' is
    no more."""

    def down(part: Part) -> Part:
      return withEnds(part, [end - (1 if end > gone else 0)
                             for end in ends(part)])

    return down

  @staticmethod
  def _cleaned(part: Part) -> Part:
    """'part' of numbers, refused if it is no part."""
    kind = type(part)
    if kind not in (*KINDS, *LOGIC, Chip):
      raise ValueError('a part is a wire, a source, a resistor, a lamp, '
                       'a capacitor, a coil, a switch, a meter, a diode, '
                       'a transistor, a logic part or a chip')
    if kind is Chip:
      if part.kind not in SPECS:
        raise ValueError('a chip is of a kind there is, not %r'
                         % (part.kind,))
      contents = (*[True if bit else False for bit in part.contents],)
      return Chip(str(part.kind), (*map(int, part.pins),), contents)
    joins = (*map(int, ends(part)),)
    if kind is Switch:
      return Switch(*joins, True if part.closed else False)
    if kind is Bit:
      return Bit(*joins, True if part.high else False, str(part.name))
    if kind is Probe:
      return Probe(*joins, str(part.name))
    if kind is BusIn:
      value = int(part.value)
      if not 0 <= value < 2 ** BUS:
        raise ValueError('a bus input is nought to fifteen, not %d'
                         % value)
      return BusIn(*joins, value, str(part.name))
    if kind is BusProbe:
      return BusProbe(*joins, str(part.name))
    return kind(*joins, *map(float, part[len(joins):]))

  @staticmethod
  def _checkNodes(nodes: tuple) -> None:
    """Raises unless the nodes are apart, each somewhere: no two at one
    place to a millionth."""
    seen = {}
    for index, node in enumerate(nodes):
      if not (math.isfinite(node.x) and math.isfinite(node.y)):
        raise ValueError('N%d is somewhere' % (index + 1))
      place = (round(node.x * 1e6), round(node.y * 1e6))
      if place in seen:
        infoSpec = """N%d and N%d are at the same place"""
        raise ValueError(infoSpec % (seen[place] + 1, index + 1))
      seen[place] = index

  @staticmethod
  def _checkParts(nodes: tuple, parts: tuple) -> None:
    """Raises unless each part joins two nodes there are, of the values
    it can have."""
    for part in parts:
      joins = ends(part)
      for end in joins:
        if not 0 <= end < len(nodes):
          raise ValueError('a part joins nodes there are, not N%d'
                           % (end + 1))
      if len(set(joins)) < len(joins) and not isinstance(part, Chip):
        raise ValueError('a part joins different nodes, not N%d to '
                         'itself' % (part.first + 1))
      if isinstance(part, Chip):
        spec = part.spec
        ports = len(spec.ins) + len(spec.outs)
        if len(joins) not in (ports, len(spec.inputs) + len(spec.outputs)):
          raise ValueError('a %s chip has %d pins' % (spec.name, ports))
        if part.contents and len(part.contents) != spec.memory:
          raise ValueError('a %s chip remembers %d bits' % (spec.name,
                                                            spec.memory))
        continue
      values = [v for v in part[len(joins):]
                if isinstance(v, float) and not isinstance(v, bool)]
      if not all(map(math.isfinite, values)):
        raise ValueError("""a part's values are numbers""")
      if isinstance(part, Source):
        if part.frequency < 0:
          raise ValueError("""a source's frequency is nought or more""")
        if part.resistance < 0:
          raise ValueError("""a source's resistance is nought or more""")
      elif not isinstance(part, (Wire, Switch, Ammeter, Voltmeter, Bit,
                                 Probe, BusIn, BusProbe)):
        if not all(v > 0 for v in values):
          names = {Resistor  : 'resistance', Capacitor: 'capacitance',
                   Coil      : 'inductance', Lamp: 'voltage and power',
                   Diode     : 'voltage', Led: 'voltage and current',
                   Transistor: 'gain', Clock: 'frequency'}
          raise ValueError("""a %s's %s is above nought"""
                           % (type(part).__name__.lower(),
                              names[type(part)]))
