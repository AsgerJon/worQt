"""
The cabin's solids: what is fixed in it, as boxes Asger and the loose
things bump into (user, 2026-11-17: Asger getting up and floating
round, "FAFO rules"), Qt-free, the vessel's own axes: his rig (the
office chair, the consoles, the panel, the sideboard and the tape deck
on it, the globe on its stand) and the furnishings fixed down
('_furnishings.obstacles'). The floor, the wall and the ceiling are the
cabin kernel's own ('_cabin_kernels').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools

import numpy

from ._cockpit import BACKREST, CUSHION, FLOOR, FRAME, GLASS, GLOBE_AT
from ._cockpit import LEFT_CONSOLE, PANEL_AXES, PANEL_HALF, PANEL_MIDDLE
from ._cockpit import RIGHT_CONSOLE, SIDEBOARD
from ._deckmodel import stillParts
from ._furnishings import obstacles
from ._shapes import UNTURNED

#  The panel's box: how far before and behind its middle it reaches (its
#  knobs, guards and globe stand out), m; the chair's foot (its five legs
#  as a flat box: half its width and height) and its column (half its
#  width); the globe's stand (its foot's half width and height, its
#  pillar's half width).
PANEL_DEEP = 0.04
CHAIR_FOOT = (0.3, 0.05)
CHAIR_COLUMN = 0.04
GLOBE_FOOT = (0.17, 0.015)
GLOBE_PILLAR = 0.025


@functools.lru_cache(maxsize=1)
def solids() -> tuple:
  """Returns the cabin's solid boxes, each its middle, half sizes and
  axes (right, up, out: the vessel's own)."""
  out = [(middle, half, UNTURNED) for middle, half in (
    CUSHION, BACKREST, LEFT_CONSOLE, RIGHT_CONSOLE, SIDEBOARD)]
  (x, y, z), half = CUSHION
  under = z - half[2]
  out.append(((x, y, FLOOR + CHAIR_FOOT[1]), (CHAIR_FOOT[0],
                                              CHAIR_FOOT[0],
                                              CHAIR_FOOT[1]), UNTURNED))
  column = 0.5 * (under - FLOOR)
  out.append(((x, y, FLOOR + column), (CHAIR_COLUMN, CHAIR_COLUMN,
                                       column), UNTURNED))
  out.append((PANEL_MIDDLE, (PANEL_HALF[0] + FRAME, PANEL_HALF[1] + FRAME,
                             PANEL_DEEP), PANEL_AXES))
  out.append(_deckBox())
  x, y, z = GLOBE_AT
  out.append((GLOBE_AT, (GLASS, GLASS, GLASS), UNTURNED))
  out.append(((x, y, FLOOR + GLOBE_FOOT[1]), (GLOBE_FOOT[0], GLOBE_FOOT[0],
                                              GLOBE_FOOT[1]), UNTURNED))
  low = z - GLASS
  out.append(((x, y, 0.5 * (FLOOR + low)), (GLOBE_PILLAR, GLOBE_PILLAR,
                                            0.5 * (low - FLOOR)),
              UNTURNED))
  return tuple(out) + obstacles()


def _deckBox() -> tuple:
  """Returns the tape deck's box: round its still body."""
  rows = numpy.concatenate([part[0][:, :3] for _, part in stillParts()])
  low, high = rows.min(axis=0), rows.max(axis=0)
  middle = tuple(float(x) for x in 0.5 * (low + high))
  half = tuple(float(x) for x in 0.5 * (high - low))
  return middle, half, UNTURNED
