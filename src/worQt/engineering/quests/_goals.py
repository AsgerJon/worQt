"""
The goals a quest sets: each watches a circuit running, frame by frame,
and says when it is reached and how far it is from it; a test bench,
'Tester', sets the circuit's inputs itself, step by step.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worktoy.desc import AttriBox
from worktoy.mcls import BaseObject

from ..circuits import Ammeter, Bit, BusIn, BusProbe, Chip, Circuit, Lamp
from ..circuits import Led, Run, Switch, Voltmeter, Wire, si

_LIT = 0.3  # of its power a lamp, of its current a diode, is lit at
_DARK = 0.05  # and dark below
_HAIR = 1e-9  # s past a moment a goal waits for, to be surely past it


def glowOf(run: Run, index: int) -> float:
  """The 'glowOf' function returns how brightly the part of 'index'
  glows in 'run' now: a lamp the share of the power it is made for that
  it takes, a light emitting diode the share of its current; nought for
  anything else."""
  part = run.circuit.parts[index]
  if isinstance(part, Lamp):
    return run.drops[index] * run.currents[index] / part.power
  if isinstance(part, Led):
    return max(run.currents[index], 0.0) / part.current
  return 0.0


def _percent(share: float) -> str:
  """'share' as a whole percentage."""
  return '%.0f %%' % (100 * share)


class Goal(BaseObject):
  """
  Goal is what a quest asks of a circuit: 'update' watches the circuit
  running, after each frame, and 'reached' turns true, for good, once it
  is achieved; 'words' say how far it is from it. A goal names the parts
  it watches by their indices, the quest's own parts, which come first
  and never move.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  reached = AttriBox[bool](False)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def update(self, run: Run) -> None:
    """The 'update' method watches 'run' as it is now; once the goal is
    reached it stays so."""
    if not self.reached:
      self._watch(run)

  def drive(self, run: Run) -> Circuit | None:
    """The 'drive' method returns the circuit of 'run' as the goal sets
    it, a test bench its inputs, or 'None' to leave it be; most goals
    only watch."""
    return None

  def words(self, run: Run) -> str:
    """The 'words' method says how far the goal is from being reached in
    'run', or that it is."""
    if self.reached:
      return 'Reached!'
    return self._words(run)

  def longest(self, run: Run) -> float:
    """The 'longest' method returns how long 'run' may run on before the
    goal must watch it and drive it again; most goals do not mind."""
    return math.inf

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _watch(self, run: Run) -> None:
    """Watches 'run' as it is now, for a goal not yet reached."""

  def _words(self, run: Run) -> str:
    """How far the goal is from being reached in 'run'."""
    return ''


class Glow(Goal):
  """
  Glow is reached once the lamp or light emitting diode of 'part' has
  glowed at 'least' of what it is made for, without ever going over
  'most', for 'seconds' on end; going over it starts it again.
  """

  __glow_part__: int = 0
  __glow_least__: float = 0.0
  __glow_most__: float = math.inf
  __glow_seconds__: float = 0.0
  __glow_since__: float | None = None
  __glow_over__: float = 0.0

  def __init__(self, part: int, least: float, seconds: float,
               most: float) -> None:
    self.__glow_part__ = part
    self.__glow_least__ = least
    self.__glow_seconds__ = seconds
    self.__glow_most__ = most

  def _watch(self, run: Run) -> None:
    share = glowOf(run, self.__glow_part__)
    if share > self.__glow_most__:
      self.__glow_since__ = None
      self.__glow_over__ = share
    elif share >= self.__glow_least__:
      if self.__glow_since__ is None:
        self.__glow_since__ = run.time
      if run.time - self.__glow_since__ >= self.__glow_seconds__:
        self.reached = True
    else:
      self.__glow_since__ = None

  def _words(self, run: Run) -> str:
    name = run.circuit.label(self.__glow_part__)
    share = glowOf(run, self.__glow_part__)
    words = '%s glows at %s; it needs %s for %s.' % (
      name, _percent(share), _percent(self.__glow_least__),
      si(self.__glow_seconds__, 's'))
    if share > self.__glow_most__:
      words += (' Far too bright: over %s it would burn out!'
                % _percent(self.__glow_most__))
    elif self.__glow_since__ is not None:
      words += ' %s so far.' % si(run.time - self.__glow_since__, 's')
    return words


