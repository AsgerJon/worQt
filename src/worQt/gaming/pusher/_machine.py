"""
Machine is a coin pusher running, honest, and the player's purse: coins
dropped down a chute, pushed off the shelf onto the table and off the
table into the tray, back to the purse.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._cabinet import Cabinet, PUSHER, SHELF_EDGE, TRAY as TRAY_BOX
from ._coin_world import CoinWorld

#  Where a coin is: in the purse, on the machine (either level, or in a
#  chute), or in the tray; or out of the game: one of the house's that
#  spilled over the edge as the machine was filled
PURSE, MACHINE, TRAY, AWAY = 0, 1, 2, -1


class Machine(BaseObject):
  """
  Machine is a two-level coin pusher, its 'cabinet', running, and the
  player's purse of 'purse' coins. It starts empty, the pusher running;
  'pour' has the house fill it as the frames go, 'filling' meanwhile:
  coins poured in two streams, a big heap on the shelf and one on the
  table, turned every which way; a moment to settle, then 'countdown'
  runs down four seconds, the machine running. Coins of the house
  spilled over the edge meanwhile are out of the game, 'AWAY'. Then the
  game is on, 'started'; 'fill' pours and plays until it is. Each
  frame's 'hits' say how many coins met hard and how hard, to be
  heard; 'wonNow' how many fell into the tray.

  'drop' sends a coin from the purse down the chute on the left (-1) or
  the right (1), if there is one and the chute is clear. 'frame' plays
  1/60 s: the pusher moves, the coins with it. A coin past the front
  edge and below the table is in the tray: 'won' counts them. Once a
  coin in the tray has lain still a while it goes back to the purse.
  The side walls let nothing by, so every coin is always in the purse,
  on the machine or in the tray, and 'total' never changes: the machine
  keeps nothing.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_purse__ = 60  # coins the player starts with
  __fallback_kept__ = 1.5  # s a coin lies still in the tray before kept
  __fallback_still__ = 5.0  # mm/s a coin moves at most, lying still
  __fallback_fill__ = 170  # coins the house pours in, filling the machine
  __fallback_shelf__ = 60  # of them, poured onto the shelf
  __fallback_stream__ = 2.0 / 60.0  # s between two coins of a pile
  __fallback_settle__ = 1.0  # s the heaps settle once poured
  __fallback_countdown__ = 4.0  # s counted down before play

  #  Private Variables
  __machine_cabinet__: Cabinet | None = None
  __machine_world__: CoinWorld | None = None
  __coin_where__: numpy.ndarray | None = None
  __coin_still__: numpy.ndarray | None = None
  __machine_time__: float = 0.0
  __machine_won__: int = 0
  __machine_dropped__: int = 0
  __machine_rng__: numpy.random.Generator | None = None
  __machine_fill__: int = 0
  __pour_queue__: list | None = None
  __pour_end__: float | None = None
  __machine_started__: bool = False
  __won_now__: int = 0

  #  Virtual Variables
  cabinet: Field[Cabinet] = Field()
  world: Field[CoinWorld] = Field()
  time: Field[float] = Field()
  purse: Field[int] = Field()
  onMachine: Field[int] = Field()
  inTray: Field[int] = Field()
  won: Field[int] = Field()
  dropped: Field[int] = Field()
  total: Field[int] = Field()
  where: Field[numpy.ndarray] = Field()
  filling: Field[bool] = Field()
  started: Field[bool] = Field()
  countdown: Field[float] = Field()
  hits: Field[tuple] = Field()
  wonNow: Field[int] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cabinet.GET
  def _getCabinet(self, ) -> Cabinet:
    """The 'cabinet' getter returns the machine's shape."""
    return self.__machine_cabinet__

  @world.GET
  def _getWorld(self, ) -> CoinWorld:
    """The 'world' getter returns the coins as they move."""
    return self.__machine_world__

  @time.GET
  def _getTime(self, ) -> float:
    """The 'time' getter returns how long the machine has run, in s."""
    return self.__machine_time__

  @purse.GET
  def _getPurse(self, ) -> int:
    """The 'purse' getter returns how many coins the player has."""
    return int((self.__coin_where__ == PURSE).sum())

  @onMachine.GET
  def _getOnMachine(self, ) -> int:
    """The 'onMachine' getter returns how many coins are on the machine,
    either level or in a chute."""
    return int((self.__coin_where__ == MACHINE).sum())

  @inTray.GET
  def _getInTray(self, ) -> int:
    """The 'inTray' getter returns how many coins lie in the tray."""
    return int((self.__coin_where__ == TRAY).sum())

  @won.GET
  def _getWon(self, ) -> int:
    """The 'won' getter returns how many coins have fallen into the
    tray."""
    return self.__machine_won__

  @dropped.GET
  def _getDropped(self, ) -> int:
    """The 'dropped' getter returns how many coins the player has
    dropped in."""
    return self.__machine_dropped__

  @total.GET
  def _getTotal(self, ) -> int:
    """The 'total' getter returns every coin there is: the purse, the
    machine and the tray together, never changing."""
    return self.purse + self.onMachine + self.inTray

  @filling.GET
  def _getFilling(self, ) -> bool:
    """The 'filling' getter tells whether the house is pouring the coins
    in."""
    return self.__pour_end__ is not None

  @countdown.GET
  def _getCountdown(self, ) -> float:
    """The 'countdown' getter returns how long until the game is on, in
    s, once the coins are poured and lie; nought while pouring, and
    before and after."""
    end = self.__pour_end__
    if end is None or self.__pour_queue__:
      return 0.0
    left = end - self.__machine_time__
    return left if left <= self.__fallback_countdown__ else 0.0

  @hits.GET
  def _getHits(self, ) -> tuple:
    """The 'hits' getter returns the last frame's hits, to be heard:
    coin on coin, coin on the cabinet and coin into the tray, each how
    many and how hard the hardest, in mm/s."""
    return self.__machine_world__.hits

  @wonNow.GET
  def _getWonNow(self, ) -> int:
    """The 'wonNow' getter returns how many coins fell into the tray in
    the last frame."""
    return self.__won_now__

  @started.GET
  def _getStarted(self, ) -> bool:
    """The 'started' getter tells whether the game is on: the machine
    filled, the chutes open."""
    return self.__machine_started__

  @where.GET
  def _getWhere(self, ) -> numpy.ndarray:
    """The 'where' getter returns, for each coin, whether it is in the
    purse, on the machine or in the tray ('PURSE', 'MACHINE', 'TRAY'),
    or out of the game ('AWAY')."""
    return self.__coin_where__.copy()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Cabinet, int, int)
  def __init__(self, cabinet: Cabinet, purse: int, seed: int) -> None:
    self.__machine_cabinet__ = cabinet
    self.__machine_rng__ = numpy.random.default_rng(seed)
    fill = self.__fallback_fill__
    count = fill + purse
    world = CoinWorld(cabinet.coin, count, cabinet.boxes(), cabinet.edges())
    world.countApart(TRAY_BOX)
    self.__machine_world__ = world
    self.__coin_where__ = numpy.full(count, PURSE)
    self.__coin_where__[:fill] = AWAY
    self.__coin_still__ = numpy.zeros(count)
    self.__machine_fill__ = fill

  @overload(Cabinet, int)
  def __init__(self, cabinet: Cabinet, purse: int) -> None:
    self.__init__(cabinet, purse, 1)

  @overload()
  def __init__(self, ) -> None:
    self.__init__(Cabinet(), self.__fallback_purse__, 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def drop(self, side: int) -> bool:
    """The 'drop' method sends a coin from the purse down the chute on
    'side', -1 left or 1 right, and tells whether one went: not before
    the game is on, nor if the purse is empty, nor while the last coin
    is still on that ramp. It
    starts lying on the ramp near its upper end, a hair off the middle,
    turned any way about its axis."""
    free = numpy.nonzero(self.__coin_where__ == PURSE)[0]
    if not self.__machine_started__:
      return False
    if not len(free) or not self.chuteClear(side):
      return False
    cabinet, rng = self.__machine_cabinet__, self.__machine_rng__
    index = int(free[0])
    x, y, z = cabinet.rampStart(side)
    at = (x, y + rng.uniform(-1.0, 1.0), z)
    spin = rng.uniform(0.0, 2.0 * math.pi)
    turn = _product(cabinet.rampTurn(side),
                    (0.0, 0.0, math.sin(spin / 2.0), math.cos(spin / 2.0)))
    nothing = (0.0, 0.0, 0.0)
    self.__machine_world__.place(index, at, turn, nothing, nothing)
    self.__coin_where__[index] = MACHINE
    self.__coin_still__[index] = 0.0
    self.__machine_dropped__ += 1
    return True

  def chuteClear(self, side: int) -> bool:
    """The 'chuteClear' method tells whether no coin is on the ramp of the
    chute on 'side', nor just off its end."""
    cabinet = self.__machine_cabinet__
    places = self.__machine_world__.places
    onMachine = self.__coin_where__ == MACHINE
    _, (x1, z1), _ = cabinet.rampLine(side)
    across = numpy.abs(places[:, 1] - cabinet.chuteY())
    near = across < cabinet.chuteWidth() / 2.0
    high = places[:, 2] > z1 - cabinet.coin.radius
    out = -side * places[:, 0] > abs(x1) - cabinet.coin.radius
    return not bool(numpy.any(onMachine & near & high & out))

  def frame(self, ) -> None:
    """The 'frame' method plays 1/60 s: the pusher moves, the coins with
    it; coins come to the tray, and those still there a while go back
    to the purse. While the house pours, each coin falls in when due."""
    cabinet, world = self.__machine_cabinet__, self.__machine_world__
    now = self.__machine_time__
    box = cabinet.pusherAt(now)
    speed = (0.0, cabinet.speedAt(now), 0.0)
    world.moveBox(PUSHER, box.centre, speed)
    face = cabinet.faceAt(now)
    half = cabinet.width / 2.0
    world.moveEdge(SHELF_EDGE, (-half, face, cabinet.shelf - 0.05),
                   (half, face, cabinet.shelf - 0.05), speed)
    queue = self.__pour_queue__
    while queue and queue[0][0] <= now:
      _, index, spot = queue.pop(0)
      self._poured(index, spot)
    world.frame()
    self.__machine_time__ = world.time
    self._sorted()
    if self.__pour_end__ is not None and world.time >= self.__pour_end__:
      self._begun()

  def played(self, seconds: float) -> None:
    """The 'played' method plays frames for 'seconds'."""
    for _ in range(round(seconds * 60.0)):
      self.frame()

  def pour(self, ) -> None:
    """The 'pour' method has the house fill the machine, from now, the
    pusher running: its coins poured in two streams, one onto the shelf
    and one onto the table, each coin falling from above the heap it
    builds, turned any way, so two big heaps grow and slide; the heaps
    settle a moment, a countdown runs, 'countdown', and then the game is
    on. Coins of the house that spill over the edge meanwhile are out of
    the game; the purse stays as it was, and nothing is counted won or
    dropped."""
    if self.filling or self.__machine_started__:
      return
    cabinet = self.__machine_cabinet__
    fill, shelf = self.__machine_fill__, self.__fallback_shelf__
    every = self.__fallback_stream__
    now = self.__machine_time__
    table = (0.0, (cabinet.retracted + cabinet.stroke + cabinet.front) / 2.0)
    upper = (0.0, cabinet.retracted / 2.0)
    queue = []
    for k in range(shelf):
      queue.append((now + k * every, k, upper))
    for k in range(fill - shelf):
      queue.append((now + 0.5 * every + k * every, shelf + k, table))
    queue.sort()
    self.__pour_queue__ = queue
    poured = queue[-1][0] if queue else now
    self.__pour_end__ = (poured + self.__fallback_settle__ +
                         self.__fallback_countdown__)

  def fill(self, ) -> None:
    """The 'fill' method pours the coins in and plays on until the game
    is on."""
    self.pour()
    while self.filling:
      self.frame()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _sorted(self, ) -> None:
    """Coins over the front edge and below the table are in the tray;
    those lying still in it long enough go back to the purse."""
    cabinet, world = self.__machine_cabinet__, self.__machine_world__
    places, speeds = world.places, world.speeds
    where, still = self.__coin_where__, self.__coin_still__
    fallen = (where == MACHINE) & (places[:, 1] > cabinet.front)
    fallen &= places[:, 2] < -cabinet.coin.radius
    self.__won_now__ = int(fallen.sum())
    self.__machine_won__ += self.__won_now__
    where[fallen] = TRAY
    tray = where == TRAY
    resting = tray & (speeds < self.__fallback_still__)
    still[resting] += 1.0 / 60.0
    still[tray & ~resting] = 0.0
    kept = AWAY if self.filling else PURSE
    for index in numpy.nonzero(still > self.__fallback_kept__)[0]:
      world.park(int(index))
      where[index] = kept
      still[index] = 0.0

  def _poured(self, index: int, spot: tuple[float, float]) -> None:
    """Pours coin 'index' onto the heap at 'spot': from 6 cm over the
    top of the coins lying there, a little off its middle, turned any
    way, spinning and falling fast."""
    cabinet, world = self.__machine_cabinet__, self.__machine_world__
    rng = self.__machine_rng__
    radius = cabinet.coin.radius
    playing = world.playing & (world.speeds < 200.0)
    places = world.places
    near = numpy.hypot(places[:, 0] - spot[0], places[:, 1] - spot[1])
    under = playing & (near < 2.0 * radius)
    top = float(places[under][:, 2].max()) if under.any() else 0.0
    top = max(top, cabinet.shelf if spot[1] < cabinet.retracted else 0.0)
    reach = 18.0 * math.sqrt(rng.random())
    angle = rng.uniform(0.0, 2.0 * math.pi)
    at = (spot[0] + reach * math.cos(angle),
          spot[1] + reach * math.sin(angle), top + 60.0)
    spin = tuple(rng.uniform(-8.0, 8.0, 3))
    world.place(index, at, _anyTurn(rng), (0.0, 0.0, -900.0), spin)
    self.__coin_where__[index] = MACHINE

  def _begun(self, ) -> None:
    """Ends the pour and the countdown: the house's coins not on the
    machine are out of the game, nothing is counted won or dropped, and
    the game is on."""
    world, where = self.__machine_world__, self.__coin_where__
    for index in range(self.__machine_fill__):
      if where[index] != MACHINE:
        world.park(index)
        where[index] = AWAY
    self.__coin_still__[:] = 0.0
    self.__machine_won__ = 0
    self.__machine_dropped__ = 0
    self.__pour_queue__ = None
    self.__pour_end__ = None
    self.__machine_started__ = True


def _anyTurn(rng: numpy.random.Generator) -> tuple[float, float, float,
                                                   float]:
  """A turn drawn evenly from all turns (Shoemake), x y z w."""
  u1, u2, u3 = rng.random(3)
  a, b = math.sqrt(1.0 - u1), math.sqrt(u1)
  return (a * math.sin(2.0 * math.pi * u2), a * math.cos(2.0 * math.pi * u2),
          b * math.sin(2.0 * math.pi * u3), b * math.cos(2.0 * math.pi * u3))


def _product(a: tuple, b: tuple) -> tuple[float, float, float, float]:
  """The turn 'b' and then 'a', as the quaternion product of the two,
  each x y z w."""
  ax, ay, az, aw = a
  bx, by, bz, bw = b
  return (aw * bx + ax * bw + ay * bz - az * by,
          aw * by - ax * bz + ay * bw + az * bx,
          aw * bz + ax * by - ay * bx + az * bw,
          aw * bw - ax * bx - ay * by - az * bz)
