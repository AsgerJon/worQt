"""
The rail world (user, 2026-11-15: "phys dedicated to rails"; "some
kinda vehicle?"): wheelsets ('_wheelset.wheelsetBody') rolling on a
track ('Ribbon') by the spec "Trains: the math first", every other body
handed to another world ('inner': the walker, the island) as it was.

A wheelset is a free rigid body in the world (float64), stepped every
'RAIL_STEP' s (the spec's stiffness budget: 0.1 ms, explicit), found on
the track each step by projecting its centre onto the ribbon (Newton
from where it was). Each rail meets it at two points ('RAIL_TOP',
'GAUGE_CORNER': knife edges along the track), each a contact of its own
where it lies inside the wheel's turned profile ('profileAt'):

- Normal: a Hertz spring along the profile's normal, N = N0 (q/q0)^1.5
  from Hoffmann's reference contact (a0 2.8134 mm, b0 1.6745 mm at N0
  5073 N; q0 from Hertz for the equal-area circle, 'Q0'), plus
  'CONTACT_DAMPING' on its rate; pushes only.
- Creep: an elastic slip u per contact relaxing over the contact's
  length l = a (the spec's standstill fix): du/dt = w - (V/l) u, solved
  exactly over a step (w the wheel's slip velocity there, V the
  wheelset's speed along the track); xi = u/l; Kalker's linear slope
  (G a b C11, C22) taken to saturation by Polach's law (kA = kS = 1,
  mu constant, 'FRICTION'); the slip held where the law saturates
  ('EPS_MOST').

Gravity, the gyroscopic couple of the spinning axle and the track's
curvature come from the rigid body's own motion: nothing is added for
them. Spin creep, the contact's longitudinal shift with yaw and the
rails' own give are left out (the spec's first slice).

The track may be several, joined by turnouts ('Turnout', user,
2026-11-16: "do all the things", the points among them): each wheelset
on one of them, stepped along the way the turnouts send it ('wayOf':
the tracks within its reach, back and ahead, piece by piece); where its
way leaves one track for another, it is on the other.

A wheelset may ride in a vehicle's frame ('Axlebox', user, 2026-11-16:
a minecart "fr"): the frame stays in the inner world (solid: walked in,
loaded, punted), and the two worlds trade every 'exchange' s: each
wheelset steps through it against its boxes, carried on with the
frame's motion as it was at the trade's start (straight on, turning as
it turned); the frame takes what its boxes pushed it with, all at
once, then the inner world steps. Explicit both ways: a box of
stiffness k on a frame of mass m holds while sqrt(k/m) 'exchange' stays
under about 1.4 (here about 0.2: the trade damps a little, never
grows).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import bisect
import math

from .._assembly import Assembly
from .._body import Body, State
from .._vectors import matrixOf, solved, turnOf as quaternionOf
from ._axlebox import Axlebox, brakeOf, motorOf, palmgrenOf
from ._turnout import wayOf
from ._wheelset import GAUGE_CORNER, NOMINAL, RADIUS, RAIL_TOP, profileAt
from ._wheelset import radiusOf

#  The step, s.
RAIL_STEP = 1e-4
#  The reference contact (Hoffmann 2006, appendix B: S1002 on UIC60):
#  its load, N, its semi-axes, m, Kalker's coefficients there, the shear
#  modulus, N/m^2; the approach at that load, m (Hertz for a circle of
#  the same area: d = 3N/(4E* sqrt(ab)), E* = E/(2(1 - nu^2)) with E =
#  2.1e11, nu = 0.27: 15.5 um); the contact's damping, N s/m (Hoffmann).
N0, A0, B0 = 5073.0, 2.8134e-3, 1.6745e-3
C11, C22, SHEAR = 4.8530, 4.5548, 8.27e10
Q0 = 3.0 * N0 / (4.0 * (2.1e11 / (2.0 * (1.0 - 0.27 ** 2)))
                 * math.sqrt(A0 * B0))
CONTACT_DAMPING = 1.5e5
#  Friction (dry, Hoffmann), and how far Polach's epsilon may grow before
#  the slip is held (the bristle slips: 0.99 of the friction).
FRICTION, EPS_MOST = 0.30, 60.0
#  Gravity, m/s^2; how deep in a rail a wheelset may be before it has
#  lost its track, m; how far across from the track's middle (its flange
#  past the rail) and how far up off the rails (flying) it may be, m: past
#  any, it is off the rails ('derailed'; user, 2026-11-16: "derail
#  shouldn't mean RuntimeError!").
GRAVITY = (0.0, 0.0, -9.81)
LOST = 0.05
OFF_ACROSS, OFF_UP = 0.06, 0.3
#  The rail's two points (y across from the middle, z up from the top).
POINTS = (RAIL_TOP, GAUGE_CORNER)
#  How often the rail world and the inner world trade the axleboxes'
#  pushes, s.
EXCHANGE = 2e-3
#  How far either way of a wheelset its way reaches at least in a call
#  (and half again as far as it may go in it), m.
REACH = 0.5
#  How far apart the places a wheelset is first looked for at lie along
#  each track, m; how near a branch's start must be to its points, m;
#  how near a track's end to its start for it to run round (closed), m.
SAMPLES, TOE_NEAR, CLOSED_NEAR = 0.5, 1e-6, 1e-4


class RailWorld:
  """
  RailWorld steps the wheelsets of an assembly (its bodies that are
  'body', or any of them if it is a tuple of wheelsets of any sizes:
  'wheelBodies') rolling on 'track' (and on 'others', tracks joined to
  it and
  to each other by 'turnouts': 'tracks' holds them all, 'track' first)
  every 'step' s, their rails gripping at
  'friction' (nought: none, frictionless), and hands the rest to 'inner'
  (another world, 'advancedAll' alike), the connections touching a
  wheelset dropped but its axleboxes ('Axlebox'), stepped here, traded
  with the inner world every 'exchange' s. On a 'device' of Warp's the
  wheelsets step in the kernel 'railRun' ('RailRun': one thread each,
  float32 in the track's frame); with the small steps on that device
  too every trade stays there, nothing back in Python till the call's
  end. None steps them in plain Python, the reference the kernel is
  held to. 'rolling' holds each
  wheelset's own state by its index: which track it is on ('track', its
  index among 'tracks') and where along it ('s'), each contact's elastic
  slip ('slips') and its last loads
  ('loads', N, by contact); 'boxLoads' each axlebox's push over the last
  call, N, its mean (its last step's swings with the trade), by the
  axlebox. A wheelset off the rails ('OFF_ACROSS' across, 'OFF_UP' up,
  'LOST' into a rail, or off the stretch of track the kernel knew) is
  stepped no more in the call: it is held where it was, its boxes push
  nothing, and its index is in 'derailed' (each call's own) for the
  world to take it over as a free body.
  """

  def __init__(self, inner: object, track: object, body: object,
               step: float = RAIL_STEP,
               friction: float = FRICTION,
               exchange: float = EXCHANGE, device: str = None,
               others: tuple = (), turnouts: tuple = ()) -> None:
    self.wheelBodies = (body,) if isinstance(body, Body) else tuple(body)
    body = self.wheelBodies[0]
    self.inner, self.track, self.body, self.step = inner, track, body, step
    self.friction, self.exchange, self.boxLoads = friction, exchange, {}
    self.device, self._run, self.derailed = device, None, set()
    self.tracks = (track,) + tuple(others)
    self.turnouts = tuple(turnouts)
    self.lengths = tuple(t.length for t in self.tracks)
    self.tracksSegments = tuple(t.segments() for t in self.tracks)
    self.segments = self.tracksSegments[0]
    self.split, self.rolling, self.params = None, {}, {}
    self._joined()
    self.samples = []
    for t, ribbon in enumerate(self.tracks):
      for k in range(int(ribbon.length / SAMPLES) + 1):
        place, frame = ribbon.frameAt(SAMPLES * k)
        self.samples.append((t, SAMPLES * k, tuple(float(x) for x in place),
                             tuple(float(x) for x in frame[:, 2])))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def advancedAll(self, assembly: Assembly, states: tuple,
                  seconds: float, start: float = 0.0) -> tuple:
    """The 'advancedAll' method returns the bodies of 'assembly'
    'seconds' on from 'states': the wheelsets rolled on the track, the
    rest stepped by the inner world."""
    if seconds <= 0.0:
      return tuple(states)
    self.derailed = set()
    inner, kept, rails, boxes = self._splitOf(assembly)
    if boxes:
      return self._traded(assembly, (inner, kept, rails, boxes), states,
                          seconds, start)
    out = list(states)
    if kept:
      stepped = self.inner.advancedAll(inner, tuple(states[i] for i in kept),
                                       seconds, start)
      for i, state in zip(kept, stepped):
        out[i] = state
    if self.device is not None and rails:
      self._runOf().rolled(rails, out, seconds, {}, {}, {})
      return tuple(out)
    for i in rails:
      out[i] = self._rolled(i, states[i], seconds)
    return tuple(out)

  def paramsOf(self, index: int) -> tuple:
    """The 'paramsOf' method returns what the wheelset at 'index' (of the
    assembly last split) is: its mass, kg, its moments about its own
    axes, kg m², and its wheels' radius at the nominal circle, m."""
    return self.params[index]

  def frameAt(self, s: float) -> tuple:
    """The 'frameAt' method returns the first track at 's' m along, as
    plain floats: its centre line's place, its frame (nine numbers, row
    by row) and its turn rates there."""
    return self.frameOn(0, s)

  def frameOn(self, track: int, s: float) -> tuple:
    """The 'frameOn' method returns track 'track' (its index) at 's' m
    along, as 'frameAt' does."""
    starts, places, frames, rates = self.tracksSegments[track]
    i = max(0, bisect.bisect_right(starts, s) - 1)
    h = s - starts[i]
    kx, ky, kz = rates[i]
    w2 = kx * kx + ky * ky + kz * kz
    w = math.sqrt(w2)
    theta = w * h
    if theta < 1e-4:
      s1 = h - w2 * h * h * h / 6.0
      s2 = 0.5 * h * h - w2 * h * h * h * h / 24.0
      s3 = h * h * h / 6.0 - w2 * h * h * h * h * h / 120.0
    else:
      sine, cosine = math.sin(theta), math.cos(theta)
      s1, s2, s3 = sine / w, (1.0 - cosine) / w2, (theta - sine) / (w2 * w)
    step = (h + s3 * (kx * kx - w2), s2 * kz + s3 * kx * ky,
            -s2 * ky + s3 * kx * kz)
    turn = ((1.0 + s2 * (kx * kx - w2), -s1 * kz + s2 * kx * ky,
             s1 * ky + s2 * kx * kz),
            (s1 * kz + s2 * kx * ky, 1.0 + s2 * (ky * ky - w2),
             -s1 * kx + s2 * ky * kz),
            (-s1 * ky + s2 * kx * kz, s1 * kx + s2 * ky * kz,
             1.0 + s2 * (kz * kz - w2)))
    f = frames[i]
    p = places[i]
    place = (p[0] + f[0] * step[0] + f[1] * step[1] + f[2] * step[2],
             p[1] + f[3] * step[0] + f[4] * step[1] + f[5] * step[2],
             p[2] + f[6] * step[0] + f[7] * step[1] + f[8] * step[2])
    frame = tuple(f[3 * r] * turn[0][c] + f[3 * r + 1] * turn[1][c]
                  + f[3 * r + 2] * turn[2][c]
                  for r in range(3) for c in range(3))
    return place, frame, rates[i]

  def along(self, place: tuple, s: float = None) -> float:
    """The 'along' method returns where along the first track 'place' (a
    wheelset's centre) lies, as 'foundOn' does, from 's' (None: from the
    nearest of its samples)."""
    way = (((0.0, self.lengths[0], 0, 0.0),), True, True)
    if s is None:
      s = min((sample for sample in self.samples if sample[0] == 0),
              key=lambda sample: _apart(_over(sample, RADIUS), place))[1]
    return self.alongWay(way, place, s)

  def foundOn(self, place: tuple, radius: float = RADIUS) -> tuple:
    """The 'foundOn' method returns which track 'place' (the centre of a
    wheelset of wheels 'radius' m) lies on and where along it (its foot
    on the centre line: the s whose frame's x is square to it): by
    Newton from the sample (every 'SAMPLES' m of every track) whose
    wheelset's centre, a wheel's radius up from the rails, lies nearest
    (where the track passes near itself, a loop's end by its start, the
    rails alone are no guide)."""
    track, s, _, _ = min(self.samples, key=lambda sample: _apart(
      _over(sample, radius), place))
    way = (((0.0, self.lengths[track], track, 0.0),), True, True)
    return track, self.alongWay(way, place, s)

  def wayFor(self, track: int, s: float, reach: float) -> tuple:
    """The 'wayFor' method returns the way a wheelset at 's' m along
    track 'track' may go within 'reach' m either way, as the turnouts
    are set now ('wayOf'; round the closed tracks)."""
    return wayOf(self.lengths, self.turnouts, track, s, reach, reach,
                 self.closed)

  def frameOnWay(self, way: tuple, u: float) -> tuple:
    """The 'frameOnWay' method returns the track 'u' m along 'way' (as
    'wayFor' returns it), as 'frameAt' does: on its piece there."""
    pieces = way[0]
    piece = pieces[0]
    for candidate in pieces:
      if candidate[0] <= u:
        piece = candidate
      else:
        break
    return self.frameOn(piece[2], u + piece[3])

  def onWay(self, way: tuple, u: float) -> tuple:
    """The 'onWay' method returns which track 'u' m along 'way' is on
    and where along it, m (held within the way's ends)."""
    pieces = way[0]
    u = min(max(u, pieces[0][0]), pieces[-1][1])
    piece = pieces[0]
    for candidate in pieces:
      if candidate[0] <= u:
        piece = candidate
      else:
        break
    return piece[2], u + piece[3]

  def alongWay(self, way: tuple, place: tuple, u: float) -> float:
    """The 'alongWay' method returns where along 'way' 'place' lies (its
    foot on the centre line), by Newton from 'u', held within the way's
    ends."""
    low, high = way[0][0][0], way[0][-1][1]
    for _ in range(4):
      at, f, k = self.frameOnWay(way, u)
      dx, dy, dz = place[0] - at[0], place[1] - at[1], place[2] - at[2]
      ahead = f[0] * dx + f[3] * dy + f[6] * dz
      left = f[1] * dx + f[4] * dy + f[7] * dz
      up = f[2] * dx + f[5] * dy + f[8] * dz
      slope = -1.0 + k[2] * left - k[1] * up
      move = -ahead / slope
      u = min(max(u + move, low), high)
      if abs(move) < 1e-10:
        break
    return u

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def memoryOf(self, index: int, state: State) -> dict:
    """The 'memoryOf' method returns what the world keeps of the
    wheelset at 'index' ('rolling'): begun anew when 'state' is not the
    one it last handed back (a reset: found on the track from nothing,
    its slips let go)."""
    memory = self.rolling.get(index)
    if memory is None or memory['state'] is not state:
      track, s = self.foundOn(state.place, self.params[index][2])
      memory = {'track': track, 's': s, 'slips': {}, 'loads': {},
                'state': None}
      self.rolling[index] = memory
    return memory

  def _joined(self, ) -> None:
    """Finds the closed tracks ('closed': each ends where it began, as
    it began, within 'CLOSED_NEAR'); refuses a turnout whose tracks are
    not the world's, or whose branch does not begin at its points,
    along its track there."""
    closed = set()
    for t, length in enumerate(self.lengths):
      start, first, _ = self.frameOn(t, 0.0)
      end, last, _ = self.frameOn(t, length)
      if _apart(start, end) < CLOSED_NEAR ** 2 and max(
          abs(a - b) for a, b in zip(first, last)) < CLOSED_NEAR:
        closed.add(t)
    self.closed = frozenset(closed)
    for turnout in self.turnouts:
      count = len(self.tracks)
      if not (0 <= turnout.track < count and 0 <= turnout.branch < count):
        raise ValueError('a turnout joins tracks %d and %d of %d' % (
          turnout.track, turnout.branch, count))
      if turnout.at > self.lengths[turnout.track]:
        raise ValueError('points %.3f m along a track %.3f m long' % (
          turnout.at, self.lengths[turnout.track]))
      place, frame, _ = self.frameOn(turnout.track, turnout.at)
      start, first, _ = self.frameOn(turnout.branch, 0.0)
      if _apart(place, start) > TOE_NEAR ** 2 or max(
          abs(a - b) for a, b in zip(frame, first)) > TOE_NEAR:
        raise ValueError('track %d does not begin at its points on track '
                         '%d' % (turnout.branch, turnout.track))

  def _runOf(self, ) -> object:
    """Returns the kernel's run on the world's device, made at first
    use."""
    if self._run is None:
      from ._railrun import RailRun
      self._run = RailRun(self, self.device)
    return self._run

  def _splitOf(self, assembly: Assembly) -> tuple:
    """Returns the assembly's bodies but the wheelsets as an assembly of
    their own (its connections renumbered, those touching a wheelset
    dropped), which of the bodies those are, the wheelsets' indices and
    the axleboxes (a frame held in a wheelset refused); made again only
    for another assembly."""
    if self.split is not None and self.split[0] is assembly:
      return self.split[1:]
    rails = tuple(i for i, body in enumerate(assembly.bodies)
                  if any(body is wheels for wheels in self.wheelBodies))
    self.params = {}
    for i in rails:
      body = assembly.bodies[i]
      inertia = body.inertia
      radius = radiusOf(body)
      self.params[i] = (body.mass, (inertia[0][0], inertia[1][1],
                                    inertia[2][2]),
                        RADIUS if radius is None else radius)
    kept = tuple(i for i in range(len(assembly.bodies)) if i not in rails)
    renumbered = {old: new for new, old in enumerate(kept)}
    connections, boxes = [], []
    for connection in assembly.connections:
      if isinstance(connection, Axlebox):
        if connection.wheelset not in rails or connection.frame in rails:
          raise ValueError('an axlebox holds a wheelset in a frame, not '
                           'body %d in body %d' % (connection.wheelset,
                                                    connection.frame))
        boxes.append(connection)
        continue
      fields = [name for name in ('body', 'first', 'second')
                if name in connection._fields]
      if not fields:
        raise TypeError('the rail world cannot renumber a %s' % type(
          connection).__name__)
      indices = [getattr(connection, name) for name in fields]
      if any(index in rails for index in indices if index is not None
             and index >= 0):
        continue
      values = list(connection)
      for name in fields:
        at = connection._fields.index(name)
        index = values[at]
        if index is not None and index >= 0:
          values[at] = renumbered[index]
      connections.append(type(connection)(*values))
    inner = Assembly(tuple(assembly.bodies[i] for i in kept),
                     tuple(connections))
    self.split = (assembly, inner, kept, rails, tuple(boxes))
    return inner, kept, rails, tuple(boxes)

  def _traded(self, assembly: Assembly, split: tuple, states: tuple,
              seconds: float, start: float) -> tuple:
    """Returns the bodies 'seconds' on from 'states', the axleboxes'
    pushes traded every 'exchange' s: each trade the wheelsets stepped
    against their boxes (the frames carried on as they moved), the
    frames pushed by them, the inner world stepped."""
    inner, kept, rails, boxes = split
    held = {}
    for box in boxes:
      held.setdefault(box.wheelset, []).append(box)
    if self._onDevice() and kept:
      return self._tradedOnDevice(split, held, states, seconds, start)
    frames = sorted({box.frame for box in boxes})
    out = list(states)
    count = max(1, math.ceil(seconds / self.exchange - 1e-9))
    h = seconds / count
    for k in range(count):
      pushes = {frame: [0.0] * 6 for frame in frames}
      seen = {id(box): _boxSeen(assembly.bodies[box.frame],
                                out[box.frame], box) for box in boxes}
      if self.device is not None:
        self._runOf().rolled(rails, out, h, held, seen, pushes)
      else:
        for i in rails:
          out[i] = self._rolled(i, out[i], h, held.get(i, ()), seen,
                                pushes)
      for frame in frames:
        out[frame] = _pushed(assembly.bodies[frame], out[frame],
                             pushes[frame])
      if kept:
        stepped = self.inner.advancedAll(
          inner, tuple(out[i] for i in kept), h, start + k * h)
        for i, state in zip(kept, stepped):
          out[i] = state
    return tuple(out)

  def _onDevice(self, ) -> bool:
    """Returns whether the trades can stay on the device: the wheelsets
    step there and the inner world is the small steps there."""
    return self.device is not None and getattr(
      self.inner, 'device', None) == self.device and hasattr(
      self.inner, 'packedFor')

  def _tradedOnDevice(self, split: tuple, held: dict, states: tuple,
                      seconds: float, start: float) -> tuple:
    """Returns the bodies 'seconds' on from 'states', every trade on the
    device (user, 2026-11-16: "Why they going back to fucking python
    bro????"): the inner world's bodies put there once, the trades run
    there ('RailRun.traded'), all handed back once."""
    inner, kept, rails, _ = split
    out = list(states)
    packed = self.inner.packedFor(inner, tuple(states[i] for i in kept))
    trades = max(1, math.ceil(seconds / self.exchange - 1e-9))
    self._runOf().traded(self.inner, packed, inner, kept, rails, out,
                         seconds, start, held, trades)
    for i, state in zip(kept, packed.states()):
      out[i] = state
    return tuple(out)

  def _rolled(self, index: int, state: State, seconds: float,
              boxes: tuple = (), seen: dict = None,
              pushes: dict = None) -> State:
    """Returns the wheelset at 'index' rolled 'seconds' on from 'state'
    (its own state kept in 'rolling'; begun anew when 'state' is not the
    one it last handed back: a reset), held in 'boxes' (each as 'seen'
    at the start, by id; what they push their frames with added to
    'pushes')."""
    for box in boxes:
      self.boxLoads[id(box)] = 0.0
    if index in self.derailed:
      return state
    memory = self.memoryOf(index, state)
    p, q = list(state.place), list(state.turn)
    v, omega = list(state.velocity), list(state.spin)
    count = max(1, math.ceil(seconds / self.step - 1e-9))
    h = seconds / count
    speed = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    way = self.wayFor(memory['track'], memory['s'],
                      REACH + 1.5 * speed * seconds)
    params = self.params[index]
    try:
      for k in range(count):
        self._stepped(memory, params, way, p, q, v, omega, h,
                      (boxes, seen, pushes, k * h, 1.0 / count)
                      if boxes else None)
    except _Derailment:
      self.derailed.add(index)
    memory['track'], memory['s'] = self.onWay(way, memory['s'])
    out = State(tuple(p), tuple(q), tuple(v), tuple(omega))
    memory['state'] = out
    return out

  def _stepped(self, memory: dict, params: tuple, way: tuple, p: list,
               q: list, v: list, omega: list, h: float,
               held: tuple = None) -> None:
    """Steps one wheelset ('params': its mass, moments and wheels'
    radius) 'h' s in place: found on its 'way' (where it is along it
    kept in its 'memory''s 's' for the call), its four
    contacts' forces and torques summed with gravity and its axleboxes'
    ('held': the boxes, as seen, the frames' pushes, the time since the
    trade began; None: free), its motion integrated (semi-implicit
    Euler; its turn by its body-frame spin)."""
    s = self.alongWay(way, p, memory['s'])
    memory['s'] = s
    at, f, _ = self.frameOnWay(way, s)
    d = (p[0] - at[0], p[1] - at[1], p[2] - at[2])
    mass, moments, radius = params
    if abs(f[1] * d[0] + f[4] * d[1] + f[7] * d[2]) > OFF_ACROSS or (
        f[2] * d[0] + f[5] * d[1] + f[8] * d[2] - radius > OFF_UP):
      raise _Derailment()
    m = matrixOf(q)
    axle = (m[0][2], m[1][2], m[2][2])
    leftward = axle[0] * f[1] + axle[1] * f[4] + axle[2] * f[7]
    sign = 1.0 if leftward >= 0.0 else -1.0
    tangent = (f[0], f[3], f[6])
    speed = abs(v[0] * tangent[0] + v[1] * tangent[1] + v[2] * tangent[2])
    force = [mass * GRAVITY[0], mass * GRAVITY[1], mass * GRAVITY[2]]
    torque = [0.0, 0.0, 0.0]
    slips, loads = memory['slips'], memory['loads']
    for side in (1.0, -1.0):
      w = side * sign * NOMINAL
      wheel = (p[0] + axle[0] * w, p[1] + axle[1] * w, p[2] + axle[2] * w)
      ahead = (f[0] * (wheel[0] - at[0]) + f[3] * (wheel[1] - at[1])
               + f[6] * (wheel[2] - at[2]))
      for kind, (across, up) in enumerate(POINTS):
        key = (side, kind)
        y = side * across
        point = (at[0] + f[0] * ahead + f[1] * y + f[2] * up,
                 at[1] + f[3] * ahead + f[4] * y + f[5] * up,
                 at[2] + f[6] * ahead + f[7] * y + f[8] * up)
        pushed = self._contact(key, point, p, m, v, omega, tangent, speed,
                               slips, loads, h, radius)
        if pushed is None:
          continue
        arm = (point[0] - p[0], point[1] - p[1], point[2] - p[2])
        force[0] += pushed[0]
        force[1] += pushed[1]
        force[2] += pushed[2]
        torque[0] += arm[1] * pushed[2] - arm[2] * pushed[1]
        torque[1] += arm[2] * pushed[0] - arm[0] * pushed[2]
        torque[2] += arm[0] * pushed[1] - arm[1] * pushed[0]
    if held is not None:
      self._boxed(held, p, m, v, omega, force, torque, h)
    self._moved(p, q, v, omega, m, force, torque, h, mass, moments)

  def _boxed(self, held: tuple, p: list, m: tuple, v: list, omega: list,
             force: list, torque: list, h: float) -> None:
    """Adds to 'force' and 'torque' what the wheelset's axleboxes push
    it with (each journal sprung and damped back into its box, the
    bearing's and the brake's torque against the axle's turning in it,
    the motor's driving it), and to their frames' pushes the like back,
    over 'h' s."""
    boxes, seen, pushes, since, share = held
    axle = (m[0][2], m[1][2], m[2][2])
    for box in boxes:
      at, moving, arm, swing, axes, spin = seen[id(box)]
      j = box.journal
      a = (m[0][0] * j[0] + m[0][1] * j[1] + m[0][2] * j[2],
           m[1][0] * j[0] + m[1][1] * j[1] + m[1][2] * j[2],
           m[2][0] * j[0] + m[2][1] * j[1] + m[2][2] * j[2])
      out = (p[0] + a[0] - at[0] - moving[0] * since,
             p[1] + a[1] - at[1] - moving[1] * since,
             p[2] + a[2] - at[2] - moving[2] * since)
      rate = (v[0] + omega[1] * a[2] - omega[2] * a[1] - moving[0],
              v[1] + omega[2] * a[0] - omega[0] * a[2] - moving[1],
              v[2] + omega[0] * a[1] - omega[1] * a[0] - moving[2])
      push = [0.0, 0.0, 0.0]
      for e, k, c in zip(axes, box.stiffness, box.damping):
        size = -(k * (e[0] * out[0] + e[1] * out[1] + e[2] * out[2])
                 + c * (e[0] * rate[0] + e[1] * rate[1] + e[2] * rate[2]))
        push[0] += size * e[0]
        push[1] += size * e[1]
        push[2] += size * e[2]
      relative = ((omega[0] - spin[0]) * axle[0]
                  + (omega[1] - spin[1]) * axle[1]
                  + (omega[2] - spin[2]) * axle[2])
      load = math.sqrt(push[0] ** 2 + push[1] ** 2 + push[2] ** 2)
      lean = 1.0 if (axle[0] * axes[1][0] + axle[1] * axes[1][1]
                     + axle[2] * axes[1][2]) >= 0.0 else -1.0
      drag = palmgrenOf(relative, load, box.bearing) + brakeOf(
        relative, box.brake) - lean * motorOf(lean * relative, box.drive,
                                              box.power)
      self.boxLoads[id(box)] += share * load
      force[0] += push[0]
      force[1] += push[1]
      force[2] += push[2]
      torque[0] += a[1] * push[2] - a[2] * push[1] - drag * axle[0]
      torque[1] += a[2] * push[0] - a[0] * push[2] - drag * axle[1]
      torque[2] += a[0] * push[1] - a[1] * push[0] - drag * axle[2]
      lever = (arm[0] + swing[0] * since, arm[1] + swing[1] * since,
               arm[2] + swing[2] * since)
      frame = pushes[box.frame]
      frame[0] -= push[0] * h
      frame[1] -= push[1] * h
      frame[2] -= push[2] * h
      frame[3] += (lever[2] * push[1] - lever[1] * push[2]
                   + drag * axle[0]) * h
      frame[4] += (lever[0] * push[2] - lever[2] * push[0]
                   + drag * axle[1]) * h
      frame[5] += (lever[1] * push[0] - lever[0] * push[1]
                   + drag * axle[2]) * h

  def _contact(self, key: tuple, point: tuple, p: list, m: tuple,
               v: list, omega: list, tangent: tuple, speed: float,
               slips: dict, loads: dict, h: float,
               radius: float = RADIUS) -> tuple | None:
    """Returns the force one rail point puts on the wheelset of wheels
    'radius' m (None where it does not touch: its slip let go): Hertz
    along the profile's normal, creep in the contact's plane from its
    relaxed slip."""
    d = (point[0] - p[0], point[1] - p[1], point[2] - p[2])
    bx = m[0][0] * d[0] + m[1][0] * d[1] + m[2][0] * d[2]
    by = m[0][1] * d[0] + m[1][1] * d[1] + m[2][1] * d[2]
    bz = m[0][2] * d[0] + m[1][2] * d[1] + m[2][2] * d[2]
    rho = math.sqrt(bx * bx + by * by)
    r, slope = profileAt(abs(bz) - NOMINAL, radius)
    if r - rho <= 0.0 or rho <= 0.0:
      slips.pop(key, None)
      loads[key] = 0.0
      return None
    size = math.sqrt(1.0 + slope * slope)
    depth = (r - rho) / size
    if depth > LOST:
      raise _Derailment()
    out = (bx / rho / size, by / rho / size,
           -slope * (1.0 if bz >= 0.0 else -1.0) / size)
    normal = (m[0][0] * out[0] + m[0][1] * out[1] + m[0][2] * out[2],
              m[1][0] * out[0] + m[1][1] * out[1] + m[1][2] * out[2],
              m[2][0] * out[0] + m[2][1] * out[1] + m[2][2] * out[2])
    moving = (v[0] + omega[1] * d[2] - omega[2] * d[1],
              v[1] + omega[2] * d[0] - omega[0] * d[2],
              v[2] + omega[0] * d[1] - omega[1] * d[0])
    sinking = (moving[0] * normal[0] + moving[1] * normal[1]
               + moving[2] * normal[2])
    load = N0 * (depth / Q0) ** 1.5 + CONTACT_DAMPING * sinking
    if load <= 0.0:
      slips.pop(key, None)
      loads[key] = 0.0
      return None
    loads[key] = load
    if self.friction <= 0.0:
      return (-load * normal[0], -load * normal[1], -load * normal[2])
    inward = (-normal[0], -normal[1], -normal[2])
    along = (tangent[0] - (tangent[0] * inward[0] + tangent[1] * inward[1]
                           + tangent[2] * inward[2]) * inward[0],
             tangent[1] - (tangent[0] * inward[0] + tangent[1] * inward[1]
                           + tangent[2] * inward[2]) * inward[1],
             tangent[2] - (tangent[0] * inward[0] + tangent[1] * inward[1]
                           + tangent[2] * inward[2]) * inward[2])
    length = math.sqrt(along[0] ** 2 + along[1] ** 2 + along[2] ** 2)
    t1 = (along[0] / length, along[1] / length, along[2] / length)
    t2 = (inward[1] * t1[2] - inward[2] * t1[1],
          inward[2] * t1[0] - inward[0] * t1[2],
          inward[0] * t1[1] - inward[1] * t1[0])
    w1 = moving[0] * t1[0] + moving[1] * t1[1] + moving[2] * t1[2]
    w2 = moving[0] * t2[0] + moving[1] * t2[1] + moving[2] * t2[2]
    grown = (load / N0) ** (1.0 / 3.0)
    a, b = A0 * grown, B0 * grown
    u1, u2 = slips.get(key, (0.0, 0.0))
    rate = speed / a
    if rate * h > 1e-9:
      fade = math.exp(-rate * h)
      u1 = w1 / rate + (u1 - w1 / rate) * fade
      u2 = w2 / rate + (u2 - w2 / rate) * fade
    else:
      u1, u2 = u1 + w1 * h, u2 + w2 * h
    g1, g2 = C11 * u1 / a, C22 * u2 / a
    pull = math.sqrt(g1 * g1 + g2 * g2)
    f1 = f2 = 0.0
    if pull > 0.0:
      epsilon = SHEAR * math.pi * a * b * pull / (4.0 * load
                                                   * self.friction)
      if epsilon > EPS_MOST:
        u1, u2 = u1 * EPS_MOST / epsilon, u2 * EPS_MOST / epsilon
        epsilon = EPS_MOST
      creep = 2.0 * load * self.friction / math.pi * (
        epsilon / (1.0 + epsilon * epsilon) + math.atan(epsilon))
      f1, f2 = -creep * g1 / pull, -creep * g2 / pull
    slips[key] = (u1, u2)
    return (-load * normal[0] + f1 * t1[0] + f2 * t2[0],
            -load * normal[1] + f1 * t1[1] + f2 * t2[1],
            -load * normal[2] + f1 * t1[2] + f2 * t2[2])

  def _moved(self, p: list, q: list, v: list, omega: list, m: tuple,
             force: list, torque: list, h: float, mass: float,
             moments: tuple) -> None:
    """Moves the wheelset ('mass', 'moments' about its own axes) 'h' s on
    in place under 'force' and 'torque' (about its centre, in the
    world): its velocity, then its spin in its own frame (Euler's
    equations, the gyroscopic couple kept), then its place and turn by
    them."""
    v[0] += force[0] / mass * h
    v[1] += force[1] / mass * h
    v[2] += force[2] / mass * h
    ix, iy, iz = moments
    wx = m[0][0] * omega[0] + m[1][0] * omega[1] + m[2][0] * omega[2]
    wy = m[0][1] * omega[0] + m[1][1] * omega[1] + m[2][1] * omega[2]
    wz = m[0][2] * omega[0] + m[1][2] * omega[1] + m[2][2] * omega[2]
    tx = m[0][0] * torque[0] + m[1][0] * torque[1] + m[2][0] * torque[2]
    ty = m[0][1] * torque[0] + m[1][1] * torque[1] + m[2][1] * torque[2]
    tz = m[0][2] * torque[0] + m[1][2] * torque[1] + m[2][2] * torque[2]
    wx += (tx - (iz - iy) * wy * wz) / ix * h
    wy += (ty - (ix - iz) * wz * wx) / iy * h
    wz += (tz - (iy - ix) * wx * wy) / iz * h
    omega[0] = m[0][0] * wx + m[0][1] * wy + m[0][2] * wz
    omega[1] = m[1][0] * wx + m[1][1] * wy + m[1][2] * wz
    omega[2] = m[2][0] * wx + m[2][1] * wy + m[2][2] * wz
    p[0] += v[0] * h
    p[1] += v[1] * h
    p[2] += v[2] * h
    half = 0.5 * h
    dw, dx, dy, dz = (-half * (q[1] * wx + q[2] * wy + q[3] * wz),
                      half * (q[0] * wx + q[2] * wz - q[3] * wy),
                      half * (q[0] * wy + q[3] * wx - q[1] * wz),
                      half * (q[0] * wz + q[1] * wy - q[2] * wx))
    q[0] += dw
    q[1] += dx
    q[2] += dy
    q[3] += dz
    size = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
    q[0], q[1] = q[0] / size, q[1] / size
    q[2], q[3] = q[2] / size, q[3] / size


class _Derailment(Exception):
  """A wheelset left the rails within a step ('RailWorld._rolled'
  catches it: the wheelset is 'derailed')."""


def wheelsetOn(track: object, s: float, speed: float,
               radius: float = RADIUS) -> State:
  """The 'wheelsetOn' function returns a wheelset of wheels 'radius' m
  standing on 'track' at 's' m along (its axle across the track, its own
  z to the left, its x ahead; its wheels on the rails' tops at their
  nominal circles), rolling ahead at 'speed' m/s without slipping."""
  place, frame = track.frameAt(s)
  x, y, z = frame[:, 0], frame[:, 1], frame[:, 2]
  centre = place + radius * z
  turn = quaternionOf(tuple(tuple(float(value) for value in row)
                            for row in ((x[0], -z[0], y[0]),
                                        (x[1], -z[1], y[1]),
                                        (x[2], -z[2], y[2]))))
  return State(tuple(float(c) for c in centre), turn,
               tuple(float(c) * speed for c in x),
               tuple(float(c) * speed / radius for c in y))


def _over(sample: tuple, radius: float) -> tuple:
  """Returns where a wheelset of wheels 'radius' m standing on a track's
  'sample' (track, s, its centre line's place, its up) has its centre."""
  _, _, place, up = sample
  return (place[0] + radius * up[0], place[1] + radius * up[1],
          place[2] + radius * up[2])


def _apart(one: tuple, two: tuple) -> float:
  """Returns how far apart places 'one' and 'two' are, squared, m²."""
  return ((one[0] - two[0]) ** 2 + (one[1] - two[1]) ** 2
          + (one[2] - two[2]) ** 2)


def _boxSeen(body: object, state: State, box: Axlebox) -> tuple:
  """Returns an axlebox as its frame ('body' in 'state') holds it at a
  trade's start: where the box is in the world, how fast it moves, its
  arm from the frame's centre and how fast that arm swings round, the
  frame's own axes, its spin."""
  m = matrixOf(state.turn)
  local = tuple(b - c for b, c in zip(box.box, body.centre))
  arm = tuple(m[i][0] * local[0] + m[i][1] * local[1] + m[i][2] * local[2]
              for i in range(3))
  w = state.spin
  swing = (w[1] * arm[2] - w[2] * arm[1], w[2] * arm[0] - w[0] * arm[2],
           w[0] * arm[1] - w[1] * arm[0])
  at = tuple(state.place[i] + arm[i] for i in range(3))
  moving = tuple(state.velocity[i] + swing[i] for i in range(3))
  axes = tuple((m[0][j], m[1][j], m[2][j]) for j in range(3))
  return at, moving, arm, swing, axes, tuple(w)


def _pushed(body: object, state: State, push: list) -> State:
  """Returns 'state' of 'body' after 'push' (an impulse, N s, and a twist
  about its centre, N m s, in the world): its velocity and spin changed
  at once; woken."""
  mass = body.mass
  velocity = tuple(state.velocity[i] + push[i] / mass for i in range(3))
  inertia = body.inertiaIn(state)
  w = state.spin
  momentum = [inertia[i][0] * w[0] + inertia[i][1] * w[1]
              + inertia[i][2] * w[2] + push[3 + i] for i in range(3)]
  spin = tuple(solved([list(row) for row in inertia], momentum))
  return State(state.place, state.turn, velocity, spin, state.bristles,
               state.holds, 0.0)
