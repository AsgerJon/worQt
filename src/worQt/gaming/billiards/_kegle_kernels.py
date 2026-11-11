"""
The Warp kernel 'KegleHits' steps keglebillard's balls and pins with,
together: the balls through their hits on the cushions and each other,
as 'Hits' has them ('_hits_kernels'), on the pins, and on the cloth;
the pins on the balls, on each other, on the cloth and the cushions, as
'PinField.step' has them, the plain Python they are checked against.
One thread, many steps a launch, compiled, so five pins cost next to
nothing.

Units are mm, s and g; z is up; float64 throughout, every number named
so ('ZERO', 'ONE'...), as Warp keeps float64 and float32 apart, and
each name keeps one type all through a kernel. Quaternions are Warp's,
x y z w.
"""
from __future__ import annotations

import warp as wp

from ._hits_kernels import (HitRules, loggedOf, pairPushed, sidePushed,
                            slated, turned)

wp.config.quiet = True
wp.set_module_options({'enable_backward': False})

ZERO = wp.constant(wp.float64(0.0))
ONE = wp.constant(wp.float64(1.0))
HALF = wp.constant(wp.float64(0.5))
TWO = wp.constant(wp.float64(2.0))
TINY = wp.constant(wp.float64(1e-6))
LEAN = wp.constant(wp.float64(0.4))  # cos of the lean the body meets at
BALL_GIVE = wp.constant(wp.float64(3.5))  # 1 + R²/I of a ball, a share
INERTIA = wp.constant(wp.float64(0.4))  # a ball's I over m R²
TURN = wp.constant(wp.float64(6.283185307179586))
UPRIGHT = wp.constant(wp.float64(0.03490658503988659))  # 2 degrees
LYING = wp.constant(wp.float64(1.3962634015954636))  # 80 degrees
POINTS = wp.constant(wp.float64(8.0))  # the foot's points, a number
ZONE = wp.constant(wp.float64(1.0))  # mm: a ball this near is stepped
TOUCH = wp.constant(wp.float64(1e-6))  # mm: nearer than this touches


@wp.struct
class PinRules:
  """The pins' shape and the numbers their contacts keep to."""
  mass: wp.float64
  centre: wp.float64
  height: wp.float64
  widest: wp.float64
  reach: wp.float64
  invAlong: wp.float64
  invAcross: wp.float64
  foot: wp.float64
  gravity: wp.float64
  cloth: wp.float64
  clothDamping: wp.float64
  clothFriction: wp.float64
  rolling: wp.float64
  ballStiff: wp.float64
  ballDamp: wp.float64
  ballFriction: wp.float64
  pinStiff: wp.float64
  pinDamp: wp.float64
  pinFriction: wp.float64
  wallStiff: wp.float64
  wallDamp: wp.float64
  fine: wp.float64
  coarse: wp.float64
  closeBy: wp.float64
  still: wp.float64
  settle: wp.float64
  radius: wp.float64
  ballMass: wp.float64
  sliding: wp.float64
  rollingDecay: wp.float64
  spinDecay: wp.float64
  spinTail: wp.float64
  spinStop: wp.float64
  width: wp.float64
  length: wp.float64
  top: wp.float64
  out: wp.float64
  bed: wp.float64


@wp.struct
class PocketRules:
  """The pockets as 'Motion' has them ('Pockets'): the corners' slots
  'corner' along each cushion, the middles' 'half' either side, the
  holes 'radius' round; and where pocketed balls are kept, 'parked'."""
  corner: wp.float64
  half: wp.float64
  radius: wp.float64
  parked: wp.float64
  apart: wp.float64


@wp.func
def _awayOf(hits: HitRules, x: wp.float64, y: wp.float64,
            side: int) -> wp.vec3d:
  """How far a ball's middle at 'x', 'y' is from cushion 'side' (left,
  right, foot, head), and the way into the table."""
  if side == 0:
    return wp.vec3d(x, ONE, ZERO)
  if side == 1:
    return wp.vec3d(hits.width - x, -ONE, ZERO)
  if side == 2:
    return wp.vec3d(y, ZERO, ONE)
  return wp.vec3d(hits.length - y, ZERO, -ONE)


@wp.func
def isOpen(hits: HitRules, pockets: PocketRules, x: wp.float64,
           y: wp.float64, side: int) -> int:
  """Whether cushion 'side' (left, right, foot, head) is cut away over a
  pocket's slot where a ball at 'x', 'y' would meet it, as
  'Motion.isOpen' has it."""
  along = y
  full = hits.length
  if side >= 2:
    along = x
    full = hits.width
  if along < pockets.corner or along > full - pockets.corner:
    return 1
  if side < 2 and wp.abs(along - HALF * full) < pockets.half:
    return 1
  return 0


