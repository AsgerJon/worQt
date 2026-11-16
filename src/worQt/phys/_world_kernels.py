"""
The Warp kernel 'worldRun' steps an assembly on as 'World.booked' does
in plain Python, compiled: one thread, every step of a call in one
launch. Its pieces follow the plain Python's: a body's half kick
(gravity, the ground), the springs', the contacts', the grease's; the
ties', actuators' and dampers' rules kept (SHAKE, RATTLE, the dampers
solved with them); the free turn split about the principal axes; the
work booked by kind. The plain Python stays the reference, the kernel
held to it ('test_compiled').

Units are m, kg, s; float64 throughout, every number named, as Warp
keeps float64 and float32 apart. Turns are quaternions, scalar first,
as 'vec4d'. A body's index below nought is the world.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import warp as wp

wp.config.log_level = wp.LOG_WARNING
wp.set_module_options({'enable_backward': False})

ZERO = wp.constant(wp.float64(0.0))
ONE = wp.constant(wp.float64(1.0))
HALF = wp.constant(wp.float64(0.5))
HUGE = wp.constant(wp.float64(1e300))  # kg: past it, part of the world
QUARTER = wp.constant(wp.float64(0.25))
TWO = wp.constant(wp.float64(2.0))
CLOSE = wp.constant(wp.float64(1e-13))  # m: rules kept to within this
PIVOT = wp.constant(wp.float64(1e-12))  # no pivot below this share
TWO_PI = wp.constant(wp.float64(2.0 * math.pi))
WALL_SLIDE = wp.constant(wp.float64(0.5))  # m/s: a wall's friction eased
UNIT = wp.constant(wp.float64(1.0 / 9007199254740992.0))
GOLDEN = wp.constant(wp.uint64(0x9E3779B97F4A7C15))
FIRST_MIX = wp.constant(wp.uint64(0xBF58476D1CE4E5B9))
SECOND_MIX = wp.constant(wp.uint64(0x94D049BB133111EB))
TRIES = wp.constant(50)
KINDS = wp.constant(6)  # ground, damper, actuator, grease, tie, contact
WIDE = wp.constant(24)  # a link's numbers
GROUND = wp.constant(0)
DAMPER = wp.constant(1)
ACTUATOR = wp.constant(2)
GREASE = wp.constant(3)
TIE = wp.constant(4)
CONTACT = wp.constant(5)


@wp.struct
class Rules:
  """What a run is: the world's and the call's numbers."""
  gravity: wp.vec3d
  h: wp.float64
  count: int
  start: wp.float64
  first: int
  bodies: int
  links: int
  rows: int
  springs: int
  motors: int
  drags: int
  contacts: int
  rounds: int
  slots: int
  ground: int
  stiffness: wp.float64
  damping: wp.float64
  grip: wp.float64
  bristle: wp.float64
  bristleDamping: wp.float64
  relaxation: wp.float64
  terrain: int
  terrainX: wp.float64
  terrainY: wp.float64
  terrainCell: wp.float64
  terrainNx: int
  terrainNy: int
  terrainTop: wp.float64
  wall: int
  wallHalf: wp.float64
  wallRadius: wp.float64
  wallOut: wp.float64
  wallHeight: wp.float64
  wallGrip: wp.float64
  grease: int
  shake: wp.float64
  spin: wp.float64
  seed: wp.uint64
  sleep: int
  sleepSpeed: wp.float64
  sleepSpin: wp.float64
  settle: wp.float64
  threads: int
  parallel: int


@wp.struct
class Bodies:
  """The bodies: what they are, where they are, and their scratch."""
  mass: wp.array(dtype=wp.float64)
  moments: wp.array(dtype=wp.vec3d)
  axes: wp.array(dtype=wp.vec4d)
  centre: wp.array(dtype=wp.vec3d)
  place: wp.array(dtype=wp.vec3d)
  velocity: wp.array(dtype=wp.vec3d)
  turn: wp.array(dtype=wp.vec4d)
  momentum: wp.array(dtype=wp.vec3d)
  groundFirst: wp.array(dtype=wp.int32)
  groundCount: wp.array(dtype=wp.int32)
  groundReach: wp.array(dtype=wp.float64)
  groundPlane: wp.array(dtype=wp.float64)
  groundArm: wp.array(dtype=wp.vec3d)
  groundRing: wp.array(dtype=wp.float64)
  rollAxis: wp.array(dtype=wp.vec3d)
  heights: wp.array(dtype=wp.float64)
  bristle: wp.array(dtype=wp.vec2d)
  bristleOn: wp.array(dtype=wp.int32)
  given: wp.array(dtype=wp.vec3d)
  drifting: wp.array(dtype=wp.vec3d)
  pushing: wp.array(dtype=wp.vec3d)
  rest: wp.array(dtype=wp.float64)
  free: wp.array(dtype=wp.int32)
  asleepNow: wp.array(dtype=wp.int32)
  stillNow: wp.array(dtype=wp.int32)
  woken: wp.array(dtype=wp.int32)
  round: wp.array(dtype=wp.float64)


@wp.struct
class Links:
  """The springs, and the ties, actuators and dampers with their rules
  and the solver's scratch."""
  springEnds: wp.array(dtype=wp.int32)
  springArms: wp.array(dtype=wp.vec3d)
  springLaw: wp.array(dtype=wp.vec4d)
  springTurned: wp.array(dtype=wp.int32)
  motorEnds: wp.array(dtype=wp.int32)
  motorAxis: wp.array(dtype=wp.vec3d)
  motorOwnAxis: wp.array(dtype=wp.vec3d)
  motorDrive: wp.array(dtype=wp.float64)
  motorReference: wp.array(dtype=wp.vec4d)
  motorBearer: wp.array(dtype=wp.int32)
  motorArms: wp.array(dtype=wp.vec3d)
  motorForward: wp.array(dtype=wp.vec3d)
  motorLeft: wp.array(dtype=wp.vec3d)
  dragBody: wp.array(dtype=wp.int32)
  dragPull: wp.array(dtype=wp.float64)
  springTurning: wp.array(dtype=wp.mat33d)
  kind: wp.array(dtype=wp.int32)
  ends: wp.array(dtype=wp.int32)
  arms: wp.array(dtype=wp.vec3d)
  data: wp.array(dtype=wp.float64)
  rowLink: wp.array(dtype=wp.int32)
  rowAxis: wp.array(dtype=wp.int32)
  armsNow: wp.array(dtype=wp.vec3d)
  ways: wp.array(dtype=wp.vec3d)
  coupling: wp.array(dtype=wp.float64)
  matrix: wp.array(dtype=wp.float64)
  impulses: wp.array(dtype=wp.float64)
  better: wp.array(dtype=wp.float64)
  speeds: wp.array(dtype=wp.float64)
  before: wp.array(dtype=wp.float64)
  misses: wp.array(dtype=wp.float64)
  soft: wp.array(dtype=wp.mat33d)
  trialVelocity: wp.array(dtype=wp.vec3d)
  trialMomentum: wp.array(dtype=wp.vec3d)
  trialPlace: wp.array(dtype=wp.vec3d)
  trialTurn: wp.array(dtype=wp.vec4d)
  linkImpulse: wp.array(dtype=wp.vec3d)
  held: wp.array(dtype=wp.int32)


@wp.struct
class Touches:
  """The contacts: their pairs and laws, each way round's skin (a
  body's, shared by all its contacts) and holds, the pieces pressed,
  and each kick's skins placed in the world."""
  pair: wp.array(dtype=wp.int32)
  law: wp.array(dtype=wp.float64)
  bodyFirst: wp.array(dtype=wp.int32)
  bodyContacts: wp.array(dtype=wp.int32)
  queue: wp.array(dtype=wp.int32)
  entrySkin: wp.array(dtype=wp.int32)
  entryCount: wp.array(dtype=wp.int32)
  entryHold: wp.array(dtype=wp.int32)
  entryOn: wp.array(dtype=wp.int32)
  skinBody: wp.array(dtype=wp.int32)
  skinArm: wp.array(dtype=wp.vec3d)
  skinShare: wp.array(dtype=wp.float64)
  skinOut: wp.array(dtype=wp.vec3d)
  skinPlace: wp.array(dtype=wp.vec3d)
  fresh: wp.array(dtype=wp.int32)
  found: wp.array(dtype=wp.int32)
  depth: wp.array(dtype=wp.float64)
  normalOf: wp.array(dtype=wp.vec3d)
  entryFound: wp.array(dtype=wp.int32)
  turning: wp.array(dtype=wp.mat33d)
  own: wp.array(dtype=wp.mat33d)
  spin: wp.array(dtype=wp.vec3d)
  boxLow: wp.array(dtype=wp.vec3d)
  boxHigh: wp.array(dtype=wp.vec3d)
  holdOn: wp.array(dtype=wp.int32)
  hold: wp.array(dtype=wp.vec3d)
  pieceFirst: wp.array(dtype=wp.int32)
  pieceCount: wp.array(dtype=wp.int32)
  planeFirst: wp.array(dtype=wp.int32)
  planeCount: wp.array(dtype=wp.int32)
  normal: wp.array(dtype=wp.vec3d)
  offset: wp.array(dtype=wp.float64)
  reach: wp.array(dtype=wp.float64)
  low: wp.array(dtype=wp.vec3d)
  high: wp.array(dtype=wp.vec3d)
  roundBall: wp.array(dtype=wp.int32)
  roundOther: wp.array(dtype=wp.int32)
  roundLaw: wp.array(dtype=wp.float64)
  roundOn: wp.array(dtype=wp.int32)
  roundStretch: wp.array(dtype=wp.vec3d)
  roundArm: wp.array(dtype=wp.vec3d)
  roundNormal: wp.array(dtype=wp.vec3d)
  roundNoted: wp.array(dtype=wp.int32)
  roundSlotFirst: wp.array(dtype=wp.int32)
  roundSlotCount: wp.array(dtype=wp.int32)
  roundSlotOf: wp.array(dtype=wp.int32)
  tdFirst: wp.array(dtype=wp.int32)
  tdCount: wp.array(dtype=wp.int32)
  tdBound: wp.array(dtype=wp.vec4d)
  tdKind: wp.array(dtype=wp.int32)
  tdData: wp.array(dtype=wp.float64)
  rpBodyFirst: wp.array(dtype=wp.int32)
  rpBodyCount: wp.array(dtype=wp.int32)
  rpReach: wp.array(dtype=wp.float64)
  rpPlaneFirst: wp.array(dtype=wp.int32)
  rpPlaneCount: wp.array(dtype=wp.int32)
  rpLow: wp.array(dtype=wp.vec3d)
  rpHigh: wp.array(dtype=wp.vec3d)
  rpBox: wp.array(dtype=wp.int32)
  rpTriFirst: wp.array(dtype=wp.int32)
  rpTriCount: wp.array(dtype=wp.int32)
  rpNormal: wp.array(dtype=wp.vec3d)
  rpOffset: wp.array(dtype=wp.float64)
  rpCorner: wp.array(dtype=wp.vec3d)
  entryOpenNow: wp.array(dtype=wp.int32)
  holdEntry: wp.array(dtype=wp.int32)


@wp.func
def qmul(p: wp.vec4d, q: wp.vec4d) -> wp.vec4d:
  """The quaternion 'p' times 'q'."""
  return wp.vec4d(p[0] * q[0] - p[1] * q[1] - p[2] * q[2] - p[3] * q[3],
                  p[0] * q[1] + p[1] * q[0] + p[2] * q[3] - p[3] * q[2],
                  p[0] * q[2] - p[1] * q[3] + p[2] * q[0] + p[3] * q[1],
                  p[0] * q[3] + p[1] * q[2] - p[2] * q[1] + p[3] * q[0])


@wp.func
def qconj(q: wp.vec4d) -> wp.vec4d:
  """The quaternion 'q's way back."""
  return wp.vec4d(q[0], -q[1], -q[2], -q[3])


@wp.func
def qunit(q: wp.vec4d) -> wp.vec4d:
  """The quaternion 'q' made a unit one."""
  size = wp.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
  return wp.vec4d(q[0] / size, q[1] / size, q[2] / size, q[3] / size)


@wp.func
def qmat(q: wp.vec4d) -> wp.mat33d:
  """The unit quaternion 'q' as a matrix, its columns the axes
  turned."""
  w = q[0]
  x = q[1]
  y = q[2]
  z = q[3]
  return wp.mat33d(ONE - TWO * (y * y + z * z), TWO * (x * y - w * z),
                   TWO * (x * z + w * y),
                   TWO * (x * y + w * z), ONE - TWO * (x * x + z * z),
                   TWO * (y * z - w * x),
                   TWO * (x * z - w * y), TWO * (y * z + w * x),
                   ONE - TWO * (x * x + y * y))


@wp.func
def apply(m: wp.mat33d, v: wp.vec3d) -> wp.vec3d:
  """The matrix 'm' times 'v', row by row as 'applied' sums."""
  return wp.vec3d(m[0, 0] * v[0] + m[0, 1] * v[1] + m[0, 2] * v[2],
                  m[1, 0] * v[0] + m[1, 1] * v[1] + m[1, 2] * v[2],
                  m[2, 0] * v[0] + m[2, 1] * v[1] + m[2, 2] * v[2])


