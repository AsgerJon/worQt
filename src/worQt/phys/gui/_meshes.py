"""
The meshes a GPU view draws the lab's bodies with, Qt-free: each body's
shape as triangles in the scene's units (cm, y up), about its centre of
mass, so a model placed at the body's centre and turned as it is draws
it; a turned solid split by a radius (a wheel's steel and its tyre's
rubber); a body's pieces one by one; parts drawn in the world as they
are (quads, as 'CarDress' makes them); the ground, a terrain's shape
as a grid and the flat ground about it, mapped for a checker.

The world is in metres with z up; the scene in centimetres with y up:
a world point (x, y, z) is the scene's 100 (x, z, -y), a turn, not a
mirror ('sceneOf', 'sceneTurnOf').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from .._shape import Shape, Sphere
from .._turned import _ARC_DRAWN, Turned

#  How many of the scene's units make a metre.
SCALE = 100.0
#  How many sides round a run of a profile is drawn with on a body that
#  is not a turned solid ('finishedRows').
DRAWN_SIDES = 96
#  The world's axes in the scene's: scene = AXES @ world.
AXES = numpy.array(((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0)))


def sceneOf(point: tuple) -> tuple[float, float, float]:
  """The 'sceneOf' function returns the world's 'point' (m, z up) in the
  scene (cm, y up)."""
  return SCALE * point[0], SCALE * point[2], -SCALE * point[1]


def sceneTurnOf(turn: tuple) -> tuple[float, float, float, float]:
  """The 'sceneTurnOf' function returns the world's 'turn' (w, x, y, z)
  as the scene's: its axis taken as a vector is (the turn's angle
  kept)."""
  return turn[0], turn[1], turn[3], -turn[2]


def bodyRows(body: object, band: float | None) -> tuple:
  """The 'bodyRows' function returns 'body''s shape as the scene draws
  it: triangles, a row a corner of its place (cm, about the body's
  centre of mass, along the scene's axes as the body's own frame lies
  unturned) and its normal; for a turned solid with a 'band' radius,
  two such meshes, what lies inside it and what lies out (the steel
  and the rubber of a wheel); else one, with an empty second."""
  shape = body.shape
  if isinstance(shape, Turned):
    inside, outside = _turnedRows(shape, band)
  elif isinstance(shape, Sphere):
    inside, outside = _sphereRows(shape.radius), numpy.zeros((0, 6))
  else:
    inside, outside = _shapeRows(shape), numpy.zeros((0, 6))
  centre = numpy.array(body.centre)
  return _toScene(inside, centre), _toScene(outside, centre)


def _toScene(rows: numpy.ndarray, centre: numpy.ndarray) -> numpy.ndarray:
  """Returns 'rows' (places and normals in a body's own frame, m, and
  any more numbers a row, kept as they are) about 'centre', in the
  scene's units and axes."""
  out = numpy.empty((len(rows), max(6, rows.shape[1])), numpy.float32)
  if len(rows):
    out[:, :3] = SCALE * (rows[:, :3] - centre) @ AXES.T
    out[:, 3:6] = rows[:, 3:6] @ AXES.T
    out[:, 6:] = rows[:, 6:]
  return out


def finishedRows(body: object, finish: object, tile: float) -> dict:
  """The 'finishedRows' function returns 'body' drawn in its 'finish',
  by key: a key alone (a str), the whole body in it, as 'bodyRows'
  draws it; else runs ((key, item), ...), each item a run of a turned
  profile (a chain of lines and arcs in the body's own frame about its
  z axis, walked as a profile is, the solid on its left) turned round
  in the body's 'sides' (a turned solid's; else 'DRAWN_SIDES'), smooth
  shaded as 'Turned.normals' has it, its picture's coordinates round
  it in whole repeats about 'tile' m apart and along it by its length
  over 'tile' (a picture a 'tile' square, near enough); or a label
  laid on such a run, ('label', repeats, run): its picture 'repeats'
  times round and once across the run ('_labelRows': a tyre's
  lettering); ('rows', rows): rows made already (in the body's own
  frame, each its place, normal and picture: a steering wheel's rim);
  or a 'Shape' (in the body's own frame) drawn as it is, flat, mapped
  to nothing; rows of eight: place, normal, picture."""
  centre = numpy.array(body.centre)
  if isinstance(finish, str):
    return {finish: bodyRows(body, None)[0]}
  sides = body.shape.sides if isinstance(body.shape, Turned) else (
    DRAWN_SIDES)
  out = {}
  for key, item in finish:
    if isinstance(item, Shape):
      flat = _shapeRows(item)
      rows = _toScene(numpy.concatenate(
        (flat, numpy.zeros((len(flat), 2))), axis=1), centre)
    elif item[0] == 'label':
      rows = _toScene(_labelRows(item[2], sides, item[1]), centre)
    elif item[0] == 'rows':
      rows = _toScene(item[1], centre)
    else:
      rows = _toScene(_runRows(item, sides, tile), centre)
    out[key] = rows if key not in out else numpy.concatenate(
      (out[key], rows))
  return out