@wp.func
def kegleContactsOf(hits: HitRules, pockets: PocketRules,
                    jaws: wp.array(dtype=wp.vec3d),
                    place: wp.array(dtype=wp.vec2d),
                    speed: wp.array(dtype=wp.vec2d), k: int) -> int:
  """Ball 'k's contacts now, as 'contactsOf' finds them, the cushions
  open over the pockets' slots, a slot's jaw counting as its cushion."""
  count = place.shape[0]
  x = place[k][0]
  y = place[k][1]
  vx = speed[k][0]
  vy = speed[k][1]
  bits = int(0)
  for side in range(4 + jaws.shape[0]):
    away = ZERO
    ix = ZERO
    iy = ZERO
    owner = side
    if side < 4:
      if isOpen(hits, pockets, x, y, side) == 1:
        continue
      sided = _awayOf(hits, x, y, side)
      away = sided[0]
      ix = sided[1]
      iy = sided[2]
    else:
      jaw = jaws[side - 4]
      dx = x - jaw[0]
      dy = y - jaw[1]
      away = wp.sqrt(dx * dx + dy * dy)
      if away <= ZERO:
        continue
      ix = dx / away
      iy = dy / away
      owner = int(jaw[2])
    if away >= hits.radius + TOUCH:
      continue
    given = hits.radius - wp.sqrt(away * away + hits.drop * hits.drop)
    if given > ZERO or (given > -TOUCH and ix * vx + iy * vy < ZERO):
      bits = bits | (1 << owner)
  for j in range(count):
    if j == k:
      continue
    dx = place[j][0] - x
    dy = place[j][1] - y
    pressed = TWO * hits.radius - wp.sqrt(dx * dx + dy * dy)
    if pressed <= -TOUCH:
      continue
    if pressed > ZERO or dx * (speed[j][0] - vx) + \
        dy * (speed[j][1] - vy) < ZERO:
      bits = bits | (1 << (4 + j))
  return bits


@wp.func
def kegleCushionsPushed(hits: HitRules, pockets: PocketRules,
                        jaws: wp.array(dtype=wp.vec3d),
                        place: wp.array(dtype=wp.vec2d),
                        speed: wp.array(dtype=wp.vec2d),
                        spin: wp.array(dtype=wp.vec3d), k: int,
                        step: wp.float64) -> wp.float64:
  """Pushes ball 'k' off each cushion it presses for 'step', as
  'cushionsPushed' does, the cushions open over the pockets' slots, and
  off each slot's jaw as off a nose; returns the push up on it."""
  x = place[k][0]
  y = place[k][1]
  lift = ZERO
  for side in range(4):
    if isOpen(hits, pockets, x, y, side) == 0:
      sided = _awayOf(hits, x, y, side)
      lift = sidePushed(hits, speed, spin, k, sided[0], sided[1],
                        sided[2], step, lift)
  for j in range(jaws.shape[0]):
    dx = x - jaws[j][0]
    dy = y - jaws[j][1]
    away = wp.sqrt(dx * dx + dy * dy)
    if away > ZERO and away < hits.radius:
      lift = sidePushed(hits, speed, spin, k, away, dx / away, dy / away,
                        step, lift)
  return lift


@wp.func
def _axis(q: wp.quatd) -> wp.vec3d:
  """The pin's axis, its own z, on the table."""
  return wp.quat_rotate(q, wp.vec3d(ZERO, ZERO, ONE))


@wp.func
def _invTimes(rules: PinRules, axis: wp.vec3d, v: wp.vec3d) -> wp.vec3d:
  """The pin's inverse inertia on the table times 'v'."""
  return rules.invAcross * v + (rules.invAlong - rules.invAcross) * \
    wp.dot(axis, v) * axis


@wp.func
def _give(rules: PinRules, axis: wp.vec3d, arm: wp.vec3d,
          way: wp.vec3d) -> wp.float64:
  """How much the pin's point at 'arm' gives along 'way'."""
  spun = _invTimes(rules, axis, wp.cross(arm, way))
  return ONE / rules.mass + wp.dot(wp.cross(spun, arm), way)


@wp.func
def _toSegment(point: wp.vec3d, start: wp.vec3d,
               end: wp.vec3d) -> wp.float64:
  """How far 'point' is from the segment 'start' to 'end'."""
  way = end - start
  length = wp.dot(way, way)
  share = ZERO
  if length > ZERO:
    share = wp.clamp(wp.dot(point - start, way) / length, ZERO, ONE)
  return wp.length(point - (start + share * way))


