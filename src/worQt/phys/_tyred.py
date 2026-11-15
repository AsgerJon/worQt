"""
A car's wheel on a tyre as its air makes it (user, 2026-11-13: "model
the wheel as a unidirectional spring working parallel to the plane of
the wheel with whatever the fuck stiffness the current air pressure
demands"): the alloy rim of '_carcass' and the rubber of its 205/55 R16
tyre as one rigid body, and the tyre on the ground a spring ('Tyre'):
pushing only, in the wheel's plane, from the hub down to the ground,
2 pi p sqrt(R a) N/m (the patch a toroidal tyre flattens to grows as 2
pi d sqrt(R a) with how far it is pressed in, d; its air pushes on all
of it: 263 kN/m at 2.3 bar). Its outline (the tyre's outside, the rim's
flanges and barrel; the spokes and hub are drawn, inside the barrel no
walker reaches) is what other things touch; balls ('probes') round its
tyre meet other wheels; lying nearly flat, its sidewalls' meet the
ground.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._assembly import Assembly, Contact, Tyre
from ._body import Body, State
from ._carcass import _CARCASS, BELT_FROM, RIM, RIM_FLANGE, RIM_LIP
from ._carcass import RIM_SEAT, RIM_SHELL, RIM_WIDTH, TYRE_MASS
from ._carcass import TYRE_PRESSURE, TYRE_YARD, WHEEL_START
from ._carcass import WHEEL_UPRIGHT, rimRuns, rubberAt
from ._turned import Turned
from ._vectors import Vector, plus, rotated

#  The tyre's section across (205 mm) and its damping, N s/m (a tenth of
#  critical for the wheel alone on it); its probes' radius, m, and how
#  many round; its sidewalls' probes' radius (on the ground, lying over:
#  small, so the tread's squash never reaches them, 1 cm in from the
#  sidewall's widest: 5 cm upright, its spring squashed that far, which
#  a 0.5 m drop's 2.5 cm does not); the walker on the tyre and tyre on
#  tyre.
TYRE_WIDTH, TYRE_DAMPING = 0.205, 400.0
PROBE, PROBES_ROUND = 0.05, 36
SIDE_PROBE = 0.01
#  Half the tread's width its spring stands on (two springs, one at
#  either edge: within the crown, its radius there within 0.6 mm of the
#  middle's): upright, it rights itself (k a² = 650 N m/rad against its
#  weight's 50), tipped past its tread's edge it falls.
TREAD = 0.05
#  What a tyre loses on the ground: rolling resistance's coefficient (a
#  car tyre's 0.010-0.015), and the arm its patch holds against pivoting
#  with (its grip times about two thirds of a 4 cm patch's radius).
ROLLING, SCRUB = 0.015, 0.03
_WALKER_ON_RUBBER = (1e5, 1.0, 0.9, 1e5, 300.0)
_RUBBER_ON_RUBBER = (1e5, 1.0, 0.9, 1e5, 300.0)
#  How many sides round the wheel's outline is drawn and touched with.
WHEEL_SIDES = 72
#  How many times round a sidewall its maker's lettering runs (the brand
#  twice, as on a racing tyre).
SIDEWALL_REPEATS = 2


def _outer() -> list[tuple[float, float]]:
  """Returns the tyre's outside across, inboard to outboard (rho, w):
  the carcass's line moved out by the rubber over it, square to it,
  where it shows over the rim's flanges."""
  line = list(_CARCASS) + [(r, -w) for r, w in reversed(_CARCASS[:-1])]
  out = []
  for k, (r, w) in enumerate(line):
    before = line[max(k - 1, 0)]
    after = line[min(k + 1, len(line) - 1)]
    dr, dw = after[0] - before[0], after[1] - before[1]
    size = math.hypot(dr, dw)
    thick = rubberAt(r)
    out.append((r + thick * dw / size, w - thick * dr / size))
  top = RIM_SEAT + RIM_FLANGE
  return [point for point in out if point[0] > top + 1e-4]


