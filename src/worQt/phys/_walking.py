"""
Walking, flying and grabbing, Qt-free. 'Walker' is a person as the
world meets them: a ball where their feet are, carrying all their
weight, walked by their legs (a twist on the ball rolling it on as fast
as they want to go, no harder than the ground grips: on ice they go
nowhere), their eyes 'eye' m over the ground; or flying as in a game's
creative mode, hanging where they stop. 'Grabber' is a tool in their
hands that pulls a body from afar, holds it floating before their eyes
and punts it away, as hard as it can push. Neither flying nor the tool
pushes back on anything: they are not of this world (the walker only
is, as it meets things).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple, TYPE_CHECKING

from ._body import Body, State
from ._poke import hitOf, poked, reachOf
from ._shape import Sphere
from ._vectors import Vector, dot, minus, norm, plus, scaled, solved

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Assembly

#  How near the walker's ball must come to something to stand on it, m;
#  and the ways looked along for it from the ball's middle: straight
#  down and four ways 35 degrees off it (the ball stands on an edge
#  beside it as well as on a face under it).
_STANDING = 0.03
_FEET = ((0.0, 0.0, -1.0),) + tuple(
  (math.sin(math.radians(35.0)) * math.cos(0.5 * math.pi * k),
   math.sin(math.radians(35.0)) * math.sin(0.5 * math.pi * k),
   -math.cos(math.radians(35.0))) for k in range(4))


class Walker(NamedTuple):
  """
  Walker is a person in the world: a ball of 'radius' m where their
  feet are, weighing 'mass' kg (all of them), their eyes 'eye' m over
  the ground; they walk at 'walk' m/s and run at 'run', their legs
  twisting the ball at most 'legs' N m (more than the ground grips, so
  the grip decides); they jump 'jump' m high. Flying they go 'fly' m/s
  along and 'rise' m/s up or down, speeding up or slowing by at most
  'thrust' m/s². The ball is the only body of them the world meets:
  they push what their feet push, and their eyes go through walls.
  """

  radius: float = 0.3
  mass: float = 80.0
  eye: float = 1.65
  walk: float = 1.6
  run: float = 4.0
  legs: float = 600.0
  jump: float = 0.8
  fly: float = 8.0
  rise: float = 5.0
  thrust: float = 30.0

  def body(self, ) -> Body:
    """The 'body' method returns the walker's ball."""
    return _ballOf(self.radius, self.mass)

  def scaled(self, scale: float) -> Walker:
    """The 'scaled' method returns the walker shrunk (or grown) to
    'scale', as a world like ours of that size must be under the same
    gravity to move alike (Froude): lengths times 'scale', speeds times
    its root, masses (and forces) times its cube, twists times its
    fourth power, accelerations as they are. Watched slowed by the root
    of 'scale' it moves as the walker does at full size. But flying,
    gravity no part of it, goes as fast as it seems to at full size,
    for the size the walker seems (user, 2026-11-13: "adjust the
    movement speed relative to the 'perceived' size rather than the
    actual"): 'fly' and 'rise' times 'scale' itself (shrunk 32 mm tall
    by the root, 20 m/s flew as 148 m/s seems at full size)."""
    root = math.sqrt(scale)
    return Walker(self.radius * scale, self.mass * scale ** 3,
                  self.eye * scale, self.walk * root, self.run * root,
                  self.legs * scale ** 4, self.jump * scale,
                  self.fly * scale, self.rise * scale, self.thrust)

  def eyeOf(self, state: State) -> Vector:
    """The 'eyeOf' method returns where the walker's eyes are, their
    ball in 'state'."""
    x, y, z = state.place
    return x, y, z - self.radius + self.eye

  def walked(self, body: Body, state: State, wanted: Vector,
             seconds: float) -> State:
    """The 'walked' method returns the ball in 'state' as the legs leave
    it after twisting it for 'seconds' toward rolling at 'wanted' (m/s,
    along the ground) and toward spinning not at all about the
    upright: its angular momentum about the point it stands on is
    turned toward that of the ball so rolling, by no more than the legs
    twist in the time. The ground's grip then rolls it on: twisted
    harder than the ground grips, it slips. The walker's legs twist
    harder than any grip takes (a ball rolling on takes 1.4 m r of
    twist for each m/s², 600 N m being 18 m/s² for the walker), so the
    ground's grip sets how quickly they speed up and stop, and how hard
    a pull at their middle they stand against: as a person braced on
    their feet, not a ball rolled over. Only the spin changes; it is
    kept awake."""
    r, m = self.radius, body.mass
    i = body.inertia[0][0]
    vx, vy, _ = state.velocity
    wx, wy, wz = state.spin
    held = (i * wx - m * r * vy, i * wy + m * r * vx, i * wz)
    whole = i / r + m * r
    want = (-whole * wanted[1], whole * wanted[0], 0.0)
    gap = minus(want, held)
    size, most = norm(gap), self.legs * seconds
    if size > most:
      gap = scaled(gap, most / size)
    spin = plus(state.spin, scaled(gap, 1.0 / i))
    return State(state.place, state.turn, state.velocity, spin,
                 state.bristles, state.holds, 0.0)

  def strode(self, state: State, wanted: Vector,
             seconds: float) -> State:
    """The 'strode' method returns the ball in 'state' as a game's player
    walks (user, 2026-11-13: "Just fucking walking!", after the legs'
    grip took a second and a half to get going): its velocity along the
    ground turned toward 'wanted' (m/s) by no more than 'thrust' x
    'seconds', up and down left as they were (gravity, a jump, the
    ground's push), and its ball rolling with it (so the ground's grip
    neither drags nor pushes it); kept awake. Nothing is pushed back."""
    vx, vy, vz = state.velocity
    gap = (wanted[0] - vx, wanted[1] - vy)
    size, most = math.hypot(gap[0], gap[1]), self.thrust * seconds
    if size > most:
      gap = (gap[0] * most / size, gap[1] * most / size)
    vx, vy = vx + gap[0], vy + gap[1]
    r = self.radius
    return State(state.place, state.turn, (vx, vy, vz),
                 (-vy / r, vx / r, 0.0), state.bristles, state.holds, 0.0)

  def flown(self, state: State, wanted: Vector, gravity: Vector,
            seconds: float) -> State:
    """The 'flown' method returns the ball in 'state' flying for
    'seconds' toward 'wanted' (m/s): what 'gravity' takes from it in the
    time made up beforehand, so its velocity halfway through the time
    (as it was halfway through the last: now's less half the fall) is
    turned toward 'wanted' by at most 'thrust' x 'seconds' (asked to
    stop it hangs where it is, not creeping up by half a fall each
    time); its spin stopped; kept awake. Nothing is pushed back."""
    halfway = minus(state.velocity, scaled(gravity, 0.5 * seconds))
    gap = minus(wanted, halfway)
    size, most = norm(gap), self.thrust * seconds
    if size > most:
      gap = scaled(gap, most / size)
    velocity = minus(plus(state.velocity, gap), scaled(gravity, seconds))
    return State(state.place, state.turn, velocity, (0.0, 0.0, 0.0),
                 state.bristles, state.holds, 0.0)

  def jumped(self, body: Body, state: State,
             gravity: float = 9.81) -> tuple[State, Vector]:
    """The 'jumped' method returns the ball in 'state' as the legs leave
    it jumping, and the impulse they gave it, N s: straight up, as hard
    as rises 'jump' m under 'gravity' m/s² (what it stood on is pushed
    down as hard)."""
    impulse = (0.0, 0.0, body.mass * math.sqrt(2.0 * gravity * self.jump))
    return poked(body, state, state.place, impulse), impulse

  def standingOn(self, assembly: Assembly, states: tuple[State, ...],
                 index: int, ground: object = None,
                 level: bool = True) -> tuple | None:
    """The 'standingOn' method returns what the walker (body 'index' of
    'assembly' in 'states') stands on: (None, point) the ground (level at
    nought, or the terrain of 'ground' if it has one: on the oval's
    banking, user, 2026-11-15; measured along its normal there; with no
    'ground' and not 'level', none: the void), (body, point) a body, the
    point where it holds them up; None while in the air (their ball
    nowhere within '_STANDING' of anything under it)."""
    state = states[index]
    x, y, z = state.place
    terrain = None if ground is None else ground.terrain
    base, up = (0.0, 1.0) if terrain is None else (
      terrain.heightAt(x, y), terrain.normalAt(x, y)[2])
    floored = level or terrain is not None
    if floored and (z - base) * up <= self.radius + _STANDING:
      return None, (x, y, base)
    near = self.radius + _STANDING
    passed = tuple(
      other for other, (body, there) in enumerate(zip(assembly.bodies,
                                                      states))
      if other == index or body.shape is None
      or (there.place[0] - x) ** 2 + (there.place[1] - y) ** 2
      + (there.place[2] - z) ** 2 > (near + reachOf(body)) ** 2)
    if len(passed) == len(states):
      return None
    for way in _FEET:
      hit = hitOf(assembly, states, state.place, way, passed)
      if hit is not None and norm(minus(hit[1], state.place)) \
          <= self.radius + _STANDING:
        return hit[0], hit[1]
    return None