@wp.func
def _segments(a0: wp.vec3d, a1: wp.vec3d, b0: wp.vec3d,
              b1: wp.vec3d) -> wp.float64:
  """How near the segments 'a0'-'a1' and 'b0'-'b1' come."""
  d1 = a1 - a0
  d2 = b1 - b0
  r = a0 - b0
  a = wp.dot(d1, d1)
  e = wp.dot(d2, d2)
  f = wp.dot(d2, r)
  c = wp.dot(d1, r)
  b = wp.dot(d1, d2)
  denom = a * e - b * b
  s = ZERO
  if denom > TINY * TINY:
    s = wp.clamp((b * f - c * e) / denom, ZERO, ONE)
  t = ZERO
  if e > ZERO:
    t = (b * s + f) / e
  if t < ZERO:
    t = ZERO
    if a > ZERO:
      s = wp.clamp(-c / a, ZERO, ONE)
  elif t > ONE:
    t = ONE
    if a > ZERO:
      s = wp.clamp((b - c) / a, ZERO, ONE)
  return wp.length((a0 + s * d1) - (b0 + t * d2))


@wp.func
def _footOf(rules: PinRules, p: wp.vec3d, axis: wp.vec3d) -> wp.vec3d:
  """Where the middle of a pin's foot is."""
  return p - rules.centre * axis


@wp.func
def _topOf(rules: PinRules, p: wp.vec3d, axis: wp.vec3d) -> wp.vec3d:
  """Where the top of a pin is."""
  return p + (rules.height - rules.centre) * axis


@wp.func
def zoneOf(rules: PinRules, p: wp.vec3d, q: wp.quatd) -> wp.vec3d:
  """The circle on the cloth round a pin a ball must come into to near
  it, its middle and its size: round the pin's axis seen from above, a
  ball's radius, the pin's widest and 'ZONE' out."""
  axis = _axis(q)
  foot = _footOf(rules, p, axis)
  top = _topOf(rules, p, axis)
  dx = top[0] - foot[0]
  dy = top[1] - foot[1]
  half = HALF * wp.sqrt(dx * dx + dy * dy)
  return wp.vec3d(HALF * (foot[0] + top[0]), HALF * (foot[1] + top[1]),
                  half + rules.radius + rules.widest + ZONE)


@wp.func
def ballsOnPin(rules: PinRules, spheres: wp.array(dtype=wp.vec2d),
               place: wp.array(dtype=wp.vec2d),
               speed: wp.array(dtype=wp.vec2d),
               spin: wp.array(dtype=wp.vec3d),
               pinP: wp.array(dtype=wp.vec3d),
               pinV: wp.array(dtype=wp.vec3d),
               pinQ: wp.array(dtype=wp.quatd),
               pinW: wp.array(dtype=wp.vec3d),
               awake: wp.array(dtype=wp.int32),
               pinNow: wp.array(dtype=wp.int32), i: int,
               dt: wp.float64) -> int:
  """Pushes pin 'i' and the balls meeting it apart for 'dt', with
  friction, as 'PinField._ballsMeet' does, the pin woken; marks pin 'i'
  in 'pinNow' for each ball pressing into it; returns the balls that
  pushed it, a bit each."""
  balls = place.shape[0]
  count = spheres.shape[0]
  ballInertia = INERTIA * rules.ballMass * rules.radius * rules.radius
  axis = _axis(pinQ[i])
  mask = int(0)
  for b in range(balls):
    centre = wp.vec3d(place[b][0], place[b][1], rules.radius)
    flat = wp.vec3d(centre[0] - pinP[i][0], centre[1] - pinP[i][1], ZERO)
    if wp.length(flat) > rules.radius + rules.reach:
      continue
    for k in range(count):
      z = spheres[k][0]
      size = spheres[k][1]
      arm = z * axis
      off = (pinP[i] + arm) - centre
      gap = wp.length(off)
      depth = rules.radius + size - gap
      if depth <= ZERO or gap <= ZERO:
        continue
      pinNow[b] = pinNow[b] | (1 << i)
      way = off / gap
      reach = arm - size * way
      ballArm = rules.radius * way
      ballSpeed = wp.vec3d(speed[b][0], speed[b][1], ZERO) + \
        wp.cross(spin[b], ballArm)
      pinSpeed = pinV[i] + wp.cross(pinW[i], reach)
      closing = wp.dot(ballSpeed - pinSpeed, way)
      push = wp.max(rules.ballStiff * depth + rules.ballDamp * closing,
                    ZERO) * dt
      if push <= ZERO:
        continue
      awake[i] = int(1)
      mask = mask | (1 << b)
      impulse = push * way
      pinV[i] = pinV[i] + impulse / rules.mass
      pinW[i] = pinW[i] + _invTimes(rules, axis, wp.cross(reach, impulse))
      speed[b] = speed[b] - wp.vec2d(impulse[0], impulse[1]) / \
        rules.ballMass
      spin[b] = spin[b] - wp.cross(ballArm, impulse) / ballInertia
      pinSpeed = pinV[i] + wp.cross(pinW[i], reach)
      ballSpeed = wp.vec3d(speed[b][0], speed[b][1], ZERO) + \
        wp.cross(spin[b], ballArm)
      slip = ballSpeed - pinSpeed
      slip = slip - wp.dot(slip, way) * way
      slipSize = wp.length(slip)
      if slipSize > ZERO:
        unit = slip / slipSize
        give = _give(rules, axis, reach, unit) + BALL_GIVE / rules.ballMass
        held = wp.min(rules.ballFriction * push, slipSize / give)
        grip = held * unit
        pinV[i] = pinV[i] + grip / rules.mass
        pinW[i] = pinW[i] + _invTimes(rules, axis, wp.cross(reach, grip))
        speed[b] = speed[b] - wp.vec2d(grip[0], grip[1]) / rules.ballMass
        spin[b] = spin[b] - wp.cross(ballArm, grip) / ballInertia
  return mask