def _runRows(pieces: tuple, sides: int, tile: float) -> numpy.ndarray:
  """Returns a run of a profile's 'pieces' turned round in 'sides' as
  'finishedRows' draws it, in the solid's own frame (m)."""
  rows, middle = _runQuads(pieces, sides)
  repeats = max(1, round(2.0 * math.pi * middle / tile))
  rows[:, 6] *= repeats
  rows[:, 7] /= tile
  return rows


def _labelRows(pieces: tuple, sides: int, repeats: int) -> numpy.ndarray:
  """Returns a run of a profile's 'pieces' turned round in 'sides' with
  a label laid on it ('finishedRows'): its picture 'repeats' times round
  and once across, upright (its top toward the run's end farther from
  the axis: the picture's second way runs from its foot up) and reading
  clockwise as seen from the side the run faces (a run facing up its
  axis is seen with the turning anticlockwise, so its picture runs
  back), in the solid's own frame (m)."""
  rows, _ = _runQuads(pieces, sides)
  across = rows[:, 7] / rows[:, 7].max()
  rho = numpy.hypot(rows[:, 0], rows[:, 1])
  if rho[across == 1.0].mean() < rho[across == 0.0].mean():
    across = 1.0 - across
  around = rows[:, 6]
  if rows[:, 5].mean() > 0.0:
    around = 1.0 - around
  rows[:, 6], rows[:, 7] = repeats * around, across
  return rows


def _runQuads(pieces: tuple, sides: int) -> tuple:
  """Returns a run of a profile's 'pieces' turned round in 'sides', as
  triangles (rows of eight: place, normal, how far round, 0 to 1, how
  far along the run, m), and its middle's distance from the axis, by its
  length."""
  starts, ends, startNormals, endNormals = [], [], [], []
  for piece in pieces:
    if piece[0] == 'line':
      (r0, w0), (r1, w1) = piece[1], piece[2]
      size = math.hypot(r1 - r0, w1 - w0)
      normal = ((w1 - w0) / size, -(r1 - r0) / size)
      starts.append((r0, w0))
      ends.append((r1, w1))
      startNormals.append(normal)
      endNormals.append(normal)
      continue
    (cr, cw), radius, a0, a1 = piece[1], piece[2], piece[3], piece[4]
    way = 1.0 if a1 > a0 else -1.0
    for k in range(_ARC_DRAWN):
      for angle, there, normals in (
          (a0 + (a1 - a0) * k / _ARC_DRAWN, starts, startNormals),
          (a0 + (a1 - a0) * (k + 1) / _ARC_DRAWN, ends, endNormals)):
        c, s = math.cos(angle), math.sin(angle)
        there.append((cr + radius * c, cw + radius * s))
        normals.append((way * c, way * s))
  starts, ends = numpy.array(starts), numpy.array(ends)
  startNormals, endNormals = numpy.array(startNormals), numpy.array(
    endNormals)
  lengths = numpy.linalg.norm(ends - starts, axis=1)
  along = numpy.concatenate(([0.0], numpy.cumsum(lengths)))
  rho = 0.5 * (starts[:, 0] + ends[:, 0])
  middle = float((rho * lengths).sum() / lengths.sum())
  angles = 2.0 * math.pi * numpy.arange(sides + 1) / sides
  cos, sin = numpy.cos(angles), numpy.sin(angles)
  quads = numpy.empty((sides, len(starts), 4, 8))
  for corner, side, there, normals, at in (
      (0, 0, starts, startNormals, along[:-1]),
      (1, 1, starts, startNormals, along[:-1]),
      (2, 1, ends, endNormals, along[1:]),
      (3, 0, ends, endNormals, along[1:])):
    c = cos[side:side + sides, None]
    s = sin[side:side + sides, None]
    quad = quads[:, :, corner]
    quad[..., 0], quad[..., 1] = there[:, 0] * c, there[:, 0] * s
    quad[..., 2] = there[:, 1]
    quad[..., 3], quad[..., 4] = normals[:, 0] * c, normals[:, 0] * s
    quad[..., 5] = normals[:, 1]
    quad[..., 6] = ((numpy.arange(sides) + side) / sides)[:, None]
    quad[..., 7] = at
  return quads[:, :, (0, 1, 3, 1, 2, 3)].reshape(-1, 8), middle


