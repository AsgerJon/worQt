"""
A car's wheel with its tyre as the user would first understand a tyre
(2026-11-13: "understanding tires as being elastic in tension only
material with pressurized air inside. Show me a typical car wheel, with
cool aluminium rim, and a 'tire' as described fitted"): an alloy rim,
16 by 6.5 inches, five twin spokes, one rigid body of aluminium; on it
a 205/55 R16 tyre of nothing but cords and air. Its carcass cords run
from bead to bead (meridians, polyester), steel belts round under the
tread, rubber round the sidewalls and across every cell (its shear),
each piece a cord that pulls when stretched and folds when not
('CordLine'); where they cross, a node, a ball as thick as the rubber
over the cords there, carrying its share of the tyre's mass; its beads
on the rim's seats; the air sealed in between the carcass and the rim
('Air') at 2.3 bar over the outside's. Nothing else holds its shape:
the air pushes out, the cords pull back.

The rim's own frame: its axle along z, outboard (the spokes' side) up
it, its middle (between the flanges) at the origin. Stepped in small
steps only ('SmallSteps').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import hashlib
import json
import math
import tempfile
from pathlib import Path

from ._assembly import ATMOSPHERE, Air, Assembly, Contact, CordLine
from ._assembly import Crowd
from ._body import Body, State
from ._gears import prismOf
from ._ground import Ground
from ._shape import Shape, Sphere
from ._vectors import Vector, minus, plus, rotated, turnAbout

#  The rim: its bead seats' radius (16 in), its width between its
#  flanges (6.5 in), a flange's height over the seat and thickness, the
#  barrel's wall, its offset (ET 45: the hub's face 45 mm outboard of
#  its middle), the hub's ring (its bore 57.1 mm across, 75 mm out, 30
#  mm thick), its spokes (five pairs, each leaning this far off its
#  pair's middle, as wide at the hub and at the barrel, and their faces
#  along the axle), how many pieces round the barrel and the hub are
#  (for touching: a 24-sided barrel lies 1.7 mm inside its circle,
#  inside the tyre), its alloy's density.
RIM_SEAT, RIM_WIDTH = 0.2032, 0.1651
RIM_FLANGE, RIM_LIP, RIM_SHELL = 0.0175, 0.010, 0.0047
RIM_OFFSET = 0.045
HUB_BORE, HUB_REACH, HUB_THICK = 0.0285, 0.075, 0.030
SPOKES, SPOKE_SPLAY = 5, math.radians(7.0)
SPOKE_INNER, SPOKE_OUTER = 0.030, 0.018
SPOKE_LOW, SPOKE_HIGH = 0.050, 0.078
RIM_SIDES, HUB_SIDES = 24, 10
ALLOY = 2700.0
#  The tyre, a 205/55 R16 (a family car's): its carcass's line from the
#  inboard bead to the crown (rho, w in the rim's frame; the outboard
#  half its mirror), the bead's wire on the seat, the line up past the
#  flange, out to the widest (95.5 mm out: with its 7 mm of rubber,
#  half of the 205 mm), the shoulder, the crown 300.5 mm out (with its
#  16 mm of tread rubber, 316.5: 16 in plus 55 % of 205 mm); how many
#  nodes round and across (bead to bead, the beads on the rim); its
#  mass; the tread band's rubber this many times as heavy a square
#  metre as the sidewalls'.
_CARCASS = ((0.2070, -0.0740), (0.2240, -0.0760), (0.2380, -0.0880),
            (0.2550, -0.0955), (0.2730, -0.0930), (0.2870, -0.0860),
            (0.2965, -0.0720), (0.3000, -0.0500), (0.3005, -0.0250),
            (0.3005, 0.0))
TYRE_AROUND, TYRE_ACROSS = 40, 13
TYRE_MASS, TREAD_HEAVIER = 8.5, 2.5
#  The rubber over the cords: under the tread 16 mm (tread, belts, base),
#  on the sidewalls 7 mm, between them as far out as each node lies.
TREAD_RUBBER, SIDE_RUBBER = 0.016, 0.007
_TREAD_FROM, _SIDE_TO = 0.295, 0.275
#  The cords' stiffness, N/m for each metre across them (stretched by
#  their whole length): the carcass (two plies of polyester), the belts
#  (two plies of steel at 22 degrees under a nylon cap), the sidewalls'
#  rubber round, and the shear across each cell (the belts' crossed
#  plies; rubber on the sidewalls); a ring is a belt's out from
#  'BELT_FROM'.
CARCASS, BELT, SIDEWALL = 2.0e6, 1.5e7, 3.5e4
TREAD_SHEAR, SIDE_SHEAR = 1.0e6, 2.0e4
BELT_FROM = 0.293
#  Its air: 2.3 bar over the outside's (a family car's), as built.
TYRE_PRESSURE = 2.3e5
#  The nodes' moment, kg m²: a node does not turn on its own (a free
#  ball rolls in the patch and carries no grip): its turning is the
#  cords'.
_STEADY = 1.0
#  How long the tyre is let settle into its air, s, before it is used
#  (the gas then set again for the pressure, and settled again for a
#  third of it); its steps; the form of the kept result (a result kept
#  by another form is worked out anew).
_SETTLE, _SETTLE_STEP = 0.12, 2.5e-4
_INFLATED_FORM = 1
#  The yard the wheels roll in: rubber grips the ground (only its grip
#  counts in small steps); the walker on the alloy; a wheel stands so
#  far from the walker at first, upright, its axle along y.
TYRE_YARD = Ground(2e5, 2.0, 1.0, 2e5, 300.0)
_WALKER_ON_ALLOY = (1e5, 1.0, 0.5, 1e5, 300.0)
_RUBBER_GRIP = 0.9
WHEEL_START = (2.0, 0.0)
WHEEL_UPRIGHT = turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)


def _sector(inner: float, outer: float, a0: float,
            a1: float) -> tuple:
  """Returns the outline of a ring's sector from angle 'a0' to 'a1',
  between radii 'inner' and 'outer', its arcs as chords (convex,
  anticlockwise)."""
  return ((inner * math.cos(a0), inner * math.sin(a0)),
          (outer * math.cos(a0), outer * math.sin(a0)),
          (outer * math.cos(a1), outer * math.sin(a1)),
          (inner * math.cos(a1), inner * math.sin(a1)))


def spokePieces() -> tuple[Shape, ...]:
  """The 'spokePieces' function returns the rim's ten spokes, each a
  prism from the hub to the barrel along its own lean."""
  out = []
  inner, outer = 0.9 * HUB_REACH, RIM_SEAT - RIM_SHELL + 0.001
  for k in range(SPOKES):
    for lean in (-SPOKE_SPLAY, SPOKE_SPLAY):
      a = 2.0 * math.pi * k / SPOKES + lean
      u = (math.cos(a), math.sin(a))
      v = (-u[1], u[0])
      outline = tuple((r * u[0] + side * v[0], r * u[1] + side * v[1])
                      for r, side in ((inner, -0.5 * SPOKE_INNER),
                                      (outer, -0.5 * SPOKE_OUTER),
                                      (outer, 0.5 * SPOKE_OUTER),
                                      (inner, 0.5 * SPOKE_INNER)))
      out.append(prismOf(outline, SPOKE_LOW, SPOKE_HIGH))
  return tuple(out)


@functools.lru_cache(maxsize=1)
def rimShape() -> Shape:
  """The 'rimShape' function returns the rim as it touches, convex
  pieces: its barrel ('RIM_SIDES' of them round), its flanges, its
  hub's ring, its spokes."""
  half = 0.5 * RIM_WIDTH
  inner, top = RIM_SEAT - RIM_SHELL, RIM_SEAT + RIM_FLANGE
  parts = []
  for k in range(RIM_SIDES):
    a0 = 2.0 * math.pi * k / RIM_SIDES
    a1 = 2.0 * math.pi * (k + 1) / RIM_SIDES
    parts.append(prismOf(_sector(inner, RIM_SEAT, a0, a1), -half, half))
    flange = _sector(inner, top, a0, a1)
    parts.append(prismOf(flange, half, half + RIM_LIP))
    parts.append(prismOf(flange, -half - RIM_LIP, -half))
  for k in range(HUB_SIDES):
    a0 = 2.0 * math.pi * k / HUB_SIDES
    a1 = 2.0 * math.pi * (k + 1) / HUB_SIDES
    parts.append(prismOf(_sector(HUB_BORE, HUB_REACH, a0, a1),
                         RIM_OFFSET, RIM_OFFSET + HUB_THICK))
  parts += spokePieces()
  shape = parts[0]
  for part in parts[1:]:
    shape = shape.joined(part)
  return shape


