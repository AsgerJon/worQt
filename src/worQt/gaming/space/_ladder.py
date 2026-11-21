"""
Ladder is Asger's hold on the handles (user, 2026-11-19: "Just have
ladders. You hold e for a second whilst a circular fills and you enter
ladder motion where you just crawl along the ladder until you hold e to
get out"; then "My intention was for handles to stretch where Asger
might wanna go when in microgravity. When Asger is in ladder mode, no
more physics. Asger just moves through the ladder system"). The handles
are straight runs ('RUNS') his middle moves along, nothing else moving
him (no physics on them: the user's own call, an approved cheat):
- the ladder up the rocket's axis from the cabin's floor through both
  hatches to the top floor's middle ('AXIS');
- in the cabin from its foot to behind his chair, to the galley's
  rations and to the daybed (a handrail overhead along each, out of a
  walking man's way);
- on the top floor from the ladder's top out to each of the four doors,
  over the gap to the drum (overhead too; a shut door stops him short
  of its leaf, 'DOOR_STOP');
- docked, on through each open door into its cage while the cage is at
  the drum, to before its seat (its handrail is the cage's,
  '_elevator.seatRows').
Held ('held': on run 'on', 'along' m from its start), W carries him
along it the way he looks, S the other way (on the ladder looking
across it: up and down), at 'SPEED'; at a joint he goes on along the
run nearest the way he goes ('TURN'), or stops (one climbed up or down
by the ladder's own way stops at its end till the key is let go). He
takes hold only of a handle he aims at within 'REACH' ('aimed'; put on
its run where he aims; user, 2026-11-19: "Make it so you have to aim
at the handles!") and lets go where he is, still. Their meshes
('ladderRows': the ladder's rails and rungs, the handrails on hanging
posts) and solids ('railsOf').
Qt-free, the rocket's own axes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._crewman import MIDDLE, STAND
from ._elevator import CAR_HIGH, HANDLE_IN, HUB_STOP
from ._furnishings import bedBox, rationCrate
from ._levels import CEILING, DOOR_WAYS, DOORS_HIGH, FLOOR, HEAD, LEVELS
from ._levels import ROOF, WALL
from ._shapes import UNTURNED, boxRows, cylinderRows, joined
from ._turns import cross, dot, unit

#  The ladder: its rails' half spacing (along y) and half thickness, its
#  foot (the cabin's floor) and top (over the top floor's floor), its
#  rungs' spacing and radius, m.
RAIL_HALF = 0.22
RAIL_THICK = 0.02
FOOT, TOP = FLOOR, LEVELS[2][0] + 1.1
RUNG_STEP = 0.3
RUNG = 0.015
RUNGS = tuple(FOOT + RUNG_STEP * (k + 1) for k in range(
  int((TOP - FOOT) / RUNG_STEP) - 1))
#  His middle on the ladder: this far before its face (he faces it, +x),
#  m; from standing on the cabin's floor to the top floor's middle (its
#  doors' middle height).
CLIMB = 0.35
FOOT_SPOT = (-CLIMB, 0.0, FLOOR + MIDDLE)
TOP_SPOT = (-CLIMB, 0.0, DOORS_HIGH)
#  The cabin's runs end this far before what they lead to (toward the
#  axis), m: the rations, the daybed; the chair's at where he gets up
#  ('_crewman.STAND').
BEFORE = 0.8
#  The top floor's runs end over the gap to the drum ('DOOR_OUT' from the
#  axis); a shut door stops his middle 'DOOR_STOP' from the axis (his
#  front short of its leaf); the cages' runs end 'HANDLE_IN' in from the
#  cage's floor at the drum, m.
DOOR_OUT = HEAD + 0.25
DOOR_STOP = HEAD - WALL - 0.3
CAGE_IN = HUB_STOP - HANDLE_IN
#  How fast he moves along, m/s; how near the way he looks (cosine) a run
#  must run for W or S to carry him along it; how near the way he goes a
#  run at a joint must run to take him on; a run steeper than this (its
#  cosine with up) is the ladder's, which W climbs and S descends
#  looking across it.
SPEED = 2.0
ALONG = 0.35
TURN = 0.5
STEEP = 0.7
#  He takes hold only of a handle he aims at (user, 2026-11-19: "Make it
#  so you have to aim at the handles!"): the line of his look, out to
#  'REACH' m from his eyes, passing within 'AIM_LADDER' m of the ladder's
#  middle line (its rungs) or 'AIM_RAIL' of a handrail's.
REACH = 1.8
AIM_LADDER = 0.25
AIM_RAIL = 0.12
#  A cage's handrail starts this far along its run (at the cage's roof,
#  '_elevator.seatRows'), m.
CAGE_RAIL_FROM = HUB_STOP - CAR_HIGH + 0.1 - DOOR_OUT
#  The handrails: over the runs by this much (in the cabin, on the top
#  floor), m; from this far along each run (clear of the hatches' way
#  up), the cabin's ending this short of theirs (not over where he
#  stands up out of his chair: pushing off the floor there his head met
#  it), m; their radius and their posts' half thickness, m.
RAIL_UP = (1.3, 0.9)
RAIL_FROM = 1.0
RAIL_SHORT = 0.5
HANDRAIL = 0.02
POST = 0.015


def _before(point: tuple, far: float) -> tuple:
  """Returns where his middle stands 'far' m from 'point' toward the
  rocket's axis, on the cabin's floor."""
  x, y = point[0], point[1]
  across = math.hypot(x, y)
  share = (across - far) / across
  return x * share, y * share, FLOOR + MIDDLE


@functools.lru_cache(maxsize=1)
def _runs() -> tuple:
  """Returns the runs: each its start, its end, its kind ('ladder',
  'cabin', 'door' (stopped by its door shut), 'cage' (there only docked,
  its door open, its cage at the drum)) and its door's number (-1:
  none)."""
  out = [(FOOT_SPOT, TOP_SPOT, 'ladder', -1),
         (FOOT_SPOT, (STAND[0], STAND[1], FLOOR + MIDDLE), 'cabin', -1),
         (FOOT_SPOT, _before(rationCrate()[0], BEFORE), 'cabin', -1),
         (FOOT_SPOT, _before(bedBox()[0], BEFORE), 'cabin', -1)]
  for k, way in enumerate(DOOR_WAYS):
    out.append((TOP_SPOT, (DOOR_OUT * way[0], DOOR_OUT * way[1],
                           DOORS_HIGH), 'door', k))
  for k, way in enumerate(DOOR_WAYS):
    out.append(((DOOR_OUT * way[0], DOOR_OUT * way[1], DOORS_HIGH),
                (CAGE_IN * way[0], CAGE_IN * way[1], DOORS_HIGH), 'cage',
                k))
  return tuple(out)


RUNS = _runs()


def spotOf(on: int, along: float) -> tuple:
  """Returns the point 'along' m from run 'on''s start."""
  a, b = RUNS[on][:2]
  u = unit(tuple(q - p for p, q in zip(a, b)))
  return tuple(p + along * w for p, w in zip(a, u))


