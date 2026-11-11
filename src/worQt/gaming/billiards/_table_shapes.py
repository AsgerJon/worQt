"""
The shapes of a three-cushion table's woodwork and cushions as
triangles, needing no Qt: 'prismMesh' extrudes a cross-section, and
'tableMeshes' gives every piece of a 'CaromTable' so, after the tables
of Søren Søgaard: sloped cushions, rails with a rounded outer edge,
square corner blocks rounded outside, the body, two tapered pedestals,
the diamonds inlaid in the rails. 'kegleMeshes' gives keglebillard's:
the cushions with straight slots cut over the pockets drilled into the
table, and the black leather behind them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._carom_table import CaromTable
  from ._kegle_table import KegleTable

RAIL_DEPTH = 100.0  # a rail from its top down
BULLNOSE = 40.0  # the rounding of a rail's outer edge
CORNER_ROUND = 45.0  # the rounding of a corner block, seen from above
GAP = 2.0  # between a rail and a corner block
APRON_INSET = 8.0  # the body's sides, in from the rails' outer edges
UNDERCUT = 6.0  # a cushion's face, back from the nose at the cloth
APRON_DEPTH = 330.0  # the body under the rails, from the cloth down
#  A pedestal: half as long as it is at the top, and at the floor, and
#  how wide it is across the table.
PEDESTAL = (330.0, 230.0, 1000.0)
#  A diamond inlaid in a rail's top: how long it is along the rail, how
#  wide across it, and how thick.
DIAMOND = (34.0, 18.0, 2.0)


def arcPoints(centre: tuple[float, float], radius: float,
              start: float, stop: float, count: int) -> list:
  """The 'arcPoints' function returns 'count' + 1 points on the arc
  about 'centre' of 'radius' from 'start' to 'stop' degrees."""
  out = []
  for k in range(count + 1):
    angle = math.radians(start + (stop - start) * k / count)
    out.append((centre[0] + radius * math.cos(angle),
                centre[1] + radius * math.sin(angle)))
  return out


def prismMesh(profile: list, length: float, mitre: bool,
              smooth: float) -> numpy.ndarray:
  """The 'prismMesh' function returns the triangles of 'profile', a
  convex cross-section given counter-clockwise as points 'a' 'b',
  extruded 'length' along z about nought: a row a corner, its place
  then its normal, three rows a triangle, each counter-clockwise seen
  from outside. 'mitre' cuts the ends at 45 degrees, a point 'a' out
  reaching 'a' further, as cushions meet in a corner. Neighbouring
  sides turning less than 'smooth' degrees share their normals at the
  corner between them, so a rounded edge looks round."""
  points = numpy.array(profile, numpy.float64)
  count = points.shape[0]
  edges = numpy.roll(points, -1, 0) - points
  normals = numpy.stack((edges[:, 1], -edges[:, 0]), 1)
  normals /= numpy.linalg.norm(normals, None, 1)[:, None]
  starts, ends = normals.copy(), normals.copy()
  limit = math.cos(math.radians(smooth))
  for k in range(count):
    before = normals[k - 1]
    if float(before @ normals[k]) > limit:
      shared = before + normals[k]
      shared /= numpy.linalg.norm(shared)
      starts[k] = shared
      ends[k - 1] = shared
  share = 1.0 if mitre else 0.0
  high = 0.5 * length + share * points[:, 0]
  rows = []
  for k in range(count):
    j = (k + 1) % count
    p, q = points[k], points[j]
    s = (starts[k][0], starts[k][1], 0.0)
    e = (ends[k][0], ends[k][1], 0.0)
    p0 = (p[0], p[1], -high[k], *s)
    q0 = (q[0], q[1], -high[j], *e)
    q1 = (q[0], q[1], high[j], *e)
    p1 = (p[0], p[1], high[k], *s)
    rows += [p0, q0, q1, p0, q1, p1]
  rows += _cap(points, high, 1.0)
  rows += _cap(points, high, -1.0)
  return numpy.array(rows, numpy.float32)


def _cap(points: numpy.ndarray, high: numpy.ndarray,
         side: float) -> list:
  """Returns the triangles closing the prism's end on 'side', 1 the
  far end, -1 the near, as a fan, with the end's normal."""
  corners = [numpy.array((p[0], p[1], side * h)) for p, h in
             zip(points, high)]
  if side < 0.0:
    corners = [corners[0]] + corners[:0:-1]
  normal = numpy.cross(corners[1] - corners[0], corners[2] - corners[0])
  normal /= numpy.linalg.norm(normal)
  rows = []
  for k in range(1, len(corners) - 1):
    for corner in (corners[0], corners[k], corners[k + 1]):
      rows.append((*corner, *normal))
  return rows


