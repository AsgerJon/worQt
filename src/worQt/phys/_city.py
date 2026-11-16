"""
The real car in town (user, 2026-11-15: uncannyball's lap of central
Copenhagen; its files in 'previews/tracks', 'previews/to_worqt.md',
their note 'README.md' beside them): the lap's road read
('_crg.readCrg', 'CITY_TRACK') and laid onto the small steps' terrain at
'CITY_CELL' m ('cityGround': the tyre yard's ground on it, walled where
the houses stand, 'cityWall'), as a course ('cityCourse'), the real
car set down at its start ('cityStart': the east gate of Amalienborg
Slotsplads, on the road's middle, heading along it; level, the town is
all but), the walker sat in it ('realCarInCity'), the car and the
walker meeting the walls. For the eye only: the ground as photographed
from above along the lap ('cityPictures', 'cityManifest'), and the
houses round the start in 3D ('cityScenery': Amalienborg's four
palaces, Frederik V, the Marble Church, the streets about, 512 m a
side, 'sceneryBox'; its ground within 4 mm of the terrain's on the
road), made by uncannyball from photographs at 45 degrees and the
laser scan. The data are public: 'CITY_CREDIT' goes with what is shown.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import json
import math
import os

import numpy

from ._assembly import Assembly
from ._body import State
from ._crg import crgTerrain, readCrg
from ._ground import Ground
from ._vectors import Vector

#  Where the lap's files are (uncannyball's, beside its note: not in
#  git, its photographs' licences not all settled), its manifest, its
#  road, its scenery; how finely its heights are laid onto the terrain's
#  grid and how far past the road's edge, m (on the road within 4 cm of
#  the file's, 3 mm mean; 20 million cells, 165 MB as the GPU holds
#  them), and how wide the course is taken to be (its plan's), m.
CITY_FOLDER = os.path.normpath(os.path.join(
  os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'previews',
  'tracks'))
CITY_MANIFEST = os.path.join(CITY_FOLDER, 'royal_race.json')
CITY_TRACK = os.path.join(CITY_FOLDER, 'royal_race.crg')
CITY_STANDING = os.path.join(CITY_FOLDER, 'royal_race_standing.crg')
CITY_SCENERY = os.path.join(CITY_FOLDER, 'royal_race_scenery.glb')
CITY_CELL, CITY_MARGIN, CITY_WIDTH = 0.5, 10.0, 7.0
#  What the car and the walker meet as a wall (the scenery is only to be
#  looked at; the lap's note leaves the threshold to us): whatever stands
#  'WALL_LEAST' m or more on the ground (over a parked van or a bus: they
#  have driven off since the scan; under any house), beyond the road's
#  edges, more than 'WALL_CORRIDOR' m from its middle line (over the
#  line itself whatever stands is overhead: the boulevards' trees every
#  14 m down their middle strip, 5 to 30 m runs at 2 to 5 km round; at
#  5 m the line met them over 127 m of the lap); its faces sliding at
#  'WALL_GRIP' (the oval's barrier's). The trees beside a street are
#  walls too: the scan cannot tell a crown from a facade. Walls stand 4
#  m or more from the middle over all but 356 m of the lap, never
#  nearer than 2.7 m (their faces smoothed).
WALL_LEAST, WALL_CORRIDOR, WALL_GRIP = 3.5, 3.0, 0.5
#  What goes with anything shown that is made from the lap's files
#  (their note's 'Manners', its lines as they are: the heights and the
#  photographs from above, CC BY 4.0; the laser scan the scenery is
#  shaped from, likewise; the photographs at 45 degrees its walls are
#  from, their licence to be confirmed).
CITY_CREDIT = ('Contains data from Klimadatastyrelsen: Danmarks '
               'Højdemodel, DHM/Terræn, DHM/Overflade and DHM/Punktsky; '
               'GeoDanmark Ortofoto, forårsbilleder. CC BY 4.0. Contains '
               'data from Klimadatastyrelsen: Skråfoto.')


def _needed(path: str) -> str:
  """Returns 'path', refused loudly where its file is not (the lap's
  files are uncannyball's, not in git)."""
  if not os.path.isfile(path):
    raise FileNotFoundError('the city lap is not all here: %s (uncannyball '
                            'makes it: see previews/to_worqt.md)' % path)
  return path


def cityHere() -> bool:
  """The 'cityHere' function returns whether the lap's files are here
  (its manifest, its road, its scenery; its pictures are looked for as
  they are read)."""
  return all(os.path.isfile(path) for path in (
    CITY_MANIFEST, CITY_TRACK, CITY_STANDING, CITY_SCENERY))


def cityTrack() -> object:
  """The 'cityTrack' function returns the lap's road ('readCrg'), read
  once."""
  return readCrg(_needed(CITY_TRACK))


@functools.lru_cache(maxsize=1)
def cityManifest() -> dict:
  """The 'cityManifest' function returns what the lap's manifest says
  (its pictures, its road's edges, its materials, its credit), read
  once."""
  with open(_needed(CITY_MANIFEST), encoding='utf-8') as file:
    return json.load(file)


@functools.lru_cache(maxsize=1)
def cityPictures() -> tuple[tuple[float, float, str], ...]:
  """The 'cityPictures' function returns the lap's ground as
  photographed from above, stretch by stretch along it: (where along
  the lap it begins, where it ends, m, its file); in each the lap runs
  up the picture, its foot where the stretch begins, its left edge 60 m
  left of the road's middle, its right 60 m right."""
  return tuple((float(begins), float(ends),
                _needed(os.path.join(CITY_FOLDER, name)))
               for begins, ends, name in cityManifest()['picture'])


def cityScenery() -> tuple:
  """The 'cityScenery' function returns the houses round the lap's start
  ('_glb.readGlb': its pieces and its pictures), read once."""
  from ._glb import readGlb
  return readGlb(_needed(CITY_SCENERY))


@functools.lru_cache(maxsize=1)
def sceneryBox() -> tuple[float, float, float, float]:
  """The 'sceneryBox' function returns the square the scenery covers
  (x0, y0, x1, y1, m: its ground drawn there, the lap's not)."""
  corners = numpy.concatenate([piece.xyz for piece in cityScenery()[0]])
  low, high = corners.min(0), corners.max(0)
  return float(low[0]), float(low[1]), float(high[0]), float(high[1])


def cityEdges() -> tuple[numpy.ndarray, numpy.ndarray]:
  """The 'cityEdges' function returns how far the road reaches to the
  right of its middle and to the left at each of its rows, m (the
  manifest's runs, each from where it begins along the lap to where it
  ends; a row past the last run's end in the last)."""
  runs = cityManifest()['edges']
  track = cityTrack()
  along = numpy.arange(len(track.x)) * track.step
  ends = numpy.array([run[1] for run in runs])
  found = numpy.minimum(numpy.searchsorted(ends, along, 'right'),
                        len(runs) - 1)
  return (numpy.array([run[2] for run in runs])[found],
          numpy.array([run[3] for run in runs])[found])


def cityWall(terrain: object) -> object:
  """The 'cityWall' function returns the town's walls on 'terrain''s
  grid ('_gridwall.standingWall': where the lap's standing heights say
  'WALL_LEAST' m or more, beyond its edges, 'WALL_CORRIDOR' m from its
  middle; seconds)."""
  from ._gridwall import standingWall
  return standingWall(cityTrack(), readCrg(_needed(CITY_STANDING)),
                      cityEdges(), (terrain.origin, terrain.cell,
                                    numpy.shape(terrain.heights)),
                      WALL_LEAST, WALL_CORRIDOR, WALL_GRIP)


@functools.lru_cache(maxsize=1)
def cityGround() -> Ground:
  """The 'cityGround' function returns the tyre yard's ground on the
  lap's terrain ('crgTerrain'), walled where the houses stand
  ('cityWall'), made once (ten seconds)."""
  from ._carcass import TYRE_YARD
  terrain = crgTerrain(cityTrack(), CITY_CELL, CITY_MARGIN)
  return Ground(*TYRE_YARD[:6], terrain, cityWall(terrain))


@functools.lru_cache(maxsize=1)
def cityCourse() -> object:
  """The 'cityCourse' function returns the lap as a course
  ('CrgCourse', 'CITY_WIDTH' wide)."""
  from ._course import CrgCourse
  return CrgCourse(cityTrack(), CITY_WIDTH)


def cityStart() -> tuple[Vector, tuple]:
  """The 'cityStart' function returns where the real car's frame starts:
  on the road's middle at the lap's start, on the ground there, heading
  along it, level."""
  track = cityTrack()
  x, y = float(track.x[0]), float(track.y[0])
  heading = float(track.heading[0])
  turn = (math.cos(0.5 * heading), 0.0, 0.0, math.sin(0.5 * heading))
  return (x, y, cityGround().terrain.heightAt(x, y)), turn


def realCarInCity(controls: object, built: object = None
                  ) -> tuple[Assembly, tuple[State, ...]]:
  """The 'realCarInCity' function returns the real car worked by
  'controls' at the lap's start ('cityStart'; built by 'built', None:
  the car of parts, '_realcar.realCar'; the stand-in car,
  '_magiccar.magicCar'), the walker sat in it."""
  from ._realcar import realCar
  built = realCar if built is None else built
  return built(controls, cityStart())
