"""
TestComputerQuests covers the computer quests: each is solved by its own
solution, built only of what was granted before it; none is solved as
it begins; the fetch's addresses and the computer's outputs are the
programs' own; a wrong program is noted wrong; the last quest's ROM is
loose, the rest fixed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Chip, program
from worQt.engineering.quests import COMPUTER, Clocked, FIBONACCI, MAIN
from worQt.engineering.quests import Progress, SUPER, TIMES

from . import QuestsTest, play


class TestComputerQuests(QuestsTest):
  """Tests for the computer quests."""

  def test_line(self) -> None:
    """Ten computer quests follow the super quests, granting the bus
    parts and the computer's chips; only the last leaves a part loose."""
    self.assertEqual(len(COMPUTER), 10)
    granted = [kind for quest in COMPUTER for kind in quest.reward]
    for name in ('SPLIT', 'JOIN', 'ADDB', 'ALU', 'REG', 'MUX', 'PC', 'DEC',
                 'ROM', 'CPU'):
      self.assertIn(name, granted)
    self.assertEqual([quest.loose for quest in COMPUTER], [0] * 9 + [1])

  def test_fair(self) -> None:
    """Each solution adds only what was granted before its quest."""
    progress = Progress()
    first = len(MAIN) + len(SUPER)
    for index in range(first):
      progress = progress.withDone(index)
    for k, quest in enumerate(COMPUTER):
      begun = quest.circuit()
      solved = quest.solution(begun)
      for part in solved.parts[len(begun.parts):]:
        self.assertIn(getattr(part, 'kind', type(part)),
                      progress.unlocked, quest.name)
      progress = progress.withDone(first + k)

  def test_solved(self) -> None:
    """Each computer quest's solution passes its bench."""
    for quest in COMPUTER:
      goal = quest.newGoal()
      run = play(quest.solution(quest.circuit()), goal, 0.02, 20.0)
      self.assertTrue(goal.reached, '%s: %s' % (quest.name,
                                                goal.words(run)))

  def test_programs(self) -> None:
    """The fetch wants the addresses 0, 1, 5, 6, 3; the computer OUT
    showing 0, 1, 2, 3, 5, 8, 13; the programmer 0, 3, 6, 9, 12, 15."""
    fetch, computer, programmer = COMPUTER[7], COMPUTER[8], COMPUTER[9]
    for quest, wanted in ((fetch, (0, 1, 5, 6, 3)),
                          (computer, (0, 1, 2, 3, 5, 8, 13)),
                          (programmer, (0, 3, 6, 9, 12, 15))):
      goal = quest.newGoal()
      self.assertIsInstance(goal, Clocked)
      play(quest.solution(quest.circuit()), goal, 0.02, 20.0)
      self.assertEqual(goal.notes(), wanted, quest.name)

  def test_wrong_program(self) -> None:
    """Fibonacci's program in the programmer's ROM is noted wrong, its
    words saying so."""
    quest = COMPUTER[9]
    begun = quest.circuit()
    rom = begun.parts[-1]
    wrong = begun.withPart(len(begun.parts) - 1,
                           Chip('ROM', rom.pins, program(FIBONACCI)))
    goal = quest.newGoal()
    run = play(wrong, goal, 0.02, 8.0)
    self.assertFalse(goal.reached)
    self.assertIn('went wrong', goal.words(run))
    right = begun.withPart(len(begun.parts) - 1,
                           Chip('ROM', rom.pins, program(TIMES)))
    goal = quest.newGoal()
    play(right, goal, 0.02, 8.0)
    self.assertTrue(goal.reached)
