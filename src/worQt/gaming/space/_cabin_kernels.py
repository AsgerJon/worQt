"""
The Warp kernels that step the cabin's loose bodies (user, 2026-11-17:
Asger getting up and floating round in micro-gravity, "FAFO rules"; the
loose things too): in the vessel's own axes, which move and turn, so
each body feels what is felt there (the vessel's push, its turning).

Two launches a small step: 'pressed' (a thread a point) finds where
each body's points meet the rooms' walls (the rocket's three levels: the
cabin's floor, cone of a wall and ceiling, the head's two levels over
it, the hatches between them; docked to the space station also the top
floor's doorways, the four shafts and the ring's tube over its deck:
'roomGap', each room how far inside it, the rooms joined as deep as the
deepest: '_stationinterior'), the solids in them (some moving: the
elevators' cages, the doors' leaves) and the other bodies' boxes, and
pushes (a spring and a damper along the meeting's normal, as stiff as
its body's share of 'OMEGA', rubbing along it no harder than 'GRIP' of
the push), the push's other half onto the other body; 'moved' (a thread
a body) moves each body a step on by what pushed it and what is felt
there (semi-implicit Euler; a body's spin by Euler's equations in its
own axes).

Body 0 is kept empty: Asger is a box of his own, stepped a frame at a time by
'walked' (a thread; turned by what he meets, his up the host's between
frames), a moving solid for the loose things ('own'); left out while he sits.
The loose things are boxes: their eight corners meet the rest (a ball of
'SKIN' each, inside the box), their boxes are met by the others' points.
float32 throughout ('feedback: GPU always'): a few metres in the cabin.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import warp as wp

from ._levels import CEILING, FLOOR, TIP as NOSE_TIP
from . import _crewman as crew
from . import _stationinterior as rooms
from . import _launchtower as tower
from . import _walkway as walkway

wp.config.log_level = wp.LOG_WARNING
#  No loop unrolled (Asger's box looks round 74 points in loops called
#  from loops: unrolled, the module took over a quarter of an hour to
#  compile for the GPU).
wp.set_module_options({'enable_backward': False, 'max_unroll': 1})


def _single(x: float) -> object:
  """Returns 'x' as a float32 constant of Warp's."""
  return wp.constant(wp.float32(x))


#  The cabin (level 0): its floor's and ceiling's heights; its wall's
#  inner radius at the floor and how fast it narrows going up (m a m),
#  and the cosine of the wall's lean (a distance across it is the radial
#  one times it); the head's levels (their radius inside, each floor and
#  ceiling), the hatches through the slabs (radius, from, to up the
#  axis).
CABIN_FLOOR = _single(FLOOR)
CABIN_TOP = _single(CEILING)
_SLOPE = rooms.CABIN_SLOPE
CABIN_LOW = _single(rooms.CABIN_LOW)
CABIN_SLOPE = _single(_SLOPE)
CABIN_LEAN = _single(1.0 / (1.0 + _SLOPE * _SLOPE) ** 0.5)
LEVEL_INSIDE = _single(rooms.LEVEL_INSIDE)
LEVEL1_LOW = _single(rooms.LEVELS[1][0])
LEVEL1_HIGH = _single(rooms.LEVELS[1][1])
LEVEL2_LOW = _single(rooms.LEVELS[2][0])
LEVEL2_HIGH = _single(rooms.LEVELS[2][1])
HATCH = _single(rooms.HATCH)
HATCH0_LOW = _single(rooms.HATCHES[0][0])
HATCH0_HIGH = _single(rooms.HATCHES[0][1])
HATCH1_LOW = _single(rooms.HATCHES[1][0])
HATCH1_HIGH = _single(rooms.HATCHES[1][1])
#  The rocket's nose's tip (its body reaches no higher on the pad).
TIP = _single(NOSE_TIP)
#  Docked: the top floor's four doorways (boxes along its own x, y, -x,
#  -y: each its low and high corners), the shafts (radius, from), the
#  ring (its tube's middle from the axis, its radius inside), the deck
#  (from the axis), the station's plane up the axis ('_stationinterior').


def _doorwayBox(way: tuple) -> tuple:
  """Returns the top floor's doorway out along 'way' (one of the
  rocket's own +-x, +-y) as a box: its low and high corners."""
  near, far = rooms.DOORWAY
  half, high = rooms.DOORWAY_HALF
  middle = rooms.DOORS_HIGH
  x, y = round(way[0]), round(way[1])
  if x:
    a, b = sorted((x * near, x * far))
    return (a, -half, middle - high), (b, half, middle + high)
  a, b = sorted((y * near, y * far))
  return (-half, a, middle - high), (half, b, middle + high)


DOORWAY0_LOW, DOORWAY0_HIGH = (wp.constant(wp.vec3(*c)) for c in
                               _doorwayBox(rooms.DOOR_WAYS[0]))
DOORWAY1_LOW, DOORWAY1_HIGH = (wp.constant(wp.vec3(*c)) for c in
                               _doorwayBox(rooms.DOOR_WAYS[1]))
DOORWAY2_LOW, DOORWAY2_HIGH = (wp.constant(wp.vec3(*c)) for c in
                               _doorwayBox(rooms.DOOR_WAYS[2]))
DOORWAY3_LOW, DOORWAY3_HIGH = (wp.constant(wp.vec3(*c)) for c in
                               _doorwayBox(rooms.DOOR_WAYS[3]))
SHAFT_INSIDE = _single(rooms.SHAFT_INSIDE)
SHAFT_FROM = _single(rooms.SHAFT_FROM)
TUBE_MIDDLE = _single(rooms.TUBE_MIDDLE)
TUBE_INSIDE = _single(rooms.TUBE_INSIDE)
DECK = _single(rooms.DECK)
PLANE = _single(rooms.PLANE)
#  On the pad (user, 2026-11-17: "The door out of the rocket should be
#  connected to a retractable walk way"; '_walkway'; "We *must* have the
#  ability to walk around in the dark before getting in"; '_launchtower'):
#  the hull's skin at the floor (its radius; it narrows as the wall
#  does), the walkway's tunnel, the doorway through the wall; the launch
#  tower's hall, stairwell, lift shaft, the doorways between them and
#  the ground (each a box: its low and high corners); the yard (a box,
#  outside the rocket's body (a round column, 'BODY' radius) and the
#  stair tower's walls (a box)).


def _box(box: tuple) -> tuple:
  """Returns 'box' (its low and high corners) as two Warp constants."""
  return wp.constant(wp.vec3(*box[0])), wp.constant(wp.vec3(*box[1]))


HOLE_LOW, HOLE_HIGH = _box(walkway.HOLE)
HALL_OUT_LOW, HALL_OUT_HIGH = _box(tower.HALL_OUT)
DOORWAY_LOW, DOORWAY_HIGH = _box(walkway.DOORWAY)
HALL_LOW, HALL_HIGH = _box(tower.HALL)
STAIRS_LOW, STAIRS_HIGH = _box(tower.STAIRWELL)
SHAFT_LOW, SHAFT_HIGH = _box(tower.SHAFT)
STAIR_TOP_LOW, STAIR_TOP_HIGH = _box(tower.STAIR_TOP)
STAIR_FOOT_LOW, STAIR_FOOT_HIGH = _box(tower.STAIR_FOOT)
LIFT_TOP_LOW, LIFT_TOP_HIGH = _box(tower.LIFT_TOP)
LIFT_FOOT_LOW, LIFT_FOOT_HIGH = _box(tower.LIFT_FOOT)
YARD_LOW, YARD_HIGH = _box(tower.YARD)
TOWER_LOW = wp.constant(wp.vec3(tower.TOWER[0][0], tower.TOWER[0][1],
                                tower.GROUND - 1.0))
TOWER_HIGH = wp.constant(wp.vec3(tower.TOWER[1][0], tower.TOWER[1][1],
                                 tower.TOWER_TOP))
BODY = _single(tower.BODY)
#  The rocket's base (its own axes: on the ground where it stands), m:
#  its body is from there up to its nose's tip ('TIP'); nowhere else
#  does it cut the pad's rooms.
BASE = _single(tower.GROUND - 0.5)
#  A meeting's spring: four of them carry a body at 'OMEGA' rad/s (its
#  mass by them sinks g / OMEGA² under g: 0.16 mm at one g, 0.8 mm at
#  five), damped 'DAMPING' of critical; rubbing at most 'GRIP' of the
#  push, slipping slower than that stuck by a damper as stiff.
OMEGA = _single(250.0)
DAMPING = _single(0.4)
GRIP = _single(0.5)
#  A loose box's corners are balls this big, inside its corners.
SKIN_SIZE = 0.004
SKIN = _single(SKIN_SIZE)
#  A meeting closing faster than this, m/s, thuds (pressing on something
#  already, faster than a part of the frame's pull and his legs could
#  close it: a knock while he stands); Asger touches what is
#  within 'NEAR' of him, m (floating a hair off the floor, he can still
#  push off it).
THUD = _single(0.6)
NEAR = _single(0.03)
#  Air in the rooms drags what moves through it (user, 2026-11-18:
#  "PHYSICS MUST BE REAL"; it was a share of the speed a second): half
#  its density times the drag's coefficient and area times the speed
#  squared, against it. The air's density (sea level's: the cabin, the
#  station and the pad all at one atmosphere), kg/m³; a box's drag
#  coefficient (a cube's), its area its mean outline's (a quarter of its
#  surface); Asger's drag coefficient times his outline, m² (a man broad
#  on: 1.0 x 0.8 m²); over his mass: his drag a metre, 1/m. A loose
#  thing's spin the air does not slow (a turning box's drag is some
#  thousandths of its own).
AIR_RHO = 1.2
AIR_DENSITY = _single(AIR_RHO)
BOX_DRAG = _single(1.05)
ASGER_DRAG = _single(0.5 * AIR_RHO * 0.8 / 80.0)
#  Asger's legs: how fast they bring him to the speed asked (most of the
#  way in), s, and at most how hard, m/s².
LEGS_TIME = _single(0.1)
LEGS_MOST = _single(40.0)


