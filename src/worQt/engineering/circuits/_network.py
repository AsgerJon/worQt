"""
Network is a circuit reckoned, its diodes and transistors each in a
region: the linear equations it keeps, solved for how it changes in
time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from .._doubles import doubles
from ._chips import HIGH, HYSTERESIS, THRESHOLD, Chip
from ._circuit import Circuit
from ._parts import Ammeter, Bit, Capacitor, Clock, Coil, Diode, Lamp, Led
from ._parts import Probe, Resistor, Source, Switch, Transistor
from ._parts import Voltmeter, Wire, ends

#  The regions each kind of part with them may be in, the first when it
#  is switched on
REGIONS = {
  Diode     : ('off', 'on'),
  Led       : ('off', 'on'),
  Transistor: ('off', 'active', 'saturated'),
}


class _Joins:
  """The nodes joined so far, each set named by one of them."""

  def __init__(self, count: int) -> None:
    self.parent = [*range(count)]

  def find(self, node: int) -> int:
    """The node naming the set 'node' is in."""
    while self.parent[node] != node:
      self.parent[node] = self.parent[self.parent[node]]
      node = self.parent[node]
    return node

  def join(self, first: int, second: int) -> bool:
    """Joins the sets of 'first' and 'second', and tells whether they
    were apart."""
    a, b = self.find(first), self.find(second)
    if a == b:
      return False
    self.parent[max(a, b)] = min(a, b)
    return True


_DOUBLE = doubles([0.0])  # a float64 tensor, to make others like it


def _zeros(rows: int, columns: int) -> torch.Tensor:
  """A float64 matrix of noughts, made so at once."""
  return _DOUBLE.new_zeros((rows, columns))


def statesOf(circuit: Circuit) -> tuple[int, ...]:
  """The 'statesOf' function returns the parts of 'circuit' holding a
  state: each capacitor, its voltage, and each coil, its current, in the
  order of the parts."""
  return (*[i for i, p in enumerate(circuit.parts)
            if isinstance(p, (Capacitor, Coil))],)


def startOf(part: tuple) -> object:
  """The 'startOf' function returns the region 'part' is switched on in:
  a diode or a transistor off; a clock high; a chip its inputs read low,
  remembering its contents, a ROM its program, or nothing set; any
  other part 'None'."""
  if type(part) in REGIONS:
    return REGIONS[type(part)][0]
  if isinstance(part, Clock):
    return 'high'
  if isinstance(part, Chip):
    spec = part.spec
    memory = part.contents or (False,) * spec.memory
    return ((False,) * len(spec.inputs), (*memory,))
  return None


def _putter(entries: list) -> object:
  """What puts a weight at a row and a column of a matrix, adding to
  what is there, by keeping it in 'entries'."""

  def put(row: int, column: int, weight: float) -> None:
    entries.append((row, column, weight))

  return put


def regionsOf(circuit: Circuit) -> tuple:
  """The 'regionsOf' function returns the regions a circuit is switched
  on in, each part's as 'startOf' has it."""
  return (*map(startOf, circuit.parts),)


def _valid(part: tuple, region: object) -> bool:
  """Whether 'part' may be in 'region'."""
  if isinstance(part, Clock):
    return region in ('high', 'low')
  if isinstance(part, Chip):
    spec = part.spec
    try:
      levels, memory = region
    except (TypeError, ValueError):
      return False
    return (len(levels) == len(spec.inputs)
            and len(memory) == spec.memory)
  return region in REGIONS.get(type(part), (None,))