def cushionProfile(table: CaromTable) -> list:
  """The 'cushionProfile' function returns a cushion's cross-section,
  'a' out from its nose, 'b' up from the cloth: the face undercut below
  the nose, the top sloping up from the nose to the rail."""
  return [(UNDERCUT, 0.0), (table.cushion, 0.0),
          (table.cushion, table.top), (0.0, table.nose)]


def railProfile(table: CaromTable) -> list:
  """The 'railProfile' function returns a rail's cross-section, 'a' out
  from its inner edge, 'b' up from the cloth: flat on top, its outer
  edge rounded down to its outer face."""
  width, top = table.rail, table.top
  bottom = top - RAIL_DEPTH
  centre = (width - BULLNOSE, top - BULLNOSE)
  arc = arcPoints(centre, BULLNOSE, 0.0, 90.0, 10)
  return [(0.0, bottom), (width, bottom), *arc, (0.0, top)]


def cornerProfile(table: CaromTable) -> list:
  """The 'cornerProfile' function returns a corner block seen from
  above, about its middle: a square a rail wide less the gaps, its
  outer corner, 'a' and 'b' both out, rounded."""
  half = 0.5 * table.rail - GAP
  centre = (half - CORNER_ROUND, half - CORNER_ROUND)
  arc = arcPoints(centre, CORNER_ROUND, 0.0, 90.0, 12)
  return [(-half, -half), (half, -half), *arc, (-half, half)]


def pedestalProfile(table: CaromTable) -> list:
  """The 'pedestalProfile' function returns a pedestal's side, 'a'
  along the table about its middle, 'b' up from the floor: wider at the
  top, under the body, than at the floor."""
  top, bottom, _ = PEDESTAL
  height = table.bed - APRON_DEPTH
  return [(-bottom, 0.0), (bottom, 0.0), (top, height), (-top, height)]


def apronProfile(table: CaromTable) -> list:
  """The 'apronProfile' function returns the body under the rails
  across, about the middle, 'b' up from the cloth: from the rails'
  undersides down 'APRON_DEPTH' below the cloth, its sides in a little
  from the rails' outer edges."""
  half = 0.5 * table.width + table.cushion + table.rail - APRON_INSET
  top = table.top - RAIL_DEPTH
  return [(-half, -APRON_DEPTH), (half, -APRON_DEPTH), (half, top),
          (-half, top)]


def diamondMesh(long: float, wide: float, high: float) -> numpy.ndarray:
  """The 'diamondMesh' function returns the triangles of a diamond as
  'prismMesh' makes them: a rhombus 'long' along z and 'wide' along x,
  'high' thick along y about nought, its edges sharp."""
  profile = [(0.0, -0.5 * long), (0.5 * wide, 0.0), (0.0, 0.5 * long),
             (-0.5 * wide, 0.0)]
  mesh = prismMesh(profile, high, False, 0.0)
  #  Turned a quarter about x, the cross-section lies flat and the
  #  length stands up: y is the old -z, z the old y.
  out = mesh.copy()
  out[:, 1], out[:, 2] = -mesh[:, 2], mesh[:, 1]
  out[:, 4], out[:, 5] = -mesh[:, 5], mesh[:, 4]
  return out


#  The cue drawn while a stroke is made, (along it from the tip, radius)
#  in mm: the blue tip, the white ferrule, the maple shaft swelling to
#  the joint, the ebony butt.
CUE_TIP = ((0.0, 6.5), (10.0, 6.5))
CUE_FERRULE = ((10.0, 6.5), (30.0, 6.5))
CUE_SHAFT = ((30.0, 6.6), (720.0, 11.0))
CUE_BUTT = ((720.0, 11.0), (1440.0, 15.0), (1450.0, 0.0))