@wp.func
def turnAxis(axis: wp.vec3d, angle: wp.float64) -> wp.vec4d:
  """The turn by 'angle' about 'axis'."""
  size = wp.length(axis)
  half = HALF * angle
  share = wp.sin(half) / size
  return wp.vec4d(wp.cos(half), axis[0] * share, axis[1] * share,
                  axis[2] * share)


@wp.func
def heldSpin(momentum: wp.vec3d, moments: wp.vec3d) -> wp.vec3d:
  """The spin along the principal axes of 'momentum' along them."""
  return wp.vec3d(momentum[0] / moments[0], momentum[1] / moments[1],
                  momentum[2] / moments[2])


@wp.func
def spinOf(b: Bodies, k: int) -> wp.vec3d:
  """Body 'k's spin in the world."""
  return apply(qmat(b.turn[k]), heldSpin(b.momentum[k], b.moments[k]))


@wp.func
def turnedPart(turn: wp.vec4d, momentum: wp.vec3d, moments: wp.vec3d,
               axis: int, share: wp.float64, h: wp.float64):
  """A part of the free turn: about principal axis 'axis' for 'share'
  of 'h', as '_turnedFreely' has it."""
  angle = share * h * momentum[axis] / moments[axis]
  c = wp.cos(angle)
  s = wp.sin(angle)
  half = wp.vec3d(ZERO, ZERO, ZERO)
  half[axis] = wp.sin(HALF * angle)
  turned = qmul(turn, wp.vec4d(wp.cos(HALF * angle), half[0], half[1],
                               half[2]))
  j = (axis + 1) % 3
  k = (axis + 2) % 3
  m = momentum
  mj = c * momentum[j] + s * momentum[k]
  mk = c * momentum[k] - s * momentum[j]
  m[j] = mj
  m[k] = mk
  return turned, m


@wp.func
def turnedFreely(turn: wp.vec4d, momentum: wp.vec3d, moments: wp.vec3d,
                 h: wp.float64):
  """A body turned freely for 'h' s, split about its principal axes:
  the first for half, the second for half, the third for all, back."""
  t, m = turnedPart(turn, momentum, moments, 0, HALF, h)
  t, m = turnedPart(t, m, moments, 1, HALF, h)
  t, m = turnedPart(t, m, moments, 2, ONE, h)
  t, m = turnedPart(t, m, moments, 1, HALF, h)
  t, m = turnedPart(t, m, moments, 0, HALF, h)
  return qunit(t), m


@wp.func
def pushBody(b: Bodies, k: int, impulse: wp.vec3d, arm: wp.vec3d,
             kind: int):
  """Body 'k' given 'impulse' at 'arm' from its centre, booked under
  'kind' (below nought, not booked)."""
  b.velocity[k] = b.velocity[k] + impulse * (ONE / b.mass[k])
  twist = cross3(arm, impulse)
  b.momentum[k] = b.momentum[k] + apply(wp.transpose(qmat(b.turn[k])),
                                        twist)
  if kind >= 0:
    at = k * 2 * KINDS + 2 * kind
    b.given[at] = b.given[at] + impulse
    b.given[at + 1] = b.given[at + 1] + twist


@wp.func
def cross3(a: wp.vec3d, b: wp.vec3d) -> wp.vec3d:
  """The cross product 'a' x 'b', summed as 'cross' sums."""
  return wp.vec3d(a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                  a[0] * b[1] - a[1] * b[0])


@wp.func
def dot3(a: wp.vec3d, b: wp.vec3d) -> wp.float64:
  """The dot product of 'a' and 'b', summed as 'dot' sums."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@wp.func
def norm3(a: wp.vec3d) -> wp.float64:
  """The length of 'a'."""
  return wp.sqrt(dot3(a, a))


@wp.func
def mixed(value: wp.uint64) -> wp.uint64:
  """'value' hashed (splitmix64), as '_draws.mixed'."""
  v = value + GOLDEN
  v = (v ^ (v >> wp.uint64(30))) * FIRST_MIX
  v = (v ^ (v >> wp.uint64(27))) * SECOND_MIX
  return v ^ (v >> wp.uint64(31))


@wp.func
def normalDraw(key: wp.uint64, pair: int, second: int) -> wp.float64:
  """One of the six normal draws of 'key', as '_draws.normalDraws'."""
  near = mixed(key ^ wp.uint64(2 * pair + 1))
  round_ = mixed(key ^ wp.uint64(2 * pair + 2))
  u = (wp.float64(near >> wp.uint64(11)) + HALF) * UNIT
  v = wp.float64(round_ >> wp.uint64(11)) * UNIT
  size = wp.sqrt(-TWO * wp.log(u))
  if second == 0:
    return size * wp.cos(TWO_PI * v)
  return size * wp.sin(TWO_PI * v)


@wp.func
def asleep(rules: Rules, b: Bodies, k: int) -> int:
  """Whether body 'k' sleeps, as '_Moving.asleep' says."""
  if rules.sleep == 0 or b.free[k] == 0:
    return 0
  if b.rest[k] >= rules.settle:
    return 1
  return 0


@wp.func
def fixedBody(b: Bodies, k: int) -> int:
  """Whether body 'k' is part of the world ('Fixed': infinitely
  heavy)."""
  if b.mass[k] > HUGE:
    return 1
  return 0


@wp.func
def stillOf(rules: Rules, b: Bodies, k: int) -> int:
  """Whether body 'k' is still, as '_Moving.still' says."""
  if norm3(b.velocity[k]) < rules.sleepSpeed and norm3(
      spinOf(b, k)) < rules.sleepSpin:
    return 1
  return 0


@wp.func
def lowestWay(axis: wp.vec3d) -> wp.vec3d:
  """The way from the middle of a circle about 'axis' (a unit, in the
  world) to its lowest point; for one lying flat, along x."""
  way = wp.vec3d(axis[0] * axis[2], axis[1] * axis[2],
                 axis[2] * axis[2] - ONE)
  size = norm3(way)
  if size < wp.float64(1e-12):
    return wp.vec3d(ONE, ZERO, ZERO)
  return way * (ONE / size)


@wp.func
def terrainAt(rules: Rules, b: Bodies, x: wp.float64,
              y: wp.float64) -> wp.vec4d:
  """The terrain at 'x', 'y': its height and its upward unit normal
  (bilinear in its cell; flat at nought off its grid)."""
  a = (x - rules.terrainX) / rules.terrainCell
  c = (y - rules.terrainY) / rules.terrainCell
  i = int(wp.floor(a))
  j = int(wp.floor(c))
  if i < 0 or j < 0 or i >= rules.terrainNx - 1 or (
          j >= rules.terrainNy - 1):
    return wp.vec4d(ZERO, ZERO, ZERO, ONE)
  u = a - wp.float64(i)
  v = c - wp.float64(j)
  ny = rules.terrainNy
  h00 = b.heights[i * ny + j]
  h10 = b.heights[(i + 1) * ny + j]
  h01 = b.heights[i * ny + j + 1]
  h11 = b.heights[(i + 1) * ny + j + 1]
  height = ((h00 * (ONE - u) + h10 * u) * (ONE - v)
            + (h01 * (ONE - u) + h11 * u) * v)
  along = ((h10 - h00) * (ONE - v) + (h11 - h01) * v) / rules.terrainCell
  across = ((h01 - h00) * (ONE - u) + (h11 - h10) * u) / rules.terrainCell
  size = wp.sqrt(along * along + across * across + ONE)
  return wp.vec4d(height, -along / size, -across / size, ONE / size)


@wp.func
def deepestWay(axis: wp.vec3d, normal: wp.vec3d) -> wp.vec3d:
  """The way from the middle of a circle about 'axis' to its point
  deepest along the ground's 'normal'; for one lying flat, along x."""
  share = -dot3(normal, axis)
  way = wp.vec3d(-normal[0] - share * axis[0],
                 -normal[1] - share * axis[1],
                 -normal[2] - share * axis[2])
  size = norm3(way)
  if size < wp.float64(1e-12):
    return wp.vec3d(ONE, ZERO, ZERO)
  return way * (ONE / size)


@wp.func
def groundOut(rules: Rules, b: Bodies, k: int, i: int,
              turning: wp.mat33d) -> wp.vec3d:
  """Where ground point 'i' of body 'k' may touch the ground, from its
  centre, in the world: a ball's lowest point, a turned solid's circle's
  lowest point (on a terrain, deepest along its normal), else the point
  turned."""
  if b.round[k] > ZERO:
    if rules.terrain == 0:
      return b.groundArm[i]
    under = terrainAt(rules, b, b.place[k][0], b.place[k][1])
    return wp.vec3d(under[1], under[2], under[3]) * (-b.round[k])
  ring = b.groundRing[i]
  if ring > ZERO:
    if rules.terrain == 0:
      return apply(turning, b.groundArm[i]) + lowestWay(
        apply(turning, b.rollAxis[k])) * ring
    arm = apply(turning, b.groundArm[i])
    middle = b.place[k] + arm
    under = terrainAt(rules, b, middle[0], middle[1])
    return arm + deepestWay(apply(turning, b.rollAxis[k]),
                            wp.vec3d(under[1], under[2],
                                     under[3])) * ring
  return apply(turning, b.groundArm[i])


@wp.func
def wallBeyond(rules: Rules, x: wp.float64, y: wp.float64) -> wp.vec3d:
  """How far 'x', 'y' is out through the oval's wall's face, m, and the
  face's outward normal there, level: (depth, nx, ny) ('OvalWall.
  beyond')."""
  half = rules.wallHalf
  radius = rules.wallRadius
  if x > half or x < -half:
    middle = half
    if x < -half:
      middle = -half
    dx = x - middle
    dy = y - radius
    far = wp.sqrt(dx * dx + dy * dy)
    if far < wp.float64(1e-9):
      return wp.vec3d(-radius - rules.wallOut, ONE, ZERO)
    return wp.vec3d(far - radius - rules.wallOut, dx / far, dy / far)
  if y < radius:
    return wp.vec3d(-y - rules.wallOut, ZERO, -ONE)
  return wp.vec3d(y - TWO * radius - rules.wallOut, ZERO, ONE)


@wp.func
def wallOf(rules: Rules, b: Bodies, place: wp.vec3d) -> wp.vec3d:
  """How deep 'place' is through the wall's face (nought: not in it, or
  over its top) and the face's outward normal: (depth, nx, ny)
  ('Ground.wallOf')."""
  none = wp.vec3d(ZERO, ZERO, ZERO)
  if rules.wall == 0:
    return none
  beyond = wallBeyond(rules, place[0], place[1])
  if beyond[0] <= ZERO:
    return none
  base = ZERO
  if rules.terrain != 0:
    base = terrainAt(rules, b, place[0], place[1])[0]
  if place[2] > base + rules.wallHeight:
    return none
  return beyond


@wp.func
def wallPush(rules: Rules, b: Bodies, place: wp.vec3d,
             moving: wp.vec3d) -> wp.vec3d:
  """The wall's push on a point at 'place' moving at 'moving', N
  ('Ground.wallPush')."""
  wall = wallOf(rules, b, place)
  if wall[0] <= ZERO:
    return wp.vec3d(ZERO, ZERO, ZERO)
  nx = wall[1]
  ny = wall[2]
  sinking = moving[0] * nx + moving[1] * ny
  push = wp.max(ZERO, rules.stiffness * wall[0]
                * (ONE + rules.damping * sinking))
  tx = moving[0] - sinking * nx
  ty = moving[1] - sinking * ny
  tz = moving[2]
  slide = wp.max(wp.sqrt(tx * tx + ty * ty + tz * tz), WALL_SLIDE)
  share = rules.wallGrip * push / slide
  return wp.vec3d(-nx * push - share * tx, -ny * push - share * ty,
                  -share * tz)


