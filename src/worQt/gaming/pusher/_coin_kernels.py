"""
The Warp kernels 'CoinWorld' steps its coins with: coins as sharp edged
cylinders, the cabinet as boxes and edges, contacts found once a frame
and solved over substeps by sequential impulses, soft and warm started
(the 'soft step' of Box2D v3, in 3D). Every kernel runs on one thread,
in order: the contacts are solved one after another, as Gauss-Seidel
does.

Units are mm, s and g; z is up. Quaternions are Warp's, x y z w.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import warp as wp

wp.config.quiet = True
#  No gradients: Warp would write each kernel backward too, for
#  differentiating through it, which the coins never need; without, the
#  first compile takes 5 s instead of 13
wp.set_module_options({'enable_backward': False})

_UP = wp.constant(wp.vec3(0.0, 0.0, 1.0))
_FEATURES = wp.constant(wp.int64(65536))
_PARTS = wp.constant(wp.int64(4096))


@wp.struct
class Rules:
  """The coin's shape and the numbers the solver keeps to."""
  radius: float
  half: float
  invMass: float
  inertia: wp.vec3  # about the coin's own x, y and axis z
  invInertia: wp.vec3
  gravity: float
  muCoin: float  # coin on coin
  muCabinet: float  # coin on the cabinet
  bounce: float
  bounceFrom: float  # mm/s two must meet at for any bounce
  hitFrom: float  # mm/s two must meet at to be heard
  spec: float  # mm a contact is watched before it touches
  inset: float  # mm in from the rim a coin over another bears
  flat: float  # this square to a face, a coin rests on its face
  push: float  # mm/s overlapping coins are pushed apart at most
  frame: float  # s a frame lasts
  edgeStep: float  # mm between the points an edge bears at
  kCoin: int  # samples round an edge circle of a coin over another
  kBox: int  # samples round an edge circle on a face
  capacity: int  # contacts kept at most


@wp.struct
class Bodies:
  """The coins: where they are, how turned, moving and spinning, where
  they were as the frame began, and whether each is in play."""
  x: wp.array(dtype=wp.vec3)
  q: wp.array(dtype=wp.quat)
  v: wp.array(dtype=wp.vec3)
  w: wp.array(dtype=wp.vec3)
  x0: wp.array(dtype=wp.vec3)
  q0: wp.array(dtype=wp.quat)
  active: wp.array(dtype=int)
  count: int


@wp.struct
class Parts:
  """The cabinet: boxes, each turned by its quaternion, and edges a
  coin's face may lie over, each moving at its velocity; 'elapsed' is
  how long since the frame began, as far as the substep being solved
  reaches."""
  boxCentre: wp.array(dtype=wp.vec3)
  boxHalf: wp.array(dtype=wp.vec3)
  boxTurn: wp.array(dtype=wp.quat)
  boxVelocity: wp.array(dtype=wp.vec3)
  boxes: int
  edgeStart: wp.array(dtype=wp.vec3)
  edgeEnd: wp.array(dtype=wp.vec3)
  edgeVelocity: wp.array(dtype=wp.vec3)
  edges: int
  elapsed: float
  apart: int  # a box whose hits are counted apart (the tray), else -1


@wp.struct
class Contacts:
  """The contacts of a frame. Coin 'i' touches coin 'j', or the
  cabinet's 'part' when 'j' is below nought (a box, or an edge counted
  on from the boxes). 'kind' 1 or 2 marks the lowest point of the top
  or bottom edge circle, found anew each substep; nought a point fixed
  on the coin. 'n' runs from i to j; 'ra' and 'rb' reach the contact
  from each one's middle as the frame began ('rb' is the point itself
  on the cabinet). 'ln', 'l1', 'l2' are the impulses so far along 'n'
  and the tangents, 'lt' the tangential impulse kept for next frame."""
  key: wp.array(dtype=wp.int64)
  i: wp.array(dtype=int)
  j: wp.array(dtype=int)
  part: wp.array(dtype=int)
  kind: wp.array(dtype=int)
  n: wp.array(dtype=wp.vec3)
  t1: wp.array(dtype=wp.vec3)
  t2: wp.array(dtype=wp.vec3)
  ra: wp.array(dtype=wp.vec3)
  rb: wp.array(dtype=wp.vec3)
  mn: wp.array(dtype=float)
  m1: wp.array(dtype=float)
  m2: wp.array(dtype=float)
  mu: wp.array(dtype=float)
  ln: wp.array(dtype=float)
  l1: wp.array(dtype=float)
  l2: wp.array(dtype=float)
  lt: wp.array(dtype=wp.vec3)
  vn0: wp.array(dtype=float)
  top: wp.array(dtype=float)
  count: wp.array(dtype=int)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  SHAPES  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@wp.func
