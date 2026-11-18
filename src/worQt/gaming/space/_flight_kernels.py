"""
The Warp kernel 'flown' moves vessels through the solar system, one
thread a vessel, a frame's time in one launch, in small steps of its own
(user, 2026-11-16: time warp, "we just put a factor on each step"; the
spec: "the vessel then covers it in as many small steps as it needs").

float32 throughout ('feedback: GPU always'): nothing is far from its
own frame. A vessel is kept from its anchor's middle, in the ecliptic's
axes; its place and velocity each in two float32s, a big part and the
small rest ('pairAdded', exact sums: Knuth's two-sum), so a step's few
metres are never lost against Terra's 6371 km. Its height over the
ground is taken from where it began the call (its height there worked
out by the host), by small differences alone. The sky is the flown
one ('_ephemeris': each body pulling every other, user, 2026-11-18,
"PHYSICS MUST BE REAL"), its states every 'SKY_SPAN' s read from its
table and drawn between them by Hermite's cubic (in 2000 s Luna goes a
quarter of a degree, the cubic misses by under a millimetre), each body
from the body it goes round, a body's place from the anchor summed
along the tree. One thread steps a vessel, its steps one after another.

Each step is Wisdom and Holman's: half a step coasting on the anchor's
pull alone, exactly (Kepler's arc, in universal variables: an ellipse or
a hyperbola alike, 'drifted'), a kick of everything else (every other
body's pull, each step, less its pull on the anchor: the anchor's own
fall; the air, the engine, the legs), half a step coasting again. The
anchor's pull being the arc itself, a step may be a fair share of an
orbit ('KEPLER_SHARE' of the anchor's free fall time: some thirty an
orbit), the other bodies' pulls each want 'ETA' of theirs; the frame's
warp is no more than the count of steps (user: "we just put a factor
on each step"). On the ground ('GROUND_NEAR') the legs want short steps
('GROUND_STEP'). A step longer than 'SNAP_STEP' (time warp) turns the
vessel on rails: its autopilot's aim at once (warp's own, the user's:
"Warp *was* an instructed cheat and is fine as it is"). The anchor's
pull twists a long vessel (its pull on the near end is the stronger:
the gravity gradient), as it twists the space station's wheel.

The space station's solids ('_stationsolids': a torus, cylinders,
capsules in its own axes) meet the hull's balls (user, 2026-11-17: a bad
approach passed straight through the station): the host says which
solids are near ('near', a bit each) and where the station is from the
vessel at the call's start (its middle, velocity, fall, turn and spin:
small numbers, the vessel's own frame); within a step its place is had
from those (its middle moving and falling, its turn spinning), each
ball pressed out of a solid by a stiff spring ('SOLID_OMEGA' for the
vessel's mass), a damper and friction against the solid's own motion
(the ring's rim runs at 94 m/s), the steps short ('CONTACT_STEP'); what
the solids push the vessel by pushes the station back as hard, at the
point they meet ('STRUCK', 'STRUCK_TWIST': the host gives it the
station after the call; it is flown too, '_station').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import warp as wp

from ._ephemeris import SPAN
from ._stationsolids import hullReach
from ._station import REACH as STATION_REACH
from ._vessel import MASS, SAG

wp.config.log_level = wp.LOG_WARNING
wp.set_module_options({'enable_backward': False})


def _single(x: float) -> object:
  """Returns 'x' as a float32 constant of Warp's."""
  return wp.constant(wp.float32(x))


