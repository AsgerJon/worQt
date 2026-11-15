"""
The shock absorber (user, 2026-11-14: "shock absorbers should be mass
damper spring systems. The ends should be omni-hinged"; rod ends,
"whichever has more fps": rigid ball joints, 'Tie'; "make it look like
a real spring. very visibly"): a coilover of two bodies, the tube (its
lower spring seat threaded on, its eye at the bottom) and the rod (its
top mount, upper spring seat and eye at the top), the rod sliding in
the tube, guided at its top seal ('Slide': gripped at the eye, where
the tie holds the tube, the two and the slide's tilt each turned the
light tube to mend one error, overshot together and see-sawed step to
step); a coil spring pushing the seats apart ('Spring',
pushing only: a coil sits loose, it pulls nothing); the damper between
the eyes ('Damper', its rebound 2.5 times its bump); a rubber bump stop
where it closes ('Spring', pushing only) and a top-out stop where it
opens fully ('Spring', pulling only); each eye on a rod end ('Tie').
The damper and the stops act eye to eye on what the eyes are mounted
to (the rod ends are rigid: the same line, the same force): acting on
the light tube and rod, each step's damping, no more than stops them,
was what stops 3.5 kg, and the tyre rig's corner rang on at a tenth of
its damping (2026-11-14).
'shockOf' builds one between two bodies' points; 'shockBench' a
quarter car's corner on a rig: a wishbone in rubber bushings, a 100 kg
weight hung at its end, the shock under it from the rig's base holding
it up (1.6 Hz; first built over it, the coil pushed the wishbone down
with the weight: a coilover pushes, the road under a car's wheel
pushing it up into the coil).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._assembly import Assembly, Bush, Contact, Damper, Fixed, Hinge
from ._assembly import Slide, Spring, Tie
from ._body import Body, State
from ._shape import Shape, boxShape
from ._turned import Turned
from ._vectors import Vector, minus, norm, plus, rotated, scaled
from ._vectors import turnAbout


class Shock(NamedTuple):
  """
  Shock is a coilover's make: its coil's rate 'spring' N/m and free
  length 'free' m; its damper's 'bump' (closing) and 'rebound' (opening)
  N s/m; eye to eye, 'longest' m (fully open: its top-out stop) and
  'shortest' m (its bump stop's first touch; the rubber then stiffens
  it by 'stop' N/m); the tube's and the rod's masses, kg (the coil's
  shared between them).
  """

  spring: float = 3e4
  free: float = 0.22
  bump: float = 1760.0
  rebound: float = 4400.0
  longest: float = 0.38
  shortest: float = 0.29
  stop: float = 3e5
  tube: float = 2.0
  rod: float = 1.5


#  Where along the shock (from its eye, m) its parts are: the tube's
#  length up from the bottom eye and its seat; the rod's length down
#  from the top eye and its seat; their radii; the coil's radius (to its
#  wire's middle), its wire's, its turns. The top-out stop is all but
#  rigid, N/m; the bump stop's rubber damps, N s/m (undamped, a 600 kg
#  block bounced on it 4 s on at 0.2 m/s).
TUBE_UP, LOWER_SEAT = 0.25, 0.12
ROD_DOWN, UPPER_SEAT = 0.26, 0.04
TUBE_RADIUS, ROD_RADIUS, SEAT_RADIUS = 0.025, 0.011, 0.058
COIL_RADIUS, WIRE_RADIUS, COIL_TURNS = 0.045, 0.0065, 7
TOP_OUT = 2e6
BUMP_DAMPING = 4000.0


def tubeProfile() -> tuple:
  """The 'tubeProfile' function returns the tube as a turned profile,
  its own z up the shock from its eye: the eye's boss, the tube, its
  seat (a threaded collar under a disc)."""
  from ._tyred import _loop
  seat = LOWER_SEAT
  return _loop([(0.0, 0.0), (0.016, 0.0), (0.016, 0.02),
                (TUBE_RADIUS, 0.02), (TUBE_RADIUS, seat - 0.03),
                (0.03, seat - 0.03), (0.03, seat - 0.008),
                (SEAT_RADIUS, seat - 0.008), (SEAT_RADIUS, seat),
                (TUBE_RADIUS, seat), (TUBE_RADIUS, TUBE_UP),
                (0.0, TUBE_UP)])


def rodProfile() -> tuple:
  """The 'rodProfile' function returns the rod as a turned profile, its
  own z up the shock, from its top eye down: the top mount, the upper
  seat, the rod down into the tube."""
  from ._tyred import _loop
  seat = -UPPER_SEAT
  return _loop([(0.0, 0.0), (0.03, 0.0), (0.03, seat + 0.012),
                (SEAT_RADIUS, seat + 0.012), (SEAT_RADIUS, seat),
                (ROD_RADIUS, seat), (ROD_RADIUS, -ROD_DOWN),
                (0.0, -ROD_DOWN)])


@functools.lru_cache(maxsize=4)
def tubeBody(mass: float) -> Body:
  """The 'tubeBody' function returns the tube, 'mass' kg (steel and its
  oil, the coil's half), as its turned shape spreads it."""
  shape = Turned(tubeProfile(), 24)
  return Body.of(shape, mass / shape.moments()[0])


@functools.lru_cache(maxsize=4)
def rodBody(mass: float) -> Body:
  """The 'rodBody' function returns the rod, 'mass' kg (its top mount,
  the coil's half), as its turned shape spreads it."""
  shape = Turned(rodProfile(), 24)
  return Body.of(shape, mass / shape.moments()[0])


def _upTo(way: Vector) -> tuple:
  """Returns the turn that takes z to the unit 'way'."""
  z = (0.0, 0.0, 1.0)
  axis = (z[1] * way[2] - z[2] * way[1], z[2] * way[0] - z[0] * way[2],
          z[0] * way[1] - z[1] * way[0])
  size = norm(axis)
  if size < 1e-12:
    return (1.0, 0.0, 0.0, 0.0) if way[2] > 0.0 else turnAbout(
      (1.0, 0.0, 0.0), math.pi)
  return turnAbout(scaled(axis, 1.0 / size), math.atan2(
    size, way[2]))


def shockOf(shock: Shock, top: int, topPoint: Vector, bottom: int,
            bottomPoint: Vector, tube: int, at: Vector,
            under: Vector) -> tuple:
  """The 'shockOf' function returns a shock absorber of make 'shock'
  between body 'top''s point 'topPoint' (where its rod's eye is, at
  'at' in the world) and body 'bottom''s 'bottomPoint' (its tube's eye,
  at 'under'), its tube body 'tube', its rod 'tube' + 1: (its two
  bodies, their states, its connections)."""
  rod = tube + 1
  way = minus(at, under)
  turn = _upTo(scaled(way, 1.0 / norm(way)))
  tubeOf, rodOf = tubeBody(shock.tube), rodBody(shock.rod)
  states = (State(plus(under, rotated(turn, tubeOf.centre)), turn),
            State(plus(at, rotated(turn, rodOf.centre)), turn))
  eye = (0.0, 0.0, 0.0)
  up = (0.0, 0.0, 1.0)
  connections = (
    Tie(top, topPoint, rod, eye), Tie(bottom, bottomPoint, tube, eye),
    Slide(tube, (0.0, 0.0, TUBE_UP), up, rod, (0.0, 0.0, TUBE_UP - norm(
      way)), up),
    Spring(tube, (0.0, 0.0, LOWER_SEAT), rod, (0.0, 0.0, -UPPER_SEAT),
           shock.spring, shock.free, 0.0, False, True),
    Damper(bottom, bottomPoint, top, topPoint, shock.bump, shock.rebound),
    Spring(bottom, bottomPoint, top, topPoint, shock.stop, shock.shortest,
           BUMP_DAMPING, False, True),
    Spring(bottom, bottomPoint, top, topPoint, TOP_OUT, shock.longest, 0.0,
           True, False))
  return (tubeOf, rodOf), states, connections


def coilOf(tube: int) -> tuple:
  """The 'coilOf' function returns how the coil of the shock whose tube
  is body 'tube' is drawn: its seats' points (on the tube, on the rod),
  the coil's radius, its wire's, its turns."""
  return (tube, (0.0, 0.0, LOWER_SEAT), tube + 1,
          (0.0, 0.0, -UPPER_SEAT), COIL_RADIUS, WIRE_RADIUS, COIL_TURNS)


def shockRuns() -> dict:
  """The 'shockRuns' function returns how a tube and a rod are drawn
  ('finishedRows'): the tube ('damper') with its seat, the rod
  ('chrome') with its top mount and seat."""
  return {'tube': (('damper', tubeProfile()),),
          'rod': (('chrome', rodProfile()),)}


#  The rig: where it stands, its wishbone's pivots (height, y), its
#  length, where the shock meets it (along it), the shock's eye to eye
#  as built (the wishbone level), the weight's mass and side.
RIG = (0.0, 2.0, 0.0)
PIVOT_HEIGHT, PIVOT_Y, PIVOTS = 0.40, 0.20, 0.3
ARM, SHOCK_AT, BUILT = 0.5, 0.30, 0.36
WEIGHT = 100.0
WEIGHT_SIDE = (WEIGHT / 7850.0) ** (1.0 / 3.0)
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)