@wp.func
def groundKick(rules: Rules, b: Bodies, k: int, hh: wp.float64):
  """Body 'k' kicked for 'hh' s by gravity and the ground; not
  asleep, nor part of the world."""
  if asleep(rules, b, k) != 0 or fixedBody(b, k) != 0:
    return
  b.velocity[k] = b.velocity[k] + rules.gravity * hh
  first = int(b.groundFirst[k])
  count = int(b.groundCount[k])
  plane = 8 * k
  top = b.groundPlane[plane + 6]
  if rules.wall != 0:
    top = top + rules.wallHeight
  if rules.ground == 0 or count == 0 or (
          b.place[k][2] - top >= b.groundReach[k]):
    for i in range(first, first + count):
      b.bristleOn[i] = 0
    return
  turning = qmat(b.turn[k])
  spin = apply(turning, heldSpin(b.momentum[k], b.moments[k]))
  force = wp.vec3d(ZERO, ZERO, ZERO)
  torque = wp.vec3d(ZERO, ZERO, ZERO)
  for i in range(first, first + count):
    out = groundOut(rules, b, k, i, turning)
    place = b.place[k] + out
    moving = b.velocity[k] + cross3(spin, out)
    if rules.wall != 0:
      walled = wallPush(rules, b, place, moving)
      force = force + walled
      torque = torque + cross3(out, walled)
    level = (b.groundPlane[plane + 2]
             + b.groundPlane[plane + 3] * (place[0] - b.groundPlane[plane])
             + b.groundPlane[plane + 4]
             * (place[1] - b.groundPlane[plane + 1]))
    if place[2] - level > b.groundPlane[plane + 5]:
      b.bristleOn[i] = 0
      continue
    depth = -place[2]
    sinking = -moving[2]
    normal = wp.vec3d(ZERO, ZERO, ONE)
    if rules.terrain != 0:
      under = terrainAt(rules, b, place[0], place[1])
      normal = wp.vec3d(under[1], under[2], under[3])
      depth = (under[0] - place[2]) * under[3]
      sinking = -dot3(moving, normal)
    if depth <= ZERO:
      b.bristleOn[i] = 0
      continue
    push = wp.max(ZERO, rules.stiffness * depth
                  * (ONE + rules.damping * sinking))
    most = rules.grip * push
    x = place[0]
    y = place[1]
    if b.bristleOn[i] != 0:
      x = b.bristle[i][0]
      y = b.bristle[i][1]
    sx = -rules.bristle * (place[0] - x)
    sy = -rules.bristle * (place[1] - y)
    held = wp.sqrt(sx * sx + sy * sy)
    if held > most:
      share = most / held
      sx = sx * share
      sy = sy * share
      x = place[0] + sx / rules.bristle
      y = place[1] + sy / rules.bristle
    fx = sx - rules.bristleDamping * moving[0]
    fy = sy - rules.bristleDamping * moving[1]
    along = wp.sqrt(fx * fx + fy * fy)
    if along > most:
      fx = fx * most / along
      fy = fy * most / along
    b.bristle[i] = wp.vec2d(x, y)
    b.bristleOn[i] = 1
    pushed = wp.vec3d(fx, fy, push)
    if rules.terrain != 0:
      pushed = wp.vec3d(fx + normal[0] * push, fy + normal[1] * push,
                        normal[2] * push)
    force = force + pushed
    torque = torque + cross3(out, pushed)
  b.velocity[k] = b.velocity[k] + force * (hh / b.mass[k])
  twist = apply(wp.transpose(turning), torque)
  b.momentum[k] = b.momentum[k] + twist * hh
  at = k * 2 * KINDS + 2 * GROUND
  b.given[at] = b.given[at] + force * hh
  b.given[at + 1] = b.given[at + 1] + torque * hh


@wp.func
def rolled(rules: Rules, b: Bodies, k: int, setting: wp.vec3d,
           h: wp.float64):
  """The bristles of body 'k''s circles (a turned solid) rolled along
  with it for 'h' s at spin 'setting': each anchor moved as the
  circle's lowest point rolls on, so rolling stretches it not at all
  and only slipping does; with the ground's 'relaxation', let go of as
  much of its stretch as the share of that length rolled."""
  turning = qmat(b.turn[k])
  first = int(b.groundFirst[k])
  for i in range(first, first + int(b.groundCount[k])):
    if b.bristleOn[i] == 0 or b.groundRing[i] <= ZERO:
      continue
    out = groundOut(rules, b, k, i, turning)
    rolling = out - apply(turning, b.groundArm[i])
    dx = -(setting[1] * rolling[2] - setting[2] * rolling[1]) * h
    dy = -(setting[2] * rolling[0] - setting[0] * rolling[2]) * h
    x = b.bristle[i][0]
    y = b.bristle[i][1]
    if rules.relaxation > ZERO:
      share = wp.min(ONE, wp.sqrt(dx * dx + dy * dy) / rules.relaxation)
      place = b.place[k] + out
      x = x + (place[0] - x) * share
      y = y + (place[1] - y) * share
    b.bristle[i] = wp.vec2d(x + dx, y + dy)


@wp.func
def groundStored(rules: Rules, b: Bodies, k: int) -> wp.float64:
  """What the ground and body 'k's bristles hold now, J."""
  first = int(b.groundFirst[k])
  count = int(b.groundCount[k])
  stored = wp.float64(0.0)
  if rules.ground == 0 or count == 0 or (
          b.place[k][2] - rules.terrainTop >= b.groundReach[k]):
    return stored
  turning = qmat(b.turn[k])
  for i in range(first, first + count):
    out = groundOut(rules, b, k, i, turning)
    place = b.place[k] + out
    through = wallOf(rules, b, place)[0]
    stored = stored + HALF * rules.stiffness * through * through
    depth = -place[2]
    if rules.terrain != 0:
      under = terrainAt(rules, b, place[0], place[1])
      depth = (under[0] - place[2]) * under[3]
    if depth <= ZERO:
      continue
    stored = stored + HALF * rules.stiffness * depth * depth
    if b.bristleOn[i] != 0:
      dx = place[0] - b.bristle[i][0]
      dy = place[1] - b.bristle[i][1]
      stored = stored + HALF * rules.bristle * (dx * dx + dy * dy)
  return stored


@wp.func
def isNought(v: wp.vec3d) -> int:
  """One if 'v' is nought, every part."""
  if v[0] == ZERO and v[1] == ZERO and v[2] == ZERO:
    return 1
  return 0


@wp.func
def pushMiddle(b: Bodies, k: int, impulse: wp.vec3d, kind: int):
  """Body 'k' given 'impulse' at its centre, booked under 'kind' (below
  nought, not booked): 'pushBody' with no arm, so no twist."""
  b.velocity[k] = b.velocity[k] + impulse * (ONE / b.mass[k])
  if kind >= 0:
    at = k * 2 * KINDS + 2 * kind
    b.given[at] = b.given[at] + impulse


@wp.func
def pushTurned(b: Bodies, k: int, impulse: wp.vec3d, arm: wp.vec3d,
               turning: wp.mat33d, kind: int):
  """'pushBody', the body's turn as the matrix 'turning' already."""
  b.velocity[k] = b.velocity[k] + impulse * (ONE / b.mass[k])
  twist = cross3(arm, impulse)
  b.momentum[k] = b.momentum[k] + apply(wp.transpose(turning), twist)
  if kind >= 0:
    at = k * 2 * KINDS + 2 * kind
    b.given[at] = b.given[at] + impulse
    b.given[at + 1] = b.given[at + 1] + twist


@wp.func
def springsKick(rules: Rules, b: Bodies, links: Links, hh: wp.float64):
  """The bodies kicked for 'hh' s by the springs, and by the damped
  ones' pushes (booked as a damper's), one spring after the other. An
  end at its body's centre (a tyre's lumps) is not turned at all; each
  body with an end off its centre is turned once for all its springs
  (a wheel's 144 sidewall springs)."""
  for k in range(rules.bodies):
    if links.springTurned[k] != 0:
      links.springTurning[k] = qmat(b.turn[k])
  for s in range(rules.springs):
    law = links.springLaw[s]
    a = int(links.springEnds[2 * s])
    c = int(links.springEnds[2 * s + 1])
    firstArm = wp.vec3d(ZERO, ZERO, ZERO)
    secondArm = wp.vec3d(ZERO, ZERO, ZERO)
    firstMoving = wp.vec3d(ZERO, ZERO, ZERO)
    secondMoving = wp.vec3d(ZERO, ZERO, ZERO)
    first = links.springArms[2 * s]
    second = links.springArms[2 * s + 1]
    firstMiddle = 1
    secondMiddle = 1
    if a >= 0:
      firstMiddle = isNought(first)
      first = b.place[a]
      firstMoving = b.velocity[a]
      if firstMiddle == 0:
        turning = links.springTurning[a]
        firstArm = apply(turning, links.springArms[2 * s])
        first = first + firstArm
        if law[2] != ZERO:
          spin = apply(turning, heldSpin(b.momentum[a], b.moments[a]))
          firstMoving = firstMoving + cross3(spin, firstArm)
    if c >= 0:
      secondMiddle = isNought(second)
      second = b.place[c]
      secondMoving = b.velocity[c]
      if secondMiddle == 0:
        turning = links.springTurning[c]
        secondArm = apply(turning, links.springArms[2 * s + 1])
        second = second + secondArm
        if law[2] != ZERO:
          spin = apply(turning, heldSpin(b.momentum[c], b.moments[c]))
          secondMoving = secondMoving + cross3(spin, secondArm)
    apart = second - first
    pull = wp.vec3d(ZERO, ZERO, ZERO)
    length = norm3(apart)
    slack = 0
    if law[1] != ZERO:
      if length > law[1] and law[3] == ONE:
        slack = 1
      if length <= law[1] and law[3] == wp.float64(2.0):
        slack = 1
    if law[1] == ZERO:
      pull = apart * law[0]
    else:
      if length > ZERO and slack == 0:
        pull = apart * (law[0] * (length - law[1]) / length)
    damped = wp.vec3d(ZERO, ZERO, ZERO)
    if law[2] != ZERO and slack == 0:
      parting = secondMoving - firstMoving
      if law[1] == ZERO:
        damped = parting * law[2]
      else:
        if length > ZERO:
          damped = apart * (law[2] * dot3(parting, apart)
                            / (length * length))
    if a >= 0:
      if firstMiddle == 1:
        pushMiddle(b, a, pull * hh, -1)
        if law[2] != ZERO:
          pushMiddle(b, a, damped * hh, 1)
      else:
        turning = links.springTurning[a]
        pushTurned(b, a, pull * hh, firstArm, turning, -1)
        if law[2] != ZERO:
          pushTurned(b, a, damped * hh, firstArm, turning, 1)
    if c >= 0:
      if secondMiddle == 1:
        pushMiddle(b, c, pull * (-hh), -1)
        if law[2] != ZERO:
          pushMiddle(b, c, damped * (-hh), 1)
      else:
        turning = links.springTurning[c]
        pushTurned(b, c, pull * (-hh), secondArm, turning, -1)
        if law[2] != ZERO:
          pushTurned(b, c, damped * (-hh), secondArm, turning, 1)


@wp.func
def ownTurning(b: Bodies, k: int) -> wp.mat33d:
  """Body 'k's own frame's turn now."""
  return qmat(qmul(b.turn[k], qconj(b.axes[k])))


@wp.func
def across(v: wp.vec3d, normal: wp.vec3d) -> wp.vec3d:
  """'v' less its part along the unit 'normal'."""
  return v - normal * dot3(v, normal)


@wp.func
def skinsAll(rules: Rules, b: Bodies, t: Touches) -> int:
  """Every body's turn, own turn and spin now; and, where the bodies
  have moved since the last look ('t.fresh[0]' nought), every skin
  point placed in the world and every body's box: then 1, the touches
  to be found anew; else nought, the last ones still right (the bodies
  are where they were: only how they move has changed). A body asleep
  has not moved: its skin stays as placed, but at a call's first look
  ('t.fresh[1]'), when every body is placed."""
  for k in range(rules.bodies):
    turning = qmat(b.turn[k])
    t.turning[k] = turning
    t.own[k] = ownTurning(b, k)
    t.spin[k] = apply(turning, heldSpin(b.momentum[k], b.moments[k]))
  if t.fresh[0] != 0:
    return 0
  every = t.fresh[1]
  for k in range(rules.bodies):
    if every != 0 or asleep(rules, b, k) == 0:
      t.boxLow[k] = b.place[k]
      t.boxHigh[k] = b.place[k]
  for i in range(t.skinBody.shape[0]):
    k = int(t.skinBody[i])
    if k < 0:
      continue
    if every == 0 and asleep(rules, b, k) != 0:
      continue
    outward = apply(t.turning[k], t.skinArm[i])
    place = b.place[k] + outward
    t.skinOut[i] = outward
    t.skinPlace[i] = place
    t.boxLow[k] = wp.min(t.boxLow[k], place)
    t.boxHigh[k] = wp.max(t.boxHigh[k], place)
  t.fresh[0] = 1
  t.fresh[1] = 0
  return 1


@wp.func
def letGo(t: Touches, entry: int, holdStart: int, count: int):
  """Way round 'entry's holds let go, where it held any."""
  if t.entryOn[entry] != 0:
    for i in range(count):
      t.holdOn[holdStart + i] = 0
    t.entryOn[entry] = 0


