"""
RunSlider covers 'Slider', a slider saying what it sets and how much:
its name, a track filled up to the handle, and the share it is at, from
nought to all. A click on the track puts the handle there, a drag takes
it along, the wheel moves it a twentieth at a notch, the arrow keys a
hundredth, Page Up and Page Down a tenth, Home and End to the ends.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from worQt.engineering.gui import Slider

from . import EngineeringWidgetTest


class RunSlider(EngineeringWidgetTest):
  """Tests for 'Slider'."""

  def openSlider(self) -> Slider:
    """A slider named 'Paste', shown live."""
    slider = Slider()
    slider.text = 'Paste'
    slider.resize(260, 32)
    self.showLive(slider)
    return slider

  def along(self, slider: Slider, share: float) -> QPointF:
    """The point 'share' of the way along the track."""
    track = slider.trackRect()
    return QPointF(track.left() + share * track.width(),
                   track.center().y())

  def wheel(self, slider: Slider, notches: int) -> None:
    """Turns the wheel over 'slider' by 'notches', away from the user
    for more."""
    point = slider.trackRect().center()
    event = QWheelEvent(point, slider.mapToGlobal(point), QPoint(0, 0),
                        QPoint(0, 120 * notches), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier,
                        Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(slider, event)

  def run_says_what_it_is(self) -> None:
    """It shows its name and the share it is at, in per cent."""
    slider = self.openSlider()
    self.assertEqual(slider.text, 'Paste')
    self.assertEqual(slider.value, 0.0)
    self.assertEqual(slider.valueText(), '0 %')
    slider.value = 0.6
    self.assertEqual(slider.valueText(), '60 %')
    self.assertFalse(slider.grab().isNull())

  def run_kept_within(self) -> None:
    """It is kept from nought to all."""
    slider = self.openSlider()
    slider.value = 1.5
    self.assertEqual(slider.value, 1.0)
    slider.value = -0.2
    self.assertEqual(slider.value, 0.0)

  def run_tells_of_changes(self) -> None:
    """It tells of each change, once, with the new share, and not of a
    share it already is at."""
    slider = self.openSlider()
    spy = self.spy(slider.valueChanged)
    slider.value = 0.3
    slider.value = 0.3
    self.assertEqual(spy.count, 1)
    self.assertAlmostEqual(spy.args[-1][0], 0.3)

  def run_a_click_puts_it_there(self) -> None:
    """A click on the track puts the handle where it is."""
    slider = self.openSlider()
    self.click(slider, self.along(slider, 1.0))
    self.assertAlmostEqual(slider.value, 1.0, delta=0.01)
    self.click(slider, self.along(slider, 0.5))
    self.assertAlmostEqual(slider.value, 0.5, delta=0.01)
    self.click(slider, self.along(slider, 0.0))
    self.assertAlmostEqual(slider.value, 0.0, delta=0.01)

  def run_a_drag_takes_it_along(self) -> None:
    """A drag takes the handle along, past the ends only to the ends."""
    slider = self.openSlider()
    self.press(slider, self.along(slider, 0.2))
    self.move(slider, self.along(slider, 0.75))
    self.assertAlmostEqual(slider.value, 0.75, delta=0.01)
    self.move(slider, self.along(slider, 1.4))
    self.release(slider, self.along(slider, 1.4))
    self.assertEqual(slider.value, 1.0)
    self.move(slider, self.along(slider, 0.1))
    self.assertEqual(slider.value, 1.0)

  def run_the_wheel(self) -> None:
    """The wheel moves it a twentieth at a notch."""
    slider = self.openSlider()
    slider.value = 0.5
    self.wheel(slider, 1)
    self.assertAlmostEqual(slider.value, 0.55)
    self.wheel(slider, -2)
    self.assertAlmostEqual(slider.value, 0.45)

  def run_the_keys(self) -> None:
    """The arrows move it a hundredth, the page keys a tenth, Home and
    End to the ends."""
    slider = self.openSlider()
    slider.value = 0.5
    self.key(slider, Qt.Key.Key_Right)
    self.assertAlmostEqual(slider.value, 0.51)
    self.key(slider, Qt.Key.Key_Left)
    self.key(slider, Qt.Key.Key_Left)
    self.assertAlmostEqual(slider.value, 0.49)
    self.key(slider, Qt.Key.Key_PageUp)
    self.assertAlmostEqual(slider.value, 0.59)
    self.key(slider, Qt.Key.Key_End)
    self.assertEqual(slider.value, 1.0)
    self.key(slider, Qt.Key.Key_Home)
    self.assertEqual(slider.value, 0.0)