RIM = Body.of(rimShape(), ALLOY)


def rimRuns() -> tuple:
  """The 'rimRuns' function returns the rim as drawn ('finishedRows'):
  its barrel and flanges turned smooth, gunmetal ('alloy'), the
  outboard flange's lip polished ('lip'); its hub's ring ('hub') and
  its spokes ('spoke', as they are) machined bright."""
  half = 0.5 * RIM_WIDTH
  inner, top = RIM_SEAT - RIM_SHELL, RIM_SEAT + RIM_FLANGE
  out = half + RIM_LIP
  barrel = (('line', (inner, -out), (top, -out)),
            ('line', (top, -out), (top, -half)),
            ('line', (top, -half), (RIM_SEAT, -half)),
            ('line', (RIM_SEAT, -half), (RIM_SEAT, half)),
            ('line', (RIM_SEAT, half), (top, half)))
  lip = (('line', (top, half), (top, out)),
         ('line', (top, out), (inner, out)))
  bore = (('line', (inner, out), (inner, -out)),)
  low, high = RIM_OFFSET, RIM_OFFSET + HUB_THICK
  hub = (('line', (HUB_BORE, low), (HUB_REACH, low)),
         ('line', (HUB_REACH, low), (HUB_REACH, high)),
         ('line', (HUB_REACH, high), (HUB_BORE, high)),
         ('line', (HUB_BORE, high), (HUB_BORE, low)))
  return (('alloy', barrel), ('lip', lip), ('alloy', bore),
          ('hub', hub)) + tuple(('spoke', piece)
                                 for piece in spokePieces())