def lengthOf(on: int) -> float:
  """Returns run 'on''s length, m."""
  return math.dist(RUNS[on][0], RUNS[on][1])


def usable(on: int, docked: bool, opened: tuple, home: tuple) -> bool:
  """Returns whether run 'on' is there ('opened': each top floor door
  open, 'home': each cage at the drum)."""
  kind, k = RUNS[on][2:]
  return kind != 'cage' or (docked and opened[k] and home[k])


def reachOf(on: int, opened: tuple) -> float:
  """Returns how far along run 'on' he may go: a door's run with its
  door not open, to 'DOOR_STOP' from the axis; else its length, m."""
  a, b, kind, k = RUNS[on]
  long = lengthOf(on)
  if kind != 'door' or opened[k]:
    return long
  way = DOOR_WAYS[k]
  u = unit(tuple(q - p for p, q in zip(a, b)))
  return max(0.0, min(long, (DOOR_STOP - dot(a, way)) / dot(u, way)))


def _railOf(on: int) -> tuple:
  """Returns run 'on''s handrail's ends and its posts' tops (the
  ceiling over it)."""
  a, b, kind, _ = RUNS[on]
  u = unit(tuple(q - p for p, q in zip(a, b)))
  if kind == 'cabin':
    up, ceiling = RAIL_UP[0], CEILING
  else:
    up, ceiling = RAIL_UP[1], ROOF - 0.25
  end = tuple(q - RAIL_SHORT * w for q, w in zip(b, u))
  if kind == 'door':
    far = HEAD - WALL - 0.05 - dot(a, DOOR_WAYS[RUNS[on][3]])
    end = tuple(p + far / dot(u, DOOR_WAYS[RUNS[on][3]]) * w
                for p, w in zip(a, u))
  start = tuple(p + RAIL_FROM * w for p, w in zip(a, u))
  return ((start[0], start[1], start[2] + up), (end[0], end[1], end[2]
                                                 + up), ceiling)