@wp.func
def meetingPush(depth: float, normal: wp.vec3, moving: wp.vec3,
                heft: float, grip: float) -> wp.vec3:
  """Returns the push on a point 'depth' m into something along
  'normal' (out of it), moving 'moving' against it, its body's share of
  mass 'heft' kg: a spring and a damper along the normal (never
  pulling), rubbing across it at most 'grip' of the push."""
  stiff = heft * OMEGA * OMEGA * 0.25
  damp = heft * OMEGA * DAMPING * 0.5
  closing = wp.dot(moving, normal)
  push = wp.max(stiff * depth - damp * closing, 0.0)
  sliding = moving - closing * normal
  speed = wp.length(sliding)
  out = push * normal
  if speed > 1.0e-6:
    rub = wp.min(grip * push, heft * OMEGA * 0.25 * speed)
    out = out - sliding * (rub / speed)
  return out


@wp.func
def deeper(best: wp.vec4, inside: float, normal: wp.vec3) -> wp.vec4:
  """Returns 'best' or the room face 'inside' its 'normal' (into the
  room), whichever is deeper inside."""
  if inside > best[3]:
    return wp.vec4(normal[0], normal[1], normal[2], inside)
  return best


@wp.func
def shallower(best: wp.vec4, inside: float, normal: wp.vec3) -> wp.vec4:
  """Returns 'best' or the face 'inside' its 'normal', whichever is
  less inside (a room is inside as far as its nearest face)."""
  if inside < best[3]:
    return wp.vec4(normal[0], normal[1], normal[2], inside)
  return best


@wp.func
def roundRoom(point: wp.vec3, radius: float, low: float,
              high: float) -> wp.vec4:
  """Returns how far 'point' is inside a round room on the axis (its
  'radius', from 'low' to 'high' up it) and the way into it from its
  nearest face."""
  across = wp.sqrt(point[0] * point[0] + point[1] * point[1])
  inward = wp.vec3(0.0, 0.0, 1.0)
  if across > 1.0e-6:
    inward = wp.vec3(-point[0] / across, -point[1] / across, 0.0)
  room = wp.vec4(inward[0], inward[1], inward[2], radius - across)
  room = shallower(room, point[2] - low, wp.vec3(0.0, 0.0, 1.0))
  return shallower(room, high - point[2], wp.vec3(0.0, 0.0, -1.0))


@wp.func
def boxRoom(point: wp.vec3, low: wp.vec3, high: wp.vec3) -> wp.vec4:
  """Returns how far 'point' is inside the box room from 'low' to
  'high' (its nearest face) and the way into it from that face."""
  room = wp.vec4(1.0, 0.0, 0.0, point[0] - low[0])
  room = shallower(room, high[0] - point[0], wp.vec3(-1.0, 0.0, 0.0))
  room = shallower(room, point[1] - low[1], wp.vec3(0.0, 1.0, 0.0))
  room = shallower(room, high[1] - point[1], wp.vec3(0.0, -1.0, 0.0))
  room = shallower(room, point[2] - low[2], wp.vec3(0.0, 0.0, 1.0))
  return shallower(room, high[2] - point[2], wp.vec3(0.0, 0.0, -1.0))


@wp.func
def boxOutside(point: wp.vec3, low: wp.vec3, high: wp.vec3) -> wp.vec4:
  """Returns how far 'point' is outside the box from 'low' to 'high'
  (along the axis it is furthest out by) and the way out of it."""
  room = wp.vec4(-1.0, 0.0, 0.0, low[0] - point[0])
  room = deeper(room, point[0] - high[0], wp.vec3(1.0, 0.0, 0.0))
  room = deeper(room, low[1] - point[1], wp.vec3(0.0, -1.0, 0.0))
  room = deeper(room, point[1] - high[1], wp.vec3(0.0, 1.0, 0.0))
  room = deeper(room, low[2] - point[2], wp.vec3(0.0, 0.0, -1.0))
  return deeper(room, point[2] - high[2], wp.vec3(0.0, 0.0, 1.0))


#  The rooms' layout ('layout', a row each): the station's shafts' ways
#  ('SHAFTS' rows, the rocket's own axes: docked), then the rocket's
#  place and its three axes ('ROCKET', four rows), then the pad's
#  ('PAD'), then each shaft's cage's inside along it ('CAGES', a row a
#  shaft: from, to, m out; user, 2026-11-19, "the spokes are not
#  pressurized. Only the elevators are": the cage is the shaft's only
#  room, moving with it), each in the world's own axes (the cabin's
#  world is the rocket's: its place nought, its axes its own, the pad's
#  where the pad is from it; the pad's world is the pad's, Terra's
#  turning ground,
#  the rocket's where it stands: user, 2026-11-18, "the pad needs to be
#  there"; '_pad'). Each room is had in its own's axes: the cabin, the
#  doorway and the station's the rocket's, the walkway's tunnel, the
#  tower's and the yard the pad's.
SHAFTS = 4
ROCKET = 4
PAD = 8
CAGES = 12
LAYOUT_ROWS = 16


@wp.func
def localIn(layout: wp.array(dtype=wp.vec3), first: int,
            point: wp.vec3) -> wp.vec3:
  """Returns 'point' (the world's own axes) in the axes whose place and
  axes are 'layout''s rows from 'first'."""
  off = point - layout[first]
  return wp.vec3(wp.dot(off, layout[first + 1]),
                 wp.dot(off, layout[first + 2]),
                 wp.dot(off, layout[first + 3]))


@wp.func
def worldOf(layout: wp.array(dtype=wp.vec3), first: int,
            room: wp.vec4) -> wp.vec4:
  """Returns 'room' (its way in, in the axes of 'layout''s rows from
  'first', and its depth) with its way in the world's own axes."""
  way = (room[0] * layout[first + 1] + room[1] * layout[first + 2]
         + room[2] * layout[first + 3])
  return wp.vec4(way[0], way[1], way[2], room[3])


@wp.func
def deeperRoom(best: wp.vec4, room: wp.vec4) -> wp.vec4:
  """Returns 'best' or 'room', whichever is deeper inside."""
  return deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))


@wp.func
def towerRooms(p: wp.vec3, q: wp.vec3, best: wp.vec4, outside: int,
               layout: wp.array(dtype=wp.vec3)) -> wp.vec4:
  """Returns 'best' or the launch tower's rooms if deeper ('p' the
  point in the pad's axes, 'q' in the rocket's): its hall, stairwell
  and lift shaft, the stairwell's doorways, the lift's open ones
  ('outside' four: the hall's, eight: the ground's), the yard round it
  (outside the rocket's body and the stair tower)."""
  best = deeperRoom(best, worldOf(layout, PAD, boxRoom(p, HALL_LOW,
                                                       HALL_HIGH)))
  best = deeperRoom(best, worldOf(layout, PAD, boxRoom(p, STAIRS_LOW,
                                                       STAIRS_HIGH)))
  best = deeperRoom(best, worldOf(layout, PAD, boxRoom(p, SHAFT_LOW,
                                                       SHAFT_HIGH)))
  best = deeperRoom(best, worldOf(layout, PAD, boxRoom(
    p, STAIR_TOP_LOW, STAIR_TOP_HIGH)))
  best = deeperRoom(best, worldOf(layout, PAD, boxRoom(
    p, STAIR_FOOT_LOW, STAIR_FOOT_HIGH)))
  if outside % 8 >= 4:
    best = deeperRoom(best, worldOf(layout, PAD, boxRoom(
      p, LIFT_TOP_LOW, LIFT_TOP_HIGH)))
  if outside >= 8:
    best = deeperRoom(best, worldOf(layout, PAD, boxRoom(
      p, LIFT_FOOT_LOW, LIFT_FOOT_HIGH)))
  yard = worldOf(layout, PAD, boxRoom(p, YARD_LOW, YARD_HIGH))
  across = wp.sqrt(q[0] * q[0] + q[1] * q[1])
  outward = wp.vec4(1.0, 0.0, 0.0, 0.0)
  if across > 1.0e-6:
    outward = wp.vec4(q[0] / across, q[1] / across, 0.0, 0.0)
  outward = worldOf(layout, ROCKET, outward)
  if q[2] > BASE and q[2] < TIP:
    yard = shallower(yard, across - BODY, wp.vec3(outward[0], outward[1],
                                                  outward[2]))
  walls = worldOf(layout, PAD, boxOutside(p, TOWER_LOW, TOWER_HIGH))
  yard = shallower(yard, walls[3], wp.vec3(walls[0], walls[1], walls[2]))
  walls = worldOf(layout, PAD, boxOutside(p, HALL_OUT_LOW, HALL_OUT_HIGH))
  yard = shallower(yard, walls[3], wp.vec3(walls[0], walls[1], walls[2]))
  return deeperRoom(best, yard)


@wp.func
def padRooms(p: wp.vec3, q: wp.vec3, best: wp.vec4, outside: int,
             layout: wp.array(dtype=wp.vec3)) -> wp.vec4:
  """Returns 'best' or the rooms outside the rocket on the pad if deeper
  ('p' the point in the pad's axes, 'q' in the rocket's): the hole from
  the hall out to the walkway (its sections are solids in the open
  air: '_walkway') and the launch tower's rooms ('towerRooms'), the
  world's own axes."""
  best = deeperRoom(best, worldOf(layout, PAD, boxRoom(p, HOLE_LOW,
                                                       HOLE_HIGH)))
  return towerRooms(p, q, best, outside, layout)


