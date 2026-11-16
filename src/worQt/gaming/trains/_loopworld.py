"""
LoopWorld is the loop de loop's world (user, 2026-11-15: "a void world,
like in skyblock, where there is only enough terrain for the loop de
loop"): the trains' line in the void ('_layout': a headshunt, points,
the station's platform, the loop eased in and out) with its siding,
and the floating island of grass on dirt under the station, all solid
(user, 2026-11-15: "the curvy bit of the track does not appear to have
collision with the Avatar"); a minecart waiting in the headshunt, a
train on the siding (user, 2026-11-16: "do all the things": a powered
cart and a cart coupled behind it), the points' lever beside them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy

from worQt.phys._body import Body, State
from worQt.phys._compiled import gpuDevice
from worQt.phys._shape import boxShape
from worQt.phys._small_steps import THREADS, SmallSteps, preloaded
from worQt.phys.rail._trackshape import trackQuads
from worQt.phys.rail import RailWorld, Turnout, wheelsetBody
from worQt.phys.rail._railrun import preloadedRails
from worQt.phys.rail._railworld import FRICTION
from worQt.phys.rail._stage import DIRT, DROP, EARTH, GRASS, ISLAND_UNDER

from worQt.gaming.sandbox import EARTH_GRAVITY, World
from worQt.gaming.sandbox._fourthpeep import FourthPeep

from ._layout import EDGE, TOE, mainLine, sidingLine
from ._minecart import COUPLED, Minecart
from ._solidtrack import chunkBody, chunksOf, stateOn, stopBody

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import Universe

#  The small steps' longest step, s (the island holds only what is
#  spawned on it; the wheelsets step in the rail world at its own).
LOOP_STEP = 2.5e-4
#  Fallen below this, m, a body has left the world (the island's top is
#  29.6 m up, the loop's foot at nought).
LOOP_LOWEST = -20.0
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
#  up): its beam's bottom and top over the rails' top, m
#  ('_solidtrack.stopBody').
BEAM_SPAN = (0.25, 0.75)
#  Where the minecart waits, m along the line: in the headshunt, its
#  back end 0.5 m before the start's buffer stop (user, 2026-11-16:
#  "let's get a 'minecart' but fr on that track").
MINECART_AT = 8.5
#  Where the train's powered cart stands on the siding, m from its
#  buffer stop's end of the track (its nose 1.55 m short of it); the
#  cart coupled behind it 'COUPLED' m further back.
TRAIN_SHORT = 5.5
#  The island (grass on dirt, its top 'ISLAND_UNDER' under the rails'
#  top): one block under the headshunt, the points and the platform, m
#  (from x, to x, from y, to y), one under the siding's far part.
ISLAND = (-6.0, EDGE + 2.0, -6.0, 9.0)
SIDING_ISLAND_BESIDE = 2.4
#  Where the avatar enters, m (x, y: on the island, right of the line,
#  before the points), looking along the line.
WALKER_AT = (TOE - 6.0, -4.0)
#  The points' lever (user, 2026-11-16: "do all the things", points
#  among them): on the island right of the line before the points
#  (x back from them, y), its handle long, m, turning about the world's
#  across from leaning back toward the line's start (set for the line)
#  to leaning ahead (for the siding), rad.
POINTS_BACK, POINTS_BESIDE = 3.0, -2.8
POINTS_LONG, POINTS_NEAR, POINTS_FAR = 0.8, -0.4, 0.4
#  How far under the line's the siding's dress is drawn, m (where the
#  two run together their beds and rails would fight to be seen).
SIDING_UNDER = 0.005


class LoopWorld(World):
  """
  LoopWorld is the loop's world: its 'tracks', the line ('track', the
  first) and the siding off its 'points' (a 'Turnout' set by its lever,
  'pointsLever', a 'FourthPeep' on the island), each drawn (rails,
  sleepers, a bed of grass on dirt) and solid (a body held still every
  'CHUNK' m along it, its bed, sleepers and rails as boxes, not drawn);
  the island under the station (its grass and its dirt, bodies held
  still, in two blocks); a 'Minecart' waiting in the headshunt
  ('MINECART_AT', first among its 'vehicles'), a train on the siding (a
  powered minecart and one coupled behind it); a buffer stop past the
  line's two ends and the siding's ('buffers', their indices); the void
  about them. Its physics is the small steps (on the GPU where there is
  one), the wheelsets on its tracks rolled by the rail world. The rail
  world knows only the earth's gravity, so another universe is
  refused.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  LOOKS = {'rail': ((148, 150, 154), 0.3, 0.35),
           'wheel': ((148, 150, 154), 0.3, 0.35),
           'cart': ((196, 28, 32), 0.1, 0.45),
           'powered': ((32, 72, 168), 0.1, 0.45),
           'coupler': ((70, 72, 78), 0.3, 0.4),
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
    self.tracks = (mainLine(), sidingLine())
    self.track, self.device = self.tracks[0], gpuDevice() or 'cpu'
    self.points = Turnout(0, TOE, 1)
    siding = self.tracks[1]
    end, _ = siding.frameAt(siding.length)
    self._fixedIsland(ISLAND)
    self._fixedIsland((ISLAND[1], float(end[0]) + 2.0,
                       SIDING_ISLAND_BESIDE, ISLAND[3]))
    for ribbon in self.tracks:
      for begins, ends in chunksOf(ribbon):
        body = chunkBody(begins, ends)
        self.fixed(body, stateOn(ribbon, 0.5 * (begins + ends), body),
                   None)
    self.buffers = (self._fixedBuffer(0, 0.0, -1.0),
                    self._fixedBuffer(0, self.track.length, 1.0),
                    self._fixedBuffer(1, siding.length, 1.0))
    self.addVehicle(Minecart(MINECART_AT, 0, False, None))
    powered = Minecart(siding.length - TRAIN_SHORT, 1, True, None)
    self.addVehicle(powered)
    self.addVehicle(Minecart(siding.length - TRAIN_SHORT - COUPLED, 1,
                             False, powered))
    self.pointsLever = FourthPeep(
      'points', None, (TOE - POINTS_BACK, POINTS_BESIDE,
                       DROP - ISLAND_UNDER), (0.0, 1.0, 0.0), POINTS_LONG,
      POINTS_NEAR, POINTS_FAR, ('Set the points for the siding',
                                'Set the points for the line'))
    self.addFourthPeep(self.pointsLever)
    self.addActor(self)

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
                     FRICTION, LIVE_EXCHANGE, self.device, self.tracks[1:],
                     (self.points,))

  def spawnPoint(self, ) -> tuple:
    """The 'spawnPoint' method returns where an avatar enters: on the
    island right of the line, before the points, looking along it."""
    return (WALKER_AT[0], WALKER_AT[1], DROP - ISLAND_UNDER), 0.0

  def fixtures(self, ) -> dict:
    """The 'fixtures' method returns the tracks' quads by look (the
    siding's drawn 'SIDING_UNDER' under the line's)."""
    out = trackQuads(self.track)
    for key, quads in trackQuads(self.tracks[1]).items():
      lowered = numpy.array(quads)
      lowered[:, :, 2] -= SIDING_UNDER
      out[key] = numpy.concatenate((out[key], lowered))
    return out

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method sets the points as their lever stands: for the
    siding once it is more than half way over."""
    self.points.thrown = self.pointsLever.value > 0.5

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

  def _fixedIsland(self, block: tuple) -> None:
    """Puts a block of the island in the world, 'block' (from x, to x,
    from y, to y, m): its grass on its dirt, its top 'ISLAND_UNDER'
    under the rails' top, held still, drawn."""
    x0, x1, y0, y1 = block
    top, long, wide = DROP - ISLAND_UNDER, x1 - x0, y1 - y0
    middle = (0.5 * (x0 + x1), 0.5 * (y0 + y1))
    self.fixed(Body.of(boxShape(long, wide, GRASS), EARTH),
               State((middle[0], middle[1], top - 0.5 * GRASS)), 'grass')
    self.fixed(Body.of(boxShape(long, wide, DIRT), EARTH),
               State((middle[0], middle[1], top - GRASS - 0.5 * DIRT)),
               'dirt')

  def _fixedBuffer(self, track: int, along: float, way: float) -> int:
    """Puts a buffer stop past an end of track 'track' at 'along' ('way':
    -1 its start, 1 its end) and returns its index: a beam across at the
    cart's ends' height ('BEAM_SPAN') and two posts under it, held still,
    drawn."""
    body = stopBody(way, BEAM_SPAN)
    return self.fixed(body, stateOn(self.tracks[track], along, body),
                      'buffer')
