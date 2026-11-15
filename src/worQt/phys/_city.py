"""
The real car in town (user, 2026-11-15: uncannyball's lap of central
Copenhagen, 'previews/uncannyball_readme.md'): the lap's road read
('_crg.readCrg', from 'CITY_TRACK', 'previews/royal_race.crg': not in
git, made by uncannyball) and laid onto the small steps' terrain at
'CITY_CELL' m ('cityGround': the tyre yard's ground on it, no walls yet:
the file is the ground and nothing else), as a course ('cityCourse'),
the real car set down at its start ('cityStart': the east gate of
Amalienborg Slotsplads, on the road's middle, heading along it; level,
the town is all but), the walker sat in it ('realCarInCity'), and the
palace square by the start (user, 2026-11-15: "Just try to see if you
can put Amalienborg Slotsplads in there lol"): its four palaces on the
octagon's diagonal sides and Frederik V on horseback in its middle
('amalienborg'), each part of the world, the walker meeting them (the
car keeps to the road: it meets none of them). The heights
are public data: 'ATTRIBUTION' goes with what is
shown.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
import os

from ._assembly import Assembly, Contact, Fixed
from ._body import Body, State
from ._crg import ATTRIBUTION, crgTerrain, readCrg
from ._ground import Ground
from ._vectors import Vector

#  Where the lap's file is (uncannyball's, beside its note), how finely
#  its heights are laid onto the terrain's grid and how far past the
#  road's edge, m (on the road within 4 cm of the file's, 3 mm mean; 20
#  million cells, 165 MB as the GPU holds them), and how wide the course
#  is taken to be (its plan's; the file has no kerbs), m.
CITY_TRACK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', '..', '..', 'previews', 'royal_race.crg')
CITY_CELL, CITY_MARGIN, CITY_WIDTH = 0.5, 10.0, 7.0
#  Amalienborg Slotsplads, as near as the lap and what is public say: its
#  middle (the statue) where the lap's hairpin round it is centred (a
#  circle fitted to its middle line 100 to 200 m from the start: within
#  3 m whichever span; Wikipedia's 55 41 02 N 12 35 35 E, to the
#  arcsecond, lies 28 m off, within its rounding), m; the way its streets
#  run (Frederiksstaden's grid, from the lap's long straight up
#  Toldbodgade into it: Amaliegade's way, rad from x; Frederiksgade
#  across it); how far its palaces' fronts stand from its middle, m (an
#  octagon's sides 47 m long, the palaces' fronts: a guess, nowhere
#  published that I found; the readme's next grid will say); each
#  palace's depth and height to its cornice, m, its roof's (a block on
#  it); the statue's pedestal (length along Frederiksgade, width, height)
#  and the bronze on it (all of it almost 12 m: Wikipedia), m; how dense
#  the masonry and the bronze are (they never move: bodies of the
#  world).
SQUARE_MIDDLE, SQUARE_WAY = (1879.0, 774.0), math.radians(68.7)
SQUARE_FRONT, PALACE_DEEP, PALACE_HIGH = 57.0, 18.0, 17.0
ROOF_HIGH, ROOF_IN = 5.0, 2.0
PEDESTAL, RIDER = (6.0, 3.0, 5.5), (5.0, 1.8, 6.3)
MASONRY, BRONZE = 1800.0, 8800.0
#  How the walker meets the square: stone gripping 0.6, a touch a part.
#  The car meets none of it (user, 2026-11-15: "the palace need not have
#  exact collision", "just don't spend compute bro!": its skin against
#  the stone, even one way at 0.3 m, was 1 500 touches looked for about
#  the square; the car keeps to the road, and driven into a palace by
#  hand it goes through).
_ON_STONE = (1e6, 1.0, 0.6, 1e6, 2e3)


def cityTrack() -> object:
  """The 'cityTrack' function returns the lap's road ('readCrg'), read
  once; refused loudly where its file is not ('CITY_TRACK')."""
  path = os.path.normpath(CITY_TRACK)
  if not os.path.isfile(path):
    raise FileNotFoundError('the city lap is not here: %s (uncannyball '
                            'makes it: see its note)' % path)
  return readCrg(path)


@functools.lru_cache(maxsize=1)
def cityGround() -> Ground:
  """The 'cityGround' function returns the tyre yard's ground on the
  lap's terrain ('crgTerrain'), made once (seconds)."""
  from ._carcass import TYRE_YARD
  return TYRE_YARD._replace(terrain=crgTerrain(cityTrack(), CITY_CELL,
                                               CITY_MARGIN))


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


