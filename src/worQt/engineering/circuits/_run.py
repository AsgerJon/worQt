"""
Run is a circuit running, taken on through time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import itertools
import math
from typing import NamedTuple

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._circuit import Circuit, Flat
from ._network import Network, REGIONS, regionsOf, statesOf
from ._chips import HIGH, THRESHOLD, Chip
from ._parts import Bit, Clock, Probe, Wire, ends


class Energies(NamedTuple):
  """
  Energies are where the energy of a circuit running has gone, in J:
  what its sources have 'delivered', what its capacitors and coils hold,
  'stored', now, and what its resistances, diodes and transistors have
  turned to 'heat', and light. The 'balance', delivered less stored and
  heat, stays nought.
  """

  delivered: float
  stored: float
  heat: float

  @property
  def balance(self) -> float:
    """What the sources have delivered less what is stored and turned to
    heat: nought, the energy kept."""
    return self.delivered - self.stored - self.heat


class Sample(NamedTuple):
  """
  Sample is a circuit running at a 'time', in s: the voltage of each
  node, 'voltages', a bus node's 5 V times its number over fifteen; the
  current through each part, 'currents', nought through a part on
  buses; the current into each transistor's base, 'bases', nought for
  other parts; its 'energies'; and the number on each bus node,
  'values', 'None' at a single node.
  """

  time: float
  voltages: tuple[float, ...]
  currents: tuple[float, ...]
  bases: tuple[float, ...]
  energies: Energies
  values: tuple = ()


class Run(BaseObject):
  """
  Run is a 'circuit' running, 'time' seconds on: its capacitors charged
  and its coils carrying current as they are now, 'held', its sources
  where they are in their swings, and each diode and transistor in its
  region, 'regions'. 'advance' takes it on by as long as is asked,
  exactly, however long: between the moments a diode or a transistor
  turns, the circuit is linear and its 'network' solves it so; each
  such moment is found, to a part in a million million of the step,
  and the regions settled anew there, so a transistor turns on just as
  its base reaches 0.7 V. 'samples' are the run after each call, the
  last minute of it.

  'voltages', 'currents', 'bases' and 'drops' are the voltage of each
  node, the current through each part from its first node to its
  second, the current into each transistor's base, and the voltage
  across each part, its first node's over its second's, now; 'values'
  the number on each bus node. A circuit of buses is run as it is
  reckoned, 'flat', each bus node four nodes, and shown as it is
  drawn; 'charges'
  and 'baseCharges' the charge each part and each base has let through
  since the run began, 'energies' where the energy has gone.

  A run goes on in a circuit changed, 'Run(circuit, run)', its time and
  energies kept and each capacitor and coil still charged and carrying
  as it was, each diode and transistor in its region, found as the same
  part between the same nodes, or between nodes at the same places; one
  new starts uncharged and off. Its samples are kept while the circuit
  has as many nodes and parts. A circuit made of nothing starts
  uncharged at nought seconds: it is switched on then. A circuit that
  cannot be reckoned holds still.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_kept__ = 60.0  # s of samples kept
  __fallback_most_turns__ = 200  # turns a call to 'advance' finds at most
  __fallback_tries__ = 64  # rounds settling the regions at most
  __fallback_searched__ = 400  # regions tried searching at most
  __fallback_looks__ = (16, 512)  # looks a step for a turn, least, most
  __fallback_bisections__ = 48  # halvings finding a turn

  #  Private Variables
  __run_circuit__: Circuit | None = None
  __run_regions__: tuple | None = None
  __run_networks__: dict | None = None
  __run_held__: torch.Tensor | None = None
  __run_time__: float = 0.0
  __run_delivered__: float = 0.0
  __run_heat__: float = 0.0
  __run_charges__: torch.Tensor | None = None
  __run_base_charges__: torch.Tensor | None = None
  __run_samples__: list | None = None
  __logic_nets__: tuple | None = None
  __logic_known__: bool = False

  #  Virtual Variables
  circuit: Field[Circuit] = Field()
  flat: Field[Flat] = Field()
  network: Field[Network] = Field()
  problemPart: Field[int] = Field()
  values: Field[tuple] = Field()
  regions: Field[tuple] = Field()
  held: Field[torch.Tensor] = Field()
  time: Field[float] = Field()
  voltages: Field[tuple[float, ...]] = Field()
  currents: Field[tuple[float, ...]] = Field()
  bases: Field[tuple[float, ...]] = Field()
  drops: Field[tuple[float, ...]] = Field()
  charges: Field[tuple[float, ...]] = Field()
  baseCharges: Field[tuple[float, ...]] = Field()
  energies: Field[Energies] = Field()
  samples: Field[tuple[Sample, ...]] = Field()
  latest: Field[Sample] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @circuit.GET
  def _getCircuit(self, ) -> Circuit:
    """The 'circuit' getter returns the circuit running."""
    if self.__run_circuit__ is None:
      raise MissingVariable(self, '__run_circuit__', Circuit)
    return self.__run_circuit__

  @flat.GET
  def _getFlat(self, ) -> Flat:
    """The 'flat' getter returns the circuit as it is reckoned, each bus
    node four nodes."""
    return self.circuit.flat()

  @network.GET
  def _getNetwork(self, ) -> Network:
    """The 'network' getter returns the circuit reckoned, as it is
    reckoned, with its diodes and transistors in their regions now."""
    return self._networkOf(self.__run_regions__)

  @problemPart.GET
  def _getProblemPart(self, ) -> int | None:
    """The 'problemPart' getter returns the part of the circuit the
    problem it cannot be reckoned for is at, or 'None'."""
    index = self.network.problemPart
    return None if index is None else self.flat.owners[index]

  @values.GET
  def _getValues(self, ) -> tuple:
    """The 'values' getter returns the number on each bus node now, read
    from its bits, and 'None' at each single node."""
    return self.latest.values

  @regions.GET
  def _getRegions(self, ) -> tuple:
    """The 'regions' getter returns the region of each part now: of a
    diode 'off' or 'on', of a transistor 'off', 'active' or
    'saturated', of a chip its inputs' levels and what it remembers, of
    every other part 'None'."""
    regions = self.__run_regions__
    return (*[regions[pieces[0]] if pieces else None
              for pieces in self.flat.parts],)

  @held.GET
  def _getHeld(self, ) -> torch.Tensor:
    """The 'held' getter returns each capacitor's voltage, in V, and each
    coil's current, in A, in the order of the parts."""
    return self.__run_held__.clone()

  @time.GET
  def _getTime(self, ) -> float:
    """The 'time' getter returns the seconds the circuit has run."""
    return self.__run_time__

  @voltages.GET
  def _getVoltages(self, ) -> tuple[float, ...]:
    """The 'voltages' getter returns the voltage of each node now, in
    V."""
    return self.latest.voltages

  @currents.GET
  def _getCurrents(self, ) -> tuple[float, ...]:
    """The 'currents' getter returns the current through each part now,
    from its first node to its second, in A."""
    return self.latest.currents

  @bases.GET
  def _getBases(self, ) -> tuple[float, ...]:
    """The 'bases' getter returns the current into each transistor's
    base now, nought for other parts, in A."""
    return self.latest.bases

  @drops.GET
  def _getDrops(self, ) -> tuple[float, ...]:
    """The 'drops' getter returns the voltage across each part now, its
    first node's over its second's, in V."""
    voltages = self.voltages
    return (*[voltages[p.first] - voltages[p.second]
              for p in self.circuit.parts],)

  @charges.GET
  def _getCharges(self, ) -> tuple[float, ...]:
    """The 'charges' getter returns the charge each part has let
    through, from its first node to its second, in C; nought through a
    part on buses."""
    return self._single(self.__run_charges__.tolist())

  @baseCharges.GET
  def _getBaseCharges(self, ) -> tuple[float, ...]:
    """The 'baseCharges' getter returns the charge into each
    transistor's base so far, nought for other parts, in C."""
    return self._single(self.__run_base_charges__.tolist())

  @energies.GET
  def _getEnergies(self, ) -> Energies:
    """The 'energies' getter returns where the energy has gone."""
    return self.latest.energies

  @samples.GET
  def _getSamples(self, ) -> tuple[Sample, ...]:
    """The 'samples' getter returns the run after each call to
    'advance', the last minute of it."""
    return (*self.__run_samples__,)

  @latest.GET
  def _getLatest(self, ) -> Sample:
    """The 'latest' getter returns the run as it is now."""
    return self.__run_samples__[-1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Circuit, object)
  def __init__(self, circuit: Circuit, run: Run) -> None:
    old = run.circuit
    self.__run_circuit__ = circuit
    self.__run_networks__ = {}
    flat, oldFlat = circuit.flat(), run.flat
    regions = [*regionsOf(flat.circuit)]
    states = statesOf(flat.circuit)
    count = len(flat.circuit.parts)
    held = torch.zeros(len(states)).double()
    charges = torch.zeros(count).double()
    baseCharges = torch.zeros(count).double()
    oldHeld, oldStates = run.held, run.network.states
    oldCharges = run.__run_charges__.tolist()
    oldBases = run.__run_base_charges__.tolist()
    oldRegions = run.__run_regions__
    for index in range(len(circuit.parts)):
      before = self._found(circuit, index, old)
      if before is None:
        continue
      for piece, was in zip(flat.parts[index], oldFlat.parts[before]):
        charges[piece] = oldCharges[was]
        baseCharges[piece] = oldBases[was]
        regions[piece] = oldRegions[was]
        if piece in states:
          held[states.index(piece)] = oldHeld[oldStates.index(was)]
    self.__run_held__ = held
    self.__run_time__ = run.time
    self.__run_delivered__ = run.energies.delivered
    self.__run_heat__ = run.energies.heat
    self.__run_charges__ = charges
    self.__run_base_charges__ = baseCharges
    self.__run_samples__ = []
    if (len(circuit.nodes), len(circuit.parts)) == (len(old.nodes),
                                                     len(old.parts)):
      self.__run_samples__ = [*run.samples]
    self.__run_regions__ = self._settled((*regions,))
    self._sample()

  @overload(Circuit)
  def __init__(self, circuit: Circuit) -> None:
    self.__run_circuit__ = circuit
    self.__run_networks__ = {}
    flat = circuit.flat().circuit
    regions = regionsOf(flat)
    self.__run_held__ = torch.zeros(len(statesOf(flat))).double()
    self.__run_charges__ = torch.zeros(len(flat.parts)).double()
    self.__run_base_charges__ = torch.zeros(len(flat.parts)).double()
    self.__run_samples__ = []
    self.__run_regions__ = self._settled(self._propagated(regions, False))
    self._sample()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def advance(self, seconds: float) -> float:
    """The 'advance' method takes the run on 'seconds', exactly, each
    diode and transistor turning when it must, and returns how far it
    went: nought if the circuit cannot be reckoned."""
    if self.network.problem or not seconds > 0:
      return 0.0
    left = float(seconds)
    turns = 0
    while left > 0:
      network = self.network
      found = None
      if turns < self.__fallback_most_turns__:
        found = self._firstTurn(network, left)
      if found is None:
        self._take(network, left)
        break
      self._take(network, found)
      left -= found
      turns += 1
      self.__run_regions__ = self._settled(self.__run_regions__)
    self._sample()
    return float(seconds)

  def state(self, ) -> torch.Tensor:
    """The 'state' method returns the whole state now: the capacitors'
    voltages and the coils' currents, then the sources' swings."""
    return self.network.stateAt(self.__run_held__, self.__run_time__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _networkOf(self, regions: tuple) -> Network:
    """The circuit reckoned with its parts in 'regions', kept for when
    they come again."""
    kept = self.__run_networks__
    if regions not in kept:
      kept[regions] = Network(self.flat.circuit, regions)
    return kept[regions]

  def _settled(self, regions: tuple) -> tuple:
    """The regions that hold for the state now, and do not grow of
    themselves, found from 'regions': first, in a circuit of logic
    alone, each chip's inputs read off the levels driving them, without
    reckoning it; then each part whose region fails turned, all at once,
    until none fails, one at a time if that comes round again; or else
    the nearest that hold, fewest parts turned first, a stable one
    before one that is not."""
    turned = self._turned(self._propagated(regions, True))
    if self._holds(turned) and not self._networkOf(turned).unstable():
      return turned
    return self._searched(turned) or turned

  def _holds(self, regions: tuple) -> bool:
    """Whether 'regions' hold for the state now."""
    network = self._networkOf(regions)
    if network.problem:
      return True
    state = network.stateAt(self.__run_held__, self.__run_time__)
    return False if network.violations(state) else True

  def _turned(self, regions: tuple) -> tuple:
    """The regions found from 'regions' by turning each part whose region
    fails, all at once, until none fails; one at a time, the worst
    first, if that comes round again."""
    held, time = self.__run_held__, self.__run_time__
    seen = set()
    single = False
    for _ in range(self.__fallback_tries__):
      network = self._networkOf(regions)
      if network.problem:
        return regions
      state = network.stateAt(held, time)
      failed = network.violations(state)
      if not failed:
        return regions
      seen.add(regions)
      chosen = [*failed]
      if single:
        chosen = [max((amount, index) for index, amount in
                      failed.items())[1]]
      turned = [*regions]
      for index in chosen:
        turned[index] = network.turned(state, index)
      turned = (*turned,)
      if turned in seen and not single:
        single = True
        continue
      regions = turned
    return regions

  def _logicNets(self, ) -> tuple | None:
    """The net of each node of the circuit reckoned, nodes joined by
    wires, and the net of its ground, if it is logic alone: wires, logic
    inputs, probes, clocks and chips, the minus pole of every input and
    clock on the ground; else 'None'."""
    if self.__logic_known__:
      return self.__logic_nets__
    self.__logic_known__ = True
    circuit = self.flat.circuit
    parent = [*range(len(circuit.nodes))]

    def find(node: int) -> int:
      while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
      return node

    for part in circuit.parts:
      if not isinstance(part, (Wire, Bit, Probe, Clock, Chip)):
        return None
      if isinstance(part, Wire):
        parent[find(part.first)] = find(part.second)
    sources = [p for p in circuit.parts if isinstance(p, (Bit, Clock))]
    if not sources:
      return None
    ground = find(sources[0].second)
    if any(find(source.second) != ground for source in sources):
      return None
    self.__logic_nets__ = (*map(find, range(len(circuit.nodes))),), ground
    return self.__logic_nets__

  def _driven(self, regions: tuple) -> dict | None:
    """The level each driven net of a circuit of logic alone is at, its
    parts in 'regions': the ground low, each logic input's and clock's
    plus pole as it is set, each chip's outputs as its logic gives them;
    'None' if two drive a net apart."""
    netOf, ground = self.__logic_nets__
    levels = {ground: False}
    for index, part in enumerate(self.flat.circuit.parts):
      driven = ()
      if isinstance(part, Bit):
        driven = ((part.first, part.high),)
      elif isinstance(part, Clock):
        driven = ((part.first, regions[index] == 'high'),)
      elif isinstance(part, Chip):
        before, memory = regions[index]
        driven = zip(part.outputs, part.spec.logic(before, memory))
      for node, high in driven:
        high = True if high else False
        if levels.setdefault(netOf[node], high) != high:
          return None
    return levels

  def _propagated(self, regions: tuple, edges: bool) -> tuple:
    """The regions found from 'regions' in a circuit of logic alone, each
    chip's inputs read off the levels driving them, a net nothing drives
    low, all at once, until none turns; 'regions' as they are if the
    circuit is not logic alone, two drive a net apart, or it does not
    settle. The circuit reckoned then only confirms them. Without
    'edges', as it is switched on, a chip takes the levels it reads as
    they are, none of them turning: a flip-flop's clock already high has
    not risen, a latch's input high still sets it."""
    if self._logicNets() is None:
      return regions
    netOf, _ = self.__logic_nets__
    parts = self.flat.circuit.parts
    current = [*regions]
    for _ in range(self.__fallback_tries__):
      levels = self._driven((*current,))
      if levels is None:
        return regions
      turned = False
      for index, part in enumerate(parts):
        if not isinstance(part, Chip):
          continue
        before, memory = current[index]
        after = (*[levels.get(netOf[node], False)
                   for node in part.inputs],)
        if after != before:
          was = before if edges else after
          memory = (*part.spec.remember(was, after, memory),)
          current[index] = (after, memory)
          turned = True
      if not turned:
        return (*current,)
    return regions

  def _searched(self, regions: tuple) -> tuple | None:
    """The regions nearest 'regions' that hold for the state now, the
    fewest parts turned first, at most so many tried: the first stable
    one, else the first, else 'None'."""
    parts = self.flat.circuit.parts
    turnable = [i for i, part in enumerate(parts) if type(part) in REGIONS]
    fallback = None
    tried = 0
    for count in range(1, len(turnable) + 1):
      for chosen in itertools.combinations(turnable, count):
        others = [[r for r in REGIONS[type(parts[i])] if r != regions[i]]
                  for i in chosen]
        for picked in itertools.product(*others):
          tried += 1
          if tried > self.__fallback_searched__:
            return fallback
          trial = [*regions]
          for index, region in zip(chosen, picked):
            trial[index] = region
          trial = (*trial,)
          if not self._holds(trial):
            continue
          if not self._networkOf(trial).unstable():
            return trial
          fallback = fallback or trial
    return fallback

  def _looks(self, network: Network, seconds: float) -> int:
    """How many times to look for a turn over 'seconds': more for an
    alternating source, so a diode's moment at each peak is not
    missed."""
    least, most = self.__fallback_looks__
    parts = self.flat.circuit.parts
    fastest = max([parts[i].frequency for i in network.alternating]
                  + [0.0])
    return int(min(max(least, math.ceil(64 * seconds * fastest)), most))

  def _firstTurn(self, network: Network, seconds: float) -> float | None:
    """When, within 'seconds', a part first fails its region, just
    after, by twice what it may miss by so it fails when looked at anew,
    or 'None' if none does."""
    start = self.state()
    if not len(network.conditions(start)) or network.violations(start):
      return None
    change = network.change()
    count = self._looks(network, seconds)
    short = seconds / count
    taken = torch.linalg.matrix_exp(change * short)
    states = [start]
    for _ in range(count):
      states.append(taken @ states[-1])
    values = network.conditions(torch.stack(states))
    looks = network.failing(values, 2.0).any(1).tolist()
    if not any(looks):
      return None
    first = looks.index(True)
    base = states[first - 1]
    low, high = 0.0, short
    for _ in range(self.__fallback_bisections__):
      middle = 0.5 * (low + high)
      moved = torch.linalg.matrix_exp(change * middle) @ base
      if network.failing(network.conditions(moved), 2.0).any():
        high = middle
      else:
        low = middle
    return (first - 1) * short + high

  def _take(self, network: Network, seconds: float) -> None:
    """Takes the run on 'seconds' as 'network' has it, adding up the
    heat, the energy delivered and the charges let through."""
    state = network.stateAt(self.__run_held__, self.__run_time__)
    taken, integral, heat, supply = network.step(float(seconds))
    self.__run_heat__ += float(state @ heat @ state)
    self.__run_delivered__ += float(state @ supply @ state)
    flowed = integral @ state
    self.__run_charges__ = self.__run_charges__ + network.currents(flowed)
    self.__run_base_charges__ = (self.__run_base_charges__
                                 + network.bases(flowed))
    after = taken @ state
    self.__run_held__ = after[:len(network.states)]
    self.__run_time__ += float(seconds)

  @staticmethod
  def _found(circuit: Circuit, index: int, old: Circuit) -> int | None:
    """The part of 'old' the part of 'index' in 'circuit' is: of the same
    kind, between the same nodes or between nodes at the same places."""
    part = circuit.parts[index]

    def alike(before: tuple) -> bool:
      if type(before) is not type(part):
        return False
      if not isinstance(part, Chip):
        return True
      return (before.kind, before.contents) == (part.kind, part.contents)

    if index < len(old.parts):
      before = old.parts[index]
      if alike(before) and ends(before) == ends(part):
        return index
    places = (*[circuit.nodes[end] for end in ends(part)],)
    for other, before in enumerate(old.parts):
      if not alike(before):
        continue
      if (*[old.nodes[end] for end in ends(before)],) == places:
        return other
    return None

  def _single(self, values: list) -> tuple[float, ...]:
    """Of 'values', one a part as it is reckoned, the value of each part
    of the circuit: its own, nought for a part on buses."""
    return (*[values[pieces[0]] if len(pieces) == 1 else 0.0
              for pieces in self.flat.parts],)

  def _sample(self, ) -> None:
    """Notes the run as it is now, forgetting what is older than a
    minute."""
    network = self.network
    flat = self.flat
    state = self.state()
    solution = network.solution(state).tolist()
    count = len(flat.circuit.nodes)
    parts = len(flat.circuit.parts)
    energies = Energies(self.__run_delivered__, network.stored(state),
                        self.__run_heat__)
    voltages, values = [], []
    for pieces in flat.nodes:
      if len(pieces) == 1:
        voltages.append(solution[pieces[0]])
        values.append(None)
        continue
      value = sum(1 << k for k, node in enumerate(pieces)
                  if solution[node] > THRESHOLD)
      voltages.append(HIGH * value / (2 ** len(pieces) - 1))
      values.append(value)
    samples = self.__run_samples__
    samples.append(Sample(
      self.__run_time__, (*voltages,),
      self._single(solution[count:count + parts]),
      self._single(network.bases(state).tolist()), energies,
      (*values,)))
    kept = self.__fallback_kept__
    while samples and samples[0].time < self.__run_time__ - kept:
      del samples[0]
