"""
SandboxApp opens a sandbox world, the player's avatar in it, seen
through its eyes; which world, a subclass says ('worldOf').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os

from worQt.app import App

from ._avatar import PERSON, Avatar
from ._gravitygun import GravityGun
from ._item import ITEMS
from ._sandboxwindow import SandboxWindow


class SandboxApp(App):
  """
  SandboxApp opens a 'SandboxWindow' on the world a subclass makes
  ('worldOf'), the player's avatar entered at its spawn point, the
  gravity gun in its hotbar's first slot, the GUI spawning 'ITEMS'. On
  a Wayland desktop it runs through XWayland ('xcb'), unless a platform
  is asked for: Wayland lets no program move the pointer, so the hidden
  pointer could not be kept in the middle while looking round.
  """

  __window_class__ = SandboxWindow

  def __init__(self, *args) -> None:
    if os.environ.get('WAYLAND_DISPLAY') and os.environ.get('DISPLAY'):
      os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
    App.__init__(self, *args)

  def worldOf(self, ) -> object:
    """The 'worldOf' method returns the world the sandbox opens on (a
    'World'), made anew."""
    raise NotImplementedError(type(self).__name__)

  def made(self, ) -> tuple:
    """The 'made' method returns a world made anew ('worldOf') and the
    player's avatar entered in it, the gravity gun in its hotbar's
    first slot (the window's start, and each 'Reset world')."""
    world = self.worldOf()
    avatar = Avatar(PERSON)
    avatar.hotbar.put(0, GravityGun())
    avatar.enter(world)
    return world, avatar

  def _createWindow(self, ) -> None:
    """Makes the window on the subclass's world, the avatar entered."""
    self.__main_window__ = SandboxWindow(self.made, ITEMS)