def _loop(points: list) -> tuple:
  """Returns a closed loop through 'points' as a profile of lines, the
  solid on its left (reversed if it was not)."""
  area = sum(a[0] * b[1] - b[0] * a[1]
             for a, b in zip(points, points[1:] + points[:1]))
  if area < 0.0:
    points = points[::-1]
  return tuple(('line', a, b)
               for a, b in zip(points, points[1:] + points[:1]))


@functools.lru_cache(maxsize=1)
def wheelOutline() -> tuple:
  """The 'wheelOutline' function returns the wheel's outline as a
  turned profile: the tyre's outside from flange to flange, the
  flanges' tops and faces, the barrel's bore."""
  half = 0.5 * RIM_WIDTH + RIM_LIP
  inner, top = RIM_SEAT - RIM_SHELL, RIM_SEAT + RIM_FLANGE
  points = [(inner, -half), (top, -half)] + _outer() + [(top, half),
                                                        (inner, half)]
  return _loop(points)


@functools.lru_cache(maxsize=1)
def tyredBody() -> Body:
  """The 'tyredBody' function returns the wheel as one rigid body: the
  rim ('RIM') and the tyre's rubber (between its carcass's line and its
  outside, 'TYRE_MASS' of it), their masses and moments summed, its
  shape the outline ('wheelOutline')."""
  outer = _outer()
  inside = [point for point in list(_CARCASS) + [
    (r, -w) for r, w in reversed(_CARCASS[:-1])]]
  rubber = Turned(_loop(outer + inside[::-1]), WHEEL_SIDES)
  volume = rubber.volume()
  tyre = Body.of(rubber, TYRE_MASS / volume)
  mass = RIM.mass + tyre.mass
  centre = tuple((RIM.mass * a + tyre.mass * b) / mass
                 for a, b in zip(RIM.centre, tyre.centre))
  inertia = [[0.0] * 3 for _ in range(3)]
  for part in (RIM, tyre):
    d = tuple(a - b for a, b in zip(part.centre, centre))
    dd = sum(x * x for x in d)
    for i in range(3):
      for j in range(3):
        inertia[i][j] += part.inertia[i][j] + part.mass * (
          (dd if i == j else 0.0) - d[i] * d[j])
  return Body(mass, centre, tuple(tuple(row) for row in inertia),
              Turned(wheelOutline(), WHEEL_SIDES))


def _probesOf(across: list, deep: float) -> tuple:
  """Returns probes' middles round the tyre at each of 'across' (points
  of its outside, rho and w, with their inward ways), 'deep' in from
  its outside, 'PROBES_ROUND' round."""
  out = []
  for k in range(PROBES_ROUND):
    a = 2.0 * math.pi * (k + 0.5) / PROBES_ROUND
    c, s = math.cos(a), math.sin(a)
    for (r, w), (ir, iw) in across:
      rho, ww = r + deep * ir, w + deep * iw
      out.append((rho * c, rho * s, ww))
  return tuple(out)


@functools.lru_cache(maxsize=1)
def wheelProbes() -> tuple[tuple, tuple]:
  """The 'wheelProbes' function returns the tyre's probes (in the
  wheel's own frame): every other point of its outside, round; and its
  sidewalls' (the widest either side), round."""
  outer = _outer()
  ways = []
  for k, point in enumerate(outer):
    before = outer[max(k - 1, 0)]
    after = outer[min(k + 1, len(outer) - 1)]
    dr, dw = after[0] - before[0], after[1] - before[1]
    size = math.hypot(dr, dw)
    ways.append((point, (-dw / size, dr / size)))
  if sum(way[0] for _, way in ways) > 0.0:
    ways = [(point, (-way[0], -way[1])) for point, way in ways]
  widest = [ways[0], ways[0]]
  for item in ways:
    if item[0][1] > widest[0][0][1]:
      widest[0] = item
    if item[0][1] < widest[1][0][1]:
      widest[1] = item
  return _probesOf(ways[::2], PROBE), _probesOf(widest, SIDE_PROBE)