class Grabber(NamedTuple):
  """
  Grabber is a tool held at the eyes that grabs a body from up to
  'reach' m away along where it points, pulling it in with at most
  'pull' N and no faster than 'fastest' m/s, then holds it 'hold' m
  before the eyes (its near side; its middle further by its own reach)
  with at most 'force' N, settling it there in about 'settle' s and
  turning it as the eyes turn with at most 'twist' N m; with nothing
  held it punts what it points at up to 'punt' m away. A body heavier
  than 'force' lifts it cannot hold up; one held against a wall is
  pushed into it no harder than 'force'. It pushes nothing back.
  """

  reach: float = 10.0
  pull: float = 400.0
  fastest: float = 6.0
  hold: float = 1.0
  force: float = 3000.0
  settle: float = 0.1
  twist: float = 300.0
  punt: float = 4.0

  def scaled(self, scale: float) -> Grabber:
    """The 'scaled' method returns the grabber shrunk (or grown) to
    'scale' as 'Walker.scaled' shrinks its walker: reaches times
    'scale', forces times its cube, speeds and times times its root,
    twists times its fourth power."""
    root = math.sqrt(scale)
    return Grabber(self.reach * scale, self.pull * scale ** 3,
                   self.fastest * root, self.hold * scale,
                   self.force * scale ** 3, self.settle * root,
                   self.twist * scale ** 4, self.punt * scale)

  def holdOf(self, body: Body) -> float:
    """The 'holdOf' method returns how far before the eyes the middle
    of 'body' is held, m."""
    return self.hold + reachOf(body)

  def held(self, body: Body, state: State, target: Vector,
           moving: Vector, turning: Vector, gravity: Vector,
           seconds: float) -> tuple[State, Vector]:
    """The 'held' method returns 'body' in 'state' as held for 'seconds'
    at 'target' (where its middle is to be, moving at 'moving' m/s,
    turning at 'turning' rad/s, under 'gravity' m/s²), and the impulse
    the grabber gave it, N s: its velocity set toward closing the gap in
    'settle' s besides moving along, its weight carried, by no more than
    'force' N in the time; its spin toward 'turning' by no more than
    'twist' N m (the weight carried first: see '_towed')."""
    state, impulse = self._towed(body, state, target, moving, gravity,
                                 seconds, self.force, 0.0)
    inertia = body.inertiaIn(state)
    gap = minus(_times(inertia, turning), _times(inertia, state.spin))
    size, most = norm(gap), self.twist * seconds
    if size > most:
      gap = scaled(gap, most / size)
    change = tuple(solved([list(row) for row in inertia], list(gap)))
    return State(state.place, state.turn, state.velocity,
                 plus(state.spin, change), state.bristles, state.holds,
                 0.0), impulse

  def pulled(self, body: Body, state: State, target: Vector,
             moving: Vector, gravity: Vector,
             seconds: float) -> tuple[State, Vector]:
    """The 'pulled' method returns 'body' in 'state' as pulled for
    'seconds' toward 'target' (moving at 'moving' m/s, under 'gravity'),
    and the impulse given it: as 'held', but no harder than 'pull' N
    and no faster than 'fastest' m/s, its spin left as it is."""
    return self._towed(body, state, target, moving, gravity, seconds,
                       self.pull, self.fastest)

  def catches(self, body: Body, state: State, target: Vector) -> bool:
    """The 'catches' method tells whether 'body' in 'state', pulled in,
    is near enough to 'target' to be held: within its own reach of it,
    half a metre at least."""
    return norm(minus(state.place, target)) <= max(0.5, reachOf(body))

  def punted(self, body: Body, state: State, point: Vector, way: Vector,
             impulse: float) -> tuple[State, Vector]:
    """The 'punted' method returns 'body' in 'state' punted at 'point'
    along 'way' with 'impulse' N s, and the impulse as given."""
    size = norm(way)
    given = scaled(way, impulse / size)
    return poked(body, state, point, given), given

  def _towed(self, body: Body, state: State, target: Vector,
             moving: Vector, gravity: Vector, seconds: float, force: float,
             fastest: float) -> tuple[State, Vector]:
    """Returns 'body' in 'state' towed toward 'target' for 'seconds' by
    no more than 'force' N (and no faster than 'fastest' m/s, if not
    nought), and the impulse: its weight carried first, what is left of
    the force moving it (as much of the force as the weight takes, the
    weight takes; a body heavier than the force is not moved, only
    lightened)."""
    most = force * seconds
    impulse = scaled(gravity, -body.mass * seconds)
    weight = norm(impulse)
    if weight >= most:
      impulse = scaled(impulse, most / weight)
      return poked(body, state, state.place, impulse), impulse
    toward = scaled(minus(target, state.place), 1.0 / self.settle)
    speed = norm(toward)
    if fastest and speed > fastest:
      toward = scaled(toward, fastest / speed)
    wanted = plus(moving, toward)
    moved = scaled(minus(wanted, state.velocity), body.mass)
    size, spare = norm(moved), most - weight
    if size > spare:
      moved = scaled(moved, spare / size)
    impulse = plus(impulse, moved)
    return poked(body, state, state.place, impulse), impulse