@wp.func
def rocketRooms(q: wp.vec3, docked: int, outside: int,
                layout: wp.array(dtype=wp.vec3)) -> wp.vec4:
  """Returns how far 'q' (the rocket's own axes) is inside the rocket's
  rooms (the cabin, the head's two levels, the hatches between them;
  'outside' two, the doorway through the cabin's wall; docked, also the
  top floor's doorways, the cages' insides along the shafts out along
  'layout''s first rows, the ring) and the way into them (its
  axes)."""
  across = wp.sqrt(q[0] * q[0] + q[1] * q[1])
  outward = wp.vec3(1.0, 0.0, 0.0)
  if across > 1.0e-6:
    outward = wp.vec3(q[0] / across, q[1] / across, 0.0)
  inner = CABIN_LOW + CABIN_SLOPE * wp.clamp(q[2] - CABIN_FLOOR, 0.0,
                                             CABIN_TOP - CABIN_FLOOR)
  wall = wp.vec3(-outward[0] * CABIN_LEAN, -outward[1] * CABIN_LEAN,
                 CABIN_SLOPE * CABIN_LEAN)
  best = wp.vec4(wall[0], wall[1], wall[2], (inner - across) * CABIN_LEAN)
  best = shallower(best, q[2] - CABIN_FLOOR, wp.vec3(0.0, 0.0, 1.0))
  best = shallower(best, CABIN_TOP - q[2], wp.vec3(0.0, 0.0, -1.0))
  best = deeperRoom(best, roundRoom(q, LEVEL_INSIDE, LEVEL1_LOW,
                                    LEVEL1_HIGH))
  best = deeperRoom(best, roundRoom(q, LEVEL_INSIDE, LEVEL2_LOW,
                                    LEVEL2_HIGH))
  best = deeperRoom(best, roundRoom(q, HATCH, HATCH0_LOW, HATCH0_HIGH))
  best = deeperRoom(best, roundRoom(q, HATCH, HATCH1_LOW, HATCH1_HIGH))
  if outside % 4 >= 2:
    best = deeperRoom(best, boxRoom(q, DOORWAY_LOW, DOORWAY_HIGH))
  if docked == 0:
    return best
  best = deeperRoom(best, boxRoom(q, DOORWAY0_LOW, DOORWAY0_HIGH))
  best = deeperRoom(best, boxRoom(q, DOORWAY1_LOW, DOORWAY1_HIGH))
  best = deeperRoom(best, boxRoom(q, DOORWAY2_LOW, DOORWAY2_HIGH))
  best = deeperRoom(best, boxRoom(q, DOORWAY3_LOW, DOORWAY3_HIGH))
  floor = -outward
  tube = wp.vec3(outward[0] * (across - TUBE_MIDDLE),
                 outward[1] * (across - TUBE_MIDDLE), q[2] - PLANE)
  size = wp.length(tube)
  inward = -outward
  if size > 1.0e-6:
    inward = -tube / size
  room = wp.vec4(inward[0], inward[1], inward[2], TUBE_INSIDE - size)
  room = shallower(room, DECK - across, floor)
  best = deeperRoom(best, room)
  for k in range(SHAFTS):
    way = layout[k]
    span = layout[CAGES + k]
    low = wp.max(SHAFT_FROM, span[0])
    high = span[1]
    out = q[0] * way[0] + q[1] * way[1]
    along = wp.clamp(out, low, wp.max(low, high))
    off = q - wp.vec3(along * way[0], along * way[1], PLANE)
    size = wp.length(off)
    inward = floor
    if size > 1.0e-6:
      inward = -off / size
    room = wp.vec4(inward[0], inward[1], inward[2], SHAFT_INSIDE - size)
    room = shallower(room, out - low, way)
    room = shallower(room, high - out, -way)
    best = deeperRoom(best, room)
  return best


@wp.func
def roomGap(point: wp.vec3, docked: int, outside: int,
            layout: wp.array(dtype=wp.vec3)) -> wp.vec4:
  """Returns how far 'point' (the world's own axes) is inside the rooms
  (the rocket's, 'rocketRooms', where the rocket is; on the pad,
  'outside' one, the pad's, 'padRooms', where the pad is: 'layout'):
  as deep as the room it is deepest in; less than nought: in a wall)
  and the way into them from the nearest face (x y z, the world's own
  axes, then the depth)."""
  q = localIn(layout, ROCKET, point)
  best = worldOf(layout, ROCKET, rocketRooms(q, docked, outside, layout))
  if outside % 2 == 1:
    best = padRooms(localIn(layout, PAD, point), q, best, outside, layout)
  return best


#  Whose a room's face is ('roomOwner', and a meeting's on it, 'walked'):
#  the rocket's (its cabin, its doorway, the station's docked, its body
#  met from the pad's air) or the pad's (the tower's, the ground, the
#  hole out of the hall).
ROCKET_FACE = -2
PAD_FACE = -1


@wp.func
def roomOwner(point: wp.vec3, docked: int, outside: int,
              layout: wp.array(dtype=wp.vec3)) -> int:
  """Returns whose face of the rooms is nearest 'point' ('roomGap''s):
  'ROCKET_FACE' or 'PAD_FACE'."""
  q = localIn(layout, ROCKET, point)
  inRocket = rocketRooms(q, docked, outside, layout)[3]
  if outside % 2 == 0:
    return ROCKET_FACE
  pad = padRooms(localIn(layout, PAD, point), q, wp.vec4(
    0.0, 0.0, 1.0, -1.0e9), outside, layout)
  if inRocket >= pad[3]:
    return ROCKET_FACE
  across = wp.sqrt(q[0] * q[0] + q[1] * q[1])
  if q[2] > BASE and q[2] < TIP and across > 1.0e-6:
    if wp.abs(across - BODY - pad[3]) < 1.0e-4:
      out = worldOf(layout, ROCKET, wp.vec4(q[0] / across, q[1] / across,
                                            0.0, 0.0))
      if (pad[0] * out[0] + pad[1] * out[1] + pad[2] * out[2]) > 0.99:
        return ROCKET_FACE
  return PAD_FACE


@wp.func
def boxDepth(point: wp.vec3, radius: float, middle: wp.vec3,
             turn: wp.quat, half: wp.vec3) -> wp.vec4:
  """Returns how far a ball ('point', 'radius') is into a box ('middle',
  'turn', 'half') and the way out of it: the normal's x, y, z and the
  depth (below nought: not in)."""
  local = wp.quat_rotate_inv(turn, point - middle)
  near = wp.vec3(wp.clamp(local[0], -half[0], half[0]),
                 wp.clamp(local[1], -half[1], half[1]),
                 wp.clamp(local[2], -half[2], half[2]))
  off = local - near
  apart = wp.length(off)
  depth = float(-1.0)
  normal = wp.vec3(0.0, 0.0, 1.0)
  if apart > 1.0e-9:
    if apart < radius:
      depth = radius - apart
      normal = off / apart
  else:
    ex = half[0] - wp.abs(local[0])
    ey = half[1] - wp.abs(local[1])
    ez = half[2] - wp.abs(local[2])
    side = float(1.0)
    if ex <= ey and ex <= ez:
      if local[0] < 0.0:
        side = -1.0
      depth = radius + ex
      normal = wp.vec3(side, 0.0, 0.0)
    elif ey <= ez:
      if local[1] < 0.0:
        side = -1.0
      depth = radius + ey
      normal = wp.vec3(0.0, side, 0.0)
    else:
      if local[2] < 0.0:
        side = -1.0
      depth = radius + ez
      normal = wp.vec3(0.0, 0.0, side)
  way = wp.quat_rotate(turn, normal)
  return wp.vec4(way[0], way[1], way[2], depth)


@wp.func
def thudOf(depth: float, closing: float, before: int, heft: float,
           thuds: wp.array(dtype=wp.float32), body: int,
           landing: wp.array(dtype=wp.float32)) -> int:
  """Counts a thud on a meeting begun closing fast ('before': the point
  touched nothing the step before), its loudness by its speed and heft;
  Asger's (body nought) meetings begun keep the fastest in 'landing' (it
  hurts him); returns one (it touches)."""
  if before == 0 and -closing > THUD:
    wp.atomic_add(thuds, 0, 1.0)
    wp.atomic_max(thuds, 1, -closing * wp.min(1.0, wp.sqrt(heft / 20.0)))
  if before == 0 and body == 0:
    wp.atomic_max(landing, 0, -closing)
  return 1


#  The most solids near a loose body a frame ('bodiesNear': its points
#  look at those alone; each point reading all four hundred solids each
#  1/1200 s step, most of them the station's empty slots, took 0.15 ms a
#  step: 10-20 ms a frame. More near than this, it reads them all.) And
#  how much further than its own reach and its speed may take it in the
#  frame it looks, m, and as if pulled how hard besides what it feels,
#  m/s² (the frame's turning and pushes).
BODY_NEAR_MOST = 48
BODY_SLACK = _single(1.0)
BODY_PULL = _single(20.0)


