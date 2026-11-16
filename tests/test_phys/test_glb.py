"""
TestGlb covers reading scenery in glTF's binary form ('_glb.readGlb';
user, 2026-11-15, uncannyball's houses round the lap's start): a file
written here, a piece of two triangles on a node under a root that
holds none, its corners and triangles as written, its places on its
picture with v turned over (glTF's v nought is a picture's top row, the
GPU's its foot), its picture's bytes, seen from both sides as its
material says; what is not such a file, or holds what is not read, is
refused loudly.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import os
import struct
import tempfile

import numpy

from worQt.phys._glb import readGlb

from . import PhysTest

#  The piece written: its corners, its places on its picture, its
#  triangles, its picture's bytes (not a real picture: only carried).
XYZ = numpy.array(((1600.0, 500.0, 2.0), (1601.0, 500.0, 2.0),
                   (1601.0, 501.0, 2.5), (1600.0, 501.0, 2.5)),
                  numpy.float32)
UV = numpy.array(((0.0, 1.0), (1.0, 1.0), (1.0, 0.25), (0.0, 0.0)),
                 numpy.float32)
TRIANGLES = numpy.array((0, 1, 2, 0, 2, 3), numpy.uint32)
PICTURE = b'\xff\xd8\xff\xe0 not really a picture'


def _padded(data: bytes, filler: bytes) -> bytes:
  """Returns 'data' padded with 'filler' to four bytes' length."""
  return data + filler * (-len(data) % 4)


def _written(folder: str, indexKind: int) -> str:
  """Writes the piece as a '.glb' into 'folder' (its triangles' corners
  of glTF's kind 'indexKind'), returns its path."""
  parts = (XYZ.tobytes(), UV.tobytes(), TRIANGLES.tobytes(), PICTURE)
  views, blob = [], b''
  for part in parts:
    views.append({'buffer': 0, 'byteOffset': len(blob),
                  'byteLength': len(part)})
    blob = _padded(blob + part, b'\x00')
  description = {
    'asset': {'version': '2.0'},
    'scene': 0, 'scenes': [{'nodes': [0]}],
    'nodes': [{'name': 'scenery', 'rotation': [-0.7071068, 0, 0, 0.7071068],
               'children': [1]},
              {'name': 'chunk_0_0', 'mesh': 0}],
    'meshes': [{'primitives': [{'attributes': {'POSITION': 0,
                                               'TEXCOORD_0': 1},
                                'indices': 2, 'material': 0}]}],
    'accessors': [
      {'bufferView': 0, 'componentType': 5126, 'count': 4, 'type': 'VEC3'},
      {'bufferView': 1, 'componentType': 5126, 'count': 4, 'type': 'VEC2'},
      {'bufferView': 2, 'componentType': indexKind, 'count': 6,
       'type': 'SCALAR'}],
    'bufferViews': views,
    'buffers': [{'byteLength': len(blob)}],
    'materials': [{'name': 'crown', 'doubleSided': True,
                   'pbrMetallicRoughness': {'baseColorTexture': {
                     'index': 0}},
                   'extensions': {'KHR_materials_unlit': {}}}],
    'textures': [{'source': 0}],
    'images': [{'bufferView': 3, 'mimeType': 'image/jpeg'}]}
  text = _padded(json.dumps(description).encode('utf-8'), b' ')
  raw = (struct.pack('<III', 0x46546C67, 2, 28 + len(text) + len(blob))
         + struct.pack('<II', len(text), 0x4E4F534A) + text
         + struct.pack('<II', len(blob), 0x004E4942) + blob)
  path = os.path.join(folder, 'scenery-%d.glb' % indexKind)
  with open(path, 'wb') as file:
    file.write(raw)
  return path


class TestGlb(PhysTest):
  """Tests for reading scenery (a moment)."""

  def setUp(self) -> None:
    """A folder for the files written."""
    self.folder = tempfile.TemporaryDirectory()

  def tearDown(self) -> None:
    """The folder gone."""
    self.folder.cleanup()

  def test_read(self) -> None:
    """One piece, as written: on its node, its material's, its corners
    and triangles, its places with v turned over, its picture, both
    sides; the root's turn left out."""
    pieces, pictures = readGlb(_written(self.folder.name, 5125))
    self.assertEqual(len(pieces), 1)
    piece = pieces[0]
    self.assertEqual((piece.name, piece.material), ('chunk_0_0', 'crown'))
    self.assertTrue(numpy.array_equal(piece.xyz, XYZ))
    self.assertTrue(numpy.array_equal(piece.triangles,
                                      TRIANGLES.reshape(-1, 3)))
    self.assertTrue(numpy.allclose(piece.uv[:, 0], UV[:, 0]))
    self.assertTrue(numpy.allclose(piece.uv[:, 1], 1.0 - UV[:, 1]))
    self.assertEqual(piece.picture, 0)
    self.assertTrue(piece.both)
    self.assertEqual(pictures, (PICTURE,))

  def test_refused(self) -> None:
    """Triangles' corners of another kind (uint16) are refused, as is a
    file that is not a '.glb'."""
    with self.assertRaises(ValueError):
      readGlb(_written(self.folder.name, 5123))
    path = os.path.join(self.folder.name, 'not.glb')
    with open(path, 'wb') as file:
      file.write(b'PK\x03\x04' + bytes(40))
    with self.assertRaises(ValueError):
      readGlb(path)
