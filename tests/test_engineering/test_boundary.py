"""
TestBoundary covers what acts on a disk's edges: 'EdgeNum' names the
edges, a 'Support' sets displacements over a stretch of one and a 'Load'
applies a force over a stretch of one. Each reads and writes its own
line of the disk's text.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.waitaminute.keenum import KeeResolveError

from worQt.engineering import EdgeNum, Support, Load

from . import EngineeringTest


class TestBoundary(EngineeringTest):
  """Tests for 'EdgeNum', 'Support' and 'Load'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  EDGES  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_edges(self) -> None:
    """The four edges are found by name; the bottom and the top run
    along x, the left and the right along y, and each knows the way out
    of the disk."""
    self.assertIs(EdgeNum('bottom'), EdgeNum.BOTTOM)
    self.assertTrue(EdgeNum.BOTTOM.horizontal)
    self.assertTrue(EdgeNum.TOP.horizontal)
    self.assertFalse(EdgeNum.LEFT.horizontal)
    self.assertFalse(EdgeNum.RIGHT.horizontal)
    self.assertEqual(EdgeNum.BOTTOM.outward, (0.0, -1.0))
    self.assertEqual(EdgeNum.RIGHT.outward, (1.0, 0.0))
    self.assertEqual(EdgeNum.TOP.outward, (0.0, 1.0))
    self.assertEqual(EdgeNum.LEFT.outward, (-1.0, 0.0))
    with self.assertRaises(KeeResolveError):
      EdgeNum('middle')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SUPPORTS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_support_reads_its_line(self) -> None:
    """A support line names the edge, the stretch along it and the
    displacements it sets."""
    support = Support('support bottom 0 0.3 y')
    self.assertIs(support.edge, EdgeNum.BOTTOM)
    self.assertEqual(support.start, 0.0)
    self.assertEqual(support.end, 0.3)
    self.assertAlmostEqual(support.width, 0.3)
    self.assertFalse(support.setsX)
    self.assertTrue(support.setsY)

  def test_support_writes_its_line(self) -> None:
    """A support gives back the line it was read from, and one built from
    values writes the same line its text would."""
    for line in ('support bottom 0 0.3 y', 'support bottom 5.7 6 x y',
                 'support left 1.2 1.5 x'):
      self.assertEqual(str(Support(line)), line)
    support = Support(EdgeNum.BOTTOM, 5.7, 6.0, True, True)
    self.assertEqual(str(support), 'support bottom 5.7 6 x y')
    self.assertEqual(str(Support(support)), str(support))

  def test_support_sets_something(self) -> None:
    """A support that sets no displacement is no support, and only 'x'
    and 'y' can be set, each once."""
    for line in ('support bottom 0 0.3', 'support bottom 0 0.3 z',
                 'support bottom 0 0.3 y y'):
      with self.assertRaises(ValueError):
        Support(line)
    with self.assertRaises(ValueError):
      Support(EdgeNum.BOTTOM, 0.0, 0.3, False, False)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LOADS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_load_reads_its_line(self) -> None:
    """A load line names the edge, the stretch along it and, after 'F',
    the force in kN, which spreads evenly over the stretch."""
    load = Load('load top 2.85 3.15 F 0 -500')
    self.assertIs(load.edge, EdgeNum.TOP)
    self.assertEqual(load.start, 2.85)
    self.assertEqual(load.end, 3.15)
    self.assertEqual(load.fx, 0.0)
    self.assertEqual(load.fy, -500.0)
    self.assertAlmostEqual(load.width, 0.3)
    qx, qy = load.intensity
    self.assertAlmostEqual(qx, 0.0)
    self.assertAlmostEqual(qy, -500.0 / 0.3)

  def test_load_writes_its_line(self) -> None:
    """A load gives back the line it was read from, and one built from
    values writes the same line its text would."""
    for line in ('load top 2.85 3.15 F 0 -500', 'load top 0 6 F 0 -1200',
                 'load right 2 2.5 F -40 0'):
      self.assertEqual(str(Load(line)), line)
    load = Load(EdgeNum.TOP, 0.0, 6.0, 0.0, -1200.0)
    self.assertEqual(str(load), 'load top 0 6 F 0 -1200')
    self.assertEqual(str(Load(load)), str(load))

  def test_load_line_needs_its_force(self) -> None:
    """The force comes after 'F', with both its components."""
    for line in ('load top 0 6 0 -1200', 'load top 0 6 F -1200',
                 'load top 0 6 F 0 -1200 7', 'support top 0 6 F 0 -1'):
      with self.assertRaises(ValueError):
        Load(line)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  STRETCHES  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_everything_has_a_width(self) -> None:
    """Supports and loads act over a stretch of the edge, never at a
    point: a stretch starts at zero or later and ends after it starts."""
    for start, end in ((0.3, 0.3), (0.3, 0.0), (-0.1, 0.3)):
      with self.assertRaises(ValueError):
        Support(EdgeNum.BOTTOM, start, end, False, True)
      with self.assertRaises(ValueError):
        Load(EdgeNum.TOP, start, end, 0.0, -1.0)

  def test_numbers_must_be_numbers(self) -> None:
    """A number in a line that is no finite number is refused."""
    for line in ('support bottom zero 0.3 y', 'support bottom 0 inf y',
                 'support bottom nan 0.3 y'):
      with self.assertRaises(ValueError):
        Support(line)