@wp.func
def entryOpen(rules: Rules, b: Bodies, t: Touches, c: int, way: int,
              holds: int, look: int) -> int:
  """Whether way round 'way' of contact 'c' (its entry) is to be pressed
  now, as 'touchDirection' has it: not both its bodies asleep; looking,
  their boxes in the world meeting (else nothing found, its holds let
  go); not looking, something found when last looked (else its holds
  let go). 1 or nought."""
  toucher = int(t.pair[2 * c + way])
  other = int(t.pair[2 * c + 1 - way])
  entry = 2 * c + way
  count = int(t.entryCount[entry])
  holdStart = int(t.entryHold[entry])
  if holds != 0 and asleep(rules, b, toucher) != 0 and asleep(
      rules, b, other) != 0:
    return 0
  lowB = t.boxLow[other]
  highB = t.boxHigh[other]
  if look != 0:
    lowA = t.boxLow[toucher]
    highA = t.boxHigh[toucher]
    if (highA[0] < lowB[0] or highB[0] < lowA[0] or highA[1] < lowB[1]
        or highB[1] < lowA[1] or highA[2] < lowB[2]
        or highB[2] < lowA[2]):
      t.entryFound[entry] = 0
      if holds != 0:
        letGo(t, entry, holdStart, count)
      return 0
  elif t.entryFound[entry] == 0:
    if holds != 0:
      letGo(t, entry, holdStart, count)
    return 0
  return 1


@wp.func
def touchPoint(rules: Rules, b: Bodies, t: Touches, c: int, way: int,
               i: int, hh: wp.float64, holds: int,
               look: int) -> wp.vec4d:
  """Skin point 'i' of way round 'way' of contact 'c' (its entry open:
  'entryOpen'), as 'touchDirection' has it: with 'holds', its push added
  to both bodies' pushes for 'hh' s (atomically: points may be pressed
  side by side) and its hold kept; returns what it holds (its press and
  its bristle's stretch, J, with 'holds' nought), whether it was found
  pressed (looking) and whether it holds now (each 1 or nought)."""
  toucher = int(t.pair[2 * c + way])
  other = int(t.pair[2 * c + 1 - way])
  entry = 2 * c + way
  lowB = t.boxLow[other]
  highB = t.boxHigh[other]
  stiffness = t.law[6 * c]
  damping = t.law[6 * c + 1]
  grip = t.law[6 * c + 2]
  bristle = t.law[6 * c + 3]
  bristleDamping = t.law[6 * c + 4]
  otherTurning = t.turning[other]
  back = wp.transpose(otherTurning)
  own = t.own[other]
  ownBack = wp.transpose(own)
  spin = t.spin[toucher]
  otherSpin = t.spin[other]
  pieceFirst = int(t.pieceFirst[other])
  pieceCount = int(t.pieceCount[other])
  skin = int(t.entrySkin[entry]) + i
  at = int(t.entryHold[entry]) + i
  place = t.skinPlace[skin]
  deepest = wp.float64(0.0)
  normal = wp.vec3d(ZERO, ZERO, ZERO)
  found = ZERO
  if look != 0:
    t.found[at] = 0
    if (place[0] < lowB[0] or place[0] > highB[0]
        or place[1] < lowB[1] or place[1] > highB[1]
        or place[2] < lowB[2] or place[2] > highB[2]):
      if holds != 0:
        t.holdOn[at] = 0
      return wp.vec4d(ZERO, ZERO, ZERO, ZERO)
    inside = apply(back, place - b.place[other])
    hit = int(0)
    for p in range(pieceFirst, pieceFirst + pieceCount):
      low = t.low[p]
      high = t.high[p]
      if (inside[0] < low[0] or inside[0] > high[0]
          or inside[1] < low[1] or inside[1] > high[1]
          or inside[2] < low[2] or inside[2] > high[2]):
        continue
      depth = wp.float64(0.0)
      facing = wp.vec3d(ZERO, ZERO, ZERO)
      planeFirst = int(t.planeFirst[p])
      for q in range(planeFirst, planeFirst + int(t.planeCount[p])):
        slack = t.offset[q] - dot3(t.normal[q], inside)
        if q == planeFirst or slack < depth:
          depth = slack
          facing = t.normal[q]
      if depth > deepest:
        deepest = depth
        normal = facing
        hit = int(1)
    if hit == 0:
      if holds != 0:
        t.holdOn[at] = 0
      return wp.vec4d(ZERO, ZERO, ZERO, ZERO)
    normal = apply(otherTurning, normal)
    t.found[at] = 1
    t.depth[at] = deepest
    t.normalOf[at] = normal
    found = ONE
  else:
    if t.found[at] == 0:
      if holds != 0:
        t.holdOn[at] = 0
      return wp.vec4d(ZERO, ZERO, ZERO, ZERO)
    deepest = t.depth[at]
    normal = t.normalOf[at]
  outward = t.skinOut[skin]
  apart = place - b.place[other]
  moving = (b.velocity[toucher] + cross3(spin, outward)) - (
    b.velocity[other] + cross3(otherSpin, apart))
  share = t.skinShare[skin]
  push = wp.max(ZERO, share * stiffness * deepest
                * (ONE + damping * (-dot3(normal, moving))))
  most = grip * push
  hadHold = int(t.holdOn[at])
  if holds == 0:
    pressed = HALF * share * stiffness * deepest * deepest
    stretched = ZERO
    if hadHold != 0:
      anchor = b.place[other] + apply(own, t.hold[at] - b.centre[other])
      stretch = across(place - anchor, normal)
      stretched = HALF * share * bristle * dot3(stretch, stretch)
    return wp.vec4d(pressed, stretched, found, ZERO)
  held = t.hold[at]
  stretch = wp.vec3d(ZERO, ZERO, ZERO)
  if hadHold != 0:
    anchor = b.place[other] + apply(own, held - b.centre[other])
    stretch = across(place - anchor, normal)
  else:
    held = b.centre[other] + apply(ownBack, place - b.place[other])
    anchor = b.place[other] + apply(own, held - b.centre[other])
    stretch = across(place - anchor, normal)
  spring = share * bristle
  pull = stretch * (-spring)
  pulling = norm3(pull)
  if pulling > most:
    pull = pull * (most / pulling)
    slipped = place + pull * (ONE / spring)
    held = b.centre[other] + apply(ownBack, slipped - b.place[other])
  along = pull - across(moving, normal) * (share * bristleDamping)
  size = norm3(along)
  if size > most:
    along = along * (most / size)
  t.hold[at] = held
  t.holdOn[at] = 1
  force = normal * push + along
  wp.atomic_add(b.pushing, 2 * toucher, force * hh)
  wp.atomic_add(b.pushing, 2 * toucher + 1, cross3(outward, force * hh))
  wp.atomic_add(b.pushing, 2 * other, -(force * hh))
  wp.atomic_add(b.pushing, 2 * other + 1, cross3(apart, force * (-hh)))
  return wp.vec4d(ZERO, ZERO, found, ONE)


@wp.func
def touchDirection(rules: Rules, b: Bodies, t: Touches, c: int, way: int,
                   hh: wp.float64, holds: int, look: int) -> wp.float64:
  """One way round contact 'c' ('way' nought: the first's skin into
  the second, one: the second's into the first): each pressing point's
  push, added up per body in 'b.pushing' for 'hh' s; with 'holds' the
  holds kept, else left; returns what the touches hold, J. The skins
  are placed already ('skinsAll'). With 'look' the touches are found
  and kept: bodies whose boxes in the world do not meet are passed
  over; a point outside the other's box in the world, or a piece's box
  along its axes, is not looked at further (a body's skin holds all its
  corners, so its box holds it). Without, the kept ones are used (the
  bodies have not moved since)."""
  entry = 2 * c + way
  stored = wp.float64(0.0)
  if entryOpen(rules, b, t, c, way, holds, look) == 0:
    return stored
  touching = int(0)
  anyFound = int(0)
  for i in range(int(t.entryCount[entry])):
    got = touchPoint(rules, b, t, c, way, i, hh, holds, look)
    stored = stored + got[0]
    if got[1] != ZERO:
      stored = stored + got[1]
    if got[2] != ZERO:
      anyFound = int(1)
    if got[3] != ZERO:
      touching = int(1)
  if look != 0:
    t.entryFound[entry] = anyFound
  if holds != 0:
    t.entryOn[entry] = touching
  return stored


@wp.func
def onTriangle(p: wp.vec3d, a: wp.vec3d, b: wp.vec3d,
               c: wp.vec3d) -> wp.vec3d:
  """The point of the triangle 'a' 'b' 'c' nearest 'p', found as
  '_rounds._onTriangle' finds it (Ericson's regions)."""
  ab = b - a
  ac = c - a
  ap = p - a
  d1 = dot3(ab, ap)
  d2 = dot3(ac, ap)
  if d1 <= ZERO and d2 <= ZERO:
    return a
  bp = p - b
  d3 = dot3(ab, bp)
  d4 = dot3(ac, bp)
  if d3 >= ZERO and d4 <= d3:
    return b
  vc = d1 * d4 - d3 * d2
  if vc <= ZERO and d1 >= ZERO and d3 <= ZERO:
    return a + ab * (d1 / (d1 - d3))
  cp = p - c
  d5 = dot3(ab, cp)
  d6 = dot3(ac, cp)
  if d6 >= ZERO and d5 <= d6:
    return c
  vb = d5 * d2 - d1 * d6
  if vb <= ZERO and d2 >= ZERO and d6 <= ZERO:
    return a + ac * (d2 / (d2 - d6))
  va = d3 * d6 - d5 * d4
  if va <= ZERO and d4 - d3 >= ZERO and d5 - d6 >= ZERO:
    share = (d4 - d3) / ((d4 - d3) + (d5 - d6))
    return b + (c - b) * share
  whole = ONE / (va + vb + vc)
  return a + (ab * (vb * whole) + ac * (vc * whole))


@wp.func
def nearestOn(t: Touches, o: int, p: wp.vec3d,
              radius: wp.float64) -> wp.vec4d:
  """How a ball of 'radius' centred at 'p' (along body 'o's principal
  axes) presses body 'o', as '_rounds.nearestOn' finds it: the normal
  out of the body and how deep, at the piece it presses deepest; a
  depth below nought where it touches none."""
  found = int(0)
  best = wp.vec3d(ZERO, ZERO, ZERO)
  bestDepth = wp.float64(-1.0)
  start = int(t.rpBodyFirst[o])
  for q in range(start, start + int(t.rpBodyCount[o])):
    low = t.rpLow[q]
    high = t.rpHigh[q]
    if (p[0] < low[0] - radius or p[0] > high[0] + radius
        or p[1] < low[1] - radius or p[1] > high[1] + radius
        or p[2] < low[2] - radius or p[2] > high[2] + radius):
      continue
    inside = int(1)
    have = int(0)
    least = wp.float64(0.0)
    leastFacing = wp.vec3d(ZERO, ZERO, ZERO)
    plane = int(t.rpPlaneFirst[q])
    for s in range(plane, plane + int(t.rpPlaneCount[q])):
      under = t.rpOffset[s] - dot3(t.rpNormal[s], p)
      if under < ZERO:
        inside = int(0)
      if have == 0 or under < least:
        least = under
        leastFacing = t.rpNormal[s]
        have = int(1)
    facing = wp.vec3d(ZERO, ZERO, ZERO)
    depth = wp.float64(0.0)
    ok = int(0)
    if inside != 0:
      facing = leastFacing
      depth = radius + least
      ok = int(1)
    else:
      near = p
      if t.rpBox[q] != 0:
        near = wp.vec3d(wp.min(wp.max(p[0], low[0]), high[0]),
                        wp.min(wp.max(p[1], low[1]), high[1]),
                        wp.min(wp.max(p[2], low[2]), high[2]))
      else:
        nearest = wp.float64(-1.0)
        tri = int(t.rpTriFirst[q])
        for r in range(tri, tri + int(t.rpTriCount[q])):
          candidate = onTriangle(p, t.rpCorner[3 * r], t.rpCorner[3 * r + 1],
                                 t.rpCorner[3 * r + 2])
          dx = candidate[0] - p[0]
          dy = candidate[1] - p[1]
          dz = candidate[2] - p[2]
          far = dx * dx + dy * dy + dz * dz
          if nearest < ZERO or far < nearest:
            nearest = far
            near = candidate
      off = p - near
      apart = norm3(off)
      if apart < radius and apart != ZERO:
        facing = off * (ONE / apart)
        depth = radius - apart
        ok = int(1)
    if ok != 0 and (found == 0 or depth > bestDepth):
      best = facing
      bestDepth = depth
      found = int(1)
  if found == 0:
    return wp.vec4d(ZERO, ZERO, ZERO, -ONE)
  return wp.vec4d(best[0], best[1], best[2], bestDepth)


@wp.func
def roundTouch(b: Bodies, t: Touches, k: int, o: int) -> wp.vec4d:
  """Where ball 'k' presses body 'o', as '_rounds.roundTouch' finds
  it: the normal pushing the ball out, in the world, and how deep; a
  depth below nought where they do not touch."""
  r = b.round[k]
  d = b.place[k] - b.place[o]
  far = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
  if b.round[o] > ZERO:
    reach = r + b.round[o]
    if far >= reach * reach or far == ZERO:
      return wp.vec4d(ZERO, ZERO, ZERO, -ONE)
    apart = wp.sqrt(far)
    return wp.vec4d(d[0] / apart, d[1] / apart, d[2] / apart,
                    reach - apart)
  reach = t.rpReach[o]
  if far >= (reach + r) * (reach + r):
    return wp.vec4d(ZERO, ZERO, ZERO, -ONE)
  turning = qmat(b.turn[o])
  found = nearestOn(t, o, apply(wp.transpose(turning), d), r)
  if found[3] < ZERO:
    return found
  normal = apply(turning, wp.vec3d(found[0], found[1], found[2]))
  return wp.vec4d(normal[0], normal[1], normal[2], found[3])


