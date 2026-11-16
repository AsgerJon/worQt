"""
Turnout is a set of points (user, 2026-11-16: "do all the things", the
points with a lever among them): a track branching off another, its
switch blades setting which way a wheelset coming toward them goes.
'wayOf' follows the tracks from where a wheelset is, back and ahead,
as the turnouts send it: the stretch of track its steps may reach,
piece by piece.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations


class Turnout:
  """
  Turnout is a set of points on the rail world's track 'track' (its
  index among the world's tracks) at 'at' m along it, where track
  'branch' begins (its start there, its frame there that of 'track':
  the two run together there and part ahead). 'thrown' says where it
  sends a wheelset coming along 'track' toward 'at' from behind: False
  on along 'track', True onto 'branch' (the blades guiding its flanges
  that way; set as the world goes, by a lever). A wheelset coming back
  along 'branch' past its start goes on along 'track' behind 'at' however
  it is set (it trails through them), as one coming back along 'track'
  past 'at' stays on 'track'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  track: int
  at: float
  branch: int
  thrown: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, track: int, at: float, branch: int) -> None:
    if track == branch:
      raise ValueError('a track cannot branch off itself')
    if at < 0.0:
      raise ValueError('points %r m along a track are off it' % (at,))
    self.track, self.at, self.branch = track, float(at), branch
    self.thrown = False


def wayOf(lengths: tuple, turnouts: tuple, track: int, s: float,
          back: float, ahead: float, closed: frozenset = frozenset()
          ) -> tuple:
  """The 'wayOf' function returns the way a wheelset at 's' m along
  track 'track' (of tracks 'lengths' m long, joined by 'turnouts'; those
  in 'closed' run round, their ends one: an oval) may go within 'back'
  m behind it and 'ahead' m ahead, as the turnouts are set: pieces
  (from, to, track, shift) in order, 'from' and 'to' m along the way
  (measured as 's' is), each on 'track' at 'from' + 'shift' m along it;
  and whether the way's two ends are the tracks' own ends (buffer
  stops) rather than its reach."""
  behind, startsAtEnd = _behind(lengths, turnouts, track, s, back, closed)
  onward, endsAtEnd = _onward(lengths, turnouts, track, s, ahead, closed)
  return behind + onward, startsAtEnd, endsAtEnd


def _onward(lengths: tuple, turnouts: tuple, track: int, s: float,
            ahead: float, closed: frozenset) -> tuple:
  """Returns the way ahead of 's' on 'track' within 'ahead' m (pieces,
  first to last; round a closed track's end onto its start) and
  whether it ends where a track does."""
  pieces, here, shift, end = [], s, 0.0, s + ahead
  while True:
    thrown = [t for t in turnouts if t.track == track and t.thrown
              and here + shift <= t.at < end + shift]
    if thrown:
      turnout = min(thrown, key=lambda t: t.at)
      toe = turnout.at - shift
      if toe > here:
        pieces.append((here, toe, track, shift))
      track, shift, here = turnout.branch, -toe, toe
      continue
    last = lengths[track] - shift
    if track in closed and last < end:
      if last > here:
        pieces.append((here, last, track, shift))
      shift, here = shift - lengths[track], last
      continue
    pieces.append((here, max(here, min(end, last)), track, shift))
    return pieces, last <= end


def _behind(lengths: tuple, turnouts: tuple, track: int, s: float,
            back: float, closed: frozenset) -> tuple:
  """Returns the way behind 's' on 'track' within 'back' m (pieces,
  first to last, the last ending at 's'; round a closed track's start
  onto its end) and whether it begins where a track does."""
  pieces, here, shift, begins = [], s, 0.0, s - back
  while True:
    first = -shift
    if begins >= first:
      pieces.insert(0, (begins, here, track, shift))
      return pieces, False
    if here > first:
      pieces.insert(0, (first, here, track, shift))
    if track in closed:
      shift, here = shift + lengths[track], first
      continue
    parent = [t for t in turnouts if t.branch == track]
    if not parent:
      return pieces, True
    turnout = parent[0]
    track, shift, here = turnout.track, turnout.at - first, first