def scaled(a: wp.vec3, b: wp.vec3) -> wp.vec3:
  """Each component of 'a' times that of 'b'."""
  return wp.vec3(a[0] * b[0], a[1] * b[1], a[2] * b[2])


@wp.func
def axisOf(q: wp.quat) -> wp.vec3:
  """The axis of a coin turned by 'q'."""
  return wp.quat_rotate(q, _UP)


@wp.func
def boxDistance(p: wp.vec3, centre: wp.vec3, half: wp.vec3,
                turn: wp.quat) -> wp.vec4:
  """The signed distance from 'p' to the box, turned by 'turn', and the
  box's outward normal nearest it, as (normal, distance)."""
  d = wp.quat_rotate_inv(turn, p - centre)
  a = wp.vec3(wp.abs(d[0]) - half[0], wp.abs(d[1]) - half[1],
              wp.abs(d[2]) - half[2])
  out = wp.vec3(wp.max(a[0], 0.0), wp.max(a[1], 0.0), wp.max(a[2], 0.0))
  lo = wp.length(out)
  n = wp.vec3(0.0)
  dist = float(0.0)
  if lo > 0.0:
    n = wp.vec3(wp.sign(d[0]) * out[0], wp.sign(d[1]) * out[1],
                wp.sign(d[2]) * out[2]) / lo
    dist = lo
  else:
    if a[0] >= a[1] and a[0] >= a[2]:
      n = wp.vec3(wp.sign(d[0]), 0.0, 0.0)
      dist = a[0]
    elif a[1] >= a[2]:
      n = wp.vec3(0.0, wp.sign(d[1]), 0.0)
      dist = a[1]
    else:
      n = wp.vec3(0.0, 0.0, wp.sign(d[2]))
      dist = a[2]
  nw = wp.quat_rotate(turn, n)
  return wp.vec4(nw[0], nw[1], nw[2], dist)


@wp.func
def faceOf(p: wp.vec3, centre: wp.vec3, half: wp.vec3,
           turn: wp.quat) -> int:
  """The face of the box, turned by 'turn', that 'p' is in front of:
  1 + the axis, signed by the side, when 'p' is outside the box across
  that face alone, or inside it, nearest that face; nought when 'p' is
  off an edge or a corner."""
  d = wp.quat_rotate_inv(turn, p - centre)
  outside = int(0)
  face = int(0)
  nearest = float(1.0e9)
  for k in range(3):
    beyond = wp.abs(d[k]) - half[k]
    side = int(1)
    if d[k] < 0.0:
      side = -1
    if beyond > 0.0:
      outside += 1
      face = side * (k + 1)
    elif outside == 0 and -beyond < nearest:
      nearest = -beyond
      face = side * (k + 1)
  if outside > 1:
    face = 0
  return face


@wp.func
def faceDistance(p: wp.vec3, centre: wp.vec3, half: wp.vec3,
                 turn: wp.quat, face: int, give: float) -> wp.vec4:
  """How far 'p' is beyond the box's 'face' (as 'faceOf' gives it), and
  the face's outward normal, as (normal, distance); the distance is a
  million when 'p' is not over the face, 'give' mm round it allowed."""
  d = wp.quat_rotate_inv(turn, p - centre)
  k = wp.abs(face) - 1
  side = float(1.0)
  if face < 0:
    side = -1.0
  n = wp.vec3(0.0)
  n[k] = side
  over = True
  for m in range(3):
    if m != k and wp.abs(d[m]) > half[m] + give:
      over = False
  nw = wp.quat_rotate(turn, n)
  dist = side * d[k] - half[k]
  if not over:
    dist = 1.0e6
  return wp.vec4(nw[0], nw[1], nw[2], dist)