@wp.kernel
def bodiesNear(places: wp.array(dtype=wp.vec3),
               velocities: wp.array(dtype=wp.vec3),
               reaches: wp.array(dtype=wp.float32),
               solidMiddles: wp.array(dtype=wp.vec3),
               solidHalves: wp.array(dtype=wp.vec3),
               solidVelocities: wp.array(dtype=wp.vec3),
               near: wp.array2d(dtype=wp.int32),
               nearCount: wp.array(dtype=wp.int32), felt: float,
               seconds: float):
  """Lists the solids each loose body (a thread a body and a solid) may
  meet this frame: within its reach ('reaches': its points' farthest
  from its middle and their round), how far it may go in 'seconds' (its
  speed, and pulled 'felt' and 'BODY_PULL' m/s²) and 'BODY_SLACK', and
  the solid's as far as it moves; at most 'BODY_NEAR_MOST' in its row
  of 'near', how many in 'nearCount' (emptied before)."""
  body, k = wp.tid()
  if body == 0:
    return
  going = (wp.length(velocities[body]) * seconds
           + 0.5 * (felt + BODY_PULL) * seconds * seconds)
  reach = (reaches[body] + going + BODY_SLACK + wp.length(solidHalves[k])
           + wp.length(solidVelocities[k]) * seconds)
  if wp.length(solidMiddles[k] - places[body]) < reach:
    slot = wp.atomic_add(nearCount, body, 1)
    if slot < BODY_NEAR_MOST:
      near[body, slot] = k


@wp.kernel
def pressed(places: wp.array(dtype=wp.vec3),
            turns: wp.array(dtype=wp.quat),
            velocities: wp.array(dtype=wp.vec3),
            spins: wp.array(dtype=wp.vec3),
            masses: wp.array(dtype=wp.float32),
            halves: wp.array(dtype=wp.vec3),
            owners: wp.array(dtype=wp.int32),
            locals: wp.array(dtype=wp.vec3),
            radii: wp.array(dtype=wp.float32),
            solidMiddles: wp.array(dtype=wp.vec3),
            solidTurns: wp.array(dtype=wp.quat),
            solidHalves: wp.array(dtype=wp.vec3),
            solidVelocities: wp.array(dtype=wp.vec3),
            layout: wp.array(dtype=wp.vec3),
            bodyNear: wp.array2d(dtype=wp.int32),
            bodyNearCount: wp.array(dtype=wp.int32),
            touched: wp.array(dtype=wp.int32),
            pushes: wp.array(dtype=wp.vec3),
            twists: wp.array(dtype=wp.vec3),
            asger: wp.array(dtype=wp.vec3),
            thuds: wp.array(dtype=wp.float32),
            landing: wp.array(dtype=wp.float32),
            up: wp.vec3, present: int, legs: int, docked: int,
            outside: int, elapsed: float):
  """Pushes each point (a thread a point) out of what it is in: the
  rooms' walls ('roomGap'; 'docked': the station's rooms too; 'outside':
  the walkway's; 'layout': where each is), the solids (where they
  were at the frame's start, moved on at their velocities 'elapsed' s
  since: an elevator's cage at 30 m/s left still a frame long had him
  0.4 m into its plates), the other bodies' boxes
  (their share pushed back; a body of no mass is put away: it meets
  nothing and is met by nothing, '_deckthings'); counts Asger's
  meetings ('asger' 0: their count in x, 1: their normals summed: he
  touches what is within 'NEAR' of him; his legs or the gun at work
  ('legs'), they hold him, not the rubbing), the fastest he met
  anything ('landing') and the thuds. A loose body's points look at
  the solids listed near it this frame ('bodiesNear'), all of them if
  more than it lists."""
  i = wp.tid()
  body = owners[i]
  middle = places[body]
  arm = wp.vec3(0.0, 0.0, 0.0)
  moving = velocities[body]
  margin = float(0.0)
  grip = GRIP
  if body != 0 and masses[body] <= 0.0:
    touched[i] = 0
    return
  if body == 0:
    if present == 0:
      touched[i] = 0
      return
    arm = up * locals[i][2]
    margin = NEAR
    if legs == 1:
      grip = 0.0
  else:
    arm = wp.quat_rotate(turns[body], locals[i])
    moving = moving + wp.cross(spins[body], arm)
  point = middle + arm
  radius = radii[i] + margin
  heft = masses[body]
  before = touched[i]
  touching = int(0)
  push = wp.vec3(0.0, 0.0, 0.0)
  normals = wp.vec3(0.0, 0.0, 0.0)
  room = roomGap(point, docked, outside, layout)
  depth = radius - room[3]
  if depth > 0.0:
    normal = wp.vec3(room[0], room[1], room[2])
    touching = thudOf(depth, wp.dot(moving, normal), before, heft,
                       thuds, body, landing)
    normals = normals + normal
    if depth > margin:
      push = push + meetingPush(depth - margin, normal, moving, heft, grip)
  listed = int(1)
  total = bodyNearCount[body]
  if body == 0 or total > BODY_NEAR_MOST:
    listed = 0
    total = solidMiddles.shape[0]
  for m in range(total):
    j = m
    if listed == 1:
      j = bodyNear[body, m]
    half = solidHalves[j]
    there = solidMiddles[j] + solidVelocities[j] * elapsed
    if wp.length(point - there) < wp.length(half) + radius:
      met = boxDepth(point, radius, there, solidTurns[j], half)
      if met[3] > 0.0:
        normal = wp.vec3(met[0], met[1], met[2])
        relative = moving - solidVelocities[j]
        touching = thudOf(met[3], wp.dot(relative, normal), before, heft,
                          thuds, body, landing)
        normals = normals + normal
        if met[3] > margin:
          push = push + meetingPush(met[3] - margin, normal, relative,
                                    heft, grip)
  for other in range(1, places.shape[0]):
    if other != body and masses[other] > 0.0:
      half = halves[other]
      there = places[other]
      if wp.length(point - there) < wp.length(half) + radius:
        met = boxDepth(point, radius, there, turns[other], half)
        if met[3] > 0.0:
          normal = wp.vec3(met[0], met[1], met[2])
          meeting = point - radius * normal
          theirs = velocities[other] + wp.cross(spins[other],
                                                meeting - there)
          shared = heft * masses[other] / (heft + masses[other])
          touching = thudOf(met[3], wp.dot(moving - theirs, normal),
                            before, shared, thuds, body, landing)
          normals = normals + normal
          if met[3] > margin:
            metPush = meetingPush(met[3] - margin, normal, moving - theirs,
                                  shared, GRIP)
            push = push + metPush
            wp.atomic_add(pushes, other, -metPush)
            wp.atomic_add(twists, other, wp.cross(meeting - there,
                                                  -metPush))
  touched[i] = touching
  if touching == 0:
    return
  wp.atomic_add(pushes, body, push)
  if body == 0:
    wp.atomic_add(asger, 0, wp.vec3(1.0, 0.0, 0.0))
    wp.atomic_add(asger, 1, normals)
  else:
    wp.atomic_add(twists, body, wp.cross(arm, push))


@wp.kernel
def moved(places: wp.array(dtype=wp.vec3),
          turns: wp.array(dtype=wp.quat),
          velocities: wp.array(dtype=wp.vec3),
          spins: wp.array(dtype=wp.vec3),
          masses: wp.array(dtype=wp.float32),
          inertias: wp.array(dtype=wp.vec3),
          halves: wp.array(dtype=wp.vec3),
          pushes: wp.array(dtype=wp.vec3),
          twists: wp.array(dtype=wp.vec3),
          asger: wp.array(dtype=wp.vec3),
          reaction: wp.array(dtype=wp.vec3),
          felt: wp.vec3, turning: wp.vec3, speeding: wp.vec3,
          gunBody: int, gun: wp.vec3, step: float):
  """Moves each loose body (a thread a body) a 'step' on: pushed, and
  feeling the vessel's push 'felt' (its own axes: what it feels, thrust,
  drag and the ground; gravity it does not), its turning ('turning',
  rad/s) and its turning faster ('speeding', rad/s²); body 'gunBody'
  also by the Grav-Gun ('gun': its force on it over its mass, m/s²,
  '_gravgun'). Body nought is no body (Asger's box is moved by
  'walked'). Its pushes are spent (made nought for the next step).
  What really pushed it (the meetings, the gun, the air; not what the
  vessel's own moving makes it feel) pushes the vessel back as hard
  ('reaction' 2: the push, N s; 3: its twist about the vessel's middle,
  N m s; the vessel's own axes: the walls and the air are the
  vessel's, a push between two loose bodies cancels). A body of no mass
  is put away: it does not move."""
  b = wp.tid()
  push = pushes[b]
  twist = twists[b]
  pushes[b] = wp.vec3(0.0, 0.0, 0.0)
  twists[b] = wp.vec3(0.0, 0.0, 0.0)
  if b == 0:
    asger[0] = wp.vec3(0.0, 0.0, 0.0)
    asger[1] = wp.vec3(0.0, 0.0, 0.0)
    return
  heft = masses[b]
  if heft <= 0.0:
    return
  place = places[b]
  velocity = velocities[b]
  feel = (push / heft - felt - wp.cross(turning, wp.cross(turning, place))
          - 2.0 * wp.cross(turning, velocity) - wp.cross(speeding, place))
  half = halves[b]
  outline = 2.0 * (half[0] * half[1] + half[1] * half[2]
                   + half[0] * half[2])
  drag = (0.5 * AIR_DENSITY * BOX_DRAG) * outline * wp.length(velocity)
  real = push - drag * velocity
  if b == gunBody:
    feel = feel + gun
    real = real + gun * heft
  velocity = velocity + (feel - (drag / heft) * velocity) * step
  places[b] = place + velocity * step
  velocities[b] = velocity
  turn = turns[b]
  inertia = inertias[b]
  spin = wp.quat_rotate_inv(turn, spins[b])
  torque = wp.quat_rotate_inv(turn, twist)
  held = wp.cw_mul(inertia, spin)
  spin = spin + wp.cw_div(torque - wp.cross(spin, held), inertia) * step
  spin = wp.quat_rotate(turn, spin)
  spin = spin + (-speeding - wp.cross(turning, spin)) * step
  spins[b] = spin
  wp.atomic_add(reaction, 2, -real * step)
  wp.atomic_add(reaction, 3, -(wp.cross(place, real) + twist) * step)
  turned = turn + wp.quat(spin[0], spin[1], spin[2], 0.0) * turn * (
    0.5 * step)
  turns[b] = wp.normalize(turned)


