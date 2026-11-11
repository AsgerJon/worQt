"""
CoinWorld is coins in 3D among the boxes and edges of a cabinet, played
a frame at a time by the kernels of '_coin_kernels', on the CPU.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

import numpy
import warp as wp
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._coin import Coin
from . import _coin_kernels as kernels

_DEVICE = 'cpu'
_GRAVITY = 9810.0  # mm/s²


class Box(NamedTuple):
  """A box of the cabinet: its 'centre' and its 'half' extents, in mm,
  along its own axes, turned by 'turn' (a quaternion, x y z w; square
  to the world's axes unless told otherwise)."""

  centre: tuple[float, float, float]
  half: tuple[float, float, float]
  turn: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)


class Edge(NamedTuple):
  """A sharp edge of the cabinet a coin's face may lie over, from
  'start' to 'end', in mm: the front of a shelf or of the table."""

  start: tuple[float, float, float]
  end: tuple[float, float, float]


def _vectors(rows: object, dtype: type) -> wp.array:
  """The rows as a Warp array of 'dtype' on the CPU."""
  data = numpy.asarray(rows, numpy.float32)
  return wp.array(data, dtype, None, None, None, None, _DEVICE)


def _zeros(count: int, dtype: type) -> wp.array:
  """A Warp array of 'count' noughts of 'dtype' on the CPU."""
  return wp.zeros(count, dtype, _DEVICE)


def _soft(hertz: float, damping: float, step: float) -> wp.vec3:
  """A soft contact's bias rate, mass scale and impulse scale, as Box2D
  v3 makes them."""
  omega = 2.0 * math.pi * hertz
  a1 = 2.0 * damping + step * omega
  a2 = step * omega * a1
  a3 = 1.0 / (1.0 + a2)
  return wp.vec3(omega / a1, a2 * a3, a3)


