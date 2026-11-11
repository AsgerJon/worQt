"""
Analysis is a frame reckoned: its reactions, its section forces along
each member, and how it bends.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from .._doubles import doubles
from ._frame import Frame
from ._parts import LineLoad, PointLoad, PointMoment

_NEAR = 1e-9  # m: stations nearer than this are one
_PIECE = 1e-3  # m: a piece is at least this long, else too stiff to solve
_PIECES = 8  # a member is cut in at least so many pieces, for its shape
_SAMPLES = 24  # values a diagram takes between two stations
_KINDS = ('N', 'V', 'M')


def _simpson(f: callable, a: float, b: float) -> float:
  """The integral of 'f' from 'a' to 'b', exact for a quadratic."""
  return (b - a) / 6 * (f(a) + 4 * f((a + b) / 2) + f(b))


def _roots(values: tuple[float, float, float], a: float,
           b: float) -> list[float]:
  """Where the quadratic through 'values' at 'a', the middle and 'b'
  is nought, strictly between them."""
  y0, y1, y2 = values
  h = (b - a) / 2
  c2 = (y0 - 2 * y1 + y2) / (2 * h * h)
  c1 = (y2 - y0) / (2 * h)
  c0 = y1
  if abs(c2) < 1e-12 * max(abs(c1), abs(c0), 1.0):
    found = [] if abs(c1) < 1e-300 else [-c0 / c1]
  else:
    disc = c1 * c1 - 4 * c2 * c0
    if disc < 0:
      return []
    root = math.sqrt(disc)
    found = [(-c1 - root) / (2 * c2), (-c1 + root) / (2 * c2)]
  middle = (a + b) / 2
  return sorted(middle + u for u in found if -h + 1e-9 < u < h - 1e-9)


class Analysis(BaseObject):
  """
  Analysis is a 'frame' reckoned by the stiffness method, exactly for
  its point loads, its line loads, straight or sloping, and its moments:
  each member cut at its loads into pieces whose ends move as the
  frame's nodes do, each piece stiff along it, EA, and in bending, EI,
  but at a hinge, a line load on it taken as the loads at its ends that
  do the same work. 'held' is why the frame is not held, or nothing if
  it is: a frame not held moves without bending, and has no forces to
  show.

  'reactions' are what each support pushes with, along x and y in kN,
  up and right positive, and its moment in kNm, anticlockwise. Along
  each member, from its first node, 'normal', 'shear' and 'moment' are
  the section forces at 's', just past it: N, tension positive; V, the
  forces on the part before the section, across it to the left as the
  member runs; M, positive when it pulls the right side as the member
  runs, as a beam run left to right sags, drawn on that side, the side
  it pulls. 'diagram' gives one of them along a member, twice where it
  jumps; 'marks' where its values are worth writing: the ends, the
  jumps and the moment's peaks, where the shear is nought; 'most' the
  greatest anywhere. 'shape' is the member as it bends, displaced.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __analysis_frame__: Frame | None = None
  __analysis_held__: str = ''
  __analysis_stations__: list | None = None
  __analysis_ends__: list | None = None
  __analysis_reactions__: tuple | None = None
  __analysis_moves__: torch.Tensor | None = None
  __analysis_turns__: dict | None = None
  __analysis_places__: list | None = None
  __analysis_kept__: dict | None = None

  #  Virtual Variables
  frame: Field[Frame] = Field()
  held: Field[str] = Field()
  reactions: Field[tuple[tuple[float, float, float], ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @frame.GET
  def _getFrame(self, ) -> Frame:
    """The 'frame' getter returns the frame reckoned."""
    if self.__analysis_frame__ is None:
      raise MissingVariable(self, '__analysis_frame__', Frame)
    return self.__analysis_frame__

  @held.GET
  def _getHeld(self, ) -> str:
    """The 'held' getter returns why the frame is not held, or nothing
    if it is."""
    return self.__analysis_held__

  @reactions.GET
  def _getReactions(self, ) -> tuple[tuple[float, float, float], ...]:
    """The 'reactions' getter returns what each support pushes with,
    along x and y, and turning, in the order of the supports; noughts if
    the frame is not held."""
    if self.__analysis_reactions__ is None:
      return (*[(0.0, 0.0, 0.0) for _ in self.frame.supports],)
    return self.__analysis_reactions__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Frame)
  def __init__(self, frame: Frame) -> None:
    self.__analysis_frame__ = frame
    self.__analysis_kept__ = {}
    self.__analysis_stations__ = [self._stationsOf(i)
                                  for i in range(len(frame.members))]
    reason = self._reasonUnheld()
    if reason:
      self.__analysis_held__ = reason
      return
    self._solve()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stations(self, member: int) -> list[float]:
    """The 'stations' method returns where the member of index 'member'
    is cut, in m along it: its ends, its loads and its line loads'
    ends."""
    key = ('stations', member)
    if key not in self.__analysis_kept__:
      self.__analysis_kept__[key] = self._keptOf(member)
    return self.__analysis_kept__[key]

  def normal(self, member: int, s: float, side: int = 1) -> float:
    """The 'normal' method returns N, in kN, tension positive, 's' m
    along the member of index 'member', just past it, or just before it
    for 'side' below nought."""
    return self._sections(member, s, side)[0]

  def shear(self, member: int, s: float, side: int = 1) -> float:
    """The 'shear' method returns V, in kN, 's' m along the member of
    index 'member', just past it, or just before it for 'side' below
    nought."""
    return self._sections(member, s, side)[1]

  def moment(self, member: int, s: float, side: int = 1) -> float:
    """The 'moment' method returns M, in kNm, 's' m along the member of
    index 'member', just past it, or just before it for 'side' below
    nought."""
    return self._sections(member, s, side)[2]

  def diagram(self, member: int, kind: str) -> list[tuple[float, float]]:
    """The 'diagram' method returns the section force 'kind', 'N', 'V'
    or 'M', along the member of index 'member': its values at points
    from end to end, twice where it jumps, before and after."""
    key = ('diagram', member, kind)
    if key in self.__analysis_kept__:
      return self.__analysis_kept__[key]
    which = _KINDS.index(kind)
    stations = self.stations(member)
    out = []
    self.__analysis_kept__[key] = out
    for a, b in zip(stations, stations[1:]):
      for k in range(_SAMPLES + 1):
        s = a + (b - a) * k / _SAMPLES
        side = -1 if k == _SAMPLES else 1
        out.append((s, self._sections(member, s, side)[which]))
    return out

  def marks(self, member: int, kind: str) -> list[tuple[float, float]]:
    """The 'marks' method returns where the section force 'kind' along
    the member of index 'member' is worth writing: at its ends, either
    side of its jumps, and, for the moment, at its peaks, where the
    shear is nought; nought left out."""
    key = ('marks', member, kind)
    if key in self.__analysis_kept__:
      return self.__analysis_kept__[key]
    which = _KINDS.index(kind)
    stations = self.stations(member)
    out = []
    for index, s in enumerate(stations):
      sides = [side for side, keep in ((-1, index > 0),
                                       (1, index < len(stations) - 1))
               if keep]
      for side in sides:
        out.append((s, self._sections(member, s, side)[which]))
    if kind == 'M':
      for a, b in zip(stations, stations[1:]):
        middle = (a + b) / 2
        values = (self.shear(member, a, 1), self.shear(member, middle),
                  self.shear(member, b, -1))
        for s in _roots(values, a, b):
          out.append((s, self.moment(member, s)))
    kept = []
    for s, value in sorted(out):
      if abs(value) < 1e-9:
        continue
      if kept and abs(kept[-1][0] - s) < 1e-9 and abs(
          kept[-1][1] - value) < 1e-6 * max(abs(value), 1.0):
        continue
      kept.append((s, value))
    self.__analysis_kept__[key] = kept
    return kept

  def most(self, kind: str) -> tuple[float, int, float]:
    """The 'most' method returns the greatest section force 'kind' in the
    frame, either way: its value, its member and where along it."""
    key = ('most', kind)
    if key in self.__analysis_kept__:
      return self.__analysis_kept__[key]
    best = (0.0, 0, 0.0)
    for member in range(len(self.frame.members)):
      for s, value in self.diagram(member, kind) + self.marks(member,
                                                               kind):
        if abs(value) > abs(best[0]):
          best = (value, member, s)
    self.__analysis_kept__[key] = best
    return best

  def shape(self, member: int) -> list[tuple[float, float, float, float]]:
    """The 'shape' method returns the member of index 'member' as it
    bends: points along it, each where it is and how far it moves, along
    x and y, in m; nothing if the frame is not held."""
    if self.held or self.__analysis_moves__ is None:
      return []
    key = ('shape', member)
    if key in self.__analysis_kept__:
      return self.__analysis_kept__[key]
    frame = self.frame
    tx, ty = frame.direction(member)
    out = []
    places = self.__analysis_places__[member]
    for k, (a, b) in enumerate(zip(places, places[1:])):
      ends = self._pieceEnds(member, k)
      for step in range(9 if k == len(places) - 2 else 8):
        share = step / 8
        u, w = self._hermite(ends, share, b[0] - a[0])
        s = a[0] + share * (b[0] - a[0])
        x, y = frame.pointAt(member, s)
        out.append((x, y, u * tx - w * ty, u * ty + w * tx))
    self.__analysis_kept__[key] = out
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _keptOf(self, member: int) -> list[float]:
    """Where the member of index 'member' has its stations, exactly:
    its ends, its loads and its line loads' ends."""
    frame = self.frame
    long = frame.length(member)
    kept = {0.0, long}
    for load in frame.loads:
      if load.member != member:
        continue
      if isinstance(load, LineLoad):
        kept |= {load.start, load.end}
      else:
        kept.add(load.at)
    out = []
    for s in sorted(min(max(s, 0.0), long) for s in kept):
      if not out or s - out[-1] >= _NEAR:
        out.append(s)
    out[-1] = long
    return out

  def _stationsOf(self, member: int) -> list[tuple[float, bool]]:
    """Where the member of index 'member' is cut into pieces for the
    reckoning: at its stations, and, for its shape, at least so many
    pieces, none shorter than a millimetre, each cut with whether it is a
    station."""
    long = self.frame.length(member)
    kept = self._keptOf(member)
    extra = [long * k / _PIECES for k in range(1, _PIECES)]
    out = [(0.0, True)]
    for s in sorted(kept + extra):
      if s - out[-1][0] < _PIECE or long - s < _PIECE:
        continue
      out.append((s, any(abs(s - k) < _NEAR for k in kept)))
    return [*out, (long, True)]

  def _reasonUnheld(self, ) -> str:
    """Why the frame cannot be held, as far as the counting tells:
    no members, a node joined to none."""
    frame = self.frame
    if not frame.members:
      return 'the frame has no members'
    for index in range(len(frame.nodes)):
      if not frame.joined(index):
        return 'N%d is joined to no member' % (index + 1)
    return ''

  def _numbering(self, ) -> list[list[int]]:
    """The node each station of each member is at: the frame's own at
    its ends, new ones between."""
    frame = self.frame
    count = len(frame.nodes)
    out = []
    for index, member in enumerate(frame.members):
      places = self.__analysis_stations__[index]
      numbers = [member.first]
      for _ in places[1:-1]:
        numbers.append(count)
        count += 1
      out.append(numbers + [member.second])
    return out

  def _solve(self, ) -> None:
    """Reckons the frame: assembles the stiffness of every piece and the
    loads, holds what the supports and the hinges hold, and solves."""
    frame = self.frame
    numbering = self._numbering()
    count = max(len(frame.nodes), 1 + max(max(n) for n in numbering))
    stiffness = torch.zeros(3 * count, 3 * count).double()
    loads = torch.zeros(3 * count).double()
    self.__analysis_ends__ = []
    self.__analysis_places__ = []
    self.__analysis_turns__ = {}
    for index in range(len(frame.members)):
      self._assembleMember(index, numbering[index], stiffness, loads)
    self._nodeLoads(numbering, loads)
    held = self._heldDofs(count, stiffness)
    free = [d for d in range(3 * count) if d not in held]
    inner = stiffness[free][:, free]
    values = torch.linalg.eigvalsh(inner)
    if not len(values) or float(values.min()) <= 1e-13 * float(
        values.abs().max()):
      self.__analysis_held__ = self._mechanism()
      return
    moves = torch.zeros(3 * count).double()
    moves[free] = torch.linalg.solve(inner, loads[free])
    self.__analysis_moves__ = moves
    pushed = stiffness @ moves - loads
    reactions = []
    for support in frame.supports:
      at = 3 * support.node
      reactions.append((*[float(pushed[at + k]) if support.holds[k] else
                          0.0 for k in range(3)],))
    self.__analysis_reactions__ = (*reactions,)

  def _mechanism(self, ) -> str:
    """Why the frame moves without bending, as far as its supports
    tell."""
    holds = [support.holds for support in self.frame.supports]
    if not any(h[0] for h in holds):
      return 'nothing holds the frame along x: it needs a pin or a fixed'
    return ('the frame can move without bending: it needs more supports '
            'or fewer hinges')

  def _local(self, index: int, piece: int) -> tuple:
    """The stiffness of the piece 'piece' of the member of index 'index',
    as it runs, its loads at its ends doing the same work as the line
    loads on it, and which of its ends turn free."""
    frame = self.frame
    member = frame.members[index]
    places = self.__analysis_stations__[index]
    a, b = places[piece][0], places[piece + 1][0]
    h = b - a
    ea, ei = member.EA / h, member.EI
    k = torch.zeros(6, 6).double()
    for i, j, value in ((0, 0, ea), (0, 3, -ea), (3, 0, -ea), (3, 3, ea)):
      k[i, j] = value
    bend = doubles([[12, 6 * h, -12, 6 * h],
                    [6 * h, 4 * h * h, -6 * h, 2 * h * h],
                    [-12, -6 * h, 12, -6 * h],
                    [6 * h, 2 * h * h, -6 * h, 4 * h * h]]) * (ei / h ** 3)
    spots = [1, 2, 4, 5]
    for row, i in enumerate(spots):
      for column, j in enumerate(spots):
        k[i, j] = bend[row, column]
    f = self._workLoads(index, a, b)
    released = []
    if piece == 0 and member.startHinge:
      released.append(2)
    if piece == len(places) - 2 and member.endHinge:
      released.append(5)
    return k, f, released

  def _workLoads(self, index: int, a: float, b: float) -> torch.Tensor:
    """The loads at the ends of the piece from 'a' to 'b' along the
    member of index 'index', as it runs, doing the same work as the line
    loads on it."""
    frame = self.frame
    tx, ty = frame.direction(index)
    h = b - a
    f = torch.zeros(6).double()
    for load in frame.loads:
      if load.member != index or not isinstance(load, LineLoad):
        continue
      if load.end <= a + _NEAR or load.start >= b - _NEAR:
        continue
      px, py = load.pushing()
      along, across = px * tx + py * ty, -px * ty + py * tx
      first, last = load.intensity(a), load.intensity(b)
      f[0] += along * h * (2 * first + last) / 6
      f[3] += along * h * (first + 2 * last) / 6
      f[1] += across * h * (7 * first + 3 * last) / 20
      f[2] += across * h * h * (3 * first + 2 * last) / 60
      f[4] += across * h * (3 * first + 7 * last) / 20
      f[5] -= across * h * h * (2 * first + 3 * last) / 60
    return f

  @staticmethod
  def _condensed(k: torch.Tensor, f: torch.Tensor,
                 released: list[int]) -> tuple:
    """'k' and 'f' with the moments at the ends 'released' let go."""
    k, f = k.clone(), f.clone()
    for r in released:
      if abs(float(k[r, r])) < 1e-300:
        continue
      column = k[:, r].clone()
      f = f - column * (f[r] / k[r, r])
      k = k - column[:, None] * k[r, :][None, :] / k[r, r]
    return k, f

  def _turning(self, index: int) -> torch.Tensor:
    """What turns the member of index 'index' from the frame's axes to
    its own, for both its ends."""
    tx, ty = self.frame.direction(index)
    turn = torch.zeros(6, 6).double()
    for at in (0, 3):
      turn[at, at], turn[at, at + 1] = tx, ty
      turn[at + 1, at], turn[at + 1, at + 1] = -ty, tx
      turn[at + 2, at + 2] = 1.0
    return turn

  def _assembleMember(self, index: int, numbers: list[int],
                      stiffness: torch.Tensor,
                      loads: torch.Tensor) -> None:
    """Adds the pieces of the member of index 'index' to the frame's
    stiffness and loads."""
    turn = self._turning(index)
    places = self.__analysis_stations__[index]
    self.__analysis_places__.append(places)
    pieces = []
    for piece in range(len(places) - 1):
      k, f, released = self._local(index, piece)
      kc, fc = self._condensed(k, f, released)
      dofs = [3 * numbers[piece] + i for i in range(3)]
      dofs += [3 * numbers[piece + 1] + i for i in range(3)]
      stiffness[torch.tensor(dofs)[:, None], torch.tensor(dofs)[None, :]] \
        += turn.T @ kc @ turn
      loads[torch.tensor(dofs)] += turn.T @ fc
      pieces.append((dofs, k, f, released))
    self.__analysis_ends__.append(pieces)

  def _nodeLoads(self, numbering: list[list[int]],
                 loads: torch.Tensor) -> None:
    """Adds the point loads and moments to the nodes at their
    stations."""
    frame = self.frame
    for load in frame.loads:
      if isinstance(load, LineLoad):
        continue
      places = self.__analysis_stations__[load.member]
      station = self._stationIndex(places, load.at)
      node = numbering[load.member][station]
      if isinstance(load, PointLoad):
        loads[3 * node] += load.right
        loads[3 * node + 1] -= load.down
      else:
        loads[3 * node + 2] += load.moment

  @staticmethod
  def _stationIndex(places: list, s: float) -> int:
    """The index of the station at 's'."""
    _, index = min((abs(place - s), i) for i, (place, _) in
                   enumerate(places))
    return index

  def _heldDofs(self, count: int, stiffness: torch.Tensor) -> set[int]:
    """The ways held: by the supports, and the turning of a node every
    member on it is hinged at, which nothing turns."""
    held = set()
    for support in self.frame.supports:
      for k, holds in enumerate(support.holds):
        if holds:
          held.add(3 * support.node + k)
    scale = float(stiffness.diagonal().abs().max())
    for node in range(count):
      dof = 3 * node + 2
      if abs(float(stiffness[dof, dof])) <= 1e-12 * scale:
        held.add(dof)
    return held

  def _pieceEnds(self, index: int, piece: int) -> tuple:
    """How the ends of the piece 'piece' of the member of index 'index'
    move, as it runs: along, across and turning at each, a released end
    turning as its piece lets it."""
    dofs, k, f, released = self.__analysis_ends__[index][piece]
    turn = self._turning(index)
    local = turn @ self.__analysis_moves__[torch.tensor(dofs)]
    if released:
      rest = [i for i in range(6) if i not in released]
      free, kept = torch.tensor(released), torch.tensor(rest)
      push = f[free] - k[free][:, kept] @ local[kept]
      local[free] = torch.linalg.solve(k[free][:, free], push)
    return local

  @staticmethod
  def _hermite(ends: torch.Tensor, share: float,
               h: float) -> tuple[float, float]:
    """How far a piece moves along and across it at 'share' of its
    length 'h', its ends moving as 'ends'."""
    u1, w1, r1, u2, w2, r2 = map(float, ends)
    t = share
    along = u1 + (u2 - u1) * t
    across = ((1 - 3 * t * t + 2 * t ** 3) * w1
              + (t - 2 * t * t + t ** 3) * h * r1
              + (3 * t * t - 2 * t ** 3) * w2
              + (-t * t + t ** 3) * h * r2)
    return along, across

  def _startForces(self, index: int) -> tuple[float, float, float]:
    """What the first node pushes the member of index 'index' with, as
    it runs: along it, across it and turning."""
    key = ('start', index)
    if key in self.__analysis_kept__:
      return self.__analysis_kept__[key]
    dofs, k, f, released = self.__analysis_ends__[index][0]
    kc, fc = self._condensed(k, f, released)
    turn = self._turning(index)
    local = turn @ self.__analysis_moves__[torch.tensor(dofs)]
    ends = kc @ local - fc
    out = float(ends[0]), float(ends[1]), float(ends[2])
    self.__analysis_kept__[key] = out
    return out

  def _sections(self, member: int, s: float,
                side: int) -> tuple[float, float, float]:
    """N, V and M 's' m along the member of index 'member', just past it,
    or just before it for 'side' below nought: from what its first node
    pushes it with and what lies on it before."""
    if self.held:
      return 0.0, 0.0, 0.0
    tx, ty, long, loads = self._memberOf(member)
    along, across, turning = self._startForces(member)
    normal, shear, moment = -along, across, across * s - turning
    for load in loads:
      if isinstance(load, LineLoad):
        part = self._lineLoad(load, s, (tx, ty))
        normal, shear, moment = (normal - part[0], shear + part[1],
                                 moment + part[2])
        continue
      before = load.at < s - _NEAR or (side > 0 and abs(load.at - s)
                                       <= _NEAR)
      if not before or load.at <= _NEAR or load.at >= long - _NEAR:
        continue
      if isinstance(load, PointMoment):
        moment -= load.moment
        continue
      along = load.right * tx - load.down * ty
      across = -load.right * ty - load.down * tx
      normal -= along
      shear += across
      moment += across * (s - load.at)
    return normal, shear, moment

  def _memberOf(self, member: int) -> tuple:
    """The direction of the member of index 'member', its length, and
    the loads on it, kept."""
    key = ('member', member)
    if key not in self.__analysis_kept__:
      frame = self.frame
      loads = [load for load in frame.loads if load.member == member]
      self.__analysis_kept__[key] = (*frame.direction(member),
                                     frame.length(member), loads)
    return self.__analysis_kept__[key]

  @staticmethod
  def _lineLoad(load: LineLoad, s: float,
                direction: tuple[float, float]) -> tuple:
    """What 'load' lays on its member before 's': along it, across it,
    and its moment about 's'."""
    end = min(load.end, s)
    if end <= load.start:
      return 0.0, 0.0, 0.0
    tx, ty = direction
    px, py = load.pushing()
    along, across = px * tx + py * ty, -px * ty + py * tx
    total = _simpson(load.intensity, load.start, end)
    turning = _simpson(lambda u: load.intensity(u) * (s - u), load.start,
                       end)
    return along * total, across * total, across * turning