@functools.lru_cache(maxsize=1)
def tyreSection() -> tuple[tuple[float, float], ...]:
  """The 'tyreSection' function returns the carcass's line across, bead
  to bead, as 'TYRE_ACROSS' points evenly along it (rho, w)."""
  line = _CARCASS + tuple((r, -w) for r, w in reversed(_CARCASS[:-1]))
  lengths = [0.0]
  for one, two in zip(line, line[1:]):
    lengths.append(lengths[-1] + math.dist(one, two))
  out = []
  for k in range(TYRE_ACROSS):
    at = lengths[-1] * k / (TYRE_ACROSS - 1)
    j = max(i for i in range(len(line) - 1) if lengths[i] <= at + 1e-12)
    j = min(j, len(line) - 2)
    share = (at - lengths[j]) / (lengths[j + 1] - lengths[j])
    out.append(tuple(a + share * (b - a)
                     for a, b in zip(line[j], line[j + 1])))
  return tuple(out)


def rubberAt(rho: float) -> float:
  """The 'rubberAt' function returns how thick the rubber over the
  cords is 'rho' from the axle, m (a node's radius)."""
  if rho >= _TREAD_FROM:
    return TREAD_RUBBER
  if rho <= _SIDE_TO:
    return SIDE_RUBBER
  share = (rho - _SIDE_TO) / (_TREAD_FROM - _SIDE_TO)
  return SIDE_RUBBER + share * (TREAD_RUBBER - SIDE_RUBBER)


