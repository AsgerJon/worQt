"""
TestProgress covers 'Progress': nothing done to start with, the
starting parts unlocked; quests opened in turn; rewards unlocked; the
text kept on disk read back, names of no quest passed over; saved and
loaded, a missing file nothing done.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worQt.engineering.circuits import KINDS, LOGIC, Lamp, Resistor, SPECS
from worQt.engineering.circuits import Source, Switch, Wire
from worQt.engineering.quests import Progress, QUESTS

from . import QuestsTest


class TestProgress(QuestsTest):
  """Tests for 'Progress'."""

  def test_start(self) -> None:
    """At first nothing is done, a wire, a source and a lamp are
    unlocked, and only the first quest is open."""
    progress = Progress()
    self.assertEqual(progress.done, ())
    self.assertEqual(progress.unlocked, (Wire, Source, Lamp))
    self.assertTrue(progress.isOpen(0))
    self.assertFalse(progress.isOpen(1))
    self.assertFalse(progress.isDone(0))

  def test_done(self) -> None:
    """A quest done unlocks its reward and opens the next, in the order
    of the quests whatever order they were done in."""
    progress = Progress().withDone(0)
    self.assertTrue(progress.isDone(0))
    self.assertTrue(progress.isOpen(1))
    self.assertIn(Switch, progress.unlocked)
    progress = progress.withDone(1)
    self.assertIn(Resistor, progress.unlocked)
    self.assertEqual(progress.done, (QUESTS[0].name, QUESTS[1].name))
    self.assertEqual(Progress().withDone(1).done, (QUESTS[1].name,))
    self.assertFalse(Progress().withDone(1).isOpen(1))

  def test_text(self) -> None:
    """Its text is a done quest's name a line, read back; names of no
    quest and blank lines are passed over."""
    progress = Progress().withDone(0).withDone(1)
    self.assertEqual(str(progress), '%s\n%s\n' % (QUESTS[0].name,
                                                  QUESTS[1].name))
    self.assertEqual(Progress(str(progress)).done, progress.done)
    read = Progress('\n  %s  \nNo such quest\n' % QUESTS[2].name)
    self.assertEqual(read.done, (QUESTS[2].name,))

  def test_file(self) -> None:
    """Saved, its folder made, and loaded, it is as it was; a file there
    is not loads as nothing done."""
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'deeper', 'quests.txt')
      self.assertEqual(Progress.load(path).done, ())
      progress = Progress().withDone(0)
      progress.save(path)
      self.assertEqual(Progress.load(path).done, progress.done)

  def test_granted(self) -> None:
    """With every quest done, everything is granted: the parts, the logic
    parts, then the chips, in their order."""
    names = ''.join('%s\n' % quest.name for quest in QUESTS)
    unlocked = Progress(names).unlocked
    self.assertEqual(unlocked, (*KINDS, *LOGIC, *SPECS))
    self.assertNotIn('NAND', Progress().unlocked)
