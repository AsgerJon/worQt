"""
DeckThings are the loose furnishings at the foot of each terminal's
stairs on Terra Prime's deck (user, 2026-11-19: "we need to put some
furnishings *with* physics at the end of the spokes"): crates, a bench,
a table and planters, each a loose box of its own mass in the cabin's
world ('_cabinworld': it knocks over, slides, is pushed by Asger).
Docked, they are bodies of the cabin's world in the docked rocket's
axes; undocked, they are put away there (no mass: '_cabin_kernels') and
kept here where they were, in the station's own axes ('places',
'turns': each its middle, its turn from its rest, w x y z). Their rest
('deckThings': each its name, look, middle, half sizes, axes along the
ring, against the axis and in, mass), their meshes ('deckThingRows').
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._shapes import UNTURNED, boxRows
from ._stationinterior import DECK, stationPoint, stationWay
from ._terminal import PLATFORM_DEEP, STEP_RUN, STEPS, GUIDE_HALF
from ._terminal import GUIDE_WALL, spokeAngles
from ._turns import product, quaternionOf

#  The furnishings at each terminal: each its name, look, how far round
#  the ring past the stairs' foot and along the axis it stands, m, its
#  half sizes (along the ring, along the axis, up), m, its mass, kg.
FURNISHINGS = (('crate', 'crate', 1.0, 1.6, (0.3, 0.3, 0.3), 30.0),
               ('crate', 'crate', 1.65, 1.6, (0.25, 0.25, 0.25), 18.0),
               ('crate', 'crate', 1.2, 2.25, (0.2, 0.2, 0.2), 10.0),
               ('bench', 'bench', 3.0, -2.0, (0.9, 0.22, 0.23), 25.0),
               ('table', 'table', 4.0, 0.6, (0.45, 0.45, 0.38), 20.0),
               ('planter', 'planter', 2.2, -0.9, (0.22, 0.22, 0.3), 35.0),
               ('planter', 'planter', 5.2, -0.9, (0.22, 0.22, 0.3), 35.0))


@functools.lru_cache(maxsize=1)
def deckThings() -> tuple:
  """Returns every deck furnishing at rest (the station's own axes): each
  its name, look, middle, half sizes (along its axes), axes (along the
  ring, against the axis, in: its up, toward the axis) and mass."""
  out = []
  foot = GUIDE_HALF + 2.0 * GUIDE_WALL + PLATFORM_DEEP + STEP_RUN * STEPS
  for angle in spokeAngles():
    for name, look, along, axial, half, mass in FURNISHINGS:
      high = DECK - half[2] - 0.002
      turned = angle + (foot + along) / high
      c, s = math.cos(turned), math.sin(turned)
      middle = (high * c, high * s, axial)
      axes = ((-s, c, 0.0), (0.0, 0.0, -1.0), (-c, -s, 0.0))
      out.append((name, look, middle, half, axes, mass))
  return tuple(out)


def deckThingRows(k: int) -> tuple:
  """Returns deck furnishing 'k''s mesh about its middle in its own axes
  (a box its size)."""
  return boxRows((0.0, 0.0, 0.0), deckThings()[k][3], UNTURNED)


def restTurn(k: int) -> tuple:
  """Returns deck furnishing 'k''s turn at rest: its own axes to the
  station's (w x y z)."""
  axes = deckThings()[k][4]
  return quaternionOf(tuple((axes[0][i], axes[1][i], axes[2][i])
                            for i in range(3)))


#  The docked rocket's axes in the station's the cabin's world is built
#  with (the debug menu's docking's), its furnishings put away at first.
TELEPORTED = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))


def deckWorldThings() -> tuple:
  """Returns the deck's furnishings as the cabin's world takes them (its
  loose things: each its name, middle, half sizes, axes at rest: its
  own, and mass), their middles laid docked as the debug menu docks;
  their turns are not: the world's 'bodiesPlaced' lays those ('laid'),
  before the first step."""
  laid = DeckThings().laid(TELEPORTED)
  return tuple((thing[0], place, thing[3], UNTURNED, thing[5])
               for thing, (place, _) in zip(deckThings(), laid))


class DeckThings:
  """
  DeckThings holds where the deck's furnishings are while undocked
  ('places', 'turns': each its middle and its turn, own axes to the
  station's, w x y z, the station's own axes); 'laid' says where each is
  in the docked rocket's own axes, 'kept' takes back where each is
  from the docked rocket's.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('places', 'turns')

  #  Public Variables
  places: list
  turns: list

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    things = deckThings()
    self.places = [list(thing[2]) for thing in things]
    self.turns = [list(restTurn(k)) for k in range(len(things))]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def laid(self, relative: tuple) -> tuple:
    """The 'laid' method returns each furnishing's middle and turn (own
    axes to the docked rocket's, w x y z) in the docked rocket's own axes
    ('relative': its axes in the station's)."""
    station = _stationTurn(relative)
    return tuple((stationPoint(tuple(p), relative), product(
      station, tuple(t))) for p, t in zip(self.places, self.turns))

  def kept(self, bodies: tuple, relative: tuple) -> None:
    """The 'kept' method takes back where each furnishing is ('bodies':
    each its middle and turn in the docked rocket's own axes) into the
    station's own axes ('relative' as 'laid')."""
    station = _stationTurn(relative)
    back = (station[0], -station[1], -station[2], -station[3])
    for k, (place, turn) in enumerate(bodies):
      self.places[k] = list(_stationOf(tuple(place), relative))
      self.turns[k] = list(product(back, tuple(turn)))


def _stationTurn(relative: tuple) -> tuple:
  """Returns the turn taking the station's own axes to the docked
  rocket's (w x y z; 'relative': the rocket's axes in the station's, the
  rows of that turn's matrix)."""
  return quaternionOf(tuple(tuple(row) for row in relative))


def _stationOf(point: tuple, relative: tuple) -> tuple:
  """Returns 'point' (the docked rocket's own axes) in the station's own
  axes ('stationPoint' undone)."""
  from ._stationinterior import PLANE
  local = (point[0], point[1], point[2] - PLANE)
  return tuple(sum(local[i] * relative[i][j] for i in range(3))
               for j in range(3))
