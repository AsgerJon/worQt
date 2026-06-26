"""
RunMouseButton subclasses 'UtilsAppTest' and covers the
'MouseButtonNum' resolvers that need a live application or real events:
'fromApp' (the buttons currently held) and 'fromEvent' (the buttons of a
'QMouseEvent', including the unresolvable-combination error).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from worQt.utils import MouseButtonNum

from . import UtilsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunMouseButton(UtilsAppTest):
  """Tests for the application/event-driven 'MouseButtonNum' resolvers."""

  def run_from_app_no_button(self) -> None:
    """With nothing held, 'fromApp' resolves the null button."""
    self.assertIs(MouseButtonNum.fromApp(), MouseButtonNum.NULL)

  def run_from_event_single(self) -> None:
    """'fromEvent' resolves the single held button."""
    event = QMouseEvent(QEvent.Type.MouseButtonPress,
                        QPointF(0, 0),
                        Qt.MouseButton.LeftButton,
                        Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.NoModifier)
    self.assertIs(MouseButtonNum.fromEvent(event), MouseButtonNum.LEFT)

  def run_from_event_unresolvable(self) -> None:
    """A combination matching no single member raises 'ValueError'."""
    both = Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
    event = QMouseEvent(QEvent.Type.MouseButtonPress,
                        QPointF(0, 0),
                        Qt.MouseButton.LeftButton,
                        both,
                        Qt.KeyboardModifier.NoModifier)
    with self.assertRaises(ValueError):
      MouseButtonNum.fromEvent(event)
