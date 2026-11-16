"""
Avatar is the player's body in a world (user, 2026-11-15: "The physical
representation of the player in the world. Basically the vehicle you can
never exit."): a ball where its feet are, its eyes over it, moved as a
game's player moves.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from worQt.phys._body import State
from worQt.phys._poke import poked
from worQt.phys._vectors import cross, matrixOf, minus, plus, product
from worQt.phys._vectors import turnAbout
from worQt.phys._walking import Walker

from ._gait import Gait
from ._hotbar import Hotbar
from ._skin import ASGERJON, EYES, SEATED

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._world import World

#  A person as a game's player moves: a 0.3 m ball of 80 kg at their
#  feet, eyes 1.65 m up; walking 6 m/s, running 12, getting to speed in
#  a tenth of a second (60 m/s²); jumping 0.8 m; flying 20 m/s, rising
#  or sinking 10 (a person walks 1.6 and runs 4: user, 2026-11-13, "make
#  the movement speed not be dogshit").
PERSON = Walker(0.3, 80.0, 1.65, 6.0, 12.0, 600.0, 0.8, 20.0, 10.0, 60.0)
#  How its feet touch whatever they meet: a contact's stiffness, N/m,
#  damping, grip, bristle, N/m, and its damping (a walker's on grass).
SOLES = (1e6, 1.0, 0.6, 1e6, 2e3)
#  How the head turns, rad a pixel the mouse moves; how far it looks up
#  or down at most, rad; Space pressed twice within this, s, starts or
#  stops flying; Ctrl held flies this much faster.
TURN = 0.0025
TILT = 1.48
TWICE = 0.3
FASTER = 2.0
#  How far before the eyes a thing is spawned, m; how near a vehicle's
#  frame (its centre) the avatar boards it, m.
FRONT = 2.0
REACH = 4.0
#  A punt jabs the gun forward (user, 2026-11-16, of the bare hand then:
#  "when it punches an item, let it make a fist that throws forward"):
#  'THRUST' m forward and back over 'PUNCH' s ('Avatar.thrust').
PUNCH, THRUST = 0.3, 0.12
#  A fall this far, m, from where it last stood (or flew) sets it back
#  where it entered (user, 2026-11-15: "automatically respawn if falling
#  too far"; a fall of some 23 blocks kills in Minecraft).
FALL = 25.0
#  The keys that move the avatar its own way (Shift too while flying: it
#  sinks; on its feet Shift alone only runs, moving nothing).
PROPELLING = frozenset(('w', 'a', 's', 'd', 'space'))
#  How far the arms and legs swing either way at full stride, rad; how
#  far forward the arms rest, seated, rad.
SWING = 0.8
RESTING = 0.6


class Avatar:
  """
  Avatar is the player's body: its ball moves by the physics laws of
  'walker' (a phys 'Walker'), its head is turned by 'yaw' (rad about
  the upright, from the world's x) and 'pitch' (rad up). It acts in the
  world it 'enter's each step, as the keys 'held' ask (their names: 'w'
  'a' 's' 'd' 'space' 'shift' 'ctrl'):

  - On its feet: W, A, S, D walk ahead, left, back and right of where
    it looks, Shift runs; at once, as a game's player; on what it
    stands on, moving with it (user, 2026-11-16: out of the cart in the
    loop, standing still in the world's terms on its floor, it braked
    the cart). Space 'pressed'
    jumps (what it stood on pushed down as hard), only while standing.
  - Space pressed twice within 'TWICE' s starts or stops flying: then
    W, A, S, D fly, Space rises, Shift sinks, Ctrl goes 'FASTER'; Shift
    held landing on something ends flying.
  - In the air, not flying, the keys do nothing: it keeps its way.
  - Fallen more than 'FALL' m from where it last stood or flew, or out
    of its world (below its 'lowest'), it is set back where it entered,
    still, not flying.
  - E boards the nearest of its world's 'vehicles' within 'REACH' m
    (user, 2026-11-16: "key_E when near vehicle to enter"; the window
    opens the GUI with E only away from them): its ball tied in the
    seat ('riding'), the head then turning in the vehicle's frame, its
    up the vehicle's (the view rides with it: through a loop, upside
    down; carried out of its world, below its 'lowest', it is set back
    where it entered); its keys do nothing but Shift, which leaves it
    standing where the seat was (user, 2026-11-16: "To leave vehicle:
    key_SHIFT, in vehicle key_E should open vehicle relevant menu": the
    window's), as does 'leave'.

  Its 'hotbar' holds the tools it can take in hand; the one in hand acts
  each step after the avatar has moved, seen floating where a hand
  would hold it (no hand is drawn: user, 2026-11-16, "loose the hand
  lol, just have the floating gun"). Its
  'gait' sways the eyes as drawn while it walks ('viewed'; where it
  aims, 'eyes', never sways); 'grounded' says whether it stood on
  something at the last step, not flying. It looks as its 'skin' (a
  picture laid out as a Minecraft skin, '_skin'; the user's own:
  AsgerJon's), posed as it goes ('posed': its arms and legs swinging
  with its stride, its head looking where it looks, seated riding, its
  right arm held out along its look with a tool in hand); drawn only,
  the world meets it as its ball.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  walker: Walker
  world: World
  index: int
  yaw: float
  pitch: float
  held: frozenset
  flying: bool
  grounded: bool
  hotbar: Hotbar
  gait: Gait
  riding: object
  skin: object

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, walker: Walker) -> None:
    self.walker, self.world, self.index = walker, None, None
    self.yaw, self.pitch, self.held = 0.0, 0.0, frozenset()
    self.flying, self.entered, self._footing = False, None, 0.0
    self._jump, self._lastSpace = False, -1.0
    self.hotbar, self.gait, self.grounded = Hotbar(), Gait(), False
    self.riding, self._board, self._frameTurn = None, False, None
    self._respawn, self._enteredYaw = False, 0.0
    self.skin = ASGERJON

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def enter(self, world: World) -> None:
    """The 'enter' method puts the avatar's ball into 'world' at its
    spawn point, still, looking the way it says; the avatar then acts in
    it each step."""
    if self.world is not None:
      raise RuntimeError('the avatar is already in a world')
    feet, yaw = world.spawnPoint()
    self.entered = State((feet[0], feet[1], feet[2] + self.walker.radius))
    self.world, self.yaw, self.pitch = world, yaw, 0.0
    self._enteredYaw = yaw
    self._footing = self.entered.place[2]
    self.index = world.spawned(self.walker.body(), self.entered, SOLES,
                               None)
    world.addActor(self)

  def turned(self, right: float, down: float) -> None:
    """The 'turned' method turns the head as the mouse moved: 'right' and
    'down' pixels; never looking up or down past 'TILT'."""
    self.yaw -= TURN * right
    self.pitch = min(TILT, max(-TILT, self.pitch - TURN * down))

  def pressed(self, key: str) -> None:
    """The 'pressed' method takes a key just pressed: Space jumps at the
    next step, or, pressed twice within 'TWICE' s, starts or stops
    flying; E boards a vehicle, Shift riding leaves it, at the next
    step."""
    if key == 'e':
      self._board = self._board or self.riding is None
      return
    if key == 'shift' and self.riding is not None:
      self._board = True
      return
    if key != 'space' or self.riding is not None:
      return
    now = time.perf_counter()
    if now - self._lastSpace <= TWICE:
      self.flying, self._jump, self._lastSpace = not self.flying, False, -1.0
      return
    self._jump, self._lastSpace = True, now

  def eyes(self, state: State) -> tuple:
    """The 'eyes' method returns where the avatar's eyes are, its ball in
    'state', and the way they look (a unit vector): riding, in the
    vehicle's frame as the last step left it."""
    forward = self.looking(self.yaw, self.pitch)
    if self._frameTurn is None:
      return self.walker.eyeOf(state), forward
    up = self.up()
    rise = self.walker.eye - self.walker.radius
    return tuple(state.place[i] + rise * up[i] for i in range(3)), forward

  def propelled(self, ) -> bool:
    """The 'propelled' method tells whether the avatar moves itself now
    (user, 2026-11-16: "if the player is not moving under his owner
    propulsion, the mouse should orbit. So orbit should happen in the
    train"): not riding (the vehicle moves it), with a key held that
    walks, jumps or flies it ('PROPELLING'; flying, Shift too)."""
    if self.riding is not None:
      return False
    keys = PROPELLING | ({'shift'} if self.flying else frozenset())
    return bool(self.held & keys)

  def looking(self, yaw: float, pitch: float) -> tuple:
    """The 'looking' method returns the way a look 'yaw' round and
    'pitch' up (rad, as the head's 'yaw' and 'pitch') points in the
    world (a unit vector): riding, in the vehicle's frame as the last
    step left it."""
    across = math.cos(pitch)
    way = (across * math.cos(yaw), across * math.sin(yaw), math.sin(pitch))
    if self._frameTurn is None:
      return way
    m = matrixOf(self._frameTurn)
    return tuple(m[i][0] * way[0] + m[i][1] * way[1] + m[i][2] * way[2]
                 for i in range(3))

  def leave(self, ) -> None:
    """The 'leave' method has the avatar leave the vehicle it rides at
    the next step (none: nothing)."""
    if self.riding is not None:
      self._board = True

  def respawned(self, ) -> None:
    """The 'respawned' method sets the avatar back where it entered at
    the next step (user, 2026-11-16: "respawn"): out of the vehicle it
    rides, still, not flying, looking the way it first looked."""
    self._respawn = True

  def nearby(self, ) -> object:
    """The 'nearby' method returns the nearest of its world's vehicles
    with no rider whose frame's centre is within 'REACH' of the avatar's
    ball, as the world's last step left them (None: none)."""
    if self.world is None:
      return None
    _, states, _ = self.world.snapshot()
    return self._nearestOf(states)

  def up(self, ) -> tuple:
    """The 'up' method returns the way up of the eyes: the world's, or
    riding, the vehicle's frame's."""
    if self._frameTurn is None:
      return 0.0, 0.0, 1.0
    m = matrixOf(self._frameTurn)
    return m[0][2], m[1][2], m[2][2]

  def thrust(self, tool: object, now: float) -> float:
    """The 'thrust' method returns how far forward a punt jabs the
    hands at 'now', m: out to 'THRUST' and back over 'PUNCH' s."""
    if tool is None or tool.punched is None:
      return 0.0
    share = (now - tool.punched) / PUNCH
    if not 0.0 <= share < 1.0:
      return 0.0
    return THRUST * math.sin(math.pi * share)

  def viewed(self, state: State, seconds: float) -> tuple:
    """The 'viewed' method returns where the eyes are seen from, the
    way they look and their way up ('up'), its ball in 'state', the gait
    moved on by 'seconds' and swaying them (to the right of the look
    and straight up)."""
    vx, vy, _ = state.velocity
    self.gait.stepped(math.hypot(vx, vy), self.grounded, seconds)
    eye, forward = self.eyes(state)
    side, rise = self.gait.offset()
    right = (math.sin(self.yaw), -math.cos(self.yaw))
    return (eye[0] + side * right[0], eye[1] + side * right[1],
            eye[2] + rise), forward, self.up()

  def scale(self, ) -> float:
    """The 'scale' method returns how big the skin's pixel is drawn, m:
    its eyes at the avatar's ('EYES')."""
    return self.walker.eye / EYES

  def posed(self, state: State) -> tuple:
    """The 'posed' method returns the avatar's figure as drawn, its ball
    in 'state': where its soles are (m; seated, lower by 'SEATED'
    pixels), its turn in the world (the vehicle's frame, then its yaw)
    and how far each of the skin's 'PARTS' turns about its own left,
    rad: the head up by the pitch, the arms and legs swinging with the
    gait's stride ('SWING' at full swing; a leg forward, its arm back),
    seated the legs ahead and the arms 'RESTING', and with a tool in
    hand the right arm held out along the look."""
    up = self.up()
    drop = self.walker.radius + (SEATED * self.scale()
                                 if self.riding is not None else 0.0)
    soles = tuple(state.place[i] - drop * up[i] for i in range(3))
    turn = turnAbout((0.0, 0.0, 1.0), self.yaw)
    if self._frameTurn is not None:
      turn = product(self._frameTurn, turn)
    if self.riding is not None:
      arms, legs = (-RESTING, -RESTING), (-0.5 * math.pi, -0.5 * math.pi)
    else:
      swing = SWING * self.gait.swing * math.sin(self.gait.phase)
      arms, legs = (swing, -swing), (-swing, swing)
    if self.hotbar.tool() is not None:
      arms = (math.atan2(-math.cos(self.pitch), -math.sin(self.pitch)),
              arms[1])
    return soles, turn, (-self.pitch, 0.0) + arms + legs

  def front(self, ) -> tuple:
    """The 'front' method returns the point 'FRONT' m before the eyes,
    along the look, as the world's last step left the avatar."""
    _, states, _ = self.world.snapshot()
    eye, forward = self.eyes(states[self.index])
    return tuple(e + FRONT * f for e, f in zip(eye, forward))

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method moves the avatar's ball in 'states' for the
    step of 'seconds' to come, as the keys held ask; then the tool in
    hand acts."""
    self._moved(states, seconds)
    tool = self.hotbar.tool()
    if tool is not None:
      tool.acted(self, states, seconds)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _moved(self, states: list, seconds: float) -> None:
    """Moves the avatar's ball in 'states' as the keys held ask; boards
    or leaves a vehicle as F asked; riding, it is the tie's."""
    i, world, walker = self.index, self.world, self.walker
    jump, self._jump = self._jump, False
    if self._respawn:
      self._respawn = False
      if self.riding is not None:
        self.riding.left()
        self.riding, self._frameTurn = None, None
      states[i], self.flying = self.entered, False
      self._footing = self.entered.place[2]
      self.yaw, self.pitch, self._board = self._enteredYaw, 0.0, False
      return
    if self._board:
      self._board = False
      self._boarded(states)
    if self.riding is not None:
      self._frameTurn = states[self.riding.frame].turn
      self.grounded, self._footing = False, states[i].place[2]
      if world.lowest is not None and states[i].place[2] < world.lowest:
        self._respawn = True
      return
    height = states[i].place[2]
    standing = walker.standingOn(world.assembly, tuple(states), i,
                                 world.ground, world.ground is not None)
    self.grounded = standing is not None and not self.flying
    if standing is not None or self.flying:
      self._footing = height
    if height < self._footing - FALL or (world.lowest is not None
                                         and height < world.lowest):
      states[i], self.flying = self.entered, False
      self._footing = self.entered.place[2]
      return
    held = self.held
    down = 'shift' in held
    if self.flying and standing is not None and down:
      self.flying = False
    if self.flying:
      states[i] = walker.flown(states[i], self._flyingOf(held, down),
                               world.universe.gravityVector(), seconds)
      return
    body = world.assembly.bodies[i]
    if standing is None:
      states[i] = poked(body, states[i], states[i].place, (0.0, 0.0, 0.0))
      return
    under, point = standing
    wanted = self._walkingOf(held, down)
    if under is not None:
      carried = states[under]
      moving = plus(carried.velocity, cross(carried.spin, minus(
        point, carried.place)))
      wanted = (wanted[0] + moving[0], wanted[1] + moving[1], wanted[2])
    states[i] = walker.strode(states[i], wanted, seconds)
    if not jump:
      return
    states[i], impulse = walker.jumped(body, states[i],
                                       world.universe.gravity)
    if under is not None and under not in world.still:
      pushed = world.assembly.bodies[under]
      states[under] = poked(pushed, states[under], point,
                            tuple(-x for x in impulse))

  def _boarded(self, states: list) -> None:
    """Leaves the vehicle ridden (looking on the way it looked, in the
    world's terms), else boards the nearest within 'REACH'."""
    _, forward = self.eyes(states[self.index])
    if self.riding is not None:
      self.riding.left()
      self.riding, self._frameTurn = None, None
      self._looked(forward)
      return
    vehicle = self._nearestOf(states)
    if vehicle is None:
      return
    vehicle.boarded(self, states)
    self.riding, self.flying = vehicle, False
    self._frameTurn = states[vehicle.frame].turn
    m = matrixOf(self._frameTurn)
    self._looked(tuple(m[0][j] * forward[0] + m[1][j] * forward[1]
                       + m[2][j] * forward[2] for j in range(3)))

  def _nearestOf(self, states: tuple) -> object:
    """Returns the nearest vehicle with no rider whose frame's centre is
    within 'REACH' of the avatar's ball in 'states' (None: none)."""
    here = states[self.index].place
    best, nearest = REACH * REACH, None
    for vehicle in self.world.vehicles:
      if vehicle.rider is not None:
        continue
      there = states[vehicle.frame].place
      gap = sum((a - b) ** 2 for a, b in zip(here, there))
      if gap <= best:
        best, nearest = gap, vehicle
    return nearest

  def _looked(self, forward: tuple) -> None:
    """Turns the head to look along 'forward' (in the frame the head now
    turns in)."""
    self.yaw = math.atan2(forward[1], forward[0])
    self.pitch = min(TILT, max(-TILT, math.asin(max(-1.0, min(
      1.0, forward[2])))))

  def _alongOf(self, held: frozenset) -> tuple[float, float]:
    """Returns the way along the ground W, A, S, D ask, a unit vector
    (or nought), as the head looks."""
    ahead = ('w' in held) - ('s' in held)
    aside = ('d' in held) - ('a' in held)
    c, s = math.cos(self.yaw), math.sin(self.yaw)
    x, y = ahead * c + aside * s, ahead * s - aside * c
    size = math.hypot(x, y)
    return (0.0, 0.0) if size == 0.0 else (x / size, y / size)

  def _walkingOf(self, held: frozenset, running: bool) -> tuple:
    """Returns how fast the keys ask to walk, m/s (running: faster)."""
    x, y = self._alongOf(held)
    speed = self.walker.run if running else self.walker.walk
    return x * speed, y * speed, 0.0

  def _flyingOf(self, held: frozenset, sinking: bool) -> tuple:
    """Returns how fast the keys ask to fly, m/s: along at 'fly', up
    (Space) or down (Shift) at 'rise', Ctrl 'FASTER'."""
    x, y = self._alongOf(held)
    fast = FASTER if 'ctrl' in held else 1.0
    along, rise = self.walker.fly * fast, self.walker.rise * fast
    upward = ('space' in held) - sinking
    return x * along, y * along, upward * rise
