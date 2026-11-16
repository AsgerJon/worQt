"""
TestPeepKinds covers the FourthPeep's kinds (user, 2026-11-16: "*Every*
fourtpeep input ... must visibly deform when activated"): a key sinks in
and springs back, or stays in latched; a knob clicks through its notches
and stops at its ends, or turns on and on; a slide control slides to
where it is sent and no further.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.sandbox import Knob, Pushbutton, Slider
from worQt.gaming.sandbox._knob import CLICK
from worQt.gaming.sandbox._pushbutton import PRESS
from worQt.gaming.sandbox._slider import SLIDE

from . import SandboxTest


class TestPeepKinds(SandboxTest):
  """Tests for 'Pushbutton', 'Knob' and 'Slider'."""

  def test_key(self) -> None:
    """Pressed, a key sinks its depth in over 'PRESS' s and springs back
    out the same; latched it stays in till let go."""
    key = Pushbutton('hold', None, (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), 0.006)
    key.used()
    key.acted([], 0.5 * PRESS)
    self.assertAlmostEqual(key.sunk(), 0.003, 12)
    key.acted([], 0.5 * PRESS)
    self.assertEqual(key.value, 1.0)
    self.assertEqual(key.target, 0.0)
    key.acted([], PRESS)
    self.assertEqual(key.value, 0.0)
    key.held(True)
    for _ in range(10):
      key.acted([], PRESS)
    self.assertEqual(key.value, 1.0)
    key.held(False)
    key.acted([], PRESS)
    self.assertEqual(key.value, 0.0)
    self.assertEqual(key.prompt(), 'Press hold')

  def test_knob(self) -> None:
    """A knob of eight notches clicks on and back, a notch each 'CLICK'
    s, stops at its ends, and from its last goes back to its first;
    with no ends it turns on and on."""
    knob = Knob('warp', None, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.02, -1.0,
                0.3, 8)
    self.assertEqual(knob.turned(3), 3)
    knob.acted([], 1.5 * CLICK)
    self.assertAlmostEqual(knob.value, 1.5, 12)
    self.assertAlmostEqual(knob.angle(), -1.0 + 0.45, 12)
    self.assertEqual(knob.turned(10), 4)
    self.assertEqual(knob.notch, 7)
    knob.used()
    self.assertEqual(knob.notch, 0)
    self.assertEqual(knob.turned(-2), 0)
    endless = Knob('orbit', None, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.02,
                   0.0, math.pi / 6.0, None)
    self.assertEqual(endless.turned(-30), 30)
    self.assertEqual(endless.notch, -30)

  def test_slider(self) -> None:
    """A slide control slides to where it is sent, end to end over
    'SLIDE' s, kept within its ends."""
    slider = Slider('throttle', None, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                    0.25)
    slider.slid(0.6)
    slider.acted([], 0.3 * SLIDE)
    self.assertAlmostEqual(slider.value, 0.3, 12)
    slider.acted([], SLIDE)
    self.assertAlmostEqual(slider.along(), 0.15, 12)
    slider.slid(4.0)
    self.assertEqual(slider.target, 1.0)
    slider.used()
    self.assertEqual(slider.target, 0.0)
