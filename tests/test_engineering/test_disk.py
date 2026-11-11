"""
TestDisk covers 'Disk', a rectangular concrete disk loaded in its own
plane: its dimensions, which make it thin, and its materials, its
supports and loads, which must fit their edges, and its text, which it
reads back.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering import Disk, EdgeNum, Support, Load

from . import EngineeringTest, DEEP_BEAM, deepBeam


class TestDisk(EngineeringTest):
  """Tests for 'Disk'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DIMENSIONS AND MATERIALS   # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_dimensions(self) -> None:
    """A disk has a length along x, a height along y and a thickness, in
    metres."""
    disk = Disk(6, 2.7, 0.3)
    self.assertEqual(disk.length, 6.0)
    self.assertEqual(disk.height, 2.7)
    self.assertEqual(disk.thickness, 0.3)

  def test_default_materials(self) -> None:
    """A disk given no materials has concrete of fc = 30 MPa and
    reinforcement of fy = 800 MPa and E = 200000 MPa, and says so in
    its text."""
    disk = Disk(6, 2.7, 0.3)
    self.assertEqual(disk.fc, 30.0)
    self.assertEqual(disk.fy, 800.0)
    self.assertEqual(disk.E, 200000.0)
    self.assertEqual(str(disk), 'disk 6 x 2.7 x 0.3 fc 30 fy 800 E 200000')

  def test_given_materials(self) -> None:
    """Materials given are the disk's own, and each is above zero."""
    disk = Disk(6, 2.7, 0.3, 35, 500, 210000)
    self.assertEqual((disk.fc, disk.fy, disk.E), (35.0, 500.0, 210000.0))
    for materials in ((0, 500, 210000), (35, -500, 210000), (35, 500, 0)):
      with self.assertRaises(ValueError):
        Disk(6, 2.7, 0.3, *materials)

  def test_dimensions_are_positive(self) -> None:
    """No dimension is zero or less."""
    for dims in ((0, 2.7, 0.3), (6, -2.7, 0.3), (6, 2.7, 0)):
      with self.assertRaises(ValueError):
        Disk(*dims)

  def test_a_disk_is_thin(self) -> None:
    """Its length and its height are each at least four times its
    thickness, as EN 1992-1-1 9.6.1 asks of a wall."""
    Disk(1.2, 1.2, 0.3)
    for dims in ((1.1, 2.7, 0.3), (6, 1.1, 0.3), (0.5, 0.5, 0.5)):
      with self.assertRaises(ValueError):
        Disk(*dims)

  def test_edges(self) -> None:
    """The bottom and the top are as long as the disk, the left and the
    right as high; a position along an edge counts from the left on the
    bottom and the top, and from the bottom on the left and the right."""
    disk = Disk(6, 2.7, 0.3)
    self.assertEqual(disk.edgeLength(EdgeNum.BOTTOM), 6.0)
    self.assertEqual(disk.edgeLength(EdgeNum.TOP), 6.0)
    self.assertEqual(disk.edgeLength(EdgeNum.LEFT), 2.7)
    self.assertEqual(disk.edgeLength(EdgeNum.RIGHT), 2.7)
    self.assertEqual(disk.pointAt(EdgeNum.BOTTOM, 1.5), (1.5, 0.0))
    self.assertEqual(disk.pointAt(EdgeNum.TOP, 1.5), (1.5, 2.7))
    self.assertEqual(disk.pointAt(EdgeNum.LEFT, 1.0), (0.0, 1.0))
    self.assertEqual(disk.pointAt(EdgeNum.RIGHT, 1.0), (6.0, 1.0))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SUPPORTS AND LOADS   # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_assigning_supports_and_loads(self) -> None:
    """Supports and loads are assigned one at a time, and kept in the
    order they came."""
    disk = Disk(6, 2.7, 0.3)
    self.assertEqual(disk.supports, ())
    self.assertEqual(disk.loads, ())
    first = Support('support bottom 0 0.3 y')
    second = Support('support bottom 5.7 6 x y')
    disk.addSupport(first)
    disk.addSupport(second)
    disk.addLoad(Load('load top 0 6 F 0 -1200'))
    self.assertEqual(disk.supports, (first, second))
    self.assertEqual(len(disk.loads), 1)

  def test_supports_and_loads_fit_their_edge(self) -> None:
    """A stretch that runs past the end of its edge is refused, and the
    disk stays as it was."""
    disk = Disk(6, 2.7, 0.3)
    with self.assertRaises(ValueError):
      disk.addSupport(Support('support left 0 3 x'))
    with self.assertRaises(ValueError):
      disk.addLoad(Load('load top 5.9 6.1 F 0 -10'))
    self.assertEqual(disk.supports, ())
    self.assertEqual(disk.loads, ())
    disk.addSupport(Support('support left 0 2.7 x'))
    self.assertEqual(len(disk.supports), 1)

  def test_copy_is_its_own(self) -> None:
    """A copy has the same materials, supports and loads, and what is
    assigned to it afterwards stays its own."""
    disk = Disk(Disk(6, 2.7, 0.3, 35, 500, 210000))
    self.assertEqual((disk.fc, disk.fy, disk.E), (35.0, 500.0, 210000.0))
    disk = deepBeam()
    copy = Disk(disk)
    self.assertEqual(str(copy), str(disk))
    copy.addLoad(Load('load top 2.85 3.15 F 0 -500'))
    self.assertEqual(len(copy.loads), 2)
    self.assertEqual(len(disk.loads), 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TEXT   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_text_round_trip(self) -> None:
    """A disk's text is its disk line, then its supports, then its loads;
    a disk reads its own text back."""
    disk = deepBeam()
    self.assertEqual(disk.length, 6.0)
    self.assertEqual(len(disk.supports), 2)
    self.assertEqual(len(disk.loads), 1)
    self.assertEqual(str(disk), DEEP_BEAM)
    self.assertEqual(str(Disk(str(disk))), DEEP_BEAM)

  def test_text_materials(self) -> None:
    """The disk line may name its materials in any order or leave any of
    them out, which then take their defaults; the text written back names
    all three."""
    disk = Disk('disk 6 x 2.7 x 0.3 E 210000 fc 35')
    self.assertEqual((disk.fc, disk.fy, disk.E), (35.0, 800.0, 210000.0))
    self.assertEqual(str(disk), 'disk 6 x 2.7 x 0.3 fc 35 fy 800 E 210000')
    self.assertEqual(str(Disk('disk 6 x 2.7 x 0.3')), str(Disk(6, 2.7, 0.3)))

  def test_text_in_any_order(self) -> None:
    """After the disk line, supports and loads come in any order, with
    blank lines between them; the text written back is in order."""
    text = """
disk 6 x 2.7 x 0.3 fc 30 fy 800 E 200000

load top 0 6 F 0 -1200
support bottom 0 0.3 y

support bottom 5.7 6 x y
"""
    self.assertEqual(str(Disk(text)), DEEP_BEAM)

  def test_text_starts_with_the_disk(self) -> None:
    """The first line is the disk line, and the only one; every other
    line is a support or a load."""
    texts = (
      '',
      'support bottom 0 0.3 y',
      'disk 6 by 2.7 by 0.3',
      'disk 6 x 2.7 x 0.3 fc',
      'disk 6 x 2.7 x 0.3 fc 30 fc 35',
      'disk 6 x 2.7 x 0.3 C30/37',
      'disk 6 x 2.7 x 0.3 fc thirty',
      'disk 6 x 2.7 x 0.3\ndisk 6 x 2.7 x 0.3',
      'disk 6 x 2.7 x 0.3\nbeam 0 6',
    )
    for text in texts:
      with self.assertRaises(ValueError):
        Disk(text)
