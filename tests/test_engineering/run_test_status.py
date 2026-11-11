"""
RunTestStatus covers 'TestStatus', the strip along the bottom of the
window saying what is going on: a dot in the colour of what it is, what
it is in words, and the details; while a test runs, a bar along its
right keeps moving, so a running test cannot be taken for a stopped one.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.gui import TestStatus

from . import EngineeringWidgetTest


class RunTestStatus(EngineeringWidgetTest):
  """Tests for 'TestStatus'."""

  def openStatus(self) -> TestStatus:
    """A strip as wide as a window, shown live."""
    status = TestStatus()
    status.resize(900, status.sizeHint().height())
    self.showLive(status)
    return status

  def run_says_what_is_going_on(self) -> None:
    """It shows what is going on and its details; idle at first."""
    status = self.openStatus()
    self.assertEqual(status.mode, 'idle')
    status.showState('running', 'Compression test running', 'strain')
    self.assertEqual(status.mode, 'running')
    self.assertEqual(status.text, 'Compression test running')
    self.assertEqual(status.details, 'strain')
    self.assertFalse(status.grab().isNull())

  def run_moves_while_running(self) -> None:
    """While a test runs the bar keeps moving; paused or finished, it
    stands still."""
    status = self.openStatus()
    status.showState('running', 'Compression test running', '')
    self.assertTrue(status.moving)
    start = status.frame
    self.wait(300)
    self.assertGreater(status.frame, start)
    for mode in ('paused', 'finished', 'idle', 'casting'):
      status.showState(mode, mode, '')
      self.assertEqual(status.moving, mode == 'casting')

  def run_colours_its_dot(self) -> None:
    """Each state has a dot of its own colour."""
    status = self.openStatus()
    colours = set()
    for mode in ('idle', 'casting', 'running', 'paused', 'finished'):
      status.showState(mode, mode, '')
      colours.add(status.dotColor.Q.name())
    self.assertEqual(len(colours), 5)

  def run_refuses_what_is_no_state(self) -> None:
    """A state it does not know is refused."""
    status = self.openStatus()
    with self.assertRaises(ValueError):
      status.showState('dancing', '', '')
