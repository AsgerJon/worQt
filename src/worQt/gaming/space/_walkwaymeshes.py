"""
The launch tower, its walkway and the door's meshes (user, 2026-11-17:
"The door out of the rocket should be connected to a retractable walk
way"; "Have us start inside a building level with the walkway";
'_walkway', '_launchtower'), Qt-free, rows of eight (place, normal,
where on a picture), each by its look:
- 'towerParts': the tower on the pad (the pad's own axes: x east, y
  north, z up from the ground): the red steel tower under the hall's
  east end, the hall (windows, a light panel, the walkway's opening),
  the stair tower west of it (its walls with windows, the stairs'
  steps on their ramps, the landings, the wall between the lanes,
  handrails, lamps, the lift's shaft), lamps over its doors outside,
  floodlights on the hall's roof, the EXIT sign;
- 'armParts': the walkway in its own axes (from its pivot at the
  hall's east wall, x out to the rocket): a glazed tunnel on a grating
  floor, a lamp along its roof, the rubber hood round the door, the
  door's panel on its wall by the door ('OUTSIDE_PANEL');
- 'leafRows': the door's leaf in the rocket's own axes, closed (it
  slides round the axis into the wall);
- 'insideParts': by the door inside, the panel with its keys
  ('INSIDE_KEYS') and the warning placard ('PLACARD').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._cockpit import FLOOR, WALL, capsuleRadius
from ._shapes import UNTURNED, boxRows, joined, quadRows
from ._launchtower import EXIT_SIGN, FLIGHTS, GROUND, HALL, LANDING, LANES
from ._launchtower import LIFT_FOOT, LIFT_TOP, SHAFT, STAIR_FOOT, STAIR_TOP
from ._launchtower import STAIRWELL, TOWER, TOWER_LEGS, TOWER_TOP
from ._launchtower import STEPS, flightOf, landingLevel, rise
from ._walkway import DOOR_HIGH, DOOR_SPAN, DOOR_WINDOW, PAD_UP, SLOPE
from ._walkway import HELD, NEST, PLATE, SEAL, SECTION_LONG, SECTIONS
from ._walkway import TUNNEL_FROM, TUNNEL_HALF, TUNNEL_HIGH

#  The hall's floor's height over the ground (the cabin's floor's), m.
DECK = FLOOR + PAD_UP
#  The steel tower's legs (half their thickness), its storeys (m), its
#  braces' half thickness; the hall's walls' thickness, m.
LEG = 0.18
STOREY = 4.0
BRACE = 0.06
HALL_WALL = 0.2
#  The stair tower's roof slab, m thick (its walls stop under it: run up
#  into it, their faces lay in its and fought, '_zfight').
TOWER_ROOF = 0.2
#  The walkway: how far it reaches from its pivot to the hull (the skin
#  at the floor), its windows' sill and head over its floor, m (its
#  sections: '_walkway', 'sectionParts').
ARM_LONG = TUNNEL_FROM * -1.0 - capsuleRadius(FLOOR)
SILL, HEAD = 0.9, 2.0
#  The door's panel outside, on the walkway's left wall by the door (its
#  middle in the rocket's own axes; its half sizes), the panel inside by
#  the door (the wall's angle (deg), height over the floor) and its keys
#  (name, key, action, across the panel from its middle, m), the warning
#  placard (the wall's angle, height of its middle, half its sizes), m.
OUTSIDE_PANEL = ((TUNNEL_FROM + ARM_LONG - 1.0, TUNNEL_HALF - 0.02,
                  FLOOR + 1.2), (0.12, 0.16, 0.02))
INSIDE_AT = (168.0, 1.25)
INSIDE_KEYS = (('DOOR', 'E', 'door', -0.08),
               ('LOCK', 'E', 'lock', 0.0),
               ('WALKWAY', 'E', 'walkway', 0.08))
KEY_HALF = (0.025, 0.025, 0.012)
PLACARD = (160.5, 1.5, (0.21, 0.297))
#  The stair tower's and the lift shaft's windows (user, 2026-11-18:
#  "Give the staircase and elevator and elevatorshaft windows"): their
#  sill and head over where one stands (a landing, a flight's middle, a
#  storey of the shaft: the landings' heights), m; across them: the
#  stairwell's south windows along its flights' middle (x), its west
#  and east ones across its lanes (y), the shaft's across it (x north
#  and through the wall to the stairs, y east), m.
SILL_OVER, HEAD_OVER = 0.9, 2.0
STAIR_ALONG = (-22.8, -20.4)
STAIR_ACROSS = (-2.4, -0.6)
SHAFT_ALONG = (-20.6, -19.0)
SHAFT_ACROSS = (0.7, 2.3)


@functools.lru_cache(maxsize=1)
def towerParts() -> dict:
  """Returns the launch tower's meshes by look (the pad's own axes): the
  steel tower under the hall's east end, the hall, the stair tower with
  its stairs and the lift's shaft, the lamps, the EXIT sign
  ('_launchtower')."""
  parts = {}

  def put(look: str, mesh: tuple) -> None:
    """Adds 'mesh' to 'look''s."""
    parts.setdefault(look, []).append(mesh)

  _steel(put)
  _hall(put)
  _stairTower(put)
  _stairs(put)
  for x, y, _ in floodlights():
    put('lamp body', boxRows((x - 0.25, y, _flood_z()), (0.25, 0.35, 0.25),
                             UNTURNED))
    put('lamp', quadRows((x + 0.002, y, _flood_z()), ((0.0, 1.0, 0.0),
                                                      (0.0, 0.0, 1.0),
                                                      (1.0, 0.0, 0.0)),
                         (0.3, 0.2)))
  middle, half = EXIT_SIGN
  put('exit', quadRows((middle[0], middle[1], middle[2] + PAD_UP), (
    (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)), half))
  return {look: joined(meshes) for look, meshes in parts.items()}


