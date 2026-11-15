"""
A window's readings (what its status line said: the time, the frames
a second, what the physics and the car do) in a dock window of their
own (user, 2026-11-14: "put the text from the statusbars into a
dockable window"): docked at the window's side or floated anywhere, a
line a reading, the text selectable to copy, never taking the keys
from the view. 'readingsOf' puts one on a window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel, QMainWindow

#  How wide the readings are at least, px, and the gap between a status
#  line's readings (four spaces: each its own line in the dock).
READINGS_WIDTH = 340
GAP = '    '


class Readings(QLabel):
  """Readings is the text of a window's readings: what it is set to is
  shown a reading a line (the status line's readings, 'GAP' apart, each
  on its own), top left, wrapped where a line is wider than the dock,
  selectable with the mouse to copy, never focused (the keys stay the
  view's)."""

  def __init__(self, ) -> None:
    QLabel.__init__(self, '')
    self.setAlignment(Qt.AlignmentFlag.AlignTop
                      | Qt.AlignmentFlag.AlignLeft)
    self.setWordWrap(True)
    self.setTextInteractionFlags(
      Qt.TextInteractionFlag.TextSelectableByMouse)
    self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.setMargin(8)
    self.setMinimumWidth(READINGS_WIDTH)

  def setText(self, text: str) -> None:
    """Shows 'text' a reading a line (its readings 'GAP' apart, each on
    its own, trimmed; its own lines kept)."""
    lines = [part.strip() for line in text.split('\n')
             for part in line.split(GAP) if part.strip()]
    QLabel.setText(self, '\n'.join(lines))


class ReadingsDock(QDockWidget):
  """ReadingsDock is the dock window holding a window's readings
  ('readings'), titled so; moved to any side of its window or floated,
  never closed (nothing would open it again), never focused."""

  def __init__(self, window: QMainWindow) -> None:
    QDockWidget.__init__(self, 'Readings', window)
    self.setObjectName('readings')
    features = QDockWidget.DockWidgetFeature
    self.setFeatures(features.DockWidgetMovable
                     | features.DockWidgetFloatable)
    self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.readings = Readings()
    self.setWidget(self.readings)


def readingsOf(window: QMainWindow) -> Readings:
  """The 'readingsOf' function docks a 'ReadingsDock' at 'window''s right
  side and returns its readings (set their text as a status line's)."""
  dock = ReadingsDock(window)
  window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
  return dock.readings