def _shapeRows(shape: object) -> numpy.ndarray:
  """Returns a shape's triangles, each corner its place and its face's
  normal (flat), in its own frame."""
  points = numpy.array(shape.points, numpy.float64)
  faces = numpy.array(shape.faces, numpy.int64)
  a, b, c = points[faces[:, 0]], points[faces[:, 1]], points[faces[:, 2]]
  normals = numpy.cross(b - a, c - a)
  sizes = numpy.linalg.norm(normals, axis=1, keepdims=True)
  normals = normals / numpy.where(sizes > 0.0, sizes, 1.0)
  rows = numpy.empty((len(faces), 3, 6))
  for k, corner in enumerate((a, b, c)):
    rows[:, k, :3], rows[:, k, 3:] = corner, normals
  return rows.reshape(-1, 6)


def _turnedRows(shape: Turned, band: float | None) -> tuple:
  """Returns a turned solid's quads as triangles with the true surface's
  normals at their corners (smooth), split into those lying wholly
  'band' or more from its axis and the rest (all the rest, with no
  band)."""
  points = numpy.array(shape.mesh().points, numpy.float64)
  quads = numpy.array(shape.quads(), numpy.int64)
  normals = numpy.array(shape.normals(), numpy.float64)
  corners = points[quads]
  out = numpy.zeros(len(quads), bool)
  if band is not None:
    reach = numpy.hypot(corners[:, :, 0], corners[:, :, 1]).min(axis=1)
    out = reach >= band - 1e-9
  rows = numpy.empty((len(quads), 6, 6))
  for k, corner in enumerate((0, 1, 3, 1, 2, 3)):
    rows[:, k, :3] = corners[:, corner]
    rows[:, k, 3:] = normals[:, corner]
  return rows[~out].reshape(-1, 6), rows[out].reshape(-1, 6)


def stripedRows(body: object, stripes: int, pitch: float) -> tuple:
  """The 'stripedRows' function returns a turned body's shape as
  'bodyRows' does, but in two meshes: its paint's spiral stripes and
  the rest (a cement truck's drum: user, 2026-11-13, "put some texture
  or whatevs on the shaft so it's rotation is clearly visible", then
  "less blocky"). The stripes are 'stripes' helices, each half its
  share of the way round, climbing 'pitch' m a turn along the axis;
  each quad is cut along their edges, which are straight on its flat
  face (the helix's phase is straight in the angle and the height), so
  they run smooth, not in steps, smooth-shaded as the quad is."""
  shape = body.shape
  points = numpy.array(shape.mesh().points, numpy.float64)
  quads = numpy.array(shape.quads(), numpy.int64)
  normals = numpy.array(shape.normals(), numpy.float64)
  plain, striped = [], []
  for quad, normal in zip(points[quads], normals):
    angles = numpy.arctan2(quad[:, 1], quad[:, 0])
    angles = angles[0] + (angles - angles[0] + math.pi) % (
      2.0 * math.pi) - math.pi
    phases = 2.0 * stripes * (angles / (2.0 * math.pi) - quad[:, 2] / pitch)
    pieces = [[(0.0, 0.0, phases[0]), (1.0, 0.0, phases[1]),
               (1.0, 1.0, phases[2]), (0.0, 1.0, phases[3])]]
    for edge in range(int(math.floor(phases.min())) + 1,
                      int(math.ceil(phases.max()))):
      pieces = [part for piece in pieces
                for part in _cutAt(piece, float(edge)) if len(part) > 2]
    for piece in pieces:
      middle = sum(corner[2] for corner in piece) / len(piece)
      rows = _fanRows(piece, quad, normal)
      (striped if math.floor(middle) % 2 == 0 else plain).append(rows)
  centre = numpy.array(body.centre)
  return tuple(_toScene(numpy.concatenate(rows) if rows else
                        numpy.zeros((0, 6)), centre)
               for rows in (plain, striped))