@wp.func
def coinDistance(rules: Rules, b: Bodies, k: int, p: wp.vec3) -> wp.vec4:
  """The signed distance from 'p' to coin 'k', a sharp edged cylinder,
  and its outward normal nearest it, as (normal, distance)."""
  qk = b.q[k]
  lp = wp.quat_rotate_inv(qk, p - b.x[k])
  r = wp.sqrt(lp[0] * lp[0] + lp[1] * lp[1])
  dr = r - rules.radius
  dz = wp.abs(lp[2]) - rules.half
  side = wp.vec3(1.0, 0.0, 0.0)
  if r > 1.0e-9:
    side = wp.vec3(lp[0] / r, lp[1] / r, 0.0)
  face = wp.vec3(0.0, 0.0, wp.sign(lp[2]))
  nl = face
  dist = dz
  if dr > 0.0 and dz > 0.0:
    dist = wp.sqrt(dr * dr + dz * dz)
    nl = (side * dr + face * dz) / dist
  elif dr > dz:
    nl = side
    dist = dr
  nw = wp.quat_rotate(qk, nl)
  return wp.vec4(nw[0], nw[1], nw[2], dist)


@wp.func
def rimPoint(rules: Rules, b: Bodies, k: int, angle: float, top: int,
             reach: float) -> wp.vec3:
  """The point 'reach' out from coin k's axis at 'angle', on its top
  face if 'top' is 1, on its bottom if nought, half way between if 2."""
  z = rules.half
  if top == 0:
    z = -rules.half
  elif top == 2:
    z = 0.0
  return b.x[k] + wp.quat_rotate(b.q[k], wp.vec3(reach * wp.cos(angle),
                                                 reach * wp.sin(angle), z))


@wp.func
def lowest(rules: Rules, b: Bodies, k: int, toward: wp.vec3,
           top: int) -> wp.vec3:
  """The point of coin k's top or bottom edge circle furthest along
  'toward', or the circle's middle if it lies square to it."""
  ax = axisOf(b.q[k])
  z = rules.half
  if top == 0:
    z = -rules.half
  d = toward - ax * wp.dot(toward, ax)
  ld = wp.length(d)
  middle = b.x[k] + ax * z
  if ld < 1.0e-6:
    return middle
  return middle + d * (rules.radius / ld)


@wp.func
def keyOf(section: int, i: int, j: int, feature: int) -> wp.int64:
  """The key of a contact, the same each frame it lasts, and growing in
  the order 'collide' finds contacts."""
  return (((wp.int64(section) * _PARTS + wp.int64(i)) * _PARTS +
           wp.int64(j)) * _FEATURES + wp.int64(feature))


@wp.func
def quickness(rules: Rules, b: Bodies, i: int) -> float:
  """How fast any point of coin i sweeps into new room at most: its
  spin about its own axis turns it in its own place, and is left out."""
  ax = axisOf(b.q[i])
  tumble = b.w[i] - ax * wp.dot(b.w[i], ax)
  return wp.length(b.v[i]) + rules.radius * wp.length(tumble)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  CONTACTS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@wp.func
def turned(rules: Rules, q: wp.quat, t: wp.vec3) -> wp.vec3:
  """The inverse inertia of a coin turned by 'q', applied to 't'."""
  return wp.quat_rotate(q, scaled(wp.quat_rotate_inv(q, t),
                                  rules.invInertia))


@wp.func
def reachOf(rules: Rules, b: Bodies, i: int, d: wp.vec3,
            r: wp.vec3) -> float:
  """How readily coin i gives along 'd' at 'r' from its middle."""
  rd = wp.cross(r, d)
  return rules.invMass + wp.dot(rd, turned(rules, b.q[i], rd))


@wp.func
def partVelocity(parts: Parts, part: int) -> wp.vec3:
  """How fast the cabinet's 'part' moves."""
  if part < parts.boxes:
    return parts.boxVelocity[part]
  return parts.edgeVelocity[part - parts.boxes]