class Network(BaseObject):
  """
  Network is a 'circuit' reckoned exactly, each diode and transistor in
  a region, 'regions'. Its unknowns are the voltage of each node, the
  current through each part, from its first node to its second, a
  transistor's into its collector, and each transistor's base current;
  its equations Kirchhoff's current law at each node and each part's
  own law: Ohm's for a resistor, a lamp and a source's internal
  resistance, a wire, a closed switch and an ammeter keeping their
  nodes at one voltage, an open switch and a voltmeter taking no
  current. In each piece of the circuit joined together, one node is
  nought volts: the minus pole of its first source, else its first
  node.

  A chip's region is the levels its inputs read and the bits it
  remembers: its outputs are sources from the ground, 'ground', behind
  10 Ω, of 5 V or nought as its spec's logic says; each input holds its
  level until it passes 2.5 V by 0.1 V, when 'turned' reads them anew
  and the chip remembers as its spec says, a flip-flop taking D as its
  clock rises. A clock is 'high' while the sine of its ticking is
  positive, 'low' while it is negative. A bit is a source of 5 V or
  nought, a probe a voltmeter.

  A diode, or a light emitting diode, is 'off', taking no current, or
  'on', keeping its voltage, behind a tenth of an ohm. A transistor is
  'off', taking nothing; 'active', its base to emitter a diode of 0.7
  V, its collector current its gain times its base current; or
  'saturated', fully on, 0.2 V from collector to emitter. Each region
  holds so long as its 'conditions' stay at nought or above: an off
  diode's voltage below its own, an on diode's current forward, an off
  transistor's base below 0.7 V, an active one's base current forward
  and its collector above 0.2 V, a saturated one's base current
  forward and its collector current short of its gain times it.
  'violations' says which fail and 'turned' where each goes; 'unstable'
  whether the regions grow of themselves away from where they are, as
  two transistors both active, each driving the other, do; 'Run' moves
  them on.

  What it holds is its 'states': the voltage of each capacitor and the
  current through each coil. Given them, and the sources at a time, the
  rest follows at once; and they change as their currents and voltages
  say, a linear system of equations, the sources' own swings joined to
  it. That is solved exactly, by the matrix exponential, so nothing
  depends on a step: an ideal oscillating circuit swings for ever, a
  capacitor charges along E (1 - exp(-t / RC)) to the digit.

  A source's poles joined by wire alone, with no internal resistance,
  is a short circuit, which cannot be reckoned: 'problem' says so, and
  'problemPart' is the source. A capacitor across an ideal source or a
  wire, which would charge at once, is given a resistance of a tenth
  of a milliohm, and a coil with nowhere else for its current, which would
  stop it at once, a gigaohm across it; so they do, the energy lost as
  it is. An active transistor has a gigaohm from collector to emitter.

  'modes' are how the circuit settles or swings of itself: each a time
  constant, as RC or L / R, and a frequency, nought unless it swings, as
  1 / (2 pi sqrt(LC)).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_tiny__ = 1e-4  # Ω in a capacitor joined straight to a source
  __fallback_leak__ = 1e9  # Ω across a coil with nowhere for its current
  __fallback_on__ = 0.1  # Ω behind a diode's or a junction's voltage
  __fallback_junction__ = 0.7  # V base to emitter, on
  __fallback_output__ = 10.0  # Ω behind a chip's output
  __fallback_saturation__ = 0.2  # V collector to emitter, fully on
  __fallback_quickest__ = 1e-6  # s: modes quicker are at once, not shown
  __fallback_kept_steps__ = 8  # steps whose solutions are kept
  __fallback_slack__ = (1e-9, 1e-12)  # V and A a condition may miss by

  #  Private Variables
  __network_circuit__: Circuit | None = None
  __network_regions__: tuple | None = None
  __network_problem__: tuple[str, int] | None = None
  __network_kept__: dict | None = None

  #  Virtual Variables
  circuit: Field[Circuit] = Field()
  regions: Field[tuple] = Field()
  problem: Field[str] = Field()
  problemPart: Field[int] = Field()
  states: Field[tuple[int, ...]] = Field()
  alternating: Field[tuple[int, ...]] = Field()
  transistors: Field[tuple[int, ...]] = Field()
  size: Field[int] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @circuit.GET
  def _getCircuit(self, ) -> Circuit:
    """The 'circuit' getter returns the circuit reckoned."""
    if self.__network_circuit__ is None:
      raise MissingVariable(self, '__network_circuit__', Circuit)
    return self.__network_circuit__

  @regions.GET
  def _getRegions(self, ) -> tuple:
    """The 'regions' getter returns the region of each part: of a diode
    'off' or 'on', of a transistor 'off', 'active' or 'saturated', of
    every other part 'None'."""
    return self.__network_regions__

  @problem.GET
  def _getProblem(self, ) -> str:
    """The 'problem' getter returns why the circuit cannot be reckoned,
    or nothing."""
    return self.__network_problem__[0] if self.__network_problem__ else ''

  @problemPart.GET
  def _getProblemPart(self, ) -> int | None:
    """The 'problemPart' getter returns the part the problem is at, or
    'None'."""
    return self.__network_problem__[1] if self.__network_problem__ else None

  @states.GET
  def _getStates(self, ) -> tuple[int, ...]:
    """The 'states' getter returns the parts holding a state: each
    capacitor, its voltage, and each coil, its current, in the order of
    the parts."""
    return self._kept('states')

  @alternating.GET
  def _getAlternating(self, ) -> tuple[int, ...]:
    """The 'alternating' getter returns the sources of a frequency above
    nought, in the order of the parts."""
    return self._kept('alternating')

  @transistors.GET
  def _getTransistors(self, ) -> tuple[int, ...]:
    """The 'transistors' getter returns the transistors, in the order of
    the parts, each with its base current an unknown after the parts'
    currents."""
    return self._kept('transistors')

  @size.GET
  def _getSize(self, ) -> int:
    """The 'size' getter returns how many numbers the circuit's state
    is: one a state, one for the steady sources and two for each
    alternating source, its sine and its cosine."""
    return self._kept('size')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Circuit, tuple)
  def __init__(self, circuit: Circuit, regions: tuple) -> None:
    if len(regions) != len(circuit.parts):
      raise ValueError('a network has a region for each part')
    for part, region in zip(circuit.parts, regions):
      if not _valid(part, region):
        raise ValueError('%s is never %s' % (type(part).__name__,
                                             region))
    self.__network_circuit__ = circuit
    self.__network_regions__ = (*regions,)
    self.__network_kept__ = {}
    self._build()

  @overload(Circuit)
  def __init__(self, circuit: Circuit) -> None:
    self.__init__(circuit, regionsOf(circuit))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stateAt(self, held: torch.Tensor, time: float) -> torch.Tensor:
    """The 'stateAt' method returns the whole state at 'time' s, the
    capacitors' voltages and the coils' currents 'held': those, then
    nought volts' worth of steady source, one, then each alternating
    source's sine and cosine at that time."""
    swings = []
    for index in self._kept('alternating'):
      turn = 2 * math.pi * self._kept('parts')[index].frequency * time
      swings += [math.sin(turn), math.cos(turn)]
    tail = doubles([1.0, *swings])
    return torch.cat((held.double(), tail))

  def solution(self, state: torch.Tensor) -> torch.Tensor:
    """The 'solution' method returns every unknown for 'state': the
    voltage of each node, the current through each part, then each
    transistor's base current."""
    if self.problem:
      return torch.zeros(self._unknowns()).double()
    return self._kept('solve') @ state

  def voltages(self, state: torch.Tensor) -> torch.Tensor:
    """The 'voltages' method returns the voltage of each node, in V, for
    'state'."""
    return self.solution(state)[:len(self.circuit.nodes)]

  def currents(self, state: torch.Tensor) -> torch.Tensor:
    """The 'currents' method returns the current through each part, from
    its first node to its second, in A, for 'state'."""
    nodes, parts = len(self.circuit.nodes), len(self._kept('parts'))
    return self.solution(state)[nodes:nodes + parts]

  def bases(self, state: torch.Tensor) -> torch.Tensor:
    """The 'bases' method returns the current into the base of each
    part, nought but for a transistor, in A, for 'state'."""
    out = torch.zeros(len(self._kept('parts'))).double()
    solution = self.solution(state)
    for index in self._kept('transistors'):
      out[index] = solution[self._extra(index)[0]]
    return out

  def levels(self, state: torch.Tensor, index: int) -> tuple[bool, ...]:
    """The 'levels' method returns the levels the inputs of the chip of
    'index' read for 'state', each turning only past the threshold by
    the hysteresis from the level its region has."""
    part = self._kept('parts')[index]
    voltages = self.voltages(state)
    ground = self._kept('ground')
    ground = float(voltages[ground]) if ground is not None else 0.0
    before, _ = self.__network_regions__[index]
    out = []
    for node, high in zip(part.inputs, before):
      level = float(voltages[node]) - ground
      edge = THRESHOLD - HYSTERESIS if high else THRESHOLD + HYSTERESIS
      out.append(True if level > edge else False)
    return (*out,)

  def stored(self, state: torch.Tensor) -> float:
    """The 'stored' method returns the energy the capacitors and coils
    hold, in J, for 'state': C U² / 2 and L I² / 2."""
    if self.problem:
      return 0.0
    quadratic = self._kept('store')
    return float(state @ quadratic @ state)

  def conditions(self, state: torch.Tensor) -> torch.Tensor:
    """The 'conditions' method returns how far each condition of the
    regions is from failing, for 'state' or for states in its rows,
    each at nought or above while the regions hold."""
    if self.problem:
      return torch.zeros(0).double()
    return state @ self._kept('conditions').T

  def failing(self, values: torch.Tensor,
              times: float = 1.0) -> torch.Tensor:
    """The 'failing' method returns, for conditions 'values', whether
    each fails by more than 'times' what it may miss by, or is no number
    at all."""
    return torch.logical_not(values >= -times * self._kept('slack'))

  def unstable(self, ) -> bool:
    """The 'unstable' method tells whether the circuit, its parts in
    their regions, has a mode growing of itself: two transistors both
    active, each driving the other, which no real circuit keeps."""
    if self.problem or not self._kept('states'):
      return False
    count = len(self._kept('states'))
    rates = torch.linalg.eigvals(self._kept('change')[:count, :count])
    growth = float(rates.real.max())
    return True if growth > 1e-9 * max(1.0, float(rates.abs().max())) \
      else False

  def violations(self, state: torch.Tensor) -> dict:
    """The 'violations' method returns the parts whose region fails for
    'state', each with how many times what it may miss by its worst
    condition fails by: a dict of part to amount."""
    if self.problem:
      return {}
    out = {}
    values = self.conditions(state).tolist()
    slack = self._kept('slack').tolist()
    for value, room, (index, _) in zip(values, slack,
                                       self._kept('owners')):
      if value < -room:
        out[index] = max(out.get(index, 0.0), -value / room)
    return out

  def turned(self, state: torch.Tensor, index: int) -> str:
    """The 'turned' method returns the region the part of 'index' goes
    to from its own when it fails, for 'state': a diode off goes on and
    on goes off; a transistor off goes active; active, off if its base
    current turns back, else saturated; saturated, off if its base
    current turns back, else active."""
    region = self.__network_regions__[index]
    part = self._kept('parts')[index]
    if isinstance(part, Clock):
      return 'low' if region == 'high' else 'high'
    if isinstance(part, Chip):
      before, memory = region
      after = self.levels(state, index)
      return after, (*part.spec.remember(before, after, memory),)
    if not isinstance(part, Transistor):
      return 'on' if region == 'off' else 'off'
    if region == 'off':
      return 'active'
    base = float(self.bases(state)[index])
    if base < -self.__fallback_slack__[1]:
      return 'off'
    return 'saturated' if region == 'active' else 'active'

  def modes(self, ) -> tuple[tuple[float, float], ...]:
    """The 'modes' method returns how the circuit settles or swings of
    itself, the slowest first: each a time constant, in s, infinite if
    it never settles, and a frequency, in Hz, nought unless it swings;
    those quicker than a microsecond, as at once, left out."""
    if self.problem or not self._kept('states'):
      return ()
    count = len(self._kept('states'))
    rates = torch.linalg.eigvals(self._kept('change')[:count, :count])
    out = []
    for rate in rates.tolist():
      if rate.imag < -1e-9 * max(abs(rate), 1.0):
        continue
      decay = -rate.real
      tau = math.inf
      if abs(decay) > 1e-9 * max(abs(rate), 1.0):
        tau = 1.0 / decay
      if tau < self.__fallback_quickest__:
        continue
      out.append((tau, max(rate.imag, 0.0) / (2 * math.pi)))
    return (*sorted(out)[::-1],)

  def change(self, ) -> torch.Tensor:
    """The 'change' method returns the matrix the whole state changes
    by: its rate of change is this times it."""
    if self.problem:
      return _zeros(self._kept('size'), self._kept('size'))
    return self._kept('change')

  def step(self, seconds: float) -> tuple[torch.Tensor, ...]:
    """The 'step' method returns what 'seconds' s does to a state, all
    exactly: the matrix taking it on, the one giving the integral of the
    state over the step, and those giving the heat made and the energy
    the sources deliver over it from where it began."""
    kept = self.__network_kept__.setdefault('steps', {})
    if seconds not in kept:
      if len(kept) >= self.__fallback_kept_steps__:
        kept.clear()
      kept[seconds] = self._step(seconds)
    return kept[seconds]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _kept(self, name: str) -> object:
    """What the network keeps of 'name'."""
    return self.__network_kept__[name]

  def _build(self, ) -> None:
    """Finds what holds a state and what each part is, then solves the
    equations for the unknowns and for how the states change."""
    parts = self.circuit.parts
    kept = self.__network_kept__
    kept['parts'] = parts
    kept['nodes'] = len(self.circuit.nodes)
    kept['states'] = statesOf(self.circuit)
    kept['alternating'] = (*[
      i for i, p in enumerate(parts)
      if isinstance(p, Clock) or (isinstance(p, Source) and p.frequency > 0)
    ],)
    kept['transistors'] = (*[i for i, p in enumerate(parts)
                             if isinstance(p, Transistor)],)
    kept['size'] = len(kept['states']) + 1 + 2 * len(kept['alternating'])
    extras, at = {}, len(self.circuit.nodes) + len(parts)
    for index, part in enumerate(parts):
      count = 1 if isinstance(part, Transistor) else 0
      if isinstance(part, Chip):
        count = len(part.spec.outputs)
      extras[index] = (*range(at, at + count),)
      at += count
    kept['extras'] = extras
    kept['unknowns'] = at
    kept['ground'] = None
    for part in parts:
      if isinstance(part, (Source, Bit, Clock)):
        kept['ground'] = part.second
        break
    if kept['ground'] is None and self.circuit.nodes:
      kept['ground'] = 0
    roles = self._roles()
    if self.__network_problem__ is not None:
      return
    try:
      self._solve(roles)
    except RuntimeError:
      self.__network_problem__ = ('the circuit cannot be reckoned', None)

  def _opened(self, ) -> set:
    """The parts taking no current: voltmeters, open switches, diodes
    and transistors off."""
    opened = set()
    for index, part in enumerate(self._kept('parts')):
      if isinstance(part, (Voltmeter, Probe, Chip)):
        opened.add(index)
      if self.__network_regions__[index] == 'off':
        opened.add(index)
      if isinstance(part, Switch) and not part.closed:
        opened.add(index)
    return opened

  def _roles(self, ) -> dict:
    """What each part is in the equations: 'open', taking no current,
    'tiny', the capacitors given a tenth of a milliohm, and 'leak', the
    coils given a gigaohm across them; and 'grounds', the node of each
    piece that is nought volts. Notes a short circuit as the problem."""
    circuit = self.circuit
    parts, count = circuit.parts, len(circuit.nodes)
    opened, tiny, leak = self._opened(), set(), set()
    ideal = _Joins(count)
    for kind in (Wire, Switch, Ammeter):
      for index, part in enumerate(parts):
        if type(part) is kind and index not in opened:
          if not ideal.join(part.first, part.second):
            opened.add(index)
    for index, part in enumerate(parts):
      ideally = isinstance(part, (Bit, Clock))
      if ideally or (isinstance(part, Source) and part.resistance == 0):
        if not ideal.join(part.first, part.second):
          words = """%s's poles are joined with nothing to resist the
          current"""
          words = ' '.join(words.split())
          self.__network_problem__ = (words % circuit.label(index), index)
          return {}
    for index, part in enumerate(parts):
      if isinstance(part, Capacitor):
        if not ideal.join(part.first, part.second):
          tiny.add(index)
    joined = _Joins(count)
    for index, part in enumerate(parts):
      if isinstance(part, Chip):
        for node in part.outputs:
          joined.join(self._kept('ground'), node)
      if index in opened or isinstance(part, Coil):
        continue
      joins = ends(part)
      for end in joins[1:]:
        joined.join(joins[0], end)
    for index, part in enumerate(parts):
      if isinstance(part, Coil):
        if joined.join(part.first, part.second):
          leak.add(index)
    grounds = {}
    for index, part in enumerate(parts):
      if isinstance(part, (Source, Bit, Clock)):
        grounds.setdefault(joined.find(part.second), part.second)
    for node in range(count):
      grounds.setdefault(joined.find(node), node)
    return {'open' : opened, 'tiny': tiny, 'leak': leak,
            'grounds': set(grounds.values())}

  def _unknowns(self, ) -> int:
    """How many unknowns there are: a voltage a node, a current a part,
    a base current a transistor and a current out of each output of a
    chip."""
    return self._kept('unknowns')

  def _extra(self, index: int) -> tuple[int, ...]:
    """The unknowns the part of 'index' has besides its current: a
    transistor's base current, a chip's currents out of its outputs."""
    return self._kept('extras')[index]

  @property
  def ground(self) -> int | None:
    """The node chips drive their outputs from and read their inputs
    over: the minus pole of the first source, else the first node."""
    return self.__network_kept__['ground']

  def _equations(self, roles: dict) -> tuple[torch.Tensor, list]:
    """The equations' matrix: Kirchhoff's current law at each node but
    the grounds, nought volts there, then each part's law, then each
    transistor's base; and the voltages the regions keep, each a row and
    how many volts."""
    circuit = self.circuit
    nodes, parts = len(circuit.nodes), circuit.parts
    size = self._unknowns()
    entries = []
    put = _putter(entries)
    kept = []
    for node in roles['grounds']:
      put(node, node, 1.0)
    for index, part in enumerate(parts):
      current = nodes + index
      for end, sign in ((part.first, 1.0), (part.second, -1.0)):
        if end not in roles['grounds']:
          put(end, current, sign)
      row, a, b = nodes + index, part.first, part.second
      if isinstance(part, Chip):
        put(row, current, 1.0)
        self._chipRows(put, index, roles)
      elif isinstance(part, Transistor):
        kept += self._transistorRows(put, index, roles)
      elif index in roles['open']:
        put(row, current, 1.0)
      elif isinstance(part, Coil):
        put(row, current, 1.0)
        if index in roles['leak']:
          conductance = 1.0 / self.__fallback_leak__
          put(row, a, -conductance)
          put(row, b, conductance)
      else:
        put(row, a, 1.0)
        put(row, b, -1.0)
        put(row, current, -self._resistance(index, roles))
        if isinstance(part, (Diode, Led)):
          kept.append((row, part.voltage))
    rows = torch.tensor([e[0] for e in entries]).long()
    columns = torch.tensor([e[1] for e in entries]).long()
    matrix = _zeros(size, size)
    matrix.index_put_((rows, columns), doubles([e[2] for e in entries]),
                      True)
    return matrix, kept

  def _chipRows(self, put: object, index: int, roles: dict) -> None:
    """Puts the rows of the chip of 'index' by 'put': each output a
    source from the ground behind 10 Ω, its current out of the chip into
    its node."""
    part = self._kept('parts')[index]
    ground = self._kept('ground')
    for node, extra in zip(part.outputs, self._extra(index)):
      if node not in roles['grounds']:
        put(node, extra, -1.0)
      if ground not in roles['grounds']:
        put(ground, extra, 1.0)
      put(extra, node, 1.0)
      put(extra, ground, -1.0)
      put(extra, extra, self.__fallback_output__)

  def _outputs(self, index: int) -> tuple[bool, ...]:
    """What the chip of 'index' drives its outputs to, in its region."""
    levels, memory = self.__network_regions__[index]
    spec = self._kept('parts')[index].spec
    return (*spec.logic(levels, memory),)

  def _drive(self, index: int) -> tuple[int, float] | None:
    """Where in the state a source of the part of 'index' is, and how
    many volts it is there: a source, a bit, a clock; else 'None'."""
    part = self._kept('parts')[index]
    count = len(self._kept('states'))
    if isinstance(part, Source):
      if part.frequency > 0:
        swing = count + 1 + 2 * self._kept('alternating').index(index)
        return swing, part.voltage
      return count, part.voltage
    if isinstance(part, Bit):
      return count, HIGH if part.high else 0.0
    if isinstance(part, Clock):
      high = self.__network_regions__[index] == 'high'
      return count, HIGH if high else 0.0
    return None

  def _transistorRows(self, put: object, index: int,
                      roles: dict) -> list:
    """Puts the rows of the transistor of 'index' by 'put', and its
    base current at its base and emitter; returns the voltages its
    region keeps, each a row and how many volts."""
    circuit = self.circuit
    nodes = len(circuit.nodes)
    part = circuit.parts[index]
    collector, emitter, base = part.first, part.second, part.base
    row = nodes + index
    extra = self._extra(index)[0]
    for end, sign in ((base, 1.0), (emitter, -1.0)):
      if end not in roles['grounds']:
        put(end, extra, sign)
    region = self.__network_regions__[index]
    if region == 'off':
      put(row, row, 1.0)
      put(extra, extra, 1.0)
      return []
    resistance = self.__fallback_on__
    put(extra, base, 1.0)
    put(extra, emitter, -1.0)
    put(extra, extra, -resistance)
    kept = [(extra, self.__fallback_junction__)]
    if region == 'active':
      conductance = 1.0 / self.__fallback_leak__
      put(row, row, 1.0)
      put(row, extra, -part.gain)
      put(row, collector, -conductance)
      put(row, emitter, conductance)
      return kept
    put(row, collector, 1.0)
    put(row, emitter, -1.0)
    put(row, row, -resistance)
    return kept + [(row, self.__fallback_saturation__)]

  def _resistance(self, index: int, roles: dict) -> float:
    """The resistance in the part of 'index', in Ω: its own, or a
    capacitor's tenth of a milliohm, a diode's tenth of an ohm, or
    nought."""
    part = self._kept('parts')[index]
    if isinstance(part, (Resistor, Lamp, Source)):
      return float(part.resistance)
    if isinstance(part, (Diode, Led)):
      return self.__fallback_on__
    if index in roles['tiny']:
      return self.__fallback_tiny__
    return 0.0

  def _solve(self, roles: dict) -> None:
    """Solves the equations for the unknowns given the state, and for
    how the state changes; keeps them, the energies' quadratic forms
    and the conditions of the regions."""
    circuit = self.circuit
    nodes, parts = len(circuit.nodes), circuit.parts
    states, alternating = self._kept('states'), self._kept('alternating')
    count, width = len(states), self._kept('size')
    size = self._unknowns()
    equations, kept = self._equations(roles)
    driven = _zeros(size, width)
    for column, index in enumerate(states):
      driven[nodes + index, column] = 1.0
    for index, part in enumerate(parts):
      drive = self._drive(index)
      if drive is not None:
        column, voltage = drive
        driven[nodes + index, column] = voltage
      if isinstance(part, Chip):
        for extra, high in zip(self._extra(index), self._outputs(index)):
          driven[extra, count] = HIGH if high else 0.0
    for row, voltage in kept:
      driven[row, count] = voltage
    solve = torch.linalg.solve(equations, driven)
    rows = _zeros(count, size)
    for row, index in enumerate(states):
      part = parts[index]
      if isinstance(part, Capacitor):
        rows[row, nodes + index] = 1.0 / part.capacitance
      else:
        rows[row, part.first] = 1.0 / part.inductance
        rows[row, part.second] = -1.0 / part.inductance
    change = _zeros(width, width)
    change[:count] = rows @ solve
    for k, index in enumerate(alternating):
      turn = 2 * math.pi * parts[index].frequency
      sine, cosine = count + 1 + 2 * k, count + 2 + 2 * k
      change[sine, cosine] = turn
      change[cosine, sine] = -turn
    keep = self.__network_kept__
    keep['solve'], keep['change'] = solve, change
    keep['store'] = self._store()
    keep['heat'] = self._heat(solve, roles)
    keep['supply'] = self._supply(solve)
    self._conditions(solve)

  def _store(self, ) -> torch.Tensor:
    """The quadratic form of the energy stored: C U² / 2 for each
    capacitor, L I² / 2 for each coil."""
    parts = self._kept('parts')
    form = _zeros(self._kept('size'), self._kept('size'))
    for row, index in enumerate(self._kept('states')):
      part = parts[index]
      if isinstance(part, Capacitor):
        form[row, row] = 0.5 * part.capacitance
      else:
        form[row, row] = 0.5 * part.inductance
    return form

  def _unit(self, *pairs: tuple[int, float]) -> torch.Tensor:
    """A column over the unknowns, each of 'pairs' an unknown and its
    weight."""
    column = _zeros(self._unknowns(), 1)
    for at, weight in pairs:
      column[at, 0] += weight
    return column

  def _heat(self, solve: torch.Tensor, roles: dict) -> torch.Tensor:
    """The quadratic form of the power turned to heat, and to light: R
    I² in each resistance, a chip's outputs' too, U² / R across each
    coil's gigaohm, and what each diode and transistor takes, its
    voltages times its currents."""
    circuit = self.circuit
    nodes = len(circuit.nodes)
    size = self._unknowns()
    form = _zeros(size, size)
    for index, part in enumerate(circuit.parts):
      current = nodes + index
      flows = []
      if isinstance(part, (Diode, Led)):
        flows = [(part.first, current)]
      if isinstance(part, Transistor):
        extra = self._extra(index)[0]
        flows = [(part.first, current), (part.base, extra)]
      if isinstance(part, Chip):
        for extra in self._extra(index):
          form[extra, extra] += self.__fallback_output__
        continue
      for high, flow in flows:
        across = self._unit((high, 1.0), (part.second, -1.0))
        into = self._unit((flow, 1.0))
        form += 0.5 * (across @ into.T + into @ across.T)
      if flows:
        continue
      form[current, current] += self._resistance(index, roles)
      if index in roles['leak']:
        across = self._unit((part.first, 1.0), (part.second, -1.0))
        form += (across @ across.T) / self.__fallback_leak__
    return solve.T @ form @ solve

  def _supply(self, solve: torch.Tensor) -> torch.Tensor:
    """The quadratic form of the power the sources deliver: each
    source's voltage times the current out of its plus pole."""
    circuit = self.circuit
    nodes, count = len(circuit.nodes), len(self._kept('states'))
    form = _zeros(self._kept('size'), self._kept('size'))
    flows = []
    for index, part in enumerate(circuit.parts):
      drive = self._drive(index)
      if drive is not None:
        flows.append((drive, -solve[nodes + index]))
      if isinstance(part, Chip):
        for extra, high in zip(self._extra(index), self._outputs(index)):
          flows.append(((count, HIGH if high else 0.0), solve[extra]))
    for (column, volts), out in flows:
      form[column] += 0.5 * volts * out
    return form + form.T

  def _conditions(self, solve: torch.Tensor) -> None:
    """Keeps the conditions of the regions as rows over the state, each
    with the part it is of and how far it may miss."""
    circuit = self.circuit
    nodes, parts = len(circuit.nodes), circuit.parts
    count = len(self._kept('states'))
    volts, amps = self.__fallback_slack__
    entries, constants, ticks = [], [], []
    owners, slack = [], []
    junction = self.__fallback_junction__
    for index, part in enumerate(parts):
      region, current = self.__network_regions__[index], nodes + index
      found = []
      if isinstance(part, (Diode, Led)) and region == 'off':
        found.append(('below', ((part.first, -1.0), (part.second, 1.0)),
                      part.voltage, volts))
      if isinstance(part, (Diode, Led)) and region == 'on':
        found.append(('forward', ((current, 1.0),), 0.0, amps))
      if isinstance(part, Transistor):
        extra = self._extra(index)[0]
        found += self._transistorConditions(part, region, current,
                                            extra)
      if isinstance(part, Chip):
        found += self._chipConditions(part, region)
      if isinstance(part, Clock):
        sine = count + 1 + 2 * self._kept('alternating').index(index)
        ticks.append((len(owners), sine,
                      1.0 if region == 'high' else -1.0))
        constants.append(0.0)
        owners.append((index, 'tick'))
        slack.append(volts)
      for tag, pairs, constant, room in found:
        for at, weight in pairs:
          entries.append((len(owners), at, weight))
        constants.append(constant)
        owners.append((index, tag))
        slack.append(room)
    picks = _zeros(len(owners), self._unknowns())
    if entries:
      at = (torch.tensor([e[0] for e in entries]).long(),
            torch.tensor([e[1] for e in entries]).long())
      picks.index_put_(at, doubles([e[2] for e in entries]), True)
    conditions = picks @ solve
    if owners:
      conditions[:, count] += doubles(constants)
    for row, sine, sign in ticks:
      conditions[row, sine] = sign
    keep = self.__network_kept__
    keep['conditions'] = conditions
    keep['owners'] = owners
    keep['slack'] = doubles([0.0, *slack])[1:]

  def _chipConditions(self, part: Chip, region: tuple) -> list:
    """The conditions of a chip in 'region': each input read low stays
    under the threshold and the hysteresis, each read high over the
    threshold less it."""
    volts, _ = self.__fallback_slack__
    levels, _ = region
    out = []
    for node, high in zip(part.inputs, levels):
      if high:
        out.append(('high', ((node, 1.0), (self._kept('ground'), -1.0)),
                    -(THRESHOLD - HYSTERESIS), volts))
      else:
        out.append(('low', ((node, -1.0), (self._kept('ground'), 1.0)),
                    THRESHOLD + HYSTERESIS, volts))
    return out

  def _transistorConditions(self, part: Transistor, region: str,
                            current: int, extra: int) -> list:
    """The conditions of a transistor in 'region': each its name, the
    unknowns it weighs, a constant and how far it may miss."""
    volts, amps = self.__fallback_slack__
    if region == 'off':
      return [('below', ((part.base, -1.0), (part.second, 1.0)),
               self.__fallback_junction__, volts)]
    out = [('forward', ((extra, 1.0),), 0.0, amps)]
    if region == 'active':
      out.append(('room', ((part.first, 1.0), (part.second, -1.0)),
                  -self.__fallback_saturation__, volts))
    else:
      out.append(('short', ((extra, part.gain), (current, -1.0)), 0.0,
                  amps))
    return out

  def _step(self, seconds: float) -> tuple[torch.Tensor, ...]:
    """What 'seconds' s does to a state: the exponential, its integral,
    and the integrals of the heat and the supply, found for a step
    small enough to be safe and doubled up to 'seconds'."""
    width = self._kept('size')
    if self.problem:
      nought = _zeros(width, width)
      return torch.eye(width).double(), nought, nought, nought
    change = self._kept('change')
    norm = float(torch.linalg.matrix_norm(change * seconds, 1))
    doublings = max(0, math.ceil(math.log2(max(norm, 1e-300) / 0.5)))
    short = seconds / 2.0 ** doublings
    wide = _zeros(2 * width, 2 * width)
    wide[:width, :width] = change * short
    wide[:width, width:] = torch.eye(width).double() * short
    grown = torch.linalg.matrix_exp(wide)
    taken, integral = grown[:width, :width], grown[:width, width:]
    forms = []
    for name in ('heat', 'supply'):
      wide = _zeros(2 * width, 2 * width)
      wide[:width, :width] = -change.T * short
      wide[:width, width:] = self._kept(name) * short
      wide[width:, width:] = change * short
      grown = torch.linalg.matrix_exp(wide)
      forms.append(taken.T @ grown[:width, width:])
    for _ in range(doublings):
      forms = [form + taken.T @ form @ taken for form in forms]
      integral = integral + taken @ integral
      taken = taken @ taken
    return taken, integral, *forms