class Toggles(Goal):
  """
  Toggles is reached once the lamp or light emitting diode of 'part' has
  turned from dark to lit or back 'times' times: lit at 30 % of what it
  is made for, dark under 5 %.
  """

  __toggle_part__: int = 0
  __toggle_times__: int = 0
  __toggle_lit__: bool | None = None
  __toggle_count__: int = 0

  def __init__(self, part: int, times: int) -> None:
    self.__toggle_part__ = part
    self.__toggle_times__ = times

  def _watch(self, run: Run) -> None:
    share = glowOf(run, self.__toggle_part__)
    lit = None
    if share >= _LIT:
      lit = True
    elif share <= _DARK:
      lit = False
    if lit is None:
      return
    if self.__toggle_lit__ is not None and lit != self.__toggle_lit__:
      self.__toggle_count__ += 1
    self.__toggle_lit__ = lit
    if self.__toggle_count__ >= self.__toggle_times__:
      self.reached = True

  def _words(self, run: Run) -> str:
    name = run.circuit.label(self.__toggle_part__)
    state = 'lit' if glowOf(run, self.__toggle_part__) >= _LIT else 'dark'
    return '%s is %s; it has turned %d of %d times.' % (
      name, state, self.__toggle_count__, self.__toggle_times__)


class Measures(Goal):
  """
  Measures is reached once an ammeter reads the current through the part
  of 'part' and a voltmeter the voltage across it, both for 'seconds'
  on end.
  """

  __measure_part__: int = 0
  __measure_seconds__: float = 0.0
  __measure_since__: float | None = None

  def __init__(self, part: int, seconds: float) -> None:
    self.__measure_part__ = part
    self.__measure_seconds__ = seconds

  def found(self, run: Run) -> tuple[bool, bool]:
    """The 'found' method tells whether an ammeter reads the part's
    current, and whether a voltmeter reads its voltage, in 'run'."""
    index = self.__measure_part__
    current, drop = abs(run.currents[index]), abs(run.drops[index])
    amps = volts = False
    for other, part in enumerate(run.circuit.parts):
      if isinstance(part, Ammeter) and current > 1e-6:
        if abs(abs(run.currents[other]) - current) <= 1e-6 * current:
          amps = True
      if isinstance(part, Voltmeter) and drop > 1e-3:
        if abs(abs(run.drops[other]) - drop) <= 1e-6 * drop:
          volts = True
    return amps, volts

  def _watch(self, run: Run) -> None:
    if all(self.found(run)):
      if self.__measure_since__ is None:
        self.__measure_since__ = run.time
      if run.time - self.__measure_since__ >= self.__measure_seconds__:
        self.reached = True
    else:
      self.__measure_since__ = None

  def _words(self, run: Run) -> str:
    amps, volts = self.found(run)
    name = run.circuit.label(self.__measure_part__)
    return ('An ammeter %s the current through %s; a voltmeter %s the '
            'voltage across it.' % ('reads' if amps else 'must read', name,
                                    'reads' if volts else 'must read'))


