"""
RunWalkKeys covers how the walk window drives the real car from the
keys (user, 2026-11-14: "key_A: make steering wheel more left, key_d:
right. Then, if neither key_A nor key_D is down, steering should
neutralize. Key_Space: handbrake (instantly locks wheels). Key_S:
disc-brakes with ABS. Key_W: increase thrust intake. Keypad_0: clutch,
Keypad_4: reverse, Keypad_5: gear 2, Keypad_6: 4, Keypad_1: gear 1,
Keypad_2: gear 3, Keypad_3: gear 5"), each key sent to the view as the
system sends it (the keypad's with its modifier): the keypad's keys
are told from the row's, Num Lock on or off; sat in the car, the
keypad's 0 holds the clutch down and its 1 puts the stick in first, W
opens the throttle and the car drives off; A turns the wheel left, D
right, and let go it comes back straight; S presses the brakes, every
caliper at the foot's pressure standing; Space pulls the handbrake, the
rear calipers at its pressure, the front ones free; F gets the driver
out; the readings (its dock window's) show the engine, the gear, the
clutch, the wheels and the keys each on a line of its own. The window
steps the car on the GPU where there is one: its share of real time is
printed; every time here is the car's own (a slow machine waits
longer, as the window does).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from worQt.phys._realcar import CHASSIS, FOOT, HANDBRAKE
from worQt.phys.gui._walk import PLACES, WalkWindow, padKey
from worQt.qtest import WidgetTest

PAD = Qt.KeyboardModifier.KeypadModifier
ROW = Qt.KeyboardModifier.NoModifier


class RunWalkKeys(WidgetTest):
  """Tests for the walk window's keys in the real car (a minute or two:
  the car built, its kernels loaded, a few seconds driven)."""

  __time_out__ = 900.0

  def setUp(self, ) -> None:
    """No window open yet."""
    super().setUp()
    self.window = None

  def tearDown(self, ) -> None:
    """Closes the window the test opened, its physics' thread stopped
    ('closeEvent'), before the base deletes it (deleted unclosed, its
    thread stepped on beside the next test's window, both working the
    real car's controls: the wheel held left by one, brought back
    straight by the other)."""
    if self.window is not None:
      self.window.close()
      self.window = None
    super().tearDown()

  def opened(self, ) -> WalkWindow:
    """Returns the walk window at the real car, shown, its physics going
    (a second of the car's time stepped); closed at the test's end."""
    window = WalkWindow()
    self.window = window
    names = [place.name for place in PLACES]
    window.placeBox.setCurrentIndex(names.index('The real car'))
    window.reset()
    self.showLive(window)
    self.waitUntil(lambda: window.clock > 1.0 or window.failed is not None,
                   300000)
    self.assertIsNone(window.failed)
    self.assertGreater(window.clock, 1.0)
    return window

  def ranFor(self, window: WalkWindow, seconds: float,
             done: object = None) -> bool:
    """Waits until the car has run 'seconds' more of its own time, or
    'done' (a function of nothing) holds first; returns whether 'done'
    held (no 'done': True)."""
    until = window.clock + seconds
    self.waitUntil(lambda: window.clock >= until or (
      done is not None and done()), 600000)
    return True if done is None else done()

  def keyed(self, window: WalkWindow, key: object, held: bool,
            modifiers: object = ROW) -> None:
    """Sends 'key' pressed ('held') or let go to the window's view, with
    'modifiers', as the system does."""
    kind = QEvent.Type.KeyPress if held else QEvent.Type.KeyRelease
    QApplication.sendEvent(window.view.quick, QKeyEvent(kind, key,
                                                        modifiers))

  def run_pad_keys(self) -> None:
    """The keypad's digits are 'pad0' to 'pad9', with Num Lock on (its
    digits) or off (what it sends then: Insert, End, Down, ...); the
    row's digits and letters stay Qt's keys."""
    kind, Key = QEvent.Type.KeyPress, Qt.Key
    for digit, off in enumerate((Key.Key_Insert, Key.Key_End,
                                 Key.Key_Down, Key.Key_PageDown,
                                 Key.Key_Left, Key.Key_Clear,
                                 Key.Key_Right)):
      on = getattr(Key, 'Key_%d' % digit)
      self.assertEqual(padKey(QKeyEvent(kind, on, PAD)), 'pad%d' % digit)
      self.assertEqual(padKey(QKeyEvent(kind, off, PAD)), 'pad%d' % digit)
      self.assertEqual(padKey(QKeyEvent(kind, on, ROW)), on)
    self.assertEqual(padKey(QKeyEvent(kind, Key.Key_W, ROW)), Key.Key_W)

  def run_drives(self) -> None:
    """The keypad's 0 held (the clutch down), its 1 puts the stick in
    first; W held and the clutch let up, the car drives off forward
    (past 2 m/s within four seconds); its share of real time printed."""
    window = self.opened()
    drive = window.place.drivetrain
    self.keyed(window, Qt.Key.Key_0, True, PAD)
    self.ranFor(window, 1.0)
    self.assertGreater(drive.pedal, 0.5)
    self.keyed(window, Qt.Key.Key_1, True, PAD)
    self.assertTrue(self.ranFor(window, 5.0,
                                lambda: drive.shifter.engaged == '1'))
    self.keyed(window, Qt.Key.Key_1, False, PAD)
    self.keyed(window, Qt.Key.Key_W, True)
    self.ranFor(window, 0.4)
    self.keyed(window, Qt.Key.Key_0, False, PAD)
    self.assertTrue(self.ranFor(
      window, 4.0, lambda: window.states[CHASSIS].velocity[0] > 2.0))
    self.keyed(window, Qt.Key.Key_W, False)
    lines = window.status.text().split('\n')
    for start in ('engine ', 'gear 1 ', 'clutch ', 'wheels ', '(W throttle'):
      self.assertTrue(any(line.startswith(start) for line in lines),
                      (start, lines))
    print('the real car on %s: %.0f %% of real time' % (
      window.solver, 100.0 * window.speedNow))

  def run_steers(self) -> None:
    """A held turns the steering wheel left, D right; let go, it comes
    back straight."""
    window = self.opened()
    wall = window.place.steer
    self.keyed(window, Qt.Key.Key_A, True)
    self.assertTrue(self.ranFor(window, 3.0, lambda: wall.value > 1.0))
    self.keyed(window, Qt.Key.Key_A, False)
    self.assertTrue(self.ranFor(window, 3.0, lambda: wall.value == 0.0))
    self.keyed(window, Qt.Key.Key_D, True)
    self.assertTrue(self.ranFor(window, 3.0, lambda: wall.value < -1.0))
    self.keyed(window, Qt.Key.Key_D, False)
    self.assertTrue(self.ranFor(window, 3.0, lambda: wall.value == 0.0))

  def run_brakes(self) -> None:
    """Standing, S presses every caliper at the foot's pressure; let go,
    none; Space pulls the handbrake, the rear calipers at its pressure,
    the front ones free; F gets the driver out."""
    window = self.opened()
    lines = window.place.ride.brakes.lines
    self.keyed(window, Qt.Key.Key_S, True)
    self.assertTrue(self.ranFor(window, 1.0, lambda: all(
      line.pressure == FOOT for line in lines)))
    self.keyed(window, Qt.Key.Key_S, False)
    self.assertTrue(self.ranFor(window, 1.0, lambda: all(
      line.pressure == 0.0 for line in lines)))
    self.keyed(window, Qt.Key.Key_Space, True)
    self.assertTrue(self.ranFor(window, 1.0, lambda: all(
      line.pressure == HANDBRAKE for line in lines[2:])))
    self.assertEqual([line.pressure for line in lines[:2]], [0.0, 0.0])
    self.keyed(window, Qt.Key.Key_Space, False)
    self.assertTrue(window.seated)
    self.keyed(window, Qt.Key.Key_F, True)
    self.assertTrue(self.ranFor(window, 1.0, lambda: not window.seated))
    self.keyed(window, Qt.Key.Key_F, False)
