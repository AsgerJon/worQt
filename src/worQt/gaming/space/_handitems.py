"""
What Asger holds in his hand ('_inventory': user, 2026-11-17: "Give
Asger a hotbar and an inventory like in minecraft. then one tool is the
gravgun, then give Asger also a telescope, if possible. Finally, put
some commandobars in Asgers inventory"): each item's meshes in his eyes'
frame (right, up, back: as the gravity gun's, '_gunmodel'), low on his
right: the gravity gun, the telescope (a brass tube narrowing to its
eyepiece, its glass ahead), a commando bar (its olive wrapper, its
yellow band), a bag of pork scratchings. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools

from ._shapes import boxRows, cylinderRows, discRows, frustumRows, joined

#  The looks (colour 0 to 255, metalness, roughness): brass, its dark
#  rings, the glass; the bar's wrapper and band.
BRASS = ((205, 160, 60), 0.6, 0.35)
RINGS = ((70, 52, 24), 0.4, 0.5)
LENS = ((140, 190, 255), 0.0, 0.08)
WRAPPER = ((85, 100, 45), 0.0, 0.7)
BAND = ((232, 200, 60), 0.0, 0.6)
BAG = ((196, 44, 32), 0.1, 0.45)
RINDS = ((228, 196, 136), 0.0, 0.8)
#  The telescope in his hand: its eyepiece's end, the way it points
#  (ahead, a little in and up), how long, its radius at the eyepiece and
#  at its glass, m.
EYEPIECE = (0.26, -0.2, -0.3)
POINTED = (-0.12, 0.16, -0.98)
LONG = 0.3
NARROW, WIDE = 0.016, 0.028
#  The bar in his hand: its middle, half its size, m.
BAR_AT = (0.2, -0.14, -0.4)
BAR_HALF = (0.055, 0.014, 0.022)
#  The bag of pork scratchings in his hand: its middle, half its size, m.
BAG_AT = (0.2, -0.15, -0.42)
BAG_HALF = (0.045, 0.06, 0.016)


@functools.lru_cache(maxsize=4)
def heldParts(kind: str) -> tuple:
  """Returns what 'kind' (an '_inventory.ITEMS' name) looks like in his
  hand: each part its look, its picture ('' none), its rows and
  triangles (the eyes' frame)."""
  if kind == 'telescope':
    return _telescopeParts()
  if kind == 'commando':
    return _barParts()
  if kind == 'scratchings':
    return _bagParts()
  raise KeyError('no %s held' % kind)


def _telescopeParts() -> tuple:
  """Returns the telescope: a brass tube widening from its eyepiece,
  dark rings at its eyepiece and its glass, the glass at its end."""
  size = sum(p * p for p in POINTED) ** 0.5
  way = tuple(p / size for p in POINTED)
  end = tuple(e + LONG * w for e, w in zip(EYEPIECE, way))
  tube = frustumRows(EYEPIECE, way, NARROW, WIDE, LONG, 28)
  rings = joined([cylinderRows(tuple(e - 0.01 * w for e, w in zip(
    EYEPIECE, way)), way, NARROW + 0.004, 0.03, 20),
                  cylinderRows(tuple(e - 0.02 * w for e, w in zip(end, way)),
                               way, WIDE + 0.005, 0.03, 28)])
  glass = discRows(tuple(e + 0.011 * w for e, w in zip(end, way)),
                   _axesOut(way), WIDE - 0.004, 28, None)
  return ((BRASS, '') + tube, (RINGS, '') + rings, (LENS, '') + glass)


def _barParts() -> tuple:
  """Returns a commando bar: its wrapper, a band round its middle."""
  axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
  wrapper = boxRows(BAR_AT, BAR_HALF, axes)
  band = boxRows(BAR_AT, (0.3 * BAR_HALF[0], BAR_HALF[1] + 0.001,
                          BAR_HALF[2] + 0.001), axes)
  return ((WRAPPER, '') + wrapper, (BAND, '') + band)


def _bagParts() -> tuple:
  """Returns a bag of pork scratchings: red, a window of rinds on its
  face toward him."""
  axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
  bag = boxRows(BAG_AT, BAG_HALF, axes)
  window = boxRows(tuple(a + d for a, d in zip(BAG_AT, (
    0.0, 0.006, BAG_HALF[2]))), (0.7 * BAG_HALF[0], 0.45 * BAG_HALF[1],
                                  0.001), axes)
  return ((BAG, '') + bag, (RINDS, '') + window)


def _axesOut(way: tuple) -> tuple:
  """Returns axes facing out along 'way' (right, up, out: unit,
  right-handed)."""
  right = (-way[2], 0.0, way[0])
  size = (right[0] ** 2 + right[2] ** 2) ** 0.5
  right = tuple(r / size for r in right)
  up = (way[1] * right[2] - way[2] * right[1],
        way[2] * right[0] - way[0] * right[2],
        way[0] * right[1] - way[1] * right[0])
  return right, up, way
