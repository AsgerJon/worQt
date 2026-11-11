"""
QuestsWindow subclasses 'CircuitsWindow' and plays the quests: a
circuit begun, a goal, and parts unlocked by reaching it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os

from PySide6.QtCore import QStandardPaths
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ....windows import MainWindow
from ...circuits import Chip, Circuit, KINDS, Node, Run, SPECS
from ...circuits.gui import CircuitsWindow
from .. import Goal, Progress, QUESTS
from . import BUS_KINDS, BusToolBar, LOGIC_KINDS, LogicToolBar
from . import QuestPanel, QuestsToolBar
from ._quest_panel import SANDBOX, kindName


class QuestsWindow(CircuitsWindow):
  """
  QuestsWindow subclasses 'CircuitsWindow' and plays the quests: the
  'questPanel' on the left lists them, the quest played lit, its brief
  and how far it is from its goal under them; the circuit in the
  middle; the part selected on the right; the 'status' along the
  bottom. A quest begins as a circuit whose parts and nodes are fixed,
  never moved nor removed, though its switches work; the player adds
  parts of the kinds unlocked, the toolbar's others greyed out, joining
  them to the fixed nodes. The goal watches the circuit run, frame by
  frame; reached, the quest is done, its reward unlocked, and the
  progress saved to 'progressPath'. The sandbox, last, is free play
  with every part unlocked.

  The super quests follow the quests: logic on a test bench that sets
  its inputs itself, step by step, and checks its probes, each granting
  what it built as a chip, added from the logic row of buttons. The
  computer quests follow them: buses, the parts of a little computer,
  the computer itself and a program for it, from the third row.

  It opens on the first quest not done, or the sandbox once all are.
  'Start over' puts the quest back as it began; 'Reset' switches it on
  anew as it is.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Circuit quests'
  __start_size__ = 1760, 960
  __progress_file__ = 'circuit-quests.txt'

  #  Private Variables
  __quest_index__: int | None = None
  __quest_goal__: Goal | None = None
  __quest_progress__: Progress | None = None
  __progress_path__: str | None = None

  #  Public Variables
  toolBar = AttriBox[QuestsToolBar](THIS)
  logicBar = AttriBox[LogicToolBar](THIS)
  busBar = AttriBox[BusToolBar](THIS)
  questPanel = AttriBox[QuestPanel](THIS)

  #  Virtual Variables
  progress: Field[Progress] = Field()
  progressPath: Field[str] = Field()
  quest: Field[int] = Field()
  goal: Field[Goal] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @progress.GET
  def _getProgress(self, ) -> Progress:
    """The 'progress' getter returns how far the player has come, read
    from 'progressPath' the first time."""
    if self.__quest_progress__ is None:
      self.__quest_progress__ = Progress.load(self.progressPath)
    return self.__quest_progress__

  @progressPath.GET
  def _getProgressPath(self, ) -> str:
    """The 'progressPath' getter returns the file the progress is kept
    in: in the user's data folder, unless set."""
    if self.__progress_path__ is None:
      place = QStandardPaths.StandardLocation.GenericDataLocation
      folder = QStandardPaths.writableLocation(place)
      self.__progress_path__ = os.path.join(folder, 'worQt',
                                            self.__progress_file__)
    return self.__progress_path__

  @quest.GET
  def _getQuest(self, ) -> int | None:
    """The 'quest' getter returns the quest played, -1 for the sandbox,
    or 'None'."""
    return self.__quest_index__

  @goal.GET
  def _getGoal(self, ) -> Goal | None:
    """The 'goal' getter returns the goal of the quest played, watching
    the circuit, or 'None' in the sandbox."""
    return self.__quest_goal__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @progressPath.SET
  def _setProgressPath(self, path: str) -> None:
    """The 'progressPath' setter keeps the progress in the file at
    'path', read anew."""
    self.__progress_path__ = str(path)
    self.__quest_progress__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the window out, sizes it and opens the
    first quest not done."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 3)
    layout.addWidget(self.logicBar, 1, 0, 1, 3)
    layout.addWidget(self.busBar, 2, 0, 1, 3)
    layout.addWidget(self.questPanel, 3, 0)
    layout.addWidget(self.circuitView, 3, 1)
    layout.addWidget(self.panel, 3, 2)
    layout.addWidget(self.status, 4, 0, 1, 3)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    layout.setColumnStretch(2, 0)
    layout.setRowStretch(3, 1)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.circuitView.setFocus()
    progress = self.progress
    first = [i for i in range(len(QUESTS)) if not progress.isDone(i)]
    self.loadQuest(first[0] if first else SANDBOX)
    self._start()

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the circuits' buttons and edits, and
    the quests'."""
    CircuitsWindow.initLogic(self)
    for button, kind in zip(self.logicBar.buttons(), LOGIC_KINDS):
      button.clicked.connect(self._logicAdder(kind))
    for button, kind in zip(self.busBar.buttons(), BUS_KINDS):
      button.clicked.connect(self._logicAdder(kind))
    self.questPanel.questChosen.connect(self.loadQuest)
    self.questPanel.startButton.clicked.connect(self.startOver)

  def curves(self, ) -> tuple:
    """The 'curves' method returns no curves: the quests plot none."""
    return ()

  def ran(self, ) -> None:
    """The 'ran' method watches the circuit for the goal, and when it is
    reached, marks the quest done, unlocks its reward and saves the
    progress."""
    goal, index = self.goal, self.quest
    if goal is None or index is None or index < 0:
      return
    goal.update(self.run)
    changed = goal.drive(self.run)
    if changed is not None:
      view = self.circuitView
      view.circuit = changed
      view.run = Run(changed, self.run)
    if goal.reached and not self.progress.isDone(index):
      self.__quest_progress__ = self.progress.withDone(index)
      try:
        self.progress.save(self.progressPath)
      except OSError as exception:
        self.panel.showNote('The progress could not be saved: %s.'
                            % exception)
      self.refresh()

  def longestStep(self, ) -> float:
    """The 'longestStep' method returns how long the circuit may run on
    before the goal must watch it again: until a test bench's next step
    or a clock's next tick, so a fast speed misses none."""
    goal, index = self.goal, self.quest
    if goal is None or index is None or index < 0:
      return math.inf
    return goal.longest(self.run)

  def reset(self, ) -> None:
    """The 'reset' method switches the circuit on anew as it is, the
    goal watching it anew."""
    self.circuitView.run = Run(self.circuit)
    self._newGoal()
    self.refresh()

  def addPart(self, kind: type) -> None:
    """The 'addPart' method adds a part of 'kind' if it is unlocked."""
    if kind not in self.progress.unlocked:
      return self.panel.showNote('%s is not unlocked yet.'
                                 % kindName(kind))
    CircuitsWindow.addPart(self, kind)

  def refresh(self, ) -> None:
    """The 'refresh' method shows the circuit as the circuits' window
    does, greys out the parts not unlocked, and shows the quests."""
    CircuitsWindow.refresh(self)
    unlocked = self.progress.unlocked
    for button, kind in zip(self.toolBar.partButtons(), KINDS):
      button.setEnabled(True if kind in unlocked else False)
      button.update()
    for bar, kinds in ((self.logicBar, LOGIC_KINDS),
                       (self.busBar, BUS_KINDS)):
      for button, kind in zip(bar.buttons(), kinds):
        button.setEnabled(True if kind in unlocked else False)
        button.update()
    self._showQuest()

  def statusOf(self, ) -> tuple[str, str, str]:
    """The 'statusOf' method says what is going on, and that the quest
    is done when it is."""
    goal = self.goal
    if goal is not None and goal.reached and self.quest is not None:
      reward = ', '.join(map(kindName, QUESTS[self.quest].reward))
      if self.quest == len(QUESTS) - 1:
        return 'finished', 'Quest done', 'Every quest is done'
      if not reward:
        return 'finished', 'Quest done', 'Nothing new to unlock'
      return 'finished', 'Quest done', 'Unlocked: %s' % reward
    return CircuitsWindow.statusOf(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def loadQuest(self, index: int) -> None:
    """The 'loadQuest' method plays the quest of 'index', as it begins,
    its parts fixed, at its speed; or the sandbox, empty, for -1. A
    quest not open yet is not played."""
    if index != SANDBOX and not self.progress.isOpen(index):
      return
    self.__quest_index__ = index
    circuit = Circuit((), ())
    speed = 1.0
    if index != SANDBOX:
      circuit = QUESTS[index].circuit()
      speed = QUESTS[index].speed
    view = self.circuitView
    view.select(None)
    view.circuit = circuit
    locked = (len(circuit.nodes), len(circuit.parts))
    if index == SANDBOX:
      locked = (0, 0)
    if index != SANDBOX:
      loose = QUESTS[index].loose
      locked = (locked[0], locked[1] - loose)
    view.locked = locked
    self.panel.locked = locked
    view.run = Run(circuit)
    self._newGoal()
    self.panel.showNote('')
    self.setSpeed(speed)

  def startOver(self, ) -> None:
    """The 'startOver' method puts the quest played back as it began."""
    if self.quest is not None:
      self.loadQuest(self.quest)

  def addLogic(self, kind: object) -> None:
    """The 'addLogic' method adds a logic part, or a chip of the kind
    named 'kind', if it is granted."""
    if isinstance(kind, str):
      try:
        return self.addChip(kind)
      except ValueError as exception:
        return self.refuse(str(exception))
    self.addPart(kind)

  def addChip(self, name: str) -> None:
    """The 'addChip' method adds a chip of the kind named 'name', if it is
    granted, selected: its inputs in a column two steps or more right of
    the node selected, or the last, its outputs four steps right of
    them, each on a new node."""
    if name not in self.progress.unlocked:
      return self.panel.showNote('%s is not granted yet.' % name)
    spec = SPECS[name]
    circuit = self.circuit
    start = self._startNode()
    x, y = circuit.nodes[start] if start is not None else (0.0, 0.0)
    inputs, outputs = len(spec.ins), len(spec.outs)
    shift = (inputs - outputs) // 2
    for step in range(1, 40):
      left = x + 2 * step
      spots = [(left, y - k) for k in range(inputs)]
      spots += [(left + 4, y - shift - k) for k in range(outputs)]
      if all(circuit.at(*spot) is None for spot in spots):
        break
    else:
      return self.panel.showNote('There is no room for the chip there.')
    count = len(circuit.nodes)
    grown = circuit.withNodes(*circuit.nodes,
                              *[Node(*spot) for spot in spots])
    chip = Chip(name, (*range(count, count + len(spots)),))
    self._edited(grown.withParts(*grown.parts, chip),
                 ('part', len(grown.parts)))

  def _logicAdder(self, kind: object) -> object:
    """What adds a logic part or a chip of 'kind' when its button is
    clicked."""

    def adder(*_) -> None:
      self.addLogic(kind)

    return adder

  def _newGoal(self, ) -> None:
    """Sets the goal of the quest played watching anew, the circuit as
    it is now its first sight."""
    index = self.quest
    self.__quest_goal__ = None
    if index is not None and index != SANDBOX:
      self.__quest_goal__ = QUESTS[index].newGoal()
      self.ran()

  def _showAll(self, ) -> None:
    """Shows what the circuit reads now, and how far the goal is."""
    CircuitsWindow._showAll(self)
    self._showQuest()

  def _showQuest(self, ) -> None:
    """Shows the quests, the one played and how far its goal is."""
    goal = self.goal
    words = goal.words(self.run) if goal is not None else ''
    reached = goal.reached if goal is not None else False
    self.questPanel.showQuest(self.progress, self.quest, words, reached)
