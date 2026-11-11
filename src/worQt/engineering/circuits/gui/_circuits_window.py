"""
CircuitsWindow subclasses 'MainWindow' and is an electric circuit,
built with the mouse and running as it is built.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QTimer
from PySide6.QtWidgets import QMenu
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ....utils import Color
from ....windows import MainWindow
from ...gui import TestStatus, TimeCurve
from .. import Ammeter, Capacitor, Circuit, Coil, Diode, EXAMPLES, KINDS
from .. import Bit, BusIn, BusProbe, Clock, Lamp, Led, Node, Probe
from .. import Resistor, Run, Source
from .. import Switch, Transistor, Voltmeter, Wire
from . import CircuitView, CircuitsPanel, CircuitsToolBar
from ._speed_slider import speedWords
from .._si import si

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QCloseEvent

#  Each kind of part as it is added: what it is made of but its nodes
_NEW = {
  Wire     : (),
  Source   : (4.5, 0.0, 0.0),
  Resistor : (100.0,),
  Lamp     : (6.0, 0.3),
  Capacitor: (1e-3,),
  Coil     : (1.0,),
  Switch   : (False,),
  Ammeter  : (),
  Voltmeter: (),
  Diode    : (0.7,),
  Led      : (2.0, 0.02),
  Bit      : (False, ''),
  Probe    : ('',),
  Clock    : (1.0,),
  BusIn    : (0, ''),
  BusProbe : ('',),
}
#  The colours of the curves, in turn
_COLORS = (Color(229, 192, 123), Color(97, 175, 239), Color(152, 195, 121),
           Color(198, 120, 221), Color(224, 108, 117))
_GAIN = 100.0  # a new transistor's gain


class CircuitsWindow(MainWindow):
  """
  CircuitsWindow subclasses 'MainWindow' and is an electric circuit
  running as it is built: the 'toolBar' above; below it the 'panel' of
  the part selected, or of the circuit and its energy, the circuit
  itself, 'circuitView', over the voltages against time,
  'voltageCurve', and the currents, 'currentCurve', as an oscilloscope
  would show them: the part selected's, and each voltmeter's and
  ammeter's; along the bottom the 'status'.

  It opens running, on a battery charging a capacitor through a lamp
  once its switch is closed; 'Examples' opens a menu of small circuits
  to start from instead, each with a word on what to do with it. A
  button for each kind of part adds one: in the place of the wire
  selected, or joining the two nodes selected, Ctrl and a click, or
  else two steps from the node selected, or the part selected's second
  node, to a new node, to the right, else up, left or down, where there
  is room; selected, to be set in the panel. A transistor joins the
  three nodes selected, collector, base and emitter in turn, or else
  has its base at the node selected, its collector and emitter a step
  above and below two steps aside.
  'Remove' takes away what is selected. 'Play' and 'Pause' run and stop
  it; 'Reset' switches it on anew, every capacitor empty and every
  coil still; the speed slider chooses how fast it runs, from a
  thousandth of real time, for what is quick, as alternating current,
  to ten times it. It runs on as it is changed, each capacitor keeping
  its charge and each coil its current.

  The window runs the circuit on every 20 ms by as long as has passed,
  to 5 ms, at most 50 ms, at the speed chosen, the panel, the curves and
  the status shown anew every fifth frame; 'advance' runs it on so long
  at once and shows it all. Either runs it on in pieces no longer than
  'longestStep' allows, 'ran' called after each; a frame gives up the
  rest of its time once it has worked 0.1 s, the circuit then running
  slower than chosen.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Circuits'
  __start_size__ = 1760, 960
  __frame_ms__ = 20  # between two frames
  __new_reach__ = 2.0  # grid steps a new part reaches
  __shown_window__ = 20.0  # s of real time the curves show

  __longest_frame__ = 0.05  # s a frame runs the circuit on at most
  __frame_grain__ = 0.005  # s a frame's time is rounded to
  __shown_every__ = 5  # frames between showing the panel and curves
  __busiest_frame__ = 0.1  # s a frame may work before it gives up

  #  Private Variables
  __run_speed__: float = 1.0
  __examples_menu__: QMenu | None = None
  __frame_clock__: float | None = None
  __frame_count__: int = 0

  #  Public Variables
  toolBar = AttriBox[CircuitsToolBar](THIS)
  panel = AttriBox[CircuitsPanel](THIS)
  circuitView = AttriBox[CircuitView](THIS)
  voltageCurve = AttriBox[TimeCurve](THIS)
  currentCurve = AttriBox[TimeCurve](THIS)
  status = AttriBox[TestStatus](THIS)
  frameTimer = AttriBox[QTimer](THIS)

  #  Virtual Variables
  circuit: Field[Circuit] = Field()
  run: Field[Run] = Field()
  running: Field[bool] = Field()
  speed: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @circuit.GET
  def _getCircuit(self, ) -> Circuit:
    """The 'circuit' getter returns the circuit shown."""
    return self.circuitView.circuit

  @run.GET
  def _getRun(self, ) -> Run:
    """The 'run' getter returns the circuit running."""
    return self.circuitView.run

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the circuit runs, not
    paused."""
    return True if self.frameTimer.isActive() else False

  @speed.GET
  def _getSpeed(self, ) -> float:
    """The 'speed' getter returns how fast the circuit runs, against real
    time."""
    return self.__run_speed__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the window out, sizes it and sets the
    circuit running."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 3)
    layout.addWidget(self.panel, 1, 0, 2, 1)
    layout.addWidget(self.circuitView, 1, 1, 1, 2)
    layout.addWidget(self.voltageCurve, 2, 1)
    layout.addWidget(self.currentCurve, 2, 2)
    layout.addWidget(self.status, 3, 0, 1, 3)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    layout.setColumnStretch(2, 1)
    layout.setRowStretch(1, 3)
    layout.setRowStretch(2, 2)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.circuitView.setFocus()
    self.setSpeed(1.0)
    self._start()
    self.refresh()

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons, the edits and the
    timer."""
    bar = self.toolBar
    bar.playButton.clicked.connect(self.togglePlay)
    bar.resetButton.clicked.connect(self.reset)
    bar.examplesButton.clicked.connect(self.showExamples)
    for button, kind in zip(bar.partButtons(), KINDS):
      button.clicked.connect(self._adder(kind))
    bar.removeButton.clicked.connect(self.circuitView.removeSelected)
    bar.speedSlider.speedChanged.connect(self.setSpeed)
    self.circuitView.circuitEdited.connect(self.setCircuit)
    self.circuitView.selectionChanged.connect(self.selected)
    self.circuitView.refused.connect(self.refuse)
    self.panel.circuitEdited.connect(self.setCircuit)
    self.panel.programWritten.connect(self.reset)
    self.frameTimer.timeout.connect(self.tick)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)

  def closeEvent(self, event: QCloseEvent) -> None:
    """Closing the window stops the circuit."""
    MainWindow.closeEvent(self, event)
    if event.isAccepted():
      self.frameTimer.stop()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setCircuit(self, circuit: Circuit) -> None:
    """The 'setCircuit' method shows 'circuit', running on from where the
    circuit before it was."""
    view = self.circuitView
    run = Run(circuit, view.run)
    if circuit is not view.circuit:
      view.circuit = circuit
    view.run = run
    self.refresh()

  def selected(self, part: tuple[str, int] | None) -> None:
    """The 'selected' method shows the part selected in the panel."""
    self.panel.showNote('')
    self.refresh()

  def togglePlay(self, ) -> None:
    """The 'togglePlay' method runs the circuit on, or pauses it."""
    if self.running:
      self.frameTimer.stop()
    else:
      self._start()
    self.refresh()

  def reset(self, ) -> None:
    """The 'reset' method switches the circuit on anew, at nought
    seconds, every capacitor empty and every coil still."""
    self.circuitView.run = Run(self.circuit)
    self.refresh()

  def setSpeed(self, speed: float) -> None:
    """The 'setSpeed' method runs the circuit at the slider's stop
    nearest 'speed' times real time, the slider there, the curves
    showing the last twenty seconds of real time."""
    slider = self.toolBar.speedSlider
    slider.speed = speed
    speed = slider.speed
    self.__run_speed__ = speed
    for curve in self.curves():
      curve.window = self.__shown_window__ * speed
    self.refresh()

  def curves(self, ) -> tuple[TimeCurve, ...]:
    """The 'curves' method returns the curves the window plots: the
    voltages and the currents."""
    return self.voltageCurve, self.currentCurve

  def ran(self, ) -> None:
    """The 'ran' method is called each time the circuit has run on, to
    watch it; here it does nothing."""

  def longestStep(self, ) -> float:
    """The 'longestStep' method returns how long the circuit may run on
    before 'ran' must watch it again; here as long as it likes."""
    return math.inf

  def tick(self, ) -> None:
    """The 'tick' method runs the circuit on by as long as has passed
    since the last frame, at the speed chosen, and shows it, the panel,
    the curves and the status every fifth frame."""
    now = time.monotonic()
    passed = now - (self.__frame_clock__ or now)
    self.__frame_clock__ = now
    grain = self.__frame_grain__
    passed = min(max(round(passed / grain) * grain, grain),
                 self.__longest_frame__)
    self._runOn(passed * self.speed, now + self.__busiest_frame__)
    self.circuitView.flow(self.speed)
    self.__frame_count__ += 1
    if self.__frame_count__ % self.__shown_every__ == 0:
      self._showAll()

  def advance(self, seconds: float) -> None:
    """The 'advance' method runs the circuit on 'seconds' and shows
    it."""
    self._runOn(seconds, math.inf)
    self.circuitView.flow(self.speed)
    self._showAll()

  def examplesMenu(self, ) -> QMenu:
    """The 'examplesMenu' method returns the menu of examples, each
    loading its circuit when chosen, made anew."""
    menu = self.__examples_menu__ = QMenu(self)
    for index, example in enumerate(EXAMPLES):
      action = menu.addAction(example.name)
      action.triggered.connect(self._loader(index))
    return menu

  def showExamples(self, ) -> None:
    """The 'showExamples' method opens the menu of examples under its
    button, without waiting for a choice."""
    button = self.toolBar.examplesButton
    where = button.mapToGlobal(QPoint(0, button.height()))
    self.examplesMenu().popup(where)

  def loadExample(self, index: int) -> None:
    """The 'loadExample' method shows the example of 'index', switched on
    anew, settled as long as it asks, at its speed, its word on what to
    do in the panel."""
    example = EXAMPLES[index]
    view = self.circuitView
    view.select(None)
    circuit = example.circuit()
    view.circuit = circuit
    run = Run(circuit)
    if example.settle > 0:
      run.advance(example.settle)
    view.run = run
    self.setSpeed(example.speed)
    self.refresh()
    self.panel.showNote(example.hint)

  def addPart(self, kind: type) -> None:
    """The 'addPart' method adds a part of 'kind', selected: in the place
    of the wire selected, or joining the two nodes selected, or two
    steps from the node selected, or the part selected's second node, or
    the last node, to a new node; or says why it cannot, a bus joined to
    a single wire."""
    try:
      self._addPart(kind)
    except ValueError as exception:
      self.refuse(str(exception))

  def refuse(self, words: str) -> None:
    """The 'refuse' method says in the panel why an edit was given up."""
    self.panel.showNote('%s%s.' % (words[:1].upper(), words[1:]))

  def _addPart(self, kind: type) -> None:
    """Adds a part of 'kind', as 'addPart' says."""
    if kind is Transistor:
      return self.addTransistor()
    view, circuit = self.circuitView, self.circuit
    values = _NEW[kind]
    parts, nodes = view.selectedOf('part'), view.selectedOf('node')
    if parts and kind is not Wire and not view.isLocked(('part',
                                                         parts[-1])):
      wire = circuit.parts[parts[-1]]
      if isinstance(wire, Wire):
        made = kind(wire.first, wire.second, *values)
        return self._edited(circuit.withPart(parts[-1], made),
                            ('part', parts[-1]))
    if len(nodes) >= 2:
      made = kind(nodes[-2], nodes[-1], *values)
      return self._edited(circuit.withParts(*circuit.parts, made),
                          ('part', len(circuit.parts)))
    start = self._startNode()
    if start is None:
      circuit = circuit.withNodes(Node(0.0, 0.0))
      start = 0
    x, y = circuit.nodes[start]
    reach = self.__new_reach__
    for dx, dy in ((reach, 0.0), (0.0, reach), (-reach, 0.0),
                   (0.0, -reach)):
      if circuit.at(x + dx, y + dy) is None:
        break
    else:
      return self.panel.showNote('There is no room beside that node: '
                                 'drag it apart, or select two nodes.')
    grown = circuit.withNodes(*circuit.nodes, Node(x + dx, y + dy))
    made = kind(start, len(circuit.nodes), *values)
    self._edited(grown.withParts(*grown.parts, made),
                 ('part', len(grown.parts)))

  def addTransistor(self, ) -> None:
    """The 'addTransistor' method adds a transistor, selected, joining
    the three nodes selected, collector, base and emitter in turn; or
    else its base at the node selected, or the part selected's second
    node, or the last, its collector and emitter a step above and below
    two steps to the right, else left; or beside and two steps up, else
    down."""
    view, circuit = self.circuitView, self.circuit
    nodes = view.selectedOf('node')
    if len(nodes) >= 3:
      collector, base, emitter = nodes[-3:]
      made = Transistor(collector, emitter, base, _GAIN)
      return self._edited(circuit.withParts(*circuit.parts, made),
                          ('part', len(circuit.parts)))
    start = self._startNode()
    if start is None:
      circuit = circuit.withNodes(Node(0.0, 0.0))
      start = 0
    x, y = circuit.nodes[start]
    for (cx, cy), (ex, ey) in (((x + 2, y + 1), (x + 2, y - 1)),
                               ((x - 2, y + 1), (x - 2, y - 1)),
                               ((x + 1, y + 2), (x - 1, y + 2)),
                               ((x - 1, y - 2), (x + 1, y - 2))):
      if circuit.at(cx, cy) is None and circuit.at(ex, ey) is None:
        break
    else:
      return self.panel.showNote('There is no room beside that node: '
                                 'drag it apart, or select three nodes.')
    count = len(circuit.nodes)
    grown = circuit.withNodes(*circuit.nodes, Node(cx, cy), Node(ex, ey))
    made = Transistor(count, count + 1, start, _GAIN)
    self._edited(grown.withParts(*grown.parts, made),
                 ('part', len(grown.parts)))

  def refresh(self, ) -> None:
    """The 'refresh' method lights 'Play' while the circuit runs, greys
    out what cannot be done now, shows the panel and the curves, and
    says what is going on."""
    bar, view = self.toolBar, self.circuitView
    bar.playButton.text = 'Pause' if self.running else 'Play'
    bar.playButton.checked = self.running
    free = [part for part in view.selection if not view.isLocked(part)]
    bar.removeButton.setEnabled(True if free else False)
    for button in (bar.playButton, bar.removeButton):
      button.update()
    self.panel.showRun(self.run, view.selected)
    self._showCurves()
    self.status.showState(*self.statusOf())
    view.update()

  def statusOf(self, ) -> tuple[str, str, str]:
    """The 'statusOf' method says what is going on: the state, in words,
    and the details."""
    run = self.run
    if run.network.problem:
      return 'paused', 'Short circuit', run.network.problem
    supplied = 0.0
    for index, part in enumerate(self.circuit.parts):
      if isinstance(part, Source):
        supplied -= run.drops[index] * run.currents[index]
    words = speedWords(self.speed)
    details = 't = %s · %s · the sources deliver %s' % (
      si(run.time, 's'), words, si(supplied, 'W'))
    if self.running:
      return 'running', 'Running', details
    return 'paused', 'Paused', details

  def _start(self, ) -> None:
    """Starts the frames."""
    self.__frame_clock__ = None
    self.frameTimer.start(self.__frame_ms__)

  def _showAll(self, ) -> None:
    """Shows what the circuit reads now in the panel, the curves and the
    status."""
    self.panel.follow(self.run)
    self._showCurves()
    self.status.showState(*self.statusOf())

  def _startNode(self, ) -> int | None:
    """The node a new part starts from: the node selected last, or the
    second node of the part selected last, or the last node, or
    'None'."""
    view, circuit = self.circuitView, self.circuit
    for kind, index in view.selection[::-1]:
      if kind == 'node':
        return index
      return circuit.parts[index].second
    return len(circuit.nodes) - 1 if circuit.nodes else None

  def _loader(self, index: int) -> object:
    """What loads the example of 'index' when it is chosen."""

    def loader(*_) -> None:
      self.loadExample(index)

    return loader

  def _adder(self, kind: type) -> object:
    """What adds a part of 'kind' when its button is clicked."""

    def adder(*_) -> None:
      self.addPart(kind)

    return adder

  def _runOn(self, seconds: float, until: float) -> None:
    """Runs the circuit on 'seconds' in pieces no longer than
    'longestStep' allows, calling 'ran' after each, giving up the rest
    once the clock passes 'until'."""
    while seconds > 1e-12:
      step = min(seconds, max(self.longestStep(), 1e-6))
      self.run.advance(step)
      self.ran()
      seconds -= step
      if time.monotonic() > until:
        return

  def _edited(self, circuit: Circuit, part: tuple[str, int]) -> None:
    """Shows 'circuit' with 'part' selected."""
    self.setCircuit(circuit)
    self.circuitView.select(part)
    self.refresh()

  def _showCurves(self, ) -> None:
    """Plots the voltages and the currents against time: the part
    selected's, or the node selected's voltage, and each voltmeter's and
    ammeter's; nothing if the window has no curves."""
    if not self.curves():
      return
    run, view = self.run, self.circuitView
    circuit = self.circuit
    since = run.time - self.voltageCurve.window * 1.05
    samples = [s for s in run.samples if s.time >= since]
    volts, amps = [], []
    chosen = view.selected
    if chosen is not None and chosen[0] == 'node':
      index = chosen[1]
      volts.append(('N%d' % (index + 1),
                    [(s.time, s.voltages[index]) for s in samples]))
    elif chosen is not None:
      index = chosen[1]
      part = circuit.parts[index]
      if not isinstance(part, (Ammeter, Voltmeter)):
        volts.append(self._dropOf(index, samples))
        amps.append(self._currentOf(index, samples))
      if isinstance(part, Transistor):
        amps.append(('%s base' % circuit.label(index),
                     [(s.time, s.bases[index]) for s in samples]))
    for index, part in enumerate(circuit.parts):
      if isinstance(part, Voltmeter):
        volts.append(self._dropOf(index, samples))
      if isinstance(part, Ammeter):
        amps.append(self._currentOf(index, samples))
    self.voltageCurve.showSeries(
      'Voltage', 'V', self._coloured(volts),
      'Select a part, or add a voltmeter, to follow its voltage.')
    self.currentCurve.showSeries(
      'Current', 'A', self._coloured(amps),
      'Select a part, or add an ammeter, to follow its current.')

  def _dropOf(self, index: int, samples: list) -> tuple[str, list]:
    """The voltage across the part of 'index' at each sample, named."""
    part = self.circuit.parts[index]
    return (self.circuit.label(index),
            [(s.time, s.voltages[part.first] - s.voltages[part.second])
             for s in samples])

  def _currentOf(self, index: int, samples: list) -> tuple[str, list]:
    """The current through the part of 'index' at each sample, out of a
    source's plus pole, named."""
    sign = -1.0 if isinstance(self.circuit.parts[index], Source) else 1.0
    return (self.circuit.label(index),
            [(s.time, sign * s.currents[index]) for s in samples])

  @staticmethod
  def _coloured(series: list) -> tuple:
    """'series', each given a colour in turn."""
    return (*[(name, _COLORS[k % len(_COLORS)], line)
              for k, (name, line) in enumerate(series)],)
