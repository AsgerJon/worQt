"""
The track's shape along its ribbon ('Ribbon'), Qt-free geometry for
whatever draws it (user, 2026-11-15: "a void world, like in skyblock,
where there is only enough terrain for the loop de loop"): two rails of
an I section ('RAIL_SECTION'), their head tops on the ribbon's centre
line level, 'GAUGE' apart at their heads' middles; concrete sleepers
under them every 'SLEEPER_PITCH' m; under those the track's bed, grass
on its top and dirt round it, as wide as 'BED_HALF' either side and
'BED_DEEP' deep. All in the track's frame at each s (x along, y left, z
up), turned into the world, as quads by key ('trackQuads').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

#  The rail's section (y across, z up from its head's top, m: a head 72
#  mm wide, a web 16 mm, a foot 150 mm, 172 mm tall, as a 60 kg rail
#  is near enough) and the distance between the two heads' middles, m
#  (1435 mm between their inner faces); the sleepers' pitch, their
#  length along the track, their reach either side, their depth, m; the
#  bed's half width and depth, m; how often the rails and the bed are
#  cut along the track, m.
RAIL_SECTION = ((-0.036, 0.0), (0.036, 0.0), (0.036, -0.05), (0.008, -0.05),
                (0.008, -0.15), (0.075, -0.15), (0.075, -0.172),
                (-0.075, -0.172), (-0.075, -0.15), (-0.008, -0.15),
                (-0.008, -0.05), (-0.036, -0.05))
GAUGE = 1.507
SLEEPER_PITCH, SLEEPER_LONG, SLEEPER_HALF, SLEEPER_DEEP = 0.6, 0.25, 1.3, 0.2
BED_HALF, BED_DEEP = 2.0, 1.0
RAIL_CUT, BED_CUT = 0.25, 0.5
#  Where the sleepers' tops and the bed's top lie, m (under the rails'
#  foot, under the sleepers).
SLEEPER_TOP = -0.172
BED_TOP = SLEEPER_TOP - SLEEPER_DEEP


def _counterclockwise(outline: tuple) -> numpy.ndarray:
  """Returns 'outline' ((y, z) corners) turning anticlockwise (its
  edges' outward normals then (dz, -dy))."""
  points = numpy.array(outline, numpy.float64)
  y, z = points[:, 0], points[:, 1]
  area = 0.5 * float(numpy.sum(y * numpy.roll(z, -1) - numpy.roll(y, -1)
                               * z))
  return points if area > 0.0 else points[::-1].copy()


def sectionsOf(ribbon: object, cut: float) -> tuple:
  """The 'sectionsOf' function returns the ribbon cut every 'cut' m and
  at its end: the centre line's places (n, 3) and the frames (n, 3, 3)."""
  ss = numpy.append(numpy.arange(0.0, ribbon.length, cut), ribbon.length)
  places, frames = zip(*(ribbon.frameAt(s) for s in ss))
  return numpy.array(places), numpy.array(frames)


def extruded(places: numpy.ndarray, frames: numpy.ndarray,
             outline: tuple, keys: tuple, shift: float = 0.0) -> dict:
  """The 'extruded' function returns 'outline' ((y, z) corners in the
  track's frame, 'shift' m to the left) swept along the sections
  'places' and 'frames': for each of its edges, by its key in 'keys' (as
  the outline is given), a quad between every two sections, each corner
  its place and its edge's outward normal there, the quads facing out."""
  points = numpy.array(outline, numpy.float64)
  turned = _counterclockwise(outline)
  flipped = not numpy.array_equal(turned, points)
  edges = len(points)
  out = {}
  for j in range(edges):
    key = keys[(edges - 2 - j) % edges] if flipped else keys[j]
    p, q = turned[j], turned[(j + 1) % edges]
    normal = numpy.array((0.0, q[1] - p[1], -(q[0] - p[0])))
    normal /= numpy.linalg.norm(normal)
    a = places + frames @ numpy.array((0.0, p[0] + shift, p[1]))
    b = places + frames @ numpy.array((0.0, q[0] + shift, q[1]))
    n = frames @ normal
    quads = numpy.empty((len(places) - 1, 4, 6))
    quads[:, 0, :3], quads[:, 1, :3] = a[:-1], b[:-1]
    quads[:, 2, :3], quads[:, 3, :3] = b[1:], a[1:]
    quads[:, 0, 3:], quads[:, 1, 3:] = n[:-1], n[:-1]
    quads[:, 2, 3:], quads[:, 3, 3:] = n[1:], n[1:]
    out.setdefault(key, []).append(quads)
  return out


def capped(place: numpy.ndarray, frame: numpy.ndarray, outline: tuple,
           ahead: bool) -> numpy.ndarray:
  """The 'capped' function returns a convex 'outline' ((y, z) in the
  track's frame) at 'place' and 'frame' as one quad facing along the
  track ('ahead') or back."""
  turned = _counterclockwise(outline)
  if not ahead:
    turned = turned[::-1]
  normal = frame[:, 0] if ahead else -frame[:, 0]
  quad = numpy.empty((1, 4, 6))
  for k, (y, z) in enumerate(turned[:4]):
    quad[0, k, :3] = place + frame @ numpy.array((0.0, y, z))
    quad[0, k, 3:] = normal
  return quad


def trackQuads(ribbon: object) -> dict:
  """The 'trackQuads' function returns the track along 'ribbon' as quads
  by key ('rail', 'sleeper', 'grass', 'dirt'), each (n, 4, 6): every
  corner's place and normal, in the world."""
  out = {}

  def add(parts: dict) -> None:
    for key, quads in parts.items():
      out.setdefault(key, []).extend(quads if isinstance(quads, list)
                                     else [quads])

  places, frames = sectionsOf(ribbon, RAIL_CUT)
  keys = ('rail',) * len(RAIL_SECTION)
  for side in (-0.5 * GAUGE, 0.5 * GAUGE):
    add(extruded(places, frames, RAIL_SECTION, keys, side))
  bed = ((-BED_HALF, BED_TOP), (BED_HALF, BED_TOP),
         (BED_HALF, BED_TOP - BED_DEEP), (-BED_HALF, BED_TOP - BED_DEEP))
  places, frames = sectionsOf(ribbon, BED_CUT)
  add(extruded(places, frames, bed, ('grass', 'dirt', 'dirt', 'dirt')))
  add({'dirt': [capped(places[0], frames[0], bed, False),
                capped(places[-1], frames[-1], bed, True)]})
  sleeper = ((-SLEEPER_HALF, SLEEPER_TOP), (SLEEPER_HALF, SLEEPER_TOP),
             (SLEEPER_HALF, BED_TOP), (-SLEEPER_HALF, BED_TOP))
  for s in numpy.arange(0.5 * SLEEPER_PITCH, ribbon.length,
                        SLEEPER_PITCH):
    place, frame = ribbon.frameAt(s)
    ends = (place - 0.5 * SLEEPER_LONG * frame[:, 0],
            place + 0.5 * SLEEPER_LONG * frame[:, 0])
    add(extruded(numpy.array(ends), numpy.array((frame, frame)), sleeper,
                 ('sleeper',) * 4))
    add({'sleeper': [capped(ends[0], frame, sleeper, False),
                     capped(ends[1], frame, sleeper, True)]})
  return {key: numpy.concatenate(quads) for key, quads in out.items()}
