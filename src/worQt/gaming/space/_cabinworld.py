"""
CabinWorld is what moves in the cabin (user, 2026-11-17: "when can Asger
get up and float around in micro-gravity?"; the loose things: "FAFO
rules"): Asger out of his chair and the loose things, stepped on a
device of Warp's by '_cabin_kernels', in the vessel's own axes, feeling
what the vessel feels there ('Accelerometer') and the gravity
enchantment's pull. Always at real time: a warp of the flight's time is
not the cabin's (it would be a hundred thousand of its steps a frame).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import numpy

from ._aerospike import G0
from ._cabinsolids import solids
from ._crewman import BALLS, HEFT
from ._furnishings import looseThings
from ._turns import quaternionOf

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._accelerometer import Accelerometer
  from ._crewman import Crewman

#  A step, s (the meetings' springs ring at 250 rad/s: 0.2 rad a step),
#  and at most this many a frame.
STEP = 1.0 / 1200.0
MOST_STEPS = 120


def preloadedCabin(device: str) -> float:
  """Has the cabin's kernels loaded on 'device' (compiled the first
  time, else from Warp's cache) and returns how long it took, s."""
  import warp as wp

  from . import _cabin_kernels
  began = time.perf_counter()
  wp.init()
  wp.load_module(_cabin_kernels, device)
  return time.perf_counter() - began