def _cutAt(piece: list, edge: float) -> list[list]:
  """Returns 'piece' (corners (s, t, phase) round a convex polygon in a
  quad's own s across and t along) cut where its phase is 'edge': the
  part under it and the part over it."""
  under, over = [], []
  for k, one in enumerate(piece):
    two = piece[(k + 1) % len(piece)]
    if one[2] <= edge:
      under.append(one)
    if one[2] >= edge:
      over.append(one)
    if (one[2] - edge) * (two[2] - edge) < 0.0:
      share = (edge - one[2]) / (two[2] - one[2])
      cut = (one[0] + share * (two[0] - one[0]),
             one[1] + share * (two[1] - one[1]), edge)
      under.append(cut)
      over.append(cut)
  return [under, over]


def _fanRows(piece: list, quad: numpy.ndarray,
             normal: numpy.ndarray) -> numpy.ndarray:
  """Returns a convex polygon in a quad ('piece': corners (s, t, ...),
  s from its first corner toward its second, t toward its fourth) as
  triangles fanned from its first corner, each corner its place and
  normal as the quad's corners give them, bilinearly."""
  def at(s: float, t: float, values: numpy.ndarray) -> numpy.ndarray:
    return ((1.0 - s) * (1.0 - t) * values[0] + s * (1.0 - t) * values[1]
            + s * t * values[2] + (1.0 - s) * t * values[3])
  rows = []
  for k in range(1, len(piece) - 1):
    for corner in (piece[0], piece[k], piece[k + 1]):
      way = at(corner[0], corner[1], normal)
      rows.append(numpy.concatenate((at(corner[0], corner[1], quad),
                                     way / numpy.linalg.norm(way))))
  return numpy.array(rows)


def _sphereRows(radius: float) -> numpy.ndarray:
  """Returns a ball of 'radius' as triangles, smooth, in its own
  frame."""
  rings, sides = 12, 24
  rows = []
  for i in range(rings):
    a0, a1 = math.pi * i / rings, math.pi * (i + 1) / rings
    for j in range(sides):
      b0, b1 = 2.0 * math.pi * j / sides, 2.0 * math.pi * (j + 1) / sides
      quad = [_onBall(a0, b0), _onBall(a1, b0), _onBall(a1, b1),
              _onBall(a0, b1)]
      for k in (0, 1, 2, 0, 2, 3):
        way = quad[k]
        rows.append((radius * way[0], radius * way[1], radius * way[2])
                    + way)
  return numpy.array(rows)


def _onBall(down: float, round_: float) -> tuple[float, float, float]:
  """Returns the unit point 'down' rad from the top, 'round_' round."""
  return (math.sin(down) * math.cos(round_),
          math.sin(down) * math.sin(round_), math.cos(down))


def pieceRows(shape: object, centre: tuple) -> numpy.ndarray:
  """The 'pieceRows' function returns a piece of a body (a solid in the
  body's own frame, 'centre' its centre of mass) as the scene draws it,
  as 'bodyRows' does a body's shape (flat)."""
  return _toScene(_shapeRows(shape), numpy.array(centre))


def quadRows(quads: numpy.ndarray) -> numpy.ndarray:
  """The 'quadRows' function returns quads in the world (n, 4, 6: each
  corner's place, m, and normal) in the scene, a row a corner (place,
  cm, and normal), to be drawn by 'quadIndices'."""
  corners = quads.reshape(-1, 6)
  out = numpy.empty((len(corners), 6), numpy.float32)
  out[:, 0], out[:, 1] = SCALE * corners[:, 0], SCALE * corners[:, 2]
  out[:, 2] = -SCALE * corners[:, 1]
  out[:, 3], out[:, 4], out[:, 5] = (corners[:, 3], corners[:, 5],
                                     -corners[:, 4])
  return out


def quadIndices(count: int) -> numpy.ndarray:
  """The 'quadIndices' function returns the corners of 'count' quads'
  two triangles each, by their rows in 'quadRows'."""
  return (4 * numpy.arange(count, dtype=numpy.uint32)[:, None]
          + numpy.array((0, 1, 2, 0, 2, 3), numpy.uint32)).ravel()


