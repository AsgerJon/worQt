"""
OvalWorld is the steam train's world (user, 2026-11-16: a steam
locomotive and "a bunch of cars being pulled by it"): a level oval of
main line ('_layout.ovalLine': two straights, two half circles of 400 m
eased in and out) on a field of grass, the train standing on its near
straight, the engine at its head; nothing else until spawned.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.phys._body import Body, State
from worQt.phys._compiled import gpuDevice
from worQt.phys._shape import boxShape
from worQt.phys._small_steps import THREADS, SmallSteps, preloaded
from worQt.phys.rail import RailWorld, wheelsetBody
from worQt.phys.rail._railrun import preloadedRails
from worQt.phys.rail._railworld import FRICTION
from worQt.phys.rail._stage import DIRT, EARTH, GRASS
from worQt.phys.rail._trackshape import trackQuads

from worQt.gaming.sandbox import EARTH_GRAVITY, World

from ._coach import COACH_HALF, GAP, Coach
from ._layout import OVAL_RADIUS, OVAL_STRAIGHT, ovalLine
from ._locomotive import BOGIE_WHEEL, DRIVER, TENDER_AT, TENDER_TAIL
from ._locomotive import TENDER_WHEEL, TRAILING_WHEEL, Locomotive
from ._loopworld import LIVE_EXCHANGE, LIVE_STEP, LOOP_STEP

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import Universe

#  The field the oval lies on: this far past the oval's ends and sides,
#  m; its grass's top at nought.
FIELD_MARGIN = 60.0
#  Where the engine's main axle stands, m along the oval (on its near
#  straight, which runs from 150 m before its start to 150 after); how
#  many coaches follow it.
ENGINE_AT, COACHES = 135.0, 3
#  Where an avatar enters: on the grass by the cab's left side, level
#  with the seat (within the avatar's reach of it: E boards), m back
#  from the main axle and out from the track's middle.
WALKER_BACK, WALKER_OUT = 4.6, 2.6
#  Fallen below this, m, a body has left the world.
OVAL_LOWEST = -20.0


class OvalWorld(World):
  """
  OvalWorld is the steam train's world: its track ('track', the oval,
  closed: its only one in 'tracks'; drawn, not solid: the ground holds
  what walks) on a field of grass on dirt (two bodies held still), the
  'Locomotive' on its near straight and 'COACHES' coaches coupled behind
  its tender (its 'vehicles', the engine first). Its physics is the
  small steps on the GPU where there is one, the wheelsets rolled by
  the rail world (wheels of every size the train has). The rail world
  knows only the earth's gravity, so another universe is refused.
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
           'coach': ((110, 30, 32), 0.1, 0.5)}
  lowest = OVAL_LOWEST

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, universe: Universe) -> None:
    if universe.gravity != EARTH_GRAVITY:
      raise NotImplementedError('the rail world knows only the earth\'s '
                                'gravity, not %r m/s²' % universe.gravity)
    World.__init__(self, universe, None)
    self.track, self.device = ovalLine(), gpuDevice() or 'cpu'
    self.tracks = (self.track,)
    long = OVAL_STRAIGHT + 2.0 * OVAL_RADIUS + 2.0 * FIELD_MARGIN + 40.0
    wide = 2.0 * OVAL_RADIUS + 2.0 * FIELD_MARGIN + 20.0
    self.fixed(Body.of(boxShape(long, wide, GRASS), EARTH),
               State((0.0, 0.0, -0.5 * GRASS)), 'grass')
    self.fixed(Body.of(boxShape(long, wide, DIRT), EARTH),
               State((0.0, 0.0, -GRASS - 0.5 * DIRT)), 'dirt')
    engine = Locomotive(ENGINE_AT, 0)
    self.addVehicle(engine)
    ahead, coaches = engine, []
    middle = ENGINE_AT + TENDER_AT + TENDER_TAIL[0] - GAP - COACH_HALF
    for _ in range(COACHES):
      coach = Coach(middle, 0, ahead)
      self.addVehicle(coach)
      coaches.append(coach)
      ahead, middle = coach, middle - 2.0 * COACH_HALF - GAP
    engine.train = tuple(coaches)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solverOf(self, ) -> object:
    """The 'solverOf' method returns the small steps on the world's
    device, its wheelsets (of every size the train has) handed to the
    rail world, stepped and traded as the loop's world's are."""
    inner = SmallSteps(self.universe.gravityVector(), None, LOOP_STEP, 1,
                       0.0, self.device, THREADS, False)
    wheels = tuple(wheelsetBody(radius) for radius in (
      DRIVER, BOGIE_WHEEL, TRAILING_WHEEL, TENDER_WHEEL)) + (
      wheelsetBody(),)
    return RailWorld(inner, self.track, wheels, LIVE_STEP, FRICTION,
                     LIVE_EXCHANGE, self.device)

  def spawnPoint(self, ) -> tuple:
    """The 'spawnPoint' method returns where an avatar enters: on the
    grass beside the engine's cab, looking along the track."""
    place, frame = self.track.frameAt(ENGINE_AT - WALKER_BACK)
    at = place + WALKER_OUT * frame[:, 1]
    return (float(at[0]), float(at[1]), 0.0), 0.0

  def fixtures(self, ) -> dict:
    """The 'fixtures' method returns the oval's quads by look."""
    return trackQuads(self.track)

  def readied(self, ) -> None:
    """The 'readied' method loads (or compiles) the small steps' and the
    rail's kernels for the world's device, saying so in 'loading'."""
    self.loading = self.device
    try:
      preloaded(self.device)
      preloadedRails(self.device)
    finally:
      self.loading = None
