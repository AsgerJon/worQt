"""
TestSkin covers the avatar's skin ('_skin'): the user's skin file is a
64 x 64 picture; each part's block and its outer layer are 24 corners,
two triangles a face, every triangle wound outward; each face lies on
its place in the picture as Minecraft lays a skin out (the head's front
on pixels 8 to 16 across and down, its outer layer's on 40 to 48 across);
the outer layer is larger all round; the figure is scaled to put its
eyes at the avatar's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import struct

import numpy

from worQt.gaming.sandbox import PERSON, Avatar
from worQt.gaming.sandbox._skin import ASGERJON, EYES, PARTS, SIZE
from worQt.gaming.sandbox._skin import partRows

from . import SandboxTest


class TestSkin(SandboxTest):
  """Tests for the avatar's skin."""

  def test_file(self) -> None:
    """The user's skin is a PNG 64 pixels across and down."""
    head = ASGERJON.read_bytes()[:24]
    self.assertEqual(head[:8], b'\x89PNG\r\n\x1a\n')
    self.assertEqual(struct.unpack('>II', head[16:24]), (SIZE, SIZE))

  def test_wound(self) -> None:
    """Every part's blocks: 24 corners, 12 triangles, each wound outward
    (its corners' turn agreeing with its normal), on the picture."""
    for part in PARTS:
      for outer in (False, True):
        with self.subTest(part=part[0], outer=outer):
          rows, indices = partRows(part, outer, 0.06)
          self.assertEqual(rows.shape, (24, 8))
          self.assertEqual(len(indices), 36)
          self.assertTrue(((rows[:, 6:] >= 0.0) & (rows[:, 6:] <= 1.0))
                          .all())
          for a, b, c in indices.reshape(-1, 3):
            turn = numpy.cross(rows[b, :3] - rows[a, :3],
                               rows[c, :3] - rows[a, :3])
            self.assertGreater(float(numpy.dot(turn, rows[a, 3:6])), 0.0)

  def test_layout(self) -> None:
    """The head's front lies on pixels 8 to 16 across and down; its
    outer layer's on 40 to 48 across; the right leg's front on 4 to 8
    across, 20 to 32 down."""
    for part, outer, across, down in ((PARTS[0], False, (8, 16), (8, 16)),
                                      (PARTS[0], True, (40, 48), (8, 16)),
                                      (PARTS[4], False, (4, 8), (20, 32))):
      with self.subTest(part=part[0], outer=outer):
        rows, _ = partRows(part, outer, 0.06)
        front = rows[rows[:, 3] > 0.5]
        pixels = numpy.column_stack((front[:, 6] * SIZE,
                                     (1.0 - front[:, 7]) * SIZE))
        self.assertEqual(pixels[:, 0].min(), across[0])
        self.assertEqual(pixels[:, 0].max(), across[1])
        self.assertEqual(pixels[:, 1].min(), down[0])
        self.assertEqual(pixels[:, 1].max(), down[1])

  def test_outer_larger(self) -> None:
    """The outer layer is larger all round by its swell."""
    for part in PARTS:
      with self.subTest(part=part[0]):
        inner, _ = partRows(part, False, 1.0)
        outer, _ = partRows(part, True, 1.0)
        grown = outer[:, :3].max(0) - inner[:, :3].max(0)
        self.assertTrue(numpy.allclose(grown, part[5]))

  def test_scale(self) -> None:
    """The figure's eyes are at the avatar's: 'EYES' pixels up at its
    scale is the walker's eye height."""
    avatar = Avatar(PERSON)
    self.assertAlmostEqual(avatar.scale() * EYES, PERSON.eye, 12)