#  A step is at most this share of the anchor's free fall time, sqrt(r³ /
#  G M) (some thirty steps an orbit: its pull is coasted on exactly), and
#  at most 'ETA' of any other body's.
KEPLER_SHARE = _single(0.2)
ETA = _single(1.0 / 512.0)
#  Below this height its legs may touch: steps of at most 'GROUND_STEP'.
GROUND_NEAR = _single(100.0)
GROUND_STEP = _single(1.0 / 240.0)
#  Steps longer than this are time warp: the vessel turns on rails.
SNAP_STEP = _single(0.05)
#  The sky's table has a state this often, s, drawn between by Hermite.
SKY_SPAN = _single(SPAN)
#  The scratch's rows a vessel, each a row of the bodies: the sky now,
#  its place and velocity at a span's start, at its end.
NOW = wp.constant(0)
START_PLACE = wp.constant(1)
START_SPEED = wp.constant(2)
END_PLACE = wp.constant(3)
END_SPEED = wp.constant(4)
SLOTS = 5
#  A vessel's row of 'STATE' numbers, what changes each frame, in and out
#  at once (one copy each way): its place and velocity (big parts and
#  small rests), turn (x y z w), spin (its own axes), height over the
#  ground where the call begins, push (N), the keys on the attitude
#  thrusters, its
#  autopilot's mode and held turn, its anchor, its aim (pitch over the
#  horizon, turn off the path, compass heading, rad; whether it is from
#  the path); out, its legs touching and the steps taken; in again, its
#  docking thrusters' push (N, its own axes: user, 2026-11-17, docking)
#  and the spin its held turn turns at (rad/s, the ecliptic's axes:
#  matching the station's, 'MATCH'); out, what the frame's forces but
#  gravity pushed it a kilogram, on the average over the frame (m/s², its
#  own axes: thrust, drag, the legs on the ground, the thrusters, the
#  station's solids; what anything in it feels: user, 2026-11-17, "there
#  better be a physically simulated such fucking thing every where it
#  needs to be calculated") and how fast its spin changed over it
#  (rad/s², its own axes); what its hull pushed the space station by
#  (N s, the ecliptic's axes) and that push's twist about the station's
#  middle (N m s); in again, whether the station's docking port has
#  caught its nose (one), the port's mouth (the station's own axes), the
#  turn the latch draws it to (its own axes in the station's, x y z w)
#  and its nose (its own axes).
PLACE_HI, PLACE_LO, SPEED_HI, SPEED_LO = 0, 3, 6, 9
TURN, SPIN, HEIGHT, PUSH, STEER = 12, 16, 19, 20, 21
MODE, HELD, ANCHOR = 24, 25, 29
AIM_PITCH, AIM_TURN, AIM_HEADING, AIM_TRAVEL = 30, 31, 32, 33
TOUCHING, STEPS = 34, 35
RCS, MATCH_SPIN = 36, 39
BUMP = 42
FELT, SPINNING = 43, 46
STRUCK, STRUCK_TWIST = 49, 52
LATCHED, LATCH_PORT, LATCH_TURN, LATCH_NOSE = 55, 56, 59, 63
STATE = 66
#  The shortest step, s, and the most a launch takes (a guard).
LEAST_STEP = _single(1e-6)
MOST_STEPS = 4000000
#  A leg on the ground: its spring (N/m: 'SAG' standing), damper (N s/m),
#  sliding damper (N s/m) and its grip (friction's share of the push).
LEG_STIFF = _single(9.82 * MASS / 4.0 / SAG)
LEG_DAMP = _single(3e5 * MASS / 20e3)
LEG_SLIDE = _single(2e5 * MASS / 20e3)
LEG_GRIP = _single(0.8)
#  A ball of the hull pressed into a solid of the station: the spring
#  (the vessel's mass times 'SOLID_OMEGA' squared: some 0.3 s a bounce),
#  the damper ('SOLID_DAMPING' of critical), the sliding damper (N s/m a
#  kg) and the grip; the steps while any solid is near, s. The solids'
#  kinds (the '_stationsolids' ones); a gradient's step, m.
SOLID_OMEGA = _single(10.0)
SOLID_DAMPING = _single(0.3)
SOLID_SLIDE = _single(10.0)
SOLID_GRIP = _single(0.5)
#  The hull reaches this far from the vessel's middle, m (a solid further
#  from it is skipped for the step: on a single GPU thread each test
#  counts).
HULL_REACH = _single(hullReach())
CONTACT_STEP = _single(1.0 / 240.0)
#  Whether the station is near is decided each step where it truly is
#  (on its circle round its planet: user, 2026-11-17, "When I tried to
#  hit the auto docking thing game crashed": warped 100 000 times, a
#  frame of 28 minutes took contact steps throughout, 400 000 of them,
#  the station judged near from the frame's start): within
#  'STATION_CLEAR' m of its middle (its reach, the hull's, a margin) the
#  contact steps; further, the steps no longer than its closing leaves
#  clear. A frame no longer than 'SHORT_FRAME' s has the station's place
#  as it moves from the frame's start (small numbers: mm); a longer, from
#  its circle (big numbers: a metre or so).
STATION_CLEAR = _single(STATION_REACH + hullReach() + 100.0)
SHORT_FRAME = _single(2.0)
TORUS = wp.constant(0)
CYLINDER = wp.constant(1)
GRADIENT_STEP = _single(0.01)
#  A port that has caught a vessel's nose draws it in (user, 2026-11-18:
#  "PHYSICS MUST BE REAL"; it snapped it into place): a spring from its
#  nose to the port's mouth, the vessel's mass times 'LATCH_OMEGA'
#  squared (a pull of some 6 s), damped as critically; a turning spring
#  to the turn it docks at, its moments times 'LATCH_OMEGA' squared,
#  damped likewise; their pushes the station's back.
LATCH_OMEGA = _single(1.0)
#  The autopilot: rad/s wanted a rad off, the fastest it turns (rad/s),
#  and how fast the attitude thrusters take the vessel to the rate wanted
#  (1/s).
RATE_GAIN = _single(0.8)
RATE_MOST = _single(0.6)
TORQUE_GAIN = _single(4.0)
PI = _single(3.14159265358979)
#  The autopilot's modes ('_autopilot.MODES').
HOLD = wp.constant(1)
PROGRADE = wp.constant(2)
RETROGRADE = wp.constant(3)
AIM = wp.constant(4)
MATCH = wp.constant(5)


@wp.struct
class Sky:
  """The heavenly bodies as the kernel has them: each body's parent (-1:
  Sol) and depth under Sol, G M, radius; the flown sky's table ('table':
  a row of 'count' places then 'count' velocities each 'SKY_SPAN' s,
  each body's from its parent, the first at 'tableStart' s, 'tableRows'
  of them); its spin vector; its air (the height it ends at, nought:
  none; its densities' logarithms from 'airStart' in 'airLogs', every
  'airStep' m)."""
  count: int
  parents: wp.array(dtype=wp.int32)
  depths: wp.array(dtype=wp.int32)
  mus: wp.array(dtype=wp.float32)
  radii: wp.array(dtype=wp.float32)
  table: wp.array(dtype=wp.vec3)
  tableStart: float
  tableRows: int
  spins: wp.array(dtype=wp.vec3)
  airTops: wp.array(dtype=wp.float32)
  airStarts: wp.array(dtype=wp.int32)
  airSteps: wp.array(dtype=wp.float32)
  airLogs: wp.array(dtype=wp.float32)


