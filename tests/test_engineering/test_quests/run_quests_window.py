"""
RunQuestsWindow covers 'QuestsApp' and its 'QuestsWindow': it opens on
the first quest, its parts fixed, the parts not unlocked greyed out;
solved, the quest is done, its reward unlocked, the next open and the
progress saved; a quest not open is not played; 'Start over' puts the
quest back; the sandbox is free and empty; a super quest's bench sets
its inputs itself, the logic buttons granted in turn, a chip added
where there is room; the quest list folds into sections; the
programmer's ROM is written through its editor, offering what the first
computer carries out, and the calculator's, the last, offering all of
the 4004's instructions; a clocked quest run on in one long step misses
no tick, the speed slider then set by the quest.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worQt.engineering.circuits import FIRST, ISA, Bit, Chip, Switch, Wire
from worQt.engineering.circuits import decoded, words
from worQt.engineering.quests import COMPUTER, DIGIT, MAIN, Progress
from worQt.engineering.quests import QUESTS, TIMES
from worQt.engineering.quests.gui import QuestsApp, QuestsWindow

from . import QuestsWidgetTest


class RunQuestsWindow(QuestsWidgetTest):
  """Tests for 'QuestsApp' and 'QuestsWindow'."""

  __application_type__ = QuestsApp

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)

  def openWindow(self, path: str) -> QuestsWindow:
    """The window, its progress kept at 'path', shown live, paused."""
    window = QuestsWindow()
    window.progressPath = path
    self.showLive(window)
    if window.running:
      window.togglePlay()
    return window

  def run_opens(self) -> None:
    """With nothing done it opens on the first quest, its parts and nodes
    fixed, only a wire, a source and a lamp to add."""
    with tempfile.TemporaryDirectory() as folder:
      window = self.openWindow(os.path.join(folder, 'quests.txt'))
      self.assertEqual(window.windowTitle(), 'Circuit quests')
      self.assertEqual(window.quest, 0)
      self.assertEqual(window.circuitView.locked, (4, 2))
      bar = window.toolBar
      self.assertTrue(bar.wireButton.isEnabled())
      self.assertFalse(bar.switchButton.isEnabled())
      self.assertFalse(bar.examplesButton.isVisible())
      self.assertEqual(window.questPanel.stateOf(1), 'shut')
      window.circuitView.select(('part', 1))
      window.circuitView.removeSelected()
      self.assertEqual(len(window.circuit.parts), 2)
      self.assertTrue(window.panel.isFixed())
      window.addPart(Switch)
      self.assertEqual(len(window.circuit.parts), 2)
      window.close()

  def run_first_light(self) -> None:
    """Two wires light the lamp; a second later the quest is done, the
    switch unlocked, the next quest open and the progress saved."""
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'quests.txt')
      window = self.openWindow(path)
      view, bar = window.circuitView, window.toolBar
      view.select(('node', 1))
      view.toggle(('node', 3))
      self.click(bar.wireButton)
      view.select(('node', 0))
      view.toggle(('node', 2))
      self.click(bar.wireButton)
      self.assertEqual(window.circuit.parts[-1], Wire(0, 2))
      for _ in range(60):
        window.advance(0.02)
      self.assertTrue(window.goal.reached)
      self.assertEqual(window.status.text, 'Quest done')
      self.assertTrue(bar.switchButton.isEnabled())
      self.assertEqual(window.questPanel.stateOf(0), 'done')
      self.assertEqual(window.questPanel.stateOf(1), 'open')
      self.assertEqual(Progress.load(path).done, (QUESTS[0].name,))
      window.close()

  def run_choose(self) -> None:
    """A quest not open is not played; one open is, as it begins; 'Start
    over' takes away what was added; the sandbox is empty and free."""
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'quests.txt')
      Progress().withDone(0).save(path)
      window = self.openWindow(path)
      self.assertEqual(window.quest, 1)
      window.loadQuest(4)
      self.assertEqual(window.quest, 1)
      window.questPanel.questChosen.emit(0)
      self.assertEqual(window.quest, 0)
      window.circuitView.select(('node', 1))
      window.circuitView.toggle(('node', 3))
      window.addPart(Wire)
      self.assertEqual(len(window.circuit.parts), 3)
      self.click(window.questPanel.startButton)
      self.assertEqual(len(window.circuit.parts), 2)
      window.loadQuest(-1)
      self.assertEqual(window.quest, -1)
      self.assertEqual(len(window.circuit.parts), 0)
      self.assertEqual(window.circuitView.locked, (0, 0))
      self.assertIsNone(window.goal)
      window.close()

  def run_super(self) -> None:
    """With the first quests done, the first super quest opens, its bench
    setting A itself; its inputs and probes, but no chips, may be added
    once it is done."""
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'quests.txt')
      progress = Progress()
      for index in range(len(MAIN)):
        progress = progress.withDone(index)
      progress.save(path)
      window = self.openWindow(path)
      self.assertEqual(window.quest, len(MAIN))
      logic = window.logicBar
      self.assertFalse(logic.inputButton.isEnabled())
      self.assertFalse(logic.notButton.isEnabled())
      for _ in range(20):
        window.advance(0.02)
      bits = [p for p in window.circuit.parts if isinstance(p, Bit)]
      self.assertTrue(bits[0].high)
      quest = QUESTS[window.quest]
      window.setCircuit(quest.solution(quest.circuit()))
      for _ in range(80):
        window.advance(0.02)
      self.assertTrue(window.goal.reached)
      self.assertTrue(logic.notButton.isEnabled())
      self.assertTrue(logic.inputButton.isEnabled())
      self.assertFalse(logic.nandButton.isEnabled())
      window.loadQuest(-1)
      self.click(logic.notButton)
      chip = window.circuit.parts[-1]
      self.assertEqual(chip, Chip('NOT', (0, 1)))
      self.assertEqual(window.panel.kind, 'chip')
      window.addChip('NAND')
      self.assertEqual(len(window.circuit.parts), 1)
      window.close()

  def openAt(self, folder: str, quest: int) -> QuestsWindow:
    """The window, every quest before that of 'quest' done."""
    path = os.path.join(folder, 'quests.txt')
    progress = Progress()
    for index in range(quest):
      progress = progress.withDone(index)
    progress.save(path)
    return self.openWindow(path)

  def write(self, window: QuestsWindow, program: tuple) -> None:
    """Writes 'program' into the ROM selected through its editor's
    menus, an instruction then its operand, where it takes one."""
    editor = window.panel.programEditor
    for row, (op, arg) in enumerate(program):
      instruction = decoded(op, arg)
      actions = editor.menuFor(row, False).actions()
      [a for a in actions
       if a.text().startswith(instruction.mnemonic + ',')][0].trigger()
      if instruction.takes:
        editor.menuFor(row, True).actions()[arg].trigger()

  def run_programmer(self) -> None:
    """The programmer opens in the computer section, its ROM loose, its
    editor live, offering what the first computer carries out; the
    three times table written through its menus reaches the goal."""
    with tempfile.TemporaryDirectory() as folder:
      quest = QUESTS.index(COMPUTER[9])
      window = self.openAt(folder, quest)
      self.assertEqual(window.quest, quest)
      self.assertEqual(window.questPanel.openSection, 2)
      self.assertTrue(window.busBar.cpuButton.isEnabled())
      self.assertFalse(window.busBar.mpuButton.isEnabled())
      rom = len(window.circuit.parts) - 1
      self.assertEqual(window.circuitView.locked[1], rom)
      window.circuitView.select(('part', rom))
      editor = window.panel.programEditor
      self.assertTrue(editor.isVisible())
      self.assertTrue(editor.isEnabled())
      self.assertEqual([i.mnemonic for i in editor.instructions],
                       [*FIRST])
      self.write(window, TIMES)
      written = words(window.circuit.parts[rom].contents)
      self.assertEqual(written[:len(TIMES)], TIMES)
      for _ in range(300):
        window.advance(0.02)
      self.assertTrue(window.goal.reached)
      self.assertEqual(window.status.text, 'Quest done')
      self.assertEqual(window.status.details, 'Nothing new to unlock')
      window.close()

  def run_calculator(self) -> None:
    """With all but the last quest done, the list opens on the
    microprocessor section; the calculator's ROM offers every
    instruction, registers named so; the decimal digit written through
    its menus reaches the goal, every quest then done."""
    with tempfile.TemporaryDirectory() as folder:
      window = self.openAt(folder, len(QUESTS) - 1)
      self.assertEqual(window.quest, len(QUESTS) - 1)
      self.assertEqual(window.questPanel.openSection, 3)
      self.assertTrue(window.busBar.mpuButton.isEnabled())
      rom = len(window.circuit.parts) - 1
      window.circuitView.select(('part', rom))
      editor = window.panel.programEditor
      self.assertEqual(len(editor.instructions), len(ISA))
      self.write(window, ((11, 5),))
      self.assertEqual([a.text() for a in
                        editor.menuFor(0, True).actions()][:2],
                       ['R0', 'R1'])
      self.write(window, DIGIT)
      written = words(window.circuit.parts[rom].contents)
      self.assertEqual(written[:len(DIGIT)], DIGIT)
      for _ in range(700):
        window.advance(0.02)
      self.assertTrue(window.goal.reached)
      self.assertEqual(window.status.details, 'Every quest is done')
      window.close()

  def run_long_steps(self) -> None:
    """The fetch quest, solved and run on three seconds at once, notes
    every tick of its clock, reaching its goal; a quest sets the speed
    slider to its own speed."""
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'quests.txt')
      fetch = QUESTS.index(COMPUTER[7])
      progress = Progress()
      for index in range(fetch):
        progress = progress.withDone(index)
      progress.save(path)
      window = self.openWindow(path)
      self.assertEqual(window.quest, fetch)
      quest = QUESTS[fetch]
      window.setCircuit(quest.solution(quest.circuit()))
      window.advance(0.001)
      self.assertLess(window.longestStep(), 0.1 + 1e-6)
      window.advance(3.0)
      self.assertTrue(window.goal.reached)
      self.assertEqual(window.goal.notes(), (0, 1, 5, 6, 3))
      window.loadQuest(QUESTS.index(MAIN[5]))
      self.assertEqual(window.toolBar.speedSlider.speed, 0.01)
      window.close()