@wp.func
def pinsOnPin(rules: PinRules, spheres: wp.array(dtype=wp.vec2d),
              pinP: wp.array(dtype=wp.vec3d),
              pinV: wp.array(dtype=wp.vec3d),
              pinQ: wp.array(dtype=wp.quatd),
              pinW: wp.array(dtype=wp.vec3d),
              awake: wp.array(dtype=wp.int32),
              credit: wp.array(dtype=wp.int32),
              mover: wp.array(dtype=wp.int32), i: int, dt: wp.float64):
  """Pushes pin 'i', moving, and each pin it meets apart for 'dt', as
  'PinField._pinsMeet' does, the other woken and credited to the ball
  that moved 'i'."""
  pins = pinP.shape[0]
  count = spheres.shape[0]
  axisP = _axis(pinQ[i])
  footI = _footOf(rules, pinP[i], axisP)
  topI = _topOf(rules, pinP[i], axisP)
  for j in range(pins):
    if j == i:
      continue
    if (awake[j] != 0 and j < i) or awake[j] == 2:
      continue
    axisQ = _axis(pinQ[j])
    footJ = _footOf(rules, pinP[j], axisQ)
    topJ = _topOf(rules, pinP[j], axisQ)
    if _segments(footI, topI, footJ, topJ) > TWO * rules.widest:
      continue
    for k in range(count):
      z = spheres[k][0]
      size = spheres[k][1]
      arm = z * axisP
      place = pinP[i] + arm
      if _toSegment(place, footJ, topJ) > size + rules.widest:
        continue
      for m in range(count):
        otherZ = spheres[m][0]
        otherSize = spheres[m][1]
        otherArm = otherZ * axisQ
        off = (pinP[j] + otherArm) - place
        gap = wp.length(off)
        depth = size + otherSize - gap
        if depth <= ZERO or gap <= ZERO:
          continue
        way = off / gap
        reach = arm + size * way
        otherReach = otherArm - otherSize * way
        mine = pinV[i] + wp.cross(pinW[i], reach)
        theirs = pinV[j] + wp.cross(pinW[j], otherReach)
        closing = wp.dot(mine - theirs, way)
        push = wp.max(rules.pinStiff * depth + rules.pinDamp * closing,
                      ZERO) * dt
        if push <= ZERO:
          continue
        awake[j] = int(1)
        if mover[i] >= 0:
          if credit[j] < 0:
            credit[j] = mover[i]
          mover[j] = mover[i]
        impulse = push * way
        pinV[i] = pinV[i] - impulse / rules.mass
        pinW[i] = pinW[i] - _invTimes(rules, axisP,
                                      wp.cross(reach, impulse))
        pinV[j] = pinV[j] + impulse / rules.mass
        pinW[j] = pinW[j] + _invTimes(rules, axisQ,
                                      wp.cross(otherReach, impulse))