@wp.func
def added(rules: Rules, b: Bodies, c: Contacts, prev: Contacts,
          cursor: wp.array(dtype=int), key: wp.int64, i: int, j: int,
          part: int, kind: int, pa: wp.vec3, pb: wp.vec3, n: wp.vec3,
          mu: float, speed: wp.vec3):
  """Adds the contact of coin i at 'pa' with j (a coin, or below nought
  the cabinet's 'part', moving at 'speed') at 'pb', 'n' from i to j,
  warm started by the impulses of last frame's contact of that key."""
  k = c.count[0]
  if k >= rules.capacity:
    return
  pp = cursor[0]
  last = prev.count[0]
  while pp < last and prev.key[pp] < key:
    pp += 1
  cursor[0] = pp
  ln = float(0.0)
  lt = wp.vec3(0.0)
  if pp < last:
    if prev.key[pp] == key:
      ln = prev.ln[pp]
      lt = prev.lt[pp]
  t1 = wp.vec3(1.0, 0.0, 0.0)
  if wp.abs(n[0]) > 0.7:
    t1 = wp.vec3(0.0, 1.0, 0.0)
  t1 = wp.normalize(t1 - n * wp.dot(t1, n))
  t2 = wp.cross(n, t1)
  ra = pa - b.x[i]
  rb = pb
  kn = reachOf(rules, b, i, n, ra)
  k1 = reachOf(rules, b, i, t1, ra)
  k2 = reachOf(rules, b, i, t2, ra)
  dv = speed - (b.v[i] + wp.cross(b.w[i], ra))
  if j >= 0:
    rb = pb - b.x[j]
    kn += reachOf(rules, b, j, n, rb)
    k1 += reachOf(rules, b, j, t1, rb)
    k2 += reachOf(rules, b, j, t2, rb)
    dv = (b.v[j] + wp.cross(b.w[j], rb)) - (b.v[i] + wp.cross(b.w[i], ra))
  c.key[k] = key
  c.i[k] = i
  c.j[k] = j
  c.part[k] = part
  c.kind[k] = kind
  c.n[k] = n
  c.t1[k] = t1
  c.t2[k] = t2
  c.ra[k] = ra
  c.rb[k] = rb
  c.mn[k] = 1.0 / kn
  c.m1[k] = 1.0 / k1
  c.m2[k] = 1.0 / k2
  c.mu[k] = mu
  c.ln[k] = ln
  c.l1[k] = wp.dot(lt, t1)
  c.l2[k] = wp.dot(lt, t2)
  c.lt[k] = lt
  c.vn0[k] = wp.dot(dv, n)
  c.top[k] = 0.0
  c.count[0] = k + 1


@wp.func
def copied(c: Contacts, src: int, dst: int):
  """Copies contact 'src' over 'dst'."""
  c.key[dst] = c.key[src]
  c.i[dst] = c.i[src]
  c.j[dst] = c.j[src]
  c.part[dst] = c.part[src]
  c.kind[dst] = c.kind[src]
  c.n[dst] = c.n[src]
  c.t1[dst] = c.t1[src]
  c.t2[dst] = c.t2[src]
  c.ra[dst] = c.ra[src]
  c.rb[dst] = c.rb[src]
  c.mn[dst] = c.mn[src]
  c.m1[dst] = c.m1[src]
  c.m2[dst] = c.m2[src]
  c.mu[dst] = c.mu[src]
  c.ln[dst] = c.ln[src]
  c.l1[dst] = c.l1[src]
  c.l2[dst] = c.l2[src]
  c.lt[dst] = c.lt[src]
  c.vn0[dst] = c.vn0[src]
  c.top[dst] = c.top[src]


@wp.func
def apartAt(b: Bodies, c: Contacts, k: int) -> float:
  """How far apart contact k's two points are as the frame begins."""
  pa = c.ra[k] + b.x[c.i[k]]
  pb = c.rb[k]
  if c.j[k] >= 0:
    pb = pb + b.x[c.j[k]]
  return wp.dot(pb - pa, c.n[k])