def _box(low: Vector, high: Vector) -> Shape:
  """Returns a box from corner 'low' to corner 'high'."""
  middle = tuple(0.5 * (a + b) for a, b in zip(low, high))
  return boxShape(*(b - a for a, b in zip(low, high))).moved(
    middle, (1.0, 0.0, 0.0, 0.0))


def rigPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'rigPieces' function returns the rig by its parts, in its own
  frame (the world's axes, from its foot's middle): ('frame', its base,
  rear post and the cross block behind the pivots), ('bracket', the
  pivots' brackets and the shock's lower mount on the base)."""
  low = PIVOT_HEIGHT - BUILT
  y = PIVOT_Y - SHOCK_AT
  frame = (_box((-0.25, -0.45, 0.0), (0.25, 0.45, 0.03)),
           _box((-0.04, 0.27, 0.03), (0.04, 0.35, PIVOT_HEIGHT + 0.08)),
           _box((-0.24, 0.25, PIVOT_HEIGHT - 0.05),
                (0.24, 0.27, PIVOT_HEIGHT + 0.05)))
  brackets = [_box((-0.05, y - 0.03, 0.03), (-0.034, y + 0.03,
                                             low + 0.02)),
              _box((0.034, y - 0.03, 0.03), (0.05, y + 0.03,
                                             low + 0.02))]
  for side in (-1.0, 1.0):
    x = side * (0.5 * PIVOTS + 0.045)
    brackets.append(_box((x - 0.01, PIVOT_Y - 0.03, PIVOT_HEIGHT - 0.03),
                         (x + 0.01, 0.25, PIVOT_HEIGHT + 0.03)))
  shape = frame[0]
  for piece in frame[1:]:
    shape = shape.joined(piece)
  bracket = brackets[0]
  for piece in brackets[1:]:
    bracket = bracket.joined(piece)
  return ('frame', shape), ('bracket', bracket)


@functools.lru_cache(maxsize=1)
def rigBody() -> Body:
  """The 'rigBody' function returns the rig (part of the world:
  'Fixed')."""
  shape = None
  for _, piece in rigPieces():
    shape = piece if shape is None else shape.joined(piece)
  return Body.of(shape, 7850.0)


@functools.lru_cache(maxsize=1)
def weightBody() -> Body:
  """The 'weightBody' function returns the weight, a steel block of
  'WEIGHT' kg, its middle at its own frame's origin."""
  return Body.of(boxShape(WEIGHT_SIDE, WEIGHT_SIDE, WEIGHT_SIDE), 7850.0)