def latheMesh(profile: tuple, segments: int) -> numpy.ndarray:
  """The 'latheMesh' function returns the triangles of a solid of
  revolution as 'prismMesh' makes them: 'profile', its outline as
  (height, radius) from the foot up, turned round the y axis in
  'segments' steps, its sides smooth, standing on a flat foot facing
  down; a keglebillard pin's 'KeglePin.profile'."""
  heights = [float(h) for h, _ in profile]
  radii = [float(r) for _, r in profile]
  count = len(profile)
  normals = []
  for k in range(count):
    low, high = max(k - 1, 0), min(k + 1, count - 1)
    if k == 0:
      low = 0
    dr, dh = radii[high] - radii[low], heights[high] - heights[low]
    size = math.hypot(dr, dh) or 1.0
    normals.append((dh / size, -dr / size))
  turns = [2.0 * math.pi * i / segments for i in range(segments + 1)]
  rows = []

  def corner(k: int, angle: float) -> tuple:
    c, s = math.cos(angle), math.sin(angle)
    nr, nh = normals[k]
    return (radii[k] * c, heights[k], radii[k] * s, nr * c, nh, nr * s)

  for k in range(count - 1):
    for a, b in zip(turns, turns[1:]):
      if radii[k + 1] > 0.0:
        rows += [corner(k, a), corner(k + 1, a), corner(k + 1, b)]
      if radii[k] > 0.0:
        rows += [corner(k, a), corner(k + 1, b), corner(k, b)]
  foot = radii[0]
  for a, b in zip(turns, turns[1:]):
    rows += [(0.0, heights[0], 0.0, 0.0, -1.0, 0.0),
             (foot * math.cos(a), heights[0], foot * math.sin(a), 0.0,
              -1.0, 0.0),
             (foot * math.cos(b), heights[0], foot * math.sin(b), 0.0,
              -1.0, 0.0)]
  return numpy.array(rows, numpy.float32)


def notchedPrism(profile: list, pieces: list,
                 smooth: float) -> numpy.ndarray:
  """The 'notchedPrism' function returns the triangles of 'profile', as
  'prismMesh' extrudes it, in 'pieces', each from 'z' to 'z' along, cut
  square at both ends: a cushion with straight slots cut over pockets
  between the pieces (the user, after a keglebillard table's photo:
  the cushions are cut out straight above the pockets)."""
  points = numpy.array(profile, numpy.float64)
  starts, ends = _edgeNormals(points, smooth)
  count = points.shape[0]
  rows = []
  for first, second in pieces:
    low = numpy.full(count, float(first))
    high = numpy.full(count, float(second))
    for k in range(count):
      j = (k + 1) % count
      p, q = points[k], points[j]
      s = (starts[k][0], starts[k][1], 0.0)
      e = (ends[k][0], ends[k][1], 0.0)
      p0 = (p[0], p[1], low[k], *s)
      q0 = (q[0], q[1], low[j], *e)
      q1 = (q[0], q[1], high[j], *e)
      p1 = (p[0], p[1], high[k], *s)
      rows += [p0, q0, q1, p0, q1, p1]
    rows += _fanCap(points, low, -1.0)
    rows += _fanCap(points, high, 1.0)
  return numpy.array(rows, numpy.float32)


def pocketLeather(kegle: KegleTable) -> numpy.ndarray:
  """The 'pocketLeather' function returns the triangles of the black
  leather behind each pocket of 'kegle' (the user): a flat panel on the
  back of each slot cut in the cushions, where the rail begins, from the
  cloth up to the rail's top, facing the table: one behind each middle
  pocket, two meeting behind each corner pocket. In the scene's axes,
  mm, y up, the cloth's middle at nought, the head at negative z, as the
  3D view has the table."""
  carom = kegle.table
  width, length = carom.width, carom.length
  depth, top = carom.cushion, carom.top
  pockets = kegle.pockets()
  half, reach = pockets.half, pockets.corner
  rows = []

  def panel(x0: float, y0: float, x1: float, y1: float, nx: float,
            ny: float) -> None:
    corners = [(x0, y0, 0.0), (x1, y1, 0.0), (x1, y1, top),
               (x0, y0, top)]
    scene = [(x - 0.5 * width, z, 0.5 * length - y, nx, 0.0, -ny)
             for x, y, z in corners]
    rows.extend(_facing([scene[0], scene[1], scene[2]]))
    rows.extend(_facing([scene[0], scene[2], scene[3]]))

  middle = 0.5 * length
  panel(-depth, middle - half, -depth, middle + half, 1.0, 0.0)
  panel(width + depth, middle - half, width + depth, middle + half,
        -1.0, 0.0)
  for sx, sy in ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)):
    cx = 0.0 if sx < 0.0 else width
    cy = 0.0 if sy < 0.0 else length
    panel(cx + sx * depth, cy + sy * depth, cx + sx * depth,
          cy - sy * reach, -sx, 0.0)
    panel(cx + sx * depth, cy + sy * depth, cx - sx * reach,
          cy + sy * depth, 0.0, -sy)
  return numpy.array(rows, numpy.float32)