@wp.func
def reduced(b: Bodies, c: Contacts, start: int):
  """Keeps at most four of the contacts from 'start' on, spread out: the
  deepest, the furthest from it, the furthest from their line and the
  furthest on its other side. Those carried over from last frame are
  preferred, so the same four stay and keep their impulses."""
  stop = c.count[0]
  if stop - start <= 4:
    return
  a = start
  score = float(1.0e9)
  for k in range(start, stop):
    sk = apartAt(b, c, k)
    if c.ln[k] > 0.0:
      sk -= 0.05
    if sk < score:
      score = sk
      a = k
  pa = c.ra[a]
  bb = a
  far = float(-1.0)
  for k in range(start, stop):
    d = wp.length(c.ra[k] - pa)
    if c.ln[k] > 0.0:
      d += 0.5
    if d > far:
      far = d
      bb = k
  pb = c.ra[bb]
  axis = c.n[a]
  cc = a
  best = float(0.0)
  for k in range(start, stop):
    area = wp.dot(wp.cross(pb - pa, c.ra[k] - pa), axis)
    if c.ln[k] > 0.0:
      area *= 1.1
    if wp.abs(area) > wp.abs(best):
      best = area
      cc = k
  dd = a
  other = float(0.0)
  for k in range(start, stop):
    area = wp.dot(wp.cross(pb - pa, c.ra[k] - pa), axis)
    if c.ln[k] > 0.0:
      area *= 1.1
    if area * best < 0.0 and wp.abs(area) > wp.abs(other):
      other = area
      dd = k
  kept = int(0)
  last = int(-1)
  for r in range(4):
    nxt = int(stop)
    if a > last and a < nxt:
      nxt = a
    if bb > last and bb < nxt:
      nxt = bb
    if cc > last and cc < nxt:
      nxt = cc
    if dd > last and dd < nxt:
      nxt = dd
    if nxt < stop:
      copied(c, nxt, start + kept)
      kept += 1
      last = nxt
  c.count[0] = start + kept


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  FINDING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@wp.func
def coinsMet(rules: Rules, b: Bodies, c: Contacts, prev: Contacts,
             cursor: wp.array(dtype=int), i: int, j: int, margin: float):
  """Adds the contacts of coins i and j.

  Two coins near parallel and beside each other at the same level, the
  one's middle within half a thickness of the other's plane, meet rim
  to rim: three points up the rims along the line of their middles,
  square to it, as two discs side by side do, however deep they have
  been pushed into each other: two coins on one floor can only part
  sideways. Two near parallel otherwise press
  square to each other's faces, each from the rim of its face toward
  the other: from points a little in from the rim when one is over the
  other, from five points on the rim toward the other when beside it,
  each bearing only where it is over the other.
  Two not parallel meet at points round each one's edge circles against
  the other's exact shape: all round when one is over the other, else
  five toward it on each edge circle and on the rim half way between."""
  zero = wp.vec3(0.0)
  begin = c.count[0]
  ai = axisOf(b.q[i])
  parallel = wp.abs(wp.dot(ai, axisOf(b.q[j]))) > 0.95
  if parallel:
    d = b.x[j] - b.x[i]
    along = wp.dot(d, ai)
    across = d - ai * along
    rho = wp.length(across)
    if rho > rules.radius and wp.abs(along) < rules.half:
      u = across / rho
      low = wp.max(-rules.half, along - rules.half)
      ceiling = wp.min(rules.half, along + rules.half)
      for k in range(3):
        z = low + (ceiling - low) * 0.5 * float(k)
        pa = b.x[i] + u * rules.radius + ai * z
        pb = b.x[i] + u * (rho - rules.radius) + ai * z
        added(rules, b, c, prev, cursor, keyOf(1, i, j, 400 + k), i, j, -1,
              0, pa, pb, u, rules.muCoin, zero)
      reduced(b, c, begin)
      return
  for side in range(2):
    a = i
    o = j
    if side == 1:
      a = j
      o = i
    local = wp.quat_rotate_inv(b.q[a], b.x[o] - b.x[a])
    rho = wp.sqrt(local[0] * local[0] + local[1] * local[1])
    over = rho <= rules.radius
    count = rules.kCoin
    toward = wp.atan2(local[1], local[0])
    if not over:
      count = 5
    step = 2.0 * wp.pi / float(rules.kCoin)
    reach = rules.radius
    if parallel and over:
      reach = rules.radius - rules.inset
    circles = 2
    if not over and not parallel:
      circles = 3
    ao = axisOf(b.q[o])
    way = wp.sign(wp.dot(b.x[a] - b.x[o], ao))
    facing = int(0)
    if wp.dot(axisOf(b.q[a]), b.x[o] - b.x[a]) > 0.0:
      facing = 1
    for top in range(circles):
      if parallel and top != facing:
        continue
      for s in range(count):
        angle = float(s) * step
        feature = side * 128 + top * 32 + s
        if not over:
          angle = toward + (float(s) - 2.0) * step
          feature = side * 128 + top * 32 + 16 + s
        p = rimPoint(rules, b, a, angle, top, reach)
        sd = coinDistance(rules, b, o, p)
        if parallel:
          lp = p - b.x[o]
          along = wp.dot(lp, ao)
          if wp.length(lp - ao * along) > rules.radius:
            continue
          sd = wp.vec4(ao[0] * way, ao[1] * way, ao[2] * way,
                       way * along - rules.half)
        if sd[3] > margin:
          continue
        no = wp.vec3(sd[0], sd[1], sd[2])
        key = keyOf(1, i, j, feature)
        if a == i:
          added(rules, b, c, prev, cursor, key, i, j, -1, 0, p,
                p - no * sd[3], -no, rules.muCoin, zero)
        else:
          added(rules, b, c, prev, cursor, key, i, j, -1, 0,
                p - no * sd[3], p, no, rules.muCoin, zero)
  reduced(b, c, begin)