@wp.func
def pinOnCloth(rules: PinRules, spheres: wp.array(dtype=wp.vec2d),
               pinP: wp.array(dtype=wp.vec3d),
               pinV: wp.array(dtype=wp.vec3d),
               pinQ: wp.array(dtype=wp.quatd),
               pinW: wp.array(dtype=wp.vec3d),
               awake: wp.array(dtype=wp.int32),
               quiet: wp.array(dtype=wp.float64), i: int, dt: wp.float64):
  """Moves pin 'i', moving, on for 'dt': pulled down, pushed up off the
  cloth where its foot's edge or its surface presses into it, with
  friction, meeting the cushions and rails, blocks it may fly over, off
  the table to lie on the floor, out of play; moved and turned, put to
  sleep once still a while, upright or lying, as 'PinField' does."""
  count = spheres.shape[0]
  pinV[i] = pinV[i] - wp.vec3d(ZERO, ZERO, rules.gravity * dt)
  q = pinQ[i]
  axis = _axis(q)
  e1 = wp.quat_rotate(q, wp.vec3d(ONE, ZERO, ZERO))
  e2 = wp.quat_rotate(q, wp.vec3d(ZERO, ONE, ZERO))
  touching = int(0)
  pressed = ZERO
  total = int(8)
  if axis[2] < LEAN:
    total = int(8) + count
  for k in range(total):
    arm = wp.vec3d(ZERO, ZERO, ZERO)
    size = ZERO
    if k < 8:
      angle = TURN * wp.float64(k) / POINTS
      arm = rules.foot * wp.cos(angle) * e1 + \
        rules.foot * wp.sin(angle) * e2 - rules.centre * axis
    else:
      sphere = spheres[k - 8]
      arm = sphere[0] * axis
      size = sphere[1]
    depth = size - (pinP[i] + arm)[2]
    if depth <= ZERO:
      continue
    touching = int(1)
    arm = arm - wp.vec3d(ZERO, ZERO, size)
    pointSpeed = pinV[i] + wp.cross(pinW[i], arm)
    push = wp.max(rules.cloth * depth - rules.clothDamping *
                  pointSpeed[2], ZERO) * dt
    pressed = pressed + push
    lift = wp.vec3d(ZERO, ZERO, push)
    pinV[i] = pinV[i] + lift / rules.mass
    pinW[i] = pinW[i] + _invTimes(rules, axis, wp.cross(arm, lift))
    pointSpeed = pinV[i] + wp.cross(pinW[i], arm)
    slide = wp.sqrt(pointSpeed[0] * pointSpeed[0] +
                    pointSpeed[1] * pointSpeed[1])
    if slide > ZERO:
      along = wp.vec3d(pointSpeed[0] / slide, pointSpeed[1] / slide, ZERO)
      held = wp.min(rules.clothFriction * push,
                    HALF * slide / _give(rules, axis, arm, along))
      grip = -held * along
      pinV[i] = pinV[i] + grip / rules.mass
      pinW[i] = pinW[i] + _invTimes(rules, axis, wp.cross(arm, grip))
  #  The felt pushing back 'rolling' ahead slows its turning across it.
  if touching != 0:
    across = wp.vec3d(pinW[i][0], pinW[i][1], ZERO)
    turning = wp.length(across)
    if turning > ZERO:
      resist = _invTimes(rules, axis,
                         (-rules.rolling * pressed / turning) * across)
      lost = -wp.dot(resist, across) / turning
      if lost > turning:
        resist = resist * (turning / lost)
      pinW[i] = pinW[i] + resist
  #  The cushions and rails, blocks 'top' high reaching 'out' past the
  #  noses' lines: a pin meets their faces and tops, and flies over.
  for k in range(count):
    arm = spheres[k][0] * axis
    size = spheres[k][1]
    place = pinP[i] + arm
    for wall in range(4):
      sign = ONE
      edge = ZERO
      coordinate = place[0]
      if wall == 1:
        sign = -ONE
        edge = rules.width
      if wall >= 2:
        coordinate = place[1]
      if wall == 3:
        sign = -ONE
        edge = rules.length
      beyond = sign * (edge - coordinate)
      du = beyond - wp.clamp(beyond, ZERO, rules.out)
      dz = place[2] - wp.min(place[2], rules.top)
      apart = wp.sqrt(du * du + dz * dz)
      depth = size - apart
      nu = ZERO
      nz = ZERO
      if apart > ZERO:
        nu = du / apart
        nz = dz / apart
      elif beyond < rules.top - place[2]:
        depth = size + beyond
        nu = -ONE
      else:
        depth = size + rules.top - place[2]
        nz = ONE
      if depth <= ZERO:
        continue
      way = wp.vec3d(-sign * nu, ZERO, nz)
      if wall >= 2:
        way = wp.vec3d(ZERO, -sign * nu, nz)
      reach = arm - size * way
      wallSpeed = pinV[i] + wp.cross(pinW[i], reach)
      push = wp.max(rules.wallStiff * depth - rules.wallDamp *
                    wp.dot(wallSpeed, way), ZERO) * dt
      impulse = push * way
      pinV[i] = pinV[i] + impulse / rules.mass
      pinW[i] = pinW[i] + _invTimes(rules, axis, wp.cross(reach, impulse))
  #  Moved on, then asleep once still a while, upright or lying.
  pinP[i] = pinP[i] + pinV[i] * dt
  spinNow = pinW[i]
  spinQ = wp.quatd(spinNow[0], spinNow[1], spinNow[2], ZERO)
  pinQ[i] = wp.normalize(q + HALF * dt * (spinQ * q))
  #  Past the rails it is off the table: on the floor, out of play.
  p = pinP[i]
  if p[0] < -rules.out or p[0] > rules.width + rules.out or \
      p[1] < -rules.out or p[1] > rules.length + rules.out:
    axisNow = _axis(pinQ[i])
    flatX = axisNow[0]
    flatY = axisNow[1]
    flat = wp.sqrt(flatX * flatX + flatY * flatY)
    if flat < TINY:
      flatX = ONE
      flatY = ZERO
      flat = ONE
    half = wp.sqrt(HALF)
    pinQ[i] = wp.quatd(-half * flatY / flat, half * flatX / flat, ZERO,
                       half)
    pinP[i] = wp.vec3d(p[0], p[1], rules.widest - rules.bed)
    pinV[i] = wp.vec3d(ZERO, ZERO, ZERO)
    pinW[i] = wp.vec3d(ZERO, ZERO, ZERO)
    quiet[i] = ZERO
    awake[i] = int(2)
    return
  tilt = wp.acos(wp.clamp(_axis(pinQ[i])[2], -ONE, ONE))
  pace = wp.length(pinV[i])
  spinning = wp.length(pinW[i]) * rules.height
  if (tilt < UPRIGHT or tilt > LYING) and pace < rules.still and \
      spinning < rules.still:
    quiet[i] = quiet[i] + dt
  else:
    quiet[i] = ZERO
  if quiet[i] >= rules.settle:
    awake[i] = int(0)
    pinV[i] = wp.vec3d(ZERO, ZERO, ZERO)
    pinW[i] = wp.vec3d(ZERO, ZERO, ZERO)
    quiet[i] = ZERO


