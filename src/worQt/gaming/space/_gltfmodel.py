"""
GltfModel reads a binary glTF file ('.glb', as Blender exports it) into
meshes the cabin draws itself (Qt-free, numpy): each node's mesh, every
primitive its rows of eight numbers a corner (place, normal, where on a
picture) in the model's own frame (its nodes' turns and sizes applied),
its triangles, its material; the materials (colour, metalness,
roughness, see-through, picture) and the pictures' bytes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy

#  glTF's numbers by their component type, and how many make an element.
COMPONENTS = {5120: numpy.int8, 5121: numpy.uint8, 5122: numpy.int16,
              5123: numpy.uint16, 5125: numpy.uint32, 5126: numpy.float32}
SIZES = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def _matrixOf(node: dict) -> numpy.ndarray:
  """Returns a node's own matrix (its 'matrix', or translation, rotation
  and scale), four by four."""
  if 'matrix' in node:
    return numpy.array(node['matrix'], numpy.float64).reshape(4, 4).T
  x, y, z, w = node.get('rotation', (0.0, 0.0, 0.0, 1.0))
  turn = numpy.array((
    (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
    (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
    (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y))))
  out = numpy.eye(4)
  out[:3, :3] = turn * numpy.array(node.get('scale', (1.0, 1.0, 1.0)))
  out[:3, 3] = node.get('translation', (0.0, 0.0, 0.0))
  return out


class GltfModel:
  """
  GltfModel holds a '.glb' file read ('path'): its document ('doc'), its
  binary chunk ('blob'). 'parts' returns every drawn primitive in the
  model's own frame, 'material' a material's look, 'picture' a
  picture's bytes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  path: Path
  doc: dict
  blob: bytes

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, path: object) -> None:
    self.path = Path(path)
    data = self.path.read_bytes()
    magic, version, _ = struct.unpack_from('<4sII', data, 0)
    if magic != b'glTF' or version != 2:
      raise ValueError('%s is no binary glTF 2 file' % self.path)
    length, kind = struct.unpack_from('<I4s', data, 12)
    if kind != b'JSON':
      raise ValueError('%s does not begin with its JSON' % self.path)
    self.doc = json.loads(data[20:20 + length])
    at = 20 + length
    self.blob = b''
    if at + 8 <= len(data):
      size, kind = struct.unpack_from('<I4s', data, at)
      if kind == b'BIN\x00':
        self.blob = data[at + 8:at + 8 + size]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def parts(self, frame: str, left: tuple) -> list:
    """The 'parts' method returns every primitive drawn, each (node's
    name, material index (None: glTF's default), rows, triangles), in
    the frame of node 'frame' (None: the scene's), nodes named in
    'left' left out."""
    doc = self.doc
    nodes = doc['nodes']
    worlds = {}

    def walked(index: int, above: numpy.ndarray) -> None:
      """Gives node 'index' and its children their matrices."""
      world = above @ _matrixOf(nodes[index])
      worlds[index] = world
      for child in nodes[index].get('children', ()):
        walked(child, world)

    for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
      walked(root, numpy.eye(4))
    back = numpy.eye(4)
    if frame is not None:
      named = [k for k, node in enumerate(nodes)
               if node.get('name') == frame]
      if not named:
        raise KeyError('%s has no node %r' % (self.path, frame))
      back = numpy.linalg.inv(worlds[named[0]])
    out = []
    for index, node in enumerate(nodes):
      if 'mesh' not in node or node.get('name') in left:
        continue
      matrix = back @ worlds[index]
      turn = numpy.linalg.inv(matrix[:3, :3]).T
      for primitive in doc['meshes'][node['mesh']]['primitives']:
        out.append((node.get('name'), primitive.get('material'),
                    self._rowsOf(primitive, matrix, turn),
                    self._trianglesOf(primitive)))
    return out

  def material(self, index: int | None) -> dict:
    """The 'material' method returns material 'index''s look: 'colour'
    (red, green, blue, nought to one, as glTF gives it: linear),
    'metal', 'rough', 'clear' (how see-through: transmission or blended
    alpha), 'picture' (its picture's index, None: none)."""
    if index is None:
      return {'colour': (1.0, 1.0, 1.0), 'metal': 1.0, 'rough': 1.0,
              'clear': 0.0, 'picture': None}
    material = self.doc['materials'][index]
    pbr = material.get('pbrMetallicRoughness', {})
    colour = pbr.get('baseColorFactor', (1.0, 1.0, 1.0, 1.0))
    clear = material.get('extensions', {}).get(
      'KHR_materials_transmission', {}).get('transmissionFactor', 0.0)
    if material.get('alphaMode') == 'BLEND':
      clear = max(clear, 1.0 - colour[3])
    texture = pbr.get('baseColorTexture')
    picture = None if texture is None else self.doc['textures'][
      texture['index']]['source']
    return {'colour': tuple(colour[:3]), 'metal': pbr.get(
      'metallicFactor', 1.0), 'rough': pbr.get('roughnessFactor', 1.0),
            'clear': float(clear), 'picture': picture}

  def picture(self, index: int) -> bytes:
    """The 'picture' method returns picture 'index''s file's bytes (as
    stored: a PNG or a JPEG)."""
    image = self.doc['images'][index]
    view = self.doc['bufferViews'][image['bufferView']]
    at = view.get('byteOffset', 0)
    return self.blob[at:at + view['byteLength']]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _read(self, index: int) -> numpy.ndarray:
    """Returns accessor 'index''s elements, one a row (float64 for
    floats)."""
    accessor = self.doc['accessors'][index]
    view = self.doc['bufferViews'][accessor['bufferView']]
    kind = numpy.dtype(COMPONENTS[accessor['componentType']])
    width = SIZES[accessor['type']]
    count = accessor['count']
    at = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', kind.itemsize * width)
    raw = numpy.frombuffer(self.blob, numpy.uint8, stride * (count - 1)
                           + kind.itemsize * width, at)
    rows = numpy.lib.stride_tricks.as_strided(
      raw, (count, kind.itemsize * width), (stride, 1)).copy()
    out = rows.view(kind).reshape(count, width)
    return out.astype(numpy.float64) if kind.kind == 'f' else out

  def _rowsOf(self, primitive: dict, matrix: numpy.ndarray,
              turn: numpy.ndarray) -> numpy.ndarray:
    """Returns a primitive's rows of eight: place and normal through
    'matrix' (normals by 'turn', made unit), where on its picture (v
    from the bottom: glTF's from the top)."""
    attributes = primitive['attributes']
    places = self._read(attributes['POSITION'])
    count = len(places)
    rows = numpy.zeros((count, 8))
    rows[:, :3] = places @ matrix[:3, :3].T + matrix[:3, 3]
    if 'NORMAL' in attributes:
      normals = self._read(attributes['NORMAL']) @ turn.T
      size = numpy.linalg.norm(normals, axis=1, keepdims=True)
      rows[:, 3:6] = normals / numpy.maximum(size, 1e-12)
    if 'TEXCOORD_0' in attributes:
      where = self._read(attributes['TEXCOORD_0'])
      rows[:, 6] = where[:, 0]
      rows[:, 7] = 1.0 - where[:, 1]
    return rows

  def _trianglesOf(self, primitive: dict) -> numpy.ndarray:
    """Returns a primitive's triangles' corners (its indices, or its
    rows in threes)."""
    if primitive.get('mode', 4) != 4:
      raise ValueError('%s: only triangles are drawn' % self.path)
    if 'indices' not in primitive:
      count = self.doc['accessors'][primitive['attributes'][
        'POSITION']]['count']
      return numpy.arange(count, dtype=numpy.uint32)
    return self._read(primitive['indices']).reshape(-1).astype(
      numpy.uint32)