def _grid() -> list[list[Vector]]:
  """Returns the tyre's points as moulded, in the rim's frame: around
  by across (the first and last across on the rim, its beads)."""
  section = tyreSection()
  out = []
  for i in range(TYRE_AROUND):
    a = 2.0 * math.pi * i / TYRE_AROUND
    c, s = math.cos(a), math.sin(a)
    out.append([(r * c, r * s, w) for r, w in section])
  return out


def _quadArea(a: Vector, b: Vector, c: Vector, d: Vector) -> float:
  """Returns the area of the quad 'a b c d' (two triangles)."""
  def half(p: Vector, q: Vector, r: Vector) -> float:
    """Returns a triangle's area."""
    u, v = minus(q, p), minus(r, p)
    return 0.5 * math.sqrt(
      (u[1] * v[2] - u[2] * v[1]) ** 2 + (u[2] * v[0] - u[0] * v[2]) ** 2
      + (u[0] * v[1] - u[1] * v[0]) ** 2)
  return half(a, b, c) + half(a, c, d)


@functools.lru_cache(maxsize=1)
def _nodeBodies() -> tuple[Body, ...]:
  """Returns the nodes across (beads left out), each a ball as thick as
  the rubber there, as heavy as its share of the tyre's mass (by the
  area about it, the tread band heavier), steadied ('_STEADY')."""
  grid, section = _grid(), tyreSection()
  weights = [0.0] * TYRE_ACROSS
  for i in range(TYRE_AROUND):
    after = (i + 1) % TYRE_AROUND
    for j in range(TYRE_ACROSS - 1):
      area = _quadArea(grid[i][j], grid[after][j], grid[after][j + 1],
                       grid[i][j + 1])
      rho = 0.5 * (section[j][0] + section[j + 1][0])
      heavy = TREAD_HEAVIER if rho >= BELT_FROM else 1.0
      weights[j] += 0.5 * area * heavy / TYRE_AROUND
      weights[j + 1] += 0.5 * area * heavy / TYRE_AROUND
  total = sum(weights[1:-1])
  moment = ((_STEADY, 0.0, 0.0), (0.0, _STEADY, 0.0), (0.0, 0.0, _STEADY))
  return tuple(Body(TYRE_MASS * weights[j] / total / TYRE_AROUND,
                    (0.0, 0.0, 0.0), moment,
                    Sphere(rubberAt(section[j][0])))
               for j in range(1, TYRE_ACROSS - 1))


def _cordsOf(rim: int, nodeOf: object) -> list:
  """Returns the tyre's cords on the rim at 'rim' ('nodeOf(i, j)' the
  index of the node round 'i', across 'j'): each meridian bead to bead
  (its ends on the rim), each ring of nodes round, two diagonals across
  each cell; each piece as long unstretched as moulded, as stiff as its
  stuff's stiffness times the width it stands for over its length."""
  grid, section = _grid(), tyreSection()
  around, across = TYRE_AROUND, TYRE_ACROSS

  def pointOf(i: int, j: int) -> tuple:
    """Returns the point round 'i', across 'j' as a cord takes it."""
    i %= around
    if j in (0, across - 1):
      return rim, grid[i][j]
    return nodeOf(i, j), (0.0, 0.0, 0.0)

  out = []
  for i in range(around):
    pieces = [math.dist(grid[i][j], grid[i][j + 1])
              for j in range(across - 1)]
    widths = [2.0 * math.pi * 0.5 * (section[j][0] + section[j + 1][0])
              / around for j in range(across - 1)]
    out.append(CordLine(tuple(pointOf(i, j) for j in range(across)),
                        tuple(CARCASS * width / length for width, length
                              in zip(widths, pieces)), tuple(pieces)))
  for j in range(1, across - 1):
    stuff = BELT if section[j][0] >= BELT_FROM else SIDEWALL
    width = 0.5 * (math.dist(section[j - 1], section[j])
                   + math.dist(section[j], section[j + 1]))
    pieces = [math.dist(grid[i][j], grid[(i + 1) % around][j])
              for i in range(around)]
    out.append(CordLine(tuple(pointOf(i, j) for i in range(around)),
                        tuple(stuff * width / length for length in pieces),
                        tuple(pieces), True))
  for i in range(around):
    after = (i + 1) % around
    for j in range(across - 1):
      rho = 0.5 * (section[j][0] + section[j + 1][0])
      stuff = TREAD_SHEAR if rho >= BELT_FROM else SIDE_SHEAR
      area = _quadArea(grid[i][j], grid[after][j], grid[after][j + 1],
                       grid[i][j + 1])
      for one, two in (((i, j), (after, j + 1)), ((after, j), (i, j + 1))):
        length = math.dist(grid[one[0]][one[1]], grid[two[0]][two[1]])
        out.append(CordLine((pointOf(*one), pointOf(*two)),
                            (stuff * area / (length * length),),
                            (length,)))
  return out