def handleOf(on: int, aside: tuple) -> tuple:
  """Returns run 'on''s handle: its line's ends (the ladder's middle line
  between its rails, a handrail; a cage's 'aside' from its run), how far
  along the run its start is, and how near it his look must pass, m."""
  a, b, kind, _ = RUNS[on]
  if kind == 'ladder':
    return ((0.0, 0.0, FOOT), (0.0, 0.0, TOP), FOOT - a[2], AIM_LADDER)
  if kind == 'cage':
    start, end = spotOf(on, CAGE_RAIL_FROM), b
    return (tuple(p + s for p, s in zip(start, aside)),
            tuple(q + s for q, s in zip(end, aside)), CAGE_RAIL_FROM,
            AIM_RAIL)
  start, end, _ = _railOf(on)
  return start, end, RAIL_FROM, AIM_RAIL


def _closest(eye: tuple, ray: tuple, start: tuple,
             end: tuple) -> tuple:
  """Returns how far along 'ray' (from 'eye', a share of it) and along
  the line from 'start' to 'end' (a share) the two come nearest, and how
  near, m."""
  d1 = ray
  d2 = tuple(e - s for s, e in zip(start, end))
  r = tuple(e - s for e, s in zip(eye, start))
  a, e, f = dot(d1, d1), dot(d2, d2), dot(d2, r)
  b, c = dot(d1, d2), dot(d1, r)
  under = a * e - b * b
  share = 0.0
  if under > 1e-12:
    share = min(1.0, max(0.0, (b * f - c * e) / under))
  t = (b * share + f) / e
  if t < 0.0:
    t, share = 0.0, min(1.0, max(0.0, -c / a))
  elif t > 1.0:
    t, share = 1.0, min(1.0, max(0.0, (b - c) / a))
  near = tuple(p + share * w for p, w in zip(eye, d1))
  there = tuple(p + t * w for p, w in zip(start, d2))
  return share, t, math.dist(near, there)


def _axesAlong(way: tuple) -> tuple:
  """Returns axes along 'way' (a turn: along it, across it, up)."""
  side = unit(cross((0.0, 0.0, 1.0), way))
  return tuple(way), side, cross(way, side)


@functools.lru_cache(maxsize=1)
def railsOf() -> tuple:
  """Returns the ladder's rails and the handrails as solids: each its
  middle, half sizes and axes (the rocket's own)."""
  half = 0.5 * (TOP - FOOT)
  out = [((0.0, side * RAIL_HALF, FOOT + half), (
    RAIL_THICK, RAIL_THICK, half), UNTURNED) for side in (1.0, -1.0)]
  for on, (_, _, kind, _) in enumerate(RUNS):
    if kind not in ('cabin', 'door'):
      continue
    start, end, ceiling = _railOf(on)
    way = unit(tuple(e - s for s, e in zip(start, end)))
    middle = tuple(0.5 * (s + e) for s, e in zip(start, end))
    out.append((middle, (0.5 * math.dist(start, end), HANDRAIL,
                         HANDRAIL), _axesAlong(way)))
    for end_ in (start, end):
      hang = 0.5 * (ceiling - end_[2])
      out.append(((end_[0], end_[1], end_[2] + hang), (POST, POST, hang),
                  UNTURNED))
  return tuple(out)


def ladderRows() -> tuple:
  """Returns the handles' mesh (the rocket's own axes): the ladder's two
  rails and its rungs across them, each handrail and its two hanging
  posts: rows (place, normal, picture) and triangles."""
  rails = railsOf()
  parts = [boxRows(middle, half, axes) for middle, half, axes in rails[:2]]
  for z in RUNGS:
    parts.append(cylinderRows((0.0, -RAIL_HALF, z), (0.0, 1.0, 0.0), RUNG,
                              2.0 * RAIL_HALF, 8))
  for on, (_, _, kind, _) in enumerate(RUNS):
    if kind not in ('cabin', 'door'):
      continue
    start, end, ceiling = _railOf(on)
    way = tuple(e - s for s, e in zip(start, end))
    parts.append(cylinderRows(start, way, HANDRAIL, math.dist(start, end),
                              8))
    for end_ in (start, end):
      hang = 0.5 * (ceiling - end_[2])
      parts.append(boxRows((end_[0], end_[1], end_[2] + hang), (
        POST, POST, hang), UNTURNED))
  return joined(parts)


