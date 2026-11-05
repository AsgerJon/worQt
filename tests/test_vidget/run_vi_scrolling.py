"""
RunViScrolling covers how 'Vidget' scrolls a text longer than its view:
following the cursor, the Ctrl keys, 'zt zz zb', 'H M L' and the wheel,
and the line numbers beside it all.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt, QEvent
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from worQt.vidget import Vidget

from . import VidgetTest

_LINES = '\n'.join('line %d' % number for number in range(1, 101))


class RunViScrolling(VidgetTest):
  """Tests for scrolling in 'Vidget'."""

  def _line(self, vidget: Vidget) -> int:
    """The line the cursor is on, counted from 0."""
    return vidget.lineNumberAt(vidget.cursor)

  def _wheel(self, vidget: Vidget, notches: int) -> None:
    """Turn the wheel 'notches' notches, down when negative."""
    center = QPointF(vidget.rect().center())
    event = QWheelEvent(
      center, QPointF(vidget.mapToGlobal(center.toPoint())),
      QPoint(0, 0), QPoint(0, notches * 120),
      Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
      Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(vidget, event)
    vidget.repaint()

  def run_follows_the_cursor(self) -> None:
    """The view scrolls as little as it takes to keep the cursor in it."""
    vidget = self.liveVidget(_LINES)
    self.keys(vidget, 'G')
    vidget.repaint()
    self.assertEqual(self._line(vidget), 99)
    self.assertGreater(vidget.scrollTop, 0)
    self.keys(vidget, 'gg')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, 0)

  def run_half_and_whole_views(self) -> None:
    """Ctrl+D and Ctrl+U scroll half a view and take the cursor along;
    Ctrl+F and Ctrl+B a whole view, less two rows."""
    vidget = self.liveVidget(_LINES)
    rows = vidget._rowsShown()
    self.ctrl(vidget, 'd')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, rows // 2)
    self.assertEqual(self._line(vidget), rows // 2)
    self.ctrl(vidget, 'u')
    vidget.repaint()
    self.assertEqual((vidget.scrollTop, self._line(vidget)), (0, 0))
    self.ctrl(vidget, 'f')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, rows - 2)
    self.ctrl(vidget, 'b')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, 0)

  def run_scroll_by_rows(self) -> None:
    """Ctrl+E and Ctrl+Y scroll a row; the cursor stays put unless the
    view would leave it behind."""
    vidget = self.liveVidget(_LINES)
    self.keys(vidget, '5j')
    self.ctrl(vidget, 'e')
    vidget.repaint()
    self.assertEqual((vidget.scrollTop, self._line(vidget)), (1, 5))
    self.ctrl(vidget, 'y')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, 0)
    self.keys(vidget, 'gg')
    self.ctrl(vidget, 'e')
    vidget.repaint()
    self.assertEqual(self._line(vidget), 1)

  def run_cursor_line_placement(self) -> None:
    """'zt', 'zz' and 'zb' scroll the cursor's line to the top, the
    middle and the bottom of the view."""
    vidget = self.liveVidget(_LINES)
    rows = vidget._rowsShown()
    self.keys(vidget, '50G')
    self.keys(vidget, 'zt')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, 49)
    self.keys(vidget, 'zz')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, 49 - (rows - 1) // 2)
    self.keys(vidget, 'zb')
    vidget.repaint()
    self.assertEqual(vidget.scrollTop, 49 - (rows - 1))

  def run_view_motions(self) -> None:
    """'H', 'M' and 'L' go to the top, middle and bottom of the view."""
    vidget = self.liveVidget(_LINES)
    rows = vidget._rowsShown()
    self.keys(vidget, 'L')
    self.assertEqual(self._line(vidget), rows - 1)
    self.keys(vidget, 'M')
    self.assertEqual(self._line(vidget), (rows - 1) // 2)
    self.keys(vidget, 'H')
    self.assertEqual(self._line(vidget), 0)

  def run_wheel(self) -> None:
    """The wheel scrolls three rows a notch, taking the cursor along
    where the view would leave it behind."""
    vidget = self.liveVidget(_LINES)
    self._wheel(vidget, -2)
    self.assertEqual(vidget.scrollTop, 6)
    self.assertEqual(self._line(vidget), 6)
    self._wheel(vidget, 1)
    self.assertEqual(vidget.scrollTop, 3)

  def run_line_numbers(self) -> None:
    """The gutter is wide enough for the last line's number, and never
    narrower than three digits."""
    short = self.vidget('one line')
    long = self.vidget('\n' * 12345)
    self.assertGreater(long.gutterWidth, short.gutterWidth)
    self.assertEqual(short.gutterWidth, self.vidget('a\nb').gutterWidth)

  def run_paints_scrolled(self) -> None:
    """A scrolled vidget paints, line numbers and all."""
    vidget = self.liveVidget(_LINES)
    self.keys(vidget, 'G')
    self.assertFalse(vidget.grab().isNull())
