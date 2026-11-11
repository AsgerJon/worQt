"""
TestTableShapes covers 'prismMesh', a cross-section extruded into
triangles, and 'tableMeshes', the pieces of a carom table: the mesh is
closed and holds the volume it should, mitred or not; each triangle
faces out, its normals of length one; the cushions' noses lie at the
nose height, their ends mitred; the rails' tops at the table's top; the
pedestals reach from the floor to the body; a diamond is a flat rhombus,
long along z; for keglebillard the cushions have straight slots cut over the pockets,
black leather on their backs (the user).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.gaming.billiards import CaromTable, prismMesh, tableMeshes
from worQt.gaming.billiards import diamondMesh
from worQt.gaming.billiards import KeglePin, KegleTable, latheMesh
from worQt.gaming.billiards._table_shapes import APRON_DEPTH, PEDESTAL
from worQt.gaming.billiards._table_shapes import kegleMeshes

from . import BilliardsTest

SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def volumeOf(mesh: numpy.ndarray) -> float:
  """The volume a closed mesh holds, by the divergence theorem;
  negative if its triangles face in."""
  corners = mesh[:, :3].astype(numpy.float64).reshape((-1, 3, 3))
  spans = numpy.cross(corners[:, 1], corners[:, 2])
  return float((corners[:, 0] * spans).sum() / 6.0)


class TestTableShapes(BilliardsTest):
  """Tests for 'prismMesh' and 'tableMeshes'."""

  def test_volume(self) -> None:
    """A unit square drawn 2 long holds 2; mitred, its far side reaching
    one further each end, 3."""
    self.assertAlmostEqual(volumeOf(prismMesh(SQUARE, 2.0, False, 30.0)),
                           2.0, 6)
    self.assertAlmostEqual(volumeOf(prismMesh(SQUARE, 2.0, True, 30.0)),
                           3.0, 6)

  def test_faces_out(self) -> None:
    """Every piece is closed and faces out: it holds a positive volume,
    each triangle turns the way its normals point, and the normals are
    of length one."""
    for name, mesh in tableMeshes(CaromTable()).items():
      self.assertGreater(volumeOf(mesh), 0.0, name)
      corners = mesh[:, :3].astype(numpy.float64).reshape((-1, 3, 3))
      normals = mesh[:, 3:].astype(numpy.float64).reshape((-1, 3, 3))
      faces = numpy.cross(corners[:, 1] - corners[:, 0],
                          corners[:, 2] - corners[:, 0])
      agree = (faces * normals.mean(1)).sum(1)
      self.assertGreater(float(agree.min()), 0.0, name)
      lengths = numpy.linalg.norm(normals.reshape((-1, 3)), None, 1)
      self.assertAlmostEqual(float(lengths.min()), 1.0, 5)
      self.assertAlmostEqual(float(lengths.max()), 1.0, 5)

  def test_diamond(self) -> None:
    """A diamond is a rhombus lying flat, 'long' along z and 'wide'
    along x, 'high' thick about nought: half the box it fills, its
    corners on the axes."""
    mesh = diamondMesh(34.0, 18.0, 2.0)
    low, high = mesh[:, :3].min(0), mesh[:, :3].max(0)
    self.assertEqual([float(v) for v in low], [-9.0, -1.0, -17.0])
    self.assertEqual([float(v) for v in high], [9.0, 1.0, 17.0])
    self.assertAlmostEqual(volumeOf(mesh), 0.5 * 34.0 * 18.0 * 2.0, 3)
    corners = {(float(x), float(z)) for x, _, z in mesh[:, :3]}
    self.assertEqual(corners, {(0.0, -17.0), (9.0, 0.0), (0.0, 17.0),
                               (-9.0, 0.0)})

  def test_pieces(self) -> None:
    """The cushions' noses at the nose height and their far sides a
    cushion deep, mitred; the rails' tops at the table's top; the
    pedestals from the floor up to the body."""
    table = CaromTable()
    meshes = tableMeshes(table)
    cushion = meshes['cushionLong'][:, :3]
    nose = cushion[cushion[:, 0] == 0.0]
    self.assertAlmostEqual(float(nose[:, 1].max()), table.nose, 4)
    self.assertAlmostEqual(float(nose[:, 2].max()), 0.5 * table.length, 2)
    self.assertAlmostEqual(float(cushion[:, 2].max()),
                           0.5 * table.length + table.cushion, 2)
    self.assertAlmostEqual(float(cushion[:, 1].max()), table.top, 4)
    rail = meshes['railShort'][:, :3]
    self.assertAlmostEqual(float(rail[:, 1].max()), table.top, 4)
    self.assertAlmostEqual(float(rail[:, 0].max()), table.rail, 4)
    pedestal = meshes['pedestal'][:, :3]
    self.assertAlmostEqual(float(pedestal[:, 1].min()), 0.0, 4)
    self.assertAlmostEqual(float(pedestal[:, 1].max()),
                           table.bed - APRON_DEPTH, 4)
    self.assertAlmostEqual(float(pedestal[:, 2].max()),
                           0.5 * PEDESTAL[2], 4)

  def test_notched(self) -> None:
    """Keglebillard's cushions have straight slots cut over the pockets
    (the user, after a table's photo): closed, facing out, the long ones
    cut at their middles and both ends, the short ones at both ends,
    square, over the middle pockets as wide as the pocket where it crosses
    the noses' line, 77 mm, at the corners back so far that a ball fits
    between the jaws. The leather is flat panels on the slots' backs, a cushion out
    from the noses, from the cloth up to the rail's top, facing the
    table: one behind each middle pocket, two behind each corner."""
    kegle = KegleTable()
    carom = kegle.table
    meshes = kegleMeshes(kegle)
    for name in ('cushionLongNotched', 'cushionShortNotched'):
      mesh = meshes[name]
      self.assertGreater(volumeOf(mesh), 0.0, name)
      corners = mesh[:, :3].astype(numpy.float64).reshape((-1, 3, 3))
      normals = mesh[:, 3:].astype(numpy.float64).reshape((-1, 3, 3))
      faces = numpy.cross(corners[:, 1] - corners[:, 0],
                          corners[:, 2] - corners[:, 0])
      self.assertGreater(float((faces * normals.mean(1)).sum(1).min()),
                         0.0, name)
    pockets = kegle.pockets()
    self.assertAlmostEqual(2.0 * pockets.half, 77.0, 0)
    self.assertGreater(pockets.corner * 2.0 ** 0.5, 2.0 * carom.radius)
    long = meshes['cushionLongNotched'][:, :3].astype(numpy.float64)
    for depth in (0.0, carom.cushion):
      rows = long[numpy.abs(long[:, 0] - depth) < 1e-6]
      self.assertAlmostEqual(float(numpy.abs(rows[:, 2]).min()),
                             pockets.half, 3)
      self.assertAlmostEqual(float(numpy.abs(rows[:, 2]).max()),
                             0.5 * carom.length - pockets.corner, 3)
    short = meshes['cushionShortNotched'][:, :3].astype(numpy.float64)
    self.assertAlmostEqual(float(short[:, 2].max()),
                           0.5 * carom.width - pockets.corner, 3)
    leather = meshes['pocketLeather'].astype(numpy.float64)
    self.assertEqual(len(leather), 6 * (2 + 2 * 4))
    x = leather[:, 0] + 0.5 * carom.width
    y = 0.5 * carom.length - leather[:, 2]
    out = numpy.maximum.reduce([-x, x - carom.width, -y, y - carom.length])
    self.assertAlmostEqual(float(out.max()), carom.cushion, 3)
    self.assertAlmostEqual(float(leather[:, 1].min()), 0.0, 6)
    self.assertAlmostEqual(float(leather[:, 1].max()), carom.top, 3)
    lengths = numpy.linalg.norm(leather[:, 3:], None, 1)
    self.assertAlmostEqual(float(lengths.min()), 1.0, 5)

  def test_lathe(self) -> None:
    """A keglebillard pin turned on the lathe: as tall as it is, as wide
    as its body, every triangle facing out, none flat, on a flat foot
    facing down."""
    mesh = latheMesh(KeglePin().profile, 32)
    places, normals = mesh[:, :3], mesh[:, 3:]
    self.assertEqual(len(mesh) % 3, 0)
    self.assertAlmostEqual(float(places[:, 1].min()), 0.0, 6)
    self.assertAlmostEqual(float(places[:, 1].max()), 120.0, 4)
    widest = float(numpy.hypot(places[:, 0], places[:, 2]).max())
    self.assertAlmostEqual(widest, 9.94, 2)
    corners = places.reshape(-1, 3, 3)
    sides = numpy.cross(corners[:, 1] - corners[:, 0],
                        corners[:, 2] - corners[:, 0])
    facing = normals.reshape(-1, 3, 3).mean(axis=1)
    self.assertTrue(numpy.all(numpy.linalg.norm(sides, axis=1) > 1e-9))
    self.assertTrue(numpy.all(numpy.einsum('ij,ij->i', sides, facing)
                              > 0.0))
    foot = numpy.isclose(places[:, 1], 0.0) & (normals[:, 1] < -0.5)
    self.assertGreater(int(foot.sum()), 0)

