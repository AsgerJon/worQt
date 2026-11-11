"""
TestQuests covers the line of quests: the parts unlocked along it cover
every kind; each quest is solved by its own solution, built only of the
parts unlocked before it, its fixed parts untouched; none is solved as
it begins; and the wrong answers stay wrong. The super quests are
solved in 'TestSuperQuests'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.circuits import Diode, KINDS, LOGIC, Resistor, SPECS
from worQt.engineering.circuits import Transistor
from worQt.engineering.quests import MAIN, Progress, QUESTS, STARTING
from worQt.engineering.quests import glowOf

from . import QuestsTest, play

#  The switches each quest's solution works, at a time: the switch and
#  whether it is closed
_ACTIONS = {
  'On and off'  : ((0.2, 3, True), (0.6, 3, False), (1.0, 3, True)),
  'Afterglow'   : ((0.5, 1, False),),
  'Touch switch': ((0.6, 5, True),),
}


class TestQuests(QuestsTest):
  """Tests for 'QUESTS'."""

  def test_line(self) -> None:
    """There are eight quests, eleven super quests, ten computer quests
    and five microprocessor quests, named once; what they unlock, with
    what a player starts with, is every kind of part, every logic part
    and every chip, each once."""
    names = [quest.name for quest in QUESTS]
    self.assertEqual(len(MAIN), 8)
    self.assertEqual(len(names), 34)
    self.assertEqual(len(set(names)), 34)
    rewards = [*STARTING]
    for quest in QUESTS:
      rewards += [*quest.reward]

    def named(kind: object) -> str:
      return kind if isinstance(kind, str) else kind.__name__

    everything = [*KINDS, *LOGIC, *SPECS]
    self.assertEqual(sorted(map(named, rewards)),
                     sorted(map(named, everything)))

  def test_fair(self) -> None:
    """Each solution keeps the quest's own parts as they were, first,
    and adds only parts unlocked before it."""
    progress = Progress()
    for index, quest in enumerate(QUESTS):
      begun = quest.circuit()
      solved = quest.solution(begun)
      count = len(begun.parts)
      self.assertEqual(solved.parts[:count], begun.parts, quest.name)
      self.assertEqual(solved.nodes[:len(begun.nodes)], begun.nodes)
      for part in solved.parts[count:]:
        kind = getattr(part, 'kind', type(part))
        self.assertIn(kind, progress.unlocked, quest.name)
      progress = progress.withDone(index)

  def test_solved(self) -> None:
    """Each of the first quests' solutions reaches its goal, its switches
    worked as its brief says, within a few seconds at its speed."""
    for quest in MAIN:
      goal = quest.newGoal()
      frame = 0.02 * quest.speed
      seconds = 4.0 if quest.speed == 1.0 else 0.3
      play(quest.solution(quest.circuit()), goal, frame, seconds,
           *_ACTIONS.get(quest.name, ()))
      self.assertTrue(goal.reached, quest.name)

  def test_begun(self) -> None:
    """No quest is reached as it begins, nothing added, its own switches
    worked."""
    for quest in QUESTS:
      goal = quest.newGoal()
      begun = quest.circuit()
      actions = [action for action in _ACTIONS.get(quest.name, ())
                 if action[1] < len(begun.parts)]
      seconds = 2.0 if quest.speed == 1.0 else 0.3
      play(begun, goal, 0.02 * quest.speed, seconds, *actions)
      self.assertFalse(goal.reached, quest.name)

  def test_wrong(self) -> None:
    """A light emitting diode behind 100 Ω burns; a diode turned round
    lets nothing forward; one transistor alone is too weak for the
    touch switch, the diode glowing at about 4 %."""
    quest = QUESTS[2]
    begun = quest.circuit()
    goal = quest.newGoal()
    play(begun.withParts(*begun.parts, Resistor(1, 3, 100.0)), goal, 0.02,
         4.0)
    self.assertFalse(goal.reached)
    quest = QUESTS[5]
    begun = quest.circuit()
    goal = quest.newGoal()
    play(begun.withParts(*begun.parts, Diode(2, 1, 0.7)), goal, 0.0002,
         0.3)
    self.assertFalse(goal.reached)
    quest = QUESTS[6]
    begun = quest.circuit()
    goal = quest.newGoal()
    run = play(begun.withParts(*begun.parts, Transistor(5, 8, 7, 100.0)),
               goal, 0.02, 3.0, (0.6, 5, True))
    self.assertFalse(goal.reached)
    self.assertLess(glowOf(run, 4), 0.05)
