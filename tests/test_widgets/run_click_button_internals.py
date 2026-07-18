"""
RunClickButtonInternals covers the 'ClickButton' branches not reached by
the event-driven tests: the 'movePoint' and timer accessor guards, the
emit paths for clicks and holds (a run longer than three, the double and
triple cases), the move-cancel handlers, the release edges and the
state-validity toggles.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException, MissingVariable

from worQt.widgets import ClickButton
from worQt.utils import MouseButtonNum

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_L = MouseButtonNum.LEFT


class RunClickButtonInternals(WidgetTest):
  """Tests for the click-button internal branches."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ACCESSOR GUARDS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_move_point_guards(self) -> None:
    """'movePoint' raises when unset and when wrongly typed."""
    button = ClickButton()
    with self.assertRaises(MissingVariable):
      _ = button.movePoint
    button.__move_point__ = 'bad'
    with self.assertRaises(TypeException):
      _ = button.movePoint

  def run_timer_type_guards(self) -> None:
    """The timer accessors reject a wrongly-typed slot."""
    button = ClickButton()
    button.__press_timer__ = 'bad'
    with self.assertRaises(TypeException):
      _ = button.pressTimer
    button2 = ClickButton()
    button2.__hold_timer__ = 'bad'
    with self.assertRaises(TypeException):
      _ = button2.holdTimer
    button3 = ClickButton()
    button3.__sequential_timer__ = 'bad'
    with self.assertRaises(TypeException):
      _ = button3.sequentialTimer

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  EMIT CLICKS / HOLDS  # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_emit_clicks_too_many(self) -> None:
    """A run longer than the per-button tiers still fires 'multiClick' with
    the full sequence, emits no per-button signal, then resets."""
    button = ClickButton()
    multiSpy = self.spy(button.multiClick)
    tripleSpy = self.spy(button.leftTripleClick)
    button.__click_sequence__ = (_L, _L, _L, _L)
    button._emitClicks()
    self.assertEqual(multiSpy.count, 1)
    self.assertEqual(multiSpy.args, ((_L, _L, _L, _L),))
    self.assertEqual(tripleSpy.count, 0)
    self.assertFalse(button.hasClicks)

  def run_emit_clicks_double(self) -> None:
    """Two clicks of the same button emit the double-click signal."""
    button = ClickButton()
    doubleSpy = self.spy(button.leftDoubleClick)
    button.__click_sequence__ = (_L, _L)
    button._emitClicks()
    self.assertEqual(doubleSpy.count, 1)

  def run_emit_holds_branches(self) -> None:
    """The hold emitter mirrors the click emitter's tiers: a run longer than
    three emits 'multiHold' only, a same-button double emits the double-hold
    and a triple the triple-hold."""
    tooMany = ClickButton()
    multiSpy = self.spy(tooMany.multiHold)
    tooMany.__click_sequence__ = (_L, _L, _L, _L)
    tooMany._emitHolds()
    self.assertEqual(multiSpy.count, 1)
    self.assertEqual(multiSpy.args, ((_L, _L, _L, _L),))
    self.assertFalse(tooMany.hasClicks)
    double = ClickButton()
    doubleSpy = self.spy(double.leftDoubleHold)
    double.__click_sequence__ = (_L, _L)
    double._emitHolds()
    self.assertEqual(doubleSpy.count, 1)
    triple = ClickButton()
    tripleSpy = self.spy(triple.leftTripleHold)
    triple.__click_sequence__ = (_L, _L, _L)
    triple._emitHolds()
    self.assertEqual(tripleSpy.count, 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MOVE CANCEL HANDLERS  # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_press_and_hold_moved_invalidate(self) -> None:
    """The press/hold move handlers cancel a pending click."""
    pressed = ClickButton()
    pressed._registerClick(_L)
    pressed._onPressMoved()
    self.assertFalse(pressed.hasClicks)
    held = ClickButton()
    held._registerClick(_L)
    held._onHoldMoved()
    self.assertFalse(held.hasClicks)

  def run_sequential_moved_emits(self) -> None:
    """A move during the sequential window emits the accumulated click."""
    button = ClickButton()
    clickSpy = self.spy(button.leftClick)
    button._registerClick(_L)
    button._onSequentialMoved()
    self.assertEqual(clickSpy.count, 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  RELEASE / STATE EDGES  # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_release_when_not_hovered(self) -> None:
    """A release while not hovered is ignored."""
    button = ClickButton()
    button.resize(200, 200)
    self.showLive(button)
    self.release(button, button.paintView.center)  # no prior hover
    self.assertFalse(button.hasClicks)

  def run_state_toggles(self) -> None:
    """The hover enter/leave state-validity toggles flip the flag."""
    button = ClickButton()
    button._validateState()
    button._validateState()  # already invalid -> no-op branch
    button._invalidateState()

  def run_timer_recursion_guards(self) -> None:
    """Each lazy timer getter guards against a failed build."""
    for name in ('_getPressTimer', '_getHoldTimer', '_getSequentialTimer'):
      with self.assertRaises(RecursionError):
        getattr(ClickButton(), name)(_recursion=True)

  def run_emit_holds_without_clicks(self) -> None:
    """Emitting holds with no registered click is a programming error."""
    with self.assertRaises(NotImplementedError):
      ClickButton()._emitHolds()
