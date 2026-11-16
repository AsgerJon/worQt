"""
The steam locomotive's model (user, 2026-11-16: found on 1DesignTool,
"Steam Locomotive", free under its 3D library licence: used in a work,
never handed on as a file on its own, so it lives in the gitignored
'models' folder; made, as its page says, by Claude Code in 1DesignTool):
a binary glTF ('.glb') read into its parts ('modelParts': each named
part's meshes, every node's place applied), in the engine's own frame
(x ahead, y to the left, z up, its origin on the rails' top under the
main driver's axle; the model's x across, y up, z ahead), with its
materials as looks (their colours from linear to the screen's, their
metal kept to what the sandbox draws: full metal reflects a sky it has
not and draws black).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import json
import struct
from pathlib import Path

import numpy

#  Where the model is kept (gitignored), and the part whose axle is the
#  engine's origin.
MODEL = Path(__file__).parent / 'models' / 'locomotive.glb'
MAIN_PART = 'driver_2'
#  The most metalness a look is given (the sandbox draws steel at 0.3).
METAL_MOST = 0.3
#  glTF's component types: numpy's for each.
_KINDS = {5126: numpy.float32, 5125: numpy.uint32, 5123: numpy.uint16,
          5121: numpy.uint8}
_WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def _matrixOf(node: dict) -> numpy.ndarray:
  """Returns a glTF node's own placing as a 4 x 4 matrix (its 'matrix',
  or its translation, rotation (x, y, z, w) and scale)."""
  if 'matrix' in node:
    return numpy.array(node['matrix'], numpy.float64).reshape(4, 4).T
  x, y, z, w = node.get('rotation', (0.0, 0.0, 0.0, 1.0))
  turn = numpy.array((
    (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
    (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
    (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y))))
  out = numpy.eye(4)
  out[:3, :3] = turn * numpy.array(node.get('scale', (1.0, 1.0, 1.0)))
  out[:3, 3] = node.get('translation', (0.0, 0.0, 0.0))
  return out


def _accessed(doc: dict, binary: bytes, index: int) -> numpy.ndarray:
  """Returns accessor 'index' of the glTF 'doc' read from 'binary' (its
  buffer), as an array of its rows."""
  accessor = doc['accessors'][index]
  view = doc['bufferViews'][accessor['bufferView']]
  kind = numpy.dtype(_KINDS[accessor['componentType']])
  width = _WIDTHS[accessor['type']]
  start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
  stride = view.get('byteStride', kind.itemsize * width)
  count = accessor['count']
  if stride == kind.itemsize * width:
    values = numpy.frombuffer(binary, kind, count * width, start)
    return values.reshape(count, width) if width > 1 else values.copy()
  rows = numpy.empty((count, width), kind)
  for k in range(count):
    rows[k] = numpy.frombuffer(binary, kind, width, start + k * stride)
  return rows


def _lookOf(material: dict) -> tuple:
  """Returns a glTF material as a look: its colour (0-255, from linear
  to the screen's), its metalness (at most 'METAL_MOST'), its
  roughness."""
  pbr = material.get('pbrMetallicRoughness', {})
  linear = numpy.array(pbr.get('baseColorFactor', (1.0, 1.0, 1.0))[:3])
  shown = numpy.where(linear <= 0.0031308, 12.92 * linear,
                      1.055 * numpy.power(linear, 1.0 / 2.4) - 0.055)
  rgb = tuple(int(round(255.0 * float(c))) for c in numpy.clip(shown, 0, 1))
  return (rgb, min(METAL_MOST, float(pbr.get('metallicFactor', 1.0))),
          float(pbr.get('roughnessFactor', 1.0)))


@functools.lru_cache(maxsize=None)
def modelParts(path: Path = MODEL) -> tuple:
  """The 'modelParts' function returns the model at 'path' (made once): a
  dict of its named parts (the layout's children), each a list of meshes
  (places (n, 3) and normals (n, 3) in the engine's own frame, indices
  (m,), the look's name), and its looks ({name: look}, each material
  'model <name>')."""
  data = Path(path).read_bytes()
  length, _ = struct.unpack_from('<I4s', data, 12)
  doc = json.loads(data[20:20 + length])
  rest = 20 + length
  size, _ = struct.unpack_from('<I4s', data, rest)
  binary = data[rest + 8:rest + 8 + size]
  nodes = doc['nodes']
  placed, parents = {}, {}
  stack = [(index, numpy.eye(4), None) for index in doc['scenes'][0][
    'nodes']]
  while stack:
    index, above, part = stack.pop()
    node = nodes[index]
    matrix = above @ _matrixOf(node)
    placed[index] = matrix
    named = node.get('name', '')
    if part is None and nodes[index].get('name', '').endswith('_layout'):
      children = [(child, matrix, nodes[child].get('name', ''))
                  for child in node.get('children', ())]
    else:
      children = [(child, matrix, part) for child in node.get('children',
                                                               ())]
    parents[index] = part if part is not None else named
    stack.extend(children)
  main = next(index for index, node in enumerate(nodes)
              if node.get('name') == MAIN_PART)
  origin = placed[main][:3, 3]
  looks = {}
  for material in doc.get('materials', ()):
    looks['model %s' % material.get('name', '')] = _lookOf(material)
  parts = {}
  for index, node in enumerate(nodes):
    if 'mesh' not in node or index not in placed:
      continue
    matrix = placed[index]
    turn = matrix[:3, :3]
    for primitive in doc['meshes'][node['mesh']]['primitives']:
      attributes = primitive['attributes']
      places = _accessed(doc, binary, attributes['POSITION']).astype(
        numpy.float64)
      normals = _accessed(doc, binary, attributes['NORMAL']).astype(
        numpy.float64)
      indices = _accessed(doc, binary, primitive['indices']).astype(
        numpy.uint32).ravel()
      places = places @ turn.T + matrix[:3, 3] - origin
      normals = normals @ turn.T
      normals /= numpy.maximum(numpy.linalg.norm(normals, axis=1,
                                                 keepdims=True), 1e-12)
      material = doc['materials'][primitive['material']].get('name', '')
      parts.setdefault(parents[index], []).append((
        places[:, (2, 0, 1)] + numpy.array((0.0, 0.0, origin[1])),
        normals[:, (2, 0, 1)], indices, 'model %s' % material))
  return parts, looks


def carvedOut(meshes: list, ends: tuple, half: float, floor: tuple,
              high: float) -> list:
  """The 'carvedOut' function returns the model's 'meshes' (a part's: a
  list of (places, normals, indices, look), in the engine's frame) with
  a passage cut through them (user, 2026-11-16: walk from the engine
  back through the train; the tender's corridor): along x from 'ends'
  (from, to, m), 'half' m either side of the middle, from its floor (a
  slope: 'floor' its height at the passage's two ends) 'high' m up.
  What lies in it goes; a triangle across its side is cut along it
  (its places and normals taken along its edges)."""
  x0, x1 = ends
  slope = (floor[1] - floor[0]) / (x1 - x0)
  base = floor[0] - slope * x0
  bounds = ((numpy.array((-1.0, 0.0, 0.0)), -x0),
            (numpy.array((1.0, 0.0, 0.0)), x1),
            (numpy.array((0.0, -1.0, 0.0)), half),
            (numpy.array((0.0, 1.0, 0.0)), half),
            (numpy.array((slope, 0.0, -1.0)), -base),
            (numpy.array((-slope, 0.0, 1.0)), base + high))
  outside = [((-1.0 * normal, -offset),) + tuple(bounds[:k])
             for k, (normal, offset) in enumerate(bounds)]
  out = []
  for places, normals, indices, look in meshes:
    triangles = indices.reshape(-1, 3)
    corners = places[triangles]
    sides = numpy.stack([corners @ normal - offset
                         for normal, offset in bounds], -1)
    within = (sides < 0.0).all(-1)
    clear = (sides >= 0.0).all(1).any(-1)
    kept = triangles[clear]
    cut = numpy.flatnonzero(~clear & ~within.all(1))
    rows, extra = [], []
    for t in cut:
      polygon = [(places[i], normals[i]) for i in triangles[t]]
      for region in outside:
        piece = polygon
        for normal, offset in region:
          piece = _clipped(piece, normal, offset)
          if len(piece) < 3:
            break
        for k in range(1, len(piece) - 1):
          extra.append((piece[0], piece[k], piece[k + 1]))
    allPlaces, allNormals = [places], [normals]
    newIndices = [kept.ravel().astype(numpy.uint32)]
    at = len(places)
    for triangle in extra:
      allPlaces.append(numpy.array([p for p, _ in triangle]))
      allNormals.append(numpy.array([n for _, n in triangle]))
      newIndices.append(numpy.arange(at, at + 3, dtype=numpy.uint32))
      at += 3
    turned = numpy.vstack(allNormals)
    turned /= numpy.maximum(numpy.linalg.norm(turned, axis=1,
                                              keepdims=True), 1e-12)
    out.append((numpy.vstack(allPlaces), turned,
                numpy.concatenate(newIndices), look))
  return out


def _clipped(polygon: list, normal: numpy.ndarray, offset: float) -> list:
  """Returns 'polygon' (corners: (place, normal)) clipped to the half
  space where 'normal' . place - 'offset' is at most nought, an edge
  crossing its plane cut where it crosses (Sutherland-Hodgman)."""
  out = []
  for k, (place, turned) in enumerate(polygon):
    after, afterTurned = polygon[(k + 1) % len(polygon)]
    here = float(place @ normal) - offset
    there = float(after @ normal) - offset
    if here <= 0.0:
      out.append((place, turned))
    if (here < 0.0 < there) or (there < 0.0 < here):
      t = here / (here - there)
      out.append((place + t * (after - place),
                  turned + t * (afterTurned - turned)))
  return out