class Ladder:
  """
  Ladder holds whether Asger is on the handles ('held'), the run he is
  on ('on') and how far along it ('along', m). 'aimed' finds the handle
  he aims at (he can take hold of it), 'taken' and 'leftOff' put him on
  and take him off, 'moved' carries him along as the keys ask, 'spot'
  is where his middle is.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('held', 'on', 'along')

  #  Public Variables
  held: bool
  on: int
  along: float

  #  Private Variables
  __stopped: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.held, self.on, self.along = False, 0, 0.0
    self.__stopped = False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def spot(self, ) -> tuple:
    """The 'spot' property is where his middle is on the handles."""
    return spotOf(self.on, self.along)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def aimed(self, eye: tuple, look: tuple, docked: bool, opened: tuple,
            home: tuple, aside: tuple) -> tuple | None:
    """The 'aimed' method returns the run and how far along it ('on',
    'along') of the handle he aims at (his look from 'eye' along 'look'
    passing near its line within 'REACH', the nearest such; 'docked',
    'opened', 'home' as 'usable'; 'aside' a cage's handrail's offset from
    its run, the docked rocket's own axes); None: none."""
    best, nearest = None, math.inf
    ray = tuple(REACH * w for w in look)
    for on in range(len(RUNS)):
      if not usable(on, docked, opened, home):
        continue
      start, end, from_, slack = handleOf(on, aside)
      share, t, gap = _closest(eye, ray, start, end)
      if gap > slack or share >= nearest:
        continue
      along = from_ + t * math.dist(start, end)
      best = (on, max(0.0, min(reachOf(on, opened), along)))
      nearest = share
    return best

  def taken(self, on: int, along: float) -> None:
    """The 'taken' method puts him on the handles at 'along' m along run
    'on'."""
    self.held, self.on, self.along = True, int(on), float(along)
    self.__stopped = False

  def leftOff(self, ) -> None:
    """The 'leftOff' method takes him off the handles (where he is)."""
    self.held = False

  def moved(self, seconds: float, ask: int, look: tuple, docked: bool,
            opened: tuple, home: tuple) -> tuple:
    """The 'moved' method carries him 'seconds' s on along the handles:
    'ask' one (W) the way he looks ('look'), minus one (S) the other way,
    nought: still ('docked', 'opened', 'home' as 'usable'); returns how
    fast it carried him (m/s, the rocket's own axes)."""
    if not self.held or seconds <= 0.0:
      return 0.0, 0.0, 0.0
    if ask == 0:
      self.__stopped = False
      return 0.0, 0.0, 0.0
    began = self.spot
    want = tuple(ask * w for w in look)
    left = SPEED * seconds
    for _ in range(len(RUNS)):
      if left <= 1e-9:
        break
      if not self.__stopped:
        self._joined(want, docked, opened, home)
      a, b = RUNS[self.on][:2]
      u = unit(tuple(q - p for p, q in zip(a, b)))
      s, climbed = dot(want, u), False
      if abs(s) < ALONG:
        if abs(u[2]) < STEEP:
          break
        s, climbed = ask * u[2], True
      sign = 1.0 if s > 0.0 else -1.0
      end = reachOf(self.on, opened) if sign > 0.0 else 0.0
      room = (end - self.along) * sign
      if room <= 1e-9:
        break
      step = min(room, left)
      self.along += sign * step
      left -= step
      if step < room:
        break
      if climbed:
        self.__stopped = True
        break
    now = self.spot
    return tuple((n - b) / seconds for b, n in zip(began, now))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _joined(self, want: tuple, docked: bool, opened: tuple,
              home: tuple) -> None:
    """At a joint (an end of his run), puts him on the run there that
    runs nearest 'want' from it (his own too), if within 'TURN' of it."""
    long = lengthOf(self.on)
    if 1e-9 < self.along < long - 1e-9:
      return
    node = RUNS[self.on][0] if self.along <= 1e-9 else RUNS[self.on][1]
    best, most = None, TURN
    for on in range(len(RUNS)):
      if not usable(on, docked, opened, home):
        continue
      a, b = RUNS[on][:2]
      for end, other, along in ((a, b, 0.0), (b, a, lengthOf(on))):
        if math.dist(end, node) > 1e-6:
          continue
        if along == 0.0 and reachOf(on, opened) <= 1e-9:
          continue
        out = unit(tuple(o - e for e, o in zip(end, other)))
        score = dot(want, out)
        if score > most:
          best, most = (on, along), score
    if best is not None:
      self.on, self.along = best
