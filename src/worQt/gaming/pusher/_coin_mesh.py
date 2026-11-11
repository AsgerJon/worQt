"""
The coin as triangles for a 3D view, its faces mapped to pictures of
them and its edge reeded in sections; it needs no Qt.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._coin import Coin

#  The parts of a coin's triangles, in order: 'coinMesh' returns where
#  each begins and how many corners it has.
TOP, BOTTOM, EDGE = 0, 1, 2


def _corner(x: float, y: float, z: float, normal: tuple, u: float,
            v: float) -> list[float]:
  """A corner: where, its normal, where on the picture."""
  return [x, y, z, normal[0], normal[1], normal[2], u, v]


def _faces(coin: Coin, segments: int, fill: float) -> tuple[list, list]:
  """The top and bottom faces as fans round their middles, each mapped
  to its picture as seen from its side: the picture's top toward y."""
  r, h = coin.radius, coin.half
  top, bottom = [], []
  for k in range(segments):
    a0 = 2.0 * math.pi * k / segments
    a1 = 2.0 * math.pi * (k + 1) / segments
    ring = [(r * math.cos(a), r * math.sin(a)) for a in (a0, a1)]
    for points, z, normal, sign, out in (
        (((0.0, 0.0), ring[0], ring[1]), h, (0.0, 0.0, 1.0), 1.0, top),
        (((0.0, 0.0), ring[1], ring[0]), -h, (0.0, 0.0, -1.0), -1.0,
         bottom)):
      for x, y in points:
        u = 0.5 + sign * 0.5 * fill * x / r
        v = 0.5 - 0.5 * fill * y / r
        out.append(_corner(x, y, z, normal, u, v))
  return top, bottom


def _reeded(angle: float, sections: int, share: float) -> bool:
  """Whether the edge is reeded at 'angle': 'sections' reeded stretches
  evenly round, each 'share' of its part of the round."""
  part = 2.0 * math.pi / sections
  return (angle % part) < share * part


def _edge(coin: Coin, segments: int, sections: int, share: float,
          depth: float) -> list:
  """The edge, a band round the coin: smooth where it is smooth, and
  where it is reeded, grooved, its corners in and out by turns, each
  facet flat."""
  r, h = coin.radius, coin.half
  out = []
  for k in range(segments):
    a0 = 2.0 * math.pi * k / segments
    a1 = 2.0 * math.pi * (k + 1) / segments
    middle = 0.5 * (a0 + a1)
    if _reeded(middle, sections, share):
      r0 = r - (depth if k % 2 else 0.0)
      r1 = r - (0.0 if k % 2 else depth)
      p0 = numpy.array((r0 * math.cos(a0), r0 * math.sin(a0)))
      p1 = numpy.array((r1 * math.cos(a1), r1 * math.sin(a1)))
      run = p1 - p0
      facet = numpy.array((run[1], -run[0])) / numpy.linalg.norm(run)
      n0 = n1 = (float(facet[0]), float(facet[1]), 0.0)
    else:
      p0 = numpy.array((r * math.cos(a0), r * math.sin(a0)))
      p1 = numpy.array((r * math.cos(a1), r * math.sin(a1)))
      n0 = (math.cos(a0), math.sin(a0), 0.0)
      n1 = (math.cos(a1), math.sin(a1), 0.0)
    u0, u1 = k / segments, (k + 1) / segments
    low0 = _corner(p0[0], p0[1], -h, n0, u0, 1.0)
    low1 = _corner(p1[0], p1[1], -h, n1, u1, 1.0)
    high0 = _corner(p0[0], p0[1], h, n0, u0, 0.0)
    high1 = _corner(p1[0], p1[1], h, n1, u1, 0.0)
    out += [low0, low1, high1, low0, high1, high0]
  return out


def coinMesh(coin: Coin, segments: int, sections: int,
             share: float) -> tuple[numpy.ndarray, tuple]:
  """The 'coinMesh' function returns the triangles of 'coin' in its own
  frame, its axis z, 'segments' round: rows of corners, each where (x,
  y, z), its normal and where on its picture (u, v), three a triangle,
  facing out; and for 'TOP', 'BOTTOM' and 'EDGE' in turn where its
  corners begin and how many there are. The faces are mapped to their
  pictures filling them; the edge is reeded in 'sections' stretches,
  each 'share' of its part of the round, smooth between, the grooves a
  tenth of a mm deep."""
  top, bottom = _faces(coin, segments, 0.996)
  edge = _edge(coin, segments, sections, share, 0.1)
  rows = numpy.array(top + bottom + edge, numpy.float32)
  parts = ((0, len(top)), (len(top), len(bottom)),
           (len(top) + len(bottom), len(edge)))
  return rows, parts