@wp.func
def pressOnPiece(t: Touches, s: int, rho: wp.float64, w: wp.float64,
                 radius: wp.float64) -> wp.vec3d:
  """How a ball of 'radius' whose middle is 'rho' from a turned solid's
  axis and 'w' up it presses its profile's piece 's', as
  '_turned.pressesOf' finds it: the normal pushing the ball out (along
  rho and w) and how deep; a depth below nought where it does not."""
  at = 6 * s
  qr = wp.float64(0.0)
  qw = wp.float64(0.0)
  outR = wp.float64(0.0)
  outW = wp.float64(0.0)
  if t.tdKind[s] == 0:
    r0 = t.tdData[at]
    w0 = t.tdData[at + 1]
    dr = t.tdData[at + 2] - r0
    dw = t.tdData[at + 3] - w0
    length2 = dr * dr + dw * dw
    share = ((rho - r0) * dr + (w - w0) * dw) / length2
    share = wp.min(ONE, wp.max(ZERO, share))
    length = wp.sqrt(length2)
    qr = r0 + share * dr
    qw = w0 + share * dw
    outR = dw / length
    outW = -dr / length
  else:
    cr = t.tdData[at]
    cw = t.tdData[at + 1]
    big = t.tdData[at + 2]
    a0 = t.tdData[at + 3]
    a1 = t.tdData[at + 4]
    low = wp.min(a0, a1)
    high = wp.max(a0, a1)
    angle = wp.atan2(w - cw, rho - cr)
    while angle < low:
      angle = angle + TWO_PI
    while angle >= low + TWO_PI:
      angle = angle - TWO_PI
    if angle > high:
      fr = cr + big * wp.cos(a0)
      fw = cw + big * wp.sin(a0)
      lr = cr + big * wp.cos(a1)
      lw = cw + big * wp.sin(a1)
      if ((fr - rho) * (fr - rho) + (fw - w) * (fw - w)
          <= (lr - rho) * (lr - rho) + (lw - w) * (lw - w)):
        angle = a0
      else:
        angle = a1
    c = wp.cos(angle)
    sn = wp.sin(angle)
    way = ONE
    if a1 < a0:
      way = -ONE
    qr = cr + big * c
    qw = cw + big * sn
    outR = way * c
    outW = way * sn
  dr = rho - qr
  dw = w - qw
  if dr * outR + dw * outW < ZERO:
    return wp.vec3d(ZERO, ZERO, -ONE)
  far = dr * dr + dw * dw
  if far >= radius * radius:
    return wp.vec3d(ZERO, ZERO, -ONE)
  apart = wp.sqrt(far)
  if apart == ZERO:
    return wp.vec3d(outR, outW, radius)
  return wp.vec3d(dr / apart, dw / apart, radius - apart)


@wp.func
def roundPushAt(rules: Rules, b: Bodies, t: Touches, i: int, slot: int,
                k: int, o: int, normal: wp.vec3d, depth: wp.float64,
                hh: wp.float64, holding: int) -> wp.float64:
  """One round contact's push, as 'ContactForces.roundPush' finds it:
  with 'holding', added to the bodies' pushes for 'hh' s, the stretch
  kept and the touch noted in 'slot'; else what it holds, J."""
  point = b.place[k] - normal * (b.round[k] - HALF * depth)
  arm = point - b.place[k]
  apart = point - b.place[o]
  moving = (b.velocity[k] + cross3(spinOf(b, k), arm)) - (
    b.velocity[o] + cross3(spinOf(b, o), apart))
  closing = dot3(normal, moving)
  slip = moving - normal * closing
  law = 5 * i
  stiffness = t.roundLaw[law]
  push = wp.max(ZERO, ONE * stiffness * depth
                * (ONE + t.roundLaw[law + 1] * (-closing)))
  most = t.roundLaw[law + 2] * push
  bristle = t.roundLaw[law + 3]
  held = wp.vec3d(ZERO, ZERO, ZERO)
  if t.roundOn[slot] != 0:
    held = t.roundStretch[slot]
  stretch = held - normal * dot3(held, normal)
  pull = stretch * (-bristle)
  pulling = norm3(pull)
  if pulling > most:
    pull = pull * (most / pulling)
    stretch = pull * (-ONE / bristle)
  along = pull - slip * t.roundLaw[law + 4]
  size = norm3(along)
  if size > most:
    along = along * (most / size)
  if holding == 0:
    return HALF * stiffness * depth * depth + HALF * bristle * dot3(
      stretch, stretch)
  t.roundOn[slot] = int(1)
  t.roundStretch[slot] = stretch
  t.roundArm[2 * slot] = arm
  t.roundArm[2 * slot + 1] = apart
  t.roundNormal[slot] = normal
  t.roundNoted[slot] = int(1)
  force = normal * push + along
  wp.atomic_add(b.pushing, 2 * k, force * hh)
  wp.atomic_add(b.pushing, 2 * k + 1, cross3(arm, force * hh))
  wp.atomic_add(b.pushing, 2 * o, -(force * hh))
  wp.atomic_add(b.pushing, 2 * o + 1, cross3(apart, -(force * hh)))
  return ZERO


@wp.func
def roundContact(rules: Rules, b: Bodies, t: Touches, i: int,
                 hh: wp.float64, holding: int,
                 stored: wp.float64) -> wp.float64:
  """Round contact 'i''s pushes, as 'roundsKick' finds them (its slots'
  notes cleared first; pushes added atomically: contacts may be pressed
  side by side); returns 'stored' and what it holds (with 'holding'
  nought), J."""
  for slot in range(int(t.roundSlotFirst[i]),
                    int(t.roundSlotFirst[i]) + int(t.roundSlotCount[i])):
    t.roundNoted[slot] = int(0)
  k = int(t.roundBall[i])
  o = int(t.roundOther[i])
  first = int(t.roundSlotFirst[i])
  if holding != 0 and asleep(rules, b, k) != 0 and (
      asleep(rules, b, o) != 0):
    return stored
  if int(t.tdCount[o]) > 0:
    r = b.round[k]
    own = ownTurning(b, o)
    p = apply(wp.transpose(own), b.place[k] - b.place[o]) + b.centre[o]
    rho = wp.sqrt(p[0] * p[0] + p[1] * p[1])
    ux = ONE
    uy = ZERO
    if rho > ZERO:
      ux = p[0] / rho
      uy = p[1] / rho
    bound = t.tdBound[o]
    near = int(1)
    if (rho < bound[0] - r or rho > bound[1] + r or p[2] < bound[2] - r
        or p[2] > bound[3] + r):
      near = int(0)
    for s in range(int(t.roundSlotCount[i])):
      slot = first + s
      press = wp.vec3d(ZERO, ZERO, -ONE)
      if near != 0:
        press = pressOnPiece(t, int(t.tdFirst[o]) + s, rho, p[2], r)
      if press[2] < ZERO:
        if holding != 0:
          t.roundOn[slot] = int(0)
        continue
      normal = apply(own, wp.vec3d(press[0] * ux, press[0] * uy,
                                   press[1]))
      stored = stored + roundPushAt(rules, b, t, i, slot, k, o, normal,
                                    press[2], hh, holding)
    return stored
  touch = roundTouch(b, t, k, o)
  if touch[3] < ZERO:
    if holding != 0:
      t.roundOn[first] = int(0)
    return stored
  normal = wp.vec3d(touch[0], touch[1], touch[2])
  stored = stored + roundPushAt(rules, b, t, i, first, k, o, normal,
                                touch[3], hh, holding)
  return stored


@wp.func
def roundsKick(rules: Rules, b: Bodies, t: Touches, hh: wp.float64,
               holding: int) -> wp.float64:
  """The round contacts' pushes, as 'ContactForces.roundPushes' finds
  them: with 'holding', added to the bodies' pushes for 'hh' s, the
  stretches kept and the touches noted for 'roundsRolled' (two bodies
  both asleep passed over); else what they hold, J, returned. A ball
  against a turned solid has a slot for each piece of its profile."""
  stored = wp.float64(0.0)
  for slot in range(rules.slots):
    t.roundNoted[slot] = int(0)
  for i in range(rules.rounds):
    stored = roundContact(rules, b, t, i, hh, holding, stored)
  return stored


@wp.func
def roundsRolled(rules: Rules, b: Bodies, t: Touches, h: wp.float64):
  """The round contacts' stretches carried on over a drift of 'h' s,
  each by its slip, as 'ContactForces.rolled' carries them."""
  for slot in range(rules.slots):
    if t.roundNoted[slot] == 0 or t.roundOn[slot] == 0:
      continue
    i = int(t.roundSlotOf[slot])
    k = int(t.roundBall[i])
    o = int(t.roundOther[i])
    normal = t.roundNormal[slot]
    moving = (b.velocity[k] + cross3(spinOf(b, k), t.roundArm[2 * slot])) - (
      b.velocity[o] + cross3(spinOf(b, o), t.roundArm[2 * slot + 1]))
    across = moving - normal * dot3(moving, normal)
    t.roundStretch[slot] = t.roundStretch[slot] + across * h


@wp.func
def contactsKick(rules: Rules, b: Bodies, t: Touches, hh: wp.float64):
  """The bodies kicked for 'hh' s by the contacts, all the pushes found
  first (along the edges, then the round ones), then given."""
  if rules.contacts == 0 and rules.rounds == 0:
    return
  for k in range(rules.bodies):
    b.pushing[2 * k] = wp.vec3d(ZERO, ZERO, ZERO)
    b.pushing[2 * k + 1] = wp.vec3d(ZERO, ZERO, ZERO)
  if rules.contacts > 0:
    look = skinsAll(rules, b, t)
    for k in range(rules.bodies):
      if asleep(rules, b, k) != 0:
        continue
      for j in range(int(t.bodyFirst[k]), int(t.bodyFirst[k + 1])):
        c = int(t.bodyContacts[j])
        if c >= rules.contacts:
          continue
        other = otherOf(t, c, k)
        if other < k and asleep(rules, b, other) == 0:
          continue
        touchDirection(rules, b, t, c, 0, hh, 1, look)
        touchDirection(rules, b, t, c, 1, hh, 1, look)
  if rules.rounds > 0:
    roundsKick(rules, b, t, hh, 1)
  for k in range(rules.bodies):
    if asleep(rules, b, k) != 0:
      continue
    impulse = b.pushing[2 * k]
    twist = b.pushing[2 * k + 1]
    b.velocity[k] = b.velocity[k] + impulse * (ONE / b.mass[k])
    b.momentum[k] = b.momentum[k] + apply(wp.transpose(qmat(b.turn[k])),
                                          twist)
    at = k * 2 * KINDS + 2 * CONTACT
    b.given[at] = b.given[at] + impulse
    b.given[at + 1] = b.given[at + 1] + twist


@wp.func
def contactsStored(rules: Rules, b: Bodies, t: Touches) -> wp.float64:
  """What the contacts hold now, J."""
  stored = wp.float64(0.0)
  if rules.contacts > 0:
    look = skinsAll(rules, b, t)
    for c in range(rules.contacts):
      stored = stored + touchDirection(rules, b, t, c, 0, ZERO, 0, look)
      stored = stored + touchDirection(rules, b, t, c, 1, ZERO, 0, look)
  if rules.rounds > 0:
    stored = stored + roundsKick(rules, b, t, ZERO, 0)
  return stored


@wp.func
def greaseKick(rules: Rules, b: Bodies, step: int, half: int,
               hh: wp.float64):
  """The bodies shaken for 'hh' s, as '_Moving.greased' shakes."""
  if rules.grease == 0:
    return
  root = wp.sqrt(hh)
  for k in range(rules.bodies):
    if asleep(rules, b, k) != 0 or fixedBody(b, k) != 0:
      continue
    key = mixed(rules.seed)
    key = mixed(key ^ wp.uint64(step))
    key = mixed(key ^ wp.uint64(half))
    key = mixed(key ^ wp.uint64(k))
    shaken = wp.vec3d(rules.shake * root * normalDraw(key, 0, 0),
                      rules.shake * root * normalDraw(key, 0, 1),
                      rules.shake * root * normalDraw(key, 1, 0))
    b.velocity[k] = b.velocity[k] + shaken
    moments = b.moments[k]
    spun = rules.spin * root
    given = wp.vec3d(moments[0] * (spun * normalDraw(key, 1, 1)),
                     moments[1] * (spun * normalDraw(key, 2, 0)),
                     moments[2] * (spun * normalDraw(key, 2, 1)))
    b.momentum[k] = b.momentum[k] + given
    at = k * 2 * KINDS + 2 * GREASE
    b.given[at] = b.given[at] + shaken * b.mass[k]
    b.given[at + 1] = b.given[at + 1] + apply(qmat(b.turn[k]), given)


