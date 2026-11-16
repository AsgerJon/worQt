"""
World is a world in the sandbox (user, 2026-11-15: "World is the well
defined both here and in minecraft. This has to be its own class."):
what is fixed in it, what is spawned into it, and the physics that
steps it, on a thread of its own, under its universe's constants.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import threading
import time
from typing import TYPE_CHECKING

from worQt.phys._assembly import Assembly, Contact, Fixed

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._universe import Universe

#  A frame, s: each step covers the real time passed since the last, at
#  least half a frame (it waits for that) and at most two; the world's
#  share of real time is said once under 'BEHIND'.
FRAME = 1.0 / 60.0
BEHIND = 0.98


class World:
  """
  World holds a world: the 'universe' it obeys, its 'ground' (a phys
  'Ground', or None: the void), every body in it ('assembly', where each
  is: 'states', how each is drawn: 'drawn', by a key of 'looks') and
  the 'actors' acting in it each step (an avatar, a vehicle: each with
  'acted(states, seconds)', changing the list of states before the
  step) and the 'vehicles' in it ('addVehicle': each puts its bodies
  in). A drawn body may be dressed ('dressedWith': meshes of its own,
  each its look: a model's parts, 'dressed') instead of drawn as its
  shape, and carry parts moving on it ('posedWith': each drawn where a
  call of its owner's puts it every frame, 'posed': a valve gear).
  Bodies are 'fixed' (held still: the world's own, their indices in
  'still') or 'spawned' (free); bodies already in are joined by a
  connection ('connected': a tie, an axlebox) and let go again
  ('loosened'). Once 'start'ed it steps itself on a
  thread of its own, each step as long as the real time passed, never
  slowed on purpose; an
  error stops it, said in 'trouble'. Below 'lowest' m a body has fallen
  out of the world (None: nothing falls out).

  A subclass says what the world is: 'solverOf' (the physics stepping
  its assembly), 'spawnPoint' (where an avatar enters), 'fixtures' (what
  is drawn fixed in it, by look), 'LOOKS' (each look's colour, 0 to 255
  a channel, metalness and roughness, and maybe a picture file and its
  glow: the world's own; 'looks' holds them and any a spawned thing
  adds) and 'readied' (loading its
  physics, on the world's thread, before the first step).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  LOOKS: dict = {}
  lowest: float = None

  #  Public Variables
  universe: Universe
  ground: object
  assembly: Assembly
  states: tuple
  drawn: dict
  looks: dict
  still: frozenset
  actors: list
  vehicles: list
  peeps: list
  dressed: dict
  posed: dict
  time: float
  trouble: str
  loading: str
  share: float
  took: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, universe: Universe, ground: object = None) -> None:
    self.universe, self.ground = universe, ground
    self.assembly, self.states, self.drawn = Assembly((), ()), (), {}
    self.still, self.looks = frozenset(), dict(self.LOOKS)
    self.actors, self.time, self.trouble = [], 0.0, None
    self.vehicles, self.placings, self.peeps = [], {}, []
    self.dressed, self.posed = {}, {}
    self.loading, self.share, self.took = None, 1.0, 0.0
    self.solver, self._shown = None, (self.assembly, (), 0.0)
    self._lock = threading.RLock()
    self._thread, self._alive = None, False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  REQUIRED METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solverOf(self, ) -> object:
    """The 'solverOf' method returns the physics stepping the world (an
    'advancedAll' of the assembly, its states, seconds and the time)."""
    raise NotImplementedError(type(self).__name__)

  def spawnPoint(self, ) -> tuple:
    """The 'spawnPoint' method returns where an avatar enters the world:
    the point its feet stand on, m, and the way it looks, rad about the
    upright from x."""
    raise NotImplementedError(type(self).__name__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def fixtures(self, ) -> dict:
    """The 'fixtures' method returns what is drawn fixed in the world
    besides its bodies: quads by look (each (n, 4, 6): every corner's
    place, m, and normal, in the world). None here."""
    return {}

  def readied(self, ) -> None:
    """The 'readied' method readies the world's physics on the world's
    own thread, before its first step (compiling kernels: slow). Nothing
    here."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def fixed(self, body: object, state: object, look: str) -> int:
    """The 'fixed' method puts 'body' in the world in 'state', held still
    for good, drawn as 'look', and returns its index."""
    with self._lock:
      return self._added(body, state, (), Fixed, look)

  def spawned(self, body: object, state: object, law: tuple,
              look: str, apart: frozenset = frozenset()) -> int:
    """The 'spawned' method puts 'body' in the world in 'state', free,
    touching every body already in it by 'law' (a 'Contact''s
    stiffness, damping, grip, bristle and its damping) but those in
    'apart' (indices of bodies it can never reach: a cart's tub and the
    track its wheels hold it over), drawn as 'look' (None: not drawn),
    and returns its index."""
    with self._lock:
      return self._added(body, state, law, None, look, apart)

  def dressedWith(self, index: int, parts: tuple, looks: dict) -> None:
    """The 'dressedWith' method draws body 'index' as 'parts' instead of
    its shape: each (rows, indices, look): a mesh about the body's
    centre in its own frame ('Mesh''s rows: place and normal, six numbers
    a corner) and the look it is drawn in, 'looks' adding any it names
    that the world has not ({look: (colour 0-255, metalness,
    roughness)})."""
    with self._lock:
      self.looks.update(looks)
      dressed = dict(self.dressed)
      dressed[index] = tuple(parts)
      self.dressed, self.drawn = dressed, dict(self.drawn)
      self._shown = self.assembly, self.states, self.time

  def posedWith(self, index: int, parts: tuple, looks: dict,
                poser: object) -> None:
    """The 'posedWith' method has body 'index' carry 'parts' moving on
    it (each (rows, indices, look) as 'dressedWith' takes them, about
    the body's centre as they stand at rest), 'looks' adding any it
    names; each frame 'poser(states)' (called on the drawing's thread
    with the world's last states) returns where each part is now, one
    (place, turn) a part in the body's own frame about its centre: the
    part as it stands at rest, turned by 'turn' about that centre, then
    moved by 'place'."""
    with self._lock:
      self.looks.update(looks)
      posed = dict(self.posed)
      posed[index] = (tuple(parts), poser)
      self.posed, self.drawn = posed, dict(self.drawn)
      self._shown = self.assembly, self.states, self.time

  def connected(self, connection: object) -> None:
    """The 'connected' method joins bodies already in the world by
    'connection' (its indices theirs)."""
    with self._lock:
      self.assembly = Assembly(self.assembly.bodies,
                               self.assembly.connections + (connection,))
      self._shown = self.assembly, self.states, self.time

  def loosened(self, connection: object) -> None:
    """The 'loosened' method takes 'connection' (that very one) out of
    the world; one not in it is refused."""
    with self._lock:
      kept = tuple(c for c in self.assembly.connections
                   if c is not connection)
      if len(kept) == len(self.assembly.connections):
        raise ValueError('that connection is not in the world')
      self.assembly = Assembly(self.assembly.bodies, kept)
      self._shown = self.assembly, self.states, self.time

  def swapped(self, index: int, body: object) -> None:
    """The 'swapped' method makes body 'index' of the world 'body', its
    state, look and connections kept (a part made over: a wheelset off
    its rails taken over as a free body, and back)."""
    with self._lock:
      bodies = list(self.assembly.bodies)
      bodies[index] = body
      self.assembly = Assembly(tuple(bodies), self.assembly.connections)
      self._shown = self.assembly, self.states, self.time

  def addVehicle(self, vehicle: object) -> None:
    """The 'addVehicle' method puts 'vehicle' in the world: its bodies
    and connections ('placed'), then among the 'vehicles', where they
    were put kept ('placings': a vehicle fallen out of the world is put
    back there)."""
    with self._lock:
      vehicle.placed(self)
      self.vehicles.append(vehicle)
      self.placings[id(vehicle)] = {index: self.states[index]
                                    for index in vehicle.bodies}

  def addFourthPeep(self, peep: object) -> None:
    """The 'addFourthPeep' method puts 'peep' (a 'FourthPeep': a lever)
    in the world: among its 'peeps' the player can use, and acting each
    step (the hand moving it) before those added after it."""
    with self._lock:
      self.peeps.append(peep)
      self.actors.append(peep)

  def addActor(self, actor: object) -> None:
    """The 'addActor' method has 'actor' act in the world each step,
    after those already acting."""
    with self._lock:
      self.actors.append(actor)

  def snapshot(self, ) -> tuple:
    """The 'snapshot' method returns the world as the last step left it:
    its assembly, its states and its time, s, taken together."""
    return self._shown

  def start(self, ) -> None:
    """The 'start' method starts the world stepping itself on a thread
    of its own."""
    if self._thread is not None:
      raise RuntimeError('the world is already running')
    self._alive = True
    self._thread = threading.Thread(target=self._run, daemon=True)
    self._thread.start()

  def stop(self, ) -> None:
    """The 'stop' method stops the world's stepping and waits for its
    thread to end."""
    self._alive = False
    if self._thread is not None:
      self._thread.join()
    self._thread = None

  def advanced(self, seconds: float) -> None:
    """The 'advanced' method steps the world on 'seconds' at once, its
    actors acting first: on the caller's thread (a test's), never while
    it is running."""
    if self._thread is not None:
      raise RuntimeError('the world is running on its own thread')
    if self.solver is None:
      self.readied()
      self.solver = self.solverOf()
    with self._lock:
      self._stepped(seconds)

  def warningText(self, ) -> str:
    """The 'warningText' method returns what is wrong with how the world
    runs ('': nothing): stopped and why, loading its physics, or the
    physics not keeping up (the world's share of real time under
    'BEHIND')."""
    if self.trouble is not None:
      return 'the physics stopped: %s' % self.trouble
    if self.loading is not None:
      return 'loading the physics for %s' % self.loading
    if self.share < BEHIND:
      return ('the physics cannot keep up: the world runs at %.0f %% of '
              'real time' % (100.0 * self.share))
    return ''

  def statusText(self, ) -> str:
    """The 'statusText' method returns a line saying how the world runs:
    stopped and why, loading its physics, or its time and its share of
    real time when under 'BEHIND'."""
    if self.trouble is not None:
      return 'the world stopped: %s' % self.trouble
    if self.loading is not None:
      return 'loading the physics for %s (a few seconds after a change)' % (
        self.loading)
    text = '%.2f s, a step %.1f ms' % (self.time, 1000.0 * self.took)
    if self.share < BEHIND:
      text += ', at %.0f %% of real time' % (100.0 * self.share)
    return text

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _added(self, body: object, state: object, law: tuple,
             holding: object, look: str,
             apart: frozenset = frozenset()) -> int:
    """Returns the index of 'body' added in 'state': held by 'holding'
    (a connection of its index), or touching every body there by
    'law' but those 'apart'."""
    index = len(self.assembly.bodies)
    connections = self.assembly.connections + (
      (holding(index),) if holding is not None else tuple(
        Contact(other, index, *law) for other in range(index)
        if other not in apart))
    self.assembly = Assembly(self.assembly.bodies + (body,), connections)
    self.states = tuple(self.states) + (state,)
    if holding is not None:
      self.still = self.still | {index}
    if look is not None:
      drawn = dict(self.drawn)
      drawn[index] = look
      self.drawn = drawn
    self._shown = self.assembly, self.states, self.time
    return index

  def _stepped(self, seconds: float) -> None:
    """Steps the world on 'seconds': its actors act, the physics steps;
    a body turned non-finite is refused loudly (those held still never
    move: not looked at)."""
    states = list(self.states)
    for actor in self.actors:
      actor.acted(states, seconds)
    self._fallenBack(states)
    stepped = tuple(self.solver.advancedAll(self.assembly, tuple(states),
                                            seconds, self.time))
    still = self.still
    for index, state in enumerate(stepped):
      if index in still:
        continue
      if not all(math.isfinite(x) for x in state.place + state.velocity):
        raise ValueError('body %d turned non-finite at %.3f s' % (
          index, self.time))
    self.states, self.time = stepped, self.time + seconds
    self._shown = self.assembly, self.states, self.time

  def _fallenBack(self, states: list) -> None:
    """Puts each riderless vehicle fallen below 'lowest' back where it
    was put (user, 2026-11-16: a minecart rolled off the end of the
    track, previews/wiley_coyote_lol.png), made as it was made
    ('restored': a derailed cart back on its rails)."""
    if self.lowest is None:
      return
    for vehicle in self.vehicles:
      if vehicle.rider is None and (
          states[vehicle.frame].place[2] < self.lowest):
        for index, state in self.placings[id(vehicle)].items():
          states[index] = state
        vehicle.restored()

  def _run(self, ) -> None:
    """Readies the physics, then steps the world until stopped: each
    step as long as the real time passed (half a frame at least, two at
    most), but no longer than the physics works out in two frames (the
    world then runs slower than real time: 'share'). An error stops
    it, said in 'trouble'."""
    try:
      self.readied()
      self.solver = self.solverOf()
    except Exception as error:
      self.trouble = '%s: %s' % (type(error).__name__, error)
      return
    last, cost = time.perf_counter(), 0.0
    while self._alive:
      now = time.perf_counter()
      passed = now - last
      if passed < 0.5 * FRAME:
        time.sleep(0.5 * FRAME - passed)
        continue
      last, real = now, min(passed, 2.0 * FRAME)
      if cost > 0.0:
        real = min(real, 2.0 * FRAME / cost)
      try:
        with self._lock:
          self._stepped(real)
      except Exception as error:
        self.trouble = '%s: %s' % (type(error).__name__, error)
        return
      self.took = time.perf_counter() - now
      found = self.took / real
      cost = found if cost == 0.0 else cost + 0.2 * (found - cost)
      self.share += 0.2 * (real / passed - self.share)