def kegleMeshes(kegle: KegleTable) -> dict:
  """The 'kegleMeshes' function returns keglebillard's pieces by name:
  the long and short cushions with straight slots cut over the pockets
  drilled into the table (the user: the cushions are cut out above the
  pockets), at the corners and the long cushions' middles, and the black
  leather on the slots' backs."""
  carom = kegle.table
  profile = cushionProfile(carom)
  pockets = kegle.pockets()
  ends = 0.5 * carom.length - pockets.corner
  across = 0.5 * carom.width - pockets.corner
  return {
    'cushionLongNotched': notchedPrism(
      profile, [(-ends, -pockets.half), (pockets.half, ends)], 30.0),
    'cushionShortNotched': notchedPrism(profile, [(-across, across)],
                                        30.0),
    'pocketLeather': pocketLeather(kegle),
  }


def _edgeNormals(points: numpy.ndarray,
                 smooth: float) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Returns the normals each side of 'points', an outline, has at its
  start and at its end, as 'prismMesh' has them: neighbouring sides
  turning less than 'smooth' degrees sharing theirs."""
  edges = numpy.roll(points, -1, 0) - points
  normals = numpy.stack((edges[:, 1], -edges[:, 0]), 1)
  normals /= numpy.linalg.norm(normals, None, 1)[:, None]
  starts, ends = normals.copy(), normals.copy()
  limit = math.cos(math.radians(smooth))
  for k in range(points.shape[0]):
    before = normals[k - 1]
    if float(before @ normals[k]) > limit:
      shared = before + normals[k]
      shared /= numpy.linalg.norm(shared)
      starts[k] = shared
      ends[k - 1] = shared
  return starts, ends


def _fanCap(points: numpy.ndarray, zs: numpy.ndarray,
            side: float) -> list:
  """Returns the triangles closing a notched piece's end, the outline
  'points' each at its own 'zs', as a fan facing out along z, 'side' 1
  the far end, -1 the near; triangles too thin to face anywhere left
  out."""
  corners = [numpy.array((p[0], p[1], z)) for p, z in zip(points, zs)]
  rows = []
  for k in range(1, len(corners) - 1):
    a, b, c = corners[0], corners[k], corners[k + 1]
    normal = numpy.cross(b - a, c - a)
    size = float(numpy.linalg.norm(normal))
    if size < 1e-9:
      continue
    if normal[2] * side < 0.0:
      b, c, normal = c, b, -normal
    normal = normal / size
    for corner in (a, b, c):
      rows.append((*corner, *normal))
  return rows


def _facing(corners: list) -> list:
  """Returns the triangle 'corners', each (place, normal), wound to turn
  the way their normals point."""
  a, b, c = (numpy.array(corner[:3]) for corner in corners)
  normal = numpy.array(corners[0][3:])
  if float(numpy.cross(b - a, c - a) @ normal) < 0.0:
    corners = [corners[0], corners[2], corners[1]]
  return list(corners)


def tableMeshes(table: CaromTable) -> dict:
  """The 'tableMeshes' function returns the triangles of each kind of
  piece of 'table', by name: the long and short cushions, mitred; the
  long and short rails, between the corner blocks; a corner block,
  standing up its rail's depth; the body, along the table; a pedestal,
  across it; and a diamond, inlaid in a rail's top."""
  cushion, rail = cushionProfile(table), railProfile(table)
  long = table.length + 2.0 * table.cushion - 2.0 * GAP
  short = table.width + 2.0 * table.cushion - 2.0 * GAP
  body = table.length + 2.0 * (table.cushion + table.rail - APRON_INSET)
  return {
    'apron': prismMesh(apronProfile(table), body, False, 30.0),
    'cushionLong': prismMesh(cushion, table.length, True, 30.0),
    'cushionShort': prismMesh(cushion, table.width, True, 30.0),
    'railLong': prismMesh(rail, long, False, 30.0),
    'railShort': prismMesh(rail, short, False, 30.0),
    'corner': prismMesh(cornerProfile(table), RAIL_DEPTH, False, 30.0),
    'pedestal': prismMesh(pedestalProfile(table), PEDESTAL[2], False,
                          30.0),
    'diamond': diamondMesh(*DIAMOND),
  }
