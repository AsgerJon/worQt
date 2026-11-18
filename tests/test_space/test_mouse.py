"""
TestMouse covers the space window's mouse while the pointer is free
(user, 2026-11-18: "the inventory desyncs the mouse from the screen";
"Put in a test for the desync mouse bullshit"): the window's own filter
('SpaceWindow.eventFilter') fed real mouse events, its viewport and
pointer stood in for. Out of his chair the filter kept every button's
release from the scene: a slot of the open inventory was left pressed,
holding the mouse, and the stack carried stuck where it was; and the
scene followed the pointer by hovering, which the slots' own areas took
from it. Now a free pointer's releases are the scene's and the window
says where the pointer is at every move.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from worQt.gaming.space._spacewindow import SpaceWindow

from . import SpaceTest

#  The scene's window, as the filter knows it (stood in for).
QUICK = object()


class TestMouse(SpaceTest):
  """Tests for the space window's mouse while the pointer is free."""

  def _window(self, taken: bool) -> SimpleNamespace:
    """Returns a stand-in for the window as its filter uses it: Asger out
    of his chair (his eyes' view), the pointer 'taken' (looking round)
    or free (the inventory open); what it is told is kept in 'told'."""
    told = []
    pointer = SimpleNamespace(
      taken=taken, take=lambda: told.append('take'),
      forget=lambda: told.append('forget'),
      movedTo=lambda at, local, stamp: told.append(('look', local)))
    viewport = SimpleNamespace(
      quick=QUICK, takesClick=lambda at: not taken,
      pointedAt=lambda at: told.append(('pointed', at)))
    return SimpleNamespace(
      told=told, pointer=pointer, viewport=viewport, mapOpen=False,
      inside=True, held={}, _heldPressed=lambda: False,
      _used=lambda right: told.append(('used', right)),
      _heldReleased=lambda: told.append('released'))

  def _sent(self, window: SimpleNamespace, kind: object, at: tuple,
            button: object = Qt.MouseButton.NoButton) -> bool:
    """Returns what the filter does with a mouse event of 'kind' at 'at'
    (True: the window's, kept from the scene)."""
    place = QPointF(*at)
    held = button if kind == QEvent.Type.MouseButtonPress else (
      Qt.MouseButton.NoButton)
    event = QMouseEvent(kind, place, place, button, held,
                        Qt.KeyboardModifier.NoModifier)
    return SpaceWindow.eventFilter(window, QUICK, event)

  def test_released(self) -> None:
    """Free (the inventory open), a click's press and its release are
    the scene's: the slot pressed is let go; the right button's release
    still ends the Grav-Gun's pull. Taken (looking round), both are the
    window's."""
    free = self._window(False)
    for button in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
      self.assertFalse(self._sent(free, QEvent.Type.MouseButtonPress,
                                  (400.0, 300.0), button))
      self.assertFalse(self._sent(free, QEvent.Type.MouseButtonRelease,
                                  (400.0, 300.0), button))
    self.assertEqual(free.told, ['released'])
    taken = self._window(True)
    self.assertTrue(self._sent(taken, QEvent.Type.MouseButtonPress,
                               (640.0, 360.0), Qt.MouseButton.LeftButton))
    self.assertTrue(self._sent(taken, QEvent.Type.MouseButtonRelease,
                               (640.0, 360.0), Qt.MouseButton.LeftButton))
    self.assertEqual(taken.told, [('used', False)])

  def test_followed(self) -> None:
    """Free, the scene is told where the pointer is at every move, after
    a click as before it and over the slots as anywhere (the stack
    carried drawn there); taken, the moves turn his look only."""
    free = self._window(False)
    places = [(300.0, 300.0), (500.0, 420.0)]
    for at in places[:1]:
      self._sent(free, QEvent.Type.MouseMove, at)
    self._sent(free, QEvent.Type.MouseButtonPress, (500.0, 420.0),
               Qt.MouseButton.LeftButton)
    self._sent(free, QEvent.Type.MouseButtonRelease, (500.0, 420.0),
               Qt.MouseButton.LeftButton)
    for at in places + [(900.0, 200.0)]:
      self._sent(free, QEvent.Type.MouseMove, at)
    pointed = [(told[1].x(), told[1].y()) for told in free.told
               if told[0] == 'pointed']
    self.assertEqual(pointed, places[:1] + places + [(900.0, 200.0)])
    taken = self._window(True)
    self._sent(taken, QEvent.Type.MouseMove, (700.0, 380.0))
    self.assertEqual([told[0] for told in taken.told], ['look'])

  def test_scene(self) -> None:
    """The scene draws the stack carried where the window says the
    pointer is and sets that nowhere itself (no hover area to lose the
    moves to the slots' own)."""
    import worQt.gaming.space as space
    scene = (Path(space.__file__).parent / 'space.qml').read_text(
      encoding='utf-8')
    self.assertIn('x: root.pointerX - 20', scene)
    self.assertIn('y: root.pointerY - 20', scene)
    self.assertNotIn('root.pointerX =', scene)
    self.assertNotIn('root.pointerY =', scene)