class Afterglow(Goal):
  """
  Afterglow is reached once the lamp of 'part' goes on glowing at
  'least' of its power for 'seconds' after the switch of 'switch' is
  opened; the words say how soon it faded the last time.
  """

  wasClosed = AttriBox[bool](True)
  __after_part__: int = 0
  __after_switch__: int = 0
  __after_least__: float = 0.0
  __after_seconds__: float = 0.0
  __after_opened__: float | None = None
  __after_lasted__: float | None = None

  def __init__(self, part: int, switch: int, least: float,
               seconds: float) -> None:
    self.__after_part__ = part
    self.__after_switch__ = switch
    self.__after_least__ = least
    self.__after_seconds__ = seconds

  def _watch(self, run: Run) -> None:
    closed = run.circuit.parts[self.__after_switch__].closed
    share = glowOf(run, self.__after_part__)
    if closed:
      self.__after_opened__ = None
    elif self.wasClosed:
      self.__after_opened__ = run.time
    self.wasClosed = closed
    opened = self.__after_opened__
    if opened is None:
      return
    if share < self.__after_least__:
      self.__after_lasted__ = run.time - opened
      self.__after_opened__ = None
    elif run.time - opened >= self.__after_seconds__:
      self.reached = True

  def _words(self, run: Run) -> str:
    name = run.circuit.label(self.__after_part__)
    switch = run.circuit.label(self.__after_switch__)
    words = '%s must glow at %s or more for %s after %s opens.' % (
      name, _percent(self.__after_least__),
      si(self.__after_seconds__, 's'), switch)
    if self.__after_opened__ is not None:
      words += ' %s so far.' % si(run.time - self.__after_opened__, 's')
    elif self.__after_lasted__ is not None:
      words += ' Last time it faded after %s.' % si(self.__after_lasted__,
                                                     's')
    return words


class OneWay(Goal):
  """
  OneWay is reached once the current through the part of 'part' has
  flowed only forward, from its first node to its second, for 'seconds'
  on end, letting through at least 'charge' C in that time.
  """

  turnedBack = AttriBox[bool](False)
  __way_part__: int = 0
  __way_charge__: float = 0.0
  __way_seconds__: float = 0.0
  __way_start__: tuple[float, float] | None = None
  __way_last__: float | None = None

  def __init__(self, part: int, charge: float, seconds: float) -> None:
    self.__way_part__ = part
    self.__way_charge__ = charge
    self.__way_seconds__ = seconds

  def _watch(self, run: Run) -> None:
    charge = run.charges[self.__way_part__]
    last = self.__way_last__
    self.__way_last__ = charge
    if last is not None and charge < last - 1e-9:
      self.__way_start__ = None
      self.turnedBack = True
      return
    if self.__way_start__ is None:
      self.__way_start__ = (run.time, charge)
      return
    start, before = self.__way_start__
    if run.time - start >= self.__way_seconds__:
      if charge - before >= self.__way_charge__:
        self.reached = True
      else:
        self.__way_start__ = (run.time, charge)

  def _words(self, run: Run) -> str:
    name = run.circuit.label(self.__way_part__)
    words = ('The current through %s must flow one way only, forward, '
             'and not too little of it.' % name)
    if self.turnedBack:
      words += ' It has turned back.'
    return words


class Touch(Goal):
  """
  Touch is reached once the light emitting diode or lamp of 'part' has
  been seen lit for 'seconds' on end with the switch of 'switch' closed,
  and dark for as long with it open.
  """

  __touch_part__: int = 0
  __touch_switch__: int = 0
  __touch_seconds__: float = 0.0
  __touch_since__: tuple[bool, float] | None = None
  __touch_seen__: tuple[bool, bool] = (False, False)

  def __init__(self, part: int, switch: int, seconds: float) -> None:
    self.__touch_part__ = part
    self.__touch_switch__ = switch
    self.__touch_seconds__ = seconds

  def _watch(self, run: Run) -> None:
    closed = run.circuit.parts[self.__touch_switch__].closed
    share = glowOf(run, self.__touch_part__)
    right = share >= 0.5 if closed else share <= _DARK
    if not right:
      self.__touch_since__ = None
      return
    if self.__touch_since__ is None or self.__touch_since__[0] != closed:
      self.__touch_since__ = (closed, run.time)
    if run.time - self.__touch_since__[1] >= self.__touch_seconds__:
      lit, dark = self.__touch_seen__
      self.__touch_seen__ = (lit or closed, dark or not closed)
    if all(self.__touch_seen__):
      self.reached = True

  def _words(self, run: Run) -> str:
    name = run.circuit.label(self.__touch_part__)
    switch = run.circuit.label(self.__touch_switch__)
    lit, dark = self.__touch_seen__
    return ('%s must glow at half or more while %s is closed (%s), and '
            'be dark while it is open (%s).' % (
              name, switch, 'seen' if lit else 'not yet',
              'seen' if dark else 'not yet'))