#  Asger's box (user, 2026-11-17: "Could we just give Asger the minecraft
#  implementation of some blocks or whatever rather than just a few
#  balls?"; "those movements were janky af"; "and make me able to
#  crouch!"; '_crewman'): half its width, its height standing and
#  crouched, its middle over its soles, the most it steps up onto, how
#  far off what it rests on it keeps, m; the most a part of a frame moves
#  it, m; how many times a move is pushed out of what it is in; how many
#  levels up its sides it looks for walls (and three a side round each);
#  a meeting's normal up its 'up' past 'FLOORED' stands on it.
BOX_HALF = _single(crew.WIDE * 0.5)
#  His mass, kg (what his meetings push the vessel back by: 'walked').
ASGER_HEFT = _single(crew.HEFT)
BOX_TALL = _single(crew.TALL)
BOX_LOW = _single(crew.LOW)
BOX_MIDDLE = _single(crew.MIDDLE)
STEP_UP = _single(crew.STEP)
GAP = _single(0.001)
MOVE_MOST = _single(0.08)
ITERATIONS = 5
LEVELS = 9
FLOORED = _single(0.6)
#  His legs walk him only while what he stands on is within this of his
#  up (a cosine: 45 deg, '_crewman.FALLEN'; leant further, knocked down,
#  they cannot push him along it: he lies on it till he gets up).
LEGS_UPRIGHT = _single(0.7)
#  How far up is no way out ('upOnto').
BLOCKED = _single(1.0e9)
#  His body turns (user, 2026-11-18: "You Spin me Round (Like a Record)": a
#  knock off his middle twists him): his moments across his up and along it,
#  kg m² ('_crewman.MOMENTS'); what he meets pushes him where it meets him
#  (his points pressed on a room's face, on the average; on a solid, those in
#  it), each meeting never pulling and set against the others 'PASSES' times
#  over (Gauss and Seidel's way), rubbing at most 'RUB' of its push (cloth or
#  a shoe on a floor or a wall). While his legs hold him on what he stands
#  on, they are his grip (nothing rubs) and they keep his feet under him:
#  what he stands on holds him up through his middle (no tipping off a
#  stair's edge); whatever else meets him, his legs too, turns him (user,
#  2026-11-18: "if you hit Asgers legs like that he should start spinning").
#  His point within 'PRESSED' of a face presses on it, within 'PATCH' of a
#  solid it touches it, m; a room's faces whose normals are within
#  'SAME_FACE' (a cosine) are one meeting; at most 'MEETINGS_MOST' meetings a
#  part, each 'MEET_ROWS' rows in 'meets' (its points summed, then their
#  middle; its normal; how fast what it meets moves there; the push it gave
#  him so far; how many points).
MOMENT_ACROSS = _single(crew.MOMENTS[0])
MOMENT_ALONG = _single(crew.MOMENTS[2])
PASSES = 4
RUB = _single(0.5)
PRESSED = _single(0.004)
PATCH = _single(0.006)
SAME_FACE = _single(0.95)
MEETINGS_MOST = 16
MEET_ROWS = 5
#  The most solids near him a frame ('nearby': his box looks at those
#  alone; a GPU thread reading all four hundred each time it looked took
#  18 ms a frame walking).
NEAR_MOST = 64
#  A face's axis is taken over an edge's when the edge's is not shallower
#  by this much, m (an edge's axis grazing a box's side would push him
#  up or aside where its face should).
EDGE_BIAS = _single(0.003)


@wp.func
def boxAxes(up: wp.vec3) -> wp.mat33:
  """Returns his box's axes as columns: across (from a fixed way: the
  vessel's z, or its x when his up is near it), across that, up."""
  ref = wp.vec3(0.0, 0.0, 1.0)
  if wp.abs(up[2]) > 0.9:
    ref = wp.vec3(1.0, 0.0, 0.0)
  a = wp.normalize(ref - wp.dot(ref, up) * up)
  b = wp.cross(up, a)
  return wp.mat33(a[0], b[0], up[0], a[1], b[1], up[1], a[2], b[2], up[2])


@wp.func
def spanOf(axis: wp.vec3, e0: wp.vec3, e1: wp.vec3, e2: wp.vec3,
           half: wp.vec3) -> float:
  """Returns how far a box (its axes 'e0' 'e1' 'e2', 'half' its size)
  reaches either way along 'axis' from its middle."""
  return (half[0] * wp.abs(wp.dot(e0, axis)) + half[1] * wp.abs(wp.dot(
    e1, axis)) + half[2] * wp.abs(wp.dot(e2, axis)))


@wp.func
def axisTried(best: wp.vec4, axis: wp.vec3, apart: wp.vec3, a0: wp.vec3,
              a1: wp.vec3, a2: wp.vec3, ha: wp.vec3, b0: wp.vec3,
              b1: wp.vec3, b2: wp.vec3, hb: wp.vec3,
              bias: float) -> wp.vec4:
  """Returns 'best' or the two boxes' overlap along 'axis' if shallower
  ('bias' added in the weighing): the way out (from box b toward box a)
  and how deep (below nought: apart)."""
  along = wp.dot(apart, axis)
  overlap = (spanOf(axis, a0, a1, a2, ha) + spanOf(axis, b0, b1, b2, hb)
             - wp.abs(along))
  if overlap + bias < best[3]:
    side = float(1.0)
    if along < 0.0:
      side = -1.0
    return wp.vec4(side * axis[0], side * axis[1], side * axis[2], overlap)
  return best


@wp.func
def edgeTried(best: wp.vec4, one: wp.vec3, two: wp.vec3, apart: wp.vec3,
              a0: wp.vec3, a1: wp.vec3, a2: wp.vec3, ha: wp.vec3,
              b0: wp.vec3, b1: wp.vec3, b2: wp.vec3,
              hb: wp.vec3) -> wp.vec4:
  """Returns 'best' or the overlap across edges 'one' and 'two' (their
  cross) if shallower by more than 'EDGE_BIAS'."""
  axis = wp.cross(one, two)
  size = wp.length(axis)
  if size < 1.0e-4:
    return best
  return axisTried(best, axis / size, apart, a0, a1, a2, ha, b0, b1, b2, hb,
                   EDGE_BIAS)


