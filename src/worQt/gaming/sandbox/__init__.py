"""
The 'worQt.gaming.sandbox' package is the sandbox (user, 2026-11-15: "we
are going to force the terminology from minecraft upon ourselves"), each
of its concepts a class of its own:

- World: a world, what is fixed in it and what is spawned into it,
  stepping itself.
- Universe: the constants a world's physics obeys (gravity).
- Avatar: the player's body in a world, the vehicle never exited; its
  'Hotbar' holds nine slots of tools.
- Tool: a held item with a behaviour ('GravityGun': pull, hold, punt).
- GUI: the screen E opens; on foot, the 'Item's to spawn ('ITEMS').
- Vehicle: what an avatar rides (E boards it, Shift leaves it): its
  bodies put in a world, a seat on its frame the rider is tied to.
- FourthPeep: a control in the world the player uses (E, looking at it
  within reach): a lever (or a toggle's bat), its value read by what it
  works; and its kinds (user, 2026-11-16: "*Every* fourtpeep input ...
  must visibly deform when activated"): 'Pushbutton' (a key, sinking in
  and springing back, or latched), 'Knob' (clicking through notches, or
  on and on), 'Slider' (a slide control).

It is the general base (user, 2026-11-16: "This must be the general
base stuff"): it has no world of its own; a package on it makes its
worlds and opens one ('SandboxApp.worldOf'), as 'worQt.gaming.trains'
does with the loop de loop in the void.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._universe import EARTH_GRAVITY, MOON_GRAVITY, Universe
from ._world import World
from ._avatar import PERSON, Avatar
from ._tool import Tool
from ._vehicle import Vehicle
from ._fourthpeep import FourthPeep
from ._pushbutton import Pushbutton
from ._knob import Knob
from ._slider import Slider
from ._gravitygun import GravityGun
from ._hotbar import SLOTS, Hotbar
from ._item import ITEMS, Item

__all__ = (
  'EARTH_GRAVITY',
  'MOON_GRAVITY',
  'Universe',
  'World',
  'PERSON',
  'Avatar',
  'Tool',
  'Vehicle',
  'FourthPeep',
  'Pushbutton',
  'Knob',
  'Slider',
  'GravityGun',
  'SLOTS',
  'Hotbar',
  'ITEMS',
  'Item',
)
