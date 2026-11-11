"""
PusherTest and PusherWidgetTest are the base classes for the tests of
'worQt.gaming.pusher': 'PusherTest' subclasses 'BaseTest' for the coins
and the machine, which need no Qt; 'PusherWidgetTest' subclasses
'WidgetTest' for the widgets.

Its functions: 'worldOf' puts coins in play on a floor or among given
boxes; 'tiltOf' is how far a coin leans from lying flat; 'onEdge' turns
a coin to stand on its edge; 'rained' drops coins one by one onto a
pile; 'overlapWith' and 'overlapOf' measure, by points through each
coin, how far a coin, or any coin, lies inside another.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
from worktoy.work_test import BaseTest

from worQt.gaming.pusher import Box, Coin, CoinWorld
from worQt.qtest import WidgetTest

STILL = (0.0, 0.0, 0.0, 1.0)
NOUGHT = (0.0, 0.0, 0.0)
FLOOR = (Box((0.0, 0.0, -10.0), (3000.0, 3000.0, 10.0)),)
BIN = FLOOR + (Box((-65.0, 0.0, 0.0), (5.0, 100.0, 100.0)),
               Box((65.0, 0.0, 0.0), (5.0, 100.0, 100.0)),
               Box((0.0, -65.0, 0.0), (100.0, 5.0, 100.0)),
               Box((0.0, 65.0, 0.0), (100.0, 5.0, 100.0)))


def worldOf(coins: list, boxes: tuple, edges: tuple) -> CoinWorld:
  """The 'worldOf' function returns 20-krone coins in play among 'boxes'
  and 'edges', each of 'coins' as (place, turn, velocity, spin)."""
  world = CoinWorld(Coin(), len(coins), boxes, edges)
  for index, (at, turn, velocity, spin) in enumerate(coins):
    world.place(index, at, turn, velocity, spin)
  return world


def tiltOf(turn: numpy.ndarray) -> float:
  """The 'tiltOf' function returns, in degrees, how far a coin turned by
  'turn' (x y z w) leans from lying flat."""
  x, y = float(turn[0]), float(turn[1])
  return math.degrees(math.acos(min(1.0, abs(1.0 - 2.0 * (x * x + y * y)))))


def onEdge(angle: float) -> tuple[float, float, float, float]:
  """The 'onEdge' function returns the turn of a coin standing on its
  edge, its faces square to y, turned 'angle' further about x."""
  half = (math.pi / 2.0 + angle) / 2.0
  return math.sin(half), 0.0, 0.0, math.cos(half)


def rained(world: CoinWorld, seconds: float, seed: int) -> list[float]:
  """The 'rained' function drops each coin of 'world' in turn from 6 cm
  over the highest in play, turned at random up to 34 degrees, across
  60 mm, playing 'seconds' after each; and returns how deep two
  overlapped at most, a drop."""
  rng = numpy.random.default_rng(seed)
  deepest = []
  for index in range(world.count):
    playing = world.playing
    top = float(world.places[playing][:, 2].max()) if playing.any() else 0.0
    axis = rng.uniform(-0.6, 0.6, 3)
    angle = float(numpy.linalg.norm(axis))
    turn = tuple(axis / angle * math.sin(angle / 2.0))
    world.place(index, (rng.uniform(-30.0, 30.0), rng.uniform(-30.0, 30.0),
                        top + 60.0),
                turn + (math.cos(angle / 2.0),), NOUGHT, NOUGHT)
    world.clearDeepest()
    world.played(seconds)
    deepest.append(world.deepest)
  return deepest


def _inverted(turn: numpy.ndarray, vector: numpy.ndarray) -> numpy.ndarray:
  """'vector' turned back by 'turn' (x y z w)."""
  u, w = turn[:3], turn[3]
  return (vector - 2.0 * w * numpy.cross(u, vector) +
          2.0 * numpy.cross(u, numpy.cross(u, vector)))


def _turned(turn: numpy.ndarray, vector: numpy.ndarray) -> numpy.ndarray:
  """'vector' turned by 'turn' (x y z w)."""
  u, w = turn[:3], turn[3]
  return (vector + 2.0 * w * numpy.cross(u, vector) +
          2.0 * numpy.cross(u, numpy.cross(u, vector)))


def _rings(coin: Coin) -> numpy.ndarray:
  """Points through a coin in its own frame: rings across its faces and
  its middle."""
  rings = []
  for reach in numpy.linspace(0.0, coin.radius, 7):
    for angle in numpy.linspace(0.0, 2.0 * math.pi, 24, False):
      for z in (-coin.half, 0.0, coin.half):
        rings.append((reach * math.cos(angle), reach * math.sin(angle), z))
  return numpy.array(rings)


def _inside(world: CoinWorld, i: int, j: int,
            rings: numpy.ndarray) -> float:
  """How far any of the points through coin i lies inside coin j."""
  coin, places, turns = world.coin, world.places, world.turns
  most = 0.0
  for point in rings:
    p = places[i] + _turned(turns[i], point)
    local = _inverted(turns[j], p - places[j])
    reach = math.hypot(local[0], local[1])
    most = max(most, min(coin.radius - reach, coin.half - abs(local[2])))
  return most


def overlapWith(world: CoinWorld, index: int) -> float:
  """The 'overlapWith' function returns, in mm, how far coin 'index' and
  any coin in play near it lie inside one another, measured on its own,
  not by the solver: rings across each coin's faces and middle against
  the other's exact shape."""
  rings = _rings(world.coin)
  places, playing = world.places, world.playing
  most = 0.0
  for other in numpy.nonzero(playing)[0]:
    if other == index:
      continue
    apart = numpy.linalg.norm(places[index] - places[other])
    if apart > 2.0 * world.coin.radius:
      continue
    most = max(most, _inside(world, index, int(other), rings),
               _inside(world, int(other), index, rings))
  return most


def overlapOf(world: CoinWorld) -> float:
  """The 'overlapOf' function returns, in mm, how far any coin in play
  lies inside another, as 'overlapWith' measures it."""
  most = 0.0
  for index in numpy.nonzero(world.playing)[0]:
    most = max(most, overlapWith(world, int(index)))
  return most


class PusherTest(BaseTest):
  """Base class for the tests of the coin pusher's coins and machine."""


class PusherWidgetTest(WidgetTest):
  """Base class for the tests of the coin pusher's widgets."""

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)