@wp.func
def strokeAt(links: Links, l: int, time: wp.float64) -> wp.vec3d:
  """Actuator 'l's stroke at 'time': its length, how fast it grows,
  and how fast that grows."""
  base = l * WIDE
  code = int(links.data[base])
  if code == 0:
    return wp.vec3d(links.data[base + 1], ZERO, ZERO)
  if code == 1:
    rate = TWO_PI * links.data[base + 3]
    swing = wp.sin(rate * time)
    amplitude = links.data[base + 2]
    return wp.vec3d(links.data[base + 1] + amplitude * swing,
                    amplitude * rate * wp.cos(rate * time),
                    -amplitude * rate * rate * swing)
  foot = wp.vec3d(links.data[base + 1], links.data[base + 2],
                  links.data[base + 3])
  arm = wp.vec3d(links.data[base + 4], links.data[base + 5],
                 links.data[base + 6])
  place = wp.vec3d(links.data[base + 8], links.data[base + 9],
                   links.data[base + 10])
  turn = wp.vec4d(links.data[base + 11], links.data[base + 12],
                  links.data[base + 13], links.data[base + 14])
  velocity = wp.vec3d(ZERO, ZERO, ZERO)
  spin = wp.vec3d(ZERO, ZERO, ZERO)
  speeding = wp.vec3d(ZERO, ZERO, ZERO)
  turning = wp.vec3d(ZERO, ZERO, ZERO)
  if int(links.data[base + 7]) == 1:
    shift = wp.vec3d(links.data[base + 15], links.data[base + 16],
                     links.data[base + 17])
    tilt = wp.vec3d(links.data[base + 18], links.data[base + 19],
                    links.data[base + 20])
    rate = TWO_PI * links.data[base + 21]
    swing = wp.sin(rate * time)
    swinging = wp.cos(rate * time)
    place = place + shift * swing
    angle = norm3(tilt)
    if angle > ZERO:
      turn = qmul(turnAxis(tilt, angle * swing), turn)
    velocity = shift * (rate * swinging)
    spin = tilt * (rate * swinging)
    speeding = shift * (-rate * rate * swing)
    turning = tilt * (-rate * rate * swing)
  reach = apply(qmat(turn), arm)
  apart = (place + reach) - foot
  moving = velocity + cross3(spin, reach)
  growing = (speeding + cross3(turning, reach)) + cross3(
    spin, cross3(spin, reach))
  length = norm3(apart)
  rate = dot3(apart, moving) / length
  return wp.vec3d(length, rate, (dot3(moving, moving)
                                 + dot3(apart, growing) - rate * rate)
                  / length)


@wp.func
def armsAll(rules: Rules, b: Bodies, links: Links):
  """Each link end's arm in the world now (a world end's point)."""
  for l in range(rules.links):
    for e in range(2):
      k = int(links.ends[2 * l + e])
      if k < 0:
        links.armsNow[2 * l + e] = links.arms[2 * l + e]
      else:
        links.armsNow[2 * l + e] = apply(qmat(b.turn[k]),
                                         links.arms[2 * l + e])


@wp.func
def linkPoint(b: Bodies, links: Links, l: int, e: int) -> wp.vec3d:
  """Where link 'l's end 'e' is now."""
  k = int(links.ends[2 * l + e])
  if k < 0:
    return links.arms[2 * l + e]
  return b.place[k] + links.armsNow[2 * l + e]


@wp.func
def linkMoving(b: Bodies, links: Links, l: int, e: int) -> wp.vec3d:
  """How fast link 'l's end 'e' moves now."""
  k = int(links.ends[2 * l + e])
  if k < 0:
    return wp.vec3d(ZERO, ZERO, ZERO)
  return b.velocity[k] + cross3(spinOf(b, k), links.armsNow[2 * l + e])


@wp.func
def waysAll(rules: Rules, b: Bodies, links: Links):
  """Each rule's way now: a tie's along its axis, an actuator's or a
  damper's from its second end to its first."""
  for r in range(rules.rows):
    l = int(links.rowLink[r])
    axis = int(links.rowAxis[r])
    if axis >= 0:
      way = wp.vec3d(ZERO, ZERO, ZERO)
      way[axis] = ONE
      links.ways[r] = way
    else:
      apart = linkPoint(b, links, l, 0) - linkPoint(b, links, l, 1)
      length = norm3(apart)
      if length > ZERO:
        links.ways[r] = apart * (ONE / length)
      else:
        links.ways[r] = wp.vec3d(ZERO, ZERO, ZERO)


@wp.func
def speedsAll(rules: Rules, b: Bodies, links: Links):
  """How fast each rule moves along its way now."""
  for r in range(rules.rows):
    l = int(links.rowLink[r])
    apart = linkMoving(b, links, l, 0) - linkMoving(b, links, l, 1)
    links.speeds[r] = dot3(links.ways[r], apart)


@wp.func
def pointMoved(mass: wp.float64, soft: wp.mat33d, at: wp.vec3d,
               by: wp.vec3d, impulse: wp.vec3d) -> wp.vec3d:
  """How much faster a body's point at 'at' moves for 'impulse' at
  'by', as 'pointMoved' has it."""
  twist = apply(soft, cross3(by, impulse))
  return impulse * (ONE / mass) - cross3(at, twist)


@wp.func
def couplingAll(rules: Rules, b: Bodies, links: Links):
  """How much each rule moves for each rule's pull, per N s."""
  for k in range(rules.bodies):
    if links.held[k] == 0:
      continue
    turning = qmat(b.turn[k])
    moments = b.moments[k]
    inverse = wp.mat33d(ONE / moments[0], ZERO, ZERO,
                        ZERO, ONE / moments[1], ZERO,
                        ZERO, ZERO, ONE / moments[2])
    links.soft[k] = wp.mul(wp.mul(turning, inverse), wp.transpose(turning))
  n = rules.rows
  for i in range(n):
    li = int(links.rowLink[i])
    for j in range(n):
      lj = int(links.rowLink[j])
      total = wp.float64(0.0)
      for e in range(2):
        k = int(links.ends[2 * li + e])
        if k < 0:
          continue
        signI = wp.float64(1.0)
        if e == 1:
          signI = wp.float64(-1.0)
        for f in range(2):
          if int(links.ends[2 * lj + f]) != k:
            continue
          signJ = wp.float64(1.0)
          if f == 1:
            signJ = wp.float64(-1.0)
          moved = pointMoved(b.mass[k], links.soft[k],
                             links.armsNow[2 * li + e],
                             links.armsNow[2 * lj + f], links.ways[j])
          total = total + signI * signJ * dot3(links.ways[i], moved)
      links.coupling[i * n + j] = total


@wp.func
def solve(links: Links, n: int) -> int:
  """'links.matrix' (n rows of n and the right side) solved into
  'links.better', as 'solved' solves; nought where no pivot."""
  wide = n + 1
  largest = wp.float64(0.0)
  for r in range(n):
    for c in range(n):
      largest = wp.max(largest, wp.abs(links.matrix[r * wide + c]))
  for k in range(n):
    pivot = k
    for r in range(k + 1, n):
      if wp.abs(links.matrix[r * wide + k]) > wp.abs(
          links.matrix[pivot * wide + k]):
        pivot = r
    if wp.abs(links.matrix[pivot * wide + k]) <= PIVOT * largest:
      return 0
    if pivot != k:
      for c in range(wide):
        hold = links.matrix[k * wide + c]
        links.matrix[k * wide + c] = links.matrix[pivot * wide + c]
        links.matrix[pivot * wide + c] = hold
    for r in range(k + 1, n):
      share = links.matrix[r * wide + k] / links.matrix[k * wide + k]
      if share != ZERO:
        for c in range(k, wide):
          links.matrix[r * wide + c] = links.matrix[r * wide + c] - (
            share * links.matrix[k * wide + c])
  for kk in range(n):
    k = n - 1 - kk
    known = wp.float64(0.0)
    for c in range(k + 1, n):
      known = known + links.matrix[k * wide + c] * links.better[c]
    links.better[k] = (links.matrix[k * wide + n] - known) / (
      links.matrix[k * wide + k])
  return 1


@wp.func
def impulsesAll(rules: Rules, links: Links):
  """Each link's impulse on its first body, its rules' added up."""
  for l in range(rules.links):
    links.linkImpulse[l] = wp.vec3d(ZERO, ZERO, ZERO)
  for r in range(rules.rows):
    l = int(links.rowLink[r])
    links.linkImpulse[l] = links.linkImpulse[l] + links.ways[r] * (
      links.impulses[r])


@wp.func
def missesAfter(rules: Rules, b: Bodies, links: Links, h: wp.float64,
                time: wp.float64):
  """How far each rule would miss after the bodies, given the trial
  impulses, are moved freely for 'h' s to 'time'."""
  for k in range(rules.bodies):
    if links.held[k] == 0:
      continue
    links.trialVelocity[k] = b.velocity[k]
    links.trialMomentum[k] = b.momentum[k]
  impulsesAll(rules, links)
  for l in range(rules.links):
    for e in range(2):
      k = int(links.ends[2 * l + e])
      if k < 0:
        continue
      sign = wp.float64(1.0)
      if e == 1:
        sign = wp.float64(-1.0)
      signed = links.linkImpulse[l] * sign
      links.trialVelocity[k] = links.trialVelocity[k] + signed * (
        ONE / b.mass[k])
      links.trialMomentum[k] = links.trialMomentum[k] + apply(
        wp.transpose(qmat(b.turn[k])),
        cross3(links.armsNow[2 * l + e], signed))
  for k in range(rules.bodies):
    if links.held[k] == 0:
      continue
    links.trialPlace[k] = b.place[k] + links.trialVelocity[k] * h
    turn, momentum = turnedFreely(b.turn[k], links.trialMomentum[k],
                                  b.moments[k], h)
    links.trialTurn[k] = turn
  for r in range(rules.rows):
    l = int(links.rowLink[r])
    first = links.arms[2 * l]
    k = int(links.ends[2 * l])
    if k >= 0:
      first = links.trialPlace[k] + apply(qmat(links.trialTurn[k]),
                                          links.arms[2 * l])
    second = links.arms[2 * l + 1]
    k = int(links.ends[2 * l + 1])
    if k >= 0:
      second = links.trialPlace[k] + apply(qmat(links.trialTurn[k]),
                                           links.arms[2 * l + 1])
    kind = int(links.kind[l])
    if kind == TIE:
      axis = int(links.rowAxis[r])
      links.misses[r] = first[axis] - second[axis]
    elif kind == ACTUATOR:
      links.misses[r] = norm3(first - second) - strokeAt(links, l, time)[0]
    else:
      links.misses[r] = ZERO


@wp.func
def pushRows(rules: Rules, b: Bodies, links: Links):
  """The bodies given the rules' impulses, booked by kind."""
  impulsesAll(rules, links)
  for l in range(rules.links):
    for e in range(2):
      k = int(links.ends[2 * l + e])
      if k < 0:
        continue
      sign = wp.float64(1.0)
      if e == 1:
        sign = wp.float64(-1.0)
      pushBody(b, k, links.linkImpulse[l] * sign, links.armsNow[2 * l + e],
               int(links.kind[l]))


@wp.func
def dampedRow(rules: Rules, links: Links, r: int, h: wp.float64):
  """Damper rule 'r's row of the matrix and its right side, as
  'dampedRow' has them (the right side left in 'links.misses')."""
  n = rules.rows
  l = int(links.rowLink[r])
  share = QUARTER * h * links.data[l * WIDE]
  for c in range(n):
    links.matrix[r * (n + 1) + c] = share * links.coupling[r * n + c]
  links.matrix[r * (n + 1) + r] = links.matrix[r * (n + 1) + r] + ONE
  links.misses[r] = -share * (links.before[r] + links.speeds[r])


@wp.func
def pulled(rules: Rules, b: Bodies, links: Links, h: wp.float64,
           time: wp.float64) -> int:
  """The rules kept over a step of 'h' to 'time' (SHAKE), the dampers'
  first half found with them; nought where no pivot."""
  n = rules.rows
  armsAll(rules, b, links)
  waysAll(rules, b, links)
  couplingAll(rules, b, links)
  speedsAll(rules, b, links)
  damped = int(0)
  for r in range(n):
    links.impulses[r] = ZERO
    if int(links.kind[int(links.rowLink[r])]) == DAMPER:
      damped = int(1)
  for tried in range(TRIES):
    missesAfter(rules, b, links, h, time)
    worst = wp.float64(0.0)
    for r in range(n):
      worst = wp.max(worst, wp.abs(links.misses[r]))
    if worst <= CLOSE and (tried > 0 or damped == 0):
      break
    for r in range(n):
      if int(links.kind[int(links.rowLink[r])]) == DAMPER:
        dampedRow(rules, links, r, h)
        kept = links.misses[r]
        for c in range(n):
          kept = kept - links.matrix[r * (n + 1) + c] * links.impulses[c]
        links.matrix[r * (n + 1) + n] = kept
      else:
        for c in range(n):
          links.matrix[r * (n + 1) + c] = links.coupling[r * n + c]
        links.matrix[r * (n + 1) + n] = -links.misses[r] / h
    if solve(links, n) == 0:
      return 0
    for r in range(n):
      links.impulses[r] = links.impulses[r] + links.better[r]
  pushRows(rules, b, links)
  return 1