class All(Goal):
  """
  All is reached once each of its 'goals' is.
  """

  __all_goals__: tuple = ()

  def __init__(self, *goals: Goal) -> None:
    self.__all_goals__ = goals

  def drive(self, run: Run) -> Circuit | None:
    for goal in self.__all_goals__:
      changed = goal.drive(run)
      if changed is not None:
        return changed
    return None

  def longest(self, run: Run) -> float:
    return min((goal.longest(run) for goal in self.__all_goals__),
               default=math.inf)

  def _watch(self, run: Run) -> None:
    for goal in self.__all_goals__:
      goal.update(run)
    if all(goal.reached for goal in self.__all_goals__):
      self.reached = True

  def _words(self, run: Run) -> str:
    return ' '.join(goal.words(run) for goal in self.__all_goals__)


def _nets(circuit: Circuit) -> object:
  """What names the net each node is in: nodes joined by a wire, an
  ammeter or a closed switch are one."""
  parent = [*range(len(circuit.nodes))]

  def find(node: int) -> int:
    while parent[node] != node:
      parent[node] = parent[parent[node]]
      node = parent[node]
    return node

  for part in circuit.parts:
    joins = isinstance(part, (Wire, Ammeter))
    if isinstance(part, Switch) and part.closed:
      joins = True
    if joins:
      parent[find(part.first)] = find(part.second)
  return find


def depthOf(circuit: Circuit, probes: tuple[int, ...]) -> float:
  """The 'depthOf' function returns how many chips the deepest of the
  probes of 'probes' reads through, each from its inputs to its
  outputs, nought straight from an input; infinite round a loop."""
  find = _nets(circuit)
  drivers = {}
  for index, part in enumerate(circuit.parts):
    if isinstance(part, Chip):
      for node in part.outputs:
        drivers[find(node)] = index
  known: dict = {}

  def depth(net: int) -> float:
    if net in known:
      return known[net]
    if net not in drivers:
      return 0.0
    known[net] = math.inf
    chip = circuit.parts[drivers[net]]
    known[net] = 1.0 + max([depth(find(n)) for n in chip.inputs] + [0.0])
    return known[net]

  return max([depth(find(circuit.parts[p].first)) for p in probes]
             + [0.0])


def readOf(run: Run, probe: int) -> int | None:
  """The 'readOf' function returns what the probe of 'probe' reads in
  'run': a bus probe the number on its bus, a probe 1 or 0, or 'None'
  where it is neither high nor low."""
  part = run.circuit.parts[probe]
  if isinstance(part, BusProbe):
    return run.values[part.first]
  level = levelOf(run, probe)
  return None if level is None else int(level)


def setOf(circuit: Circuit, index: int, value: int) -> Circuit:
  """The 'setOf' function returns 'circuit' with the input of 'index', a
  logic input or a bus input, set to 'value'; itself if it is so."""
  part = circuit.parts[index]
  if isinstance(part, BusIn):
    if part.value == value:
      return circuit
    return circuit.withPart(index, BusIn(part.first, part.second,
                                         int(value), part.name))
  if part.high == bool(value):
    return circuit
  return circuit.withPart(index, Bit(part.first, part.second, bool(value),
                                     part.name))


def levelOf(run: Run, probe: int) -> bool | None:
  """The 'levelOf' function returns what the probe of 'probe' reads in
  'run': high at 3.5 V or more, low at 1 V or less, else 'None'."""
  volts = run.drops[probe]
  if volts >= 3.5:
    return True
  if volts <= 1.0:
    return False
  return None


def table(count: int, logic: object) -> tuple:
  """The 'table' function returns the steps of a truth table of 'count'
  inputs: each row of input levels, counted up from all low, with the
  outputs 'logic' gives for it."""
  rows = []
  for number in range(2 ** count):
    bits = (*[(number >> (count - 1 - k)) & 1 == 1
              for k in range(count)],)
    rows.append((bits, (*logic(*bits),)))
  return (*rows,)