def _facesOf(rim: int, nodeOf: object) -> tuple:
  """Returns the closed surface sealing the tyre's air in: the carcass's
  cells and, across the rim between the beads, its well; triangles of
  (body, point) corners, wound out of the air."""
  grid = _grid()
  around, across = TYRE_AROUND, TYRE_ACROSS

  def pointOf(i: int, j: int) -> tuple:
    """Returns the corner round 'i', across 'j'."""
    i %= around
    if j in (0, across - 1):
      return rim, grid[i][j]
    return nodeOf(i, j), (0.0, 0.0, 0.0)

  quads = []
  for i in range(around):
    for j in range(across - 1):
      quads.append(((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)))
    quads.append(((i, across - 1), (i + 1, across - 1), (i + 1, 0),
                  (i, 0)))
  volume = 0.0
  for quad in quads:
    a, b, c, d = (grid[i % around][j] for i, j in quad)
    for p, q, r in ((a, b, c), (a, c, d)):
      volume += (p[0] * (q[1] * r[2] - q[2] * r[1])
                 + p[1] * (q[2] * r[0] - q[0] * r[2])
                 + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
  out = []
  for quad in quads:
    a, b, c, d = (pointOf(*corner) for corner in quad)
    for face in ((a, b, c), (a, c, d)):
      out.append(face if volume > 0.0 else face[::-1])
  return tuple(out)


def _wheelParts(rim: int, gas: float) -> tuple[list, list]:
  """Returns a wheel's bodies (the rim at 'rim', then its nodes round by
  across) and its tyre's cords and air ('gas', J)."""
  free = TYRE_ACROSS - 2

  def nodeOf(i: int, j: int) -> int:
    """Returns the index of the node round 'i', across 'j'."""
    return rim + 1 + (i % TYRE_AROUND) * free + (j - 1)

  bodies = [RIM] + list(_nodeBodies()) * TYRE_AROUND
  connections = _cordsOf(rim, nodeOf) + [Air(_facesOf(rim, nodeOf), gas)]
  return bodies, connections


def _volumeOf(states: tuple, rim: int) -> float:
  """Returns the volume a wheel's tyre seals in (its rim at 'rim') as
  'states' have it, m³."""
  _, connections = _wheelParts(rim, 0.0)
  faces = connections[-1].faces
  total = 0.0
  for face in faces:
    p, q, r = (_placed(states, rim, index, point) for index, point in face)
    total += (p[0] * (q[1] * r[2] - q[2] * r[1])
              + p[1] * (q[2] * r[0] - q[0] * r[2])
              + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
  return total


def _placed(states: tuple, rim: int, index: int, point: Vector) -> Vector:
  """Returns a body's point (in its own frame) in the world as 'states'
  have it (the rim's or a node's centre)."""
  state = states[index]
  if index == rim:
    return plus(state.place, rotated(state.turn, minus(point,
                                                        RIM.centre)))
  return state.place


@functools.lru_cache(maxsize=1)
def inflated() -> tuple:
  """The 'inflated' function returns the tyre as it settles into its
  air on a rim held still (no gravity, nothing touching): each node's
  place in the rim's frame, round by across, and the gas that gives it
  'TYRE_PRESSURE' so (J); a tyre is put on a wheel as it stands
  inflated, not as moulded (let inflate where it is put, its first
  steps flung its nodes outward at metres a second). Worked out once,
  in small steps on the CPU (some seconds, said on the terminal), and
  kept in the temp folder, named for everything it hangs on."""
  made = repr((_INFLATED_FORM, _CARCASS, TYRE_AROUND, TYRE_ACROSS,
               TYRE_MASS, TREAD_HEAVIER, TREAD_RUBBER, SIDE_RUBBER,
               CARCASS, BELT, SIDEWALL, TREAD_SHEAR, SIDE_SHEAR,
               BELT_FROM, TYRE_PRESSURE, _SETTLE, _SETTLE_STEP,
               RIM.mass))
  name = hashlib.sha1(made.encode()).hexdigest()[:16]
  path = Path(tempfile.gettempdir()) / ('worqt-phys-tyre-%s.json' % name)
  if path.exists():
    kept = json.loads(path.read_text())
    return tuple(tuple(tuple(at) for at in row)
                 for row in kept['places']), kept['gas']
  print('inflating the tyre once (some seconds, kept in %s)' % path,
        flush=True)
  places, gas = _inflating()
  path.write_text(json.dumps({'places': places, 'gas': gas}))
  return places, gas


def _inflating() -> tuple:
  """Returns 'inflated''s result, worked out."""
  from ._assembly import Fixed
  from ._small_steps import SmallSteps
  grid = _grid()
  states = [State(RIM.centre)]
  for i in range(TYRE_AROUND):
    for j in range(1, TYRE_ACROSS - 1):
      states.append(State(grid[i][j]))
  states = tuple(states)
  world = SmallSteps((0.0, 0.0, 0.0), None, _SETTLE_STEP, 1, 0.0, 'cpu')
  gas = (TYRE_PRESSURE + ATMOSPHERE) * _volumeOf(states, 0)
  for share in (1.0, 1.0 / 3.0):
    bodies, connections = _wheelParts(0, gas)
    assembly = Assembly(tuple(bodies), (Fixed(0),) + tuple(connections))
    states = world.advancedAll(assembly, states, share * _SETTLE)
    gas = (TYRE_PRESSURE + ATMOSPHERE) * _volumeOf(states, 0)
  free = TYRE_ACROSS - 2
  places = tuple(tuple(states[1 + i * free + j - 1].place
                       for j in range(1, TYRE_ACROSS - 1))
                 for i in range(TYRE_AROUND))
  return places, gas


def tyredWheel(rim: int, place: Vector, turn: tuple,
               velocity: Vector) -> tuple[list, list, list]:
  """The 'tyredWheel' function returns a wheel with its tyre inflated
  ('inflated'), its rim's own frame's origin at 'place', turned by
  'turn', all moving at 'velocity': its bodies (the rim at 'rim', then
  its nodes round by across), their states, and its tyre's cords and
  air."""
  places, gas = inflated()
  bodies, connections = _wheelParts(rim, gas)
  states = [State(plus(place, rotated(turn, RIM.centre)), turn, velocity)]
  for row in places:
    for at in row:
      states.append(State(plus(place, rotated(turn, at)), (1.0, 0.0, 0.0,
                                                           0.0), velocity))
  return bodies, states, connections


def tyreYard() -> tuple[Assembly, tuple[State, ...]]:
  """The 'tyreYard' function returns the walker (body 0) standing in the
  yard and a wheel ('tyredWheel') standing upright on its tread
  'WHEEL_START' from them, its axle along y, its spokes toward -y; the
  walker touching every rim (on the alloy) and, with the tyres' nodes,
  as a crowd ('wheelsOf')."""
  from ._scenes import WALKER
  walker = WALKER.body()
  states = [State((0.0, 0.0, WALKER.radius))]
  outer = tyreSection()[TYRE_ACROSS // 2][0] + TREAD_RUBBER
  place = (WHEEL_START[0], WHEEL_START[1], outer + 0.005)
  bodies, wheel, connections = tyredWheel(1, place, WHEEL_UPRIGHT,
                                          (0.0, 0.0, 0.0))
  return _withWheels((walker,) + tuple(bodies), tuple(connections),
                     tuple(states) + tuple(wheel))


def wheelGiven(assembly: Assembly, states: tuple, state: State) -> tuple[
    Assembly, tuple[State, ...]]:
  """The 'wheelGiven' function returns 'assembly' in 'states' with one
  more wheel, upright, its rim's middle at 'state''s place, moving as
  it does ('tyredWheel'), its bodies last."""
  rim = len(assembly.bodies)
  bodies, wheel, connections = tyredWheel(rim, state.place, WHEEL_UPRIGHT,
                                          state.velocity)
  kept = tuple(c for c in assembly.connections
               if isinstance(c, (CordLine, Air)))
  return _withWheels(assembly.bodies + tuple(bodies),
                     kept + tuple(connections), tuple(states)
                     + tuple(wheel))


def wheelsOf(assembly: Assembly) -> tuple[tuple[int, tuple], ...]:
  """The 'wheelsOf' function returns the wheels of 'assembly': each its
  rim's index and its nodes' (round by across), found from the tyres'
  meridians (cord lines with both ends on one body, the rim)."""
  found: dict = {}
  for line in assembly.cordLines:
    if line.closed or len(line.points) < 3:
      continue
    rim = line.points[0][0]
    if line.points[-1][0] != rim:
      continue
    found.setdefault(rim, []).append(tuple(index for index, _
                                           in line.points[1:-1]))
  return tuple((rim, tuple(rows)) for rim, rows in found.items())


def _withWheels(bodies: tuple, cords: tuple,
                states: tuple) -> tuple[Assembly, tuple[State, ...]]:
  """Returns the yard's assembly of 'bodies' (the walker first, then
  wheels) with the tyres' 'cords' (and air), every touch put back: the
  walker on every rim and every node, every tyre's nodes on every other
  wheel's rim, and, two tyres or more, the tyres as a crowd (rubber's
  grip; the walker in it, its 0.3 m made every node look 0.3 m round
  itself for others)."""
  from ._scenes import _WALKER_ON_STEEL
  probe = Assembly(bodies, cords)
  wheels = wheelsOf(probe)
  connections = list(cords)
  for rim, rows in wheels:
    connections.append(Contact(0, rim, *_WALKER_ON_ALLOY))
    for row in rows:
      for node in row:
        connections.append(Contact(0, node, *_WALKER_ON_STEEL[:2],
                                   _RUBBER_GRIP))
    for other, _ in wheels:
      if other == rim:
        continue
      for row in rows:
        for node in row:
          connections.append(Contact(node, other, *_WALKER_ON_STEEL[:2],
                                     _RUBBER_GRIP))
  if len(wheels) > 1:
    groups = [tuple(node for row in rows for node in row)
              for _, rows in wheels]
    connections.append(Crowd(tuple(groups), _RUBBER_GRIP))
  return Assembly(bodies, tuple(connections)), states


def rimFinishes(assembly: Assembly) -> dict:
  """The 'rimFinishes' function returns how the rims of 'assembly' are
  drawn, by index ('rimRuns')."""
  runs = rimRuns()
  return {rim: runs for rim, _ in wheelsOf(assembly)}
