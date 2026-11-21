"""
The cabin's solids: what is fixed in it, as boxes Asger and the loose
things bump into (user, 2026-11-17: Asger getting up and floating
round, "FAFO rules"), Qt-free, the vessel's own axes: his rig (the
pilot seat, the consoles, the curved panel and its hood as boxes round
the curve, the risers its wings stand on, the globe in the panel, the
sideboard and the tape deck on it), the furnishings fixed down
('_furnishings.obstacles') and the ladder's rails up the rocket's axis
through its three levels ('_ladder'). The floors, the walls and the
ceilings are the cabin kernel's own ('_cabin_kernels').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._cockpit import BACKREST, CUSHION, FACE_HIGH, FACE_LOW, FLOOR
from ._cockpit import GLASS
from ._cabin import PEDESTAL
from ._cockpit import GLOBE_AT, GLOBE_AXES, HOOD_DEEP, HOOD_HIGH
from ._cockpit import HOOD_RADIUS, HOOD_SPAN, LEFT_CONSOLE, PANEL_DEEP
from ._cockpit import PANEL_RADIUS, PANEL_SPAN, RIGHT_CONSOLE, RISER
from ._cockpit import SIDEBOARD, TOP, hoodAxes, hoodPoint, panelAxes
from ._cockpit import panelPoint
from ._deckmodel import stillParts
from ._furnishings import obstacles
from ._ladder import railsOf
from ._shapes import UNTURNED

#  The curved panel and its hood as boxes round the curve, each so many
#  rad round; how far before its face the panel's reach (its knobs, keys
#  and guards stand out), m.
PANEL_PIECE = math.radians(10.0)
STANDS_OUT = 0.04


@functools.lru_cache(maxsize=1)
def solids() -> tuple:
  """Returns the cabin's solid boxes, each its middle, half sizes and
  axes (right, up, out: the vessel's own)."""
  out = [(middle, half, UNTURNED) for middle, half in (
    CUSHION, BACKREST, LEFT_CONSOLE, RIGHT_CONSOLE, SIDEBOARD)]
  (x, y, z), half = CUSHION
  under = z - half[2] - 0.1
  stand = 0.5 * (under - FLOOR)
  out.append(((x, y, FLOOR + stand), (PEDESTAL[0], PEDESTAL[1], stand),
              UNTURNED))
  out.append(((x, y, under + 0.05), (half[0] + 0.02, half[1] + 0.06,
                                     0.05), UNTURNED))
  out += _curved(panelPoint, panelAxes, PANEL_RADIUS, PANEL_SPAN,
                 FACE_LOW, FACE_HIGH, PANEL_DEEP)
  out += _curved(hoodPoint, hoodAxes, HOOD_RADIUS, HOOD_SPAN, 0.0,
                 HOOD_HIGH, HOOD_DEEP)
  (ahead, inward), (hx, hy) = RISER
  for (x, y, _), _ in (LEFT_CONSOLE, RIGHT_CONSOLE):
    high = panelPoint(0.0, FACE_LOW, 0.0)[2] - 0.03
    side = math.copysign(inward, y - CUSHION[0][1])
    out.append(((x + ahead, y - side, 0.5 * (TOP + high)), (
      hx, hy, 0.5 * (high - TOP)), UNTURNED))
  out.append(_deckBox())
  out.append((GLOBE_AT, (GLASS, GLASS, GLASS), GLOBE_AXES))
  out += list(railsOf())
  return tuple(out) + obstacles()


def _curved(pointOf: object, axesOf: object, radius: float, span: float,
            low: float, high: float, deep: float) -> list:
  """Returns a curved sheet's body (the panel's, the hood's: 'pointOf',
  'axesOf' theirs; 'radius' m out along its middle line, 'span' rad
  round either way, from 'low' to 'high' up its slant, 'deep' behind)
  as boxes, a 'PANEL_PIECE' round each, reaching 'STANDS_OUT' before
  its face."""
  count = max(1, int(math.ceil(2.0 * span / PANEL_PIECE)))
  piece = 2.0 * span * radius / count
  out = []
  for k in range(count):
    right = -span * radius + (k + 0.5) * piece
    middle = pointOf(right, 0.5 * (low + high), 0.5 * (STANDS_OUT - deep))
    out.append((middle, (0.5 * piece * (radius + 0.2) / radius,
                         0.5 * (high - low), 0.5 * (STANDS_OUT + deep)),
                axesOf(right)))
  return out


def _deckBox() -> tuple:
  """Returns the tape deck's box: round its still body."""
  rows = numpy.concatenate([part[0][:, :3] for _, part in stillParts()])
  low, high = rows.min(axis=0), rows.max(axis=0)
  middle = tuple(float(x) for x in 0.5 * (low + high))
  half = tuple(float(x) for x in 0.5 * (high - low))
  return middle, half, UNTURNED