@wp.struct
class Fleet:
  """The vessels as the kernel has them: each one's row of what changes
  ('states', 'STATE' numbers a vessel: see 'PLACE_HI' and on, in and out);
  its mass, moments of inertia, legs (four a vessel), drag (along, across)
  and attitude thrusters' most torques. Scratch: the bodies' places from
  their parents now, and their places and velocities at the span's ends,
  'SLOTS' rows a vessel. The hull's balls (x y z radius, its own axes) and
  the station's solids (kind, from, to, radius: its own axes), all vessels';
  each vessel's near solids ('near', a bit each), and the station from it at
  the call's start: its middle (from the vessel), velocity, fall (its
  anchor's pull), turn (its own axes to the ecliptic's) and spin (rad/s, the
  ecliptic's axes)."""
  states: wp.array2d(dtype=wp.float32)
  masses: wp.array(dtype=wp.float32)
  inertias: wp.array(dtype=wp.vec3)
  legs: wp.array(dtype=wp.vec3)
  drags: wp.array(dtype=wp.vec2)
  attitude: wp.array(dtype=wp.vec3)
  offsets: wp.array(dtype=wp.vec3)
  balls: wp.array(dtype=wp.vec4)
  solidKinds: wp.array(dtype=wp.int32)
  solidFrom: wp.array(dtype=wp.vec3)
  solidTo: wp.array(dtype=wp.vec3)
  solidRadii: wp.array(dtype=wp.float32)
  near: wp.array(dtype=wp.int32)
  solidAt: wp.array(dtype=wp.vec3)
  solidSpeed: wp.array(dtype=wp.vec3)
  solidFall: wp.array(dtype=wp.vec3)
  solidTurn: wp.array(dtype=wp.quat)
  solidSpin: wp.array(dtype=wp.vec3)
  stationAt: wp.array(dtype=wp.vec3)
  stationVel: wp.array(dtype=wp.vec3)


@wp.func
def vecAt(states: wp.array2d(dtype=wp.float32), i: int, c: int) -> wp.vec3:
  """Returns the three numbers of vessel 'i''s row from column 'c'."""
  return wp.vec3(states[i, c], states[i, c + 1], states[i, c + 2])


@wp.func
def quatAt(states: wp.array2d(dtype=wp.float32), i: int,
           c: int) -> wp.quat:
  """Returns the four numbers of vessel 'i''s row from column 'c' as a
  quaternion (x y z w)."""
  return wp.quat(states[i, c], states[i, c + 1], states[i, c + 2],
                 states[i, c + 3])


@wp.func
def vecPut(states: wp.array2d(dtype=wp.float32), i: int, c: int,
           v: wp.vec3) -> int:
  """Puts 'v' in vessel 'i''s row from column 'c'; returns nought."""
  for k in range(3):
    states[i, c + k] = v[k]
  return 0


@wp.func
def pairAdded(hi: wp.vec3, lo: wp.vec3, d: wp.vec3) -> wp.mat33:
  """Returns 'hi' + 'lo' + 'd' as a big part (row 0) and its rest (row
  1), each a component's two-sum carried exactly."""
  out = wp.mat33()
  for k in range(3):
    s = hi[k] + d[k]
    bb = s - hi[k]
    e = (hi[k] - (s - bb)) + (d[k] - bb)
    rest = lo[k] + e
    big = s + rest
    out[0, k] = big
    out[1, k] = rest - (big - s)
  return out


@wp.func
def stumpff(z: float) -> wp.vec2:
  """Returns Stumpff's C(z) and S(z): their series near nought (float32
  keeps its digits there), their closed forms further out."""
  if wp.abs(z) < 1.0:
    c = float(0.0)
    s = float(0.0)
    cTerm = float(0.5)
    sTerm = float(1.0 / 6.0)
    for k in range(8):
      c = c + cTerm
      s = s + sTerm
      cTerm = -cTerm * z / float((2 * k + 3) * (2 * k + 4))
      sTerm = -sTerm * z / float((2 * k + 4) * (2 * k + 5))
    return wp.vec2(c, s)
  if z > 0.0:
    root = wp.sqrt(z)
    return wp.vec2((1.0 - wp.cos(root)) / z,
                   (root - wp.sin(root)) / (z * root))
  root = wp.sqrt(-z)
  return wp.vec2((wp.cosh(root) - 1.0) / (-z),
                 (wp.sinh(root) - root) / (-z * root))


@wp.func
def drifted(r0: wp.vec3, v0: wp.vec3, mu: float, dt: float) -> wp.mat33:
  """Returns how far a body at 'r0' moving at 'v0' goes in 'dt' s pulled
  by a body of G M 'mu' at nought alone (row 0, m) and how its velocity
  changes (row 1, m/s): Kepler's arc in universal variables, its f and
  g less their ones kept small (a step's few metres on 6371 km)."""
  out = wp.mat33()
  r0n = wp.length(r0)
  root = wp.sqrt(mu)
  radial = wp.dot(r0, v0) / r0n
  alpha = 2.0 / r0n - wp.dot(v0, v0) / mu
  chi = root * dt / r0n
  for _ in range(12):
    z = alpha * chi * chi
    cs = stumpff(z)
    chi2 = chi * chi
    lean = r0n * radial / root
    f = lean * chi2 * cs[0] + (1.0 - alpha * r0n) * chi2 * chi * cs[1] \
      + r0n * chi - root * dt
    slope = lean * chi * (1.0 - z * cs[1]) + (1.0 - alpha * r0n) \
      * chi2 * cs[0] + r0n
    chi = chi - f / slope
  z = alpha * chi * chi
  cs = stumpff(z)
  chi2 = chi * chi
  f1 = -chi2 * cs[0] / r0n
  g = dt - chi2 * chi * cs[1] / root
  moved = r0 * f1 + v0 * g
  rn = wp.length(r0 + moved)
  fdot = root / (rn * r0n) * (alpha * chi2 * chi * cs[1] - chi)
  gdot1 = -chi2 * cs[0] / rn
  changed = r0 * fdot + v0 * gdot1
  for j in range(3):
    out[0, j] = moved[j]
    out[1, j] = changed[j]
  return out


