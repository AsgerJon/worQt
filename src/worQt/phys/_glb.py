"""
Scenery in glTF's binary form ('.glb'), as uncannyball makes it (user,
2026-11-15, 'previews/to_worqt.md': "Draw royal_race_scenery.glb around
it with the readScenery loader"): the houses round a lap, only to be
looked at, every piece a set of triangles with one photograph laid on
it, drawn unlit.

'readGlb' reads one into its pieces ('GlbPiece': the corners where the
file has them, in the lap's own x, y and z, m, z up: the file's root
turn, z up to glTF's y up, is left out, as its note says to; each
corner's place on its picture, as the GPU takes it, its foot v nought:
glTF's v nought is a picture's top row; the triangles; which picture;
whether seen from both sides) and its pictures (each the bytes of a
JPEG or PNG, as the file holds them). Only what uncannyball writes is
read: float32 corners and picture places, uint32 corners of triangles,
pictures in the file's own buffer; anything else is refused loudly.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import json
import struct
from typing import NamedTuple

import numpy

#  A '.glb''s first word, its version, and its two chunks' kinds.
GLB_MAGIC, GLB_VERSION = 0x46546C67, 2
JSON_CHUNK, BINARY_CHUNK = 0x4E4F534A, 0x004E4942
#  The accessors' kinds read: float32 and uint32, by glTF's number, and
#  how many numbers each of its shapes holds.
_KINDS = {5126: numpy.float32, 5125: numpy.uint32}
_WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}


class GlbPiece(NamedTuple):
  """
  GlbPiece is one piece of a glTF scene ('readGlb'): the node it hangs
  on ('name'), its material's name ('material'), its corners ('xyz', m,
  float32, a row each), where each lies on its picture ('uv', as the GPU
  takes it: v nought at the picture's foot), its triangles ('triangles',
  three corners each, anticlockwise seen from outside), which of the
  file's pictures lies on it ('picture') and whether it is seen from
  both sides ('both': a tree's crown, seen from under it too).
  """

  name: str
  material: str
  xyz: numpy.ndarray
  uv: numpy.ndarray
  triangles: numpy.ndarray
  picture: int
  both: bool


def _chunksOf(raw: bytes) -> tuple[dict, bytes]:
  """Returns a '.glb''s description (its JSON) and its binary chunk;
  refused loudly where it is not one."""
  magic, version, length = struct.unpack_from('<III', raw, 0)
  if magic != GLB_MAGIC or version != GLB_VERSION:
    raise ValueError('not a glTF 2 binary file (its first words %#x, %d)'
                     % (magic, version))
  size, kind = struct.unpack_from('<II', raw, 12)
  if kind != JSON_CHUNK:
    raise ValueError('a glTF binary file with no description first')
  description = json.loads(raw[20:20 + size].decode('utf-8'))
  start = 20 + size
  size, kind = struct.unpack_from('<II', raw, start)
  if kind != BINARY_CHUNK:
    raise ValueError('a glTF binary file with no binary chunk second')
  return description, raw[start + 8:start + 8 + size]


def _bytesOf(description: dict, blob: bytes, index: int) -> bytes:
  """Returns the bytes of buffer view 'index' (of the file's own
  buffer)."""
  view = description['bufferViews'][index]
  if view.get('buffer', 0) != 0 or 'byteStride' in view:
    raise ValueError('buffer view %d is not plainly in the file' % index)
  start = view.get('byteOffset', 0)
  return blob[start:start + view['byteLength']]


def _arrayOf(description: dict, blob: bytes, index: int) -> numpy.ndarray:
  """Returns accessor 'index' as a numpy array (a row an item, or flat
  for scalars)."""
  accessor = description['accessors'][index]
  kind = _KINDS.get(accessor['componentType'])
  width = _WIDTHS.get(accessor['type'])
  if kind is None or width is None or 'sparse' in accessor:
    raise ValueError('accessor %d is of a kind not read here (%s %s)' % (
      index, accessor['componentType'], accessor['type']))
  data = _bytesOf(description, blob, accessor['bufferView'])
  start = accessor.get('byteOffset', 0)
  flat = numpy.frombuffer(data, kind, accessor['count'] * width, start)
  return flat.reshape(-1, width) if width > 1 else flat


@functools.lru_cache(maxsize=1)
def readGlb(path: str) -> tuple[tuple[GlbPiece, ...], tuple[bytes, ...]]:
  """The 'readGlb' function returns the scene in the '.glb' at 'path',
  read once: its pieces (a 'GlbPiece' for every primitive of every node
  with a mesh, in the file's order; triangles only) and its pictures
  (the bytes of each image, by its index)."""
  with open(path, 'rb') as file:
    raw = file.read()
  description, blob = _chunksOf(raw)
  pictures = []
  for image in description.get('images', ()):
    if 'bufferView' not in image:
      raise ValueError('a picture not in the file: %s' % image.get('uri'))
    pictures.append(bytes(_bytesOf(description, blob, image['bufferView'])))
  textures = description.get('textures', ())
  pieces = []
  for node in description['nodes']:
    if 'mesh' not in node:
      continue
    for part in description['meshes'][node['mesh']]['primitives']:
      if part.get('mode', 4) != 4:
        raise ValueError('a piece of %s is not triangles' % node['name'])
      material = description['materials'][part['material']]
      texture = material['pbrMetallicRoughness']['baseColorTexture']
      uv = numpy.array(_arrayOf(description, blob,
                                part['attributes']['TEXCOORD_0']))
      uv[:, 1] = 1.0 - uv[:, 1]
      pieces.append(GlbPiece(
        node['name'], material.get('name', ''),
        _arrayOf(description, blob, part['attributes']['POSITION']), uv,
        _arrayOf(description, blob, part['indices']).reshape(-1, 3),
        textures[texture['index']]['source'],
        bool(material.get('doubleSided', False))))
  return tuple(pieces), tuple(pictures)
