"""
RunSpeedSlider covers 'SpeedSlider', the slider setting how fast the
circuit runs: it opens at real time; its handle snaps to the stops, a
thousandth of real time to ten times it, a click, a notch of the wheel
or an arrow moving it a stop; it tells of each new speed once; a speed
set moves it to the nearest stop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from worQt.engineering.circuits.gui import SPEEDS, SpeedSlider
from worQt.engineering.circuits.gui import nearestStop, speedText
from worQt.engineering.circuits.gui import speedWords

from . import CircuitsWidgetTest


class RunSpeedSlider(CircuitsWidgetTest):
  """Tests for 'SpeedSlider'."""

  def openSlider(self) -> SpeedSlider:
    """A speed slider, shown live."""
    slider = SpeedSlider()
    slider.resize(330, 32)
    self.showLive(slider)
    return slider

  def atStop(self, slider: SpeedSlider, stop: float) -> QPointF:
    """The point of the stop of index 'stop' along the track."""
    track = slider.trackRect()
    share = stop / (len(SPEEDS) - 1)
    return QPointF(track.left() + share * track.width(),
                   track.center().y())

  def wheel(self, slider: SpeedSlider, notches: int) -> None:
    """Turns the wheel over 'slider' by 'notches'."""
    point = slider.trackRect().center()
    event = QWheelEvent(point, slider.mapToGlobal(point), QPoint(0, 0),
                        QPoint(0, 120 * notches), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier,
                        Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(slider, event)

  def run_words(self) -> None:
    """Speeds are said as fractions or as times real time."""
    self.assertEqual(speedText(0.001), '1/1000×')
    self.assertEqual(speedText(1.0), '1×')
    self.assertEqual(speedText(5.0), '5×')
    self.assertEqual(speedWords(1.0), 'real time')
    self.assertEqual(speedWords(0.02), '1/50 of real time')
    self.assertEqual(speedWords(2.0), '2× real time')
    self.assertEqual(nearestStop(0.012), SPEEDS.index(0.01))
    self.assertEqual(nearestStop(1e6), len(SPEEDS) - 1)

  def run_opens_at_real_time(self) -> None:
    """It opens at real time, named 'Speed'."""
    slider = self.openSlider()
    self.assertEqual(slider.text, 'Speed')
    self.assertEqual(slider.speed, 1.0)
    self.assertEqual(slider.valueText(), '1×')
    self.assertFalse(slider.grab().isNull())

  def run_snaps_to_stops(self) -> None:
    """A click between two stops puts the handle on the nearer."""
    slider = self.openSlider()
    self.click(slider, self.atStop(slider, 2.2))
    self.assertEqual(slider.stop, 2)
    self.assertAlmostEqual(slider.value, 2 / (len(SPEEDS) - 1), 12)
    self.assertEqual(slider.speed, 0.005)
    self.click(slider, self.atStop(slider, 11.7))
    self.assertEqual(slider.speed, 10.0)

  def run_a_stop_a_step(self) -> None:
    """An arrow or a notch of the wheel moves it a stop; Home and End
    to the ends."""
    slider = self.openSlider()
    self.key(slider, Qt.Key.Key_Right)
    self.assertEqual(slider.speed, 2.0)
    self.key(slider, Qt.Key.Key_Left)
    self.key(slider, Qt.Key.Key_Left)
    self.assertEqual(slider.speed, 0.5)
    self.wheel(slider, 2)
    self.assertEqual(slider.speed, 2.0)
    self.key(slider, Qt.Key.Key_Home)
    self.assertEqual(slider.speed, 0.001)
    self.key(slider, Qt.Key.Key_End)
    self.assertEqual(slider.speed, 10.0)

  def run_tells_once(self) -> None:
    """Each new speed is told once, none for the same speed."""
    slider = self.openSlider()
    spy = self.spy(slider.speedChanged)
    slider.speed = 0.1
    slider.speed = 0.1
    slider.speed = 0.11
    self.assertEqual(spy.count, 1)
    self.assertEqual(spy.args[-1][0], 0.1)
    slider.speed = 5.0
    self.assertEqual(spy.count, 2)
    self.assertEqual(spy.args[-1][0], 5.0)