@wp.func
def steadied(rules: Rules, b: Bodies, links: Links, h: wp.float64,
             time: wp.float64) -> int:
  """The rules kept moving as they must at 'time' (RATTLE's second
  half), the dampers' second half found with them; nought where no
  pivot."""
  n = rules.rows
  armsAll(rules, b, links)
  waysAll(rules, b, links)
  couplingAll(rules, b, links)
  speedsAll(rules, b, links)
  for r in range(n):
    l = int(links.rowLink[r])
    kind = int(links.kind[l])
    if kind == DAMPER:
      dampedRow(rules, links, r, h)
      links.matrix[r * (n + 1) + n] = links.misses[r]
    else:
      for c in range(n):
        links.matrix[r * (n + 1) + c] = links.coupling[r * n + c]
      rate = wp.float64(0.0)
      if kind == ACTUATOR:
        rate = strokeAt(links, l, time)[1]
      links.matrix[r * (n + 1) + n] = rate - links.speeds[r]
  if solve(links, n) == 0:
    return 0
  for r in range(n):
    links.impulses[r] = links.better[r]
  pushRows(rules, b, links)
  return 1


@wp.func
def remember(rules: Rules, b: Bodies, links: Links):
  """How fast each rule moves now, noted before a half step's kicks."""
  if rules.rows == 0:
    return
  armsAll(rules, b, links)
  waysAll(rules, b, links)
  speedsAll(rules, b, links)
  for r in range(rules.rows):
    links.before[r] = links.speeds[r]


@wp.func
def servoTorque(b: Bodies, links: Links, m: int,
                axis: wp.vec3d) -> wp.float64:
  """Motor 'm''s servo torque now: its torque, and its second body's
  turn on its first from the reference, about its axis, against its
  target, stiffness, damping and most."""
  second = int(links.motorEnds[2 * m + 1])
  first = int(links.motorEnds[2 * m])
  secondTurn = qmul(b.turn[second], qconj(b.axes[second]))
  firstTurn = wp.vec4d(ONE, ZERO, ZERO, ZERO)
  spin = spinOf(b, second)
  if first >= 0:
    firstTurn = qmul(b.turn[first], qconj(b.axes[first]))
    spin = spin - spinOf(b, first)
  reference = links.motorReference[m]
  twist = qmul(qmul(qconj(firstTurn), secondTurn), qconj(reference))
  about = apply(qmat(reference), links.motorOwnAxis[m])
  along = twist[1] * about[0] + twist[2] * about[1] + twist[3] * about[2]
  angle = wp.float64(2.0) * wp.atan2(along, twist[0])
  torque = (links.motorDrive[7 * m]
            + links.motorDrive[7 * m + 2]
            * (links.motorDrive[7 * m + 1] - angle)
            - links.motorDrive[7 * m + 3] * dot3(spin, axis))
  most = links.motorDrive[7 * m + 4]
  return wp.max(-most, wp.min(most, torque))


@wp.func
def twistBody(b: Bodies, k: int, twist: wp.vec3d):
  """Body 'k' given the angular impulse 'twist' (in the world), booked
  as an actuator's work."""
  b.momentum[k] = b.momentum[k] + apply(wp.transpose(qmat(b.turn[k])),
                                        twist)
  at = k * 2 * KINDS + 2 * 2
  b.given[at + 1] = b.given[at + 1] + twist


@wp.func
def tractionShare(b: Bodies, links: Links, m: int, first: int,
                  second: int, axis: wp.vec3d, torque: wp.float64,
                  limit: wp.float64) -> wp.float64:
  """The share of its torque driveshaft 'm' gives now ('_world.
  _tractionShare'): all of it while its wheel's rim outruns the first
  body's speed along its own x by no more than 'limit' of it (3 m/s at
  least), none by twice."""
  turning = qmat(b.turn[first])
  forward = apply(turning, links.motorForward[m])
  left = apply(turning, links.motorLeft[m])
  speed = dot3(b.velocity[first], forward)
  rim = links.motorDrive[7 * m + 6] * dot3(
    spinOf(b, second) - spinOf(b, first), left)
  ahead = ONE
  if torque * dot3(axis, left) < ZERO:
    ahead = -ONE
  slip = ahead * (rim - speed) / wp.max(wp.abs(speed), wp.float64(3.0))
  return wp.max(ZERO, wp.min(ONE, TWO - slip / limit))


@wp.func
def shaftKick(b: Bodies, links: Links, m: int, axis: wp.vec3d,
              hh: wp.float64):
  """Driveshaft 'm' (a motor with a bearer): its second body twisted
  about 'axis' by its torque for 'hh' s (less, with damping, an inboard
  brake's on the shaft's rate), its first back along the bisector of
  the shaft's line and the axis (a constant-velocity joint's), its
  bearer the difference."""
  first = int(links.motorEnds[2 * m])
  second = int(links.motorEnds[2 * m + 1])
  inner = b.place[first] + apply(qmat(b.turn[first]),
                                 links.motorArms[2 * m])
  outer = b.place[second] + apply(qmat(b.turn[second]),
                                  links.motorArms[2 * m + 1])
  line = outer - inner
  size = wp.sqrt(dot3(line, line))
  if dot3(line, axis) < ZERO:
    size = -size
  line = line / size
  middle = (line + axis) * wp.float64(0.5)
  torque = links.motorDrive[7 * m]
  limit = links.motorDrive[7 * m + 5]
  if limit > ZERO and torque != ZERO:
    torque = torque * tractionShare(b, links, m, first, second, axis,
                                    torque, limit)
  bearer = int(links.motorBearer[m])
  damping = links.motorDrive[7 * m + 3]
  if damping > ZERO:
    rate = (dot3(axis, spinOf(b, second) - spinOf(b, bearer))
            + dot3(middle, spinOf(b, bearer) - spinOf(b, first)))
    most = links.motorDrive[7 * m + 4]
    torque = torque - wp.max(-most, wp.min(most, damping * rate))
  torque = torque * hh
  twistBody(b, second, axis * torque)
  twistBody(b, bearer, (middle - axis) * torque)
  twistBody(b, first, middle * (-torque))


@wp.func
def motorsKick(rules: Rules, b: Bodies, links: Links, hh: wp.float64):
  """The bodies twisted for 'hh' s by the motors: each one's second body
  about its axis by its torque (a servo's worked out now,
  'servoTorque'), its first (if a body) back, booked as an actuator's
  work; a driveshaft's as 'shaftKick' says."""
  for m in range(rules.motors):
    second = int(links.motorEnds[2 * m + 1])
    turning = qmat(b.turn[second])
    axis = apply(turning, links.motorAxis[m])
    if links.motorBearer[m] >= 0:
      shaftKick(b, links, m, axis, hh)
      continue
    torque = links.motorDrive[7 * m]
    if links.motorDrive[7 * m + 2] > ZERO or (
            links.motorDrive[7 * m + 3] > ZERO):
      torque = servoTorque(b, links, m, axis)
    twist = axis * (torque * hh)
    b.momentum[second] = b.momentum[second] + apply(wp.transpose(turning),
                                                    twist)
    at = second * 2 * KINDS + 2 * 2
    b.given[at + 1] = b.given[at + 1] + twist
    first = int(links.motorEnds[2 * m])
    if first >= 0:
      back = qmat(b.turn[first])
      b.momentum[first] = b.momentum[first] - apply(wp.transpose(back),
                                                    twist)
      at = first * 2 * KINDS + 2 * 2
      b.given[at + 1] = b.given[at + 1] - twist


@wp.func
def dragsKick(rules: Rules, b: Bodies, links: Links, hh: wp.float64):
  """The bodies the air drags pushed back for 'hh' s: half its density
  times their drag area ('dragPull') times their speed squared, booked
  as a damper's heat."""
  for d in range(rules.drags):
    k = int(links.dragBody[d])
    if asleep(rules, b, k) != 0:
      continue
    velocity = b.velocity[k]
    speed = wp.sqrt(dot3(velocity, velocity))
    impulse = velocity * (-links.dragPull[d] * speed * hh)
    b.velocity[k] = velocity + impulse / b.mass[k]
    at = k * 2 * KINDS + 2 * DAMPER
    b.given[at] = b.given[at] + impulse


@wp.func
def kicked(rules: Rules, b: Bodies, links: Links, t: Touches, step: int,
           half: int, hh: wp.float64):
  """A half step's kicks: the rules' speeds noted, then gravity and the
  ground, the springs, the contacts and the grease."""
  remember(rules, b, links)
  for k in range(rules.bodies):
    groundKick(rules, b, k, hh)
  springsKick(rules, b, links, hh)
  motorsKick(rules, b, links, hh)
  dragsKick(rules, b, links, hh)
  contactsKick(rules, b, t, hh)
  greaseKick(rules, b, step, half, hh)


@wp.func
def touchingPair(rules: Rules, t: Touches, c: int) -> int:
  """Whether contact 'c's bodies touch now: either way round holding,
  or for a round contact (numbered after the edges' ones) its ball
  holding."""
  if c >= rules.contacts:
    i = c - rules.contacts
    first = int(t.roundSlotFirst[i])
    for slot in range(first, first + int(t.roundSlotCount[i])):
      if t.roundOn[slot] != 0:
        return 1
    return 0
  if t.entryOn[2 * c] != 0 or t.entryOn[2 * c + 1] != 0:
    return 1
  return 0


@wp.func
def otherOf(t: Touches, c: int, k: int) -> int:
  """The body at contact 'c's other end from body 'k'."""
  first = int(t.pair[2 * c])
  if first == k:
    return int(t.pair[2 * c + 1])
  return first


@wp.func
def woken(rules: Rules, b: Bodies, t: Touches):
  """Every body asleep touching one awake and moving woken, and every
  body asleep touching one so woken, at once, as '_woken' wakes them
  (walked from the awake bodies along each body's contacts); the
  touches found anew if any woke."""
  for k in range(rules.bodies):
    b.asleepNow[k] = asleep(rules, b, k)
    b.woken[k] = 0
  queued = int(0)
  for k in range(rules.bodies):
    if b.asleepNow[k] != 0 or stillOf(rules, b, k) != 0:
      continue
    for j in range(int(t.bodyFirst[k]), int(t.bodyFirst[k + 1])):
      c = int(t.bodyContacts[j])
      other = otherOf(t, c, k)
      if touchingPair(rules, t, c) != 0 and b.asleepNow[other] != 0:
        if b.woken[other] == 0:
          b.woken[other] = 1
          t.queue[queued] = other
          queued = queued + 1
  taken = int(0)
  while taken < queued:
    k = int(t.queue[taken])
    taken = taken + 1
    for j in range(int(t.bodyFirst[k]), int(t.bodyFirst[k + 1])):
      c = int(t.bodyContacts[j])
      other = otherOf(t, c, k)
      if touchingPair(rules, t, c) != 0 and b.asleepNow[other] != 0:
        if b.woken[other] == 0:
          b.woken[other] = 1
          t.queue[queued] = other
          queued = queued + 1
  for k in range(rules.bodies):
    if b.woken[k] != 0:
      b.rest[k] = ZERO
      t.fresh[0] = 0


@wp.func
def slept(rules: Rules, b: Bodies, t: Touches, h: wp.float64):
  """How long each body that may sleep has been still counted, and
  those still long enough whose every touching body is asleep or still
  put to sleep, stopped, as '_slept' does; one that may not yet waits
  half the settling again."""
  for k in range(rules.bodies):
    b.asleepNow[k] = asleep(rules, b, k)
    b.stillNow[k] = 0
    if b.asleepNow[k] == 0:
      b.stillNow[k] = stillOf(rules, b, k)
  for k in range(rules.bodies):
    if b.free[k] != 0 and b.asleepNow[k] == 0:
      if b.stillNow[k] != 0:
        b.rest[k] = b.rest[k] + h
      else:
        b.rest[k] = ZERO
  for k in range(rules.bodies):
    if b.free[k] == 0 or b.asleepNow[k] != 0 or b.rest[k] < rules.settle:
      continue
    ready = int(1)
    for j in range(int(t.bodyFirst[k]), int(t.bodyFirst[k + 1])):
      c = int(t.bodyContacts[j])
      other = otherOf(t, c, k)
      if touchingPair(rules, t, c) != 0 and b.asleepNow[other] == 0 and (
          b.stillNow[other] == 0):
        ready = int(0)
    if ready != 0:
      b.velocity[k] = wp.vec3d(ZERO, ZERO, ZERO)
      b.momentum[k] = wp.vec3d(ZERO, ZERO, ZERO)
    else:
      b.rest[k] = HALF * rules.settle


@wp.func_native("""
#if defined(__CUDA_ARCH__)
__syncthreads();
#endif
""")
def barrier():
  """Every thread of the block waits here for the rest (on a GPU; on
  the CPU, one thread running, nothing to wait for)."""
  ...