def terrainMesh(terrain: object, tile: float,
                dropped: numpy.ndarray = None) -> tuple:
  """The 'terrainMesh' function returns 'terrain''s shape at its grid's
  points, as the scene draws it: vertices (place, normal, and a
  picture's coordinates, two of 'tile' m squares to one) and the
  triangles' indices (anticlockwise from above), those of the squares
  wholly paved apart from the rest ('Terrain.paved'), those wholly
  asphalt apart again (none, all the rest): (vertices, ground's,
  paved's, asphalt's). The squares whose four corners are all
  'dropped' (a grid of the terrain's shape) are left out (another mesh
  draws there)."""
  heights = numpy.array(terrain.heights, numpy.float64)
  cell, (x0, y0) = terrain.cell, terrain.origin
  nx, ny = heights.shape
  xs = x0 + cell * numpy.arange(nx)
  ys = y0 + cell * numpy.arange(ny)
  gx, gy = numpy.meshgrid(xs, ys, indexing='ij')
  along = numpy.gradient(heights, cell, axis=0)
  across = numpy.gradient(heights, cell, axis=1)
  normals = numpy.stack((-along, -across, numpy.ones_like(heights)), axis=2)
  normals /= numpy.linalg.norm(normals, axis=2)[..., None]
  vertices = numpy.empty((nx, ny, 8), numpy.float32)
  vertices[..., 0], vertices[..., 1] = SCALE * gx, SCALE * heights
  vertices[..., 2] = -SCALE * gy
  vertices[..., 3], vertices[..., 4] = normals[..., 0], normals[..., 2]
  vertices[..., 5] = -normals[..., 1]
  vertices[..., 6], vertices[..., 7] = gx / (2.0 * tile), gy / (2.0 * tile)
  i, j = numpy.meshgrid(numpy.arange(nx - 1), numpy.arange(ny - 1),
                        indexing='ij')
  a = (i * ny + j).ravel()
  b, c, d = a + ny, a + ny + 1, a + 1
  quads = numpy.stack((a, b, c, a, c, d), axis=1).astype(numpy.uint32)
  if dropped is not None:
    kept = ~(dropped[:-1, :-1] & dropped[1:, :-1] & dropped[1:, 1:]
             & dropped[:-1, 1:]).ravel()
    quads = quads[kept]
  none = numpy.zeros(0, numpy.uint32)
  if terrain.paved is None:
    return vertices.reshape(-1, 8), quads.ravel(), none, none
  kinds = numpy.array(terrain.paved, numpy.int8)
  corners = (kinds[:-1, :-1], kinds[1:, :-1], kinds[1:, 1:],
             kinds[:-1, 1:])
  paved = numpy.logical_and.reduce([k > 0 for k in corners]).ravel()
  asphalt = numpy.logical_and.reduce([k == 2 for k in corners]).ravel()
  if dropped is not None:
    paved, asphalt = paved[kept], asphalt[kept]
  return (vertices.reshape(-1, 8), quads[~paved].ravel(),
          quads[paved & ~asphalt].ravel(), quads[asphalt].ravel())


#  How thick a drawn oval wall is, m (its face is where the physics
#  has it; it is drawn that thick behind), and how often it is sampled
#  round the oval, m; how tall the blue stripe along the foot of its
#  face is, m (user, 2026-11-13: "a clear stripe of blue at the lower
#  bit of the barrier as found at the actual track ... replacing the
#  white so they don't fight": the face is cut there, blue below, white
#  above, meeting on one edge).
WALL_THICK, WALL_STEP, WALL_STRIPE = 0.4, 2.0, 0.3