def amalienborg() -> tuple:
  """The 'amalienborg' function returns the palace square's parts, each
  (key, size (length, width, height), its middle (x, y, z), its heading,
  rad): the four palaces' masonry and roofs on the octagon's diagonal
  sides ('SQUARE_FRONT' from its middle, the streets in its four sides
  between), the statue's pedestal and its bronze, each on the ground
  under it."""
  terrain = cityGround().terrain
  side = 2.0 * SQUARE_FRONT * math.tan(math.pi / 8.0)
  parts = []
  for k in range(4):
    way = SQUARE_WAY + math.pi / 4.0 + k * math.pi / 2.0
    out = SQUARE_FRONT + 0.5 * PALACE_DEEP
    x = SQUARE_MIDDLE[0] + out * math.cos(way)
    y = SQUARE_MIDDLE[1] + out * math.sin(way)
    base = terrain.heightAt(x, y)
    heading = way + 0.5 * math.pi
    parts.append(('palace', (side, PALACE_DEEP, PALACE_HIGH),
                  (x, y, base + 0.5 * PALACE_HIGH), heading))
    parts.append(('roof', (side - 2.0 * ROOF_IN, PALACE_DEEP - 2.0 * ROOF_IN,
                           ROOF_HIGH),
                  (x, y, base + PALACE_HIGH + 0.5 * ROOF_HIGH), heading))
  x, y = SQUARE_MIDDLE
  base = terrain.heightAt(x, y)
  across = SQUARE_WAY - 0.5 * math.pi
  parts.append(('pedestal', PEDESTAL, (x, y, base + 0.5 * PEDESTAL[2]),
                across))
  parts.append(('bronze', RIDER, (x, y, base + PEDESTAL[2]
                                  + 0.5 * RIDER[2]), across))
  return tuple(parts)


def realCarInCity(controls: object) -> tuple[Assembly, tuple[State, ...]]:
  """The 'realCarInCity' function returns the real car worked by
  'controls' at the lap's start ('cityStart'), the walker sat in it, and
  the palace square ('amalienborg') after it, each part of the world,
  the walker meeting each (the car none)."""
  from ._realcar import realCar
  from ._shape import boxShape
  assembly, states = realCar(controls, cityStart())
  first = len(assembly.bodies)
  bodies, placed = list(assembly.bodies), list(states)
  connections = list(assembly.connections)
  for k, (key, size, middle, heading) in enumerate(amalienborg()):
    index = first + k
    bodies.append(Body.of(boxShape(*size), BRONZE if key == 'bronze'
                          else MASONRY))
    placed.append(State(middle, (math.cos(0.5 * heading), 0.0, 0.0,
                                 math.sin(0.5 * heading))))
    connections.append(Fixed(index))
    connections.append(Contact(0, index, *_ON_STONE))
  return Assembly(tuple(bodies), tuple(connections)), tuple(placed)


def squareFirst() -> int:
  """The 'squareFirst' function returns where the square's bodies start
  among 'realCarInCity''s (after the real car's)."""
  from ._realcar import HALVES
  return HALVES[1] + 1


def squareFinishes() -> dict:
  """The 'squareFinishes' function returns how the square's bodies are
  drawn, by their index in 'realCarInCity''s assembly: each its key
  ('palace', 'roof', 'pedestal', 'bronze')."""
  first = squareFirst()
  return {first + k: part[0] for k, part in enumerate(amalienborg())}