def wantedOf(walker: Walker, yaw: float, ahead: float, aside: float,
             running: bool) -> Vector:
  """The 'wantedOf' function returns how fast 'walker' wants to go
  along the ground, m/s: looking along 'yaw' (rad, the view's: they
  look along -cos, -sin), 'ahead' forward less back and 'aside' right
  less left (each -1, 0 or 1), walking or 'running'."""
  forward = (-math.cos(yaw), -math.sin(yaw))
  right = (forward[1], -forward[0])
  x = ahead * forward[0] + aside * right[0]
  y = ahead * forward[1] + aside * right[1]
  size = math.hypot(x, y)
  if size == 0.0:
    return 0.0, 0.0, 0.0
  speed = (walker.run if running else walker.walk) / size
  return x * speed, y * speed, 0.0


def flyingOf(walker: Walker, yaw: float, ahead: float, aside: float,
             upward: float, fast: bool) -> Vector:
  """The 'flyingOf' function returns how fast 'walker' wants to fly,
  m/s: along the ground as 'wantedOf' has it at 'fly' m/s, and 'upward'
  (-1, 0 or 1) at 'rise'; twice as fast when 'fast'."""
  x, y, _ = wantedOf(walker, yaw, ahead, aside, False)
  times = (2.0 if fast else 1.0) * walker.fly / walker.walk
  climb = (2.0 if fast else 1.0) * walker.rise * upward
  return x * times, y * times, climb


def _times(matrix: tuple, vector: Vector) -> Vector:
  """Returns 'matrix' times 'vector'."""
  return tuple(dot(row, vector) for row in matrix)


@functools.lru_cache(maxsize=8)
def _ballOf(radius: float, mass: float) -> Body:
  """Returns a ball of 'radius' weighing 'mass', solid and even."""
  volume = 4.0 / 3.0 * math.pi * radius ** 3
  return Body.of(Sphere(radius), mass / volume)

