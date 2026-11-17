"""
The cabin's furnishings round the room past Asger's corner (user,
2026-11-16: "Have the rest of it have the contents of a camping cabin.
Not a fire place, but the same ... 'hygge'"), Qt-free, in the vessel's
own axes, each mesh by its look: a sofa with cushions and a knitted
blanket, a coffee table with candles and mugs, a floor lamp, a
bookshelf full of books, a kitchen counter with a kettle, a coffee pot
and mugs, a daybed, a plant, fairy lights along the wall, a rag rug.
Where the warm lights are: the lamp's, the candles'. Rows of eight
(place, normal, where on a picture). What is fixed down is solid boxes
too ('obstacles'); the mugs, kettle, coffee pot, pillows and the plant
are loose things (user, 2026-11-17: "FAFO rules"), their meshes apart
('looseThings', 'looseParts'); the books are held in by rails.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
import random

import numpy

from ._cockpit import FLOOR, WALL, capsuleRadius
from ._shapes import UNTURNED, ballRows, boxRows, cylinderRows
from ._shapes import discRows, frustumRows, joined, pointAlong, quadRows

#  Each piece of furniture: where it stands (x, y on the floor, m) and
#  the way its front faces (deg from x toward y: into the room). The
#  bookshelf stood straight behind him; the door is there now (user,
#  2026-11-17: "bro just fit the door. the furnishings can be fixed in
#  place later"): it stands 20 deg round the wall, clear of it.
SOFA = ((0.0, -4.05), 90.0)
TABLE = ((0.0, -2.9), 90.0)
LAMP = ((1.6, -3.85), 90.0)
SHELF = ((4.05 * math.cos(math.radians(200.0)),
          4.05 * math.sin(math.radians(200.0))), 20.0)
COUNTER = ((-2.95, -2.85), 44.0)
BED = ((-3.05, 2.35), -38.0)
PLANT = ((3.1, -2.45), 140.0)
#  The rations (user, 2026-11-17: "To eat, Asger goes to the kitchen
#  where an endless supply of RCIR from the French armed forces"): a
#  crate on the floor at the counter's right end, its half sizes, a
#  ration box's half sizes, m.
RATIONS = (1.0, 0.0)
CRATE = (0.22, 0.17, 0.16)
RATION_BOX = (0.105, 0.075, 0.045)
RUG = ((0.2, -2.55), 1.45)
#  The candles on the coffee table (x, y on its top from its middle,
#  radius, height), the lamp's shade's middle height, the fairy lights'
#  string (from, to: deg round the wall; height, sag, m; bulbs).
CANDLES = ((-0.25, 0.05, 0.035, 0.18), (-0.13, -0.06, 0.03, 0.12),
           (-0.05, 0.08, 0.028, 0.09))
TABLE_HIGH = 0.46
SHADE_HIGH = 1.45
STRING = ((-60.0, -168.0), 2.1, 0.12, 54)
#  A round thing's axes (it stands as the vessel does); a mug's radius,
#  height, m, and mass, kg.
UPRIGHT = UNTURNED
MUG = (0.042, 0.1, 0.35)
#  The bookshelf's brass rails: how high up its row of books, its share
#  of the tallest.
RAIL = 0.6


def _frame(facing: float) -> tuple:
  """Returns a piece's axes when its front faces 'facing' (deg): along
  it (its right as one faces it), toward its front, up (its pictures on
  its tops)."""
  a = math.radians(facing)
  return ((math.sin(a), -math.cos(a), 0.0), (math.cos(a), math.sin(a),
                                             0.0), (0.0, 0.0, 1.0))


def _placed(spot: tuple, along: float, toward: float, high: float) -> tuple:
  """Returns the point 'along', 'toward' and 'high' (m) from a piece's
  spot ((x, y), facing)."""
  (x, y), facing = spot
  axes = _frame(facing)
  return (x + along * axes[0][0] + toward * axes[1][0],
          y + along * axes[0][1] + toward * axes[1][1], FLOOR + high)


def _block(spot: tuple, along: float, toward: float, high: float,
           half: tuple, cell: tuple = None) -> tuple:
  """Returns a box of a piece: its middle 'along', 'toward', 'high' from
  the piece's spot, 'half' its sizes along its axes, its top laid over
  'cell' of a picture (None: none)."""
  return boxRows(_placed(spot, along, toward, high), half,
                 _frame(spot[1]), cell)


@functools.lru_cache(maxsize=1)
def furnishings() -> dict:
  """Returns the still furnishings' meshes by look: each look's rows and
  triangles, joined (the loose things are not among them:
  'looseThings')."""
  return {look: joined(meshes) for look, meshes in _built()[0].items()}


def obstacles() -> tuple:
  """Returns the still furnishings' solid boxes, each its middle, half
  sizes and axes (the vessel's own): what Asger and the loose things
  bump into."""
  return _built()[1]


def looseThings() -> tuple:
  """Returns the loose things (user, 2026-11-17, of them floating:
  "FAFO rules"): each its name, its middle at rest, its half sizes along
  its axes, its axes at rest (the vessel's own) and its mass, kg."""
  return tuple(thing[:5] for thing in _built()[2])


@functools.lru_cache(maxsize=1)
def looseParts() -> tuple:
  """Returns the loose things' meshes, one a look of each (worked out
  once: the scenery asks for them every frame): the thing's index, the
  look, its rows about the thing's middle (the vessel's own axes, as it
  rests; read-only) and triangles."""
  out = []
  for k, thing in enumerate(_built()[2]):
    for look, (rows, faces) in thing[5]:
      about = numpy.array(rows, numpy.float64)
      about[:, :3] -= numpy.array(thing[1])
      about.flags.writeable = False
      out.append((k, look, about, faces))
  return tuple(out)


@functools.lru_cache(maxsize=1)
def _built() -> tuple:
  """Returns the furnishings made: the still meshes by look, the solid
  boxes and the loose things (each its name, middle, half sizes, axes,
  mass and its meshes by look)."""
  meshes, solids, things = {}, [], []

  def put(look: str, mesh: tuple) -> None:
    """Adds 'mesh' to 'look''s still meshes."""
    meshes.setdefault(look, []).append(mesh)

  def solid(middle: tuple, half: tuple, axes: tuple) -> None:
    """Adds a solid box."""
    solids.append((tuple(middle), tuple(half), tuple(axes)))

  def block(look: str, spot: tuple, along: float, toward: float,
            high: float, half: tuple, cell: tuple = None,
            firm: bool = True) -> None:
    """Adds a box of a piece as a still mesh (see '_block'), solid if
    'firm' (a blanket is not)."""
    put(look, _block(spot, along, toward, high, half, cell))
    if firm:
      solid(_placed(spot, along, toward, high), half, _frame(spot[1]))

  def loose(name: str, parts: tuple, middle: tuple, half: tuple,
            axes: tuple, mass: float) -> None:
    """Adds a loose thing: its meshes ('parts': each look and mesh),
    its middle, half sizes along 'axes', its mass."""
    things.append((name, tuple(middle), tuple(half), tuple(axes),
                   float(mass), tuple(parts)))

  room = (put, solid, block, loose)
  _sofa(room)
  _table(room)
  _lamp(room)
  _shelf(room)
  _counter(room)
  _bed(room)
  _plant(room)
  _rations(room)
  (x, y), radius = RUG
  put('rug', discRows((x, y, FLOOR + 0.004), ((1.0, 0.0, 0.0),
                                              (0.0, 1.0, 0.0),
                                              (0.0, 0.0, 1.0)), radius, 64,
                      (0.0, 0.0, 1.0, 1.0)))
  return meshes, tuple(solids), tuple(things)


def _upright(middle: tuple, half: tuple, look: str, mesh: tuple) -> tuple:
  """Returns a round loose thing standing on its foot ('middle' its
  middle, 'half' its half sizes, its axes the vessel's), its one mesh
  'look'."""
  return ((look, mesh),), middle, half, UPRIGHT


def _sofa(room: tuple) -> None:
  """A three seat sofa against the wall: its base, back, arms, seat and
  back cushions, the knitted blanket over its arm (solid: a pillow rests
  on it); two throw pillows, loose on its seat against its back."""
  put, solid, block, loose = room
  s = SOFA
  block('sofa', s, 0.0, 0.0, 0.21, (1.1, 0.42, 0.21))
  block('sofa', s, 0.0, -0.33, 0.62, (1.1, 0.09, 0.22))
  for side in (-1.0, 1.0):
    block('sofa', s, side * 1.02, 0.0, 0.52, (0.09, 0.42, 0.11))
  for k in (-1.0, 0.0, 1.0):
    block('cream', s, k * 0.62, 0.05, 0.49, (0.3, 0.34, 0.07))
    block('cream', s, k * 0.62, -0.2, 0.68, (0.29, 0.08, 0.18))
  block('blanket', s, 0.82, 0.08, 0.57, (0.26, 0.36, 0.012),
        (0.0, 0.0, 1.0, 1.0))
  block('blanket', s, 0.82, 0.43, 0.38, (0.26, 0.012, 0.2),
        (0.0, 0.0, 1.0, 1.0))
  for along, high, half in ((-0.72, 0.722, (0.16, 0.06, 0.16)),
                            (0.75, 0.734, (0.15, 0.06, 0.15))):
    toward = -0.12 + half[1] + 0.002
    loose('pillow', (('rust', _block(s, along, toward, high, half)),),
          _placed(s, along, toward, high), half, _frame(s[1]), 0.35)


def _table(room: tuple) -> None:
  """The low coffee table: its oak top, its legs, three candles on a
  tray (stuck in it; their flames are the light's: 'flamesRows'); two
  mugs, loose."""
  put, solid, block, loose = room
  t = TABLE
  block('oak', t, 0.0, 0.0, TABLE_HIGH - 0.02, (0.62, 0.32, 0.02))
  for a in (-0.55, 0.55):
    for b in (-0.25, 0.25):
      block('oak', t, a, b, 0.5 * (TABLE_HIGH - 0.04),
            (0.025, 0.025, 0.5 * (TABLE_HIGH - 0.04)))
  block('brass', t, -0.15, 0.0, TABLE_HIGH + 0.006, (0.18, 0.13, 0.006))
  for along, toward, radius, high in CANDLES:
    base = _placed(t, along, toward, TABLE_HIGH + 0.012)
    put('wax', cylinderRows(base, (0.0, 0.0, 1.0), radius, high, 20))
    solid(pointAlong(base, (0.0, 0.0, 1.0), 0.5 * high),
          (radius, radius, 0.5 * high), UPRIGHT)
  for along, toward, look in ((0.3, 0.1, 'ceramic'), (0.42, -0.08,
                                                      'blue')):
    _mug(loose, _placed(t, along, toward, TABLE_HIGH), look)


def _mug(loose: object, foot: tuple, look: str) -> None:
  """Adds a loose mug standing on 'foot'."""
  loose('mug', *_upright(pointAlong(foot, (0.0, 0.0, 1.0), 0.5 * MUG[1]),
                         (MUG[0], MUG[0], 0.5 * MUG[1]), look,
                         cylinderRows(foot, (0.0, 0.0, 1.0), MUG[0],
                                      MUG[1], 20)), MUG[2])


def flamesRows() -> tuple:
  """Returns the candles' flames: a little cone over each wick."""
  parts = []
  for along, toward, radius, high in CANDLES:
    wick = _placed(TABLE, along, toward, TABLE_HIGH + 0.012 + high)
    parts.append(frustumRows(wick, (0.0, 0.0, 1.0), 0.009, 0.0015, 0.035,
                             12))
  return joined(parts)


def roundFlamesRows() -> tuple:
  """Returns the candles' flames weightless (user, 2026-11-17, of the
  candles' flames going round and blue in zero gravity: "FAFO rules"):
  with nothing pulling the hot air up, a little ball over each wick."""
  parts = []
  for along, toward, radius, high in CANDLES:
    wick = _placed(TABLE, along, toward, TABLE_HIGH + 0.012 + high)
    parts.append(ballRows(pointAlong(wick, (0.0, 0.0, 1.0), 0.008), 0.009,
                          12))
  return joined(parts)


def candleLight() -> tuple:
  """Returns where the candles' light is: over their flames."""
  along = sum(c[0] for c in CANDLES) / len(CANDLES)
  toward = sum(c[1] for c in CANDLES) / len(CANDLES)
  return _placed(TABLE, along, toward, TABLE_HIGH + 0.3)


def _lamp(room: tuple) -> None:
  """The floor lamp by the sofa: its foot, its pole (the shade is its
  own look: 'shadeRows'; all three solid)."""
  put, solid, block, loose = room
  l = LAMP
  foot = _placed(l, 0.0, 0.0, 0.0)
  put('brass', frustumRows(foot, (0.0, 0.0, 1.0), 0.16, 0.12, 0.03, 32))
  put('brass', cylinderRows(_placed(l, 0.0, 0.0, 0.03), (0.0, 0.0, 1.0),
                            0.012, SHADE_HIGH - 0.03, 12))
  solid(pointAlong(foot, (0.0, 0.0, 1.0), 0.015), (0.15, 0.15, 0.015),
        UPRIGHT)
  solid(pointAlong(foot, (0.0, 0.0, 1.0), 0.5 * SHADE_HIGH),
        (0.012, 0.012, 0.5 * SHADE_HIGH), UPRIGHT)
  solid(pointAlong(foot, (0.0, 0.0, 1.0), SHADE_HIGH), (0.21, 0.21, 0.15),
        UPRIGHT)


def shadeRows() -> tuple:
  """Returns the floor lamp's paper shade (it glows)."""
  return frustumRows(_placed(LAMP, 0.0, 0.0, SHADE_HIGH - 0.15),
                     (0.0, 0.0, 1.0), 0.24, 0.15, 0.3, 40)


def lampLight() -> tuple:
  """Returns where the floor lamp's light is: in its shade."""
  return _placed(LAMP, 0.0, 0.0, SHADE_HIGH)


def _shelf(room: tuple) -> None:
  """The bookshelf against the wall behind him: its sides, back and
  shelves of oak; rows of books on each shelf, held in by a brass rail
  across its front as on a ship's shelves (user, 2026-11-17, of them all
  falling: "Let's lock that down. It's only funny if it is stuff Asger
  could have had a reasonable chance of securing before take off"):
  still, each row a solid box."""
  put, solid, block, loose = room
  f = SHELF
  wide, deep, high = 0.8, 0.16, 1.9
  for side in (-1.0, 1.0):
    block('oak', f, side * wide, 0.0, 0.5 * high, (0.02, deep, 0.5 * high))
  block('oak', f, 0.0, -deep + 0.01, 0.5 * high, (wide, 0.01, 0.5 * high))
  shelves = (0.03, 0.47, 0.91, 1.35, 1.88)
  for z in shelves:
    block('oak', f, 0.0, 0.0, z, (wide - 0.02, deep, 0.015))
  books = random.Random(1978)
  looks = ('book red', 'book green', 'book blue', 'book ochre',
           'book cream')
  for z, top in zip(shelves[:-1], shelves[1:]):
    along, tallest = -wide + 0.03, 0.0
    while along < wide - 0.08:
      thick = books.uniform(0.025, 0.06)
      tall = min(top - z - 0.06, books.uniform(0.2, 0.34))
      look = books.choice(looks)
      toward = books.uniform(0.0, 0.02)
      half = (0.5 * thick - 0.002, books.uniform(0.09, 0.12), 0.5 * tall)
      at = (along + 0.5 * thick, toward, z + 0.015 + 0.5 * tall)
      put(look, _block(f, *at, half))
      tallest = max(tallest, tall)
      along += thick
      if books.random() < 0.08:
        along += books.uniform(0.04, 0.12)
    solid(_placed(f, 0.0, 0.0, z + 0.015 + 0.5 * tallest),
          (wide - 0.03, 0.14, 0.5 * tallest), _frame(f[1]))
    put('brass', cylinderRows(_placed(f, -wide + 0.02, deep - 0.012,
                                      z + RAIL * tallest),
                              _frame(f[1])[0], 0.006, 2.0 * wide - 0.04,
                              12))


def _counter(room: tuple) -> None:
  """The kitchen counter: an oak cupboard, its light top; a kettle, a
  coffee pot and two mugs on it, loose."""
  put, solid, block, loose = room
  c = COUNTER
  block('oak', c, 0.0, 0.0, 0.44, (0.7, 0.3, 0.44))
  block('cream', c, 0.0, 0.01, 0.9, (0.72, 0.32, 0.02))
  foot = _placed(c, -0.35, 0.0, 0.92)
  kettle = joined([frustumRows(foot, (0.0, 0.0, 1.0), 0.1, 0.07, 0.2, 24),
                   cylinderRows(pointAlong(foot, (0.0, 0.0, 1.0), 0.2),
                                (0.0, 0.0, 1.0), 0.02, 0.03, 12)])
  loose('kettle', *_upright(pointAlong(foot, (0.0, 0.0, 1.0), 0.115),
                            (0.1, 0.1, 0.115), 'black', kettle), 1.2)
  foot = _placed(c, 0.0, 0.05, 0.92)
  loose('coffee pot', *_upright(
    pointAlong(foot, (0.0, 0.0, 1.0), 0.11), (0.075, 0.075, 0.11), 'blue',
    frustumRows(foot, (0.0, 0.0, 1.0), 0.075, 0.06, 0.22, 24)), 0.9)
  for along, look in ((0.3, 'ceramic'), (0.45, 'rust')):
    _mug(loose, _placed(c, along, 0.1, 0.92), look)


def _bed(room: tuple) -> None:
  """The daybed: its oak frame, a mattress, the blanket over it; a
  pillow, loose."""
  put, solid, block, loose = room
  b = BED
  block('oak', b, 0.0, 0.0, 0.18, (1.0, 0.45, 0.18))
  block('cream', b, 0.0, 0.0, 0.43, (0.97, 0.42, 0.07))
  block('blanket', b, 0.2, 0.0, 0.51, (0.72, 0.43, 0.012),
        (0.0, 0.0, 1.0, 1.0), False)
  half = (0.14, 0.3, 0.07)
  loose('pillow', (('cream', _block(b, -0.8, 0.0, 0.572, half)),),
        _placed(b, -0.8, 0.0, 0.572), half, _frame(b[1]), 0.6)


def _rations(room: tuple) -> None:
  """The rations by the kitchen counter, endless: an olive crate on the
  floor, its stencilled label on its front, ration boxes stacked on it
  (their tops printed RCIR); all solid, fixed."""
  put, solid, block, loose = room
  c = COUNTER
  along, toward = RATIONS
  block('olive', c, along, toward, CRATE[2], CRATE)
  _, front, _ = _frame(c[1])
  label = _placed(c, along, toward + CRATE[1] + 0.001, CRATE[2])
  side, _, up = _frame(c[1])
  right = tuple(-x for x in side)
  put('rcir', quadRows(label, (right, up, front), (0.17, 0.1),
                       (0.0, 0.0, 1.0, 1.0)))
  low = 2.0 * CRATE[2] + RATION_BOX[2]
  for shift, high in ((-0.1, low), (0.1, low),
                      (0.0, low + 2.0 * RATION_BOX[2])):
    block('rcir', c, along + shift, toward, high, RATION_BOX,
          (0.0, 0.0, 1.0, 1.0))


def rationCrate() -> tuple:
  """Returns the rations' stack (to be looked at and eaten from): its
  middle, its axes (along, toward its front, up) and half sizes."""
  along, toward = RATIONS
  high = CRATE[2] + 2.0 * RATION_BOX[2]
  return (_placed(COUNTER, along, toward, high), _frame(COUNTER[1]),
          (CRATE[0], CRATE[1], high))


def sofaBox() -> tuple:
  """Returns the sofa's seat (to be looked at and sat on): its middle,
  its axes (along, toward its front, up) and half sizes."""
  return _placed(SOFA, 0.0, 0.0, 0.35), _frame(SOFA[1]), (1.1, 0.42, 0.25)


def sofaSeat() -> tuple:
  """Returns where Asger sits on the sofa: the middle cushion's top's
  middle, and the way the sofa faces."""
  return _placed(SOFA, 0.0, 0.05, 0.56), _frame(SOFA[1])[1]


def bedBox() -> tuple:
  """Returns the daybed (to be looked at and slept in): its middle, its
  axes (along, toward its front, up) and half sizes, frame to
  blanket."""
  return _placed(BED, 0.0, 0.0, 0.26), _frame(BED[1]), (1.0, 0.45, 0.26)


def _plant(room: tuple) -> None:
  """A potted plant, loose: a terracotta pot, its leaves fanned out
  round (only the pot bumps into things)."""
  put, solid, block, loose = room
  p = PLANT
  foot = _placed(p, 0.0, 0.0, 0.0)
  pot = frustumRows(foot, (0.0, 0.0, 1.0), 0.16, 0.21, 0.36, 28)
  leaves = random.Random(1979)
  fanned = []
  for k in range(14):
    a = 2.0 * math.pi * k / 14 + leaves.uniform(-0.2, 0.2)
    lean = leaves.uniform(0.35, 0.9)
    long = leaves.uniform(0.35, 0.6)
    way = (math.cos(a) * math.sin(lean), math.sin(a) * math.sin(lean),
           math.cos(lean))
    base = _placed(p, 0.0, 0.0, 0.34)
    middle = tuple(b + 0.5 * long * w for b, w in zip(base, way))
    side = (-math.sin(a), math.cos(a), 0.0)
    normal = (way[1] * side[2] - way[2] * side[1],
              way[2] * side[0] - way[0] * side[2],
              way[0] * side[1] - way[1] * side[0])
    fanned.append(boxRows(middle, (0.06, 0.5 * long, 0.004),
                          (side, way, normal)))
  loose('plant', (('terracotta', pot), ('leaf', joined(fanned))),
        pointAlong(foot, (0.0, 0.0, 1.0), 0.18), (0.2, 0.2, 0.18), UPRIGHT,
        6.0)


def bulbsRows() -> tuple:
  """Returns the fairy lights strung along the wall: little warm bulbs,
  the string sagging between its hooks."""
  (a0, a1), high, sag, count = STRING
  parts = []
  for k in range(count):
    share = k / (count - 1)
    a = math.radians(a0 + (a1 - a0) * share)
    hook = (share * 6.0) % 1.0
    z = FLOOR + high - sag * math.sin(math.pi * hook)
    r = capsuleRadius(z) - WALL - 0.06
    parts.append(cylinderRows((r * math.cos(a), r * math.sin(a), z - 0.02),
                              (0.0, 0.0, 1.0), 0.016, 0.04, 10))
  return joined(parts)
