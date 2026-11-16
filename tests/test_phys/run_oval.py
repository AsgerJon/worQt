"""
RunOval covers the walk window at the oval (user, 2026-11-15: "park the
old car by inside the grass on the Dover track, put this car there
instead, have an AI driver take the wheel"): the real car on the start
line, the walker sat in it, the racing driver at its wheel ('Robot
hands' on: it pulls away and races, the readings saying what it does and
the lap it runs); the oval drawn (its terrain and its track), the old
car parked in the infield drawn in its finishes and its dress; 'Robot
hands' off, the player drives. The window steps the car on the GPU
where there is one: its share of real time is printed; every time here
is the car's own.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys._realcar import CHASSIS
from worQt.phys._realdriver import FORWARD
from worQt.phys._realoval import parkedFirst
from worQt.phys.gui._walk import PLACES, WalkWindow
from worQt.phys.gui._walkdress import ParkedDress
from worQt.qtest import WidgetTest


class RunOval(WidgetTest):
  """Tests for the walk window at the oval (a minute or two: the cars
  built, the kernels loaded, seconds raced)."""

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
    """Returns the walk window at the oval, shown, its physics going (a
    second of the car's time stepped)."""
    window = WalkWindow()
    self.window = window
    names = [place.name for place in PLACES]
    window.placeBox.setCurrentIndex(names.index('The oval'))
    window.reset()
    self.showLive(window)
    self.waitUntil(lambda: window.clock > 1.0 or window.failed is not None,
                   300000)
    self.assertIsNone(window.failed)
    self.assertGreater(window.clock, 1.0)
    return window

  def run_races(self) -> None:
    """The racing driver drives at once: in ten seconds of the car's it
    is 60 m round or more, in second gear or higher, the readings saying
    so and the lap it runs; the oval and the old car are drawn; its share
    of real time printed."""
    window = self.opened()
    self.assertTrue(window.robotHands)
    self.assertIsNotNone(window.racer)
    self.assertIsNotNone(window.view.terrain)
    self.assertTrue(window.view.oval)
    self.assertTrue(any(isinstance(dress, ParkedDress)
                        for dress in window.view.extras))
    self.assertIn(parkedFirst(window.assembly), window.view.finishes)
    until = window.clock + 10.0
    self.waitUntil(lambda: window.clock >= until
                   or window.failed is not None, 600000)
    self.assertIsNone(window.failed)
    self.assertGreater(window.racer.along, 60.0)
    self.assertGreaterEqual(FORWARD.index(window.racer.gear), 1)
    lines = window.status.text().split('\n')
    for start in ('robot driving', 'lap 1 '):
      self.assertTrue(any(line.startswith(start) for line in lines),
                      (start, lines))
    print('the real car racing the oval on %s: %.0f %% of real time, %.1f '
          'm/s' % (window.solver, 100.0 * window.speedNow,
                   window.racer.speedOf(window.states)))

  def run_hands_off(self) -> None:
    """'Robot hands' off, the readings say the player drives; on again,
    the driver drives."""
    window = self.opened()
    window.handsButton.setChecked(False)
    self.assertFalse(window.robotHands)
    self.waitUntil(lambda: any(line.startswith('you drive') for line in
                               window.status.text().split('\n')), 5000)
    window.handsButton.setChecked(True)
    self.assertTrue(window.robotHands)
    self.waitUntil(lambda: any(line.startswith('robot driving') for line in
                               window.status.text().split('\n')), 5000)
    self.assertGreater(window.states[CHASSIS].place[2], 0.5)
