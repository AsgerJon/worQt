"""
How the real car's corners are drawn (user, 2026-11-15: "make it look
proper, not these blocky things"): each part round where it is round
('_tubes': smooth tubes, balls), at the places its physics' convex
pieces stand ('_rig.armPieces', 'knucklePieces', '_strut.uprightPieces'),
as finishes of rows ('_meshes.finishedRows': (key, ('rows', rows)), in
the body's own frame, the car's), the left front or rear corner's
mirrored onto its corner ('sidedRows'). Qt-free, numpy.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools

import numpy

from ._brakes import DISC_AT
from ._rig import HUB_HEIGHT, LOWER_BALL, LOWER_PIVOT_Y, LOWER_SPREAD
from ._rig import SHOCK_FOOT, TIE_OUTER, UPPER_BALL, UPPER_PIVOT_Y
from ._rig import UPPER_SPREAD, WHEEL_Y, _padAt
from ._strut import BOSS, BOSS_IN, BOSS_OUT, LOWER_AT, RADIUS_BACK
from ._strut import SEAT_ROUND, STRUT_FOOT, TUBE_LONG, TUBE_ROUND
from ._strut import strutWay
from ._tubes import ballRows, joinedRows, tubeRows
from ._vectors import plus, scaled

#  The parts' sizes as drawn, m: a wishbone's tube, its ball joint, its
#  bushes (radius, half length along its pivot's axis); the upright's
#  (at its foot and at its top), the spindle's, the steering arm's.
ARM_TUBE, BALL, BUSH, BUSH_HALF = 0.014, 0.024, 0.022, 0.03
UPRIGHT_FOOT, UPRIGHT_TOP, SPINDLE, STEER_ARM = 0.03, 0.024, 0.016, 0.012


def sidedRows(rows: numpy.ndarray, side: float, at: float) -> numpy.ndarray:
  """The 'sidedRows' function returns the left corner's 'rows' at the
  corner 'at' along x on 'side' (mirrored on the right: each triangle's
  corners turned the other way round, so it still faces out)."""
  out = rows.copy()
  out[:, 0] += at
  if side < 0.0:
    out[:, 1] *= -1.0
    out[:, 4] *= -1.0
    triangles = out.reshape(-1, 3, 8)
    out = triangles[:, (0, 2, 1)].reshape(-1, 8)
  return out


def _sidedFinish(finish: tuple, side: float, at: float) -> tuple:
  """Returns a finish of rows (key, ('rows', rows)) at its corner."""
  return tuple((key, ('rows', sidedRows(item[1], side, at)))
               for key, item in finish)


@functools.lru_cache(maxsize=8)
def armFinish(lower: bool, side: float, at: float) -> tuple:
  """The 'armFinish' function returns a wishbone drawn round, at the
  corner 'at' on 'side': ('arm', its two legs from its pivots to its
  ball joint and, the lower, its shock's lug), ('chrome', its ball
  joint), ('rubber', its bushes on its pivots)."""
  if lower:
    ball, y, x0, spread = LOWER_BALL, LOWER_PIVOT_Y, 0.0, LOWER_SPREAD
  else:
    ball, y, x0, spread = UPPER_BALL, UPPER_PIVOT_Y, UPPER_BALL[0], (
      UPPER_SPREAD)
  pivots = [(x0 + way * spread, y, ball[2]) for way in (-1.0, 1.0)]
  legs = [tubeRows(pivot, ball, ARM_TUBE) for pivot in pivots]
  if lower:
    legs.append(tubeRows((SHOCK_FOOT[0], SHOCK_FOOT[1] - 0.10,
                          SHOCK_FOOT[2]), (SHOCK_FOOT[0], SHOCK_FOOT[1]
                                           + 0.02, SHOCK_FOOT[2]),
                         ARM_TUBE))
  bushes = [tubeRows((p[0] - BUSH_HALF, p[1], p[2]),
                     (p[0] + BUSH_HALF, p[1], p[2]), BUSH) for p in pivots]
  return _sidedFinish((('arm', ('rows', joinedRows(*legs))),
                       ('chrome', ('rows', ballRows(ball, BALL))),
                       ('rubber', ('rows', joinedRows(*bushes)))),
                      side, at)


def _caliper(pad: tuple) -> tuple:
  """Returns the caliper over the disc at 'pad', and its bracket to the
  hub, as rows: ('caliper', ...), ('knuckle', ...)."""
  disc = WHEEL_Y + DISC_AT
  body = joinedRows(tubeRows((pad[0], disc - 0.022, pad[2]),
                             (pad[0], disc + 0.022, pad[2]), 0.034))
  bracket = tubeRows((-0.01, disc - 0.035, HUB_HEIGHT + 0.01),
                     (pad[0], disc - 0.035, pad[2]), 0.012)
  return body, bracket


@functools.lru_cache(maxsize=4)
def knuckleFinish(side: float, at: float) -> tuple:
  """The 'knuckleFinish' function returns a front knuckle drawn round,
  at the corner 'at' on 'side': ('knuckle', its cast upright tapering
  from its lower ball joint to its upper, its hub's boss, the spindle,
  the steering arm, the caliper's bracket), ('caliper', on the disc)."""
  caliper, bracket = _caliper(_padAt())
  hub = (0.0, LOWER_BALL[1] - 0.03, HUB_HEIGHT)
  body = joinedRows(
    tubeRows(LOWER_BALL, UPPER_BALL, UPRIGHT_FOOT, (True, True),
             UPRIGHT_TOP),
    tubeRows(hub, (0.0, LOWER_BALL[1] + 0.03, HUB_HEIGHT), 0.045),
    tubeRows(hub, (0.0, WHEEL_Y + 0.09, HUB_HEIGHT), SPINDLE),
    tubeRows((-0.005, TIE_OUTER[1], TIE_OUTER[2]), TIE_OUTER, STEER_ARM),
    bracket)
  return _sidedFinish((('knuckle', ('rows', body)),
                       ('caliper', ('rows', caliper))), side, at)


@functools.lru_cache(maxsize=4)
def uprightFinish(side: float, at: float) -> tuple:
  """The 'uprightFinish' function returns a rear upright drawn round, at
  the corner 'at' on 'side': ('knuckle', its hub's boss, the spindle, its
  leg down to the radius rod's eye, its arm back to the toe link, its
  brace up to the strut's foot, the caliper's bracket), ('damper', the
  strut's tube and its spring's lower seat), ('caliper')."""
  caliper, bracket = _caliper(_padAt())
  hub = (0.0, BOSS_IN, HUB_HEIGHT)
  body = joinedRows(
    tubeRows(hub, (0.0, BOSS_OUT, HUB_HEIGHT), BOSS),
    tubeRows(hub, (0.0, WHEEL_Y + 0.09, HUB_HEIGHT), SPINDLE),
    tubeRows((0.0, BOSS_IN + 0.02, HUB_HEIGHT - BOSS + 0.01), RADIUS_BACK,
             0.017, (True, True), 0.014),
    tubeRows((-0.03, TIE_OUTER[1], HUB_HEIGHT), TIE_OUTER, STEER_ARM),
    tubeRows((0.0, BOSS_IN + 0.01, HUB_HEIGHT + BOSS - 0.01), STRUT_FOOT,
             0.02, (True, True), 0.017),
    ballRows(RADIUS_BACK, 0.02), bracket)
  way = strutWay()
  seat = plus(STRUT_FOOT, scaled(way, LOWER_AT))
  damper = joinedRows(
    tubeRows(STRUT_FOOT, plus(STRUT_FOOT, scaled(way, TUBE_LONG)),
             TUBE_ROUND),
    tubeRows(plus(seat, scaled(way, -0.006)), seat, SEAT_ROUND))
  return _sidedFinish((('knuckle', ('rows', body)),
                       ('damper', ('rows', damper)),
                       ('caliper', ('rows', caliper))), side, at)