@wp.func
def stateOf(sky: Sky, k: int, t: float) -> wp.mat33:
  """Returns where body 'k' is from its parent at time 't' (row 0, m)
  and how fast it moves (row 1, m/s): the table's row at 't' (a time of
  its rows)."""
  out = wp.mat33()
  j = int(wp.round((t - sky.tableStart) / SKY_SPAN))
  j = wp.clamp(j, 0, sky.tableRows - 1)
  place = sky.table[(2 * j) * sky.count + k]
  moving = sky.table[(2 * j + 1) * sky.count + k]
  for c in range(3):
    out[0, c] = place[c]
    out[1, c] = moving[c]
  return out


@wp.func
def skySolved(sky: Sky, fleet: Fleet, base: int, t: float) -> int:
  """Solves the sky at time 't' into the scratch's span end ('base' the
  vessel's first scratch row); returns nought."""
  for k in range(sky.count):
    state = stateOf(sky, k, t)
    fleet.offsets[base + END_PLACE * sky.count + k] = state[0]
    fleet.offsets[base + END_SPEED * sky.count + k] = state[1]
  return 0


@wp.func
def skyShifted(sky: Sky, fleet: Fleet, base: int) -> int:
  """Makes the span's end its start; returns nought."""
  for k in range(sky.count):
    fleet.offsets[base + START_PLACE * sky.count + k] = fleet.offsets[
      base + END_PLACE * sky.count + k]
    fleet.offsets[base + START_SPEED * sky.count + k] = fleet.offsets[
      base + END_SPEED * sky.count + k]
  return 0


@wp.func
def skyDrawn(sky: Sky, fleet: Fleet, base: int, share: float,
             span: float) -> int:
  """Puts each body's place from its parent 'share' of the way through
  a span 'span' s long in the scratch's 'NOW' row (Hermite's cubic);
  returns nought."""
  u = share
  u2 = u * u
  u3 = u2 * u
  h00 = 2.0 * u3 - 3.0 * u2 + 1.0
  h10 = (u3 - 2.0 * u2 + u) * span
  h01 = 3.0 * u2 - 2.0 * u3
  h11 = (u3 - u2) * span
  n = sky.count
  for k in range(n):
    fleet.offsets[base + NOW * n + k] = (
      fleet.offsets[base + START_PLACE * n + k] * h00
      + fleet.offsets[base + START_SPEED * n + k] * h10
      + fleet.offsets[base + END_PLACE * n + k] * h01
      + fleet.offsets[base + END_SPEED * n + k] * h11)
  return 0


@wp.func
def relativeOf(sky: Sky, fleet: Fleet, row: int, body: int,
               to: int) -> wp.vec3:
  """Returns where body 'body' is from body 'to', summed along the tree
  from their nearest common forebear (the places of the bodies from
  their parents in the fleet's scratch 'row')."""
  out = wp.vec3(0.0, 0.0, 0.0)
  a = body
  b = to
  while sky.depths[a] > sky.depths[b]:
    out = out + fleet.offsets[row + a]
    a = sky.parents[a]
  while sky.depths[b] > sky.depths[a]:
    out = out - fleet.offsets[row + b]
    b = sky.parents[b]
  while a != b:
    out = out + fleet.offsets[row + a] - fleet.offsets[row + b]
    a = sky.parents[a]
    b = sky.parents[b]
  return out


@wp.func
def densityAt(sky: Sky, k: int, height: float) -> float:
  """Returns the air's density over body 'k' at 'height', kg/m³."""
  top = sky.airTops[k]
  if top <= 0.0 or height >= top:
    return 0.0
  x = wp.max(height, 0.0) / sky.airSteps[k]
  low = wp.min(int(x), int(top / sky.airSteps[k] + 0.5) - 1)
  share = x - float(low)
  start = sky.airStarts[k]
  one = sky.airLogs[start + low]
  two = sky.airLogs[start + low + 1]
  return wp.exp(one + share * (two - one))


@wp.func
def heightOf(base: wp.vec3, height0: float, radius: float,
             d: wp.vec3) -> float:
  """Returns the height over the ground of a point 'd' from 'base' (the
  vessel's place where the call began, 'height0' m high over a ground
  'radius' m from the middle): by small differences alone."""
  far = wp.length(base + d)
  return height0 + (2.0 * wp.dot(base, d) + wp.dot(d, d)) / (
    far + height0 + radius)


@wp.func
def rotationOf(q: wp.quat) -> wp.vec3:
  """Returns the turn 'q' as a rotation vector (axis times angle,
  rad), the short way round."""
  v = wp.vec3(q[0], q[1], q[2])
  w = q[3]
  if w < 0.0:
    v = -v
    w = -w
  s = wp.length(v)
  if s < 1e-9:
    return 2.0 * v
  return v * (2.0 * wp.atan2(s, w) / s)


