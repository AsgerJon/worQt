"""
A railway wheelset, the loop's first vehicle (user, 2026-11-15: "This
looks so fucking awesome, but i feel like something is missing... like
some kinda vehicle?"; the spec's first benchmark: a lone wheelset
rolling down through a loop): two wheels pressed on an axle, turned
from steel as one solid ('wheelsetBody': its mass and its moments from
its shape, nothing assumed), its axle along its own z.

Each wheel's running surface ('profileAt'), in e, how far out from its
nominal rolling circle (m; outward, away from the track's middle, above
nought): the tread a cone of 'CONE' (1:20), radius 'RADIUS' at the
nominal circle, 'NOMINAL' from the wheelset's middle; inward of it the
flange, its face at 'FLANGE_ANGLE' from the axle, 'FLANGE_HIGH' over
the tread, joined to the tread by a root fillet of 'ROOT' (a smooth
profile: the contact's normal turns, never jumps). The rails meet it at
two points each ('RAIL_TOP' on the head's top, 'GAUGE_CORNER' at the
gauge corner, 14 mm down), each a contact of its own, switched on by
its own penetration (the spec: tread and flange as two contacts, never
one that jumps): the knife-edge rails of the textbooks, so the cone's
closed forms hold.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from .._body import Body
from .._turned import Turned

#  The wheel: its radius at the nominal rolling circle, how far that
#  circle lies from the wheelset's middle, the tread's cone, m and
#  rise per run (approximate, a new coned wheel); the flange: its root
#  this far in from the nominal circle, its face's angle from the axle,
#  its height over the tread, m; the root's fillet, m.
RADIUS, NOMINAL, CONE = 0.46, 0.75, 0.05
ROOT_AT, FLANGE_ANGLE, FLANGE_HIGH = -0.037, math.radians(70.0), 0.028
ROOT = 0.003
#  Where each rail meets the wheel, in the track's frame from its middle
#  line at the rails' top (y across, z up), m: the head's top at the
#  nominal circle, the gauge corner 14 mm down at half the gauge.
RAIL_TOP = (NOMINAL, 0.0)
GAUGE_CORNER = (0.7175, -0.014)
#  Steel, kg/m^3.
STEEL = 7850.0
#  The wheelset's other sizes (its drawn and weighed solid), m: the
#  axle's radius and its journals' (where the axleboxes would ride) and
#  their reach, the hub's radius and its span, the web's faces, the
#  rim's inner radius and its faces, the flange's back face, its tip's
#  chamfer, the outer face of the rim.
AXLE, JOURNAL, JOURNAL_FROM, AXLE_END = 0.08, 0.065, 0.98, 1.1
HUB, HUB_FROM, HUB_TO = 0.12, 0.66, 0.84
WEB_FROM, WEB_TO, RIM = 0.735, 0.765, 0.40
BACK, CHAMFER, FACE = 0.68, 0.007, 0.815


def _fillet() -> tuple:
  """Returns the root fillet joining the flange's face to the tread:
  its centre (e, r), where it leaves the tread (e) and where it meets
  the flange (e), from the two lines' corner at 'ROOT_AT'."""
  tread = -CONE
  flange = -math.tan(FLANGE_ANGLE)
  corner = RADIUS + CONE * (-ROOT_AT)
  turn = math.atan(-flange) - math.atan(-tread)
  away = ROOT * math.tan(0.5 * turn)
  onTread = ROOT_AT + away * math.cos(math.atan(-tread))
  onFlange = ROOT_AT - away * math.cos(math.atan(-flange))
  rTread = RADIUS - CONE * onTread
  normal = (-tread, 1.0)
  size = math.hypot(*normal)
  centre = (onTread + ROOT * normal[0] / size, rTread + ROOT * normal[1]
            / size)
  return centre, onTread, onFlange, corner


_CENTRE, _ON_TREAD, _ON_FLANGE, _CORNER = _fillet()
_ON_FLANGE_R = _CENTRE[1] - math.sqrt(max(
  ROOT * ROOT - (_ON_FLANGE - _CENTRE[0]) ** 2, 0.0))
_TIP = RADIUS + CONE * (-ROOT_AT) + FLANGE_HIGH


def profileAt(e: float) -> tuple[float, float]:
  """The 'profileAt' function returns the wheel's radius at 'e' m out
  from its nominal rolling circle and its slope dr/de: the tread, the
  root's fillet, the flange's face, its tip (flat: past it the wheel
  has nothing to stand on)."""
  if e >= _ON_TREAD:
    return RADIUS - CONE * e, -CONE
  if e >= _ON_FLANGE:
    de = e - _CENTRE[0]
    dr = -math.sqrt(max(ROOT * ROOT - de * de, 0.0))
    return _CENTRE[1] + dr, -de / dr if dr < 0.0 else -1e9
  slope = math.tan(FLANGE_ANGLE)
  r = _ON_FLANGE_R + slope * (_ON_FLANGE - e)
  if r >= _TIP:
    return _TIP, 0.0
  return r, -slope


def _halfProfile() -> list:
  """Returns the right half's outline (w along the axle from the
  middle out, rho from it), as points walked outward, the solid on the
  left: axle, hub, web, rim, flange, tread, rim, web, hub, axle,
  journal."""
  w0 = NOMINAL
  tip = _TIP
  flangeFace = w0 + _ON_FLANGE - (tip - profileAt(_ON_FLANGE)[0]) / (
    math.tan(FLANGE_ANGLE))
  points = [(AXLE, 0.0), (AXLE, HUB_FROM), (HUB, HUB_FROM), (HUB, WEB_FROM),
            (RIM, WEB_FROM), (RIM, BACK), (tip - CHAMFER, BACK),
            (tip, BACK + CHAMFER), (tip, flangeFace)]
  for k in range(9):
    e = _ON_FLANGE + (_ON_TREAD - _ON_FLANGE) * k / 8.0
    points.append((profileAt(e)[0], w0 + e))
  points += [(profileAt(FACE - w0)[0], FACE), (RIM, FACE), (RIM, WEB_TO),
             (HUB, WEB_TO), (HUB, HUB_TO), (AXLE, HUB_TO),
             (AXLE, JOURNAL_FROM), (JOURNAL, JOURNAL_FROM),
             (JOURNAL, AXLE_END), (0.0, AXLE_END)]
  return points


@functools.lru_cache(maxsize=1)
def wheelsetBody() -> Body:
  """The 'wheelsetBody' function returns the wheelset, turned from steel
  (its profile mirrored about its middle, both wheels, the axle and its
  journals), its axle along its own z, made once (the rail world knows
  a wheelset by this very body)."""
  half = _halfProfile()
  left = [(rho, -w) for rho, w in reversed(half)]
  points = [(0.0, -AXLE_END)] + left[:-1] + half[1:]
  points = [point for k, point in enumerate(points)
            if k == 0 or point != points[k - 1]]
  pieces = tuple(('line', points[k], points[(k + 1) % len(points)])
                 for k in range(len(points)))
  return Body.of(Turned(pieces, 96), STEEL)
