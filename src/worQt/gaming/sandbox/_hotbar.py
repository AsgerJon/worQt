"""
Hotbar is the avatar's row of held items (user, 2026-11-15: "a hotbar
with nine items where the first one will be the gravity gun").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._tool import Tool

#  How many slots the hotbar has.
SLOTS = 9


class Hotbar:
  """
  Hotbar holds 'SLOTS' slots, each a 'Tool' or None (an empty hand), one
  of them 'selected': its tool is the one in the avatar's hands. A tool
  is put away (it lets go of what it held) when another slot is
  selected. Selecting wraps round the ends ('scrolled').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  slots: list
  selected: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.slots, self.selected = [None] * SLOTS, 0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def put(self, index: int, tool: Tool) -> None:
    """The 'put' method puts 'tool' (or None) in slot 'index'."""
    if not 0 <= index < SLOTS:
      raise IndexError('the hotbar has slots 0 to %d, not %r'
                       % (SLOTS - 1, index))
    self.slots[index] = tool

  def tool(self, ) -> Tool:
    """The 'tool' method returns the tool in the hands (None: empty)."""
    return self.slots[self.selected]

  def select(self, index: int) -> None:
    """The 'select' method takes slot 'index' into the hands, putting
    away the tool that was there."""
    if not 0 <= index < SLOTS:
      raise IndexError('the hotbar has slots 0 to %d, not %r'
                       % (SLOTS - 1, index))
    if index == self.selected:
      return
    held = self.tool()
    if held is not None:
      held.putAway()
    self.selected = index

  def scrolled(self, steps: int) -> None:
    """The 'scrolled' method selects the slot 'steps' on (back where
    negative), round the ends."""
    self.select((self.selected + steps) % SLOTS)

  def names(self, ) -> list:
    """The 'names' method returns each slot's tool's name ('' empty)."""
    return [('' if tool is None else tool.name) for tool in self.slots]

  def icons(self, ) -> list:
    """The 'icons' method returns each slot's tool's icon file ('' for
    none)."""
    return [('' if tool is None else tool.icon) for tool in self.slots]