@wp.func
def pointing(q: wp.quat, aim: wp.vec3) -> wp.vec3:
  """Returns the rotation vector (the vessel's own axes) taking its
  nose (its own z) to the unit 'aim' (the ecliptic's), about an axis
  across its nose."""
  u = wp.quat_rotate(wp.quat_inverse(q), aim)
  axis = wp.cross(wp.vec3(0.0, 0.0, 1.0), u)
  s = wp.length(axis)
  if s < 1e-7:
    if u[2] > 0.0:
      return wp.vec3(0.0, 0.0, 0.0)
    return wp.vec3(PI, 0.0, 0.0)
  return axis * (wp.atan2(s, u[2]) / s)


@wp.func
def pointed(q: wp.quat, aim: wp.vec3) -> wp.quat:
  """Returns 'q' turned the short way so its nose points along the unit
  'aim' (on rails)."""
  nose = wp.quat_rotate(q, wp.vec3(0.0, 0.0, 1.0))
  c = wp.dot(nose, aim)
  if c < -0.99999:
    side = wp.quat_rotate(q, wp.vec3(1.0, 0.0, 0.0))
    return wp.normalize(wp.mul(wp.quat_from_axis_angle(side, PI), q))
  axis = wp.cross(nose, aim)
  turn = wp.normalize(wp.quat(axis[0], axis[1], axis[2], 1.0 + c))
  return wp.normalize(wp.mul(turn, q))


@wp.func
def aimed(p: wp.vec3, path: wp.vec3, spin: wp.vec3, pitch: float,
          turn: float, heading: float, travel: float) -> wp.vec3:
  """Returns where the aim mode points ('_autopilot.aimOf', line for
  line): 'pitch' over the horizon at 'p', along the path's heading
  ('path' flattened onto the horizon) and 'turn' off it to the right
  when 'travel', else along the compass 'heading' (from north toward
  east; the north of the body turning at 'spin')."""
  up = wp.normalize(p)
  axis = wp.vec3(0.0, 0.0, 1.0)
  if wp.length(spin) > 1e-12:
    axis = wp.normalize(spin)
  east = wp.cross(axis, up)
  if wp.length(east) < 1e-6:
    east = wp.cross(wp.vec3(1.0, 0.0, 0.0), up)
  east = wp.normalize(east)
  north = wp.cross(up, east)
  way = north * wp.cos(heading) + east * wp.sin(heading)
  if travel > 0.5:
    flat = path - up * wp.dot(path, up)
    if wp.length(flat) > 1e-3:
      way = wp.normalize(flat)
  right = wp.cross(way, up)
  level = way * wp.cos(pitch) + up * wp.sin(pitch)
  return wp.normalize(level * wp.cos(turn) + right * wp.sin(turn))


@wp.func
def aimFor(mode: int, p: wp.vec3, v: wp.vec3, ground: wp.vec3,
           inAir: bool, spin: wp.vec3, pitch: float, turn: float,
           heading: float, travel: float) -> wp.vec4:
  """Returns the autopilot's aim for 'mode' (x, y, z) and whether it has
  one (w: 1 or 0): along or against the path (over the ground in the
  air, the orbit's above), or the aim mode's."""
  path = v
  if inAir:
    path = ground
  if mode == AIM:
    aim = aimed(p, path, spin, pitch, turn, heading, travel)
    return wp.vec4(aim[0], aim[1], aim[2], 1.0)
  size = wp.length(path)
  if (mode == PROGRADE or mode == RETROGRADE) and size > 1.0:
    aim = path / size
    if mode == RETROGRADE:
      aim = -aim
    return wp.vec4(aim[0], aim[1], aim[2], 1.0)
  return wp.vec4(0.0, 0.0, 0.0, 0.0)


@wp.func
def solidDistance(kind: int, a: wp.vec3, b: wp.vec3, radius: float,
                  x: wp.vec3) -> float:
  """Returns how far 'x' is out of a solid of the station (its own
  axes; less than nought: inside): '_stationsolids.solidDistance'."""
  if kind == TORUS:
    flat = wp.sqrt(x[0] * x[0] + x[1] * x[1]) - a[0]
    return wp.sqrt(flat * flat + x[2] * x[2]) - radius
  if kind == CYLINDER:
    across = wp.sqrt(x[0] * x[0] + x[1] * x[1]) - radius
    along = wp.max(a[2] - x[2], x[2] - b[2])
    outA = wp.max(across, 0.0)
    outB = wp.max(along, 0.0)
    return wp.min(wp.max(across, along), 0.0) + wp.sqrt(outA * outA
                                                         + outB * outB)
  ab = b - a
  long2 = wp.dot(ab, ab)
  share = float(0.0)
  if long2 > 0.0:
    share = wp.clamp(wp.dot(x - a, ab) / long2, 0.0, 1.0)
  return wp.length(x - (a + ab * share)) - radius


@wp.func
def solidNormal(kind: int, a: wp.vec3, b: wp.vec3, radius: float,
                x: wp.vec3) -> wp.vec3:
  """Returns the way out of a solid at 'x' (its own axes): its
  distance's gradient, by central differences."""
  h = GRADIENT_STEP
  g = wp.vec3(
    solidDistance(kind, a, b, radius, x + wp.vec3(h, 0.0, 0.0))
    - solidDistance(kind, a, b, radius, x - wp.vec3(h, 0.0, 0.0)),
    solidDistance(kind, a, b, radius, x + wp.vec3(0.0, h, 0.0))
    - solidDistance(kind, a, b, radius, x - wp.vec3(0.0, h, 0.0)),
    solidDistance(kind, a, b, radius, x + wp.vec3(0.0, 0.0, h))
    - solidDistance(kind, a, b, radius, x - wp.vec3(0.0, 0.0, h)))
  size = wp.length(g)
  if size > 0.0:
    return g / size
  return wp.vec3(0.0, 0.0, 1.0)