class Tester(Goal):
  """
  Tester is a test bench: it sets the logic inputs of 'inputs' itself,
  step by step, each of 'steps' input levels and the outputs the probes
  of 'outputs' must then read, or 'None' to check nothing; it waits
  'wait' s before it looks. It is reached once every step of a pass,
  from the first, reads right, and, if 'most' is finite, the outputs
  read through no more than 'most' chips. 'drive' returns the circuit
  with the inputs set, or 'None' when they are.
  """

  __test_inputs__: tuple = ()
  __test_outputs__: tuple = ()
  __test_steps__: tuple = ()
  __test_wait__: float = 0.0
  __test_most__: float = math.inf
  __test_step__: int = 0
  __test_since__: float | None = None
  __test_wrong__: str = ''
  __test_right__: int = 0

  def __init__(self, inputs: tuple, outputs: tuple, steps: tuple,
               wait: float, most: float) -> None:
    self.__test_inputs__ = (*inputs,)
    self.__test_outputs__ = (*outputs,)
    self.__test_steps__ = (*steps,)
    self.__test_wait__ = wait
    self.__test_most__ = most

  def drive(self, run: Run) -> Circuit | None:
    """The 'drive' method returns the circuit of 'run' with its inputs
    set as the step now says, or 'None' if they are, or the goal is
    reached."""
    if self.reached:
      return None
    circuit = run.circuit
    wanted, _ = self.__test_steps__[self.__test_step__]
    changed = circuit
    for index, value in zip(self.__test_inputs__, wanted):
      changed = setOf(changed, index, value)
    if self.__test_since__ is None:
      self.__test_since__ = run.time
    return None if changed is circuit else changed

  def longest(self, run: Run) -> float:
    """The 'longest' method returns how long until the bench looks at
    the step it is on, a hair past it."""
    since = self.__test_since__
    if self.reached or since is None:
      return math.inf
    return max(since + self.__test_wait__ - run.time, 0.0) + _HAIR

  def _watch(self, run: Run) -> None:
    since = self.__test_since__
    if since is None or run.time - since < self.__test_wait__ - 1e-12:
      return
    wanted, expected = self.__test_steps__[self.__test_step__]
    circuit = run.circuit
    if any(setOf(circuit, i, value) is not circuit
           for i, value in zip(self.__test_inputs__, wanted)):
      return
    if self.__test_step__ == 0:
      self.__test_right__ = 0
    if expected is not None:
      read = (*[readOf(run, p) for p in self.__test_outputs__],)
      deep = depthOf(run.circuit, self.__test_outputs__)
      if read != expected or deep > self.__test_most__:
        self.__test_wrong__ = self._wrong(run, wanted, expected, read,
                                          deep)
        self.__test_right__ = -len(self.__test_steps__)
    self.__test_right__ += 1
    self.__test_step__ = (self.__test_step__ + 1) % len(self.__test_steps__)
    self.__test_since__ = None
    if self.__test_right__ >= len(self.__test_steps__):
      self.reached = True

  def _named(self, run: Run, indices: tuple, bits: tuple) -> str:
    """The parts of 'indices' named with their levels of 'bits', a level
    'None' read as '?'."""
    words = []
    for index, bit in zip(indices, bits):
      level = '?' if bit is None else str(int(bit))
      words.append('%s %s' % (run.circuit.label(index), level))
    return ', '.join(words)

  def _wrong(self, run: Run, wanted: tuple, expected: tuple, read: tuple,
             deep: float) -> str:
    """What went wrong at a step, in words."""
    if read != expected:
      return 'With %s: read %s, not %s.' % (
        self._named(run, self.__test_inputs__, wanted),
        self._named(run, self.__test_outputs__, read),
        self._named(run, self.__test_outputs__, expected))
    return 'Right, but through %s chips; at most %d.' % (
      'endless' if math.isinf(deep) else '%d' % deep, self.__test_most__)

  def _words(self, run: Run) -> str:
    count = len(self.__test_steps__)
    wanted, expected = self.__test_steps__[self.__test_step__]
    words = 'Testing step %d of %d: %s' % (
      self.__test_step__ + 1, count,
      self._named(run, self.__test_inputs__, wanted))
    if expected is not None:
      words += ', wants %s' % self._named(run, self.__test_outputs__,
                                          expected)
    words += '. %d right in a row.' % max(self.__test_right__, 0)
    if not math.isinf(self.__test_most__):
      deep = depthOf(run.circuit, self.__test_outputs__)
      words += ' Deepest output: %s chips, at most %d.' % (
        'endless' if math.isinf(deep) else '%d' % deep, self.__test_most__)
    if self.__test_wrong__:
      words += ' Last wrong: %s' % self.__test_wrong__
    return words


