"""
The avatar's skin (user, 2026-11-16: "the Avatar should have a skin like
in minecraft", "give it AsgerJon's skin"): a 64 x 64 picture laid out as
Minecraft lays a skin out, wrapped round six blocks (the head, the body,
two arms, two legs: 'PARTS', in the picture's pixels) and, a little
larger, round the same blocks again (its outer layer: hair or a hat, a
jacket, sleeves, trousers; where it is see-through, nothing). 'partRows'
makes a block's rows for Qt Quick 3D. Qt-free. Drawn only: the world
meets the avatar as its ball, not as these blocks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from pathlib import Path

import numpy

#  The skins beside this file; the user's own, from its Minecraft
#  account (user, 2026-11-16: "give it AsgerJon's skin"); how many
#  pixels a skin is across.
SKINS = Path(__file__).with_name('skins')
ASGERJON = SKINS / 'asgerjon.png'
SIZE = 64
#  How high the eyes are over the soles, pixels (the face's fourth row
#  of eight from the top): the figure is scaled to put them at the
#  avatar's eyes.
EYES = 28.0
#  How far a seated figure sinks below its soles' place, pixels (its
#  hips 2 pixels over the seat, its legs ahead).
SEATED = 10.0
#  The parts, each: its name; its block, pixels in the figure's frame
#  (x ahead, y to its left, z up from the soles: from x, to x, from y,
#  to y, from z, to z); where it turns (its pivot); where its block's
#  picture begins in the skin and where its outer layer's does (u, v
#  from the top left); how much larger the outer layer is all round,
#  pixels. A block's picture lies as Minecraft lays it: across the top
#  its top and its bottom, under them its right side, its front, its
#  left side and its back ('_FACES').
PARTS = (
  ('head', (-4, 4, -4, 4, 24, 32), (0, 0, 24), (0, 0), (32, 0), 0.5),
  ('body', (-2, 2, -4, 4, 12, 24), (0, 0, 12), (16, 16), (16, 32), 0.25),
  ('right arm', (-2, 2, -8, -4, 12, 24), (0, -6, 22), (40, 16), (40, 32),
   0.25),
  ('left arm', (-2, 2, 4, 8, 12, 24), (0, 6, 22), (32, 48), (48, 48),
   0.25),
  ('right leg', (-2, 2, -4, 0, 0, 12), (0, -2, 12), (0, 16), (0, 32),
   0.25),
  ('left leg', (-2, 2, 0, 4, 0, 12), (0, 2, 12), (16, 48), (0, 48), 0.25))
#  A block's faces: its outward normal, its four corners as seen from
#  outside (top left, top right, bottom right, bottom left; each a pick
#  of (from or to) along x, y, z: 0 from, 1 to) and where its picture
#  lies (u, v from the block's picture's top left, as multiples of its
#  depth 'd' (x), width 'w' (y) and height 'h' (z); then its picture's
#  width and height, likewise).
_FACES = (
  ((1, 0, 0), ((1, 0, 1), (1, 1, 1), (1, 1, 0), (1, 0, 0)),
   ('d', 'd'), ('w', 'h')),
  ((0, -1, 0), ((0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)),
   ('', 'd'), ('d', 'h')),
  ((0, 1, 0), ((1, 1, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0)),
   ('dw', 'd'), ('d', 'h')),
  ((-1, 0, 0), ((0, 1, 1), (0, 0, 1), (0, 0, 0), (0, 1, 0)),
   ('ddw', 'd'), ('w', 'h')),
  ((0, 0, 1), ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)),
   ('d', ''), ('w', 'd')),
  ((0, 0, -1), ((1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0)),
   ('dw', ''), ('w', 'd')))


def _measure(letters: str, sizes: dict) -> float:
  """Returns the sum of the sizes named by 'letters' ('d', 'w', 'h')."""
  return float(sum(sizes[letter] for letter in letters))


def partRows(part: tuple, outer: bool,
             scale: float) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Returns 'part' (one of 'PARTS') as rows of eight numbers a corner
  (its place, m, from the part's pivot in the figure's frame; its
  outward normal; where it lies on the skin, nought to one from the
  picture's bottom left) and indices, two triangles a face, wound
  outward: its block, or 'outer', its outer layer's ('scale' m a
  pixel)."""
  _, block, pivot, inner, layer, swell = part
  grow = swell if outer else 0.0
  low = (block[0] - grow, block[2] - grow, block[4] - grow)
  high = (block[1] + grow, block[3] + grow, block[5] + grow)
  sizes = {'d': block[1] - block[0], 'w': block[3] - block[2],
           'h': block[5] - block[4]}
  u0, v0 = layer if outer else inner
  rows, indices = [], []
  for normal, corners, at, span in _FACES:
    left = u0 + _measure(at[0], sizes)
    top = v0 + _measure(at[1], sizes)
    right = left + _measure(span[0], sizes)
    bottom = top + _measure(span[1], sizes)
    pictured = ((left, top), (right, top), (right, bottom), (left, bottom))
    first = len(rows)
    for pick, (u, v) in zip(corners, pictured):
      place = tuple(scale * ((high if pick[i] else low)[i] - pivot[i])
                    for i in range(3))
      rows.append(place + tuple(float(n) for n in normal)
                  + (u / SIZE, 1.0 - v / SIZE))
    indices += [first, first + 3, first + 2, first, first + 2, first + 1]
  return (numpy.array(rows, numpy.float32),
          numpy.array(indices, numpy.uint32))
