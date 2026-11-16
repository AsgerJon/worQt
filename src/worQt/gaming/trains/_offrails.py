"""
A wheelset off its rails (user, 2026-11-16: "derail shouldn't mean
RuntimeError!"; then a whole steam train, its wheels of four sizes):
taken from the rail world into the small steps as a free body
('offRailsBody': its mass, centre and inertia, its shape cylinders),
everything that held it there (its axleboxes, its crank pins) a spring
and damper from the same point of its frame or rod to the same point of
it ('tookOff'), its vehicle's frames and it meeting the ground; put
back as it was made ('putBack').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from worQt.phys._assembly import Contact, Spring
from worQt.phys._body import Body, State
from worQt.phys._shape import cylinderShape
from worQt.phys._vectors import UNTURNED, turnAbout
from worQt.phys.rail import Axlebox, wheelsetBody
from worQt.phys.rail._crankpin import CrankPin
from worQt.phys.rail._wheelset import AXLE, AXLE_END, BACK, FACE
from worQt.phys.rail._wheelset import FLANGE_HIGH, NOMINAL, RADIUS
from worQt.phys.rail._wheelset import ROOT_AT, radiusOf

#  How many sides a wheel's and the axle's cylinders have.
WHEEL_SIDES, AXLE_SIDES = 24, 10


def offRailsBody(radius: float = RADIUS) -> Body:
  """The 'offRailsBody' function returns a wheelset of wheels 'radius' m
  off its rails: the wheelset's mass, centre and inertia, its shape
  cylinders of 'WHEEL_SIDES' (each wheel's flange and tread) and
  'AXLE_SIDES' (the axle, journal to journal), its axle along its own z
  as the wheelset's; made once a size."""
  return _offRailsOf(float(radius))


@functools.lru_cache(maxsize=None)
def _offRailsOf(radius: float) -> Body:
  """Returns a wheelset of wheels 'radius' m off its rails
  ('offRailsBody')."""
  wheels = wheelsetBody(radius)
  root = NOMINAL + ROOT_AT
  shape = cylinderShape(AXLE, 2.0 * AXLE_END, AXLE_SIDES)
  for side in (1.0, -1.0):
    for rim, low, high in ((radius + FLANGE_HIGH, BACK, root),
                           (radius, root, FACE)):
      shape = shape.joined(cylinderShape(rim, high - low, WHEEL_SIDES)
                           .moved((0.0, side * 0.5 * (low + high), 0.0),
                                  UNTURNED))
  shape = shape.moved((0.0, 0.0, 0.0), turnAbout((1.0, 0.0, 0.0),
                                                 0.5 * math.pi))
  return Body(wheels.mass, wheels.centre, wheels.inertia, shape)


def tookOff(world: object, index: int, states: list, law: tuple,
            frames: tuple) -> tuple:
  """The 'tookOff' function makes the wheelset at 'index' a free body of
  'world' in 'states' ('offRailsBody' of its size): each axlebox and
  crank pin that held it let go, a spring and a damper as stiff and as
  damped (its stiffness along, its damping along) from the same point
  of the same body to the same point of it instead; put back between
  its axleboxes, moving as they move, turning as it turned; it and
  'frames' (its vehicle's bodies, each once) meeting the world's own
  bodies ('world.still') by 'law' (a 'Contact''s numbers). Returns what
  it did: (the holds let go, the springs, the contacts, its radius)."""
  bodies = world.assembly.bodies
  radius = radiusOf(bodies[index])
  held = tuple(c for c in world.assembly.connections
               if isinstance(c, Axlebox) and c.wheelset == index)
  springs = []
  for hold in held:
    world.loosened(hold)
    spring = Spring(hold.frame, hold.box, index, hold.journal,
                    hold.stiffness[0], 0.0, hold.damping[0])
    world.connected(spring)
    springs.append(spring)
  world.swapped(index, offRailsBody(radius))
  boxes = [hold for hold in held if not isinstance(hold, CrankPin)]
  if boxes:
    frame = boxes[0].frame
    body, carried = bodies[frame], states[frame]
    middle = tuple(sum(box.box[c] for box in boxes) / len(boxes)
                   for c in range(3))
    middle = (middle[0], middle[1], middle[2])
    was = states[index]
    states[index] = State(body.placeOf(carried, middle), was.turn,
                          body.velocityOf(carried, middle), was.spin)
  contacts = []
  for other in sorted(world.still):
    for touched in (index,) + tuple(frames):
      contact = Contact(other, touched, *law)
      world.connected(contact)
      contacts.append(contact)
  return held, tuple(springs), tuple(contacts), radius


def putBack(world: object, index: int, record: tuple) -> None:
  """The 'putBack' function undoes 'tookOff' for the wheelset at 'index'
  ('record' what it returned): its wheelset's body again, its springs
  and contacts let go, its axleboxes and crank pins holding it again."""
  held, springs, contacts, radius = record
  world.swapped(index, wheelsetBody(radius))
  for connection in springs + contacts:
    world.loosened(connection)
  for hold in held:
    world.connected(hold)