class Clocked(Goal):
  """
  Clocked runs a computer: it ticks the logic input of 'clock' itself,
  high then low, 'wait' s each, and reads the probe of 'probe' after
  each tick, noting each reading, or only each change if 'changes'. It
  is reached once its notes are 'expected', the probe then steady for
  'quiet' ticks; notes that go wrong are kept, to be put right only by
  starting over.
  """

  __clock_part__: int = 0
  __clock_probe__: int = 0
  __clock_expected__: tuple = ()
  __clock_quiet__: int = 0
  __clock_wait__: float = 0.0
  __clock_notes__: list | None = None
  __clock_since__: float | None = None
  __clock_ticks__: int = 0
  __clock_steady__: int = 0
  changes = AttriBox[bool](False)

  def __init__(self, clock: int, probe: int, expected: tuple,
               changes: bool, quiet: int, wait: float) -> None:
    self.__clock_part__ = clock
    self.__clock_probe__ = probe
    self.__clock_expected__ = (*expected,)
    self.changes = True if changes else False
    self.__clock_quiet__ = quiet
    self.__clock_wait__ = wait
    self.__clock_notes__ = []

  def notes(self, ) -> tuple:
    """The 'notes' method returns what the probe has read so far."""
    return (*self.__clock_notes__,)

  def drive(self, run: Run) -> Circuit | None:
    """The 'drive' method ticks the clock: high in the first half of a
    tick, low in the second."""
    if self.reached:
      return None
    if self.__clock_since__ is None:
      self.__clock_since__ = run.time
      self._note(run)
    high = (run.time - self.__clock_since__) % (2 * self.__clock_wait__)
    level = 1 if high < self.__clock_wait__ else 0
    changed = setOf(run.circuit, self.__clock_part__, level)
    return None if changed is run.circuit else changed

  def longest(self, run: Run) -> float:
    """The 'longest' method returns how long until the clock turns next,
    a hair past it."""
    since = self.__clock_since__
    if self.reached or since is None:
      return math.inf
    wait = self.__clock_wait__
    turns = math.floor((run.time - since) / wait) + 1
    return max(since + turns * wait - run.time, 0.0) + _HAIR

  def _watch(self, run: Run) -> None:
    since = self.__clock_since__
    if since is None:
      return
    ticks = int((run.time - since) // (2 * self.__clock_wait__))
    while self.__clock_ticks__ < ticks:
      self.__clock_ticks__ += 1
      self._note(run)
    expected = self.__clock_expected__
    if (self.notes() == expected
        and self.__clock_steady__ >= self.__clock_quiet__):
      self.reached = True

  def _note(self, run: Run) -> None:
    """Notes what the probe reads, or that it is steady."""
    value = readOf(run, self.__clock_probe__)
    notes = self.__clock_notes__
    if self.changes and notes and notes[-1] == value:
      self.__clock_steady__ += 1
      return
    expected = [*self.__clock_expected__]
    if not self.changes and notes == expected and value == expected[-1]:
      self.__clock_steady__ += 1
      return
    self.__clock_steady__ = 0
    notes.append(value)

  def _words(self, run: Run) -> str:
    name = run.circuit.label(self.__clock_probe__)

    def listed(values: tuple) -> str:
      return ', '.join('?' if v is None else str(v) for v in values)

    notes, expected = self.notes(), self.__clock_expected__
    words = 'Tick %d: %s reads %s. So far %s; wanted %s.' % (
      self.__clock_ticks__, name, listed((readOf(run,
                                                 self.__clock_probe__),)),
      listed(notes), listed(expected))
    if notes != expected[:len(notes)]:
      words += ' That went wrong: put it right, then Reset to start over.'
    return words
