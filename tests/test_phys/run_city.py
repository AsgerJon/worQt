"""
RunCity covers the walk window in town (user, 2026-11-15: uncannyball's
lap of central Copenhagen): where the lap's file is, the real car at its
start, the walker sat in it, the city driver at its wheel ('Robot hands'
on): it pulls away along the lap, the readings saying so, the lap it
runs and the height data's credit (its maker's terms); the road drawn
along its rows ('crg'), the palace square drawn in its finishes; V the
chase view (user, 2026-11-15: "more camera views like chase where the
mouse can look around, like in GTA V"): the camera behind the car and
over it, level, a look turned away easing back behind as the car goes,
V again the driver's eyes as they were. Its share of real time is
printed; every time here is the car's own.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os
import time

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from worQt.phys import norm, rotated
from worQt.phys._city import CITY_TRACK, squareFirst
from worQt.phys._realcar import CHASSIS
from worQt.phys._crg import ATTRIBUTION
from worQt.phys.gui._walk import CHASE_DISTANCE, CHASE_LIFT, PLACES
from worQt.phys.gui._walk import WalkWindow
from worQt.qtest import WidgetTest


class RunCity(WidgetTest):
  """Tests for the walk window in town (a minute or two)."""

  __time_out__ = 900.0

  def setUp(self, ) -> None:
    """No window open yet."""
    super().setUp()
    self.window = None

  def tearDown(self, ) -> None:
    """Closes the window the test opened, its physics' thread stopped,
    before the base deletes it."""
    if self.window is not None:
      self.window.close()
      self.window = None
    super().tearDown()

  def opened(self, ) -> WalkWindow:
    """Returns the walk window in town, shown, its physics going (a
    second of the car's time); skipped where the lap's file is not."""
    if not os.path.isfile(os.path.normpath(CITY_TRACK)):
      self.skipTest('the city lap is not here')
    window = WalkWindow()
    self.window = window
    names = [place.name for place in PLACES]
    window.placeBox.setCurrentIndex(names.index('Copenhagen'))
    window.reset()
    self.showLive(window)
    self.waitUntil(lambda: window.clock > 1.0 or window.failed is not None,
                   300000)
    self.assertIsNone(window.failed)
    return window

  def keyed(self, window: WalkWindow, key: object) -> None:
    """Presses and lets go 'key' on the window's view."""
    for kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
      QApplication.sendEvent(window.view.quick, QKeyEvent(
        kind, key, Qt.KeyboardModifier.NoModifier))

  def run_chase(self) -> None:
    """V: the camera 6.5 m behind the car, over it, level (not riding
    it); a look turned a radian away eases back behind within three
    seconds of the car going; V again: the driver's eyes, as they
    were."""
    window = self.opened()
    view = window.view
    seat = (view.yaw, view.pitch)
    self.keyed(window, Qt.Key.Key_V)
    self.assertTrue(view.chasing)
    self.waitUntil(lambda: view.distance == CHASE_DISTANCE, 5000)
    self.assertIsNone(view.riding)
    chassis = window.states[CHASSIS]
    ahead = rotated(chassis.turn, (1.0, 0.0, 0.0))
    eye = tuple(t + view.distance * math.cos(view.pitch) * a for t, a in zip(
      view.target, (math.cos(view.yaw), math.sin(view.yaw), 0.0)))
    behind = [e - p for e, p in zip(eye, chassis.place)]
    self.assertLess(behind[0] * ahead[0] + behind[1] * ahead[1], -3.0)
    self.assertAlmostEqual(view.target[2] - chassis.place[2], CHASE_LIFT,
                           delta=0.01)
    until = window.clock + 4.0
    self.waitUntil(lambda: window.clock >= until
                   or window.failed is not None, 600000)
    view.around, view.lookedAt = 1.0, time.perf_counter() - 10.0
    until = window.clock + 3.0
    self.waitUntil(lambda: window.clock >= until
                   or window.failed is not None, 600000)
    self.assertGreater(norm(window.states[CHASSIS].velocity), 2.0)
    self.assertLess(abs(view.around), 0.1)
    self.keyed(window, Qt.Key.Key_V)
    self.assertFalse(view.chasing)
    self.assertEqual((view.yaw, view.pitch), seat)
    self.waitUntil(lambda: view.distance == 0.0
                   and view.riding is not None, 5000)

  def run_drives(self) -> None:
    """The city driver drives at once: in ten seconds of the car's it is
    50 m round or more; the readings say who drives, the lap and the
    credit; the road and the square are drawn; its share of real time
    printed."""
    window = self.opened()
    self.assertTrue(window.robotHands)
    self.assertIsNotNone(window.view.crg)
    self.assertIn(squareFirst(), window.view.finishes)
    until = window.clock + 10.0
    self.waitUntil(lambda: window.clock >= until
                   or window.failed is not None, 600000)
    self.assertIsNone(window.failed)
    self.assertGreater(window.racer.along, 50.0)
    lines = window.status.text().split('\n')
    for start in ('robot driving', 'lap 1 ', ATTRIBUTION[:20]):
      self.assertTrue(any(line.startswith(start) for line in lines),
                      (start, lines))
    print('the real car in town on %s: %.0f %% of real time, %.1f m/s' % (
      window.solver, 100.0 * window.speedNow,
      window.racer.speedOf(window.states)))
