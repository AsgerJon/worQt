"""
TestCrackColors covers the colours cracks are drawn in: by how far a face
has given, opened or slid, on a scale running evenly in the logarithm
from a micrometre to a millimetre, blue through green and yellow to red,
as heat maps are; and the ticks the scale is read by.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.gui import crackColor, crackShare, crackTicks
from worQt.engineering.gui import crackLevel, levelColor, CRACK_LEVELS

from . import EngineeringTest


class TestCrackColors(EngineeringTest):
  """Tests for the crack colours."""

  def test_the_share(self) -> None:
    """A micrometre is the scale's bottom, a millimetre its top, their
    geometric mean its middle; beyond either end it is kept at the
    end."""
    self.assertAlmostEqual(crackShare(0.001), 0.0)
    self.assertAlmostEqual(crackShare(1.0), 1.0)
    self.assertAlmostEqual(crackShare(math.sqrt(0.001)), 0.5)
    self.assertEqual(crackShare(1e-6), 0.0)
    self.assertEqual(crackShare(5.0), 1.0)
    self.assertEqual(crackShare(0.0), 0.0)

  def test_the_colours(self) -> None:
    """Narrow cracks are blue, middling green, wide red."""
    narrow, middle = crackColor(0.001), crackColor(math.sqrt(0.001))
    wide = crackColor(1.0)
    self.assertGreater(narrow.blueF(), narrow.redF())
    self.assertGreater(middle.greenF(), middle.blueF())
    self.assertGreater(middle.greenF(), middle.redF())
    self.assertGreater(wide.redF(), wide.blueF())
    self.assertGreater(wide.redF(), wide.greenF())

  def test_the_ticks(self) -> None:
    """The scale is read at each tenfold, from a micrometre to a
    millimetre."""
    ticks = crackTicks()
    self.assertEqual([label for _, label in ticks],
                     ['1 µm', '10 µm', '100 µm', '1 mm'])
    shares = [share for share, _ in ticks]
    for share, wanted in zip(shares, (0.0, 1 / 3, 2 / 3, 1.0)):
      self.assertAlmostEqual(share, wanted)

  def test_the_narrow_are_faint(self) -> None:
    """Cracks are drawn a colour at a time, the narrower the fainter, so
    the wide stand out of the many narrow."""
    self.assertEqual(crackLevel(0.001), 0)
    self.assertEqual(crackLevel(1.0), CRACK_LEVELS - 1)
    faint, solid = levelColor(0), levelColor(CRACK_LEVELS - 1)
    self.assertLess(faint.alphaF(), 0.5)
    self.assertEqual(solid.alphaF(), 1.0)