@wp.func
def skinsPar(rules: Rules, b: Bodies, t: Touches, tid: int,
             n: int) -> int:
  """'skinsAll' side by side, thread 'tid' of 'n' taking every n-th
  body and skin point (the boxes grown atomically); returns whether the
  touches are to be found anew."""
  for k in range(tid, rules.bodies, n):
    turning = qmat(b.turn[k])
    t.turning[k] = turning
    t.own[k] = ownTurning(b, k)
    t.spin[k] = apply(turning, heldSpin(b.momentum[k], b.moments[k]))
  look = int(0)
  if t.fresh[0] == 0:
    look = int(1)
  every = t.fresh[1]
  if look != 0:
    for k in range(tid, rules.bodies, n):
      if every != 0 or asleep(rules, b, k) == 0:
        t.boxLow[k] = b.place[k]
        t.boxHigh[k] = b.place[k]
  barrier()
  if look != 0:
    for i in range(tid, t.skinBody.shape[0], n):
      k = int(t.skinBody[i])
      if k < 0:
        continue
      if every == 0 and asleep(rules, b, k) != 0:
        continue
      outward = apply(t.turning[k], t.skinArm[i])
      place = b.place[k] + outward
      t.skinOut[i] = outward
      t.skinPlace[i] = place
      wp.atomic_min(t.boxLow, k, place)
      wp.atomic_max(t.boxHigh, k, place)
  barrier()
  if tid == 0 and look != 0:
    t.fresh[0] = 1
    t.fresh[1] = 0
  return look


@wp.func
def contactsKickPar(rules: Rules, b: Bodies, t: Touches, hh: wp.float64,
                    tid: int, n: int):
  """'contactsKick' side by side: each way round of each contact
  opened ('entryOpen'), then every skin point pressed by a thread of
  its own ('touchPoint'), every round contact by one ('roundContact'),
  the pushes added atomically, then given each body."""
  if rules.contacts == 0 and rules.rounds == 0:
    return
  for k in range(tid, rules.bodies, n):
    b.pushing[2 * k] = wp.vec3d(ZERO, ZERO, ZERO)
    b.pushing[2 * k + 1] = wp.vec3d(ZERO, ZERO, ZERO)
  barrier()
  if rules.contacts > 0:
    look = skinsPar(rules, b, t, tid, n)
    for e in range(tid, 2 * rules.contacts, n):
      c = e // 2
      way = e - 2 * c
      opened = entryOpen(rules, b, t, c, way, 1, look)
      t.entryOpenNow[e] = opened
      if opened != 0:
        if look != 0:
          t.entryFound[e] = 0
        t.entryOn[e] = 0
    barrier()
    for slot in range(tid, t.holdEntry.shape[0], n):
      e = int(t.holdEntry[slot])
      if e < 0:
        continue
      if t.entryOpenNow[e] == 0:
        continue
      c = e // 2
      way = e - 2 * c
      got = touchPoint(rules, b, t, c, way, slot - int(t.entryHold[e]),
                       hh, 1, look)
      if got[2] != ZERO:
        wp.atomic_max(t.entryFound, e, 1)
      if got[3] != ZERO:
        wp.atomic_max(t.entryOn, e, 1)
  for i in range(tid, rules.rounds, n):
    roundContact(rules, b, t, i, hh, 1, ZERO)
  barrier()
  for k in range(tid, rules.bodies, n):
    if asleep(rules, b, k) != 0:
      continue
    impulse = b.pushing[2 * k]
    twist = b.pushing[2 * k + 1]
    b.velocity[k] = b.velocity[k] + impulse * (ONE / b.mass[k])
    b.momentum[k] = b.momentum[k] + apply(wp.transpose(qmat(b.turn[k])),
                                          twist)
    at = k * 2 * KINDS + 2 * CONTACT
    b.given[at] = b.given[at] + impulse
    b.given[at + 1] = b.given[at + 1] + twist
  barrier()


@wp.func
def kickedPar(rules: Rules, b: Bodies, links: Links, t: Touches,
              step: int, half: int, hh: wp.float64, tid: int, n: int):
  """'kicked' side by side: the rules' speeds noted, the bodies'
  gravity and ground each by a thread, the springs, motors and drags by
  one, the contacts side by side, the grease by one."""
  if tid == 0:
    remember(rules, b, links)
  barrier()
  for k in range(tid, rules.bodies, n):
    groundKick(rules, b, k, hh)
  barrier()
  if tid == 0:
    springsKick(rules, b, links, hh)
    motorsKick(rules, b, links, hh)
    dragsKick(rules, b, links, hh)
  barrier()
  contactsKickPar(rules, b, t, hh, tid, n)
  if tid == 0:
    greaseKick(rules, b, step, half, hh)
  barrier()


@wp.func
def driftOne(rules: Rules, b: Bodies, k: int, h: wp.float64):
  """Body 'k' moved and turned freely for 'h' s, as 'worldRun' drifts
  each (asleep or part of the world, not)."""
  if asleep(rules, b, k) != 0 or fixedBody(b, k) != 0:
    b.drifting[2 * k] = wp.vec3d(ZERO, ZERO, ZERO)
    b.drifting[2 * k + 1] = wp.vec3d(ZERO, ZERO, ZERO)
    return
  setting = spinOf(b, k)
  if b.round[k] > ZERO:
    first = int(b.groundFirst[k])
    if int(b.groundCount[k]) > 0 and b.bristleOn[first] != 0:
      r = b.round[k]
      x = b.bristle[first][0] + r * setting[1] * h
      y = b.bristle[first][1] - r * setting[0] * h
      b.bristle[first] = wp.vec2d(x, y)
  if b.rollAxis[k][0] != ZERO or b.rollAxis[k][1] != ZERO or (
          b.rollAxis[k][2] != ZERO):
    rolled(rules, b, k, setting, h)
  b.place[k] = b.place[k] + b.velocity[k] * h
  turn, momentum = turnedFreely(b.turn[k], b.momentum[k], b.moments[k], h)
  b.turn[k] = turn
  b.momentum[k] = momentum
  b.drifting[2 * k] = b.velocity[k]
  b.drifting[2 * k + 1] = (setting + spinOf(b, k)) * HALF


@wp.func
def rolledSlot(rules: Rules, b: Bodies, t: Touches, slot: int,
               h: wp.float64):
  """Round slot 'slot''s stretch carried on over a drift of 'h' s, as
  'roundsRolled' carries each."""
  if t.roundNoted[slot] == 0 or t.roundOn[slot] == 0:
    return
  i = int(t.roundSlotOf[slot])
  k = int(t.roundBall[i])
  o = int(t.roundOther[i])
  normal = t.roundNormal[slot]
  moving = (b.velocity[k] + cross3(spinOf(b, k), t.roundArm[2 * slot])) - (
    b.velocity[o] + cross3(spinOf(b, o), t.roundArm[2 * slot + 1]))
  across = moving - normal * dot3(moving, normal)
  t.roundStretch[slot] = t.roundStretch[slot] + across * h


@wp.func
def runParallel(rules: Rules, b: Bodies, links: Links, t: Touches,
                out: wp.array(dtype=wp.float64), tid: int, n: int):
  """'worldRun''s steps side by side, thread 'tid' of 'n' in one block
  (user, 2026-11-13: "everything should run on gpu always!"): what each
  body, skin point, contact and round slot needs done by a thread of
  its own, every n-th, the rules, the springs, motors and drags, the
  grease and sleep by thread nought, each phase waiting for the last
  ('barrier'); the work booked atomically (its sums in another order
  than the serial run's: alike but for the last bits)."""
  h = rules.h
  hh = HALF * h
  if tid == 0:
    for k in range(rules.bodies):
      out[6] = out[6] + groundStored(rules, b, k)
    out[7] = contactsStored(rules, b, t)
  barrier()
  for step in range(rules.count):
    now = rules.start + wp.float64(step + 1) * h
    if rules.sleep != 0:
      if tid == 0:
        woken(rules, b, t)
      barrier()
    kickedPar(rules, b, links, t, rules.first + step, 0, hh, tid, n)
    if rules.rows > 0:
      if tid == 0:
        if pulled(rules, b, links, h, now) == 0:
          out[10] = ONE
      barrier()
      if out[10] != ZERO:
        return
    for k in range(tid, rules.bodies, n):
      driftOne(rules, b, k, h)
    barrier()
    if tid == 0:
      t.fresh[0] = 0
    if rules.rounds > 0:
      for slot in range(tid, rules.slots, n):
        rolledSlot(rules, b, t, slot, h)
    barrier()
    kickedPar(rules, b, links, t, rules.first + step, 1, hh, tid, n)
    if rules.rows > 0:
      if tid == 0:
        if steadied(rules, b, links, h, now) == 0:
          out[10] = ONE
      barrier()
      if out[10] != ZERO:
        return
    for k in range(tid, rules.bodies, n):
      for kind in range(KINDS):
        at = k * 2 * KINDS + 2 * kind
        wp.atomic_add(out, kind, dot3(b.given[at], b.drifting[2 * k])
                      + dot3(b.given[at + 1], b.drifting[2 * k + 1]))
        b.given[at] = wp.vec3d(ZERO, ZERO, ZERO)
        b.given[at + 1] = wp.vec3d(ZERO, ZERO, ZERO)
    barrier()
    if rules.sleep != 0:
      if tid == 0:
        slept(rules, b, t, h)
      barrier()
  if tid == 0:
    for k in range(rules.bodies):
      out[8] = out[8] + groundStored(rules, b, k)
    out[9] = contactsStored(rules, b, t)


@wp.kernel
def worldRun(rules: Rules, b: Bodies, links: Links, t: Touches,
             out: wp.array(dtype=wp.float64)):
  """The assembly stepped on 'rules.count' steps of 'rules.h' from
  'rules.start', as 'World.booked' steps it; 'out' the work by kind,
  what the ground and the contacts held before and after, and nought
  where a rule had no pivot (refused). With 'rules.parallel', the same
  steps side by side by the launch's threads, in one block
  ('runParallel'): a GPU's; else by one thread, the reference's order to
  the last bit."""
  if rules.parallel != 0:
    runParallel(rules, b, links, t, out, wp.tid(), rules.threads)
    return
  h = rules.h
  hh = HALF * h
  for k in range(rules.bodies):
    out[6] = out[6] + groundStored(rules, b, k)
  out[7] = contactsStored(rules, b, t)
  for step in range(rules.count):
    now = rules.start + wp.float64(step + 1) * h
    if rules.sleep != 0:
      woken(rules, b, t)
    kicked(rules, b, links, t, rules.first + step, 0, hh)
    if rules.rows > 0:
      if pulled(rules, b, links, h, now) == 0:
        out[10] = ONE
        return
    for k in range(rules.bodies):
      if asleep(rules, b, k) != 0 or fixedBody(b, k) != 0:
        b.drifting[2 * k] = wp.vec3d(ZERO, ZERO, ZERO)
        b.drifting[2 * k + 1] = wp.vec3d(ZERO, ZERO, ZERO)
        continue
      setting = spinOf(b, k)
      if b.round[k] > ZERO:
        first = int(b.groundFirst[k])
        if int(b.groundCount[k]) > 0 and b.bristleOn[first] != 0:
          r = b.round[k]
          x = b.bristle[first][0] + r * setting[1] * h
          y = b.bristle[first][1] - r * setting[0] * h
          b.bristle[first] = wp.vec2d(x, y)
      if b.rollAxis[k][0] != ZERO or b.rollAxis[k][1] != ZERO or (
              b.rollAxis[k][2] != ZERO):
        rolled(rules, b, k, setting, h)
      b.place[k] = b.place[k] + b.velocity[k] * h
      turn, momentum = turnedFreely(b.turn[k], b.momentum[k], b.moments[k],
                                    h)
      b.turn[k] = turn
      b.momentum[k] = momentum
      b.drifting[2 * k] = b.velocity[k]
      b.drifting[2 * k + 1] = (setting + spinOf(b, k)) * HALF
    t.fresh[0] = 0
    if rules.rounds > 0:
      roundsRolled(rules, b, t, h)
    kicked(rules, b, links, t, rules.first + step, 1, hh)
    if rules.rows > 0:
      if steadied(rules, b, links, h, now) == 0:
        out[10] = ONE
        return
    for k in range(rules.bodies):
      for kind in range(KINDS):
        at = k * 2 * KINDS + 2 * kind
        out[kind] = out[kind] + dot3(b.given[at], b.drifting[2 * k]) + (
          dot3(b.given[at + 1], b.drifting[2 * k + 1]))
        b.given[at] = wp.vec3d(ZERO, ZERO, ZERO)
        b.given[at + 1] = wp.vec3d(ZERO, ZERO, ZERO)
    if rules.sleep != 0:
      slept(rules, b, t, h)
  for k in range(rules.bodies):
    out[8] = out[8] + groundStored(rules, b, k)
  out[9] = contactsStored(rules, b, t)