@wp.func
def ballOnCloth(rules: PinRules, place: wp.array(dtype=wp.vec2d),
                turn: wp.array(dtype=wp.vec4d),
                speed: wp.array(dtype=wp.vec2d),
                spin: wp.array(dtype=wp.vec3d), k: int, dt: wp.float64):
  """Moves ball 'k', touching no cushion and no ball, on the cloth for
  'dt': sliding until it rolls, rolling slowing, its side spin dying;
  moved and turned."""
  unitInertia = INERTIA * rules.radius * rules.radius
  vx = speed[k][0]
  vy = speed[k][1]
  wx = spin[k][0]
  wy = spin[k][1]
  wz = spin[k][2]
  sx = vx - rules.radius * wy
  sy = vy + rules.radius * wx
  skid = wp.sqrt(sx * sx + sy * sy)
  if skid > TINY:
    share = wp.min(rules.sliding * rules.gravity * dt,
                   skid / BALL_GIVE) / skid
    jx = -sx * share
    jy = -sy * share
    vx = vx + jx
    vy = vy + jy
    wx = wx + rules.radius * jy / unitInertia
    wy = wy - rules.radius * jx / unitInertia
  else:
    rolling = wp.sqrt(vx * vx + vy * vy)
    if rolling > ZERO:
      slower = wp.max(rolling - rules.rollingDecay * dt, ZERO) / rolling
      vx = vx * slower
      vy = vy * slower
      wx = -vy / rules.radius
      wy = vx / rules.radius
  side = wp.max(wp.abs(wz) - rules.spinDecay * dt, ZERO)
  if vx == ZERO and vy == ZERO:
    #  Spinning in place: steadily to the knee, then fading, as
    #  'Cloth.spinningAt' has it (the user: dies in no less than ~3 s).
    knee = wp.max(rules.spinDecay * rules.spinTail, rules.spinStop)
    side = wp.abs(wz)
    left = dt
    if side > knee:
      steady = (side - knee) / rules.spinDecay
      if left <= steady:
        side = side - rules.spinDecay * left
        left = ZERO
      else:
        left = left - steady
        side = knee
    if left > ZERO:
      side = side * wp.exp(-left / rules.spinTail)
    if side <= rules.spinStop:
      side = ZERO
  if wz < ZERO:
    side = -side
  speed[k] = wp.vec2d(vx, vy)
  spin[k] = wp.vec3d(wx, wy, side)
  place[k] = place[k] + wp.vec2d(vx * dt, vy * dt)
  turn[k] = turned(turn[k], wx * dt, wy * dt, side * dt)