def wallMesh(terrain: object, wall: object) -> tuple:
  """The 'wallMesh' function returns an oval's safety barrier 'wall'
  ('OvalWall') standing on 'terrain', as 'terrainMesh' gives a
  terrain's: its face toward the track (the lowest 'WALL_STRIPE' m of
  it apart), its top and its back, a band every 'WALL_STEP' m round,
  'WALL_THICK' thick: (vertices, the white's indices, the stripe's)."""
  from .._terrain import OVAL_LENGTH, ovalAt
  count = int(round(OVAL_LENGTH / WALL_STEP))
  rows, white, blue = [], [], []
  stripe = min(WALL_STRIPE, wall.height)
  for k in range(count + 1):
    along = k * OVAL_LENGTH / count
    x, y, heading = ovalAt(along, wall.out)
    ox, oy = math.sin(heading), -math.cos(heading)
    bx, by = x + WALL_THICK * ox, y + WALL_THICK * oy
    face = terrain.heightAt(x, y)
    back = terrain.heightAt(bx, by)
    u, cut = along / WALL_STEP, stripe / wall.height
    for (px, py, pz), (nx, ny, nz), v in (
            ((x, y, face), (-ox, -oy, 0.0), 0.0),
            ((x, y, face + stripe), (-ox, -oy, 0.0), cut),
            ((x, y, face + stripe), (-ox, -oy, 0.0), cut),
            ((x, y, face + wall.height), (-ox, -oy, 0.0), 1.0),
            ((x, y, face + wall.height), (0.0, 0.0, 1.0), 1.0),
            ((bx, by, back + wall.height), (0.0, 0.0, 1.0), 1.2),
            ((bx, by, back + wall.height), (ox, oy, 0.0), 1.2),
            ((bx, by, back), (ox, oy, 0.0), 2.2)):
      rows.append((SCALE * px, SCALE * pz, -SCALE * py, nx, nz, -ny, u, v))
    if k:
      first, last = 8 * (k - 1), 8 * k
      for strip, into in ((0, blue), (2, white), (4, white), (6, white)):
        a, b = first + strip, first + strip + 1
        c, d = last + strip + 1, last + strip
        into.extend((a, c, d, a, b, c))
  return (numpy.array(rows, numpy.float32),
          numpy.array(white, numpy.uint32), numpy.array(blue, numpy.uint32))


#  The oval's surfaces drawn as their own mesh, following its curves
#  (user, 2026-11-12: "the apron bro... make it smooth rather than this
#  jacked minecraft looking thing": drawn square by square of the
#  terrain's grid, its edges stepped a metre at a time): sampled every
#  'TRACK_STEP' m round; across, a band of ground 'TRACK_MARGIN' m wide
#  either side (the grid's squares stop short of the track under it),
#  the apron in 'TRACK_APRON' strips, the banking and its run-off in
#  'TRACK_BANK'.
TRACK_STEP, TRACK_MARGIN, TRACK_APRON, TRACK_BANK = 1.0, 2.0, 6, 24


def _heightsAt(terrain: object, x: numpy.ndarray,
               y: numpy.ndarray) -> numpy.ndarray:
  """Returns 'terrain''s heights at 'x', 'y' as the physics has them
  (bilinear in its grid's cells; points off the grid at its edge)."""
  grid = numpy.array(terrain.heights, numpy.float64)
  fx = (x - terrain.origin[0]) / terrain.cell
  fy = (y - terrain.origin[1]) / terrain.cell
  i = numpy.clip(numpy.floor(fx).astype(int), 0, grid.shape[0] - 2)
  j = numpy.clip(numpy.floor(fy).astype(int), 0, grid.shape[1] - 2)
  tx, ty = numpy.clip(fx - i, 0.0, 1.0), numpy.clip(fy - j, 0.0, 1.0)
  return ((1.0 - tx) * (1.0 - ty) * grid[i, j] + tx * (1.0 - ty)
          * grid[i + 1, j] + (1.0 - tx) * ty * grid[i, j + 1]
          + tx * ty * grid[i + 1, j + 1])