def z_(z: float) -> float:
  """Returns 'z' (the rocket's own, on the pad) on the pad's axes."""
  return z + PAD_UP


def _flood_z() -> float:
  """Returns the floodlights' height (the pad's axes)."""
  return z_(TOWER_TOP) + 0.6


def floodlights() -> tuple:
  """Returns where the tower's floodlights are (the pad's own axes): on
  the hall's roof, at its east corners."""
  (_, y0, _), (x1, y1, _) = HALL
  return tuple((x1 + 0.3, y, _flood_z()) for y in (y0, y1))


def hallLight() -> tuple:
  """Returns where the hall's light is (the rocket's own axes)."""
  (x0, y0, z0), (x1, y1, z1) = HALL
  return 0.5 * (x0 + x1), 0.5 * (y0 + y1), z1 - 0.3


def _steel(put: object) -> None:
  """Adds the steel tower under the hall's east end: four legs from the
  ground, braced every storey."""
  xs = sorted({x for x, _ in TOWER_LEGS})
  ys = sorted({y for _, y in TOWER_LEGS})
  x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
  top = z_(FLOOR) - 0.3
  for x, y in TOWER_LEGS:
    put('tower', boxRows((x, y, 0.5 * top), (LEG, LEG, 0.5 * top),
                         UNTURNED))
  sides = (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)),
           ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1)))
  storeys = int(top // STOREY)
  for k in range(storeys + 1):
    z = min(top - 0.2, STOREY * (k + 1))
    for (ax, ay), (bx, by) in sides:
      ux, uy = (1.0, 0.0) if bx != ax else (0.0, 1.0)
      put('tower', _beam((ax + LEG * ux, ay + LEG * uy, z),
                         (bx - LEG * ux, by - LEG * uy, z), BRACE + 0.02))
      if k < storeys:
        low = z - STOREY if k else 0.3
        ux, uy = (1.0, 0.0) if bx != ax else (0.0, 1.0)
        near = (ax + LEG * ux, ay + LEG * uy)
        far = (bx - LEG * ux, by - LEG * uy)
        a, b = ((near + (low,)), (far + (z,))) if k % 2 else (
          (far + (low,)), (near + (z,)))
        put('tower', _beam(*_shortened(a, b, BRACE + 0.04), BRACE))


def _wall(put: object, look: str, low: tuple, high: tuple,
          holes: tuple) -> None:
  """Adds a wall (the box from 'low' to 'high', the pad's axes) with
  'holes' through it (each its low and high corners across and up: its
  long side's axis and z), cut into the boxes round them."""
  along = 0 if high[0] - low[0] >= high[1] - low[1] else 1
  cuts = sorted({low[along], high[along]} | {
    c for (a, _), (b, _) in holes for c in (a, b)})
  for c0, c1 in zip(cuts[:-1], cuts[1:]):
    spans = [(low[2], high[2])]
    for (a, za), (b, zb) in holes:
      if a <= 0.5 * (c0 + c1) <= b:
        spans = [piece for z0, z1 in spans for piece in (
          (z0, min(z1, za)), (max(z0, zb), z1)) if piece[1] - piece[0]
                 > 1e-6]
    for z0, z1 in spans:
      lo, hi = list(low), list(high)
      lo[along], hi[along], lo[2], hi[2] = c0, c1, z0, z1
      put(look, boxRows(tuple(0.5 * (a + b) for a, b in zip(lo, hi)),
                        tuple(0.5 * (b - a) for a, b in zip(lo, hi)),
                        UNTURNED))


def _hall(put: object) -> None:
  """Adds the hall: its floor, roof, north, south and east walls (the
  walkway's opening, windows either side), a light panel in its
  ceiling; its west wall is the stair tower's."""
  (x0, y0, z0), (x1, y1, z1) = HALL
  w = HALL_WALL
  put('hall floor', boxRows((0.5 * (x0 + x1 + w), 0.0, z_(z0) - 0.15), (
    0.5 * (x1 + w - x0), y1 + w, 0.15), UNTURNED))
  put('hall', boxRows((0.5 * (x0 + x1 + w), 0.0, z_(z1) + 0.1), (
    0.5 * (x1 + w - x0), y1 + w, 0.1), UNTURNED))
  sill, head = z_(z0) + 1.0, z_(z0) + 2.2
  for y in (y0 - w, y1):
    _wall(put, 'hall', (x0, y, z_(z0)), (x1 + w, y + w, z_(z1)),
          (((x0 + 0.8, sill), (x1 - 0.8, head)),))
    put('glass', boxRows((0.5 * (x0 + x1), y + 0.5 * w, 0.5 * (
      sill + head)), (0.5 * (x1 - x0) - 0.8, 0.01, 0.5 * (head - sill)),
                         UNTURNED))
  _wall(put, 'hall', (x1, y0, z_(z0)), (x1 + w, y1, z_(z1)),
        (((-TUNNEL_HALF - 0.05, z_(z0)), (TUNNEL_HALF + 0.05, z_(z0)
                                           + TUNNEL_HIGH)),))
  put('lamp', boxRows((0.5 * (x0 + x1), 0.0, z_(z1) - 0.02), (1.2, 0.5,
                                                              0.02),
                      UNTURNED))


def _stairTower(put: object) -> None:
  """Adds the stair tower's walls: outside round its footprint (the
  stairs' doorway out west, the lift's north), its roof, its east wall
  the hall's west (the stairs' and the lift's doorways into it), the
  wall between the stairwell and the lift, the lift's shaft's west
  wall; their windows, a pane of glass in each ('towerWindows'); a lamp
  over each door outside."""
  (tx0, ty0), (tx1, ty1) = TOWER
  ground, roof = z_(GROUND), z_(TOWER_TOP)
  top = roof - TOWER_ROOF
  (sx0, sy0, _), (sx1, sy1, _) = STAIRWELL
  put('tower wall', boxRows((0.5 * (tx0 + tx1), 0.5 * (ty0 + ty1),
                             roof - 0.5 * TOWER_ROOF), (
    0.5 * (tx1 - tx0), 0.5 * (ty1 - ty0), 0.5 * TOWER_ROOF), UNTURNED))
  windows = towerWindows()
  foot = STAIR_FOOT
  walls = {'west': ((tx0, ty0, ground), (sx0, ty1, top), [
             ((foot[0][1], ground), (foot[1][1], ground + 2.2))]),
           'south': ((sx0, ty0, ground), (sx1, sy0, top), [])}
  lift = LIFT_FOOT
  (hx0, hy0, _), (hx1, hy1, _) = SHAFT
  walls['north'] = ((sx0, hy1, ground), (sx1, ty1, top), [
    ((lift[0][0], ground), (lift[1][0], ground + 2.2))])
  stair, door = STAIR_TOP, LIFT_TOP
  floor = z_(FLOOR)
  walls['east'] = ((sx1, ty0, ground), (tx1, ty1, top), [
    ((stair[0][1], floor), (stair[1][1], floor + 2.2)),
    ((door[0][1], floor), (door[1][1], floor + 2.2))])
  walls['between'] = ((sx0, sy1, ground), (sx1, hy0, top), [])
  walls['shaft west'] = ((sx0, hy0, ground), (hx0, hy1, top), [])
  for name, (low, high, holes) in walls.items():
    cut = [((a, z0), (b, z1)) for wall, (a, b), (z0, z1) in windows
           if wall == name]
    _wall(put, 'tower wall', low, high, tuple(holes + cut))
    for wall, (a, b), (z0, z1) in windows:
      if wall != name:
        continue
      middle = [0.5 * (l + h) for l, h in zip(low, high)]
      half = [0.01, 0.01, 0.5 * (z1 - z0)]
      along = 0 if high[0] - low[0] >= high[1] - low[1] else 1
      middle[along], half[along] = 0.5 * (a + b), 0.5 * (b - a)
      middle[2] = 0.5 * (z0 + z1)
      put('glass', boxRows(tuple(middle), tuple(half), UNTURNED))
  put('lamp', boxRows((foot[0][0] - 0.05, 0.5 * (foot[0][1] + foot[1][1]),
                       ground + 2.5), (0.05, 0.3, 0.06), UNTURNED))
  put('lamp', boxRows((0.5 * (lift[0][0] + lift[1][0]), ty1 + 0.05,
                       ground + 2.5), (0.3, 0.05, 0.06), UNTURNED))


@functools.lru_cache(maxsize=1)
def towerWindows() -> tuple:
  """Returns the stair tower's windows (the pad's axes): each its wall
  ('south', 'west', 'east', 'north', 'between': the stairwell's and the
  shaft's), its span across the wall (along its long side) and its sill
  and head. The stairwell: on its south wall along each flight climbing
  there (from its middle), on its west and east walls at each landing
  there (the top one the hall's doorway); the shaft: a window a storey
  (the landings' heights) on its north wall (over the door at its foot)
  and its east wall (below the hall), and through to the stairwell, so
  the lift is seen from the stairs and the stairs from the lift."""
  out = []
  for k in range(0, FLIGHTS, 2):
    stand = z_(landingLevel(k)) + 0.5 * rise()
    out.append(('south', STAIR_ALONG, (stand + SILL_OVER,
                                       stand + HEAD_OVER)))
  for k in range(1, FLIGHTS):
    stand = z_(landingLevel(k))
    out.append(('west' if k % 2 == 0 else 'east', STAIR_ACROSS, (
      stand + SILL_OVER, stand + HEAD_OVER)))
  hall = z_(FLOOR) - 0.4
  for k in range(FLIGHTS + 1):
    stand = z_(landingLevel(k))
    sill, head = stand + SILL_OVER, stand + HEAD_OVER
    if k > 0:
      out.append(('north', SHAFT_ALONG, (sill, head)))
    if head < hall:
      out.append(('east', SHAFT_ACROSS, (sill, head)))
    out.append(('between', SHAFT_ALONG, (sill, head)))
  return tuple(out)


def _stairs(put: object) -> None:
  """Adds the stairs: each flight's steps on its ramp, the landings, the
  wall between the lanes, a handrail up each flight, a lamp on the wall
  at each landing."""
  steps = STEPS
  for k in range(FLIGHTS):
    (y0, y1), (xa, xb), (za, zb) = flightOf(k)
    run = (xb - xa) / steps
    up = (zb - za) / steps
    for j in range(steps):
      x = xa + (j + 0.5) * run
      top = z_(za) + (j + 1) * up
      put('steps', boxRows((x, 0.5 * (y0 + y1), top - 0.5 * up - 0.05), (
        0.5 * abs(run), 0.5 * (y1 - y0), 0.5 * up + 0.05), UNTURNED))
    rail = y0 + 0.06 if k % 2 == 0 else y1 - 0.06
    put('rail', _beam((xa, rail, z_(za) + 0.95), (xb, rail, z_(zb) + 0.95),
                      0.025))
  (x0, y0, _), (x1, y1, _) = STAIRWELL
  for k in range(1, FLIGHTS + 1):
    west = k % 2 == 0
    xa, xb = (x0, x0 + LANDING) if west else (x1 - LANDING, x1)
    level = z_(landingLevel(k))
    put('steps', boxRows((0.5 * (xa + xb), 0.5 * (y0 + y1), level - 0.15),
                         (0.5 * (xb - xa), 0.5 * (y1 - y0), 0.15),
                         UNTURNED))
    wall = x0 + 0.02 if west else x1 - 0.02
    put('lamp', boxRows((wall, 0.5 * (y0 + y1), level + 2.2), (0.02, 0.3,
                                                                0.05),
                        UNTURNED))
  wall = (x0 + LANDING, x1 - LANDING)
  put('tower wall', boxRows((0.5 * sum(wall), LANES[0], 0.5 * (
    z_(GROUND) + z_(FLOOR + 3.0))), (0.5 * (wall[1] - wall[0]), LANES[1],
                                     0.5 * (FLOOR + 3.0 - GROUND)),
                            UNTURNED))


@functools.lru_cache(maxsize=None)
def sectionParts(k: int) -> dict:
  """Returns walkway section 'k''s meshes by look ('_walkway.SECTIONS':
  nested, each 'NEST' smaller than the one after), in its own axes (its
  near end at its floor, x out along it, z up): its floor's grating,
  its roof, its walls below its windows' sills and over their heads,
  their mullions and glass, a lamp; the last at the rocket also its
  rubber seal and hood round the door (its air bumper, 'SEAL' deep
  past its end: user, 2026-11-18, "Use a soft inflatable thing like for
  airliners") and the door's panel outside."""
  parts = {}

  def put(look: str, mesh: tuple) -> None:
    """Adds 'mesh' to 'look''s."""
    parts.setdefault(look, []).append(mesh)

  long, middle = SECTION_LONG, 0.5 * SECTION_LONG
  inset = (SECTIONS - 1 - k) * NEST
  wide, low = TUNNEL_HALF - inset, inset
  high = TUNNEL_HIGH - inset
  outer = wide + PLATE
  put('grating', boxRows((middle, 0.0, low - 0.5 * PLATE), (
    middle, outer, 0.5 * PLATE), UNTURNED))
  put('tunnel', boxRows((middle, 0.0, high + 0.5 * PLATE), (
    middle, outer, 0.5 * PLATE), UNTURNED))
  sill, head = low + SILL, min(high - 0.1, low + HEAD)
  for side in (-1.0, 1.0):
    y = side * (wide + 0.5 * PLATE)
    put('tunnel', boxRows((middle, y, 0.5 * (low + sill)), (
      middle, 0.5 * PLATE, 0.5 * (sill - low)), UNTURNED))
    put('tunnel', boxRows((middle, y, 0.5 * (head + high)), (
      middle, 0.5 * PLATE, 0.5 * (high - head)), UNTURNED))
    for x in (0.05, middle, long - 0.05):
      put('tunnel', boxRows((x, y, 0.5 * (sill + head)), (
        0.05, 0.5 * PLATE, 0.5 * (head - sill)), UNTURNED))
    put('glass', boxRows((middle, y, 0.5 * (sill + head)), (
      middle, 0.005, 0.5 * (head - sill)), UNTURNED))
  put('lamp', boxRows((middle, 0.0, high - 0.02), (middle - 0.4, 0.06,
                                                  0.02), UNTURNED))
  if k < SECTIONS - 1:
    return {look: joined(meshes) for look, meshes in parts.items()}
  for side in (-1.0, 1.0):
    put('rubber', boxRows((long - 0.1, side * (wide - 0.05),
                           low + 0.5 * (high - low)), (
      0.12, 0.05, 0.5 * (high - low)), UNTURNED))
    put('rubber', boxRows((long + 0.5 * SEAL, side * (outer + 0.04),
                           0.5 * (low + high)), (
      0.5 * SEAL, 0.08, 0.5 * (high - low)), UNTURNED))
  put('rubber', boxRows((long + 0.5 * SEAL, 0.0, high + 0.06), (
    0.5 * SEAL, outer + 0.12, 0.08), UNTURNED))
  hood = DOOR_HIGH - FLOOR
  inward = -SLOPE * hood
  put('rubber', _beam((long - 0.05, -outer, high + 0.05),
                      (long + inward, -outer, hood + 0.05), 0.05,
                      (0.0, 1.0, 0.0)))
  put('rubber', _beam((long - 0.05, outer, high + 0.05),
                      (long + inward, outer, hood + 0.05), 0.05,
                      (0.0, 1.0, 0.0)))
  put('tunnel', quadRows((long + 0.5 * inward - 0.02, 0.0,
                          0.5 * (high + hood) + 0.05), (
    (0.0, 1.0, 0.0), _unit((inward + 0.05, 0.0, hood - high)),
    _unit((high - hood, 0.0, inward + 0.05))), (
    outer, 0.5 * math.hypot(inward + 0.05, high - hood))))
  (x, y, z), half = OUTSIDE_PANEL
  axes = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
  local = (x - (TUNNEL_FROM + HELD - SECTION_LONG), y, z - FLOOR)
  put('panel', boxRows(local, half, axes))
  put('key green', boxRows((local[0], local[1] - half[2] - 0.006,
                            local[2]), (0.04, 0.04, 0.006), axes))
  return {look: joined(meshes) for look, meshes in parts.items()}


def outsideKey() -> tuple:
  """Returns the door's key outside: its middle and axes (right, up,
  out of the walkway's wall) and half sizes, the rocket's own axes (the
  walkway at the door)."""
  (x, y, z), half = OUTSIDE_PANEL
  axes = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
  return (x, y - half[2] - 0.006, z), axes, (0.06, 0.06, 0.03)


@functools.lru_cache(maxsize=1)
def leafRows() -> tuple:
  """Returns the door's leaf closed, in the wall's cut (the rocket's own
  axes; it turns about the axis): its outer face, inner face and edges,
  in steps round, its window ('DOOR_WINDOW') open through it, lined
  ('doorGlassRows': its pane)."""
  a0, a1 = (math.radians(a) for a in DOOR_SPAN)
  (w0, w1), (low, high) = DOOR_WINDOW
  w0, w1 = math.radians(w0), math.radians(w1)
  steps = 6
  angles = [a0 + (a1 - a0) * k / steps for k in range(steps + 1)]
  bands = ((FLOOR + 0.004, low), (low, high), (high, DOOR_HIGH - 0.004))
  parts = []
  for out, sign in ((0.003, 1.0), (WALL - 0.003, -1.0)):
    for b0, b1 in zip(angles[:-1], angles[1:]):
      glazed = b0 >= w0 - 1e-9 and b1 <= w1 + 1e-9
      for k, (z0, z1) in enumerate(bands):
        if glazed and k == 1:
          continue
        corners = [_onWall(b, z, out) for b, z in (
          (b0, z0), (b1, z0), (b1, z1), (b0, z1))]
        parts.append(_quadOf(corners, sign))
  middle = _onWall(0.5 * (w0 + w1), 0.5 * (low + high), 0.5 * WALL)
  for b0, b1 in zip(angles[:-1], angles[1:]):
    if b0 >= w0 - 1e-9 and b1 <= w1 + 1e-9:
      for z in (low, high):
        parts.append(_facing([_onWall(b, z, out) for b, out in (
          (b0, 0.003), (b1, 0.003), (b1, WALL - 0.003),
          (b0, WALL - 0.003))], middle))
  for b in (w0, w1):
    parts.append(_facing([_onWall(b, z, out) for z, out in (
      (low, 0.003), (low, WALL - 0.003), (high, WALL - 0.003),
      (high, 0.003))], middle))
  for b, sign in ((a0, -1.0), (a1, 1.0)):
    corners = [_onWall(b, z, out) for z, out in (
      (FLOOR + 0.004, 0.003), (FLOOR + 0.004, WALL - 0.003),
      (DOOR_HIGH - 0.004, WALL - 0.003), (DOOR_HIGH - 0.004, 0.003))]
    parts.append(_quadOf(corners, sign))
  return joined(parts)


@functools.lru_cache(maxsize=1)
def insideParts() -> dict:
  """Returns the panel inside by the door (its plate, its keys: amber,
  red, green) and the placard's frame, by look (the rocket's own
  axes)."""
  parts = {}
  middle, axes = wallFrame(*INSIDE_AT, 0.012)
  parts['panel'] = [boxRows(middle, (0.14, 0.07, 0.012), axes)]
  for (_, _, _, across), look in zip(INSIDE_KEYS, ('key amber', 'key red',
                                                   'key green')):
    key, keyAxes = insideKey(across)
    parts.setdefault(look, []).append(boxRows(key, KEY_HALF, keyAxes))
  angle, high, half = PLACARD
  middle, axes = wallFrame(angle, high, 0.006)
  parts.setdefault('panel', []).append(boxRows(
    middle, (half[0] + 0.012, half[1] + 0.012, 0.006), axes))
  return {look: joined(meshes) for look, meshes in parts.items()}


def insideKey(across: float) -> tuple:
  """Returns a key of the panel inside, 'across' it from its middle: its
  middle and axes (right, up, out into the cabin)."""
  middle, axes = wallFrame(*INSIDE_AT, 0.024 + KEY_HALF[2])
  return tuple(m + across * r for m, r in zip(middle, axes[0])), axes


def placardRows() -> tuple:
  """Returns the warning placard's face (its picture across it)."""
  angle, high, half = PLACARD
  middle, axes = wallFrame(angle, high, 0.0125)
  return quadRows(middle, axes, half)


def placardBox() -> tuple:
  """Returns the placard as a box to look at: its middle, axes and half
  sizes."""
  angle, high, half = PLACARD
  middle, axes = wallFrame(angle, high, 0.0125)
  return middle, axes, (half[0], half[1], 0.02)


def wallFrame(angle: float, high: float, out: float) -> tuple:
  """Returns a place on the cabin's inner wall at 'angle' (deg) and
  'high' over the floor, 'out' m from it into the cabin, and the wall's
  axes there (right as one faces it, up it, out of it into the
  cabin)."""
  a = math.radians(angle)
  z = FLOOR + high
  inward = (-math.cos(a), -math.sin(a), 0.0)
  up = _unit((-SLOPE * inward[0], -SLOPE * inward[1], 1.0))
  normal = _unit((inward[0], inward[1], SLOPE))
  right = _cross(up, normal)
  r = capsuleRadius(z) - WALL
  place = (r * math.cos(a) + out * normal[0],
           r * math.sin(a) + out * normal[1], z + out * normal[2])
  return place, (right, up, normal)


def _onWall(angle: float, z: float, depth: float) -> tuple:
  """Returns the point on the cone 'depth' m in from the skin at 'angle'
  (rad) and 'z'."""
  r = capsuleRadius(z) - depth
  return r * math.cos(angle), r * math.sin(angle), z


def doorGlassRows() -> tuple:
  """Returns the door's window's pane closed, in the middle of the
  leaf's thickness (the rocket's own axes; it turns with the leaf), a
  face each way (seen from in and out)."""
  (w0, w1), (low, high) = DOOR_WINDOW
  angles = numpy.linspace(math.radians(w0), math.radians(w1), 5)
  parts = []
  for b0, b1 in zip(angles[:-1], angles[1:]):
    corners = [_onWall(b, z, 0.5 * WALL) for b, z in (
      (b0, low), (b1, low), (b1, high), (b0, high))]
    parts += [_quadOf(corners, 1.0), _quadOf(corners, -1.0)]
  return joined(parts)


def _facing(corners: list, toward: tuple) -> tuple:
  """Returns a quad through four 'corners' facing 'toward' (a point
  on its front's side)."""
  rows, faces = _quadOf(corners, 1.0)
  middle = numpy.mean(rows[:, :3], 0)
  if float(numpy.dot(rows[0, 3:6], numpy.array(toward) - middle)) < 0.0:
    return _quadOf(corners, -1.0)
  return rows, faces


def _quadOf(corners: list, sign: float) -> tuple:
  """Returns a quad through four 'corners', facing the way their winding
  gives (times 'sign')."""
  a, b, c = corners[0], corners[1], corners[2]
  normal = _unit(_cross(tuple(q - p for p, q in zip(a, b)),
                        tuple(q - p for p, q in zip(a, c))))
  normal = tuple(sign * n for n in normal)
  rows = [tuple(corner) + normal + (0.0, 0.0) for corner in corners]
  faces = (0, 1, 2, 0, 2, 3) if sign > 0 else (0, 2, 1, 0, 3, 2)
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _beam(a: tuple, b: tuple, half: float, side: tuple = None) -> tuple:
  """Returns a square beam from 'a' to 'b', 'half' its thickness."""
  along = tuple(q - p for p, q in zip(a, b))
  long = math.sqrt(sum(x * x for x in along))
  along = tuple(x / long for x in along)
  if side is None:
    side = (0.0, 0.0, 1.0) if abs(along[2]) < 0.9 else (1.0, 0.0, 0.0)
  out = _unit(_cross(along, side))
  up = _cross(out, along)
  middle = tuple(0.5 * (p + q) for p, q in zip(a, b))
  return boxRows(middle, (0.5 * long, half, half), (along, up, out))


def _shortened(a: tuple, b: tuple, by: float) -> tuple:
  """Returns the line from 'a' to 'b' shortened by 'by' at either end
  (two diagonal braces meeting at one point drew their faces in one
  plane there: they end inside the level brace instead, '_zfight')."""
  along = _unit(tuple(q - p for p, q in zip(a, b)))
  return (tuple(p + by * u for p, u in zip(a, along)),
          tuple(q - by * u for q, u in zip(b, along)))


def _unit(v: tuple) -> tuple:
  """Returns 'v' made a unit."""
  size = math.sqrt(sum(x * x for x in v))
  return tuple(x / size for x in v)


def _cross(a: tuple, b: tuple) -> tuple:
  """Returns 'a' across 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])
