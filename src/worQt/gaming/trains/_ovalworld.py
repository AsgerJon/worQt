"""
OvalWorld is the steam train's world (user, 2026-11-16: a steam
locomotive and "a bunch of cars being pulled by it"; then "make trains
have collision and all that": solid track, buffers and couplings, cars
meeting cars, something to run into): a level oval of main line
('_layout.ovalLine': two straights, two half circles of 400 m eased in
and out) on a field of grass, solid; at the end of its near straight a
set of points, a siding going straight on to a buffer stop, three loose
coaches standing on it; the train on the near straight before the
points, the engine at its head; the points' lever beside the line.
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
from worQt.phys.rail import RailWorld, Turnout, wheelsetBody
from worQt.phys.rail._railrun import preloadedRails
from worQt.phys.rail._railworld import FRICTION
from worQt.phys.rail._stage import DIRT, EARTH, GRASS
from worQt.phys.rail._trackshape import trackQuads

from worQt.gaming.sandbox import EARTH_GRAVITY, World
from worQt.gaming.sandbox._fourthpeep import FourthPeep

from ._coach import COACH_LONG, Coach
from ._coupling import BUFFER_UP, CarEnd, buffered
from ._layout import OVAL_RADIUS, OVAL_STRAIGHT, OVAL_TOE
from ._layout import ovalLine, ovalSiding
from ._locomotive import BOGIE_WHEEL, DRIVER, TENDER_AT, TENDER_HEAD
from ._locomotive import TENDER_WHEEL, TRAILING_WHEEL, Locomotive
from ._loopworld import LIVE_EXCHANGE, LIVE_STEP, LOOP_STEP, SIDING_UNDER
from ._solidtrack import chunkBody, chunksOf, stateOn, stopBody

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import Universe

#  The field the oval lies on: this far past the oval's ends and sides,
#  m; its grass's top at nought.
FIELD_MARGIN = 60.0
#  The oval's track is solid in straight pieces within 'OVAL_SAG' m of
#  its curves (~10 m long on them: some 350 pieces in all).
OVAL_SAG = 0.03
#  Where the engine's main axle stands, m along the oval (on its near
#  straight, which runs from 150 m before its start to 150 after: the
#  points 15 m ahead); how many coaches follow it.
ENGINE_AT, COACHES = 135.0, 3
#  The loose coaches on the siding: how many, the first's middle m along
#  it (clear of the oval: the two part 6 m apart 100 m on), the others
#  behind it buffer to buffer; the buffer stop's beam at the buffers'
#  height (its bottom and top, m over the rails).
LOOSE, LOOSE_AT = 3, 200.0
STOP_SPAN = (BUFFER_UP - 0.3, BUFFER_UP + 0.3)
#  The points' lever: this far before the points, m, this far to the
#  left of the line (the side the avatar enters on), its handle long, m,
#  turning about the line's across from leaning back (set for the oval)
#  to leaning ahead (for the siding), rad.
POINTS_BACK, POINTS_BESIDE = 12.0, 3.2
POINTS_LONG, POINTS_NEAR, POINTS_FAR = 0.8, -0.4, 0.4
#  Where an avatar enters: on the grass by the cab's left side, level
#  with the seat (within the avatar's reach of it: E boards), m back
#  from the main axle and out from the track's middle.
WALKER_BACK, WALKER_OUT = 4.6, 2.6
#  Fallen below this, m, a body has left the world.
OVAL_LOWEST = -20.0


class OvalWorld(World):
  """
  OvalWorld is the steam train's world: its 'tracks' (the oval, closed:
  'track'; the siding off its 'points', a 'Turnout' set by its lever
  'pointsLever'), drawn and solid (a body held still every ~10 m along
  them: '_solidtrack'), on a field of grass on dirt (two bodies held
  still), a buffer stop past the siding's end ('stop'); the 'Locomotive'
  on the near straight and 'COACHES' coaches coupled behind its tender
  (its 'train'), 'LOOSE' coaches standing loose on the siding ('loose'),
  buffer to buffer; buffers between every car's front and every other
  car's back and the stop ('buffers'). Its 'cars' are every car body
  (index, vehicle): any two not coupled meet as bodies too. Its physics
  is the small steps on the GPU where there is one, the wheelsets rolled
  by the rail world (wheels of every size the train has). The rail
  world knows only the earth's gravity, so another universe is refused.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  LOOKS = {'rail': ((148, 150, 154), 0.3, 0.35),
           'wheel': ((60, 62, 66), 0.3, 0.4),
           'sleeper': ((168, 166, 158), 0.0, 0.8),
           'grass': ((86, 128, 54), 0.0, 0.95),
           'dirt': ((112, 84, 58), 0.0, 1.0),
           'engine': ((22, 70, 44), 0.2, 0.35),
           'black': ((32, 32, 34), 0.1, 0.6),
           'rod': ((150, 152, 158), 0.5, 0.3),
           'tender': ((22, 70, 44), 0.2, 0.35),
           'coach': ((110, 30, 32), 0.1, 0.5),
           'loose': ((28, 92, 104), 0.1, 0.5),
           'stop': ((196, 48, 40), 0.2, 0.5)}
  lowest = OVAL_LOWEST

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, universe: Universe) -> None:
    if universe.gravity != EARTH_GRAVITY:
      raise NotImplementedError('the rail world knows only the earth\'s '
                                'gravity, not %r m/s²' % universe.gravity)
    World.__init__(self, universe, None)
    self.tracks = (ovalLine(), ovalSiding())
    self.track, self.device = self.tracks[0], gpuDevice() or 'cpu'
    self.points = Turnout(0, OVAL_TOE, 1)
    self.cars = []
    long = OVAL_STRAIGHT + 2.0 * OVAL_RADIUS + 2.0 * FIELD_MARGIN + 40.0
    wide = 2.0 * OVAL_RADIUS + 2.0 * FIELD_MARGIN + 20.0
    self.fixed(Body.of(boxShape(long, wide, GRASS), EARTH),
               State((0.0, 0.0, -0.5 * GRASS)), 'grass')
    self.fixed(Body.of(boxShape(long, wide, DIRT), EARTH),
               State((0.0, 0.0, -GRASS - 0.5 * DIRT)), 'dirt')
    for ribbon in self.tracks:
      for begins, ends in chunksOf(ribbon, OVAL_SAG):
        body = chunkBody(begins, ends)
        self.fixed(body, stateOn(ribbon, 0.5 * (begins + ends), body),
                   None)
    siding = self.tracks[1]
    body = stopBody(1.0, STOP_SPAN)
    self.stop = self.fixed(body, stateOn(siding, siding.length, body),
                           'stop')
    engine = Locomotive(ENGINE_AT, 0)
    self.addVehicle(engine)
    ahead, coaches = engine, []
    middle = ENGINE_AT + TENDER_AT + TENDER_HEAD - 0.5 * COACH_LONG
    for k in range(COACHES):
      coach = Coach(middle, 0, ahead, 'coach', k)
      self.addVehicle(coach)
      coaches.append(coach)
      ahead, middle = coach, middle - COACH_LONG
    engine.train = tuple(coaches)
    self.loose = tuple(Coach(LOOSE_AT - k * COACH_LONG, 1, None, 'loose',
                             COACHES + k) for k in range(LOOSE))
    for coach in self.loose:
      self.addVehicle(coach)
    ends = [CarEnd(self.stop, 0.0, -1.0, None)]
    for vehicle in self.vehicles:
      ends += [vehicle.front, vehicle.back]
    self.buffers = buffered(self, tuple(ends))
    place, frame = self.track.frameAt(OVAL_TOE - POINTS_BACK)
    pivot = place + POINTS_BESIDE * frame[:, 1]
    self.pointsLever = FourthPeep(
      'points', None, (float(pivot[0]), float(pivot[1]), 0.0),
      (0.0, 1.0, 0.0), POINTS_LONG, POINTS_NEAR, POINTS_FAR,
      ('Set the points for the siding', 'Set the points for the oval'))
    self.addFourthPeep(self.pointsLever)
    self.addActor(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solverOf(self, ) -> object:
    """The 'solverOf' method returns the small steps on the world's
    device, its wheelsets (of every size the train has) handed to the
    rail world on both tracks, stepped and traded as the loop's world's
    are."""
    inner = SmallSteps(self.universe.gravityVector(), None, LOOP_STEP, 1,
                       0.0, self.device, THREADS, False)
    wheels = tuple(wheelsetBody(radius) for radius in (
      DRIVER, BOGIE_WHEEL, TRAILING_WHEEL, TENDER_WHEEL)) + (
      wheelsetBody(),)
    return RailWorld(inner, self.track, wheels, LIVE_STEP, FRICTION,
                     LIVE_EXCHANGE, self.device, self.tracks[1:],
                     (self.points,))

  def spawnPoint(self, ) -> tuple:
    """The 'spawnPoint' method returns where an avatar enters: on the
    grass beside the engine's cab, looking along the track."""
    place, frame = self.track.frameAt(ENGINE_AT - WALKER_BACK)
    at = place + WALKER_OUT * frame[:, 1]
    return (float(at[0]), float(at[1]), 0.0), 0.0

  def fixtures(self, ) -> dict:
    """The 'fixtures' method returns the tracks' quads by look (the
    siding's drawn 'SIDING_UNDER' under the oval's)."""
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
    """The 'readied' method loads (or compiles) the small steps' and the
    rail's kernels for the world's device, saying so in 'loading'."""
    self.loading = self.device
    try:
      preloaded(self.device)
      preloadedRails(self.device)
    finally:
      self.loading = None
