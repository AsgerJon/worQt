"""
The brake bench (user, 2026-11-14: "disc brakes (actual friction
applies to discs connected to wheels)", "Disc brakes first, send it!"):
the Soufflé wheel ('_tyred') with a cast iron disc bolted to its hub
face, one body ('brakedWheel'), turning on a bearing (two ties on its
axle) on a stand's stub axle, the stand's caliper squeezing the disc
('DiscBrake') as hard as its line's pressure says ('BrakeLine'). The
disc: 280 mm across, 12 mm thick, solid, its pads sweeping it from 85
mm out to its rim; its hat 40 mm deep to the wheel's mounting face (the
wheel's offset, 45 mm out of the rim's middle), inboard of the spokes.
The caliper sits behind the axle, its pads' middle 112.5 mm out, a
floating caliper (one 54 mm piston). Spun by hand (the grabber), the
wheel is slowed by the pads' friction and held once stopped.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools

from ._assembly import Assembly, BrakeLine, Contact, DiscBrake, Fixed, Tie
from ._body import Body, State
from ._carcass import RIM_OFFSET, TYRE_PRESSURE, WHEEL_UPRIGHT
from ._shape import Shape, boxShape, cylinderShape
from ._turned import Turned
from ._tyred import _WALKER_ON_RUBBER, _loop, tyreOf, tyredBody
from ._tyred import wheelOutline
from ._vectors import Vector, plus, rotated

#  The disc, m: its swept ring (from, to: the pads reach it there), its
#  thickness, its middle plane along the wheel's axle (in the wheel's
#  own frame: the hat's depth inboard of the mounting face), the hat's
#  wall (from, to) and the hat's top's bore and thickness; cast iron,
#  kg/m³.
DISC_INNER, DISC_OUTER, DISC_THICK = 0.085, 0.140, 0.012
DISC_AT = RIM_OFFSET - 0.040
HAT_IN, HAT_OUT, HAT_BORE, HAT_TOP = 0.070, 0.076, 0.030, 0.006
CAST_IRON = 7200.0
#  The pads' middle, m from the axle (the swept ring's middle), and the
#  bench: where the wheel's middle stands (x, y, the axle's height).
PAD_RADIUS = 0.5 * (DISC_INNER + DISC_OUTER)
BENCH = (0.0, 2.0, 0.36)
#  The walker on the stand's steel.
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)


def discProfile() -> tuple:
  """The 'discProfile' function returns the disc and its hat as a
  turned profile in the wheel's own frame (rho, w): the ring the pads
  sweep (in to the hat's wall), the hat's wall up to the mounting face,
  its top over the hub to its bore."""
  low, high = DISC_AT - 0.5 * DISC_THICK, DISC_AT + 0.5 * DISC_THICK
  points = [(HAT_IN, low), (DISC_OUTER, low), (DISC_OUTER, high),
            (HAT_OUT, high), (HAT_OUT, RIM_OFFSET),
            (HAT_BORE, RIM_OFFSET), (HAT_BORE, RIM_OFFSET - HAT_TOP),
            (HAT_IN, RIM_OFFSET - HAT_TOP)]
  return _loop(points)


@functools.lru_cache(maxsize=1)
def discBody() -> Body:
  """The 'discBody' function returns the disc alone (cast iron, 5.2
  kg), in the wheel's own frame."""
  return Body.of(Turned(discProfile(), 72), CAST_IRON)


@functools.lru_cache(maxsize=1)
def brakedWheel() -> Body:
  """The 'brakedWheel' function returns the wheel and its disc as one
  body ('tyredBody' and 'discBody': masses and moments summed), its
  shape the wheel's outline (the disc lies within the rim's barrel,
  where nothing reaches it)."""
  parts = (tyredBody(), discBody())
  mass = sum(part.mass for part in parts)
  centre = tuple(sum(part.mass * part.centre[i] for part in parts) / mass
                 for i in range(3))
  inertia = [[0.0] * 3 for _ in range(3)]
  for part in parts:
    d = tuple(a - b for a, b in zip(part.centre, centre))
    dd = sum(x * x for x in d)
    for i in range(3):
      for j in range(3):
        inertia[i][j] += part.inertia[i][j] + part.mass * (
          (dd if i == j else 0.0) - d[i] * d[j])
  return Body(mass, centre, tuple(tuple(row) for row in inertia),
              tyredBody().shape)


def standPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'standPieces' function returns the stand by its parts, in its
  own frame (the world's axes, from the wheel's middle on its axle):
  ('stand', its foot, post and stub axle, the wheel's bearing on it),
  ('caliper', the caliper either side of the disc, its bridge over the
  disc's rim and its bracket to the axle). The wheel's outboard face
  looks along -y, so the stand stands on its inboard side, +y."""
  height = BENCH[2]

  def box(low: Vector, high: Vector) -> Shape:
    """Returns a box from corner 'low' to corner 'high'."""
    middle = tuple(0.5 * (a + b) for a, b in zip(low, high))
    size = tuple(b - a for a, b in zip(low, high))
    return boxShape(*size).moved(middle, (1.0, 0.0, 0.0, 0.0))

  disc = -DISC_AT
  near, far = disc + 0.5 * DISC_THICK, disc - 0.5 * DISC_THICK
  stand = (box((-0.20, 0.07, -height), (0.20, 0.27, 0.02 - height)),
           box((-0.04, 0.13, 0.02 - height), (0.04, 0.19, 0.05)),
           cylinderShape(0.022, 0.25, 16).moved((0.0, 0.065, 0.0),
                                                (1.0, 0.0, 0.0, 0.0)))
  caliper = (box((-0.150, near + 0.002, -0.035), (-0.080, near + 0.028,
                                                  0.035)),
             box((-0.150, far - 0.016, -0.035), (-0.080, far - 0.002,
                                                 0.035)),
             box((-0.165, far - 0.016, -0.035), (-0.145, near + 0.028,
                                                 0.035)),
             box((-0.100, near + 0.008, -0.018), (0.0, near + 0.022,
                                                  0.018)))
  out = []
  for key, pieces in (('stand', stand), ('caliper', caliper)):
    shape = pieces[0]
    for piece in pieces[1:]:
      shape = shape.joined(piece)
    out.append((key, shape))
  return tuple(out)


@functools.lru_cache(maxsize=1)
def standBody() -> Body:
  """The 'standBody' function returns the stand, steel (part of the
  world on the bench: 'Fixed')."""
  shape = None
  for _, piece in standPieces():
    shape = piece if shape is None else shape.joined(piece)
  return Body.of(shape, 7850.0)


def benchOf(line: BrakeLine) -> tuple[Assembly, tuple[State, ...]]:
  """The 'benchOf' function returns the brake bench with its brake on
  'line': the walker (body 0) 2 m before the wheel's outboard face, the
  stand (1, part of the world), the braked wheel (2) on its bearing
  (ties on its axle 20 and 70 mm out), still, its tyre ('tyreOf') 4 cm
  over the ground, the brake's pads on its disc."""
  from ._scenes import WALKER
  stand, wheel = standBody(), brakedWheel()
  states = (State((0.0, 0.0, WALKER.radius)),
            State(plus(BENCH, stand.centre)),
            State(plus(BENCH, rotated(WHEEL_UPRIGHT, wheel.centre)),
                  WHEEL_UPRIGHT))
  connections = (Fixed(1),
                 Tie(1, (0.0, -0.02, 0.0), 2, (0.0, 0.0, 0.02)),
                 Tie(1, (0.0, -0.07, 0.0), 2, (0.0, 0.0, 0.07)),
                 DiscBrake(2, 1, (0.0, 0.0, DISC_AT), (0.0, 0.0, 1.0),
                           (-PAD_RADIUS, -DISC_AT, 0.0), DISC_INNER,
                           DISC_OUTER, line),
                 tyreOf(2, TYRE_PRESSURE),
                 Contact(0, 1, *_WALKER_ON_STEEL),
                 Contact(0, 2, *_WALKER_ON_RUBBER))
  return Assembly((WALKER.body(), stand, wheel), connections), states


def discRuns() -> tuple:
  """The 'discRuns' function returns the disc as drawn ('finishedRows'):
  its profile in one run ('disc', cast iron's finish)."""
  return (('disc', discProfile()),)


def benchFinishes(assembly: Assembly) -> dict:
  """The 'benchFinishes' function returns how the bench's bodies are
  drawn, by index: the wheel as the tyre yard's ('tyredFinishes') with
  its disc, the stand by its parts ('standPieces')."""
  from ._carcass import rimRuns
  from ._tyred import tyreRuns
  return {2: rimRuns() + tyreRuns() + discRuns(), 1: standPieces()}
