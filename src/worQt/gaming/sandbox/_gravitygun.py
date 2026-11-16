"""
GravityGun is the first tool (user, 2026-11-15: "Alyx' gravity gun would
be one"): it pulls in what it points at, holds it before the eyes and
punts it away; nothing it does pushes back on the avatar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import TYPE_CHECKING

from worQt.phys._poke import hitOf
from worQt.phys._vectors import minus, norm, plus, scaled
from worQt.phys._walking import Grabber

from ._tool import GRIP, GRIP_ALONG, Tool

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._avatar import Avatar

#  How fast a punt sends a body off, m/s, and the most mass it punts so
#  (a heavier body is punted as that much: not slammed into what holds
#  it), kg; how far past its hold a held body is let go, m; how far down
#  the hold may lie at most, rad; how far a wheel's notch moves the
#  hold, m, and how near and how far it may be moved.
PUNT_SPEED = 12.0
PUNT_MASS = 100.0
LOST = 2.0
LOWEST = 0.75
NOTCH = 0.25
NEAREST, FURTHEST = -0.3, 3.0
#  Its hotbar icon: a ray gun of our own with a 3 on it (user,
#  2026-11-15: "noone can accuse us of copying valve").
ICON = str(Path(__file__).with_name('icons') / 'gravitygun.svg')
#  How it is seen in the hands, in the lower right corner beside the
#  hotbar: a stubby ray gun of boxes (its body, a glowing stripe on top,
#  the barrel and three prongs, a tilted grip where the hand holds it),
#  a 3 painted on its left side; 'HELD' is its body's middle in the
#  eyes' frame, m.
HELD = (GRIP[0], GRIP[1] + 0.065, GRIP[2] - 0.07)
_ALONG = (0.0, 0.0, 1.0)
_GREY, _DARK, _GLOW = (112, 120, 132), (70, 76, 86), (255, 154, 46)


def _at(x: float, y: float, z: float) -> tuple:
  """Returns a point 'HELD' plus ('x', 'y', 'z'), m."""
  return HELD[0] + x, HELD[1] + y, HELD[2] + z


PARTS = (((0.05, 0.05, 0.22), _at(0.0, 0.0, 0.0), _ALONG, _GREY),
         ((0.02, 0.006, 0.14), _at(0.0, 0.028, -0.02), _ALONG, _GLOW),
         ((0.038, 0.038, 0.06), _at(0.0, 0.0, -0.14), _ALONG, _DARK),
         ((0.006, 0.006, 0.045), _at(0.018, 0.016, -0.19), _ALONG,
          _GLOW),
         ((0.006, 0.006, 0.045), _at(-0.018, 0.016, -0.19), _ALONG,
          _GLOW),
         ((0.006, 0.006, 0.045), _at(0.0, -0.022, -0.19), _ALONG, _GLOW),
         ((0.038, 0.09, 0.04), GRIP, GRIP_ALONG, _DARK))
LABEL = ('3', _at(-0.0255, 0.0, 0.03), -90.0, (255, 210, 63), 0.035)
#  The gun as a textured model instead (user, 2026-11-16: "i found a
#  better one maybe"): Summer Engine's asset store "Gravity Gun" by
#  Timofey Arefyev, made with meshy-6, no licence stated (kept out of
#  git: 'models/' is ignored). In its own units its barrel points along
#  -x, its grip hangs down at 'MODEL_GRIP', 1.9 long; shown 'MODEL_SIZE'
#  m a unit, turned barrel ahead, its grip in the hand at 'GRIP', the 3
#  on its left side. Without the file the gun of boxes is shown.
MODEL_FILE = Path(__file__).parent / 'models' / 'gravitygun.glb'
MODEL_GRIP = (0.68, -0.33, 0.0)
MODEL_SIZE = 0.18


def _fromModel(x: float, y: float, z: float) -> tuple:
  """Returns where the model's point ('x', 'y', 'z') is in the eyes'
  frame, m (turned -90 degrees about y: its x to z, its z to -x)."""
  gx, gy, gz = MODEL_GRIP
  return (GRIP[0] - MODEL_SIZE * (z - gz), GRIP[1] + MODEL_SIZE * (y - gy),
          GRIP[2] + MODEL_SIZE * (x - gx))


MODEL = (str(MODEL_FILE), _fromModel(0.0, 0.0, 0.0), (0.0, -90.0, 0.0),
         MODEL_SIZE) if MODEL_FILE.exists() else None
#  Where it glows while it holds something (user, 2026-11-16: "a light
#  thing should indicate that the gun has it"): between the claws (the
#  model's) or before the barrel (the boxes').
GLOW = _fromModel(-0.82, 0.17, 0.0) if MODEL is not None else _at(
  0.0, 0.0, -0.21)
#  How far before the eyes the grabber holds a thing, past its own reach,
#  m (user, 2026-11-16: "when holding an item, the item should be nearer
#  the gun": the grabber's own 1.0 held a ball 1.15 m out, well beyond
#  the claws at ~0.7 m).
HOLD = 0.55
MODEL_LABEL = ('3', _fromModel(-0.1, 0.2, 0.17), -90.0, (255, 210, 63),
               0.035)


class GravityGun(Tool):
  """
  GravityGun grabs by its 'grabber' (a phys 'Grabber': reach, pull, hold,
  force) what its avatar's eyes point at, past the avatar and the
  world's bodies held still:

  - Right button pressed pulls the body pointed at toward the hold, and
    holds it once it is near (letting the button go stops a pull); held,
    it is carried there as the avatar moves and turns; pressed again it
    is dropped. Lost more than 'LOST' m past its hold, it is let go.
  - The hold lies along the look, never lower than 'LOWEST' down, as far
    out as the grabber holds that body plus 'further' (the wheel, while
    holding: 'NOTCH' a notch, 'NEAREST' to 'FURTHEST').
  - Left button punts what is held (along the look, letting it go: a
    yeet) or what is pointed at within the grabber's punt reach (a
    punt), at 'PUNT_SPEED', as if it weighed no more than 'PUNT_MASS'.
  - It hums, idle or holding, and glows at 'GLOW' while it holds.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  name = 'Gravity gun'
  icon = ICON
  parts = PARTS if MODEL is None else ()
  label = LABEL if MODEL is None else MODEL_LABEL
  model = MODEL
  glow = GLOW

  #  Public Variables
  grabber: Grabber
  further: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, grabber: Grabber = None) -> None:
    Tool.__init__(self, )
    self.grabber = Grabber(10.0, 400.0, 6.0, HOLD, 3000.0, 0.1, 300.0,
                           4.0) if grabber is None else grabber
    self.further, self._lastYaw = 0.0, None
    self._pulling, self._drop, self._punt = False, False, False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def humming(self, ) -> int:
    """The gun hums idle, or holding while it holds."""
    return 2 if self.held is not None else 1

  def pressed(self, button: str) -> None:
    """Right: drops what is held, else starts pulling; left: punts."""
    if button == 'right':
      if self.held is not None:
        self._drop = True
      else:
        self._pulling = True
    elif button == 'left':
      self._punt = True

  def released(self, button: str) -> None:
    """Right let go stops a pull."""
    if button == 'right':
      self._pulling = False

  def wheeled(self, notches: float) -> bool:
    """While holding, the wheel moves the hold nearer or further."""
    if self.held is None:
      return False
    self.further = min(FURTHEST, max(NEAREST,
                                     self.further + NOTCH * notches))
    return True

  def putAway(self, ) -> None:
    """Put away it lets go and stops pulling."""
    Tool.putAway(self, )
    self._pulling, self._drop, self._punt = False, False, False

  def acted(self, avatar: Avatar, states: list, seconds: float) -> None:
    """Points, pulls, holds and punts for the step to come."""
    world = avatar.world
    eye, forward = avatar.eyes(states[avatar.index])
    turning = 0.0 if self._lastYaw is None else (
      (avatar.yaw - self._lastYaw) / seconds)
    self._lastYaw = avatar.yaw
    if self._drop:
      self.held, self._drop = None, False
    passed = (avatar.index,) + tuple(world.still)
    hit = hitOf(world.assembly, tuple(states), eye, forward, passed)
    near = hit is not None and norm(minus(hit[1], eye)) <= (
      self.grabber.reach)
    self.pointed = hit[0] if near and self.held is None else None
    if self._punt:
      self._punt = False
      self._punted(avatar, states, eye, forward, hit)
      return
    if self.held is None and not (self._pulling and near):
      return
    index = hit[0] if self.held is None else self.held
    self._carried(avatar, states, eye, index, turning, seconds)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _aim(self, avatar: Avatar) -> tuple:
    """Returns the way from the eyes to the hold: the look, no lower than
    'LOWEST' down."""
    pitch = max(avatar.pitch, -LOWEST)
    across = math.cos(pitch)
    return (across * math.cos(avatar.yaw), across * math.sin(avatar.yaw),
            math.sin(pitch))

  def _carried(self, avatar: Avatar, states: list, eye: tuple,
               index: int, turning: float, seconds: float) -> None:
    """Pulls body 'index' toward the hold, holding it once caught; or
    holds it there, letting it go once lost."""
    world, grabber = avatar.world, self.grabber
    body, state = world.assembly.bodies[index], states[index]
    hold = grabber.holdOf(body)
    target = plus(eye, scaled(self._aim(avatar), hold + self.further))
    walker = states[avatar.index]
    moving = (walker.velocity[0], walker.velocity[1], 0.0)
    gravity = world.universe.gravityVector()
    if self.held is None:
      if grabber.catches(body, state, target):
        self.held, self._pulling = index, False
      else:
        states[index], _ = grabber.pulled(body, state, target, moving,
                                          gravity, seconds)
        return
    if norm(minus(state.place, target)) > LOST + hold:
      self.held = None
      return
    states[index], _ = grabber.held(body, state, target, moving,
                                    (0.0, 0.0, turning), gravity, seconds)

  def _punted(self, avatar: Avatar, states: list, eye: tuple,
              forward: tuple, hit: tuple) -> None:
    """Punts what is held along the look, letting it go, or what is
    pointed at within the punt's reach, where it is pointed at."""
    if self.held is not None:
      index, self.held = self.held, None
      point = states[index].place
      self.yeets += 1
    elif hit is not None and norm(minus(hit[1], eye)) <= self.grabber.punt:
      index, point = hit[0], hit[1]
      self.punts += 1
    else:
      return
    body = avatar.world.assembly.bodies[index]
    mass = min(body.mass, PUNT_MASS)
    states[index], _ = self.grabber.punted(body, states[index], point,
                                           forward, mass * PUNT_SPEED)
    self.punched = time.perf_counter()