def ovalTrackMesh(terrain: object, tile: float) -> tuple:
  """The 'ovalTrackMesh' function returns the oval's surfaces on
  'terrain' (as 'oval' makes it) drawn following its curves: vertices
  (as 'terrainMesh''s, the picture's coordinates fixed to the ground
  as the terrain's), and the indices of its ground margins, its
  concrete (the banking and run-off) and its asphalt (the apron), each
  edge a curve, not steps; and which of the terrain's grid points it
  covers (for 'terrainMesh''s 'dropped')."""
  from .._terrain import OVAL_LENGTH, OVAL_RUNOFF, ovalAcross, ovalAt
  from .._terrain import ovalShapeAt
  rows = int(round(OVAL_LENGTH / TRACK_STEP))
  places = []
  for k in range(rows + 1):
    along = k * OVAL_LENGTH / rows
    x, y, heading = ovalAt(along, 0.0)
    width, _, apron = ovalShapeAt(along)
    edges = (-apron - TRACK_MARGIN, -apron, 0.0, width + OVAL_RUNOFF,
             width + OVAL_RUNOFF + TRACK_MARGIN)
    inners = numpy.concatenate((
      numpy.linspace(edges[0], edges[1], 3)[:-1],
      numpy.linspace(edges[1], edges[2], TRACK_APRON + 1)[:-1],
      numpy.linspace(edges[2], edges[3], TRACK_BANK + 1)[:-1],
      numpy.linspace(edges[3], edges[4], 3)))
    outs = inners - 0.5 * width
    places.append(numpy.stack((x + outs * math.sin(heading),
                               y - outs * math.cos(heading)), axis=1))
  places = numpy.array(places)
  count = places.shape[1]
  px, py = places[..., 0].ravel(), places[..., 1].ravel()
  heights = _heightsAt(terrain, px, py)
  step = 0.25
  slopeX = (_heightsAt(terrain, px + step, py)
            - _heightsAt(terrain, px - step, py)) / (2.0 * step)
  slopeY = (_heightsAt(terrain, px, py + step)
            - _heightsAt(terrain, px, py - step)) / (2.0 * step)
  normals = numpy.stack((-slopeX, -slopeY, numpy.ones_like(slopeX)), 1)
  normals /= numpy.linalg.norm(normals, axis=1)[:, None]
  vertices = numpy.empty((len(px), 8), numpy.float32)
  vertices[:, 0], vertices[:, 1] = SCALE * px, SCALE * heights
  vertices[:, 2] = -SCALE * py
  vertices[:, 3], vertices[:, 4] = normals[:, 0], normals[:, 2]
  vertices[:, 5] = -normals[:, 1]
  vertices[:, 6], vertices[:, 7] = px / (2.0 * tile), py / (2.0 * tile)
  k, j = numpy.meshgrid(numpy.arange(rows), numpy.arange(count - 1),
                        indexing='ij')
  a = k * count + j
  b, c, d = a + 1, a + count + 1, a + count
  quads = numpy.stack((a, b, c, a, c, d), axis=2)
  bands = (2, 2 + TRACK_APRON, 2 + TRACK_APRON + TRACK_BANK, count - 1)
  kinds = []
  for low, high in ((0, bands[0]), (bands[2], bands[3]),
                    (bands[1], bands[2]), (bands[0], bands[1])):
    kinds.append(quads[:, low:high].reshape(-1, 6))
  ground = numpy.concatenate(kinds[:2]).ravel().astype(numpy.uint32)
  paved, asphalt = (kind.ravel().astype(numpy.uint32)
                    for kind in kinds[2:])
  grid = numpy.array(terrain.heights)
  gx = terrain.origin[0] + terrain.cell * numpy.arange(grid.shape[0])
  gy = terrain.origin[1] + terrain.cell * numpy.arange(grid.shape[1])
  inner, width, apron, _ = ovalAcross(*numpy.meshgrid(gx, gy,
                                                      indexing='ij'))
  covered = ((inner >= -apron - TRACK_MARGIN)
             & (inner <= width + OVAL_RUNOFF + TRACK_MARGIN))
  return vertices, ground, paved, asphalt, covered


def groundMesh(hole: tuple | None, outer: float,
               tile: float) -> tuple[numpy.ndarray, numpy.ndarray]:
  """The 'groundMesh' function returns the flat ground at height nought
  out to 'outer' m each way about the origin but for 'hole' (x0, y0,
  x1, y1: a terrain's grid, drawn by its own mesh; None: all of it),
  as 'terrainMesh' gives a terrain's. (The hole was once a square about
  the origin: the oval's grid is not, and its flat ground, at the
  infield's height, showed through the apron in spikes.)"""
  corners = []
  if hole is None:
    squares = [(-outer, -outer, outer, outer)]
  else:
    x0, y0, x1, y1 = hole
    squares = [(-outer, -outer, outer, y0), (-outer, y1, outer, outer),
               (-outer, y0, x0, y1), (x1, y0, outer, y1)]
  for x0, y0, x1, y1 in squares:
    corners.extend(((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
  vertices = numpy.array([sceneOf((x, y, 0.0)) + (0.0, 1.0, 0.0,
                                                  x / (2.0 * tile),
                                                  y / (2.0 * tile))
                          for x, y in corners], numpy.float32)
  indices = []
  for k in range(0, len(corners), 4):
    indices.extend((k, k + 1, k + 2, k, k + 2, k + 3))
  return vertices, numpy.array(indices, numpy.uint32)