def tyreOf(body: int, pressure: float) -> Tyre:
  """The 'tyreOf' function returns the tyre of the wheel at 'body', its
  air 'pressure' Pa over the outside's ('Tyre')."""
  probes, sides = wheelProbes()
  radius = max(r for r, _ in _outer())
  return Tyre(body, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), radius, TYRE_WIDTH,
              pressure, TYRE_DAMPING, PROBE, probes, sides, SIDE_PROBE,
              TREAD, ROLLING, SCRUB)


def wheelYard() -> tuple[Assembly, tuple[State, ...]]:
  """The 'wheelYard' function returns the walker (body 0) in the yard
  and a wheel on its tyre ('tyredBody', 'tyreOf') standing upright on
  its tread 'WHEEL_START' from them, its axle along y, its spokes toward
  -y."""
  from ._scenes import WALKER
  radius = tyreOf(1, TYRE_PRESSURE).radius
  states = (State((0.0, 0.0, WALKER.radius)),
            _placed((WHEEL_START[0], WHEEL_START[1], radius + 0.002),
                    WHEEL_UPRIGHT, (0.0, 0.0, 0.0)))
  return _yardOf((WALKER.body(), tyredBody()), states)


def tyredGiven(assembly: Assembly, states: tuple, state: State) -> tuple[
    Assembly, tuple[State, ...]]:
  """The 'tyredGiven' function returns 'assembly' in 'states' with one
  more wheel, upright, its middle at 'state''s place, moving as it
  does, last."""
  wheel = _placed(state.place, WHEEL_UPRIGHT, state.velocity)
  return _yardOf(assembly.bodies + (tyredBody(),),
                 tuple(states) + (wheel,))


def _placed(place: Vector, turn: tuple, velocity: Vector) -> State:
  """Returns a wheel with its own frame's origin at 'place', turned by
  'turn', moving at 'velocity'."""
  return State(plus(place, rotated(turn, tyredBody().centre)), turn,
               velocity)


def _yardOf(bodies: tuple, states: tuple) -> tuple[Assembly,
                                                    tuple[State, ...]]:
  """Returns the yard's assembly: the walker first, then wheels, each on
  its tyre, the walker touching every wheel, every wheel every other."""
  wheels = range(1, len(bodies))
  connections = [tyreOf(k, TYRE_PRESSURE) for k in wheels]
  connections += [Contact(0, k, *_WALKER_ON_RUBBER) for k in wheels]
  connections += [Contact(a, b, *_RUBBER_ON_RUBBER) for a in wheels
                  for b in wheels if a < b]
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def tyreRuns() -> tuple:
  """The 'tyreRuns' function returns the tyre as drawn: its outside
  over the rims' flanges (the outline's pieces between points of it, as
  the outline walks them), the tread ('tread', where the belts are) and
  the sidewalls apart, each lettered by its maker (user, 2026-11-14:
  "some soul in those tires ... brand: Soufflé"): ('sidewall', a label
  on it, 'SIDEWALL_REPEATS' times round: 'finishedRows')."""
  outside = set(_outer())
  out, run, kind = [], [], None
  for piece in wheelOutline():
    if piece[1] not in outside or piece[2] not in outside:
      continue
    key = 'tread' if min(piece[1][0], piece[2][0]) >= BELT_FROM else (
      'sidewall')
    if key != kind and run:
      out.append((kind, tuple(run)))
      run = []
    kind = key
    run.append(piece)
  out.append((kind, tuple(run)))
  return tuple((key, ('label', SIDEWALL_REPEATS, run))
               if key == 'sidewall' else (key, run) for key, run in out)


def tyredFinishes(assembly: Assembly) -> dict:
  """The 'tyredFinishes' function returns how the wheels of 'assembly'
  are drawn, by index: the rim ('rimRuns') and the tyre ('tyreRuns')."""
  runs = rimRuns() + tyreRuns()
  return {tyre.body: runs for tyre in assembly.tyres}
