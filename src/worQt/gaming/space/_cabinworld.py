"""
CabinWorld is what moves in the cabin (user, 2026-11-17: "when can Asger
get up and float around in micro-gravity?"; the loose things: "FAFO
rules"): Asger out of his chair and the loose things, stepped on a
device of Warp's by '_cabin_kernels', in the vessel's own axes, feeling
what the vessel feels there ('Accelerometer'). Always at real time: a
warp of the flight's time is not the cabin's (it would be a hundred
thousand of its steps a frame).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import numpy

from ._cabinsolids import solids
from ._crewman import HEFT, MIDDLE
from ._furnishings import looseThings
from ._turns import cross, quaternionOf

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._accelerometer import Accelerometer
  from ._crewman import Crewman

#  A step, s (the meetings' springs ring at 250 rad/s: 0.2 rad a step),
#  and at most this many a frame.
STEP = 1.0 / 1200.0
MOST_STEPS = 120
#  The solids' places kept for the space station's (docked: its
#  elevators' cages, its garden's furniture) or the launch tower's (its
#  stairs' steps), after the cabin's own; Asger's box after them.
STATION_SLOTS = 320
#  Where a solid not there is kept (far from everything), m.
AWAY = (0.0, 0.0, -1e4)
#  His legs wanting nothing ('stepped''s 'want': no velocity, not
#  walking, not wanting, no leap; the window's for Asger dead, the
#  user's let's play, 2026-11-18: its own, of five, raised every frame).
STILL = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0))


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
  CabinWorld steps the cabin's bodies on 'device' ('stepped'): Asger's
  box a frame at a time ('_cabin_kernels.walked': left out while he
  sits), his box then a moving solid for the loose things (the last
  solid's slot); each of its loose things ('things'; the cabin's:
  '_furnishings.looseThings', none since the user's "remove them
  completely", 2026-11-18; bodies from 1: body 0 is kept empty) every
  frame as long as the real time passed, in steps of 'STEP' (none, no
  steps: Asger's box alone, a step a frame). Docked to the space
  station ('stationed') its rooms join the cabin's and its solids
  (moving, some) the cabin's own. 'shown' says where each loose thing
  is and
  how it is turned from how it rests; 'thuds' counts the meetings begun
  hard and 'loudest' says how hard the loudest of the last frame was
  (m/s, by its heft); 'landed' how fast Asger met anything the last
  frame (m/s: it may hurt him); 'lastSteps' and 'lastMs' how many steps
  the last frame took and how long, ms (the debug view's).

  What pushes Asger and the loose things pushes back as hard what
  pushed them (user, 2026-11-18: "PHYSICS MUST BE REAL"; his jetpack
  blows the air, which carries its push to the walls): 'pushedBack' is
  what the last frame's loose things pushed the vessel by, and his
  chair stopping him as he sat down, its push (N s) and the twist about
  its middle (N m s), its own axes; 'asgerPushed' what Asger out of his
  chair pushed back likewise (the vessel's while he is in its cabin;
  outside it, on the pad, the tower's and the ground's).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  device: str
  things: tuple
  pointCount: int
  thuds: int
  loudest: float
  landed: float
  lastSteps: int
  lastMs: float
  pushedBack: tuple
  asgerPushed: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, device: str, things: tuple = None) -> None:
    import warp as wp

    from . import _cabin_kernels
    preloadedCabin(device)
    self.wp, self.kernels, self.device = wp, _cabin_kernels, device
    self.thuds, self.loudest, self.landed, self._present = 0, 0.0, 0.0, 0
    self.lastSteps, self.lastMs = 0, 0.0
    self.pushedBack = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    self.asgerPushed = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    self._last = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    self.docked, self.outside = False, 0
    things = looseThings() if things is None else tuple(things)
    self.things = things
    rest = [_turnOf(axes) for _, _, _, axes, _ in things]
    self._rest = numpy.array(rest, numpy.float64).reshape(-1, 4)
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
    self._held = len(held)
    vec3, quat = wp.vec3, wp.quat
    self.places = self._sent(self._places, vec3)
    self.turns = self._sent(_warpQuats(self._turns), quat)
    self._velocities = numpy.zeros((len(masses), 3))
    self.velocities = self._sent(self._velocities, vec3)
    self.spins = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.masses = self._sent(masses, wp.float32)
    self.halves = self._sent(halves, vec3)
    self.inertias = self._sent(inertias, vec3)
    self.owners = self._sent(owners, wp.int32)
    self.locals = self._sent(locals_, vec3)
    self.radii = self._sent(radii, wp.float32)
    away = [AWAY] * (STATION_SLOTS + 1)
    self.own = self._held + STATION_SLOTS
    self._middles = numpy.array([m for m, _, _ in held] + away,
                                numpy.float64)
    self._solidTurns = numpy.array([_turnOf(axes) for _, _, axes in held]
                                   + [(1.0, 0.0, 0.0, 0.0)] * (
                                     STATION_SLOTS + 1), numpy.float64)
    self._halves = numpy.array([h for _, h, _ in held] + [
      (0.1, 0.1, 0.1)] * (STATION_SLOTS + 1), numpy.float64)
    self.solidMiddles = self._sent(self._middles, vec3)
    self.solidTurns = self._sent(_warpQuats(self._solidTurns), quat)
    self.solidHalves = self._sent(self._halves, vec3)
    self.solidVelocities = self._sent(numpy.zeros((len(self._middles), 3)),
                                      vec3)
    self.ways = self._sent(numpy.zeros((4, 3)), vec3)
    self.touched = self._sent([0] * len(owners), wp.int32)
    self.pushes = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.twists = self._sent(numpy.zeros((len(masses), 3)), vec3)
    self.asger = self._sent(numpy.zeros((2, 3)), vec3)
    self.thudding = self._sent([0.0, 0.0], wp.float32)
    self.landing = self._sent([0.0], wp.float32)
    self.body = self._sent(numpy.zeros((1, 3)), vec3)
    self.bodyVelocity = self._sent(numpy.zeros((1, 3)), vec3)
    self.ground = self._sent(numpy.zeros((1, 3)), vec3)
    self.contact = self._sent([(1.0, 1.0, 0.0)], vec3)
    self.bodyMet = self._sent(numpy.zeros((3, 3)), vec3)
    self.near = self._sent([0] * _cabin_kernels.NEAR_MOST, wp.int32)
    self.nearCount = self._sent([0], wp.int32)
    self.reaction = self._sent(numpy.zeros((4, 3)), vec3)
    reaches = [0.0] * len(masses)
    for owner, local, radius in zip(owners, locals_, radii):
      reaches[owner] = max(reaches[owner], math.hypot(*local) + radius)
    self.reaches = self._sent(reaches, wp.float32)
    self.bodyNear = wp.zeros((len(masses), _cabin_kernels.BODY_NEAR_MOST),
                             wp.int32, device)
    self.bodyNearCount = self._sent([0] * len(masses), wp.int32)
    self._pressed, self._moved, self._walked, self._nearby = (
      self._recorded())
    self._bodiesNear = wp.launch(
      _cabin_kernels.bodiesNear, (len(masses), len(self._middles)), [
        self.places, self.velocities, self.reaches, self.solidMiddles,
        self.solidHalves, self.solidVelocities, self.bodyNear,
        self.bodyNearCount, 0.0, 1.0 / 60.0], [], [], [], device, None,
      False, False, True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stepped(self, seconds: float, accelerometer: Accelerometer,
              crewman: Crewman, want: tuple, gun: tuple = None,
              jet: tuple = (0.0, 0.0, 0.0)) -> None:
    """The 'stepped' method moves the cabin's bodies 'seconds' s on (real
    time), feeling what 'accelerometer' read; Asger ('crewman') too,
    unless he sits, his legs as 'want' asks ('Crewman.wantOf' and a leap:
    the velocity wanted, walking, wanting, the leap's velocity); the
    Grav-Gun's push ('gun': its force on Asger over his mass, m/s², the
    loose thing it acts on (its index in 'shown', None: none) and its
    force on that over its mass; None: no push) and his jetpack's
    ('jet': its force on him over his mass, m/s²), its own axes; and
    says what they pushed back by ('pushedBack', 'asgerPushed')."""
    self.pushedBack = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    self.asgerPushed = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    if seconds <= 0.0:
      return
    began = time.perf_counter()
    wp = self.wp
    present = 0 if crewman.sitting else 1
    if present and not self._present:
      self._asgerSent(crewman)
    seated = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    if self._present and not present:
      seated = self._seated()
      self._asgerAway()
    self._present = present
    self.reaction.zero_()
    vec3 = wp.vec3
    felt, turning, speeding = (vec3(*accelerometer.felt),
                               vec3(*accelerometer.turning),
                               vec3(*accelerometer.speeding))
    onAsger, thing, onThing = gun or ((0.0, 0.0, 0.0), None,
                                      (0.0, 0.0, 0.0))
    if present:
      wanted, walking, wanting, leap = want
      walked = self._walked
      for name, value in (
          ('felt', felt), ('turning', turning), ('speeding', speeding),
          ('wanted', vec3(*wanted)), ('leap', vec3(*leap)),
          ('up', vec3(*crewman.up)), ('walking', int(walking)),
          ('wanting', int(wanting)), ('gun', vec3(*onAsger)),
          ('jet', vec3(*jet)),
          ('crouch', 1 if crewman.crouching else 0),
          ('docked', 1 if self.docked else 0), ('outside', self.outside),
          ('seconds', float(seconds))):
        walked.set_param_by_name(name, value)
      nearby = self._nearby
      for name, value in (
          ('up', vec3(*crewman.up)), ('seconds', float(seconds)),
          ('margin', math.hypot(*crewman.velocity) * seconds + 1.0)):
        nearby.set_param_by_name(name, value)
      nearby.launch()
      walked.launch()
    if not self.pointCount:
      self._taken(crewman, present, seated)
      self.lastSteps = present
      self.lastMs = 1e3 * (time.perf_counter() - began)
      return
    steps = max(1, min(MOST_STEPS, math.ceil(seconds / STEP)))
    step = seconds / steps
    self.bodyNearCount.zero_()
    near = self._bodiesNear
    near.set_param_by_name('felt', float(math.sqrt(sum(
      x * x for x in accelerometer.felt))))
    near.set_param_by_name('seconds', float(seconds))
    near.launch()
    moved = self._moved
    for name, value in (('felt', felt), ('turning', turning),
                        ('speeding', speeding), ('step', float(step)),
                        ('gunBody', -1 if thing is None else thing + 1),
                        ('gun', vec3(*onThing))):
      moved.set_param_by_name(name, value)
    for k in range(steps):
      self._pressed.set_param_by_name('elapsed', float(k * step))
      self._pressed.launch()
      moved.launch()
    self._taken(crewman, present, seated)
    self.lastSteps = steps
    self.lastMs = 1e3 * (time.perf_counter() - began)

  def stationed(self, docked: bool, ways: tuple, boxes: tuple) -> None:
    """The 'stationed' method joins the space station's rooms to the
    cabin's ('docked'; its shafts out along 'ways', the docked rocket's
    own axes) and puts its solids ('boxes': each its middle, half sizes,
    turn (w x y z) and velocity, where it is as the frame begins: the
    world moves it on through the frame; at most 'STATION_SLOTS') in the
    world, the rest away; undocked, its rooms not joined (the boxes may
    be the launch tower's then, '_launchtower')."""
    if len(boxes) > STATION_SLOTS:
      raise ValueError('%d station solids, room for %d' % (
        len(boxes), STATION_SLOTS))
    wp = self.wp
    first = self._held
    count = STATION_SLOTS
    middles = numpy.array([AWAY] * count, numpy.float64)
    halves = numpy.full((count, 3), 0.1)
    turns = numpy.tile([1.0, 0.0, 0.0, 0.0], (count, 1))
    velocities = numpy.zeros((count, 3))
    for k, (middle, half, turn, velocity) in enumerate(boxes):
      middles[k], halves[k], turns[k], velocities[k] = (middle, half,
                                                        turn, velocity)
    if docked:
      self.ways.assign(numpy.asarray(ways, numpy.float32))
    self._middles[first:first + count] = middles
    self._halves[first:first + count] = halves
    self._solidTurns[first:first + count] = turns
    self.solidMiddles.assign(self._middles.astype(numpy.float32))
    self.solidHalves.assign(self._halves.astype(numpy.float32))
    self.solidTurns.assign(_warpQuats(self._solidTurns).astype(
      numpy.float32))
    every = numpy.zeros((len(self._middles), 3), numpy.float32)
    every[first:first + count] = velocities
    self.solidVelocities.assign(every)
    self.docked = bool(docked)
    if self._pressed is not None:
      self._pressed.set_param_by_name('docked', 1 if docked else 0)

  def walked(self, outside: int) -> None:
    """The 'walked' method joins the rooms outside the rocket on the pad
    to the cabin's ('_walkway.Walkway.outside': one, the walkway's
    tunnel and the tower's platform; two, the doorway)."""
    if int(outside) != self.outside:
      self.outside = int(outside)
      if self._pressed is not None:
        self._pressed.set_param_by_name('outside', self.outside)

  def solidBoxes(self, ) -> tuple:
    """The 'solidBoxes' method returns the solids in the world now, as
    the frame began (the cabin's, the tower's or the station's; not his
    own box, none put away): their middles, half sizes and axes as
    columns (numpy arrays (n, 3), (n, 3), (n, 3, 3))."""
    keep = numpy.ones(len(self._middles), bool)
    keep[self.own] = False
    keep &= self._middles[:, 2] > AWAY[2] + 1.0
    w, x, y, z = self._solidTurns[keep].T
    axes = numpy.stack([
      numpy.stack([1 - 2 * (y * y + z * z), 2 * (x * y + w * z),
                   2 * (x * z - w * y)], 1),
      numpy.stack([2 * (x * y - w * z), 1 - 2 * (x * x + z * z),
                   2 * (y * z + w * x)], 1),
      numpy.stack([2 * (x * z + w * y), 2 * (y * z - w * x),
                   1 - 2 * (x * x + y * y)], 1)], 2)
    return self._middles[keep], self._halves[keep], axes

  def movingOf(self, index: int) -> tuple:
    """The 'movingOf' method returns how fast loose thing 'index' (as
    'shown' counts them) moved as the last frame ended, m/s (the
    vessel's own axes)."""
    return tuple(self._velocities[index + 1].tolist())

  def kept(self, ) -> dict:
    """The 'kept' method returns what a saved game keeps of the loose
    things ('_savegame'): each body's place, turn (w x y z), velocity and
    spin, the vessel's own axes."""
    return {'places': self._places.tolist(),
            'turns': self._turns.tolist(),
            'velocities': self.velocities.numpy().astype(
              numpy.float64).tolist(),
            'spins': self.spins.numpy().astype(numpy.float64).tolist()}

  def keptFrom(self, kept: dict) -> None:
    """The 'keptFrom' method puts the loose things back as 'kept' had
    them (a saved game), Asger's box sent anew with the next step (if he
    is up then), the station's and the tower's solids put away (the
    window puts them back as it finds itself)."""
    count = len(self._places)
    shapes = {name: numpy.asarray(kept[name], numpy.float64)
              for name in ('places', 'turns', 'velocities', 'spins')}
    for name, values in shapes.items():
      if len(values) != count:
        raise ValueError('the save has %d loose bodies, the cabin %d'
                         % (len(values), count))
    self._places, self._turns = shapes['places'], shapes['turns']
    self._velocities = shapes['velocities']
    self.places.assign(self._places.astype(numpy.float32))
    self.turns.assign(_warpQuats(self._turns).astype(numpy.float32))
    self.velocities.assign(self._velocities.astype(numpy.float32))
    self.spins.assign(shapes['spins'].astype(numpy.float32))
    self.teleported()

  def teleported(self, ) -> None:
    """The 'teleported' method sends Asger's box anew with the next step
    from where he is then (a saved game loaded, the debug menu's warp;
    if he is up then), the station's and the tower's solids put away
    (the window puts them back as it finds itself)."""
    self.stationed(False, (), ())
    self._asgerAway()
    self._present = 0
    self._last = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))

  def shown(self, ) -> tuple:
    """The 'shown' method returns each loose thing's place (its middle,
    the vessel's own axes) and turn from how it rests (w x y z)."""
    turns = _products(self._turns[1:], _inverses(self._rest))
    return tuple((tuple(p), tuple(t)) for p, t in zip(
      self._places[1:].tolist(), turns.tolist()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _recorded(self, ) -> tuple:
    """Returns the two kernels' launches recorded once on the arrays
    (each step replays them, only the frame's numbers set anew: a
    launch packed afresh costs some 0.3 ms of Python)."""
    wp, kernels, device = self.wp, self.kernels, self.device
    zero = wp.vec3(0.0, 0.0, 0.0)
    nearby = wp.launch(kernels.nearby, len(self._middles), [
      self.solidMiddles, self.solidHalves, self.solidVelocities, self.body,
      self.near, self.nearCount, wp.vec3(0.0, 0.0, 1.0), 0.0, self.own,
      1.0 / 60.0], [], [], [], device, None, False, False, True)
    walked = wp.launch(kernels.walked, 1, [
      self.body, self.bodyVelocity, self.ground, self.contact,
      self.bodyMet,
      self.thudding, self.solidMiddles, self.solidTurns, self.solidHalves,
      self.solidVelocities, self.ways, self.near, self.nearCount,
      self.reaction, zero, zero, zero, zero, zero,
      wp.vec3(0.0, 0.0, 1.0), 0, 0, zero, zero, 0, 0, 0, self.own,
      1.0 / 60.0], [], [], [], device, None, False, False, True)
    pressed = wp.launch(kernels.pressed, self.pointCount, [
      self.places, self.turns, self.velocities, self.spins, self.masses,
      self.halves, self.owners, self.locals, self.radii,
      self.solidMiddles, self.solidTurns, self.solidHalves,
      self.solidVelocities, self.ways, self.bodyNear,
      self.bodyNearCount, self.touched,
      self.pushes, self.twists, self.asger, self.thudding, self.landing,
      zero, 0, 0, 0, 0, 0.0], [], [], [], device, None, False, False,
                      True)
    moved = wp.launch(kernels.moved, len(self._places), [
      self.places, self.turns, self.velocities, self.spins, self.masses,
      self.inertias, self.pushes, self.twists, self.asger, self.reaction,
      zero, zero, zero, -1, zero, 0.0], [], [], [], device, None, False,
      False, True)
    return pressed, moved, walked, nearby

  def _asgerSent(self, crewman: Crewman) -> None:
    """Puts Asger's box where he got up: its middle, its velocity,
    standing on the floor, not crouched."""
    wp = self.wp
    self.body.assign(numpy.asarray([crewman.soles()], numpy.float32))
    self.ground.zero_()
    self.bodyVelocity.assign(numpy.asarray([crewman.velocity],
                                           numpy.float32))
    self.contact.assign(numpy.asarray([(1.0, 1.0, 0.0)], numpy.float32))

  def _asgerAway(self, ) -> None:
    """Takes Asger's box out of the loose things' way (he sits)."""
    own = self.own
    middles = self.solidMiddles.numpy()
    velocities = self.solidVelocities.numpy()
    middles[own], velocities[own] = AWAY, (0.0, 0.0, 0.0)
    self.solidMiddles.assign(middles)
    self.solidVelocities.assign(velocities)

  def _seated(self, ) -> tuple:
    """Returns what Asger sitting down pushes the vessel by: his chair
    stops him as he moved at the last frame's end (his push, N s, and
    its twist about the vessel's middle, N m s, its own axes)."""
    middle, velocity = self._last
    moving = tuple(HEFT * v for v in velocity)
    return moving, cross(middle, moving)

  def _taken(self, crewman: Crewman, present: int,
             seated: tuple) -> None:
    """Takes the bodies back from the device: the loose things' places
    and turns, Asger's body (if he is up), the thuds, and what they
    pushed the vessel by (with what his chair took, 'seated')."""
    back = self.reaction.numpy().astype(numpy.float64)
    self.asgerPushed = tuple(tuple(row.tolist()) for row in back[:2])
    self.pushedBack = tuple(tuple((row + numpy.asarray(extra)).tolist())
                            for row, extra in zip(back[2:], seated))
    self._places = self.places.numpy().astype(numpy.float64)
    self._velocities = self.velocities.numpy().astype(numpy.float64)
    x, y, z, w = self.turns.numpy().astype(numpy.float64).T
    self._turns = numpy.stack([w, x, y, z], 1)
    self.landed = 0.0
    if present:
      met = self.bodyMet.numpy().astype(numpy.float64)
      contact = self.contact.numpy()[0]
      soles = self.body.numpy()[0].astype(numpy.float64).tolist()
      middle = tuple(s + MIDDLE * u for s, u in zip(soles, crewman.up))
      velocity = tuple(self.bodyVelocity.numpy()[0].astype(
        numpy.float64).tolist())
      self._last = middle, velocity
      crewman.placed(middle, velocity, int(round(met[0][0])),
                     tuple(met[1].tolist()), bool(contact[2] > 0.5),
                     float(met[0][1]), tuple(met[2].tolist()))
      self.landed = float(met[0][2])
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


def restingLoose(things: tuple = None) -> tuple:
  """Returns the loose things ('things'; None: the cabin's,
  '_furnishings.looseThings') as they rest, as 'CabinWorld.shown' says
  where they are: each its middle and no turn."""
  things = looseThings() if things is None else things
  return tuple((middle, (1.0, 0.0, 0.0, 0.0))
               for _, middle, _, _, _ in things)


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
