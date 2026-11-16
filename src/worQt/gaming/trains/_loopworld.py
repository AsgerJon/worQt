"""
LoopWorld is the loop de loop's world (user, 2026-11-15: "a void world,
like in skyblock, where there is only enough terrain for the loop de
loop"): the loop's track in the void and the floating island of grass
on dirt under its start, both solid (user, 2026-11-15: "the curvy bit
of the track does not appear to have collision with the Avatar"). Nothing
else is in it until spawned.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worQt.phys._body import Body, State
from worQt.phys._compiled import gpuDevice
from worQt.phys._shape import boxShape
from worQt.phys._vectors import UNTURNED, turnOf
from worQt.phys._small_steps import THREADS, SmallSteps, preloaded
from worQt.phys.rail._trackshape import BED_DEEP, BED_HALF, BED_TOP, GAUGE
from worQt.phys.rail._trackshape import RAIL_SECTION, SLEEPER_DEEP
from worQt.phys.rail._trackshape import SLEEPER_HALF, SLEEPER_LONG
from worQt.phys.rail._trackshape import SLEEPER_PITCH, SLEEPER_TOP
from worQt.phys.rail._trackshape import trackQuads
from worQt.phys.rail import RailWorld, loopTrack, wheelsetBody
from worQt.phys.rail._railrun import preloadedRails
from worQt.phys.rail._railworld import FRICTION
from worQt.phys.rail._stage import DIRT, DROP, EARTH, GRASS, ISLAND_FROM
from worQt.phys.rail._stage import ISLAND_HALF, ISLAND_TO, ISLAND_UNDER
from worQt.phys.rail._stage import WALKER_AT

from worQt.gaming.sandbox import EARTH_GRAVITY, World

from ._minecart import Minecart

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import Universe

#  The small steps' longest step, s (the island holds only what is
#  spawned on it; the wheelsets step in the rail world at its own).
LOOP_STEP = 2.5e-4
#  Fallen below this, m, a body has left the world (the island's top is
#  29.6 m up, the loop's foot at nought).
LOOP_LOWEST = -20.0
#  The track is solid in pieces this long, m (two sleepers each: on the
#  loop a piece lies within 18 mm of the curve); a rail's head, as
#  wide and as tall as the rail, m.
CHUNK = 2.0 * SLEEPER_PITCH
RAIL_WIDE = RAIL_SECTION[1][0] - RAIL_SECTION[0][0]
RAIL_HIGH = -RAIL_SECTION[6][1]
#  The rail world as the window runs it, s: the spec's reference, its
#  wheels' step 0.1 ms and the axleboxes traded with the small steps
#  every 2 ms, all on the world's device (float32: the wheelsets in the
#  track's frame; every trade on the device, nothing back in Python
#  till the call's end): the loop's world with the avatar and the cart
#  8.2 ms a frame on the GPU (204 % of real time) while another project
#  used 62 % of it (19.8 ms with a trip through Python each trade).
LIVE_STEP, LIVE_EXCHANGE = 1e-4, 2e-3
#  The buffer stops past either end of the track (user, 2026-11-16,
#  previews/wiley_coyote_lol.png: the minecart rolled off the start's
#  open end into the void, its rider in it): a steel beam across at the
#  height of the cart's ends (its wings, forks and beams, 0.39-0.56 m
#  up), long, wide, high, its middle over the rails' top, m, on two
#  posts down to the bed; steel, kg/m³.
BEAM, BEAM_WIDE, BEAM_HIGH, BEAM_AT = 0.3, 2.6, 0.5, 0.5
POST = 0.2
STEEL = 7850.0
#  Where the minecart waits, m along the track: on the start platform,
#  its front wheels 0.5 m before its edge (user, 2026-11-16: "let's get
#  a 'minecart' but fr on that track").
MINECART_AT = 8.5


class LoopWorld(World):
  """
  LoopWorld is the loop's world: its track (drawn: rails, sleepers, a
  bed of grass on dirt; solid: a body held still every 'CHUNK' m along
  it, its bed, sleepers and rails as boxes, not drawn) and the island
  under the start platform (its grass and its dirt, bodies held still);
  a 'Minecart' waiting on the start platform ('MINECART_AT', among its
  'vehicles'); a buffer stop past either end of the track ('buffers',
  their indices); the void about them. Its
  physics is the small steps (on the GPU where there is one), the
  wheelsets on its track rolled by the rail world. The rail world knows
  only the earth's gravity, so another universe is refused.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  LOOKS = {'rail': ((148, 150, 154), 0.3, 0.35),
           'wheel': ((148, 150, 154), 0.3, 0.35),
           'cart': ((196, 28, 32), 0.1, 0.45),
           'buffer': ((196, 48, 40), 0.2, 0.5),
           'sleeper': ((168, 166, 158), 0.0, 0.8),
           'grass': ((86, 128, 54), 0.0, 0.95),
           'dirt': ((112, 84, 58), 0.0, 1.0)}
  lowest = LOOP_LOWEST

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, universe: Universe) -> None:
    if universe.gravity != EARTH_GRAVITY:
      raise NotImplementedError('the rail world knows only the earth\'s '
                                'gravity, not %r m/s²' % universe.gravity)
    World.__init__(self, universe, None)
    self.track, self.device = loopTrack(), gpuDevice() or 'cpu'
    top = DROP - ISLAND_UNDER
    long, wide = ISLAND_TO - ISLAND_FROM, 2.0 * ISLAND_HALF
    middle = 0.5 * (ISLAND_FROM + ISLAND_TO)
    self.fixed(Body.of(boxShape(long, wide, GRASS), EARTH),
               State((middle, 0.0, top - 0.5 * GRASS)), 'grass')
    self.fixed(Body.of(boxShape(long, wide, DIRT), EARTH),
               State((middle, 0.0, top - GRASS - 0.5 * DIRT)), 'dirt')
    pieces = math.ceil(self.track.length / CHUNK - 1e-9)
    for k in range(pieces):
      begins = k * CHUNK
      self._fixedChunk(begins, min(self.track.length, begins + CHUNK))
    self.buffers = (self._fixedBuffer(0.0, -1.0),
                    self._fixedBuffer(self.track.length, 1.0))
    self.addVehicle(Minecart(MINECART_AT))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solverOf(self, ) -> object:
    """The 'solverOf' method returns the small steps on the world's
    device, its wheelsets handed to the rail world (stepped and traded
    'LIVE_STEP', 'LIVE_EXCHANGE')."""
    inner = SmallSteps(self.universe.gravityVector(), None, LOOP_STEP, 1,
                       0.0, self.device, THREADS, False)
    return RailWorld(inner, self.track, wheelsetBody(), LIVE_STEP,
                     FRICTION, LIVE_EXCHANGE, self.device)

  def spawnPoint(self, ) -> tuple:
    """The 'spawnPoint' method returns where an avatar enters: on the
    island, beside the start platform, looking along the track."""
    return (WALKER_AT[0], WALKER_AT[1], DROP - ISLAND_UNDER), 0.0

  def fixtures(self, ) -> dict:
    """The 'fixtures' method returns the track's quads by look."""
    return trackQuads(self.track)

  def readied(self, ) -> None:
    """The 'readied' method loads (or compiles) the small steps' kernels
    for the world's device, saying so in 'loading' meanwhile."""
    self.loading = self.device
    try:
      preloaded(self.device)
      preloadedRails(self.device)
    finally:
      self.loading = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _fixedBuffer(self, along: float, way: float) -> int:
    """Puts a buffer stop past the track's end at 'along' ('way': -1 its
    start, 1 its end) and returns its index: a beam across at the tub's
    end walls' height and two posts under it, held still, drawn."""
    beam = boxShape(BEAM, BEAM_WIDE, BEAM_HIGH).moved(
      (way * 0.5 * BEAM, 0.0, BEAM_AT), UNTURNED)
    low = BED_TOP - BED_DEEP
    high = BEAM_AT - 0.5 * BEAM_HIGH
    for side in (-0.6, 0.6):
      beam = beam.joined(boxShape(POST, POST, high - low).moved(
        (way * 0.5 * BEAM, side, 0.5 * (low + high)), UNTURNED))
    body = Body.of(beam, STEEL)
    place, frame = self.track.frameAt(along)
    rows = tuple(tuple(float(x) for x in row) for row in frame)
    centre = tuple(float(place[i]) + sum(rows[i][j] * body.centre[j]
                                         for j in range(3))
                   for i in range(3))
    return self.fixed(body, State(centre, turnOf(rows)), 'buffer')

  def _fixedChunk(self, begins: float, ends: float) -> None:
    """Puts the track from 'begins' to 'ends' m along in the world as one
    body held still, straight along the track's frame at its middle:
    the bed, the sleepers whose middles lie in it, the two rails' heads,
    each a box; not drawn (the track's dress is)."""
    middle, long = 0.5 * (begins + ends), ends - begins
    shape = boxShape(long, 2.0 * BED_HALF, BED_DEEP).moved(
      (0.0, 0.0, BED_TOP - 0.5 * BED_DEEP), UNTURNED)
    first = math.ceil((begins - 0.5 * SLEEPER_PITCH) / SLEEPER_PITCH)
    at = (first + 0.5) * SLEEPER_PITCH
    while at < ends:
      shape = shape.joined(boxShape(
        SLEEPER_LONG, 2.0 * SLEEPER_HALF, SLEEPER_DEEP).moved(
        (at - middle, 0.0, SLEEPER_TOP - 0.5 * SLEEPER_DEEP), UNTURNED))
      at += SLEEPER_PITCH
    for side in (-0.5 * GAUGE, 0.5 * GAUGE):
      shape = shape.joined(boxShape(long, RAIL_WIDE, RAIL_HIGH).moved(
        (0.0, side, -0.5 * RAIL_HIGH), UNTURNED))
    body = Body.of(shape, EARTH)
    place, frame = self.track.frameAt(middle)
    rows = tuple(tuple(float(x) for x in row) for row in frame)
    centre = tuple(float(place[i]) + sum(rows[i][j] * body.centre[j]
                                         for j in range(3))
                   for i in range(3))
    self.fixed(body, State(centre, turnOf(rows)), None)
