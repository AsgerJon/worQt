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
says where the pointer is at every move. Taken, the cursor is hidden by
the X server before the pointer is put back in the middle (user,
2026-11-18: "when i open the inventory the mouse escapes"): Qt Quick put
a shown cursor back a moment after the inventory shut, Xwayland let the
pointer's lock go, and gamescope let the mouse out of its window. A
click is what takes the mouse back (user, 2026-11-19: "I used to hit
escape and then click which somehow allowed the mouse to snap back"):
shutting the inventory with E or Esc, or the pause menu with Esc, leaves
it free till a click in the window takes it; the menus' buttons act on
the press, taking it then; taken, if it ever leaves the window it is let
go, so a click takes it again ("the mouse escapes with now way back").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from worQt.gaming.sandbox._hiddencursor import HiddenCursor, drawnOnX
from worQt.gaming.sandbox import _pointer as pointerModule
from worQt.gaming.sandbox._pointer import Pointer

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
      letGo=lambda: told.append('let go'),
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

  def test_clicked_back(self) -> None:
    """Free, nothing under the click to take it, a click takes the mouse
    (the click is the window's); taken, the pointer leaving the window
    is let go (a click takes it again). E or Esc shutting the inventory
    and Esc shutting the pause menu leave it free; the inventory's close
    button and the pause menu's resume take it, on the press."""
    from PySide6.QtCore import QEvent as Event
    free = self._window(False)
    free.viewport.takesClick = lambda at: False
    self.assertTrue(self._sent(free, QEvent.Type.MouseButtonPress,
                               (640.0, 360.0), Qt.MouseButton.LeftButton))
    self.assertEqual(free.told, ['take'])
    taken = self._window(True)
    self.assertFalse(SpaceWindow.eventFilter(taken, QUICK, Event(
      QEvent.Type.Leave)))
    self.assertEqual(taken.told, ['let go', 'forget'])
    told = []
    window = SimpleNamespace(
      inventory=SimpleNamespace(closed=lambda: told.append('closed')),
      _inventoryOpen=True, pointer=SimpleNamespace(
        take=lambda: told.append('take')),
      _paused=True, _pauseAsk='', _pauseNote='')
    window._inventoryShut = lambda: SpaceWindow._inventoryShut(window)
    window._resumed = lambda: SpaceWindow._resumed(window)
    SpaceWindow._inventoryShut(window)
    self.assertEqual(told, ['closed'])
    window._inventoryOpen = True
    SpaceWindow._inventoryShutPicked(window)
    self.assertEqual(told, ['closed', 'closed', 'take'])
    SpaceWindow._resumed(window)
    self.assertFalse(window._paused)
    self.assertEqual(told[-1], 'take')
    window._paused = True
    SpaceWindow._pausePicked(window, 'resume')
    self.assertFalse(window._paused)
    self.assertEqual(told, ['closed', 'closed', 'take', 'take'])
    import worQt.gaming.space as space
    scene = (Path(space.__file__).parent / 'space.qml').read_text(
      encoding='utf-8')
    self.assertIn('onPressed: root.pausePicked(pauseButton.what)', scene)
    self.assertIn('onPressed: root.inventoryShutPicked()', scene)

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

  def test_hidden(self) -> None:
    """Taken, the cursor is hidden by the X server before the pointer is
    put back in the middle (the warp then locks it); let go, shown
    again. Off X11 (here: no Qt app) the X server's hide does
    nothing."""
    told = []
    surface = SimpleNamespace(
      setCursor=lambda cursor: told.append('blank'),
      unsetCursor=lambda: told.append('unset'))
    pointer = Pointer(surface)
    pointer.hiding = SimpleNamespace(
      hidden=lambda: told.append('hidden'),
      shown=lambda: told.append('shown'))
    pointer._recentred = lambda: told.append('warped')
    cursor = pointerModule.QCursor
    pointerModule.QCursor = lambda shape: shape  # no app: no real one
    try:
      pointer.take()
    finally:
      pointerModule.QCursor = cursor
    self.assertEqual(told, ['blank', 'hidden', 'warped'])
    pointer.letGo()
    self.assertEqual(told[3:], ['unset', 'shown'])
    hiding = HiddenCursor()
    self.assertEqual(hiding.live, drawnOnX())
    hiding.hidden()
    self.assertEqual(hiding.held, hiding.live)
    hiding.shown()
    self.assertFalse(hiding.held)
