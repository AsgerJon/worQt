"""
RunDiskWidget covers 'DiskWidget': it shows a disk to scale, fitted and
centred in its frame, maps between metres on the disk and pixels on the
screen both ways, and paints the disk with its supports and loads.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPointF
from worktoy.waitaminute import TypeException

from worQt.engineering import Disk
from worQt.engineering.gui import DiskWidget

from . import EngineeringWidgetTest, deepBeam


class RunDiskWidget(EngineeringWidgetTest):
  """Tests for 'DiskWidget'."""

  def _liveWidget(self, disk: Disk = None) -> DiskWidget:
    widget = DiskWidget()
    if disk is not None:
      widget.disk = disk
    widget.resize(800, 500)
    self.showLive(widget)
    widget.repaint()
    return widget

  def run_starts_empty(self) -> None:
    """A new widget shows no disk, and paints all the same."""
    widget = self._liveWidget()
    self.assertIsNone(widget.disk)
    self.assertTrue(widget.diskRect().isEmpty())
    self.assertFalse(widget.grab().isNull())

  def run_shows_only_disks(self) -> None:
    """What is no disk is refused."""
    widget = DiskWidget()
    with self.assertRaises(TypeException):
      widget.disk = 'disk 6 x 2.7 x 0.3'

  def run_fits_the_disk(self) -> None:
    """The disk is drawn to scale, as large as fits in the frame and
    centred in it."""
    widget = self._liveWidget(deepBeam())
    frame, box = widget.frameRect(), widget.diskRect()
    self.assertTrue(frame.adjusted(-1e-6, -1e-6, 1e-6, 1e-6).contains(box))
    self.assertAlmostEqual(box.width() / box.height(), 6.0 / 2.7)
    fills = min(frame.width() - box.width(), frame.height() - box.height())
    self.assertAlmostEqual(fills, 0.0)
    self.assertAlmostEqual(box.center().x(), frame.center().x())
    self.assertAlmostEqual(box.center().y(), frame.center().y())

  def run_follows_a_new_disk(self) -> None:
    """Showing another disk fits that one instead."""
    widget = self._liveWidget(deepBeam())
    widget.disk = Disk(2.0, 4.0, 0.2)
    box = widget.diskRect()
    self.assertAlmostEqual(box.width() / box.height(), 0.5)

  def run_maps_metres_both_ways(self) -> None:
    """The disk's corner at the origin is the bottom left of its box,
    y grows upwards on the disk and downwards on the screen, and a point
    mapped to the screen maps back to where it was."""
    widget = self._liveWidget(deepBeam())
    box = widget.diskRect()
    origin = widget.toScreen(0.0, 0.0)
    corner = widget.toScreen(6.0, 2.7)
    self.assertAlmostEqual(origin.x(), box.left())
    self.assertAlmostEqual(origin.y(), box.bottom())
    self.assertAlmostEqual(corner.x(), box.right())
    self.assertAlmostEqual(corner.y(), box.top())
    x, y = widget.toModel(widget.toScreen(1.5, 2.0))
    self.assertAlmostEqual(x, 1.5)
    self.assertAlmostEqual(y, 2.0)
    x, y = widget.toModel(QPointF(box.center()))
    self.assertAlmostEqual(x, 3.0)
    self.assertAlmostEqual(y, 1.35)

  def run_paints_the_disk(self) -> None:
    """The disk is filled in its own colour, its supports and loads drawn
    around it."""
    widget = self._liveWidget(deepBeam())
    image = widget.grab().toImage()
    ratio = image.devicePixelRatio()
    center = widget.diskRect().center()
    pixel = image.pixelColor(int(center.x() * ratio),
                             int(center.y() * ratio))
    self.assertEqual(pixel.rgb(), widget.diskColor.Q.rgb())