@wp.func
def boxMet(rules: Rules, b: Bodies, c: Contacts, prev: Contacts,
           cursor: wp.array(dtype=int), parts: Parts, i: int, bx: int,
           margin: float):
  """Adds the contacts of coin i with box 'bx': while it lies near
  square to the face nearest, points round the edge circle facing it
  (the other, a coin's thickness off, would only crowd the four points
  kept and leave it rocking on two); while it leans, each circle's
  lowest point toward that face. A coin whose
  middle is in front of a face meets that face alone, and only where it
  is over it: a rim slipped a hair past a corner is not taken for being
  inside the box across another face (so a coin dragged against the
  back wall is pushed off it, never down under it). Off an edge or a
  corner, it meets the box's exact shape."""
  centre = parts.boxCentre[bx]
  half = parts.boxHalf[bx]
  turn = parts.boxTurn[bx]
  speed = parts.boxVelocity[bx]
  reach = margin + wp.length(speed) * rules.frame
  far = boxDistance(b.x[i], centre, half, turn)
  if far[3] > rules.radius + reach:
    return
  face = faceOf(b.x[i], centre, half, turn)
  ni = axisOf(b.q[i])
  down = -wp.vec3(far[0], far[1], far[2])
  if face != 0:
    toward = faceDistance(b.x[i], centre, half, turn, face, 1.0e6)
    down = -wp.vec3(toward[0], toward[1], toward[2])
  leaning = down - ni * wp.dot(down, ni)
  square = wp.abs(wp.dot(ni, down)) >= rules.flat
  facing = int(0)
  if wp.dot(ni, down) > 0.0:
    facing = 1
  begin = c.count[0]
  for top in range(2):
    if square and top != facing:
      continue
    for s in range(rules.kBox + 1):
      p = wp.vec3(0.0)
      kind = int(0)
      if s < rules.kBox:
        if not square:
          continue
        angle = 2.0 * wp.pi * (float(s) + 0.5) / float(rules.kBox)
        p = rimPoint(rules, b, i, angle, top, rules.radius)
      else:
        if wp.length(leaning) < 0.05:
          continue
        p = lowest(rules, b, i, down, top)
        kind = 2 - top
      sd = boxDistance(p, centre, half, turn)
      if face != 0:
        sd = faceDistance(p, centre, half, turn, face, 0.5)
      if sd[3] > reach:
        continue
      nb = wp.vec3(sd[0], sd[1], sd[2])
      if kind > 0 and wp.dot(nb, down) > -0.99:
        continue
      added(rules, b, c, prev, cursor, keyOf(0, i, bx, top * 32 + s), i,
            -1, bx, kind, p, p - nb * sd[3], -nb, rules.muCabinet, speed)
  reduced(b, c, begin)


@wp.func
def edgeMet(rules: Rules, b: Bodies, c: Contacts, prev: Contacts,
            cursor: wp.array(dtype=int), parts: Parts, i: int, ed: int,
            margin: float):
  """Adds the contacts of coin i's faces with edge 'ed': points along
  the edge within the coin's reach. An edge bears only on a face."""
  start = parts.edgeStart[ed]
  end = parts.edgeEnd[ed]
  speed = parts.edgeVelocity[ed]
  reach = margin + wp.length(speed) * rules.frame
  run = end - start
  length = wp.length(run)
  along = run / length
  t = wp.dot(b.x[i] - start, along)
  if wp.length(b.x[i] - (start + along * t)) > rules.radius + reach:
    return
  g0 = int(wp.ceil(wp.max(t - rules.radius - reach, 0.0) / rules.edgeStep))
  g1 = int(wp.floor(wp.min(t + rules.radius + reach, length) /
                    rules.edgeStep))
  ni = axisOf(b.q[i])
  part = parts.boxes + ed
  begin = c.count[0]
  for g in range(g0, g1 + 1):
    p = start + along * (float(g) * rules.edgeStep)
    sd = coinDistance(rules, b, i, p)
    if sd[3] > reach:
      continue
    no = wp.vec3(sd[0], sd[1], sd[2])
    if wp.abs(wp.dot(no, ni)) < 0.5:
      continue
    added(rules, b, c, prev, cursor, keyOf(0, i, part, g), i, -1, part, 0,
          p - no * sd[3], p, no, rules.muCabinet, speed)
  reduced(b, c, begin)


