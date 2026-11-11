"""
TestRebar covers 'Rebar', a group of straight reinforcing bars in a
disk: its line in the disk's text, its area, how it must lie inside the
disk, and how a resized disk carries it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering import Disk, Rebar

from . import EngineeringTest, DEEP_BEAM

_TIE = 'rebar 0.05 0.06 5.95 0.06 4 20'


class TestRebar(EngineeringTest):
  """Tests for 'Rebar'."""

  def test_reads_and_writes_its_line(self) -> None:
    """A rebar line gives where the bars run, from and to, how many
    there are and their diameter in mm."""
    rebar = Rebar(_TIE)
    self.assertEqual(rebar.start, (0.05, 0.06))
    self.assertEqual(rebar.end, (5.95, 0.06))
    self.assertEqual(rebar.count, 4)
    self.assertEqual(rebar.diameter, 20.0)
    self.assertEqual(str(rebar), _TIE)
    self.assertEqual(str(Rebar(0.05, 0.06, 5.95, 0.06, 4, 20)), _TIE)
    self.assertEqual(str(Rebar(rebar)), _TIE)

  def test_area_and_name(self) -> None:
    """The area is that of all the bars, in mm², and the bars are named
    the way a drawing names them."""
    rebar = Rebar(_TIE)
    self.assertAlmostEqual(rebar.area, 4 * math.pi * 20 ** 2 / 4)
    self.assertEqual(rebar.name, '4 Ø20')
    self.assertTrue(rebar.horizontal)
    self.assertFalse(Rebar('rebar 0.1 0.1 0.1 2 2 12').horizontal)

  def test_bars_are_bars(self) -> None:
    """There is at least one bar, of a diameter above zero, running
    somewhere."""
    for line in ('rebar 0.05 0.06 5.95 0.06 0 20',
                 'rebar 0.05 0.06 5.95 0.06 4 0',
                 'rebar 0.05 0.06 0.05 0.06 4 20',
                 'rebar 0.05 0.06 5.95 0.06 2.5 20',
                 'rebar 0.05 0.06 5.95 0.06 4',
                 'support 0.05 0.06 5.95 0.06 4 20'):
      with self.assertRaises(ValueError):
        Rebar(line)

  def test_bars_lie_inside_the_disk(self) -> None:
    """Bars running out of the disk are refused."""
    disk = Disk(6, 2.7, 0.3)
    with self.assertRaises(ValueError):
      disk.addRebar(Rebar('rebar -0.05 0.06 5.95 0.06 4 20'))
    with self.assertRaises(ValueError):
      disk.addRebar(Rebar('rebar 0.05 0.06 6.05 0.06 4 20'))
    disk.addRebar(Rebar(_TIE))
    self.assertEqual(len(disk.rebars), 1)

  def test_in_the_text(self) -> None:
    """The reinforcement comes last in the disk's text, and is read back
    with it."""
    disk = Disk(DEEP_BEAM)
    disk.addRebar(Rebar(_TIE))
    text = '%s\n%s' % (DEEP_BEAM, _TIE)
    self.assertEqual(str(disk), text)
    self.assertEqual(str(Disk(text)), text)
    self.assertEqual(str(Disk(disk)), text)

  def test_replacing_and_removing(self) -> None:
    """Reinforcement is replaced in its place, or removed."""
    disk = Disk(6, 2.7, 0.3)
    disk.addRebar(Rebar(_TIE))
    disk.replaceRebar(0, Rebar('rebar 0.05 0.1 5.95 0.1 6 16'))
    self.assertEqual(str(disk.rebars[0]), 'rebar 0.05 0.1 5.95 0.1 6 16')
    disk.removeRebar(0)
    self.assertEqual(disk.rebars, ())
    with self.assertRaises(IndexError):
      disk.removeRebar(0)

  def test_resized_carries_the_bars(self) -> None:
    """A resized disk keeps each end of a bar as far from its nearer
    edge as it was: a tie along the bottom still runs from end to end."""
    disk = Disk(6, 2.7, 0.3)
    disk.addRebar(Rebar(_TIE))
    disk.addRebar(Rebar('rebar 0.05 2.64 5.95 2.64 2 12'))
    tie, top = disk.resized(8, 3, 0.3).rebars
    self.assertEqual(str(tie), 'rebar 0.05 0.06 7.95 0.06 4 20')
    self.assertEqual(str(top), 'rebar 0.05 2.94 7.95 2.94 2 12')
