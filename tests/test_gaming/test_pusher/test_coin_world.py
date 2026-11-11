"""
TestCoinWorld covers 'CoinWorld', coins as rigid sharp edged discs: a
coin lies on the floor at half its thickness; sliding, it stops where
friction says; rolling on its edge it keeps rolling, upright; dropped on
its edge it falls flat; pushed slowly to an edge it tips as its middle
passes it, and falls; a stack built one coin at a time stands, sagging
little; coins dropped on a pile come to rest, none sunk into another
past a mm; a coin out of play is nowhere.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.pusher import Box, Coin, CoinWorld, Edge

from . import PusherTest, STILL, NOUGHT, FLOOR, BIN
from . import worldOf, tiltOf, onEdge, rained, overlapOf, overlapWith

COIN = Coin()
R, H = COIN.radius, COIN.half


class TestCoinWorld(PusherTest):
  """Tests for 'CoinWorld'."""

  def test_resting(self) -> None:
    """A coin laid on the floor lies there, half its thickness up, a
    hair lower as the contact gives."""
    world = worldOf([((0.0, 0.0, H), STILL, NOUGHT, NOUGHT)], FLOOR, ())
    world.played(1.0)
    self.assertAlmostEqual(world.places[0, 2], H, 1)
    self.assertLess(world.speeds[0], 0.01)
    self.assertLess(tiltOf(world.turns[0]), 0.01)

  def test_sliding(self) -> None:
    """Sliding at 500 mm/s a coin stops after v²/(2 mu g), within 2 %,
    still flat."""
    world = worldOf([((0.0, 0.0, H), STILL, (500.0, 0.0, 0.0), NOUGHT)],
                    FLOOR, ())
    world.played(1.0)
    theory = 500.0 ** 2 / (2.0 * 0.25 * 9810.0)
    self.assertAlmostEqual(world.places[0, 0] / theory, 1.0, 1)
    self.assertLess(abs(world.places[0, 0] - theory), 0.02 * theory)
    self.assertLess(world.speeds[0], 0.01)
    self.assertLess(tiltOf(world.turns[0]), 0.01)

  def test_rolling(self) -> None:
    """Rolling on its edge at 400 mm/s a coin keeps its speed and stays
    upright for 2 s: rolling costs nothing on a hard floor."""
    world = worldOf([((0.0, 0.0, R), onEdge(0.0), (400.0, 0.0, 0.0),
                      (0.0, 400.0 / R, 0.0))], FLOOR, ())
    world.played(2.0)
    self.assertAlmostEqual(world.speeds[0], 400.0, -1)
    self.assertGreater(tiltOf(world.turns[0]), 85.0)
    self.assertGreater(world.places[0, 0], 780.0)

  def test_falling_over(self) -> None:
    """A coin dropped on its edge from 20 mm, leaning a little, falls
    over and lies flat."""
    world = worldOf([((0.0, 0.0, R + 20.0), onEdge(-0.17), NOUGHT,
                      NOUGHT)], FLOOR, ())
    world.played(3.0)
    self.assertLess(tiltOf(world.turns[0]), 0.5)
    self.assertAlmostEqual(world.places[0, 2], H, 1)

  def test_tipping(self) -> None:
    """A coin pushed slowly to the edge of a table tips once its middle
    is past the edge, within 3 mm, and falls off."""
    table = Box((0.0, -500.0, -10.0), (500.0, 500.0, 10.0))
    start = -30.0 - R - 0.5 - 50.0
    pusher = Box((0.0, start, 10.1), (200.0, 50.0, 10.0))
    edge = Edge((-500.0, 0.0, -0.05), (500.0, 0.0, -0.05))
    world = worldOf([((0.0, -30.0, H), STILL, NOUGHT, NOUGHT)],
                    (table, pusher), (edge,))
    tipped = None
    for frame in range(150):
      world.moveBox(1, (0.0, start + 30.0 * frame / 60.0, 10.1),
                    (0.0, 30.0, 0.0))
      world.frame()
      if tipped is None and tiltOf(world.turns[0]) > 5.0:
        tipped = float(world.places[0, 1])
    self.assertIsNotNone(tipped)
    self.assertGreater(tipped, 0.0)
    self.assertLess(tipped, 3.0)
    self.assertLess(world.places[0, 2], -50.0)

  def test_incline(self) -> None:
    """On a box turned 30 degrees a coin lying on it slides down at
    g (sin - mu cos), within 2 %."""
    slope = math.radians(30.0)
    turn = (math.sin(-slope / 2.0), 0.0, 0.0, math.cos(-slope / 2.0))
    ramp = Box((0.0, 0.0, 0.0), (100.0, 400.0, 5.0), turn)
    normal = (0.0, math.sin(slope), math.cos(slope))
    at = tuple((5.0 + H + 0.02) * n for n in normal)
    world = worldOf([(at, turn, NOUGHT, NOUGHT)], (ramp,), ())
    world.played(0.2)
    rate = 9810.0 * (math.sin(slope) - 0.25 * math.cos(slope))
    self.assertLess(abs(world.speeds[0] / (rate * 0.2) - 1.0), 0.02)
    self.assertLess(tiltOf(world.turns[0]) - 30.0, 0.5)

  def test_side_by_side(self) -> None:
    """Two coins laid on a floor 3 mm into each other side by side part
    sideways, both staying on the floor."""
    world = worldOf([((0.0, 0.0, H), STILL, NOUGHT, NOUGHT),
                     ((2.0 * R - 3.0, 0.0, H), STILL, NOUGHT, NOUGHT)],
                    FLOOR, ())
    world.played(1.0)
    places = world.places
    self.assertGreater(places[1, 0] - places[0, 0], 2.0 * R - 0.1)
    self.assertLess(abs(places[0, 2] - H), 0.1)
    self.assertLess(abs(places[1, 2] - H), 0.1)

  def test_against_wall(self) -> None:
    """A coin carried back on a shelf against a wall standing 0.6 mm
    over it stays on the shelf, against the wall, the shelf sliding
    under it: never pushed down under the wall."""
    shelf = Box((0.0, 0.0, -10.0), (200.0, 300.0, 10.0))
    wall = Box((0.0, -100.0, 50.6), (200.0, 100.0, 50.0))
    world = worldOf([((0.0, 30.0, H), STILL, (0.0, -50.0, 0.0), NOUGHT)],
                    (shelf, wall), ())
    lowest = H
    for frame in range(150):
      world.moveBox(0, (0.0, -50.0 * frame / 60.0, -10.0),
                    (0.0, -50.0, 0.0))
      world.frame()
      lowest = min(lowest, float(world.places[0, 2]))
    self.assertGreater(lowest, H - 0.2)
    self.assertAlmostEqual(world.places[0, 1], R, 0)

  def test_stack(self) -> None:
    """Twelve coins stacked one by one, each a little off the one under,
    stand: the top within 1 mm of over the bottom, at rest. The contacts
    are soft, as stiff as the substeps allow (stiffer, stacks shake
    apart), so each gives under the coins over it: 2.9 mm all told, a
    coin pressing a contact some 0.025 mm."""
    world = CoinWorld(COIN, 12, FLOOR, ())
    for index in range(12):
      top = world.places[index - 1, 2] + H if index else 0.0
      world.place(index, (0.3 * (index % 2), 0.0, top + H + 0.5), STILL,
                  NOUGHT, NOUGHT)
      world.played(0.3)
    world.played(2.0)
    places = world.places
    rigid = H + 22.0 * H
    self.assertLess(math.hypot(places[-1, 0] - 0.3, places[-1, 1]), 1.0)
    self.assertLess(rigid - places[-1, 2], 3.2)
    self.assertGreater(rigid - places[-1, 2], 0.0)
    self.assertLess(world.speeds.max(), 0.5)

  def test_pile(self) -> None:
    """Forty coins dropped one by one from 6 cm onto a pile in a bin
    come to rest; none ends up sunk into another past 1 mm."""
    world = CoinWorld(COIN, 40, BIN, ())
    rained(world, 0.25, 5)
    world.played(4.0)
    self.assertLess(world.speeds.max(), 2.0)
    self.assertLess(overlapOf(world), 1.0)
    self.assertLess(world.places[:, 2].max(), 40.0)

  def test_landing(self) -> None:
    """Coins dropped one by one from 6 cm onto a pile, turned at random,
    land on it rather than through it: as they land, at most two of
    thirty dip a mm into another (the measure stops at half a coin's
    thickness, a coin right through), and half under 0.6 mm."""
    world = CoinWorld(COIN, 30, BIN, ())
    rng = numpy.random.default_rng(5)
    dips = []
    for index in range(30):
      top = float(world.places[world.playing][:, 2].max()) if index else 0.0
      axis = rng.uniform(-0.6, 0.6, 3)
      angle = float(numpy.linalg.norm(axis))
      turn = tuple(axis / angle * math.sin(angle / 2.0))
      world.place(index, (rng.uniform(-30.0, 30.0), rng.uniform(-30.0, 30.0),
                          top + 60.0), turn + (math.cos(angle / 2.0),),
                  NOUGHT, NOUGHT)
      deepest = 0.0
      for _ in range(15):
        world.frame()
        deepest = max(deepest, overlapWith(world, index))
      dips.append(deepest)
    self.assertLessEqual(sum(dip > 1.0 for dip in dips), 2)
    self.assertLess(float(numpy.median(dips)), 0.6)

  def test_out_of_play(self) -> None:
    """A coin out of play is touched by nothing and touches nothing: a
    coin dropped through where it lies falls to the floor."""
    world = worldOf([((0.0, 0.0, H), STILL, NOUGHT, NOUGHT),
                     ((0.0, 0.0, 30.0), STILL, NOUGHT, NOUGHT)], FLOOR, ())
    world.park(0)
    world.played(1.0)
    self.assertFalse(world.playing[0])
    self.assertAlmostEqual(world.places[1, 2], H, 1)