@wp.kernel
def collide(rules: Rules, b: Bodies, c: Contacts, prev: Contacts,
            parts: Parts, cursor: wp.array(dtype=int)):
  """Finds the frame's contacts, as the coins lie as it begins: those
  touching, and those that may touch within the frame; the cabinet's
  first, so that, should there be more than room for, a coin is never
  left without its floor."""
  c.count[0] = 0
  cursor[0] = 0
  for i in range(b.count):
    b.x0[i] = b.x[i]
    b.q0[i] = b.q[i]
  for i in range(b.count):
    if b.active[i] == 0:
      continue
    margin = rules.spec + quickness(rules, b, i) * rules.frame
    for bx in range(parts.boxes):
      boxMet(rules, b, c, prev, cursor, parts, i, bx, margin)
    for ed in range(parts.edges):
      edgeMet(rules, b, c, prev, cursor, parts, i, ed, margin)
  for i in range(b.count):
    if b.active[i] == 0:
      continue
    for j in range(i + 1, b.count):
      if b.active[j] == 0:
        continue
      margin = rules.spec + (quickness(rules, b, i) +
                             quickness(rules, b, j)) * rules.frame
      if wp.length(b.x[j] - b.x[i]) <= 2.0 * rules.radius + margin:
        coinsMet(rules, b, c, prev, cursor, i, j, margin)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  SOLVING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@wp.func
def impulsed(rules: Rules, b: Bodies, c: Contacts, k: int, p: wp.vec3):
  """Applies impulse 'p' at contact k: to j along it, to i against."""
  i = c.i[k]
  j = c.j[k]
  b.v[i] = b.v[i] - p * rules.invMass
  b.w[i] = b.w[i] - turned(rules, b.q[i], wp.cross(c.ra[k], p))
  if j >= 0:
    b.v[j] = b.v[j] + p * rules.invMass
    b.w[j] = b.w[j] + turned(rules, b.q[j], wp.cross(c.rb[k], p))


@wp.func
def relative(b: Bodies, c: Contacts, parts: Parts, k: int) -> wp.vec3:
  """How fast j's point of contact k moves away from i's."""
  i = c.i[k]
  j = c.j[k]
  vb = wp.vec3(0.0)
  if j >= 0:
    vb = b.v[j] + wp.cross(b.w[j], c.rb[k])
  else:
    vb = partVelocity(parts, c.part[k])
  return vb - (b.v[i] + wp.cross(b.w[i], c.ra[k]))


@wp.func
def gapOf(rules: Rules, b: Bodies, c: Contacts, parts: Parts,
          k: int) -> float:
  """How far apart contact k's points are now, along its normal; below
  nought where they overlap. A lowest point is found anew, against its
  box, while it still faces the face it was found on."""
  i = c.i[k]
  j = c.j[k]
  if c.kind[k] > 0:
    low = lowest(rules, b, i, c.n[k], 2 - c.kind[k])
    bx = c.part[k]
    centre = parts.boxCentre[bx] + parts.boxVelocity[bx] * parts.elapsed
    sd = boxDistance(low, centre, parts.boxHalf[bx], parts.boxTurn[bx])
    if wp.dot(wp.vec3(sd[0], sd[1], sd[2]), c.n[k]) < -0.99:
      c.ra[k] = low - b.x[i]
      return sd[3]
  pa = b.x[i] + wp.quat_rotate(b.q[i] * wp.quat_inverse(b.q0[i]), c.ra[k])
  pb = c.rb[k]
  if j >= 0:
    pb = b.x[j] + wp.quat_rotate(b.q[j] * wp.quat_inverse(b.q0[j]),
                                 c.rb[k])
  else:
    pb = pb + partVelocity(parts, c.part[k]) * parts.elapsed
  return wp.dot(pb - pa, c.n[k])


@wp.func
def solved(rules: Rules, b: Bodies, c: Contacts, parts: Parts, h: float,
           biased: int, soft: wp.vec3, hard: wp.vec3):
  """One pass over the contacts: each pushed apart as far as needed,
  softly ('soft' between coins, 'hard' against the cabinet: rate, mass
  scale, impulse scale) when 'biased', then held by friction within
  the cone of its push."""
  for k in range(c.count[0]):
    s = gapOf(rules, b, c, parts, k)
    vn = wp.dot(relative(b, c, parts, k), c.n[k])
    ms = float(1.0)
    ims = float(0.0)
    want = float(0.0)
    if s > 0.0:
      want = s / h
    elif biased == 1:
      how = hard
      if c.j[k] >= 0:
        how = soft
      want = wp.max(how[0] * s, -rules.push)
      ms = how[1]
      ims = how[2]
    ln = c.ln[k]
    d = -c.mn[k] * ms * (vn + want) - ims * ln
    fresh = wp.max(ln + d, 0.0)
    d = fresh - ln
    c.ln[k] = fresh
    c.top[k] = wp.max(c.top[k], d)
    impulsed(rules, b, c, k, c.n[k] * d)
    dv = relative(b, c, parts, k)
    f1 = c.l1[k] - c.m1[k] * wp.dot(dv, c.t1[k])
    f2 = c.l2[k] - c.m2[k] * wp.dot(dv, c.t2[k])
    most = c.mu[k] * fresh
    size = wp.sqrt(f1 * f1 + f2 * f2)
    if size > most:
      f1 = f1 * most / size
      f2 = f2 * most / size
    impulsed(rules, b, c, k, c.t1[k] * (f1 - c.l1[k]) +
             c.t2[k] * (f2 - c.l2[k]))
    c.l1[k] = f1
    c.l2[k] = f2


