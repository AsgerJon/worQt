"""
GUI is the screen E opens (user, 2026-11-15: "like in minecraft when you
open the inventory ... In avatar only mode, or 'walking' i suppose, this
would open the menu where you can spawn stuff in like a ball"), drawn in
the scene ('Viewport.menuShown'), no window of its own (user,
2026-11-16: "I click on another window in wayland, the previous window
don't get to take the keyboard focus back!": as a popup window it
grabbed the keyboard and, closing, handed the focus back to the scene).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._viewport import Viewport


class GUI(QObject):
  """
  GUI is the screen over the middle of the view ('viewport' draws it):
  on foot, the items there are to spawn ('items'), a button each; a
  click emits 'picked' with that item. In a vehicle (user, 2026-11-16:
  "in vehicle key_E should open vehicle relevant menu"), the vehicle's:
  its name, what it says of itself ('readout') and 'Get out' (emits
  'leaveAsked'). Below either 'Respawn' (emits 'respawnAsked') and
  'Reset world' ('resetAsked'; user, 2026-11-16: "the normal E menu
  needs to have respawn and reset"), each shutting the screen back to
  looking round. 'opened' opens it, 'shut' shuts it ('closed' says
  whether back to looking round: by E or a button; by Esc or a click
  beside it, the mouse stays free); 'open' says whether it is.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  picked = Signal(object)
  closed = Signal(bool)
  respawnAsked = Signal()
  resetAsked = Signal()
  leaveAsked = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  items: tuple
  viewport: Viewport
  open: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, items: tuple, viewport: Viewport) -> None:
    QObject.__init__(self, )
    self.items, self.viewport, self.open = tuple(items), viewport, False
    viewport.menuPicked.connect(self._picked)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def opened(self, vehicle: object = None, states: tuple = ()) -> None:
    """The 'opened' method opens the screen: on foot the items to spawn,
    in 'vehicle' its own (its bodies as in 'states')."""
    world = (('Respawn', 'respawn'), ('Reset world', 'reset'))
    if vehicle is None:
      self.viewport.menuShown('Spawn  (E or Esc closes)', '', [
        (item.name, 'item:%d' % k) for k, item in enumerate(self.items)],
        world)
    else:
      self.viewport.menuShown('%s  (E or Esc closes)' % vehicle.name,
                              vehicle.readout(states),
                              [('Get out  (Shift)', 'leave')], world)
    self.open = True

  def shut(self, byE: bool) -> None:
    """The 'shut' method shuts the screen, 'closed' saying whether back
    to looking round ('byE')."""
    if not self.open:
      return
    self.viewport.menuHidden()
    self.open = False
    self.closed.emit(byE)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _picked(self, key: str) -> None:
    """A click on the screen: an item spawned (the screen stays), a
    world's button or 'Get out' (the screen shut back to looking round
    first), beside it ('close': shut, the mouse free)."""
    if not self.open:
      return
    if key == 'close':
      self.shut(False)
    elif key.startswith('item:'):
      self.picked.emit(self.items[int(key[5:])])
    else:
      self.shut(True)
      asked = {'respawn': self.respawnAsked, 'reset': self.resetAsked,
               'leave': self.leaveAsked}[key]
      asked.emit()
