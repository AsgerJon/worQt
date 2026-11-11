"""
Recorder plays a shot at once and samples it, a 'Stretch' at a time,
and Recording is the shot so sampled, to be shown as it streams in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import bisect
import math
from typing import NamedTuple, TYPE_CHECKING

import numpy

from ._carom_table import Ball, isParked
from ._motion import Motion

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Iterator

#  How many numbers a ball's state takes in a sample: 'x', 'y', the four
#  of its 'turn', 'vx', 'vy', 'wx', 'wy', 'wz', and one if 'settling'.
STATE = 12

#  How many numbers a pin's state takes in a sample: its 'number', where
#  its centre of mass is, 'x', 'y', 'z', the four of its turn 'q', scalar
#  first, one if it is awake, and the ball it is credited to, its index
#  in the balls' names, -1 for none.
PIN_STATE = 10

_DUE = 1e-9  # s: a sample due this little after now is taken now


class Stretch(NamedTuple):
  """
  Stretch is a piece of a recorded shot as it streams: 'first', the
  number of its first sample; 'states', its samples, an array of
  samples by balls by 'STATE'; 'touches', the contacts beginning in it,
  each its time and its 'Touch'; whether the shot is 'over' with it,
  every ball at rest; and in keglebillard the pins' samples, 'pins', an
  array of samples by pins by 'PIN_STATE'.
  """

  first: int
  states: numpy.ndarray
  touches: tuple
  over: bool
  pins: numpy.ndarray = None


class Recording(NamedTuple):
  """
  Recording is a shot sampled 'rate' times a second, from the moment
  the balls were struck: the balls' 'names'; the samples in 'parts',
  one array a stretch, each beginning at the sample in 'starts'; the
  contacts in 'touches', each its time and its 'Touch'; whether it is
  'over', all of it there; and in keglebillard the pins' samples in
  'pinParts', one array a stretch beside 'parts'. It never changes:
  'joined' returns it with a stretch more.

  'ballsAt' gives the balls at any moment there is a sample for,
  between two samples in a straight line, their turns blended; past the
  last sample, as they are at it. 'placesOf' gives the balls' middles
  over a run of samples at once. 'pinsAt' gives the pins at any moment,
  as 'ballsAt' gives the balls.
  """

  names: tuple = ()
  rate: float = 1000.0
  parts: tuple = ()
  starts: tuple = ()
  touches: tuple = ()
  over: bool = False
  pinParts: tuple = ()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def joined(self, stretch: Stretch) -> Recording:
    """The 'joined' method returns the recording with 'stretch' added
    at its end; the recording as it is if 'stretch' does not begin where
    it ends, or it is over."""
    if self.over or stretch.first != self.count():
      return self
    parts, starts, pinParts = self.parts, self.starts, self.pinParts
    if len(stretch.states):
      parts = (*parts, stretch.states)
      starts = (*starts, stretch.first)
      if stretch.pins is not None:
        pinParts = (*pinParts, stretch.pins)
    return Recording(self.names, self.rate, parts, starts,
                     (*self.touches, *stretch.touches), stretch.over,
                     pinParts)

  def count(self, ) -> int:
    """The 'count' method returns how many samples there are."""
    if not self.parts:
      return 0
    return self.starts[-1] + len(self.parts[-1])

  def known(self, ) -> float:
    """The 'known' method returns the time of the last sample, nought
    if there is none."""
    return max(self.count() - 1, 0) / self.rate

  def stateOf(self, index: int) -> numpy.ndarray:
    """The 'stateOf' method returns sample 'index', balls by 'STATE'."""
    part = bisect.bisect_right(self.starts, index) - 1
    return self.parts[part][index - self.starts[part]]

  def placesOf(self, start: int, stop: int) -> numpy.ndarray:
    """The 'placesOf' method returns where the balls' middles are in
    the samples from 'start' up to 'stop', not counting it: samples by
    balls by 'x' and 'y'."""
    stop = min(stop, self.count())
    if stop <= start:
      return numpy.zeros((0, len(self.names), 2))
    first = max(bisect.bisect_right(self.starts, start) - 1, 0)
    pieces = []
    for begins, part in zip(self.starts[first:], self.parts[first:]):
      if begins >= stop:
        break
      low, high = max(start - begins, 0), min(stop - begins, len(part))
      pieces.append(part[low:high, :, :2])
    return numpy.concatenate(pieces)

  def ballsAt(self, seconds: float) -> tuple[Ball, ...]:
    """The 'ballsAt' method returns the balls 'seconds' after they were
    struck, between the samples either side, at the last one past it."""
    last = self.count() - 1
    if last < 0:
      return ()
    place = min(max(seconds * self.rate, 0.0), float(last))
    index = min(int(math.floor(place + _DUE)), last)
    share = place - index
    first = self.stateOf(index)
    if share <= 0.0 or index == last:
      return tuple(_ballOf(name, row) for name, row in zip(self.names,
                                                           first))
    second = self.stateOf(index + 1)
    return tuple(_blended(name, one, other, share)
                 for name, one, other in zip(self.names, first, second))

  def pinsAt(self, seconds: float) -> numpy.ndarray:
    """The 'pinsAt' method returns the pins 'seconds' after the balls
    were struck, pins by 'PIN_STATE', between the samples either side,
    their turns blended; at the last one past it; none if the shot has
    no pins."""
    last = self.count() - 1
    if last < 0 or not self.pinParts:
      return numpy.zeros((0, PIN_STATE))
    place = min(max(seconds * self.rate, 0.0), float(last))
    index = min(int(math.floor(place + _DUE)), last)
    share = place - index
    first = self._pinsOf(index)
    if share <= 0.0 or index == last:
      return numpy.array(first)
    return _pinsBlended(first, self._pinsOf(index + 1), share)

  def lastPins(self, ) -> numpy.ndarray:
    """The 'lastPins' method returns the pins at the last sample, pins by
    'PIN_STATE': at rest, once the recording is over."""
    return self.pinsAt(self.known())

  def last(self, ) -> tuple[Ball, ...]:
    """The 'last' method returns the balls at the last sample: at rest,
    once the recording is over."""
    if not self.parts:
      return ()
    return tuple(_ballOf(name, row) for name, row in zip(
      self.names, self.stateOf(self.count() - 1)))

  def struck(self, ) -> tuple[Ball, ...]:
    """The 'struck' method returns the balls struck, as they were then:
    those moving or spinning at the first sample."""
    return tuple(ball for ball in self.ballsAt(0.0)
                 if any((ball.vx, ball.vy, ball.wx, ball.wy, ball.wz)))

  def _pinsOf(self, index: int) -> numpy.ndarray:
    """Returns the pins in sample 'index', pins by 'PIN_STATE'."""
    part = bisect.bisect_right(self.starts, index) - 1
    return self.pinParts[part][index - self.starts[part]]

  def touchesOf(self, ) -> tuple:
    """The 'touchesOf' method returns the contacts, each a 'Touch', in
    the order they began."""
    return tuple(touch for _, touch in self.touches)

  def timeOf(self, count: int) -> float:
    """The 'timeOf' method returns when the first 'count' contacts had
    all begun: nought for none, the end for more than there are."""
    if count <= 0:
      return 0.0
    if count > len(self.touches):
      return math.inf
    return self.touches[count - 1][0]


class Recorder(NamedTuple):
  """
  Recorder plays shots on the table of 'motion' at once, and samples
  them 'rate' times a second, streaming them 'size' samples a
  'Stretch'; a shot is followed until every ball rests, 'longest'
  seconds at most.

  The steps through hits are whole, never cut short, and one 'Hits'
  follows each run of hits through all its samples, so the samples do
  not change the shot: it is the one 'Motion.played' gives over its
  whole length at once, whatever the rate. Between hits the samples are
  taken on the cloth exactly; through a hit, as the step that reaches
  each one ends, a hair later at most. A contact beginning on the cloth
  is timed exactly; one beginning through a hit, at the next sample, a
  sample's time later at most. The last sample is the balls at rest.
  """

  motion: Motion = Motion()
  rate: float = 1000.0
  size: int = 50
  longest: float = 60.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def resting(self, balls: tuple[Ball, ...]) -> bool:
    """The 'resting' method tells whether every ball of 'balls' is
    still and touches nothing it is moving into."""
    motion, radius = self.motion, self.motion.table.radius
    if motion.inContact(balls):
      return False
    return all(motion.cloth.phaseOf(ball, radius) == 'still'
               for ball in balls)

  def stretches(self, balls: tuple[Ball, ...]) -> Iterator[Stretch]:
    """The 'stretches' method plays 'balls' on from now until all rest,
    yielding the samples a 'Stretch' at a time, the last one 'over'."""
    motion, cloth = self.motion, self.motion.cloth
    radius, every = self.motion.table.radius, 1.0 / self.rate
    balls, passed, hits = tuple(balls), 0.0, None
    rows, touches, count, first = [], [], 0, 0
    while True:
      while count * every <= passed + _DUE:
        rows.append(_rowsOf(balls))
        count += 1
      over = self.resting(balls) or passed >= self.longest
      if over:
        rows.append(_rowsOf(balls))
        count += 1
      if over or len(rows) >= self.size:
        yield Stretch(first, numpy.array(rows), tuple(touches), over)
        if over:
          return
        rows, touches, first = [], [], count
      if hits is not None or motion.inContact(balls):
        if hits is None:
          hits = motion.hitsOf(balls)
        balls, used, began = hits.run(count * every - passed, True)
        passed += used
        touches.extend((passed, touch) for touch in began)
        if hits.over:
          hits = None
        continue
      glide = motion.glided(balls, self.longest - passed)
      end, inner, at = passed + glide.span, balls, passed
      while count * every < end - _DUE:
        span = count * every - at
        inner = tuple(cloth.moved(ball, phase, span, radius)
                      for ball, phase in zip(inner, glide.phases))
        at = count * every
        rows.append(_rowsOf(inner))
        count += 1
        if len(rows) >= self.size:
          yield Stretch(first, numpy.array(rows), tuple(touches), False)
          rows, touches, first = [], [], count
      balls, passed = glide.after, end
      touches.extend((end, touch) for touch in glide.touches)

  def recorded(self, balls: tuple[Ball, ...]) -> Recording:
    """The 'recorded' method returns the whole shot of 'balls', played
    on until all rest, as a 'Recording'."""
    recording = Recording(tuple(ball.name for ball in balls), self.rate)
    for stretch in self.stretches(balls):
      recording = recording.joined(stretch)
    return recording


def _rowsOf(balls: tuple[Ball, ...]) -> list:
  """Returns the state of each of 'balls', 'STATE' numbers each."""
  return [[ball.x, ball.y, *ball.turn, ball.vx, ball.vy, ball.wx,
           ball.wy, ball.wz, 1.0 if ball.settling else 0.0]
          for ball in balls]


def _ballOf(name: str, row: numpy.ndarray) -> Ball:
  """Returns the ball 'name' in the state 'row'."""
  values = [float(value) for value in row]
  return Ball(name, values[0], values[1], tuple(values[2:6]),
              *values[6:11], values[11] > 0.5)


def _blended(name: str, one: numpy.ndarray, other: numpy.ndarray,
             share: float) -> Ball:
  """Returns the ball 'name' 'share' of the way from the state 'one' to
  'other': in a straight line, its turn blended the short way round and
  kept of length one; as at 'one' while it goes into a pocket, so it
  does not fly to where it is kept."""
  first = [float(value) for value in one]
  second = [float(value) for value in other]
  if isParked(first[0], first[1]) or isParked(second[0], second[1]):
    return _ballOf(name, one)
  if sum(a * b for a, b in zip(first[2:6], second[2:6])) < 0.0:
    second[2:6] = [-value for value in second[2:6]]
  values = [a + (b - a) * share for a, b in zip(first[:11], second[:11])]
  size = math.sqrt(sum(value * value for value in values[2:6]))
  turn = tuple(value / size for value in values[2:6])
  return Ball(name, values[0], values[1], turn, *values[6:11],
              first[11] > 0.5)


def _pinsBlended(one: numpy.ndarray, other: numpy.ndarray,
                 share: float) -> numpy.ndarray:
  """Returns the pins 'share' of the way from the states 'one' to
  'other': each in a straight line, its turn blended the short way
  round and kept of length one, the rest as in 'one'."""
  out = numpy.array(one, dtype=float)
  second = numpy.array(other, dtype=float)
  flip = numpy.sum(out[:, 4:8] * second[:, 4:8], axis=1) < 0.0
  second[flip, 4:8] *= -1.0
  out[:, 1:8] += (second[:, 1:8] - out[:, 1:8]) * share
  sizes = numpy.linalg.norm(out[:, 4:8], axis=1)
  out[:, 4:8] /= numpy.where(sizes > 0.0, sizes, 1.0)[:, None]
  return out