@wp.func
def precessed(rules: Rules, wb: wp.vec3, h: float) -> wp.vec3:
  """A coin's spin 'wb', in its own frame, after 'h' of turning freely:
  Euler's equations taken a step implicitly, by one Newton step, as
  Bullet and Box2D do, for a step taken explicitly feeds a fast spin
  energy (a coin in the tray spun ever faster)."""
  inertia = wp.diag(rules.inertia)
  turning = wp.vec3(rules.inertia[0] * wb[0], rules.inertia[1] * wb[1],
                    rules.inertia[2] * wb[2])
  rest = wp.cross(wb, turning) * h
  slope = inertia + (wp.skew(wb) * inertia - wp.skew(turning)) * h
  return wb - wp.inverse(slope) * rest


@wp.kernel
def substep(rules: Rules, b: Bodies, c: Contacts, parts: Parts, h: float,
            soft: wp.vec3, hard: wp.vec3):
  """One substep: gravity and the coins' own turning, the impulses of
  last substep again, a soft pass, the moves, and a pass to relax."""
  for i in range(b.count):
    if b.active[i] == 0:
      continue
    b.v[i] = b.v[i] + wp.vec3(0.0, 0.0, -rules.gravity) * h
    qi = b.q[i]
    b.w[i] = wp.quat_rotate(qi, precessed(rules, wp.quat_rotate_inv(qi,
                                                                     b.w[i]),
                                          h))
  for k in range(c.count[0]):
    impulsed(rules, b, c, k, c.n[k] * c.ln[k] + c.t1[k] * c.l1[k] +
             c.t2[k] * c.l2[k])
  solved(rules, b, c, parts, h, 1, soft, hard)
  for i in range(b.count):
    if b.active[i] == 0:
      continue
    b.x[i] = b.x[i] + b.v[i] * h
    qi = b.q[i]
    wi = b.w[i]
    b.q[i] = wp.normalize(qi + (wp.quat(wi[0], wi[1], wi[2], 0.0) * qi) *
                          (0.5 * h))
  solved(rules, b, c, parts, h, 0, soft, hard)


@wp.kernel
def finish(rules: Rules, b: Bodies, c: Contacts, parts: Parts,
           stats: wp.array(dtype=float)):
  """Ends the frame: those meeting fast enough bounce, the tangential
  impulses are kept for next frame, and 'stats' notes the contacts, the
  deepest overlap, and the hits: contacts met at over 'hitFrom' mm/s
  that pushed, coin on coin, coin on the cabinet and coin on the box
  counted apart, each how many and how hard the hardest (mm/s)."""
  deepest = float(0.0)
  for k in range(c.count[0]):
    if c.vn0[k] < -rules.hitFrom and c.top[k] > 0.0:
      slot = int(4)
      if c.j[k] >= 0:
        slot = 2
      elif c.part[k] == parts.apart:
        slot = 6
      stats[slot] = stats[slot] + 1.0
      stats[slot + 1] = wp.max(stats[slot + 1], -c.vn0[k])
    if c.vn0[k] < -rules.bounceFrom and c.top[k] > 0.0:
      vn = wp.dot(relative(b, c, parts, k), c.n[k])
      ln = c.ln[k]
      fresh = wp.max(ln - c.mn[k] * (vn + rules.bounce * c.vn0[k]), 0.0)
      impulsed(rules, b, c, k, c.n[k] * (fresh - ln))
      c.ln[k] = fresh
    c.lt[k] = c.t1[k] * c.l1[k] + c.t2[k] * c.l2[k]
    deepest = wp.max(deepest, -gapOf(rules, b, c, parts, k))
  stats[0] = float(c.count[0])
  stats[1] = wp.max(stats[1], deepest)
