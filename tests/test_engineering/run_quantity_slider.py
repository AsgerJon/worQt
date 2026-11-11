"""
RunQuantitySlider covers 'QuantitySlider', a 'Slider' setting a quantity
between a least and a greatest, shown in its unit: its 'quantity' is the
share along its track of the way between them, or on a log scale of the
factor between them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.gui import QuantitySlider

from . import EngineeringWidgetTest


class RunQuantitySlider(EngineeringWidgetTest):
  """Tests for 'QuantitySlider'."""

  def openSlider(self) -> QuantitySlider:
    """A slider of a stiffness from 5 to 50 GPa, shown live."""
    slider = QuantitySlider()
    slider.text = 'Stiffness'
    slider.setScale(5.0, 50.0, 'GPa', 1)
    slider.resize(300, 30)
    self.showLive(slider)
    return slider

  def run_the_scale(self) -> None:
    """Its quantity runs from the least to the greatest as its share goes
    from nought to all, shown in its unit."""
    slider = self.openSlider()
    self.assertEqual((slider.low, slider.high), (5.0, 50.0))
    self.assertEqual(slider.unit, 'GPa')
    slider.value = 0.0
    self.assertAlmostEqual(slider.quantity, 5.0)
    slider.value = 1.0
    self.assertAlmostEqual(slider.quantity, 50.0)
    slider.quantity = 25.0
    self.assertAlmostEqual(slider.value, 20.0 / 45.0)
    self.assertEqual(slider.valueText(), '25.0 GPa')

  def run_kept_within(self) -> None:
    """Its quantity is kept between the least and the greatest."""
    slider = self.openSlider()
    slider.quantity = 80.0
    self.assertAlmostEqual(slider.quantity, 50.0)
    slider.quantity = -3.0
    self.assertAlmostEqual(slider.quantity, 5.0)

  def run_log_scale(self) -> None:
    """On a log scale its quantity runs by equal factors: from 0.01 to 1,
    0.1 halfway; kept within; a linear scale again after 'setScale'."""
    slider = self.openSlider()
    slider.setLogScale(0.01, 1.0, '°', 3)
    self.assertTrue(slider.logScale)
    slider.value = 0.0
    self.assertAlmostEqual(slider.quantity, 0.01)
    slider.value = 0.5
    self.assertAlmostEqual(slider.quantity, 0.1)
    slider.value = 1.0
    self.assertAlmostEqual(slider.quantity, 1.0)
    slider.quantity = 0.1
    self.assertAlmostEqual(slider.value, 0.5)
    self.assertEqual(slider.valueText(), '0.100 °')
    slider.quantity = 5.0
    self.assertAlmostEqual(slider.quantity, 1.0)
    slider.quantity = 0.0
    self.assertAlmostEqual(slider.quantity, 0.01)
    slider.setScale(5.0, 50.0, 'GPa', 1)
    self.assertFalse(slider.logScale)
    slider.value = 0.5
    self.assertAlmostEqual(slider.quantity, 27.5)

  def run_tells_of_changes(self) -> None:
    """It tells of each change of its quantity, in its unit."""
    slider = self.openSlider()
    spy = self.spy(slider.quantityChanged)
    slider.quantity = 30.0
    self.assertEqual(spy.count, 1)
    self.assertAlmostEqual(spy.args[-1][0], 30.0)
    self.assertFalse(slider.grab().isNull())
