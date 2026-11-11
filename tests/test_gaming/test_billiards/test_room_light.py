"""
TestRoomLight covers 'roomLight', the light of the room round the
table, and 'radianceBytes', its '.hdr' bytes: the lamp straight up is
far the brightest and runs along the table, not across it; the walls
glow at the horizon, the ceiling and floor darker; the bytes carry the
Radiance header and read back to the image.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.gaming.billiards.gui import radianceBytes, roomLight

from . import BilliardsTest


class TestRoomLight(BilliardsTest):
  """Tests for 'roomLight' and 'radianceBytes'."""

  def test_shape(self) -> None:
    """Rows by columns by red, green and blue, in floats."""
    image = roomLight(64, 32)
    self.assertEqual(image.shape, (32, 64, 3))
    self.assertEqual(image.dtype, numpy.float32)
    self.assertGreater(float(image.min()), 0.0)

  def test_lamp(self) -> None:
    """Straight up is the lamp, far the brightest, fifteen times the
    walls; half way up it lies along the table, the middle column, not
    across it, a quarter round."""
    image = roomLight(512, 256)
    lamp = float(image[0, 256, 0])
    self.assertEqual(lamp, float(image.max()))
    self.assertGreater(lamp, 15.0 * float(image[128, 0, 0]))
    half = 64  # rows down to 45 degrees up
    self.assertEqual(float(image[half, 256, 0]), lamp)
    self.assertLess(float(image[half, 384, 0]), 1.0)

  def test_room(self) -> None:
    """The walls glow at the horizon; the ceiling and floor are
    darker."""
    image = roomLight(512, 256)
    walls = float(image[128, 100, 0])
    self.assertGreater(walls, float(image[250, 100, 0]))
    self.assertGreater(walls, float(image[100, 128, 0]))

  def test_bytes(self) -> None:
    """The Radiance header, then four bytes a pixel that read back to
    the image within a part in a hundred of the brightest."""
    image = roomLight(64, 32)
    data = radianceBytes(image)
    header = b'#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y 32 +X 64\n'
    self.assertTrue(data.startswith(header))
    body = data[len(header):]
    self.assertEqual(len(body), 64 * 32 * 4)
    pixels = numpy.frombuffer(body, numpy.uint8).reshape((32, 64, 4))
    mantissas = pixels[..., :3].astype(numpy.float64)
    exponents = pixels[..., 3].astype(numpy.int64) - 136
    back = mantissas * numpy.ldexp(1.0, exponents)[..., None]
    worst = float(numpy.abs(back - image).max())
    self.assertLess(worst, 0.01 * float(image.max()))
