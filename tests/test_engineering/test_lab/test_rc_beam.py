"""
TestRCBeam covers 'RCBeam', 'BarLayer' and 'Stirrups': a beam of
reinforced concrete as cast for a test, its concrete following from its
strength by EN 1992-1-1's table 3.1, its bars fitting side by side and
the two layers apart, its stirrups every spacing but in its gaps.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.lab import BarLayer, RCBeam, Stirrups

from . import LabTest, standardBeam


class TestRCBeam(LabTest):
  """Tests for 'RCBeam' and 'BarLayer'."""

  def test_bar_layer(self) -> None:
    """A layer's area is its bars' together; its depth, to their
    centres."""
    layer = BarLayer(3, 16.0, 30.0)
    self.assertAlmostEqual(layer.area, 3 * math.pi * 64)
    self.assertAlmostEqual(layer.depth, 38.0)
    self.assertEqual(str(layer), '3 Ø16, cover 30')
    self.assertEqual(str(BarLayer(0, 16.0, 30.0)), 'none')

  def test_standard(self) -> None:
    """The standard beam is 3300 x 300 x 200, C30, 3 Ø16 and 2 Ø10,
    with Ø8 stirrups every 150 mm."""
    beam = standardBeam()
    self.assertEqual((beam.length, beam.height, beam.width),
                     (3300.0, 300.0, 200.0))
    self.assertEqual((beam.fcm, beam.fy, beam.Es), (38.0, 550.0, 2e5))
    self.assertEqual(beam.bottom, BarLayer(3, 16.0, 30.0))
    self.assertEqual(beam.top, BarLayer(2, 10.0, 30.0))
    self.assertEqual(beam.stirrups, Stirrups(8.0, 150.0, ()))
    self.assertEqual(RCBeam(*beam.values()).values(), beam.values())

  def test_concrete(self) -> None:
    """The concrete follows from fcm by EN 1992-1-1: C30's Ecm 32.8 GPa,
    fctm 2.90 MPa, epsC1 2.16 and epsCu1 3.5 per mille."""
    beam = standardBeam()
    self.assertAlmostEqual(beam.fck, 30.0)
    self.assertAlmostEqual(beam.Ecm, 32837, -1)
    self.assertAlmostEqual(beam.fctm, 2.896, 3)
    self.assertAlmostEqual(beam.epsC1, 0.00216, 5)
    self.assertAlmostEqual(beam.epsCu1, 0.0035)
    strong = RCBeam(3300.0, 300.0, 200.0, 98.0, 550.0, 2e5,
                    beam.bottom, beam.top)
    self.assertAlmostEqual(strong.epsC1, 0.0028)
    self.assertAlmostEqual(strong.epsCu1, 0.0028)
    self.assertAlmostEqual(strong.fctm, 2.12 * math.log(10.8))

  def test_stirrups(self) -> None:
    """Stirrups stand every spacing along the beam, the first half a
    spacing in, but in its gaps; two legs each; none of diameter
    nought."""
    stirrups = Stirrups(8.0, 150.0, ())
    self.assertAlmostEqual(stirrups.area, 2 * math.pi * 16)
    places = stirrups.places(3300.0)
    self.assertEqual(places[:3], (75.0, 225.0, 375.0))
    self.assertEqual(len(places), 22)
    gapped = stirrups.withGap(200.0, 1000.0)
    self.assertEqual(gapped.places(3300.0)[:2], (75.0, 1125.0))
    self.assertEqual(gapped.withGapAt(0, 100.0, 300.0).gaps,
                     ((100.0, 300.0),))
    self.assertEqual(gapped.withoutGap(0).gaps, ())
    self.assertEqual(Stirrups(0.0, 150.0, ()).places(3300.0), ())
    self.assertEqual(str(gapped), 'Ø8 c/c 150, 1 gap')
    self.assertEqual(str(Stirrups(0.0, 150.0, ())), 'none')

  def test_beam_stirrups(self) -> None:
    """A beam has Ø8 stirrups every 150 mm unless given others; a beam
    refuses a spacing under 50 mm and a gap off it."""
    beam = standardBeam()
    self.assertEqual(beam.stirrups, Stirrups(8.0, 150.0, ()))
    self.assertEqual(len(beam.values()), 9)
    bare = beam.withStirrups(Stirrups(0.0, 150.0, ()))
    self.assertEqual(bare.stirrups.places(bare.length), ())
    for wrong in (Stirrups(8.0, 40.0, ()), Stirrups(-1.0, 150.0, ()),
                  Stirrups(8.0, 150.0, ((500.0, 400.0),)),
                  Stirrups(8.0, 150.0, ((3000.0, 3400.0),))):
      with self.assertRaises(ValueError):
        beam.withStirrups(wrong)

  def test_bars_fit(self) -> None:
    """Bars fit side by side with their gaps and covers, the layers
    apart; a layer may have none."""
    beam = standardBeam()
    values = [*beam.values()]
    for bottom in (BarLayer(9, 16.0, 30.0), BarLayer(3, 16.0, 0.0),
                   BarLayer(2.5, 16.0, 30.0)):
      values[6] = bottom
      with self.assertRaises(ValueError):
        RCBeam(*values)
    values[6] = BarLayer(0, 16.0, 30.0)
    self.assertEqual(RCBeam(*values).bottom.area, 0.0)
    values[1] = 100.0
    values[0] = 1000.0
    values[6] = BarLayer(2, 25.0, 30.0)
    values[7] = BarLayer(2, 25.0, 30.0)
    with self.assertRaises(ValueError):
      RCBeam(*values)

  def test_shape(self) -> None:
    """A beam has its sizes, is 4 times as long as high, and its
    concrete is stronger than 8 MPa."""
    beam = standardBeam()
    for index, value in ((0, 1000.0), (1, -300.0), (3, 8.0)):
      values = [*beam.values()]
      values[index] = value
      with self.assertRaises(ValueError):
        RCBeam(*values)
