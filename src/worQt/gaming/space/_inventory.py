"""
Inventory is what Asger carries (user, 2026-11-17: "Give Asger a hotbar
and an inventory like in minecraft. then one tool is the gravgun, then
give Asger also a telescope, if possible. Finally, put some commandobars
in Asgers inventory"): Minecraft's, a hotbar of 'HOTBAR' slots (the
first of 'SLOTS') over the rest, each slot empty or a stack of one kind
of item, no more than its kind's stack; one hotbar slot selected (what
is in his hand); open, a stack picked up on the pointer ('carried')
moves between slots by clicks as Minecraft's does. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  The slots: the hotbar's first (keys 1 to 9), then three rows of nine.
HOTBAR = 9
SLOTS = 36
#  The kinds of item, by their names: what they are called, how many
#  stack in a slot, what they are for ('tool': held and used; 'food':
#  eaten one at a time).
ITEMS = {'gravgun': ('Grav-Gun', 1, 'tool'),
         'telescope': ('Telescope', 1, 'tool'),
         'commando': ('Commando bar', 16, 'food'),
         'scratchings': ('Pork scratchings', 16, 'food')}
#  What he carries to begin with: each a slot and its stack (the bars in
#  the inventory above the hotbar: user, "put some commandobars in
#  Asgers inventory"; a few bags of pork scratchings beside them: "key_E
#  should *always* open Asger's inventory, where there should be a few
#  snacks").
CARRIED = ((0, 'gravgun', 1), (1, 'telescope', 1), (HOTBAR, 'commando', 12),
           (HOTBAR + 1, 'scratchings', 4))


class Inventory:
  """
  Inventory holds Asger's stacks ('slots': each None or [kind, count]),
  the hotbar's slot selected ('selected'), and while it is open the
  stack on the pointer ('carried': None or [kind, count]). 'held' is
  the kind in his hand; 'chosen' and 'scrolled' select a hotbar slot;
  'clicked' moves stacks as Minecraft's clicks do; 'closed' puts the
  carried stack back; 'usedUp' takes one of the held stack.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  slots: list
  selected: int
  carried: list | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.slots, self.selected, self.carried = [None] * SLOTS, 0, None
    for slot, kind, count in CARRIED:
      self.slots[slot] = [kind, count]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def held(self, ) -> str | None:
    """The 'held' property is the kind of item in his hand (the selected
    hotbar slot's; None: his hand is empty)."""
    stack = self.slots[self.selected]
    return None if stack is None else stack[0]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def chosen(self, slot: int) -> None:
    """The 'chosen' method selects hotbar slot 'slot' (nought the first:
    key 1)."""
    if not 0 <= slot < HOTBAR:
      raise IndexError('hotbar slot %d of %d' % (slot, HOTBAR))
    self.selected = slot

  def scrolled(self, steps: int) -> None:
    """The 'scrolled' method moves the selection 'steps' slots on (the
    wheel), round the hotbar."""
    self.selected = (self.selected + int(steps)) % HOTBAR

  def clicked(self, slot: int, right: bool) -> None:
    """The 'clicked' method clicks slot 'slot' open, as Minecraft's
    inventory takes it: left, nothing carried, picks its stack up;
    carrying, lays the stack down there, onto the same kind as far as
    it stacks, or swaps it for another; right, nothing carried, picks
    half up; carrying, lays one down there (on nothing or the same
    kind)."""
    if not 0 <= slot < SLOTS:
      raise IndexError('slot %d of %d' % (slot, SLOTS))
    here, carried = self.slots[slot], self.carried
    if carried is None:
      if here is None:
        return
      if not right:
        self.slots[slot], self.carried = None, here
        return
      taken = (here[1] + 1) // 2
      self.carried = [here[0], taken]
      here[1] -= taken
      if here[1] == 0:
        self.slots[slot] = None
      return
    most = ITEMS[carried[0]][1]
    if right:
      if here is None:
        self.slots[slot] = [carried[0], 1]
      elif here[0] == carried[0] and here[1] < most:
        here[1] += 1
      else:
        return
      carried[1] -= 1
      if carried[1] == 0:
        self.carried = None
      return
    if here is None:
      self.slots[slot], self.carried = carried, None
    elif here[0] == carried[0]:
      moved = min(carried[1], most - here[1])
      here[1] += moved
      carried[1] -= moved
      if carried[1] == 0:
        self.carried = None
    else:
      self.slots[slot], self.carried = carried, here

  def closed(self, ) -> None:
    """The 'closed' method puts the stack carried back (onto stacks of
    its kind first, then the first empty slot; the hotbar first)."""
    carried = self.carried
    if carried is None:
      return
    most = ITEMS[carried[0]][1]
    for k, here in enumerate(self.slots):
      if carried[1] and here is not None and here[0] == carried[0]:
        moved = min(carried[1], most - here[1])
        here[1] += moved
        carried[1] -= moved
    for k, here in enumerate(self.slots):
      if carried[1] and here is None:
        self.slots[k] = [carried[0], carried[1]]
        carried[1] = 0
    if carried[1]:
      raise RuntimeError('no room for %d %s' % (carried[1], carried[0]))
    self.carried = None

  def usedUp(self, ) -> bool:
    """The 'usedUp' method takes one item of the held stack (eaten);
    returns whether there was one."""
    stack = self.slots[self.selected]
    if stack is None:
      return False
    stack[1] -= 1
    if stack[1] == 0:
      self.slots[self.selected] = None
    return True

  def rows(self, ) -> list:
    """The 'rows' method returns each slot as the view shows it: its
    kind ('' none), its count, what it is called."""
    return [{'kind': '', 'count': 0, 'title': ''} if stack is None else {
      'kind': stack[0], 'count': stack[1], 'title': ITEMS[stack[0]][0]}
            for stack in self.slots]