@wp.kernel
def flown(sky: Sky, fleet: Fleet, start: float, seconds: float,
          longest: float):
  """Moves each vessel 'seconds' s on from time 'start' (s since the
  last leap), no step longer than 'longest'."""
  i = wp.tid()
  states = fleet.states
  b = int(states[i, ANCHOR])
  row = i * sky.count * SLOTS
  spanStart = sky.tableStart + wp.floor(
    (start - sky.tableStart) / SKY_SPAN) * SKY_SPAN
  spanEnd = spanStart + SKY_SPAN
  skySolved(sky, fleet, row, spanStart)
  skyShifted(sky, fleet, row)
  skySolved(sky, fleet, row, spanEnd)
  skyDrawn(sky, fleet, row, (start - spanStart) / SKY_SPAN, SKY_SPAN)
  hi = vecAt(states, i, PLACE_HI)
  lo = vecAt(states, i, PLACE_LO)
  vhi = vecAt(states, i, SPEED_HI)
  vlo = vecAt(states, i, SPEED_LO)
  q = quatAt(states, i, TURN)
  w = vecAt(states, i, SPIN)
  spun = w
  felt = wp.vec3(0.0, 0.0, 0.0)
  base = hi + lo
  baseHi = hi
  baseLo = lo
  height0 = states[i, HEIGHT]
  radius = sky.radii[b]
  mass = fleet.masses[i]
  inertia = fleet.inertias[i]
  drag = fleet.drags[i]
  push = states[i, PUSH]
  rcs = vecAt(states, i, RCS)
  matchSpin = vecAt(states, i, MATCH_SPIN)
  thrusters = fleet.attitude[i]
  steer = vecAt(states, i, STEER)
  mode = int(states[i, MODE])
  held = quatAt(states, i, HELD)
  aimPitch = states[i, AIM_PITCH]
  aimTurn = states[i, AIM_TURN]
  aimHeading = states[i, AIM_HEADING]
  aimTravel = states[i, AIM_TRAVEL]
  spin = sky.spins[b]
  airTop = sky.airTops[b]
  done = float(0.0)
  free = float(1e30)
  anchorMu = sky.mus[b]
  steps = int(0)
  touching = int(0)
  bump = float(0.0)
  near = fleet.near[i]
  solidAt = fleet.solidAt[i]
  solidSpeed = fleet.solidSpeed[i]
  solidFall = fleet.solidFall[i]
  solidTurn = fleet.solidTurn[i]
  solidSpin = fleet.solidSpin[i]
  spinRate = wp.length(solidSpin)
  stationAt = fleet.stationAt[i]
  stationVel = fleet.stationVel[i]
  startAt = baseHi + baseLo
  contact = int(0)
  stiff = mass * SOLID_OMEGA * SOLID_OMEGA
  damp = 2.0 * SOLID_DAMPING * mass * SOLID_OMEGA
  struck = wp.vec3(0.0, 0.0, 0.0)
  struckTwist = wp.vec3(0.0, 0.0, 0.0)
  latched = states[i, LATCHED] > 0.5
  latchPort = vecAt(states, i, LATCH_PORT)
  latchTurn = quatAt(states, i, LATCH_TURN)
  latchNose = vecAt(states, i, LATCH_NOSE)
  while done < seconds and steps < MOST_STEPS:
    d = (hi - baseHi) + (lo - baseLo)
    height = heightOf(base, height0, radius, d)
    r = wp.length(hi + lo)
    dt = wp.min(seconds - done, wp.min(longest, ETA * free))
    dt = wp.min(dt, KEPLER_SHARE * wp.sqrt(r * r * r / anchorMu))
    if height < GROUND_NEAR:
      dt = wp.min(dt, GROUND_STEP)
    contact = int(0)
    if near != 0:
      coast = drifted(stationAt, stationVel, anchorMu, done)
      there = stationAt + coast[0]
      going = stationVel + coast[1]
      apart = wp.length(there - (hi + lo))
      if apart > STATION_CLEAR:
        closing = wp.max(wp.length(going - (vhi + vlo)), 1.0)
        dt = wp.min(dt, wp.max(CONTACT_STEP, (apart - STATION_CLEAR)
                                / closing))
      else:
        dt = wp.min(dt, CONTACT_STEP)
        contact = 1
    if latched:
      dt = wp.min(dt, CONTACT_STEP)
    dt = wp.max(dt, LEAST_STEP)
    # coast half a step on the anchor's pull
    arc = drifted(hi + lo, vhi + vlo, anchorMu, 0.5 * dt)
    pair = pairAdded(hi, lo, arc[0])
    hi = pair[0]
    lo = pair[1]
    pair = pairAdded(vhi, vlo, arc[1])
    vhi = pair[0]
    vlo = pair[1]
    p = hi + lo
    v = vhi + vlo
    t = start + done + 0.5 * dt
    while t > spanEnd:
      skyShifted(sky, fleet, row)
      spanStart = spanEnd
      spanEnd = spanStart + SKY_SPAN
      skySolved(sky, fleet, row, spanEnd)
    share = wp.clamp((t - spanStart) / SKY_SPAN, 0.0, 1.0)
    skyDrawn(sky, fleet, row, share, SKY_SPAN)
    # every other body pulls, less its pull on the anchor (the anchor's
    # own fall)
    accel = wp.vec3(0.0, 0.0, 0.0)
    free = float(1e30)
    for k in range(sky.count):
      if k == b:
        continue
      fromAnchor = relativeOf(sky, fleet, row, k, b)
      there = fromAnchor - p
      r2 = wp.dot(there, there)
      a2 = wp.dot(fromAnchor, fromAnchor)
      if r2 > 0.0 and a2 > 0.0:
        r = wp.sqrt(r2)
        accel = accel + there * (sky.mus[k] / (r2 * r)) - fromAnchor * (
          sky.mus[k] / (a2 * wp.sqrt(a2)))
        free = wp.min(free, wp.sqrt(r2 * r / sky.mus[k]))
    force = wp.vec3(0.0, 0.0, 0.0)
    torque = wp.vec3(0.0, 0.0, 0.0)
    nose = wp.quat_rotate(q, wp.vec3(0.0, 0.0, 1.0))
    d = (hi - baseHi) + (lo - baseLo)
    height = heightOf(base, height0, radius, d)
    ground = v - wp.cross(spin, p)
    # the air drags, along the nose and across it
    rho = densityAt(sky, b, height)
    if rho > 0.0:
      speed = wp.length(ground)
      if speed > 0.0:
        along = wp.dot(nose, ground) / speed
        area = drag[0] * wp.abs(along) + drag[1] * wp.sqrt(
          wp.max(0.0, 1.0 - along * along))
        force = force - ground * (0.5 * rho * speed * area)
    force = force + nose * push + wp.quat_rotate(q, rcs)
    # the legs stand on the turning ground
    touching = int(0)
    if height < GROUND_NEAR:
      spinWorld = wp.quat_rotate(q, w)
      for leg in range(4):
        arm = wp.quat_rotate(q, fleet.legs[i * 4 + leg])
        low = heightOf(base, height0, radius, d + arm)
        if low < 0.0:
          normal = wp.normalize(p + arm)
          moving = v + wp.cross(spinWorld, arm) - wp.cross(spin, p + arm)
          into = wp.dot(moving, normal)
          press = -LEG_STIFF * low - LEG_DAMP * into
          if press > 0.0:
            slide = moving - normal * into
            rub = slide * (-LEG_SLIDE)
            most = LEG_GRIP * press
            size = wp.length(rub)
            if size > most:
              rub = rub * (most / size)
            push2 = normal * press + rub
            force = force + push2
            torque = torque + wp.cross(arm, push2)
            touching = touching + 1
    # the hull's balls pressed out of the station's near solids
    if contact != 0:
      tau = done + 0.5 * dt
      offset = solidAt + solidSpeed * tau + solidFall * (0.5 * tau * tau)
      flowing = solidSpeed + solidFall * tau
      if seconds > SHORT_FRAME:
        coast = drifted(stationAt, stationVel, anchorMu, tau)
        offset = stationAt + coast[0] - startAt
        flowing = stationVel + coast[1]
      turn = solidTurn
      if spinRate > 0.0:
        turn = wp.mul(wp.quat_from_axis_angle(solidSpin / spinRate,
                                              spinRate * tau), solidTurn)
      spinWorld = wp.quat_rotate(q, w)
      middle = wp.quat_rotate_inv(turn, d - offset)
      for j in range(fleet.solidKinds.shape[0]):
        if ((near >> j) & 1) == 0:
          continue
        kind = fleet.solidKinds[j]
        sa = fleet.solidFrom[j]
        sb = fleet.solidTo[j]
        sr = fleet.solidRadii[j]
        clear = solidDistance(kind, sa, sb, sr, middle)
        if clear > HULL_REACH:
          continue
        for k in range(fleet.balls.shape[0]):
          ball = fleet.balls[k]
          local = wp.vec3(ball[0], ball[1], ball[2])
          if clear > wp.length(local) + ball[3]:
            continue
          arm = wp.quat_rotate(q, local)
          rel = d + arm - offset
          own = wp.quat_rotate_inv(turn, rel)
          gap = solidDistance(kind, sa, sb, sr, own) - ball[3]
          if gap < 0.0:
            normal = wp.quat_rotate(turn, solidNormal(kind, sa, sb, sr,
                                                      own))
            reach = ball[3] + 0.5 * gap
            touch = arm - normal * reach
            there = rel - normal * reach
            moving = v + wp.cross(spinWorld, touch) - (
              flowing + wp.cross(solidSpin, there))
            into = wp.dot(moving, normal)
            press = -stiff * gap - damp * into
            if press > 0.0:
              slide = moving - normal * into
              rub = slide * (-SOLID_SLIDE * mass)
              most = SOLID_GRIP * press
              size = wp.length(rub)
              if size > most:
                rub = rub * (most / size)
              shove = normal * press + rub
              force = force + shove
              torque = torque + wp.cross(touch, shove)
              struck = struck - shove * dt
              struckTwist = struckTwist + wp.cross(there, -shove) * dt
              bump = wp.max(bump, -into)
    # the port that caught its nose draws it in, and turns it to its
    # docking turn; as hard back on the station
    if latched:
      tau = done + 0.5 * dt
      offset = solidAt + solidSpeed * tau + solidFall * (0.5 * tau * tau)
      flowing = solidSpeed + solidFall * tau
      if seconds > SHORT_FRAME:
        coast = drifted(stationAt, stationVel, anchorMu, tau)
        offset = stationAt + coast[0] - startAt
        flowing = stationVel + coast[1]
      turn = solidTurn
      if spinRate > 0.0:
        turn = wp.mul(wp.quat_from_axis_angle(solidSpin / spinRate,
                                              spinRate * tau), solidTurn)
      spinWorld = wp.quat_rotate(q, w)
      arm = wp.quat_rotate(q, latchNose)
      mouth = wp.quat_rotate(turn, latchPort)
      drawn = (offset + mouth) - (d + arm)
      drawing = (flowing + wp.cross(solidSpin, mouth)) - (
        v + wp.cross(spinWorld, arm))
      pull = (drawn * (LATCH_OMEGA * LATCH_OMEGA)
              + drawing * (2.0 * LATCH_OMEGA)) * mass
      force = force + pull
      torque = torque + wp.cross(arm, pull)
      struck = struck - pull * dt
      struckTwist = struckTwist + wp.cross(mouth, -pull) * dt
      off = rotationOf(wp.mul(wp.quat_inverse(q), wp.mul(turn,
                                                         latchTurn)))
      lagging = w - wp.quat_rotate_inv(q, solidSpin)
      aligning = wp.cw_mul(inertia, off * (LATCH_OMEGA * LATCH_OMEGA)
                           - lagging * (2.0 * LATCH_OMEGA))
      twist = wp.quat_rotate(q, aligning)
      torque = torque + twist
      struckTwist = struckTwist - twist * dt
    # the attitude thrusters: the autopilot, each key taking its own axis
    # over; the anchor's pull twisting it (stronger on its near end)
    own = wp.quat_rotate(wp.quat_inverse(q), torque)
    rb = wp.quat_rotate_inv(q, p)
    rr = wp.dot(rb, rb)
    own = own + wp.cross(rb, wp.cw_mul(inertia, rb)) * (
      3.0 * anchorMu / (rr * rr * wp.sqrt(rr)))
    target = aimFor(mode, p, v, ground, height < airTop, spin, aimPitch,
                    aimTurn, aimHeading, aimTravel)
    aim = wp.vec3(target[0], target[1], target[2])
    aiming = target[3] > 0.5
    railed = dt > SNAP_STEP
    if not railed:
      wanted = wp.vec3(0.0, 0.0, 0.0)
      if mode > 0:
        error = wp.vec3(0.0, 0.0, 0.0)
        if mode == HOLD or mode == MATCH:
          error = rotationOf(wp.mul(wp.quat_inverse(q), held))
        elif aiming:
          error = pointing(q, aim)
        want = error * RATE_GAIN
        size = wp.length(want)
        if size > RATE_MOST:
          want = want * (RATE_MOST / size)
        if mode == MATCH:
          want = want + wp.quat_rotate_inv(q, matchSpin)
        if mode != HOLD and mode != MATCH:
          want = wp.vec3(want[0], want[1], 0.0)
        wanted = wp.cw_mul(inertia, want - w) * TORQUE_GAIN
      for k in range(3):
        wanted[k] = wp.clamp(wanted[k], -thrusters[k], thrusters[k])
        if steer[k] != 0.0:
          wanted[k] = steer[k] * thrusters[k]
      own = own + wanted
    # what pushes it but gravity, felt in its own axes over the step
    felt = felt + wp.quat_rotate_inv(q, force / mass) * dt
    # kick
    pair = pairAdded(vhi, vlo, (accel + force / mass) * dt)
    vhi = pair[0]
    vlo = pair[1]
    if railed:
      if mode == MATCH:
        w = wp.quat_rotate_inv(held, matchSpin)
      elif mode > 0:
        w = wp.vec3(0.0, 0.0, 0.0)
    else:
      gyro = wp.cross(w, wp.cw_mul(inertia, w))
      w = w + wp.cw_div(own - gyro, inertia) * dt
    turned = wp.length(w) * dt
    if turned > 0.0:
      q = wp.normalize(wp.mul(q, wp.quat_from_axis_angle(
        w / wp.length(w), turned)))
    # coast the other half
    arc = drifted(hi + lo, vhi + vlo, anchorMu, 0.5 * dt)
    pair = pairAdded(hi, lo, arc[0])
    hi = pair[0]
    lo = pair[1]
    pair = pairAdded(vhi, vlo, arc[1])
    vhi = pair[0]
    vlo = pair[1]
    # on rails the autopilot's aim is had at the step's end
    if railed and (mode == HOLD or mode == MATCH):
      q = held
    elif railed and mode > 0:
      p = hi + lo
      v = vhi + vlo
      inAir = heightOf(base, height0, radius, (hi - baseHi)
                       + (lo - baseLo)) < airTop
      target = aimFor(mode, p, v, v - wp.cross(spin, p), inAir, spin,
                      aimPitch, aimTurn, aimHeading, aimTravel)
      if target[3] > 0.5:
        q = pointed(q, wp.vec3(target[0], target[1], target[2]))
    done = done + dt
    steps = steps + 1
  vecPut(states, i, PLACE_HI, hi)
  vecPut(states, i, PLACE_LO, lo)
  vecPut(states, i, SPEED_HI, vhi)
  vecPut(states, i, SPEED_LO, vlo)
  for k in range(4):
    states[i, TURN + k] = q[k]
  vecPut(states, i, SPIN, w)
  states[i, TOUCHING] = float(touching)
  states[i, STEPS] = float(steps)
  states[i, BUMP] = bump
  lasted = wp.max(done, LEAST_STEP)
  vecPut(states, i, FELT, felt / lasted)
  vecPut(states, i, SPINNING, (w - spun) / lasted)
  vecPut(states, i, STRUCK, struck)
  vecPut(states, i, STRUCK_TWIST, struckTwist)