@wp.kernel
def kegleRun(hits: HitRules, rules: PinRules, pockets: PocketRules,
             holes: wp.array(dtype=wp.vec2d),
             jaws: wp.array(dtype=wp.vec3d),
             spheres: wp.array(dtype=wp.vec2d),
             place: wp.array(dtype=wp.vec2d),
             turn: wp.array(dtype=wp.vec4d),
             speed: wp.array(dtype=wp.vec2d),
             spin: wp.array(dtype=wp.vec3d),
             settling: wp.array(dtype=wp.int32),
             going: wp.array(dtype=wp.int32),
             pinGoing: wp.array(dtype=wp.int32),
             pinNow: wp.array(dtype=wp.int32),
             lifts: wp.array(dtype=wp.float64),
             pinP: wp.array(dtype=wp.vec3d),
             pinV: wp.array(dtype=wp.vec3d),
             pinQ: wp.array(dtype=wp.quatd),
             pinW: wp.array(dtype=wp.vec3d),
             awake: wp.array(dtype=wp.int32),
             credit: wp.array(dtype=wp.int32),
             mover: wp.array(dtype=wp.int32),
             quiet: wp.array(dtype=wp.float64), red: wp.int32,
             begun: wp.float64, start: wp.float64, seconds: wp.float64,
             whole: wp.int32, most: wp.int32,
             events: wp.array(dtype=wp.vec4i),
             out: wp.array(dtype=wp.float64)):
  """Steps the balls and the pins together for 'seconds' at most, cut
  short at the end unless 'whole', every ball each step: through its
  hits on a cushion or a ball as 'hitsRun' has them, else on the cloth,
  and on any pin it meets; the pins moving. Hands back once all are
  clear ('out' [2] one): no ball touching a cushion or a ball, no pin
  moving, and no ball moving near a pin ('zoneOf'). 'going' holds the
  balls' contacts as 'hitsRun' has them, 'pinGoing' the pins each ball
  presses into, a bit each; 'awake' 1 a pin moving, 2 one off the table,
  out of play; each contact beginning is written to 'events',
  (step, kind, first, second), kind 0 a cushion, 1 a pair, 2 a pin, 3
  a ball into a hole of 'holes' ('pockets', 'jaws': 'Motion' has them),
  kept far off the table after, where nothing meets it;
  a pin is credited to the first ball to set it going, red when red
  is among them ('red', its index, -1 for none). Time is kept from
  'start', the run begun at 'begun', each step added on, so a run cut
  anywhere goes on the same. 'out': the time now, the steps, whether
  all are clear, how many events."""
  count = place.shape[0]
  pins = pinP.shape[0]
  room = events.shape[0]
  used = start
  steps = int(0)
  clear = int(0)
  logged = int(0)
  while used - begun < seconds and steps < most:
    #  A ball whose middle comes over a hole goes into it, kept far off.
    for k in range(count):
      if place[k][1] < HALF * pockets.parked:
        continue
      for h in range(holes.shape[0]):
        dx = place[k][0] - holes[h][0]
        dy = place[k][1] - holes[h][1]
        if dx * dx + dy * dy <= pockets.radius * pockets.radius:
          place[k] = wp.vec2d(pockets.parked - pockets.apart *
                              wp.float64(h), pockets.parked)
          speed[k] = wp.vec2d(ZERO, ZERO)
          spin[k] = wp.vec3d(ZERO, ZERO, ZERO)
          settling[k] = int(0)
          going[k] = int(0)
          pinGoing[k] = int(0)
          if logged < room:
            events[logged] = wp.vec4i(steps, 3, k, h)
            logged += 1
          break
    #  The balls' contacts now, as 'hitsRun' finds them, the cushions
    #  open over the pockets.
    anyContact = int(0)
    pairs = int(0)
    cushions = int(0)
    for k in range(count):
      mine = kegleContactsOf(hits, pockets, jaws, place, speed, k)
      if mine != 0:
        anyContact = int(1)
      if mine >= 16:
        pairs = int(1)
      if mine & 15 != 0:
        cushions = int(1)
      logged = loggedOf(events, logged, steps, k, mine & (~going[k]),
                        count)
      going[k] = mine
    #  The pins: any moving, a ball moving near one, how fast they close.
    moving = int(0)
    near = int(0)
    fastest = ZERO
    for i in range(pins):
      if awake[i] == 2:
        continue
      axisI = _axis(pinQ[i])
      footI = _footOf(rules, pinP[i], axisI)
      topI = _topOf(rules, pinP[i], axisI)
      pace = wp.length(pinV[i]) + rules.reach * wp.length(pinW[i])
      if awake[i] == 1:
        moving = int(1)
      zone = zoneOf(rules, pinP[i], pinQ[i])
      for b in range(count):
        vx = speed[b][0]
        vy = speed[b][1]
        rolling = wp.sqrt(vx * vx + vy * vy)
        centre = wp.vec3d(place[b][0], place[b][1], rules.radius)
        gap = _toSegment(centre, footI, topI) - rules.radius - rules.widest
        both = rolling + pace
        if gap < both * rules.coarse + ONE:
          fastest = wp.max(fastest, wp.max(both, ONE))
        if rolling > ZERO:
          dx = place[b][0] - zone[0]
          dy = place[b][1] - zone[1]
          off = wp.sqrt(dx * dx + dy * dy) - zone[2]
          if off < ZERO or (off < TOUCH and dx * vx + dy * vy < ZERO):
            near = int(1)
      if awake[i] == 1:
        for j in range(pins):
          if j != i and awake[j] != 2:
            axisJ = _axis(pinQ[j])
            apart = _segments(footI, topI, _footOf(rules, pinP[j], axisJ),
                              _topOf(rules, pinP[j], axisJ)) - \
              TWO * rules.widest
            if apart < TWO * pace * rules.coarse + ONE:
              fastest = wp.max(fastest, wp.max(TWO * pace, ONE))
    if anyContact == 0 and moving == 0 and near == 0:
      clear = int(1)
      break
    dt = rules.coarse
    if fastest > ZERO:
      dt = wp.clamp(rules.closeBy / fastest, rules.fine, rules.coarse)
    if pairs != 0:
      dt = wp.min(dt, hits.caromStep)
    elif cushions != 0:
      dt = wp.min(dt, hits.cushionStep)
    if whole == 0:
      dt = wp.min(dt, seconds - (used - begun))
    #  The balls' pushes on cushions and each other, as in 'hitsRun'.
    for k in range(count):
      lift = ZERO
      if going[k] & 15 != 0:
        lift = kegleCushionsPushed(hits, pockets, jaws, place, speed, spin,
                                   k, dt)
      lifts[k] = lift
    for k in range(count):
      for m in range(count):
        if m > k and (going[k] >> (4 + m)) & 1 == 1:
          pairPushed(hits, place, speed, spin, lifts, 0, k, m, dt)
    #  Balls on pins, each pin credited, each touch beginning logged.
    for b in range(count):
      pinNow[b] = int(0)
    for i in range(pins):
      if awake[i] == 2:
        continue
      mask = ballsOnPin(rules, spheres, place, speed, spin, pinP, pinV,
                        pinQ, pinW, awake, pinNow, i, dt)
      if mask != 0:
        met = int(-1)
        for b in range(count):
          if (mask >> b) & 1 == 1 and met < 0:
            met = b
        if red >= 0:
          if (mask >> red) & 1 == 1:
            met = red
        mover[i] = met
        if credit[i] < 0:
          credit[i] = met
    for b in range(count):
      fresh = pinNow[b] & (~pinGoing[b])
      kept = pinNow[b]
      centre = wp.vec3d(place[b][0], place[b][1], rules.radius)
      for i in range(pins):
        if (fresh >> i) & 1 == 1 and logged < room:
          events[logged] = wp.vec4i(steps, 2, b, i)
          logged += 1
        #  A touch goes on till the ball is 'ZONE' clear of the pin.
        if (pinGoing[b] >> i) & 1 == 1 and (kept >> i) & 1 == 0:
          axisK = _axis(pinQ[i])
          clearOf = _toSegment(centre, _footOf(rules, pinP[i], axisK),
                               _topOf(rules, pinP[i], axisK)) - \
            rules.radius - rules.widest
          if clearOf < ZONE:
            kept = kept | (1 << i)
      pinGoing[b] = kept
    #  Pins on pins, then each pin moving on the cloth.
    for i in range(pins):
      if awake[i] == 1:
        pinsOnPin(rules, spheres, pinP, pinV, pinQ, pinW, awake, credit,
                  mover, i, dt)
    for i in range(pins):
      if awake[i] == 1:
        pinOnCloth(rules, spheres, pinP, pinV, pinQ, pinW, awake, quiet, i,
                   dt)
    #  The balls moved on: on the slate through a hit, else on the cloth.
    for k in range(count):
      if going[k] != 0:
        slated(hits, place, turn, speed, spin, settling, k, lifts[k], dt)
      else:
        ballOnCloth(rules, place, turn, speed, spin, k, dt)
        if pinNow[k] != 0:
          settling[k] = int(0)
    used = used + dt
    steps = steps + 1
    if logged > room - 64:
      break
  out[0] = used
  out[1] = wp.float64(steps)
  out[2] = wp.float64(clear)
  out[3] = wp.float64(logged)