class CoinWorld(BaseObject):
  """
  CoinWorld is 'count' coins of one 'coin' among the cabinet's 'boxes'
  and 'edges', in mm, s and g, z up. A coin is in play once 'place'd
  and out again once 'park'ed; out of play it is nowhere. Each 'frame'
  plays 1/60 s: contacts are found as it begins, then solved over
  'substeps', soft and warm started; while any coin moves fast, the
  contacts are found anew each quarter of the frame (found once, a coin
  falling onto another and turning as it hit slipped through it).
  Boxes and edges may move, each at its velocity through a frame
  ('moveBox', 'moveEdge').

  'places' and 'turns' are the coins' middles and quaternions (x y z w)
  as arrays to read, not write; 'speeds' how fast each moves.
  'contacts' and 'deepest' tell how many contacts the last frame had
  and how far any two overlapped at most since 'deepest' was cleared;
  'hits' how many met hard in the last frame, and how hard, to be
  heard.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_frame__ = 1.0 / 60.0  # s a frame plays
  __fallback_substeps__ = 8  # substeps a frame
  __fallback_looks__ = 4  # times a frame contacts are looked for, ...
  __fallback_calm__ = 150.0  # ... while a coin's point moves this fast
  __fallback_damping__ = 5.0  # damping ratio of a soft contact
  __fallback_stiffness__ = 0.25  # a contact's frequency, of the substeps'
  __fallback_contacts__ = 64  # contacts kept at most, a coin

  #  Private Variables
  __world_coin__: Coin | None = None
  __world_rules__: kernels.Rules | None = None
  __world_bodies__: kernels.Bodies | None = None
  __world_parts__: kernels.Parts | None = None
  __world_now__: kernels.Contacts | None = None
  __world_last__: kernels.Contacts | None = None
  __world_cursor__: wp.array | None = None
  __world_stats__: wp.array | None = None
  __world_time__: float = 0.0

  #  Virtual Variables
  coin: Field[Coin] = Field()
  count: Field[int] = Field()
  time: Field[float] = Field()
  places: Field[numpy.ndarray] = Field()
  turns: Field[numpy.ndarray] = Field()
  speeds: Field[numpy.ndarray] = Field()
  playing: Field[numpy.ndarray] = Field()
  contacts: Field[int] = Field()
  deepest: Field[float] = Field()
  hits: Field[tuple] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @coin.GET
  def _getCoin(self, ) -> Coin:
    """The 'coin' getter returns the coin every coin here is."""
    return self.__world_coin__

  @count.GET
  def _getCount(self, ) -> int:
    """The 'count' getter returns how many coins there are, in play or
    not."""
    return self.__world_bodies__.count

  @time.GET
  def _getTime(self, ) -> float:
    """The 'time' getter returns how long has been played, in s."""
    return self.__world_time__

  @places.GET
  def _getPlaces(self, ) -> numpy.ndarray:
    """The 'places' getter returns the coins' middles, a row a coin."""
    return self.__world_bodies__.x.numpy()

  @turns.GET
  def _getTurns(self, ) -> numpy.ndarray:
    """The 'turns' getter returns how the coins are turned, a
    quaternion (x y z w) a row."""
    return self.__world_bodies__.q.numpy()

  @speeds.GET
  def _getSpeeds(self, ) -> numpy.ndarray:
    """The 'speeds' getter returns how fast each coin's middle moves."""
    return numpy.linalg.norm(self.__world_bodies__.v.numpy(), None, 1)

  @playing.GET
  def _getPlaying(self, ) -> numpy.ndarray:
    """The 'playing' getter returns, for each coin, whether it is in
    play."""
    return self.__world_bodies__.active.numpy() == 1

  @contacts.GET
  def _getContacts(self, ) -> int:
    """The 'contacts' getter returns how many contacts the last frame
    had."""
    return int(self.__world_stats__.numpy()[0])

  @hits.GET
  def _getHits(self, ) -> tuple:
    """The 'hits' getter returns the last frame's hits, contacts met at
    over 60 mm/s: coin on coin, coin on the cabinet, and coin on the box
    counted apart ('countApart'), each how many and how hard the hardest,
    in mm/s; six numbers."""
    return tuple(float(v) for v in self.__world_stats__.numpy()[2:8])

  @deepest.GET
  def _getDeepest(self, ) -> float:
    """The 'deepest' getter returns how far, in mm, any two overlapped
    at most since it was last cleared."""
    return float(self.__world_stats__.numpy()[1])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Coin, int, tuple, tuple)
  def __init__(self, coin: Coin, count: int, boxes: tuple,
               edges: tuple) -> None:
    wp.init()
    self.__world_coin__ = coin
    self.__world_rules__ = self._rulesFor(coin, count)
    self.__world_bodies__ = self._bodiesFor(count)
    self.__world_parts__ = self._partsFor(boxes, edges)
    self.__world_now__ = self._contactsFor(count)
    self.__world_last__ = self._contactsFor(count)
    self.__world_cursor__ = _zeros(1, int)
    self.__world_stats__ = _zeros(8, float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def place(self, index: int, at: tuple, turn: tuple, velocity: tuple,
            spin: tuple) -> None:
    """The 'place' method puts coin 'index' in play at 'at', turned by
    'turn' (x y z w), moving at 'velocity' and spinning at 'spin'
    (rad/s about the world's axes)."""
    bodies = self.__world_bodies__
    for array, value in ((bodies.x, at), (bodies.q, turn),
                         (bodies.v, velocity), (bodies.w, spin)):
      rows = array.numpy()
      rows[index] = value
    bodies.active.numpy()[index] = 1

  def park(self, index: int) -> None:
    """The 'park' method takes coin 'index' out of play."""
    bodies = self.__world_bodies__
    bodies.active.numpy()[index] = 0
    bodies.v.numpy()[index] = (0.0, 0.0, 0.0)
    bodies.w.numpy()[index] = (0.0, 0.0, 0.0)

  def moveBox(self, index: int, centre: tuple, velocity: tuple) -> None:
    """The 'moveBox' method puts box 'index' at 'centre' as the next
    frame begins, moving at 'velocity' through it."""
    parts = self.__world_parts__
    parts.boxCentre.numpy()[index] = centre
    parts.boxVelocity.numpy()[index] = velocity

  def moveEdge(self, index: int, start: tuple, end: tuple,
               velocity: tuple) -> None:
    """The 'moveEdge' method puts edge 'index' from 'start' to 'end' as
    the next frame begins, moving at 'velocity' through it."""
    parts = self.__world_parts__
    parts.edgeStart.numpy()[index] = start
    parts.edgeEnd.numpy()[index] = end
    parts.edgeVelocity.numpy()[index] = velocity

  def frame(self, ) -> None:
    """The 'frame' method plays a frame: the contacts are looked for and
    solved over the substeps; while a coin moves fast, four times, each
    over a quarter of them. Between looks, the moving boxes and edges
    move on as their velocities have them."""
    rules, bodies = self.__world_rules__, self.__world_bodies__
    parts, stats = self.__world_parts__, self.__world_stats__
    stats.numpy()[2:] = 0.0
    looks = self.__fallback_looks__ if self._hurried() else 1
    substeps = self.__fallback_substeps__ // looks
    span = self.__fallback_frame__ / looks
    rules.frame = span
    step = span / substeps
    hertz = self.__fallback_stiffness__ / step
    soft = _soft(hertz, self.__fallback_damping__, step)
    for look in range(looks):
      if look:
        self._movedOn(span)
      now, last = self.__world_last__, self.__world_now__
      self.__world_now__, self.__world_last__ = now, last
      parts.elapsed = 0.0
      wp.launch(kernels.collide, 1, [rules, bodies, now, last, parts,
                                     self.__world_cursor__], [], [], [],
                _DEVICE)
      for substep in range(substeps):
        parts.elapsed = (substep + 1) * step
        wp.launch(kernels.substep, 1, [rules, bodies, now, parts, step,
                                       soft, soft], [], [], [], _DEVICE)
      wp.launch(kernels.finish, 1, [rules, bodies, now, parts, stats], [],
                [], [], _DEVICE)
    self.__world_time__ += self.__fallback_frame__

  def played(self, seconds: float) -> None:
    """The 'played' method plays frames for 'seconds'."""
    for _ in range(round(seconds / self.__fallback_frame__)):
      self.frame()

  def _hurried(self, ) -> bool:
    """Tells whether any coin in play sweeps into new room faster than
    'calm' (its spin about its own axis left out): a coin falling or
    landing, which needs its contacts looked for again within the
    frame."""
    bodies = self.__world_bodies__
    playing = bodies.active.numpy() == 1
    if not playing.any():
      return False
    v = numpy.linalg.norm(bodies.v.numpy()[playing], None, 1)
    q = bodies.q.numpy()[playing]
    x, y, z, s = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    axes = numpy.stack((2.0 * (x * z + s * y), 2.0 * (y * z - s * x),
                        1.0 - 2.0 * (x * x + y * y)), 1)
    spin = bodies.w.numpy()[playing]
    tumble = spin - axes * (spin * axes).sum(1)[:, None]
    w = numpy.linalg.norm(tumble, None, 1)
    quickest = float((v + self.__world_coin__.radius * w).max())
    return quickest > self.__fallback_calm__

  def _movedOn(self, seconds: float) -> None:
    """Moves the boxes and edges on by their velocities for 'seconds'."""
    parts = self.__world_parts__
    centres = parts.boxCentre.numpy()
    centres += parts.boxVelocity.numpy() * seconds
    for ends in (parts.edgeStart.numpy(), parts.edgeEnd.numpy()):
      ends += parts.edgeVelocity.numpy() * seconds

  def countApart(self, index: int) -> None:
    """The 'countApart' method has the hits on box 'index' counted apart
    in 'hits': the tray, a coin landing in it heard as won."""
    self.__world_parts__.apart = index

  def clearDeepest(self, ) -> None:
    """The 'clearDeepest' method starts 'deepest' over at nought."""
    self.__world_stats__.numpy()[1] = 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _rulesFor(self, coin: Coin, count: int) -> kernels.Rules:
    """The numbers the kernels keep to, for 'count' of 'coin'."""
    across, along = coin.inertia()
    rules = kernels.Rules()
    rules.radius = coin.radius
    rules.half = coin.half
    rules.invMass = 1.0 / coin.mass
    rules.inertia = wp.vec3(across, across, along)
    rules.invInertia = wp.vec3(1.0 / across, 1.0 / across, 1.0 / along)
    rules.gravity = _GRAVITY
    rules.muCoin = 0.3
    rules.muCabinet = 0.25
    rules.bounce = 0.2
    rules.bounceFrom = 150.0
    rules.hitFrom = 60.0
    rules.spec = 1.0
    rules.inset = 0.8
    rules.flat = 0.9
    rules.push = 300.0
    rules.frame = self.__fallback_frame__
    rules.edgeStep = 2.0
    rules.kCoin = 16
    rules.kBox = 8
    rules.capacity = max(1, count) * self.__fallback_contacts__
    return rules

  @staticmethod
  def _bodiesFor(count: int) -> kernels.Bodies:
    """'count' coins, none in play, unturned."""
    bodies = kernels.Bodies()
    bodies.x = _zeros(count, wp.vec3)
    bodies.q = _vectors(numpy.tile((0.0, 0.0, 0.0, 1.0), (count, 1)),
                        wp.quat)
    bodies.v = _zeros(count, wp.vec3)
    bodies.w = _zeros(count, wp.vec3)
    bodies.x0 = _zeros(count, wp.vec3)
    bodies.q0 = _zeros(count, wp.quat)
    bodies.active = _zeros(count, int)
    bodies.count = count
    return bodies

  @staticmethod
  def _partsFor(boxes: tuple, edges: tuple) -> kernels.Parts:
    """The cabinet of 'boxes' and 'edges', all standing still."""
    parts = kernels.Parts()
    boxRows = [box.centre for box in boxes] or [(0.0, 0.0, -1.0e6)]
    halfRows = [box.half for box in boxes] or [(0.0, 0.0, 0.0)]
    parts.boxCentre = _vectors(boxRows, wp.vec3)
    parts.boxHalf = _vectors(halfRows, wp.vec3)
    turns = [box.turn for box in boxes] or [(0.0, 0.0, 0.0, 1.0)]
    parts.boxTurn = _vectors(turns, wp.quat)
    parts.boxVelocity = _zeros(len(boxRows), wp.vec3)
    parts.boxes = len(boxes)
    starts = [edge.start for edge in edges] or [(0.0, 0.0, -1.0e6)]
    ends = [edge.end for edge in edges] or [(1.0, 0.0, -1.0e6)]
    parts.edgeStart = _vectors(starts, wp.vec3)
    parts.edgeEnd = _vectors(ends, wp.vec3)
    parts.edgeVelocity = _zeros(len(starts), wp.vec3)
    parts.edges = len(edges)
    parts.elapsed = 0.0
    parts.apart = -1
    return parts

  def _contactsFor(self, count: int) -> kernels.Contacts:
    """Room for the contacts of 'count' coins."""
    room = max(1, count) * self.__fallback_contacts__
    contacts = kernels.Contacts()
    contacts.key = _zeros(room, wp.int64)
    for name in ('i', 'j', 'part', 'kind'):
      setattr(contacts, name, _zeros(room, int))
    for name in ('n', 't1', 't2', 'ra', 'rb', 'lt'):
      setattr(contacts, name, _zeros(room, wp.vec3))
    for name in ('mn', 'm1', 'm2', 'mu', 'ln', 'l1', 'l2', 'vn0', 'top'):
      setattr(contacts, name, _zeros(room, float))
    contacts.count = _zeros(1, int)
    return contacts
