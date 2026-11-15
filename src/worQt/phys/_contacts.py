"""
ContactForces pushes touching bodies apart and holds them by their
bristles: the contacts of an assembly.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import TYPE_CHECKING

import numpy

from ._rounds import ROUND, isRound, isTurned, piecesOf, roundTouch
from ._rounds import turnedTouches
from ._shape import Sphere
from ._vectors import Vector, applied, conjugate, cross, dot, matrixOf
from ._vectors import minus, norm, plus, product, scaled, transposed

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Contact


class ContactForces:
  """
  ContactForces is 'contacts' between the bodies 'movers' (the world's
  stepping's '_Moving', in the order of the assembly's bodies): each
  point of either body's skin (its edges' points, 'Shape.skin') pressed
  into the other is pushed out and held by its bristle, its hold kept
  in its body's 'holds' (keyed by the point's place in the skin and the
  other's place, where on the other it is held, in the other's own
  frame). A contact with a ball ('rounds') is one point instead, the
  nearest ('_rounds.roundTouch'): its stiffness N/m there, its bristle a
  stretch kept in the ball's holds (keyed 'ROUND' and the other's
  place, in the world) that only slipping stretches, carried on as the
  bodies drift ('rolled'). A ball against a turned solid ('Turned') has
  a contact for every piece of its profile it presses, each held under
  'ROUND' less the piece's place.
  """

  def __init__(self, contacts: tuple[Contact, ...], movers: list) -> None:
    self.movers = movers
    self.shapes, self.skins = {}, {}
    self.stepping = False
    self.contacts = tuple(c for c in contacts
                          if not (isRound(movers[c.first])
                                  or isRound(movers[c.second])))
    for contact in self.contacts:
      if isTurned(movers[contact.first]) or isTurned(
          movers[contact.second]):
        raise ValueError('a turned solid meets only balls so far')
    self.rounds = tuple(c for c in contacts
                        if isRound(movers[c.first])
                        or isRound(movers[c.second]))
    self.pieces, self.rolling, self.roundings = {}, [], []
    for contact in self.rounds:
      for index in (contact.first, contact.second):
        mover = movers[index]
        if (not isRound(mover) and not isTurned(mover)
            and id(mover) not in self.pieces):
          self.pieces[id(mover)] = piecesOf(mover)
    for contact in self.rounds:
      first, second = movers[contact.first], movers[contact.second]
      if isRound(first):
        ball, other, theirs = first, second, contact.second
      else:
        ball, other, theirs = second, first, contact.first
      slots = len(other.body.shape.profile) if isTurned(other) else 1
      self.roundings.append((contact, ball, other, theirs,
                             self.pieces.get(id(other)), slots))
    for contact in self.contacts:
      for index in (contact.first, contact.second):
        mover = movers[index]
        if id(mover) not in self.shapes:
          self.shapes[id(mover)] = _shapeOf(mover)
        key = (id(mover), contact.spacing)
        if key not in self.skins:
          self.skins[key] = _skinOf(mover, contact.spacing)

  def touches(self, ) -> list[tuple]:
    """The 'touches' method returns every skin point pressed into
    another body now, both ways round each contact: the contact, the
    body pressing ('toucher') and its arm to the point, the body pressed
    ('other', and its place) and its arm to the point, where the point
    is, how deep, the outward normal, how fast the point moves against
    the other, its hold's key, and its share of edge."""
    out = []
    for contact in self.contacts:
      for mine, theirs in ((contact.first, contact.second),
                           (contact.second, contact.first)):
        toucher, other = self.movers[mine], self.movers[theirs]
        if self.stepping and toucher.asleep() and other.asleep():
          continue
        out.extend(self.pressed(contact, toucher, other, theirs))
    return out

  def pressed(self, contact: Contact, toucher, other, theirs: int) -> list:
    """The 'pressed' method returns the points of 'toucher's skin
    pressed into 'other' (its place 'theirs') now, as 'touches' has
    them, and lets go the holds of the points not pressed in."""
    points = self.skins[(id(toucher), contact.spacing)]
    _, pieces, reach = self.shapes[id(other)]
    turning, otherTurning = matrixOf(toucher.turn), matrixOf(other.turn)
    back = transposed(otherTurning)
    spin, otherSpin = toucher.spin(), other.spin()
    out = []
    for index, (arm, share) in enumerate(points):
      key = (index, theirs)
      outward = applied(turning, arm)
      place = plus(toucher.place, outward)
      apart = minus(place, other.place)
      if norm(apart) > reach:
        toucher.holds.pop(key, None)
        continue
      inside = applied(back, apart)
      deepest, normal = 0.0, None
      for planes in pieces:
        depth = min(offset - dot(facing, inside)
                    for facing, offset in planes)
        if depth > deepest:
          deepest = depth
          normal = min(planes, key=lambda plane: plane[1] - dot(plane[0],
                                                                inside))[0]
      if normal is None:
        toucher.holds.pop(key, None)
        continue
      moving = minus(plus(toucher.velocity, cross(spin, outward)),
                     plus(other.velocity, cross(otherSpin, apart)))
      out.append((contact, toucher, outward, other, theirs, apart, place,
                  deepest, applied(otherTurning, normal), moving, key,
                  share))
    return out

  def pushes(self, holds: bool) -> list[tuple]:
    """The 'pushes' method returns each touch's force on its toucher
    (the other is pushed as hard the other way), with the touch: the
    push out along the normal, and the bristle's pull and damping along
    the face, together no more than the grip times the push; with
    'holds' the bristles are held to their new places, slipping, else
    left as they are."""
    out = []
    for touch in self.touches():
      contact, toucher, _, other, _, _, place, depth, normal, moving, key, (
        share) = touch
      push = contact.pushOf(share, depth, -dot(normal, moving))
      most = contact.grip * push
      held = toucher.holds.get(key)
      if held is None:
        held = _inOwn(other, place)
      anchor = _inWorld(other, held)
      stretch = _across(minus(place, anchor), normal)
      bristle = share * contact.bristle
      pull = scaled(stretch, -bristle)
      pulling = norm(pull)
      if pulling > most:
        pull = scaled(pull, most / pulling)
        slipped = plus(place, scaled(pull, 1.0 / bristle))
        held = _inOwn(other, slipped)
      along = minus(pull, scaled(_across(moving, normal),
                                 share * contact.bristleDamping))
      size = norm(along)
      if size > most:
        along = scaled(along, most / size)
      if holds:
        toucher.holds[key] = held
      out.append((plus(scaled(normal, push), along), touch))
    return out

  def kick(self, h: float) -> None:
    """The 'kick' method gives the bodies the contacts' pushes for 'h'
    s, booked under 'contact'; two bodies both asleep are passed over
    (a body asleep takes no push)."""
    self.stepping = True
    pushes = self.pushes(True)
    self.rolling = []
    rounds = self.roundPushes(True)
    self.stepping = False
    for force, touch in pushes:
      _, toucher, arm, other, _, apart, _, _, _, _, _, _ = touch
      toucher.pushed(scaled(force, h), arm, 'contact')
      other.pushed(scaled(force, -h), apart, 'contact')
    for force, ball, arm, other, apart, _, _, _ in rounds:
      ball.pushed(scaled(force, h), arm, 'contact')
      other.pushed(scaled(force, -h), apart, 'contact')

  def roundPushes(self, holds: bool) -> list[tuple]:
    """The 'roundPushes' method returns each round contact's force on
    its ball (the other pushed as hard the other way): the force, the
    ball and its arm to the point, the other and its arm, the contact,
    how deep, and the bristle's stretch. The push out along the normal;
    the bristle's pull, dragged so it pulls no harder than the grip
    times the push, and its damping against the slip, together no more
    than that either. With 'holds' the stretches are kept (let go where
    nothing touches) and noted for 'rolled', else left as they are."""
    out = []
    for contact, ball, other, theirs, pieces, slots in self.roundings:
      if self.stepping and ball.asleep() and other.asleep():
        continue
      if slots > 1 or isTurned(other):
        touches = turnedTouches(ball, other)
      else:
        touch = roundTouch(ball, other, pieces)
        touches = [] if touch is None else [(0,) + tuple(touch)]
      if holds:
        pressed = {slot for slot, _, _, _ in touches}
        for slot in range(slots):
          if slot not in pressed:
            ball.holds.pop((ROUND - slot, theirs), None)
      for slot, normal, depth, point in touches:
        key = (ROUND - slot, theirs)
        out.append(self.roundPush(contact, ball, other, key, normal, depth,
                                  point, holds))
    return out

  def roundPush(self, contact: Contact, ball, other, key: tuple,
                normal: Vector, depth: float, point: Vector,
                holds: bool) -> tuple:
    """The 'roundPush' method returns one round contact's force on its
    ball, as 'roundPushes' lists it, its stretch kept under 'key' and
    noted for 'rolled' with 'holds'."""
    arm, apart = minus(point, ball.place), minus(point, other.place)
    moving = minus(plus(ball.velocity, cross(ball.spin(), arm)),
                   plus(other.velocity, cross(other.spin(), apart)))
    closing = dot(normal, moving)
    slip = minus(moving, scaled(normal, closing))
    push = contact.pushOf(1.0, depth, -closing)
    most = contact.grip * push
    stretch = _across(ball.holds.get(key, (0.0, 0.0, 0.0)), normal)
    pull = scaled(stretch, -contact.bristle)
    pulling = norm(pull)
    if pulling > most:
      pull = scaled(pull, most / pulling)
      stretch = scaled(pull, -1.0 / contact.bristle)
    along = minus(pull, scaled(slip, contact.bristleDamping))
    size = norm(along)
    if size > most:
      along = scaled(along, most / size)
    if holds:
      ball.holds[key] = stretch
      self.rolling.append((ball, other, key, arm, apart, normal))
    return (plus(scaled(normal, push), along), ball, arm, other, apart,
            contact, depth, stretch)

  def rolled(self, h: float) -> None:
    """The 'rolled' method carries the round contacts' stretches on
    over a drift of 'h' s: each by its slip, how fast the ball's point
    slides over the other's along their faces (rolling stretches
    nothing)."""
    for ball, other, key, arm, apart, normal in self.rolling:
      held = ball.holds.get(key)
      if held is None:
        continue
      moving = minus(plus(ball.velocity, cross(ball.spin(), arm)),
                     plus(other.velocity, cross(other.spin(), apart)))
      ball.holds[key] = plus(held, scaled(_across(moving, normal), h))

  def forces(self, ) -> dict:
    """The 'forces' method returns the contacts' force and torque about
    its centre on each body they push, keyed by the body's 'id', the
    holds left as they are."""
    out: dict[int, tuple[Vector, Vector]] = {}
    kept = {id(mover): dict(mover.holds) for mover in self.movers}
    for force, touch in self.pushes(False):
      _, toucher, arm, other, _, apart, _, _, _, _, _, _ = touch
      for mover, at, given in ((toucher, arm, force),
                               (other, apart, scaled(force, -1.0))):
        had = out.get(id(mover), ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        out[id(mover)] = (plus(had[0], given),
                          plus(had[1], cross(at, given)))
    for force, ball, arm, other, apart, _, _, _ in self.roundPushes(False):
      for mover, at, given in ((ball, arm, force),
                               (other, apart, scaled(force, -1.0))):
        had = out.get(id(mover), ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        out[id(mover)] = (plus(had[0], given),
                          plus(had[1], cross(at, given)))
    for mover in self.movers:
      mover.holds = kept[id(mover)]
    return out

  def stored(self, ) -> float:
    """The 'stored' method returns the energy the contacts hold now,
    pressed in and stretching their bristles, J."""
    kept = {id(mover): dict(mover.holds) for mover in self.movers}
    total = 0.0
    for touch in self.touches():
      contact, toucher, _, other, _, _, place, depth, normal, _, key, (
        share) = touch
      total += 0.5 * share * contact.stiffness * depth * depth
      held = toucher.holds.get(key)
      if held is not None:
        stretch = _across(minus(place, _inWorld(other, held)), normal)
        total += 0.5 * share * contact.bristle * dot(stretch, stretch)
    for _, _, _, _, _, contact, depth, stretch in self.roundPushes(False):
      total += 0.5 * contact.stiffness * depth * depth
      total += 0.5 * contact.bristle * dot(stretch, stretch)
    for mover in self.movers:
      mover.holds = kept[id(mover)]
    return total

  def quickest(self, ) -> float:
    """The 'quickest' method returns a bound on how fast, rad/s, the
    contacts could swing the bodies (Gershgorin's, row by row: no body
    swings faster than twice its own give times all the stiffness
    pressing it). A contact presses, each way round, as much edge as
    could at once (a face laid flat: the most skin on one face's plane,
    but no more than the other's), at its stiffness in and both ways
    along; a body is pressed by no more edge than twice its own skin,
    however many contacts it has (its own pressing out, as much
    pressing in); it gives as easily as at the point of its skin where
    it gives most ('giveOf')."""
    pressing, most = {}, {}
    for contact in self.contacts:
      stiff = contact.stiffness + 2.0 * contact.bristle
      ends = [self.movers[contact.first], self.movers[contact.second]]
      lengths = [mover.body.shape.faceLength(contact.spacing)
                 if mover.body.shape is not None else 0.0
                 for mover in ends]
      for mover in ends:
        key = (id(mover), contact.spacing)
        pressing[key] = pressing.get(key, 0.0) + 2.0 * min(lengths) * stiff
        most[key] = max(most.get(key, 0.0), stiff)
    quickest = 0.0
    for contact in self.contacts:
      for mover in (self.movers[contact.first],
                    self.movers[contact.second]):
        key = (id(mover), contact.spacing)
        skin = sum(share for _, share in self.skins[key])
        pressed = min(pressing[key], 2.0 * skin * most[key])
        quickest = max(quickest, 2.0 * giveOf(mover, contact.spacing)
                       * pressed)
    rounding, steepest, spacing = {}, {}, {}
    for contact in self.rounds:
      stiff = contact.stiffness + 2.0 * contact.bristle
      for mover in (self.movers[contact.first],
                    self.movers[contact.second]):
        rounding[id(mover)] = rounding.get(id(mover), 0.0) + stiff
        steepest[id(mover)] = max(steepest.get(id(mover), 0.0), stiff)
        spacing[id(mover)] = (mover, contact.spacing)
    for key, (mover, gap) in spacing.items():
      pressed = rounding[key]
      if isRound(mover):
        pressed = min(pressed, _CROWD * steepest[key])
      quickest = max(quickest, 2.0 * giveOf(mover, gap) * pressed)
    return math.sqrt(quickest)


def giveOf(mover, spacing: float) -> float:
  """The 'giveOf' function returns how easily a body gives, m/s per N
  s, at the point of its skin where it gives most, whichever way pushed:
  one over its mass, and the most its turn moves that point (the
  greatest eigenvalue of [r]x' I^-1 [r]x, r the point's arm along the
  principal axes)."""
  shape = mover.body.shape
  if shape is None:
    return 1.0 / mover.mass
  if isinstance(shape, Sphere):
    return 1.0 / mover.mass + shape.radius ** 2 / mover.moments[0]
  if isTurned(mover):
    return _giveOf(mover.body, mover.moments, mover.axes, None)
  return _giveOf(mover.body, mover.moments, mover.axes, spacing)


#  The most a ball can touch at once: twelve balls as large about it,
#  and one thing more.
_CROWD = 13


@functools.lru_cache(maxsize=256)
def _giveOf(body, moments: tuple, axes: tuple, spacing: float) -> float:
  """Returns 'giveOf' for 'body', remembered ('spacing' None: a turned
  solid, at its corners)."""
  back = transposed(matrixOf(axes))
  soft = numpy.diag([1.0 / moments[0], 1.0 / moments[1], 1.0 / moments[2]])
  most = 0.0
  points = (body.shape.corners() if spacing is None
            else [point for point, _ in body.shape.skin(spacing)])
  for point in points:
    x, y, z = applied(back, minus(point, body.centre))
    across = numpy.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    turning = across.T @ soft @ across
    most = max(most, float(numpy.linalg.eigvalsh(turning)[-1]))
  return 1.0 / body.mass + most


def _shapeOf(mover) -> tuple:
  """The '_shapeOf' function returns a body's points, each its index and
  its arm along the principal axes, its pieces' planes along them too
  (each face's normal and how far along it from the centre), and how
  far from the centre its farthest point is."""
  shape, body = mover.body.shape, mover.body
  if shape is None:
    return (), (), 0.0
  back = transposed(matrixOf(mover.axes))
  points = tuple((index, applied(back, minus(point, body.centre)))
                 for index, point in enumerate(shape.points))
  pieces = tuple(tuple((applied(back, facing),
                        offset - dot(facing, body.centre))
                       for facing, offset in planes)
                 for planes in shape.pieces())
  reach = max((norm(arm) for _, arm in points), default=0.0)
  return points, pieces, reach


def _skinOf(mover, spacing: float) -> tuple:
  """The '_skinOf' function returns a body's skin, its edges' points
  'spacing' apart, each its arm along the principal axes and its share
  of edge, m."""
  shape, body = mover.body.shape, mover.body
  if shape is None:
    return ()
  back = transposed(matrixOf(mover.axes))
  return tuple((applied(back, minus(point, body.centre)), share)
               for point, share in shape.skin(spacing))


def _across(vector: Vector, normal: Vector) -> Vector:
  """The '_across' function returns 'vector' less its part along the
  unit 'normal'."""
  return minus(vector, scaled(normal, dot(vector, normal)))


def _ownTurn(mover) -> tuple:
  """The '_ownTurn' function returns a body's own frame's turn now."""
  return matrixOf(product(mover.turn, conjugate(mover.axes)))


def _inWorld(mover, point: Vector) -> Vector:
  """The '_inWorld' function returns where 'point', in a body's own
  frame, is in the world now."""
  return plus(mover.place, applied(_ownTurn(mover),
                                   minus(point, mover.body.centre)))


def _inOwn(mover, place: Vector) -> Vector:
  """The '_inOwn' function returns 'place', in the world, in a body's
  own frame as it is now."""
  return plus(mover.body.centre, applied(transposed(_ownTurn(mover)),
                                         minus(place, mover.place)))