def shockBench(shock: Shock = None) -> tuple[Assembly, tuple[State, ...]]:
  """The 'shockBench' function returns a quarter car's corner on a rig:
  the walker (body 0) 2 m before it, the rig (1, part of the world),
  the wishbone (2, the hinge bench's, in rubber bushings, its pivots
  along x, pointing at the walker, level as built), the weight (3, on a
  rod end at the wishbone's end), the shock absorber of make 'shock'
  ('Shock()' by default; tube 4, rod 5) from the rig's base up to the
  wishbone 'SHOCK_AT' m out, 'BUILT' m eye to eye. It sinks onto the
  coil as built, the weight's and the wishbone's load on it."""
  from ._hinges import armBody
  from ._scenes import WALKER
  shock = Shock() if shock is None else shock
  arm = armBody(True)
  level = turnAbout((1.0, 0.0, 0.0), -0.5 * math.pi)
  pivots = plus(RIG, (0.0, PIVOT_Y, PIVOT_HEIGHT))
  end = plus(pivots, (0.0, -ARM, 0.0))
  hang = (0.0, 0.0, 0.5 * WEIGHT_SIDE + 0.02)
  at = plus(pivots, (0.0, -SHOCK_AT, 0.0))
  under = minus(at, (0.0, 0.0, BUILT))
  states = [State((0.0, 0.0, WALKER.radius)),
            State(plus(RIG, rigBody().centre)),
            State(plus(pivots, rotated(level, arm.centre)), level),
            State(minus(end, hang))]
  connections = [Fixed(1)]
  for side in (-0.5, 0.5):
    own = (side * PIVOTS, 0.0, 0.0)
    connections.append(Hinge(1, plus((0.0, PIVOT_Y, PIVOT_HEIGHT), own),
                             (1.0, 0.0, 0.0), 2, own, (1.0, 0.0, 0.0),
                             Bush()))
  connections.append(Tie(2, (0.0, 0.0, -ARM), 3, hang))
  bodies, shocked, parts = shockOf(shock, 2, (0.0, 0.0, -SHOCK_AT), 1,
                                   minus(under, RIG), 4, at, under)
  states += list(shocked)
  connections += list(parts)
  connections += [Contact(0, k, *_WALKER_ON_STEEL) for k in (1, 2, 3)]
  return Assembly((WALKER.body(), rigBody(), arm, weightBody())
                  + bodies, tuple(connections)), tuple(states)


def shockCoils(assembly: Assembly) -> tuple:
  """The 'shockCoils' function returns how the shock bench's coil is
  drawn ('coilOf': its tube is body 4)."""
  return (coilOf(4),)


def benchFinishes(assembly: Assembly) -> dict:
  """The 'benchFinishes' function returns how the shock bench's bodies
  are drawn, by index: the rig and the wishbone by their parts, the
  weight whole, the shock's tube and rod by their profiles."""
  from ._hinges import armPieces
  runs = shockRuns()
  return {1: rigPieces(), 2: armPieces(True), 3: 'weight',
          4: runs['tube'], 5: runs['rod']}
