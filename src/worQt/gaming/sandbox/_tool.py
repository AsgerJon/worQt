"""
Tool is an item held in the avatar's hands with a behaviour of its own
(user, 2026-11-15: "These are held items just like in minecraft that
each specify a particular behaviour").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._avatar import Avatar

#  Where the avatar's right hand grips a tool in the eyes' frame (x
#  right, y up, z back, m), and the way its grip runs from there (the
#  hand's own z axis: tilted 15 degrees back).
GRIP = (0.34, -0.235, -0.43)
GRIP_ALONG = (0.0, 0.2588, 0.9659)


class Tool:
  """
  Tool is a held item: its 'name'; its 'icon' (an image file shown in the
  hotbar; '': the name is shown instead); how it is seen in the hands
  ('parts': boxes, each its size, its middle, the way its own z axis points,
  and its colour, 0 to 255 a channel; 'label': words painted on it, its text,
  middle, turn about the eyes' y, degrees, colour and height; 'model': a glTF
  file shown there too, its file, where its origin goes, its turn, degrees
  about x, y and z, and its size, m a unit of its own, None: none; all in the
  eyes' frame, m: x right, y up, z back, the look along -z; held at 'GRIP');
  when it last punched something ('punched': s on the perf counter, None:
  never), how many things it has launched held ('yeets') and shoved
  ('punts'), how it hums ('humming': 0 not at all, 1 idle, 2 holding) and
  where it glows while it holds ('glow': a point in the eyes' frame, m; None:
  nowhere); what the mouse's buttons do with it ('pressed' and 'released',
  each 'left' or 'right', on the window's thread); what the wheel does
  ('wheeled', True when the tool took the turn); what it does each step of
  the world its avatar is in ('acted', on the world's thread); what it leaves
  when put away ('putAway'); and the bodies it marks for the view ('pointed',
  'held': indices, or None). This base does nothing: an empty hand.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  name: str = ''
  icon: str = ''
  parts: tuple = ()
  label: tuple = None
  model: tuple = None
  glow: tuple = None

  #  Public Variables
  pointed: int
  held: int
  punched: float
  yeets: int
  punts: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.pointed, self.held, self.punched = None, None, None
    self.yeets, self.punts = 0, 0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def humming(self, ) -> int:
    """The 'humming' property is how the tool hums: not at all here."""
    return 0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def pressed(self, button: str) -> None:
    """The 'pressed' method takes a mouse button just pressed ('left' or
    'right'). Nothing here."""

  def released(self, button: str) -> None:
    """The 'released' method takes a mouse button let go. Nothing
    here."""

  def wheeled(self, notches: float) -> bool:
    """The 'wheeled' method takes the wheel turned 'notches' (away from
    the player positive) and tells whether it used them. Not here."""
    return False

  def acted(self, avatar: Avatar, states: list, seconds: float) -> None:
    """The 'acted' method does what the tool does for the step of
    'seconds' to come, in the hands of 'avatar' (its world's 'states',
    changed in place). Nothing here."""

  def putAway(self, ) -> None:
    """The 'putAway' method lets go of whatever the tool held, as it
    leaves the hands."""
    self.pointed, self.held = None, None
