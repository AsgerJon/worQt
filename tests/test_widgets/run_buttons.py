"""
RunButtons subclasses 'WidgetTest' and tests the button widgets'
logic - the parts reachable without synthesizing real mouse events:
'PaintButton' state getters and the enable/disable slots, and
'ClickButton' timers, click-sequence registration, the per-button signal
dictionaries and the click/hold emission.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

from worktoy.waitaminute import MissingVariable

from worQt.widgets import PaintButton, ClickButton
from worQt.utils import ButtonStateFlags, MouseButtonNum
from worQt.utils.geom import Point2D

from . import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunButtons(WidgetTest):
  """Tests for 'PaintButton' and 'ClickButton' logic."""

  # \____________________________ PaintButton

  def run_paint_button_defaults(self) -> None:
    """A fresh paint button is un-hovered, un-pressed and enabled."""
    button = PaintButton()
    self.assertFalse(button.hovered)
    self.assertFalse(button.pressed)
    self.assertFalse(button.disabled)
    self.assertIs(button.button, MouseButtonNum.NULL)
    self.assertEqual(button.cursorPosition.x, -1)

  def run_paint_button_state_is_flag(self) -> None:
    """'state' is a 'ButtonStateFlags' for both enabled and disabled."""
    button = PaintButton()
    self.assertIsInstance(button.state, ButtonStateFlags)
    button.disabled = True
    self.assertTrue(button.disabled)
    self.assertIsInstance(button.state, ButtonStateFlags)

  def run_paint_button_enable_disable_slots(self) -> None:
    """The enable/disable slots toggle the disabled state."""
    button = PaintButton()
    button.disable()
    self.assertTrue(button.disabled)
    button.enable()
    self.assertFalse(button.disabled)

  # \____________________________ ClickButton

  def run_click_defaults(self) -> None:
    """A fresh click button has no clicks and is not moving."""
    button = ClickButton()
    self.assertEqual(button.clickSequence, ())
    self.assertFalse(button.hasClicks)
    self.assertFalse(button.moving)

  def run_move_point_missing(self) -> None:
    """Reading 'movePoint' before any move raises 'MissingVariable'."""
    button = ClickButton()
    with self.assertRaises(MissingVariable):
      _ = button.movePoint

  def run_timers(self) -> None:
    """The three timers are lazily built 'QTimer' singletons."""
    button = ClickButton()
    self.assertIsInstance(button.pressTimer, QTimer)
    self.assertIsInstance(button.holdTimer, QTimer)
    self.assertIsInstance(button.sequentialTimer, QTimer)
    button._stopTimers()

  def run_signal_dicts(self) -> None:
    """Each signal dictionary maps the five mouse buttons."""
    button = ClickButton()
    for getter in (button.singleClickDict, button.singleHoldDict,
                   button.doubleClickDict, button.doubleHoldDict):
      self.assertEqual(set(getter), {
        MouseButtonNum.LEFT, MouseButtonNum.RIGHT, MouseButtonNum.MIDDLE,
        MouseButtonNum.FORWARD, MouseButtonNum.BACK,
      })

  def run_register_click(self) -> None:
    """Registering a button records it; clearing empties the sequence."""
    button = ClickButton()
    button._registerClick(MouseButtonNum.LEFT)
    self.assertEqual(button.clickSequence, (MouseButtonNum.LEFT,))
    self.assertTrue(button.hasClicks)
    button._clearClickSequence()
    self.assertEqual(button.clickSequence, ())

  def run_register_null_raises(self) -> None:
    """Registering the null button is refused."""
    button = ClickButton()
    with self.assertRaises(ValueError):
      button._registerClick(MouseButtonNum.NULL)

  def run_register_second_invalidates(self) -> None:
    """A second registration of a DIFFERENT button invalidates the sequence."""
    button = ClickButton()
    button._registerClick(MouseButtonNum.LEFT)
    button._registerClick(MouseButtonNum.RIGHT)
    self.assertEqual(button.clickSequence, ())

  def run_register_same_button_accumulates(self) -> None:
    """Re-registering the SAME button accumulates it, so a double-click can
    reach length two and emit its double-click signal."""
    button = ClickButton()
    button._registerClick(MouseButtonNum.LEFT)
    button._registerClick(MouseButtonNum.LEFT)
    self.assertEqual(
        button.clickSequence,
        (MouseButtonNum.LEFT, MouseButtonNum.LEFT),
    )

  def run_emit_single_click_fires_signal(self) -> None:
    """Emitting a single registered click fires its per-button signal."""
    button = ClickButton()
    fired = []
    button.leftClick.connect(lambda: fired.append(True))
    button._registerClick(MouseButtonNum.LEFT)
    button._emitClicks()
    self.assertEqual(fired, [True])
    self.assertEqual(button.clickSequence, ())

  def run_emit_single_hold_fires_signal(self) -> None:
    """Emitting a single registered hold fires its per-button signal."""
    button = ClickButton()
    fired = []
    button.rightHold.connect(lambda: fired.append(True))
    button._registerClick(MouseButtonNum.RIGHT)
    button._emitHolds()
    self.assertEqual(fired, [True])

  def run_emit_without_clicks_raises(self) -> None:
    """Emitting with no registered clicks is a programming error."""
    button = ClickButton()
    with self.assertRaises(NotImplementedError):
      button._emitClicks()
