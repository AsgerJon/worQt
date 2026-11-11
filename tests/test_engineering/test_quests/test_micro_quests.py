"""
TestMicroQuests covers the microprocessor quests, after Intel's 4004:
each is solved by its own solution, built only of what was granted
before it; none is solved as it begins; the microprocessor counts down
by threes and the calculator's program counts a decimal digit; a wrong
program is noted wrong; only the last quest's ROM is loose.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Chip, program
from worQt.engineering.quests import COMPUTER, COUNTDOWN, Clocked, DIGIT
from worQt.engineering.quests import MAIN, MICRO, Progress, QUESTS, SUPER
from worQt.engineering.quests import TIMES, outputs

from . import QuestsTest, play


class TestMicroQuests(QuestsTest):
  """Tests for the microprocessor quests."""

  def test_line(self) -> None:
    """Five microprocessor quests come last, granting the register file,
    the stack, the accumulator and the microprocessor; only the last
    leaves a part loose."""
    self.assertEqual(len(MICRO), 5)
    self.assertEqual(QUESTS[-len(MICRO):], MICRO)
    self.assertEqual([quest.reward for quest in MICRO],
                     [('RF',), ('STACK',), ('ACC',), ('MPU',), ()])
    self.assertEqual([quest.loose for quest in MICRO], [0, 0, 0, 0, 1])

  def test_fair(self) -> None:
    """Each solution adds only what was granted before its quest."""
    progress = Progress()
    first = len(MAIN) + len(SUPER) + len(COMPUTER)
    for index in range(first):
      progress = progress.withDone(index)
    for k, quest in enumerate(MICRO):
      begun = quest.circuit()
      solved = quest.solution(begun)
      for part in solved.parts[len(begun.parts):]:
        self.assertIn(getattr(part, 'kind', type(part)),
                      progress.unlocked, quest.name)
      progress = progress.withDone(first + k)

  def test_solved(self) -> None:
    """Each microprocessor quest's solution passes its bench, and none
    passes as it begins."""
    for quest in MICRO:
      goal = quest.newGoal()
      run = play(quest.solution(quest.circuit()), goal, 0.02, 20.0)
      self.assertTrue(goal.reached, '%s: %s' % (quest.name,
                                                goal.words(run)))
      goal = quest.newGoal()
      play(quest.circuit(), goal, 0.02, 2.0)
      self.assertFalse(goal.reached, quest.name)

  def test_programs(self) -> None:
    """The countdown shows 15, 12, 9, 6, 3, 0; the decimal digit 1 to 9
    and round to 0, as the quests want them."""
    self.assertEqual(outputs(COUNTDOWN, 16, 3), (0, 15, 12, 9, 6, 3, 0))
    self.assertEqual(outputs(DIGIT, 16, 3), (0, *range(1, 10), 0))
    for quest, wanted in ((MICRO[3], outputs(COUNTDOWN, 16, 3)),
                          (MICRO[4], outputs(DIGIT, 16, 3))):
      goal = quest.newGoal()
      self.assertIsInstance(goal, Clocked)
      play(quest.solution(quest.circuit()), goal, 0.02, 20.0)
      self.assertEqual(goal.notes(), wanted, quest.name)

  def test_wrong_program(self) -> None:
    """The three times table in the calculator's ROM is noted wrong, its
    words saying so."""
    quest = MICRO[4]
    begun = quest.circuit()
    rom = begun.parts[-1]
    wrong = begun.withPart(len(begun.parts) - 1,
                           Chip('ROM', rom.pins, program(TIMES)))
    goal = quest.newGoal()
    run = play(wrong, goal, 0.02, 4.0)
    self.assertFalse(goal.reached)
    self.assertIn('went wrong', goal.words(run))
