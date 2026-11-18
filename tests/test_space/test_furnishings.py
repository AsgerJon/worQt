"""
TestFurnishings covers the cabin round Asger's corner (user, 2026-11-16:
"Have the rest of it have the contents of a camping cabin. Not a fire
place, but the same ... 'hygge'"; the warp knob "kinda... magic"):
every piece inside the capsule's wall and over its floor, clear of his
corner (his chair, desk, globe and sideboard), its warm lights in the
room; nothing loose (user, 2026-11-18: "remove them completely. Do not
have items that look like they should be floating in microgravity when
they don't"); the glint on the warp knob alone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.space._cockpit import FLOOR, SEAT_AT, WALL, Cockpit
from worQt.gaming.space._cockpit import capsuleRadius
from worQt.gaming.space._dashboard import pieces
from worQt.gaming.space._furnishings import bulbsRows, candleLight
from worQt.gaming.space._furnishings import flamesRows, furnishings
from worQt.gaming.space._furnishings import lampLight, looseParts
from worQt.gaming.space._furnishings import looseThings, shadeRows

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
    self.assertIn('book red', meshes)
    self.assertIn('brass', meshes)
    for light in (lampLight(), candleLight()):
      self.assertGreater(light[2], FLOOR + 0.3)
      self.assertLess(math.hypot(light[0], light[1]), capsuleRadius(
        light[2]) - WALL)

  def test_glint(self) -> None:
    """The warp knob glints, on itself and on its guard's lid, and so
    does WARP TO ACTION (user, 2026-11-17: "the same enchanted glint as
    the general warp dial"), on its cap (no guard); nothing else; the
    cabin's lights are pieces of their own (they glow; the flames round
    as well)."""
    every = pieces(Cockpit().controls)
    glints = [(kind, what.action) for kind, what in every
              if kind.startswith('glint')]
    self.assertEqual(glints, [('glint', 'warp'), ('glint lid', 'warp'),
                              ('glint', 'action')])
    for kind in ('flames', 'flames round', 'shade', 'bulbs'):
      self.assertIn((kind, 0), every)

  def test_none_loose(self) -> None:
    """Nothing in the cabin is loose, and nothing is there that looks as
    if it should float weightless and does not (user, 2026-11-18: "no,
    remove them completely"): no mug, kettle, coffee pot, pillow or
    plant; the books are held in their shelf."""
    self.assertEqual(looseThings(), ())
    self.assertEqual(looseParts(), ())
    meshes = self._meshes()
    for look in ('leaf', 'terracotta', 'ceramic'):
      self.assertNotIn(look, meshes)
    self.assertIn('book red', meshes)