class CabinWorld:
  """
  CabinWorld steps the cabin's bodies on 'device' ('stepped'): body 0
  Asger (left out while he sits: 'Crewman.buckled'), then each of
  '_furnishings.looseThings', every frame as long as the real time
  passed, in steps of 'STEP'. 'shown' says where each loose thing is and
  how it is turned from how it rests; 'thuds' counts the meetings begun
  hard and 'loudest' says how hard the loudest of the last frame was
  (m/s, by its heft).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  device: str
  pointCount: int
  thuds: int
  loudest: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, device: str) -> None:
    import warp as wp

    from . import _cabin_kernels
    preloadedCabin(device)
    self.wp, self.kernels, self.device = wp, _cabin_kernels, device
    self.thuds, self.loudest, self._present = 0, 0.0, 0
    things = looseThings()
    rest = [_turnOf(axes) for _, _, _, axes, _ in things]
    self._rest = numpy.array(rest, numpy.float64)
    self._places = numpy.array([(0.0, 0.0, 0.0)] + [
      middle for _, middle, _, _, _ in things], numpy.float64)
    self._turns = numpy.array([(1.0, 0.0, 0.0, 0.0)] + rest,
                              numpy.float64)
    halves = [(0.0, 0.0, 0.0)] + [half for _, _, half, _, _ in things]
    masses = [HEFT] + [mass for _, _, _, _, mass in things]
    inertias = [(1.0, 1.0, 1.0)] + [
      (m / 3.0 * (h[1] ** 2 + h[2] ** 2), m / 3.0 * (h[0] ** 2 + h[2] ** 2),
       m / 3.0 * (h[0] ** 2 + h[1] ** 2)) for (_, _, h, _, m) in things]
    owners, locals_, radii = [], [], []
    for along, radius in BALLS:
      owners.append(0)
      locals_.append((0.0, 0.0, along))
      radii.append(radius)
    skin = _cabin_kernels.SKIN_SIZE
    for k, (_, _, half, _, _) in enumerate(things):
      inset = tuple(h - skin for h in half)
      for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
          for sz in (-1.0, 1.0):
            owners.append(k + 1)
            locals_.append((sx * inset[0], sy * inset[1], sz * inset[2]))
            radii.append(skin)
    self.pointCount = len(owners)
    held = solids()
    vec3, quat = wp.vec3, wp.quat
    self.places = self._sent(self._places, vec3)
    self.turns = self._sent(_warpQuats(self._turns), quat)
    self.velocities = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.spins = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.masses = self._sent(masses, wp.float32)
    self.halves = self._sent(halves, vec3)
    self.inertias = self._sent(inertias, vec3)
    self.owners = self._sent(owners, wp.int32)
    self.locals = self._sent(locals_, vec3)
    self.radii = self._sent(radii, wp.float32)
    self.solidMiddles = self._sent([m for m, _, _ in held], vec3)
    self.solidTurns = self._sent(_warpQuats(numpy.array(
      [_turnOf(axes) for _, _, axes in held], numpy.float64)), quat)
    self.solidHalves = self._sent([h for _, h, _ in held], vec3)
    self.touched = self._sent([0] * len(owners), wp.int32)
    self.pushes = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.twists = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.asger = self._sent(numpy.zeros((2, 3)), vec3)
    self.met = self._sent(numpy.zeros((2, 3)), vec3)
    self.thudding = self._sent([0.0, 0.0], wp.float32)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stepped(self, seconds: float, accelerometer: Accelerometer,
              crewman: Crewman, enchanted: float, want: tuple) -> None:
    """The 'stepped' method moves the cabin's bodies 'seconds' s on (real
    time), feeling what 'accelerometer' read and the enchantment's
    'enchanted' g toward the floor; Asger ('crewman') too, unless he
    sits, his legs as 'want' asks ('Crewman.wantOf' and a leap: the
    velocity wanted, walking, wanting, the leap's velocity)."""
    if seconds <= 0.0:
      return
    wp, kernels, device = self.wp, self.kernels, self.device
    present = 0 if crewman.buckled else 1
    if present and not self._present:
      self._asgerSent(crewman)
    self._present = present
    wanted, walking, wanting, leap = want
    steps = max(1, min(MOST_STEPS, math.ceil(seconds / STEP)))
    step = seconds / steps
    vec3 = wp.vec3
    up = vec3(*crewman.up)
    felt, turning = vec3(*accelerometer.felt), vec3(*accelerometer.turning)
    speeding = vec3(*accelerometer.speeding)
    pull = vec3(0.0, 0.0, -enchanted * G0)
    still = vec3(0.0, 0.0, 0.0)
    for k in range(steps):
      wp.launch(kernels.pressed, self.pointCount, [
        self.places, self.turns, self.velocities, self.spins, self.masses,
        self.halves, self.owners, self.locals, self.radii,
        self.solidMiddles, self.solidTurns, self.solidHalves, self.touched,
        self.pushes, self.twists, self.asger, self.thudding, up, present,
        1 if (walking or wanting) else 0], [], [], [], device)
      wp.launch(kernels.moved, len(self._places), [
        self.places, self.turns, self.velocities, self.spins, self.masses,
        self.inertias, self.pushes, self.twists, self.asger, self.met,
        felt, turning, speeding, pull, vec3(*wanted),
        vec3(*leap) if k == 0 else still, up, int(walking), int(wanting),
        present, float(step)], [], [], [], device)
    self._taken(crewman, present)

  def shown(self, ) -> tuple:
    """The 'shown' method returns each loose thing's place (its middle,
    the vessel's own axes) and turn from how it rests (w x y z)."""
    turns = _products(self._turns[1:], _inverses(self._rest))
    return tuple((tuple(p), tuple(t)) for p, t in zip(
      self._places[1:].tolist(), turns.tolist()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _asgerSent(self, crewman: Crewman) -> None:
    """Puts Asger's body where he got up: its middle, its velocity."""
    wp = self.wp
    for target, value in ((self.places, crewman.middle),
                          (self.velocities, crewman.velocity)):
      wp.copy(target, self._sent([value], wp.vec3), 0, 0, 1)

  def _taken(self, crewman: Crewman, present: int) -> None:
    """Takes the bodies back from the device: the loose things' places
    and turns, Asger's body (if he is up), the thuds."""
    self._places = self.places.numpy().astype(numpy.float64)
    x, y, z, w = self.turns.numpy().astype(numpy.float64).T
    self._turns = numpy.stack([w, x, y, z], 1)
    if present:
      met = self.met.numpy().astype(numpy.float64)
      crewman.placed(tuple(self._places[0].tolist()), tuple(
        self.velocities.numpy()[0].astype(numpy.float64).tolist()),
                     int(round(met[0][0])), tuple(met[1].tolist()))
    count, loudest = self.thudding.numpy().tolist()
    self.thuds += int(round(count))
    self.loudest = float(loudest)
    self.thudding.zero_()

  def _sent(self, values: object, kind: object) -> object:
    """Returns 'values' as a Warp array of 'kind' on the device."""
    wp = self.wp
    host = numpy.ascontiguousarray(numpy.asarray(values, numpy.int32 if (
      kind is wp.int32) else numpy.float32))
    return wp.array(host, kind, None, None, None, None, self.device)


def restingLoose() -> tuple:
  """Returns the loose things as they rest, as 'CabinWorld.shown' says
  where they are: each its middle and no turn."""
  return tuple((middle, (1.0, 0.0, 0.0, 0.0))
               for _, middle, _, _, _ in looseThings())


def _turnOf(axes: tuple) -> tuple:
  """Returns the turn (w x y z) taking the vessel's axes to 'axes' (its
  right, up, out)."""
  return quaternionOf(tuple((axes[0][k], axes[1][k], axes[2][k])
                            for k in range(3)))


def _warpQuats(turns: numpy.ndarray) -> numpy.ndarray:
  """Returns turns (w x y z rows) as Warp takes them (x y z w)."""
  turns = numpy.asarray(turns, numpy.float64)
  return numpy.stack([turns[:, 1], turns[:, 2], turns[:, 3], turns[:, 0]],
                     1)


def _inverses(turns: numpy.ndarray) -> numpy.ndarray:
  """Returns unit turns (w x y z rows) turned back."""
  out = numpy.array(turns, numpy.float64)
  out[:, 1:] *= -1.0
  return out


def _products(one: numpy.ndarray, two: numpy.ndarray) -> numpy.ndarray:
  """Returns the turns 'one' after 'two', row by row (w x y z)."""
  w1, x1, y1, z1 = one.T
  w2, x2, y2, z2 = two.T
  return numpy.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                      w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                      w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                      w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], 1)
