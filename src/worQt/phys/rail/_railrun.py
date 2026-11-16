"""
RailRun steps a rail world's wheelsets with the Warp kernel 'railRun'
('_rail_kernels', one thread a wheelset, float32) instead of its plain
Python (the reference, float64), on a device of Warp's. Each call takes
every wheelset into the track's frame where it stands (the track's
centre line there its origin) and back, in float64, so the kernel
handles nothing larger than a metre or so.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import bisect
import math
from typing import TYPE_CHECKING

import numpy

from .._body import State
from .._vectors import conjugate, matrixOf, product, turnOf
from ._railworld import GRAVITY

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._railworld import RailWorld

#  A contact's place among a wheelset's four, by (side, kind) as the
#  rail world keys them.
KEYS = ((1.0, 0), (1.0, 1), (-1.0, 0), (-1.0, 1))
#  Unreachable, m along: no guard where the track ends before the
#  table.
NOWHERE = 1e30


def preloadedRails(device: str) -> None:
  """The 'preloadedRails' function has the rail kernel ready on
  'device' (compiled, or loaded from Warp's cache)."""
  import warp as wp
  wp.init()
  from . import _rail_kernels
  wp.load_module(_rail_kernels, device)


class RailRun:
  """
  RailRun steps the wheelsets of 'world' (a 'RailWorld') on 'device':
  'rolled' takes each into the track's frame where it stands, with the
  track about it within the kernel's 'WINDOW' as a table, launches one
  thread a wheelset for all the call's steps, and takes them back.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  world: RailWorld
  device: str

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, world: RailWorld, device: str) -> None:
    import warp as wp
    wp.init()
    from . import _rail_kernels
    self.wp, self.kernels = wp, _rail_kernels
    self.world, self.device = world, device
    starts, places, frames, rates = world.segments
    self.starts = list(starts)
    self.places = numpy.array(places)
    self.frames = numpy.array(frames).reshape(-1, 3, 3)
    self.rates = numpy.array(rates)
    self._key, self._tableRows, self._framesKey = None, 0, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def rolled(self, rails: tuple, states: list, seconds: float,
             held: dict, seen: dict, pushes: dict) -> None:
    """The 'rolled' method rolls the wheelsets at 'rails' 'seconds' on
    in 'states' (in place), each held in its boxes of 'held' (as 'seen'
    at the start, by id), adding what they push their frames with to
    'pushes' (by frame: impulse and twist); their memories kept in the
    world's 'rolling', the boxes' loads in its 'boxLoads'. (One trade:
    the frames' states come and go through the host.)"""
    wp, kernels = self.wp, self.kernels
    begun = self._begun(rails, states, held, [kernels.WINDOW] * len(rails))
    there = begun[0]
    looked = self._seenRows
    j = 0
    for k, i in enumerate(rails):
      origin, axes, _ = there[k]
      back = axes.T
      for box in held.get(i, ()):
        place, moving, arm, swing, frame, spin = seen[id(box)]
        looked[j, 0:3] = back @ (numpy.array(place) - origin)
        looked[j, 3:6] = back @ numpy.array(moving)
        looked[j, 6:9] = back @ numpy.array(arm)
        looked[j, 9:12] = back @ numpy.array(swing)
        looked[j, 12:21] = (back @ numpy.array(frame).T).ravel()
        looked[j, 21:24] = back @ numpy.array(spin)
        j += 1
    if j:
      self.seen.assign(looked.astype(numpy.float32))
    self.results.zero_()
    self._launched(seconds)
    summed = self._ended(rails, states, held, begun, 1)
    j = 0
    for k, i in enumerate(rails):
      axes = there[k][1]
      for box in held.get(i, ()):
        frame = pushes[box.frame]
        impulse, twist = axes @ summed[j, 0:3], axes @ summed[j, 3:6]
        for c in range(3):
          frame[c] += float(impulse[c])
          frame[3 + c] += float(twist[c])
        j += 1

  def traded(self, inner: object, packed: object, assembly: object,
             kept: tuple, rails: tuple, states: list, seconds: float,
             start: float, held: dict, trades: int) -> None:
    """The 'traded' method steps the wheelsets at 'rails' and the inner
    world's bodies ('assembly' of 'inner', its bodies 'kept' of the
    world's, 'packed' on the device with their states) 'seconds' on in
    'trades' trades, all on the device: each trade every box read off
    its frame there ('boxesSeen'), the wheelsets stepped ('railRun'),
    the frames pushed ('framesPushed'), the inner world stepped
    ('steppedOn'); nothing comes back to the host till the end, where
    the wheelsets are set in 'states' (the inner world's bodies are
    'packed''s to hand back)."""
    wp, kernels, device = self.wp, self.kernels, self.device
    windows = [kernels.WINDOW + 1.5 * seconds * math.sqrt(
      sum(v * v for v in states[i].velocity)) for i in rails]
    begun = self._begun(rails, states, held, windows)
    self._framesReadied(rails, held, kept, packed)
    there = begun[0]
    high, low = numpy.zeros((len(rails), 3)), numpy.zeros((len(rails), 3))
    turned = numpy.zeros((len(rails), 3, 3))
    for k in range(len(rails)):
      origin, axes, _ = there[k]
      exact = origin - numpy.array(packed.origin)
      high[k] = exact.astype(numpy.float32)
      low[k] = exact - high[k].astype(numpy.float64)
      turned[k] = axes
    self.originHigh.assign(high.astype(numpy.float32))
    self.originLow.assign(low.astype(numpy.float32))
    self.localAxes.assign(turned.astype(numpy.float32))
    self.results.zero_()
    bodies, h = packed.bodies, seconds / trades
    for k in range(trades):
      if self.boxCount:
        wp.launch(kernels.boxesSeen, self.boxCount, [
          bodies.place, bodies.shift, bodies.turn, bodies.velocity,
          bodies.spin, self.boxBody, self.boxWheel, self.boxArm,
          self.boxAxes, self.originHigh, self.originLow, self.localAxes,
          self.seen], [], [], [], device)
      self._launched(h)
      if self.boxCount:
        wp.launch(kernels.framesPushed, self.frameCount, [
          self.frameBody, self.frameFirst, self.frameCounts,
          self.frameBoxes, self.boxWheel, self.localAxes, self.results,
          bodies.turn, bodies.velocity, bodies.spin, bodies.give,
          bodies.turnGive], [], [], [], device)
      inner.steppedOn(packed, assembly, h, start + k * h)
    self._ended(rails, states, held, begun, trades)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _begun(self, rails: tuple, states: list, held: dict,
             windows: list) -> tuple:
    """Sends the wheelsets at 'rails' to the device, each in the track's
    frame where it stands with the track within its window as a table;
    returns those frames and their memories."""
    world, kernels = self.world, self.kernels
    memories = [world.memoryOf(i, states[i]) for i in rails]
    boxes = tuple(box for i in rails for box in held.get(i, ()))
    there = [self._frameOf(memory['s']) for memory in memories]
    tables = [self._tableOf(memory['s'], frame, window) for memory, frame,
              window in zip(memories, there, windows)]
    self._readied(rails, held, boxes, sum(len(t[0]) for t in tables))
    if boxes:
      self.brakes.assign(numpy.array([box.brake for box in boxes],
                                     numpy.float32))
    rows, ranges, at = self._wheelRows, self._heldRows, 0
    rows[:] = 0.0
    table = self._table
    gravity = numpy.array(GRAVITY)
    for k, i in enumerate(rails):
      (origin, axes, turn), (steps, clamps, guards) = there[k], tables[k]
      state, memory = states[i], memories[k]
      back = axes.T
      rows[k, 0:3] = back @ (numpy.array(state.place) - origin)
      rows[k, 3:7] = product(conjugate(turn), state.turn)
      rows[k, 7:10] = back @ numpy.array(state.velocity)
      rows[k, 10:13] = back @ numpy.array(state.spin)
      for c, key in enumerate(KEYS):
        rows[k, 14 + 2 * c:16 + 2 * c] = memory['slips'].get(key,
                                                             (0.0, 0.0))
      rows[k, 27:30] = back @ gravity
      rows[k, 30:32], rows[k, 32:34] = clamps, guards
      ranges[k, 2:4] = (at, len(steps))
      table[at:at + len(steps)] = steps
      at += len(steps)
    self.wheels.assign(rows.astype(numpy.float32))
    self.held.assign(ranges)
    self.table.assign(table.astype(numpy.float32))
    return there, memories

  def _launched(self, seconds: float) -> None:
    """Launches the wheelsets' kernel for 'seconds' in the world's
    steps."""
    wp, world = self.wp, self.world
    count = max(1, math.ceil(seconds / world.step - 1e-9))
    wp.launch(self.kernels.railRun, self.wheelCount, [
      count, seconds / count, world.friction, world.body.mass,
      wp.vec3(*world.moments), self.table, self.wheels, self.held,
      self.seen, self.fixed, self.results, self.brakes], [], [], [],
      self.device)

  def _ended(self, rails: tuple, states: list, held: dict, begun: tuple,
             trades: int) -> numpy.ndarray:
    """Takes the wheelsets back from the device into 'states' (their
    memories kept; one that stopped, lost, off its table or off the
    rails, put in the world's 'derailed', as it was when it stopped),
    the boxes' loads (their mean over the 'trades') into the world's
    'boxLoads'; returns the results' rows."""
    world = self.world
    there, memories = begun
    got = self.wheels.numpy().astype(numpy.float64)
    for k, i in enumerate(rails):
      if got[k, 26] != 0.0:
        world.derailed.add(i)
    for k, i in enumerate(rails):
      origin, axes, turn = there[k]
      row = got[k]
      out = State(tuple(float(x) for x in origin + axes @ row[0:3]),
                  _unit(product(turn, tuple(float(x) for x in row[3:7]))),
                  tuple(float(x) for x in axes @ row[7:10]),
                  tuple(float(x) for x in axes @ row[10:13]))
      memory = memories[k]
      memory['s'] += float(row[13])
      memory['slips'] = {key: (float(row[14 + 2 * c]),
                               float(row[15 + 2 * c]))
                         for c, key in enumerate(KEYS) if row[22 + c] > 0.0}
      memory['loads'] = {key: float(row[22 + c])
                         for c, key in enumerate(KEYS)}
      memory['state'] = out
      states[i] = out
    summed = self.results.numpy().astype(numpy.float64)
    j = 0
    for i in rails:
      for box in held.get(i, ()):
        world.boxLoads[id(box)] = float(summed[j, 6]) / trades
        j += 1
    return summed

  def _framesReadied(self, rails: tuple, held: dict, kept: tuple,
                     packed: object) -> None:
    """Has the device's arrays of the boxes' frames ready (made only for
    other boxes or another packing): each box's frame as a body of the
    small steps, its wheelset, its arm and its frame's own axes in the
    frame's principal axes; each frame's boxes."""
    wp = self.wp
    boxes = tuple(box for i in rails for box in held.get(i, ()))
    key = (tuple(id(box) for box in boxes), id(packed), tuple(kept))
    if key == self._framesKey:
      return
    where = {index: k for k, index in enumerate(kept)}
    nb = max(1, len(boxes))
    body, wheel = numpy.zeros(nb, numpy.int32), numpy.zeros(nb, numpy.int32)
    arms, axes = numpy.zeros((nb, 3)), numpy.zeros((nb, 3, 3))
    frames, j = {}, 0
    for k, i in enumerate(rails):
      for box in held.get(i, ()):
        inner = where[box.frame]
        turn = matrixOf(packed.axes[inner])
        back = numpy.array(turn).T
        body[j], wheel[j] = inner, k
        arms[j] = back @ (numpy.array(box.box)
                          - numpy.array(packed.centres[inner]))
        axes[j] = back
        frames.setdefault(inner, []).append(j)
        j += 1
    order = sorted(frames)
    firsts, counts, listed = [], [], []
    for inner in order:
      firsts.append(len(listed))
      counts.append(len(frames[inner]))
      listed.extend(frames[inner])
    self.boxCount, self.frameCount = len(boxes), len(order)
    self.boxBody = self._sent(body, wp.int32)
    self.boxWheel = self._sent(wheel, wp.int32)
    self.boxArm = self._sent(arms, wp.vec3)
    self.boxAxes = self._sent(axes, wp.mat33)
    self.frameBody = self._sent(numpy.array(order or [0], numpy.int32),
                                wp.int32)
    self.frameFirst = self._sent(numpy.array(firsts or [0], numpy.int32),
                                 wp.int32)
    self.frameCounts = self._sent(numpy.array(counts or [0], numpy.int32),
                                  wp.int32)
    self.frameBoxes = self._sent(numpy.array(listed or [0], numpy.int32),
                                 wp.int32)
    n = len(rails)
    self.originHigh = self._sent(numpy.zeros((n, 3)), wp.vec3)
    self.originLow = self._sent(numpy.zeros((n, 3)), wp.vec3)
    self.localAxes = self._sent(numpy.zeros((n, 3, 3)), wp.mat33)
    self._framesKey = key

  def _frameOf(self, s: float) -> tuple:
    """Returns the track's frame at 's': its centre line's place there,
    its axes (columns) and their turn (a quaternion)."""
    place, frame, _ = self.world.frameAt(s)
    axes = numpy.array(frame).reshape(3, 3)
    return (numpy.array(place), axes,
            turnOf(tuple(tuple(float(x) for x in row) for row in axes)))

  def _tableOf(self, s: float, there: tuple, window: float) -> tuple:
    """Returns the track within 'window' m of 's' as table rows in the
    track's frame at 's' (each step's start along from 's', place,
    frame, turn rates; the first started at the window's edge or the
    track's start), how far it may go back and ahead along (the track's
    ends or the table's), and where it is off its table."""
    length = self.world.track.length
    origin, axes, _ = there
    back = axes.T
    begins = max(s - window, 0.0)
    first = max(0, bisect.bisect_right(self.starts, begins) - 1)
    last = bisect.bisect_right(self.starts, s + window)
    place, frame, rate = self.world.frameAt(begins)
    steps = [(begins, numpy.array(place), numpy.array(frame).reshape(3, 3),
              numpy.array(rate))]
    for i in range(first + 1, last):
      steps.append((self.starts[i], self.places[i], self.frames[i],
                    self.rates[i]))
    rows = numpy.zeros((len(steps), self.kernels.TABLE_ROW))
    for k, (start, there, turned, rate) in enumerate(steps):
      rows[k, 0] = start - s
      rows[k, 1:4] = back @ (there - origin)
      rows[k, 4:13] = (back @ turned).ravel()
      rows[k, 13:16] = rate
    ends = min(s + window, length)
    clamps = (begins - s, ends - s)
    guards = (begins - s if begins > 0.0 else -NOWHERE,
              ends - s if ends < length else NOWHERE)
    return rows, clamps, guards

  def _readied(self, rails: tuple, held: dict, boxes: tuple,
               tableRows: int) -> None:
    """Has the device's arrays ready for 'rails' held in 'boxes' with
    'tableRows' of track: made, and the boxes' unchanging numbers sent,
    only when these change (the table grown, never shrunk)."""
    key = (tuple(rails), tuple(id(box) for box in boxes))
    wp, kernels = self.wp, self.kernels
    if tableRows > self._tableRows:
      self._tableRows = 2 * tableRows
      self._table = numpy.zeros((self._tableRows, kernels.TABLE_ROW))
      self.table = self._sent(self._table, wp.float32)
    if key == self._key:
      return
    n, nb = len(rails), max(1, len(boxes))
    self.wheelCount = n
    self._wheelRows = numpy.zeros((n, kernels.WHEEL_ROW))
    self._seenRows = numpy.zeros((nb, kernels.SEEN_ROW))
    self._heldRows = numpy.zeros((n, 4), numpy.int32)
    at = 0
    for k, i in enumerate(rails):
      self._heldRows[k, 0:2] = (at, len(held.get(i, ())))
      at += len(held.get(i, ()))
    fixed = numpy.zeros((nb, kernels.FIXED_ROW))
    for j, box in enumerate(boxes):
      fixed[j] = (box.side,) + box.stiffness + box.damping + tuple(
        box.bearing)
    self.wheels = self._sent(self._wheelRows, wp.float32)
    self.held = self._sent(self._heldRows, wp.int32)
    self.seen = self._sent(self._seenRows, wp.float32)
    self.fixed = self._sent(fixed, wp.float32)
    self.brakes = self._sent(numpy.zeros(nb, numpy.float32), wp.float32)
    self.results = self._sent(numpy.zeros((nb, kernels.RESULT_ROW)),
                              wp.float32)
    self._key = key

  def _sent(self, values: numpy.ndarray, kind: object) -> object:
    """Returns 'values' as a Warp array of 'kind' on the device."""
    if values.dtype == numpy.float64:
      values = values.astype(numpy.float32)
    return self.wp.array(numpy.ascontiguousarray(values), kind, None,
                         None, None, None, self.device)


def _unit(q: tuple) -> tuple:
  """Returns quaternion 'q' made unit length."""
  size = math.sqrt(sum(x * x for x in q))
  return tuple(x / size for x in q)
