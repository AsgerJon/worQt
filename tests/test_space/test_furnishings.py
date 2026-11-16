"""
TestFurnishings covers the cabin round Asger's corner (user, 2026-11-16:
"Have the rest of it have the contents of a camping cabin. Not a fire
place, but the same ... 'hygge'"; the warp knob "kinda... magic"; the
gravity knob's "lots o glint", the loose things "FAFO rules"): every
piece, still or loose, inside the capsule's wall and over its floor,
clear of his corner (his chair, desk, globe and sideboard), its warm
lights in the room; the loose things resting free of what is solid;
the glint on the warp and gravity knobs alone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import itertools
import math

import numpy

from worQt.gaming.space._cockpit import FLOOR, SEAT_AT, WALL, Cockpit
from worQt.gaming.space._cockpit import capsuleRadius
from worQt.gaming.space._dashboard import pieces
from worQt.gaming.space._furnishings import bulbsRows, candleLight
from worQt.gaming.space._furnishings import flamesRows, furnishings
from worQt.gaming.space._furnishings import lampLight, looseParts
from worQt.gaming.space._furnishings import looseThings, shadeRows
from worQt.gaming.space._cabinsolids import solids

from . import SpaceTest

#  How far from his rig's middle the furnishings keep, m (his corner:
#  the sideboard's far edge is 1.2 m from it).
CLEAR = 1.6


class TestFurnishings(SpaceTest):
  """Tests for the cabin's furnishings."""

  def _meshes(self, ) -> dict:
    """Returns every furnishing's mesh by its name."""
    out = dict(furnishings())
    out.update({'flames': flamesRows(), 'shade': shadeRows(),
                'bulbs': bulbsRows()})
    things = looseThings()
    for k, (thing, look, rows, faces) in enumerate(looseParts()):
      placed = numpy.array(rows)
      placed[:, :3] += numpy.array(things[thing][1])
      out['%s %d' % (look, k)] = (placed, faces)
    return out

  def test_inside(self) -> None:
    """Every corner of every piece is inside the capsule's wall, over its
    floor, out of his corner."""
    for name, (rows, _) in self._meshes().items():
      wall = numpy.vectorize(capsuleRadius)(rows[:, 2]) - WALL
      self.assertTrue((numpy.hypot(rows[:, 0], rows[:, 1]) <= wall).all(),
                      name)
      self.assertTrue((rows[:, 2] >= FLOOR - 1e-9).all(), name)
      away = numpy.hypot(rows[:, 0] - SEAT_AT[0], rows[:, 1] - SEAT_AT[1])
      self.assertTrue((away > CLEAR).all(), name)

  def test_cosy(self) -> None:
    """There is a sofa, a blanket, a rug, books, candles, a lamp and
    fairy lights; the lamp's and the candles' lights are in the room,
    over the floor."""
    meshes = self._meshes()
    for name in ('sofa', 'blanket', 'rug', 'wax', 'flames', 'shade',
                 'bulbs'):
      self.assertIn(name, meshes)
      self.assertGreater(len(meshes[name][0]), 0, name)
    looks = {look for _, look, _, _ in looseParts()}
    for look in ('book red', 'leaf', 'ceramic', 'rust', 'black'):
      self.assertIn(look, looks)
    for light in (lampLight(), candleLight()):
      self.assertGreater(light[2], FLOOR + 0.3)
      self.assertLess(math.hypot(light[0], light[1]), capsuleRadius(
        light[2]) - WALL)

  def test_glint(self) -> None:
    """The warp and gravity knobs alone glint, on themselves and on
    their guards' lids; the cabin's lights are pieces of their own (they
    glow; the flames round as well)."""
    every = pieces(Cockpit().controls)
    glints = [(kind, what.action) for kind, what in every
              if kind.startswith('glint')]
    self.assertEqual(glints, [('glint', 'warp'), ('glint lid', 'warp'),
                              ('glint', 'gravity'),
                              ('glint lid', 'gravity')])
    for kind in ('flames', 'flames round', 'shade', 'bulbs'):
      self.assertIn((kind, 0), every)

  def test_resting(self) -> None:
    """Each loose thing rests free of every solid box (its corners at
    most a hair into one: it would jump at the start) and has a mass."""
    held = solids()
    for name, middle, half, axes, mass in looseThings():
      self.assertGreater(mass, 0.0, name)
      for sx, sy, sz in itertools.product((-1.0, 1.0), repeat=3):
        corner = tuple(m + sx * half[0] * a + sy * half[1] * b
                       + sz * half[2] * c for m, a, b, c in zip(
          middle, *axes))
        for box, (inner, size, turned) in enumerate(held):
          off = tuple(p - q for p, q in zip(corner, inner))
          local = [sum(o * t for o, t in zip(off, way)) for way in turned]
          into = min(h - abs(x) for h, x in zip(size, local))
          self.assertLess(into, 1e-6, (name, box, corner))
