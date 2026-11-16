"""
Item is a thing the GUI spawns into a world (user, 2026-11-15: "a gui
where i can spawn items or whatever"); 'ITEMS' are those there are.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.phys._body import Body, State
from worQt.phys._shape import Sphere, boxShape

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._world import World


class Item:
  """
  Item is a thing to spawn: its 'name', its 'body' (a phys 'Body'), how it
  meets everything in the world ('law': a 'Contact''s stiffness,
  damping, grip, bristle, its damping, and for a solid with edges how
  far apart its skin's points are) and how it is drawn ('look': its
  colour, 0 to 255 a channel, metalness and roughness).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  name: str
  body: Body
  law: tuple
  look: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, body: Body, law: tuple,
               look: tuple) -> None:
    self.name, self.body, self.law, self.look = name, body, law, look

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def spawned(self, world: World, place: tuple) -> int:
    """The 'spawned' method puts one into 'world', still, its middle at
    'place', and returns its index there."""
    key = 'item: %s' % self.name
    world.looks[key] = self.look
    return world.spawned(self.body, State(tuple(place)), self.law, key)


#  The items there are: an oak ball 300 mm across (9.9 kg) and a wooden
#  crate 500 mm a side (20 kg), as the yard's; wood on anything: grip
#  0.5, the crate's skin a point every 5 cm.
ITEMS = (Item('Ball', Body.of(Sphere(0.15), 700.0),
              (2e5, 2.0, 0.5, 2e5, 400.0), ((176, 128, 78), 0.0, 0.7)),
         Item('Crate', Body.of(boxShape(0.5, 0.5, 0.5), 160.0),
              (2e5, 2.0, 0.5, 2e5, 200.0, 0.05),
              ((156, 112, 64), 0.0, 0.85)))
