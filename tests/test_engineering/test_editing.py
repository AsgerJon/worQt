"""
TestEditing covers how a 'Disk' is edited: resized, with its supports
and loads carried along as an engineer would expect; its supports and
loads replaced and removed one at a time, the room a support has and a
free stretch for a new one; and its materials changed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering import Disk, EdgeNum, Support, Load

from . import EngineeringTest, deepBeam


class TestEditing(EngineeringTest):
  """Tests for editing a 'Disk'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LIMITS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_limits(self) -> None:
    """A disk's length and height may be no less than its 'leastSide',
    four thicknesses, and its thickness no more than its
    'greatestThickness', a quarter of the lesser of the two."""
    disk = Disk(6, 2.7, 0.3)
    self.assertAlmostEqual(disk.leastSide, 1.2)
    self.assertAlmostEqual(disk.greatestThickness, 0.675)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  RESIZING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_resized_is_a_new_disk(self) -> None:
    """A resized disk is a new one, of the same materials; the disk it
    came from stays as it was."""
    disk = Disk(6, 2.7, 0.3, 35, 500, 210000)
    resized = disk.resized(7, 3, 0.25)
    self.assertEqual((resized.length, resized.height), (7.0, 3.0))
    self.assertEqual(resized.thickness, 0.25)
    self.assertEqual((resized.fc, resized.fy, resized.E),
                     (35.0, 500.0, 210000.0))
    self.assertEqual(disk.length, 6.0)

  def test_the_far_bearing_rides_along(self) -> None:
    """A support at the end of an edge that moves stays at that end, as
    wide as it was; the one at the other end stays where it is."""
    first, second = deepBeam().resized(7, 2.7, 0.3).supports
    self.assertEqual((first.start, first.end), (0.0, 0.3))
    self.assertAlmostEqual(second.start, 6.7)
    self.assertAlmostEqual(second.end, 7.0)
    self.assertTrue(second.setsX and second.setsY)

  def test_a_load_along_the_whole_edge_stretches(self) -> None:
    """A load along the whole of an edge that grows still covers it, and
    keeps its intensity: the force grows with it."""
    load = deepBeam().resized(7, 2.7, 0.3).loads[0]
    self.assertEqual((load.start, load.end), (0.0, 7.0))
    self.assertAlmostEqual(load.intensity[1], -200.0)
    self.assertAlmostEqual(load.fy, -1400.0)

  def test_others_stay_where_they_are(self) -> None:
    """Supports and loads clear of the moving ends keep their places."""
    disk = Disk(6, 2.7, 0.3)
    disk.addSupport(Support('support bottom 2 2.3 y'))
    disk.addSupport(Support('support left 1 1.3 x'))
    disk.addLoad(Load('load top 2.85 3.15 F 0 -500'))
    resized = disk.resized(8, 3, 0.3)
    self.assertEqual(str(resized.supports[0]), 'support bottom 2 2.3 y')
    self.assertEqual(str(resized.supports[1]), 'support left 1 1.3 x')
    self.assertEqual(str(resized.loads[0]), 'load top 2.85 3.15 F 0 -500')

  def test_shrinking_pushes_back_onto_the_edge(self) -> None:
    """A stretch the shrinking edge would leave behind is pushed back to
    its end, as wide as it was."""
    disk = Disk(6, 2.7, 0.3)
    disk.addSupport(Support('support bottom 4 4.3 y'))
    support = disk.resized(4.1, 2.7, 0.3).supports[0]
    self.assertAlmostEqual(support.start, 3.8)
    self.assertAlmostEqual(support.end, 4.1)

  def test_the_height_moves_the_side_supports(self) -> None:
    """The height moves the top: a support at the top of a side rides up
    with it."""
    disk = Disk(6, 2.7, 0.3)
    disk.addSupport(Support('support right 2.4 2.7 x'))
    support = disk.resized(6, 3, 0.3).supports[0]
    self.assertAlmostEqual(support.start, 2.7)
    self.assertAlmostEqual(support.end, 3.0)

  def test_resized_stays_thin(self) -> None:
    """A disk is not resized out of being a disk."""
    with self.assertRaises(ValueError):
      deepBeam().resized(1.1, 2.7, 0.3)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SUPPORTS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_replacing_a_support(self) -> None:
    """A support is replaced in its place; a replacement that does not
    fit its edge is refused, and the disk stays as it was."""
    disk = deepBeam()
    disk.replaceSupport(0, Support('support bottom 1 1.3 x y'))
    self.assertEqual(str(disk.supports[0]), 'support bottom 1 1.3 x y')
    with self.assertRaises(ValueError):
      disk.replaceSupport(0, Support('support bottom 5.9 6.2 y'))
    self.assertEqual(str(disk.supports[0]), 'support bottom 1 1.3 x y')
    with self.assertRaises(IndexError):
      disk.replaceSupport(2, Support('support bottom 1 1.3 y'))

  def test_removing_a_support(self) -> None:
    """A support is removed by its place; the others keep their order."""
    disk = deepBeam()
    disk.removeSupport(0)
    self.assertEqual(len(disk.supports), 1)
    self.assertEqual(str(disk.supports[0]), 'support bottom 5.7 6 x y')
    with self.assertRaises(IndexError):
      disk.removeSupport(1)

  def test_room_for_a_support(self) -> None:
    """A support has room along its edge up to its neighbours there, or
    the ends of the edge."""
    disk = deepBeam()
    self.assertEqual(disk.supportRoom(0), (0.0, 5.7))
    self.assertEqual(disk.supportRoom(1), (0.3, 6.0))
    disk.addSupport(Support('support left 1 1.3 x'))
    self.assertEqual(disk.supportRoom(2), (0.0, 2.7))

  def test_free_stretch(self) -> None:
    """A free stretch for a new support is found at the start of the
    edge, else at its end, else in between; on a full edge there is
    none."""
    disk = Disk(6, 2.7, 0.3)
    self.assertEqual(disk.freeStretch(EdgeNum.BOTTOM, 0.3), 0.0)
    disk.addSupport(Support('support bottom 0 0.3 y'))
    self.assertAlmostEqual(disk.freeStretch(EdgeNum.BOTTOM, 0.3), 5.7)
    disk.addSupport(Support('support bottom 5.7 6 y'))
    self.assertAlmostEqual(disk.freeStretch(EdgeNum.BOTTOM, 0.3), 0.3)
    disk.addSupport(Support('support left 0 2.7 x'))
    self.assertIsNone(disk.freeStretch(EdgeNum.LEFT, 0.3))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LOADS AND MATERIALS  # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_replacing_and_removing_a_load(self) -> None:
    """A load is replaced in its place, or removed; one that does not fit
    its edge is refused."""
    disk = deepBeam()
    disk.replaceLoad(0, Load('load top 2.85 3.15 F 0 -500'))
    self.assertEqual(str(disk.loads[0]), 'load top 2.85 3.15 F 0 -500')
    with self.assertRaises(ValueError):
      disk.replaceLoad(0, Load('load top 5 7 F 0 -1'))
    with self.assertRaises(IndexError):
      disk.replaceLoad(1, Load('load top 0 1 F 0 -1'))
    disk.removeLoad(0)
    self.assertEqual(disk.loads, ())
    with self.assertRaises(IndexError):
      disk.removeLoad(0)

  def test_with_materials(self) -> None:
    """A disk with other materials is a new one, of the same dimensions,
    supports and loads."""
    disk = deepBeam().withMaterials(35, 500, 210000)
    self.assertEqual((disk.fc, disk.fy, disk.E), (35.0, 500.0, 210000.0))
    self.assertEqual(disk.length, 6.0)
    self.assertEqual(len(disk.supports), 2)
    self.assertEqual(len(disk.loads), 1)
    with self.assertRaises(ValueError):
      deepBeam().withMaterials(0, 500, 210000)