@wp.func
def boxApart(ca: wp.vec3, axes: wp.mat33, ha: wp.vec3, cb: wp.vec3,
             turn: wp.quat, hb: wp.vec3) -> wp.vec4:
  """Returns how deep box a ('ca', its 'axes' as columns, 'ha') is in box
  b ('cb', 'turn', 'hb') and the way out of it (separating axes: the
  shallowest overlap of the fifteen; below nought: apart at least so
  far)."""
  a0 = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  a1 = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  a2 = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  b0 = wp.quat_rotate(turn, wp.vec3(1.0, 0.0, 0.0))
  b1 = wp.quat_rotate(turn, wp.vec3(0.0, 1.0, 0.0))
  b2 = wp.quat_rotate(turn, wp.vec3(0.0, 0.0, 1.0))
  apart = ca - cb
  best = wp.vec4(0.0, 0.0, 1.0, 1.0e9)
  best = axisTried(best, a0, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, a1, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, a2, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = edgeTried(best, a0, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a0, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a0, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a1, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a1, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a1, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a2, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a2, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a2, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  return best


@wp.func
def liftTried(least: float, axis: wp.vec3, apart: wp.vec3, a0: wp.vec3,
              a1: wp.vec3, a2: wp.vec3, ha: wp.vec3, b0: wp.vec3,
              b1: wp.vec3, b2: wp.vec3, hb: wp.vec3,
              up: wp.vec3) -> float:
  """Returns 'least' or how far box a must go along 'up' to come apart
  from box b along 'axis' if less (nought: apart along it already)."""
  along = wp.dot(apart, axis)
  overlap = (spanOf(axis, a0, a1, a2, ha) + spanOf(axis, b0, b1, b2, hb)
             - wp.abs(along))
  if overlap <= 0.0:
    return 0.0
  side = float(1.0)
  if along < 0.0:
    side = -1.0
  going = side * wp.dot(up, axis)
  if going > 1.0e-4:
    return wp.min(least, overlap / going)
  return least


@wp.func
def liftEdge(least: float, one: wp.vec3, two: wp.vec3, apart: wp.vec3,
             a0: wp.vec3, a1: wp.vec3, a2: wp.vec3, ha: wp.vec3,
             b0: wp.vec3, b1: wp.vec3, b2: wp.vec3, hb: wp.vec3,
             up: wp.vec3) -> float:
  """Returns 'least' or the lift across edges 'one' and 'two'."""
  axis = wp.cross(one, two)
  size = wp.length(axis)
  if size < 1.0e-4:
    return least
  return liftTried(least, axis / size, apart, a0, a1, a2, ha, b0, b1, b2,
                   hb, up)


@wp.func
def liftApart(ca: wp.vec3, axes: wp.mat33, ha: wp.vec3, cb: wp.vec3,
              turn: wp.quat, hb: wp.vec3) -> float:
  """Returns how far box a ('ca', its 'axes' as columns, its up the
  third; 'ha') must go up to be clear of box b ('cb', 'turn', 'hb'):
  the least along any of the separating axes ('BLOCKED': going up never
  parts them)."""
  a0 = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  a1 = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  a2 = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  b0 = wp.quat_rotate(turn, wp.vec3(1.0, 0.0, 0.0))
  b1 = wp.quat_rotate(turn, wp.vec3(0.0, 1.0, 0.0))
  b2 = wp.quat_rotate(turn, wp.vec3(0.0, 0.0, 1.0))
  apart = ca - cb
  least = BLOCKED
  least = liftTried(least, a0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, a1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, a2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a0, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a0, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a0, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a1, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a1, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a1, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a2, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a2, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a2, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  return least


@wp.func
def samplePoint(soles: wp.vec3, axes: wp.mat33, high: float, level: int,
                i: int, j: int) -> wp.vec3:
  """Returns where one of the points looked at round his box is: on
  'level' up it (of 'LEVELS'), 'i' and 'j' across (each of -1, 0, 1)."""
  a = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  b = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  h = high * float(level) / float(LEVELS - 1)
  return (soles + h * up + BOX_HALF * float(i) * a
          + BOX_HALF * float(j) * b)


@wp.func
def sampled(level: int, i: int, j: int) -> int:
  """Returns whether that point is looked at: round the sides on every
  level, the middles of the foot and the top too."""
  if i == 0 and j == 0 and level > 0 and level < LEVELS - 1:
    return 0
  return 1


@wp.func
def deepestIn(soles: wp.vec3, axes: wp.mat33, high: float, t: float,
              own: int, docked: int, outside: int,
              layout: wp.array(dtype=wp.vec3),
              solidMiddles: wp.array(dtype=wp.vec3),
              solidTurns: wp.array(dtype=wp.quat),
              solidHalves: wp.array(dtype=wp.vec3),
              solidVelocities: wp.array(dtype=wp.vec3),
              near: wp.array(dtype=wp.int32), count: int) -> wp.vec4:
  """Returns how deep his box (its soles at 'soles', 'high') is in what
  it meets at 't' s into the frame (the rooms' walls at its points, the
  solids, but his own, 'own') at the deepest, and the way out of it
  (depth below nought: in nothing)."""
  best = wp.vec4(0.0, 0.0, 1.0, -1.0e9)
  for level in range(LEVELS):
    for i in range(-1, 2):
      for j in range(-1, 2):
        if sampled(level, i, j) == 1:
          room = roomGap(samplePoint(soles, axes, high, level, i, j), docked,
                         outside, layout)
          if -room[3] > best[3]:
            best = wp.vec4(room[0], room[1], room[2], -room[3])
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  middle = soles + 0.5 * high * up
  half = wp.vec3(BOX_HALF, BOX_HALF, 0.5 * high)
  for m in range(count):
    k = near[m]
    there = solidMiddles[k] + solidVelocities[k] * t
    reach = wp.length(solidHalves[k]) + wp.length(half)
    if wp.length(middle - there) < reach:
      met = boxApart(middle, axes, half, there, solidTurns[k],
                     solidHalves[k])
      if met[3] > best[3]:
        best = met
  return best


@wp.func
def pushedOut(soles: wp.vec3, axes: wp.mat33, high: float, t: float,
              own: int, docked: int, outside: int,
              layout: wp.array(dtype=wp.vec3),
              solidMiddles: wp.array(dtype=wp.vec3),
              solidTurns: wp.array(dtype=wp.quat),
              solidHalves: wp.array(dtype=wp.vec3),
              solidVelocities: wp.array(dtype=wp.vec3),
              near: wp.array(dtype=wp.int32), count: int) -> wp.vec3:
  """Returns his box's soles pushed out of what it is in, the deepest
  first, 'ITERATIONS' times at most, each a 'GAP' clear of it."""
  out = soles
  free = int(0)
  for _ in range(ITERATIONS):
    if free == 0:
      met = deepestIn(out, axes, high, t, own, docked, outside, layout,
                      solidMiddles, solidTurns, solidHalves,
                      solidVelocities, near, count)
      if met[3] > 0.0:
        out = out + wp.vec3(met[0], met[1], met[2]) * (met[3] + GAP)
      else:
        free = int(1)
  return out


@wp.func
def turnedBy(up: wp.vec3, twist: wp.vec3) -> wp.vec3:
  """Returns how much faster his body spins for the twist 'twist' (N m
  s), his up 'up': his moments' inverse."""
  along = wp.dot(twist, up)
  return (twist - along * up) / MOMENT_ACROSS + (along / MOMENT_ALONG) * up


@wp.func
def boxGap(point: wp.vec3, middle: wp.vec3, turn: wp.quat,
           half: wp.vec3) -> float:
  """Returns how far 'point' is outside a box ('middle', 'turn',
  'half'), m (below nought: inside it so far)."""
  local = wp.quat_rotate_inv(turn, point - middle)
  qx = wp.abs(local[0]) - half[0]
  qy = wp.abs(local[1]) - half[1]
  qz = wp.abs(local[2]) - half[2]
  out = wp.length(wp.vec3(wp.max(qx, 0.0), wp.max(qy, 0.0),
                          wp.max(qz, 0.0)))
  return out + wp.min(wp.max(qx, wp.max(qy, qz)), 0.0)


@wp.func
def patchOf(soles: wp.vec3, axes: wp.mat33, high: float, centre: wp.vec3,
            half: wp.vec3, there: wp.vec3, turn: wp.quat,
            hb: wp.vec3) -> wp.vec3:
  """Returns where his box (its soles at 'soles', 'high'; its middle
  'centre', 'half') meets a solid ('there', 'turn', 'hb'): the middle
  of his points touching it ('PATCH'); none touching it (an edge of it
  between them), the point of his box nearest its middle."""
  total = wp.vec3(0.0, 0.0, 0.0)
  count = float(0.0)
  for level in range(LEVELS):
    for i in range(-1, 2):
      for j in range(-1, 2):
        if sampled(level, i, j) == 1:
          point = samplePoint(soles, axes, high, level, i, j)
          if boxGap(point, there, turn, hb) < PATCH:
            total = total + point
            count = count + 1.0
  if count > 0.5:
    return total / count
  a = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  b = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  off = there - centre
  return (centre + wp.clamp(wp.dot(off, a), -half[0], half[0]) * a
          + wp.clamp(wp.dot(off, b), -half[1], half[1]) * b
          + wp.clamp(wp.dot(off, up), -half[2], half[2]) * up)


@wp.func
def roomMet(meets: wp.array(dtype=wp.vec3),
            owners: wp.array(dtype=wp.int32), count: int, point: wp.vec3,
            normal: wp.vec3, owner: int) -> int:
  """Adds his point 'point' pressed on a room's face ('normal', the
  rocket's or the pad's: 'owner', 'ROCKET_FACE' or 'PAD_FACE') to that
  face's meeting (one of the same owner's whose normal is within
  'SAME_FACE' of it), or a new one; returns how many meetings there are
  then."""
  found = int(-1)
  for c in range(count):
    if found < 0 and owners[c] == owner:
      if wp.dot(meets[MEET_ROWS * c + 1], normal) > SAME_FACE:
        found = c
  out = int(count)
  if found < 0:
    if out >= MEETINGS_MOST:
      return out
    found = out
    out = out + 1
    zero = wp.vec3(0.0, 0.0, 0.0)
    meets[MEET_ROWS * found] = zero
    meets[MEET_ROWS * found + 1] = normal
    meets[MEET_ROWS * found + 2] = zero
    meets[MEET_ROWS * found + 3] = zero
    meets[MEET_ROWS * found + 4] = zero
    owners[found] = owner
  meets[MEET_ROWS * found] = meets[MEET_ROWS * found] + point
  meets[MEET_ROWS * found + 4] = meets[MEET_ROWS * found + 4] + wp.vec3(
    1.0, 0.0, 0.0)
  return out


@wp.func
def solidMet(meets: wp.array(dtype=wp.vec3),
             owners: wp.array(dtype=wp.int32), count: int, point: wp.vec3,
             normal: wp.vec3, moving: wp.vec3, solid: int) -> int:
  """Adds his meeting with solid 'solid' (where: 'point', its way out:
  'normal', how fast it moves: 'moving'); returns how many meetings
  there are then."""
  if count >= MEETINGS_MOST:
    return count
  meets[MEET_ROWS * count] = point
  meets[MEET_ROWS * count + 1] = normal
  meets[MEET_ROWS * count + 2] = moving
  meets[MEET_ROWS * count + 3] = wp.vec3(0.0, 0.0, 0.0)
  meets[MEET_ROWS * count + 4] = wp.vec3(1.0, 0.0, 0.0)
  owners[count] = solid
  return count + 1


@wp.func
def upOnto(soles: wp.vec3, axes: wp.mat33, high: float, t: float, own: int,
           docked: int, outside: int, layout: wp.array(dtype=wp.vec3),
           solidMiddles: wp.array(dtype=wp.vec3),
           solidTurns: wp.array(dtype=wp.quat),
           solidHalves: wp.array(dtype=wp.vec3),
           solidVelocities: wp.array(dtype=wp.vec3),
           near: wp.array(dtype=wp.int32), count: int) -> float:
  """Returns how far up his box (its soles at 'soles') must go to stand
  clear on what it is in (nought: in nothing); 'BLOCKED' when that is
  no way out: a wall, or what is higher than 'STEP_UP' over its soles
  (lowered onto a step, it is set on the step's top, never pushed off
  its edge)."""
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  need = float(0.0)
  for level in range(LEVELS):
    for i in range(-1, 2):
      for j in range(-1, 2):
        if sampled(level, i, j) == 1:
          room = roomGap(samplePoint(soles, axes, high, level, i, j), docked,
                         outside, layout)
          if room[3] < 0.0:
            lean = wp.dot(wp.vec3(room[0], room[1], room[2]), up)
            if lean > 0.3:
              need = wp.max(need, -room[3] / lean)
            else:
              need = BLOCKED
  middle = soles + 0.5 * high * up
  half = wp.vec3(BOX_HALF, BOX_HALF, 0.5 * high)
  for m in range(count):
    k = near[m]
    there = solidMiddles[k] + solidVelocities[k] * t
    reach = wp.length(solidHalves[k]) + wp.length(half)
    if wp.length(middle - there) < reach:
      lift = liftApart(middle, axes, half, there, solidTurns[k],
                       solidHalves[k])
      if lift > STEP_UP + 0.01:
        need = BLOCKED
      else:
        need = wp.max(need, lift)
  return need


@wp.kernel
def nearby(solidMiddles: wp.array(dtype=wp.vec3),
           solidHalves: wp.array(dtype=wp.vec3),
           solidVelocities: wp.array(dtype=wp.vec3),
           place: wp.array(dtype=wp.vec3),
           near: wp.array(dtype=wp.int32),
           nearCount: wp.array(dtype=wp.int32), up: wp.vec3,
           margin: float, own: int, seconds: float):
  """Lists the solids (a thread a solid) his box may meet this frame
  ('place': his soles; 'margin': how far he may go in it, m; the solid
  as far as it moves in 'seconds'): at most 'NEAR_MOST', in 'near', how
  many in 'nearCount' ('walked' looks at those alone, and empties it)."""
  k = wp.tid()
  if k == own:
    return
  middle = place[0] + 0.5 * BOX_TALL * wp.normalize(up)
  reach = (wp.length(solidHalves[k]) + 0.5 * BOX_TALL + 2.0 * BOX_HALF
           + margin + wp.length(solidVelocities[k]) * seconds)
  if wp.length(solidMiddles[k] - middle) < reach:
    slot = wp.atomic_add(nearCount, 0, 1)
    if slot < NEAR_MOST:
      near[slot] = k


@wp.kernel
def walked(place: wp.array(dtype=wp.vec3),
           velocity: wp.array(dtype=wp.vec3),
           ground: wp.array(dtype=wp.vec3),
           contact: wp.array(dtype=wp.vec3),
           met: wp.array(dtype=wp.vec3),
           thuds: wp.array(dtype=wp.float32),
           solidMiddles: wp.array(dtype=wp.vec3),
           solidTurns: wp.array(dtype=wp.quat),
           solidHalves: wp.array(dtype=wp.vec3),
           solidVelocities: wp.array(dtype=wp.vec3),
           layout: wp.array(dtype=wp.vec3),
           near: wp.array(dtype=wp.int32),
           nearCount: wp.array(dtype=wp.int32),
           reaction: wp.array(dtype=wp.vec3),
           turned: wp.array(dtype=wp.vec3),
           solidPushes: wp.array(dtype=wp.vec3),
           solidMoments: wp.array(dtype=wp.vec3),
           meets: wp.array(dtype=wp.vec3),
           owners: wp.array(dtype=wp.int32),
           felt: wp.vec3, turning: wp.vec3, speeding: wp.vec3,
           wanted: wp.vec3, leap: wp.vec3, up: wp.vec3, was: wp.vec3,
           spin: wp.vec3, walking: int, wanting: int, gun: wp.vec3,
           jet: wp.vec3, crouch: int, docked: int, outside: int, own: int,
           seconds: float):
  """Moves Asger's box a frame ('seconds' s) on, one thread: what is
  felt there moves it (as a loose thing: 'felt', 'turning', 'speeding'),
  his legs while he stands upright on his feet ('LEGS_UPRIGHT';
  'wanted', 'walking', 'wanting',
  a 'leap' once: as against what he stands on, 'ground' its velocity,
  kept from frame to frame: the user's let's play, 2026-11-18, standing
  on the side of an elevator's cage running 30 m/s out his legs held him
  still to the station, the cage's roof and floor beat him to death;
  weightless, pushing off what he touches), the Grav-Gun's field or
  pulse ('gun': its force on him over his mass, m/s², '_gravgun'), his
  jetpack ('jet': likewise, '_jetpack'); in parts of the frame no
  longer than 'MOVE_MOST', first along his up, then across, each pushed
  out of what it meets ('pushedOut'), his box upright along 'up'
  (Minecraft's way); walking, it steps up onto what is no higher than
  'STEP_UP' and keeps to the ground going down (a ledge deeper than
  that: he falls; crouched ('crouch'), he stops at it). It stands up
  again only with room overhead. His body turns about its middle
  ('BOX_MIDDLE' over his soles: 'was' his up as the last frame left
  him, 'up' as the host turned him since) and spins 'spin' (rad/s):
  what he meets pushes him where it meets him (user, 2026-11-18: "You
  Spin me Round (Like a Record)"; 'MOMENT_ACROSS'), so a knock off his
  middle twists him as well as stopping him, and what he stands on
  holds him up where it holds him (off its edge, he topples). Its
  place, velocity, what it touches ('contact': touching, standing on
  something (two: upright), crouched; 'met' 0: how many meetings, how
  far it stepped up, the fastest it met anything; 1: their normals
  summed; 2: those it stands on's) back for the host ('place': his
  soles); his spin ('turned' 0) and the twist his meetings gave him
  over the frame ('turned' 1, N m s), the solid he stands on ('turned'
  2: its slot and one, nought none, kept from frame to frame); the
  thuds; its box into
  the solids' slot 'own'
  (moving as it does through the frame) for the loose things. Whatever
  really changed his speed and spin (his legs on what he stands on, the
  leap, what he met, the gun, the jetpack's and the air's pushes: all
  but what the vessel's own moving makes him feel) pushes the vessel
  back as hard ('reaction' 0: the push, N s; 1: its twist about the
  vessel's middle, N m s, his legs' at his middle, a meeting's where it
  met him; the vessel's own axes); what of that a solid took (his
  meetings with it, his legs and leap on it standing on it) is in
  'solidPushes' (N s) and 'solidMoments' (its twist about the world's
  middle, N m s), summed (the host's to empty) for the host to push
  what moves the solid (an elevator's cage, the door, the walkway, the
  rocket's legs) by; what the rooms' faces took, after the solids: 'own'
  + 1 the rocket's faces', + 2 the pad's ('roomOwner')."""
  v = velocity[0]
  w = spin
  under = ground[0]
  up = wp.normalize(up)
  axes = boxAxes(up)
  soles = place[0]
  if wp.length(was) > 0.5:
    soles = soles + BOX_MIDDLE * (wp.normalize(was) - up)
  known = wp.min(nearCount[0], NEAR_MOST)
  nearCount[0] = 0
  touching = int(0)
  pressing = int(0)
  grounded = int(0)
  upright = int(0)
  crouched = int(0)
  standing = int(turned[2][0] + 0.5) - 1
  if contact[0][0] > 0.5:
    touching = int(1)
  if contact[0][0] > 1.5:
    pressing = int(1)
  if contact[0][1] > 0.5:
    grounded = int(1)
  if contact[0][1] > 1.5:
    upright = int(1)
  if contact[0][2] > 0.5:
    crouched = int(1)
  if crouch == 1:
    crouched = int(1)
  elif crouched == 1:
    risen = deepestIn(soles, axes, BOX_TALL, 0.0, own, docked, outside,
                      layout, solidMiddles, solidTurns, solidHalves,
                      solidVelocities, near, known)
    if risen[3] <= 0.0:
      crouched = int(0)
  high = BOX_TALL
  if crouched == 1:
    high = BOX_LOW
  start = soles + 0.5 * high * up
  half = wp.vec3(BOX_HALF, BOX_HALF, 0.5 * high)
  solidMiddles[own] = start
  solidTurns[own] = wp.quat_from_matrix(axes)
  solidHalves[own] = half
  count = int(wp.ceil(seconds * (wp.length(v) + 2.0) / MOVE_MOST))
  count = wp.clamp(count, 1, 24)
  dt = seconds / float(count)
  rose = float(0.0)
  landing = float(0.0)
  hardest = float(0.0)
  normals = wp.vec3(0.0, 0.0, 0.0)
  floors = wp.vec3(0.0, 0.0, 0.0)
  meetings = int(0)
  pushedBack = wp.vec3(0.0, 0.0, 0.0)
  twistedBack = wp.vec3(0.0, 0.0, 0.0)
  twisted = wp.vec3(0.0, 0.0, 0.0)
  for k in range(count):
    t = float(k + 1) * dt
    body = soles + BOX_MIDDLE * up
    feel = (-felt - wp.cross(turning, wp.cross(turning, body))
            - 2.0 * wp.cross(turning, v) - wp.cross(speeding, body))
    framed = feel
    began = v
    footing = wp.vec3(0.0, 0.0, 0.0)
    if k == 0 and touching == 1:
      v = v + leap
      footing = footing + ASGER_HEFT * leap
    feel = feel + gun + jet
    gripping = int(0)
    if touching == 1:
      rel = v - under
      legs = (wanted - rel) / LEGS_TIME
      if walking == 1:
        along = rel - wp.dot(rel, up) * up
        legs = (wanted - along) / LEGS_TIME
      size = wp.length(legs)
      if size > LEGS_MOST:
        legs = legs * (LEGS_MOST / size)
      if (walking == 1 and upright == 1) or (walking == 0
                                             and wanting == 1):
        feel = feel + legs
        footing = footing + ASGER_HEFT * dt * legs
        gripping = upright
    if standing >= 0:
      solidPushes[standing] = solidPushes[standing] - footing
      solidMoments[standing] = solidMoments[standing] - wp.cross(
        body, footing)
    v = v + (feel - ASGER_DRAG * wp.length(v) * v) * dt
    meeting = v
    move = v * dt
    rise = wp.dot(move, up) * up
    across = move - rise
    p = soles + rise
    settled = int(0)
    if wp.dot(rise, up) < 0.0:
      onto = upOnto(p, axes, high, t, own, docked, outside, layout,
                    solidMiddles, solidTurns, solidHalves, solidVelocities,
                    near, known)
      if onto < BLOCKED:
        settled = int(1)
        if onto > 0.0:
          p = p + (onto + GAP) * up
    if settled == 0:
      p = pushedOut(p, axes, high, t, own, docked, outside, layout,
                    solidMiddles, solidTurns, solidHalves, solidVelocities,
                    near, known)
    before = p
    p = pushedOut(before + across, axes, high, t, own, docked, outside,
                  layout, solidMiddles, solidTurns, solidHalves,
                  solidVelocities, near, known)
    wide = wp.length(across)
    onFoot = int(0)
    if upright == 1 and walking == 1 and wp.dot(v, up) < 0.5:
      onFoot = int(1)
    if onFoot == 1 and wide > 1.0e-6:
      way = across / wide
      gone = wp.dot(p - before, way)
      if gone < 0.95 * wide - 1.0e-4:
        raised = pushedOut(before + STEP_UP * up, axes, high, t, own,
                           docked, outside, layout, solidMiddles, solidTurns,
                           solidHalves, solidVelocities, near, known)
        lift = wp.dot(raised - before, up)
        ahead = pushedOut(raised + across, axes, high, t, own, docked,
                          outside, layout, solidMiddles, solidTurns,
                          solidHalves, solidVelocities, near, known)
        lowered = ahead - (lift + 0.002) * up
        onto = upOnto(lowered, axes, high, t, own, docked, outside, layout,
                      solidMiddles, solidTurns, solidHalves,
                      solidVelocities, near, known)
        if onto < BLOCKED:
          down = lowered + (onto + GAP) * up
          climbed = wp.dot(down - before, up)
          if wp.dot(down - before, way) > gone + 0.002 and climbed > 0.002:
            p = down
            rose = rose + climbed
    if onFoot == 1:
      dropped = p - STEP_UP * up
      onto = upOnto(dropped, axes, high, t, own, docked, outside, layout,
                    solidMiddles, solidTurns, solidHalves, solidVelocities,
                    near, known)
      if onto < BLOCKED and onto > 0.003:
        p = dropped + (onto + GAP) * up
      elif onto <= 0.003 and crouched == 1:
        p = before
        v = wp.dot(v, up) * up
    soles = p
    core = soles + BOX_MIDDLE * up
    middle = soles + 0.5 * high * up
    wasPressing = pressing
    touching = int(0)
    pressing = int(0)
    grounded = int(0)
    upright = int(0)
    standing = int(-1)
    closing = float(0.0)
    floorMost = float(-2.0)
    beneath = wp.vec3(0.0, 0.0, 0.0)
    held = int(0)
    for level in range(LEVELS):
      for i in range(-1, 2):
        for j in range(-1, 2):
          if sampled(level, i, j) == 1:
            point = samplePoint(soles, axes, high, level, i, j)
            room = roomGap(point, docked, outside, layout)
            if room[3] < NEAR:
              normal = wp.vec3(room[0], room[1], room[2])
              touching = int(1)
              meetings = meetings + 1
              normals = normals + normal
              face = roomOwner(point, docked, outside, layout)
              if wp.dot(normal, up) > floorMost:
                floorMost = wp.dot(normal, up)
                beneath = wp.vec3(0.0, 0.0, 0.0)
                standing = own + 1
                if face == PAD_FACE:
                  standing = own + 2
              if wp.dot(normal, up) > FLOORED:
                grounded = int(1)
                floors = floors + normal
              if room[3] < PRESSED:
                pressing = int(1)
                closing = wp.max(closing, -wp.dot(
                  meeting + wp.cross(w, point - core), normal))
                held = roomMet(meets, owners, held, point, normal, face)
    for c in range(held):
      meets[MEET_ROWS * c] = meets[MEET_ROWS * c] / meets[
        MEET_ROWS * c + 4][0]
    for m in range(known):
      n = near[m]
      if n != own:
        there = solidMiddles[n] + solidVelocities[n] * t
        reach = wp.length(solidHalves[n]) + wp.length(half) + NEAR
        if wp.length(middle - there) < reach:
          box = boxApart(middle, axes, half, there, solidTurns[n],
                         solidHalves[n])
          if box[3] > -NEAR:
            normal = wp.vec3(box[0], box[1], box[2])
            touching = int(1)
            meetings = meetings + 1
            normals = normals + normal
            if wp.dot(normal, up) > floorMost:
              floorMost = wp.dot(normal, up)
              beneath = solidVelocities[n]
              standing = n
            if wp.dot(normal, up) > FLOORED:
              grounded = int(1)
              floors = floors + normal
            turn = solidTurns[n]
            hb = solidHalves[n]
            top = wp.dot(there - soles, up) + spanOf(up, wp.quat_rotate(
              turn, wp.vec3(1.0, 0.0, 0.0)), wp.quat_rotate(turn, wp.vec3(
                0.0, 1.0, 0.0)), wp.quat_rotate(turn, wp.vec3(0.0, 0.0,
                                                              1.0)), hb)
            foot = top - 2.0 * spanOf(up, wp.quat_rotate(turn, wp.vec3(
              1.0, 0.0, 0.0)), wp.quat_rotate(turn, wp.vec3(0.0, 1.0, 0.0)),
                                      wp.quat_rotate(turn, wp.vec3(
                                        0.0, 0.0, 1.0)), hb)
            step = int(0)
            if (onFoot == 1 and wp.abs(wp.dot(normal, up)) < 0.3
                and top > 0.005 and top <= STEP_UP + 0.01
                and foot < 0.005):
              step = int(1)
            if box[3] > -PRESSED and step == 0:
              pressing = int(1)
              point = patchOf(soles, axes, high, middle, half, there,
                              turn, hb)
              closing = wp.max(closing, -wp.dot(
                meeting + wp.cross(w, point - core) - solidVelocities[n],
                normal))
              held = solidMet(meets, owners, held, point, normal,
                              solidVelocities[n], n)
    if gripping == 1:
      for c in range(held):
        if wp.dot(meets[MEET_ROWS * c + 1], up) > FLOORED:
          meets[MEET_ROWS * c] = core - BOX_MIDDLE * meets[
            MEET_ROWS * c + 1]
    for _ in range(PASSES):
      for c in range(held):
        point = meets[MEET_ROWS * c]
        normal = meets[MEET_ROWS * c + 1]
        moving = meets[MEET_ROWS * c + 2]
        given = meets[MEET_ROWS * c + 3]
        arm = point - core
        u = v + wp.cross(w, arm) - moving
        lever = wp.cross(arm, normal)
        give = 1.0 / ASGER_HEFT + wp.dot(lever, turnedBy(up, lever))
        old = wp.dot(given, normal)
        fresh = wp.max(old - wp.dot(u, normal) / give, 0.0)
        push = (fresh - old) * normal
        v = v + push / ASGER_HEFT
        w = w + turnedBy(up, wp.cross(arm, push))
        given = given + push
        if gripping == 0:
          u = v + wp.cross(w, arm) - moving
          slide = u - wp.dot(u, normal) * normal
          speed = wp.length(slide)
          if speed > 1.0e-6:
            way = slide / speed
            lever = wp.cross(arm, way)
            give = 1.0 / ASGER_HEFT + wp.dot(lever, turnedBy(up, lever))
            rubbed = given - wp.dot(given, normal) * normal
            wish = rubbed - (speed / give) * way
            most = RUB * wp.dot(given, normal)
            size = wp.length(wish)
            if size > most:
              wish = wish * (most / size)
            push = wish - rubbed
            v = v + push / ASGER_HEFT
            w = w + turnedBy(up, wp.cross(arm, push))
            given = given + push
        meets[MEET_ROWS * c + 3] = given
    offMiddle = wp.vec3(0.0, 0.0, 0.0)
    for c in range(held):
      point = meets[MEET_ROWS * c]
      given = meets[MEET_ROWS * c + 3]
      offMiddle = offMiddle + wp.cross(point - core, given)
      solid = owners[c]
      if solid == ROCKET_FACE:
        solid = own + 1
      elif solid == PAD_FACE:
        solid = own + 2
      solidPushes[solid] = solidPushes[solid] - given
      solidMoments[solid] = solidMoments[solid] - wp.cross(point, given)
    twisted = twisted + offMiddle
    if floorMost > LEGS_UPRIGHT:
      upright = grounded
    if touching == 1:
      under = beneath
    if wasPressing == 0:
      hardest = wp.max(hardest, closing)
      landing = wp.max(landing, closing)
    elif closing > THUD + (LEGS_MOST + wp.length(framed)) * dt:
      hardest = wp.max(hardest, closing)
    really = ASGER_HEFT * ((v - began) - framed * dt)
    pushedBack = pushedBack - really
    twistedBack = twistedBack - wp.cross(body, really) - offMiddle
  wp.atomic_add(reaction, 0, pushedBack)
  wp.atomic_add(reaction, 1, twistedBack)
  if hardest > THUD:
    wp.atomic_add(thuds, 0, 1.0)
    wp.atomic_max(thuds, 1, hardest)
  place[0] = soles
  velocity[0] = v
  ground[0] = under
  turned[0] = w
  turned[1] = twisted
  turned[2] = wp.vec3(float(standing + 1), 0.0, 0.0)
  solidVelocities[own] = (soles + 0.5 * high * up - start) / seconds
  stood = float(0.0)
  if grounded == 1:
    stood = 1.0 + float(upright)
  touched = float(0.0)
  if pressing == 1:
    touched = 2.0
  elif touching == 1:
    touched = 1.0
  low = float(0.0)
  if crouched == 1:
    low = 1.0
  contact[0] = wp.vec3(touched, stood, low)
  met[0] = wp.vec3(float(meetings), rose, landing)
  met[1] = normals
  met[2] = floors
