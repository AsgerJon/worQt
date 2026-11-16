"""
TestHandPicture covers the hand and the cue laid behind ball 1 in the
view from above: the two pictures are one size, to lie one over the
other, the cue's chalked tip at the right edge on the middle line, where
the hand leaves the picture clear, the cue's back end faded out; and the
cue's stroke, 'cueBackAt': still at the address, drawn back smoothly to
the backswing, held, sent on ever faster to meet the ball at the wait,
then on through to its share of the backswing past the ball, and held.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.billiards.gui import FOLLOW_SECONDS, FOLLOW_SHARE
from worQt.gaming.billiards.gui import cueBackAt, cuePicture, handPicture

from . import BilliardsWidgetTest


class TestHandPicture(BilliardsWidgetTest):
  """Tests for 'handPicture', 'cuePicture' and 'cueBackAt'."""

  def test_pictures(self) -> None:
    """The hand and the cue are pictures of one size; the cue's chalked
    tip is at the right edge on the middle line, where the hand's
    picture is clear; the cue's back end is faded out."""
    hand, cue = handPicture(), cuePicture()
    self.assertEqual(hand.size(), cue.size())
    middle = cue.height() // 2
    tip = cue.pixelColor(cue.width() - 3, middle)
    self.assertGreater(tip.alpha(), 200)
    self.assertGreater(tip.blue(), tip.red())
    self.assertEqual(hand.pixelColor(cue.width() - 3, middle).alpha(), 0)
    self.assertLess(cue.pixelColor(0, middle).alpha(), 5)

  def test_stroke(self) -> None:
    """Still at the address; drawn back smoothly, never past the
    backswing; held; sent on, ever faster, meeting the ball at the wait;
    then on through, slowing, to its share of the backswing past the
    ball, and held there."""
    wait, most = 1.0, 100.0
    self.assertEqual(cueBackAt(0.0, wait, most), 0.0)
    self.assertEqual(cueBackAt(0.1, wait, most), 0.0)
    drawn = [cueBackAt(0.12 + 0.01 * k, wait, most) for k in range(51)]
    self.assertTrue(all(b >= a for a, b in zip(drawn, drawn[1:])))
    self.assertTrue(all(0.0 <= back <= most for back in drawn))
    self.assertAlmostEqual(cueBackAt(0.62, wait, most), most, 9)
    self.assertEqual(cueBackAt(0.7, wait, most), most)
    sent = [cueBackAt(0.76 + 0.02 * k, wait, most) for k in range(13)]
    steps = [a - b for a, b in zip(sent, sent[1:])]
    self.assertTrue(all(b > a > 0.0 for a, b in zip(steps, steps[1:])))
    #  A nanosecond before it meets the ball it is still its speed, 833
    #  mm/s, times that back: 8e-7 mm, which six places do not hide.
    self.assertAlmostEqual(cueBackAt(wait - 1e-9, wait, most), 0.0, 5)
    self.assertEqual(cueBackAt(wait, wait, most), 0.0)
    through = [cueBackAt(wait + 0.01 * k, wait, most) for k in range(16)]
    self.assertTrue(all(b < a for a, b in zip(through, through[1:])))
    past = cueBackAt(wait + FOLLOW_SECONDS, wait, most)
    self.assertAlmostEqual(past, -FOLLOW_SHARE * most, 9)
    self.assertEqual(cueBackAt(wait + 5.0, wait, most), past)
