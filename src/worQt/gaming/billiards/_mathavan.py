"""
mathavanRebound is a ball off a cushion as Mathavan, Jackson and Parkin
(2010) have it: the cushion rigid, met at its nose; the reference the
engine's cushion is checked against.

Mathavan S, Jackson MR, Parkin RM. A theoretical analysis of billiard
ball dynamics under cushion impacts. Proc. IMechE Part C, 2010,
224(9):1863-1873. doi:10.1243/09544062JMES1964
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  Impulse steps through the squeeze, at the least: the push is followed
#  in this many pieces of the speed into the cushion.
_PIECES = 4000


def mathavanRebound(vx: float, vy: float, wx: float, wy: float,
                    wz: float, radius: float, height: float,
                    restitution: float, cushionFriction: float,
                    tableFriction: float,
                    pieces: int = _PIECES) -> tuple[float, ...]:
  """The 'mathavanRebound' function returns a ball of 'radius' after it
  meets a rigid cushion whose nose is 'height' above the cloth, as
  Mathavan et al. (2010) have it, in the cushion's frame: 'x' along the
  cushion, 'y' into it, 'z' up; 'vx', 'vy' (mm/s) and 'wx', 'wy', 'wz'
  (rad/s) as it comes, (vx, vy, wx, wy, wz) as it leaves.

  The nose pushes along the line from it to the ball's middle, so also
  down into the slate; friction at the nose, 'cushionFriction', against
  the slip there, and at the slate, 'tableFriction', under the nose's
  push down, each a Coulomb friction; the weight is nothing beside the
  push. The hit is followed through the impulse given, in 'pieces' steps
  of the speed in: squeezed till the ball no longer moves into the
  cushion, then let go till the nose has given back 'restitution'
  squared of the work it took (Stronge's restitution)."""
  sin = (height - radius) / radius
  cos = math.sqrt(1.0 - sin * sin)
  state = (vx, vy, wx, wy, wz)
  if vy <= 0.0:
    return state
  step = vy / pieces
  taken = 0.0
  while state[1] > 0.0:
    after = _pushed(state, step, radius, sin, cos, cushionFriction,
                    tableFriction)
    if after[1] > 0.0:
      taken += cos * step * 0.5 * (state[1] + after[1])
      state = after
      continue
    share = state[1] / (state[1] - after[1])
    taken += cos * step * share * 0.5 * state[1]
    state = tuple(a + share * (b - a) for a, b in zip(state, after))
    break
  wanted = restitution * restitution * taken
  given = 0.0
  while given < wanted:
    after = _pushed(state, step, radius, sin, cos, cushionFriction,
                    tableFriction)
    work = cos * step * 0.5 * abs(state[1] + after[1])
    if given + work >= wanted and work > 0.0:
      share = (wanted - given) / work
      return tuple(a + share * (b - a) for a, b in zip(state, after))
    given += work
    state = after
  return state


def _pushed(state: tuple, impulse: float, radius: float, sin: float,
            cos: float, cushionFriction: float,
            tableFriction: float) -> tuple[float, ...]:
  """Returns 'state' after the nose has pushed 'impulse' more (a
  kilogram), with the friction it and the slate give then, as Mathavan
  et al.'s equations (14)-(18) have it."""
  vx, vy, wx, wy, wz = state
  #  The slip at the nose, along the cushion and up its face, and on the
  #  slate.
  slipX = vx + wy * radius * sin - wz * radius * cos
  slipY = -vy * sin + wx * radius
  slateX = vx - wy * radius
  slateY = vy + wx * radius
  nose = math.atan2(slipY, slipX)
  slate = math.atan2(slateY, slateX)
  mu, muSlate = cushionFriction, tableFriction
  down = sin + mu * math.sin(nose) * cos
  vx -= (mu * math.cos(nose) + muSlate * math.cos(slate) * down) * impulse
  vy -= (cos - mu * sin * math.sin(nose)
         + muSlate * math.sin(slate) * down) * impulse
  turn = 2.5 / radius * impulse
  wx -= turn * (mu * math.sin(nose) + muSlate * math.sin(slate) * down)
  wy -= turn * (mu * math.cos(nose) * sin
                - muSlate * math.cos(slate) * down)
  wz += turn * mu * math.cos(nose) * cos
  return vx, vy, wx, wy, wz
