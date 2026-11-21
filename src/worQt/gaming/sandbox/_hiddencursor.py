"""
HiddenCursor is the mouse cursor hidden through the X server's own
'XFixesHideCursor' while a surface has the pointer taken (user,
2026-11-18: "when i open the inventory the mouse escapes", "This has to
be fixed!"). Qt's 'BlankCursor' is a cursor of clear pixels: Xwayland
counts it as shown, and only while its cursor is truly hidden does it
answer a warp (the pointer put back in the middle, '_pointer') by
locking the pointer and sending its moves as motions ('relative
pointer'); gamescope holds the mouse in its window only while that lock
is there and the cursor's image is empty. Hidden so, the lock is made at
the first warp; shown again ('shown'), Xwayland lets it go. Off X11 (Qt
on another platform: nothing warps there; or no Qt app running) it does
nothing.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import ctypes

from PySide6.QtGui import QGuiApplication

#  XFixes' version asked for: 'HideCursor' and 'ShowCursor' came in 4.
_XFIXES = 4


class HiddenCursor:
  """
  HiddenCursor holds its own connection to the X server Qt draws on (its
  'DISPLAY'; none off X11: 'live' False): 'hidden' hides the cursor
  ('held' while so), answered before it returns (the warp Qt sends next
  must come after it), 'shown' shows it again. The server hides it on
  the whole screen whichever window is named: the root is named, never
  gone. Raises if Qt is on X11 and the X libraries or XFixes 4 are
  missing.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  live: bool
  held: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.live, self.held = False, False
    self._x11, self._fixes, self._display, self._root = None, None, None, 0
    if not drawnOnX():
      return
    x11 = ctypes.CDLL('libX11.so.6')
    fixes = ctypes.CDLL('libXfixes.so.3')
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XDefaultRootWindow.restype = ctypes.c_ulong
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    fixes.XFixesQueryVersion.argtypes = [
      ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
      ctypes.POINTER(ctypes.c_int)]
    fixes.XFixesHideCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    fixes.XFixesShowCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    display = x11.XOpenDisplay(None)
    if not display:
      raise RuntimeError('cannot open the X display Qt draws on')
    major, minor = ctypes.c_int(_XFIXES), ctypes.c_int(0)
    if not fixes.XFixesQueryVersion(display, ctypes.byref(major),
                                    ctypes.byref(minor)) \
        or major.value < _XFIXES:
      raise RuntimeError('the X server has no XFixes %d (has %d.%d)'
                         % (_XFIXES, major.value, minor.value))
    self._x11, self._fixes, self._display = x11, fixes, display
    self._root = x11.XDefaultRootWindow(display)
    self.live = True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hidden(self, ) -> None:
    """The 'hidden' method hides the cursor, the server done with it
    before it returns."""
    if not self.live or self.held:
      return
    self._fixes.XFixesHideCursor(self._display, self._root)
    self._x11.XSync(self._display, 0)
    self.held = True

  def shown(self, ) -> None:
    """The 'shown' method shows the cursor again, if hidden."""
    if not self.live or not self.held:
      return
    self._fixes.XFixesShowCursor(self._display, self._root)
    self._x11.XFlush(self._display)
    self.held = False


def drawnOnX() -> bool:
  """Returns whether a Qt app is running on X11 ('xcb'; without an app
  'QGuiApplication.platformName' says the default, not the one used)."""
  if QGuiApplication.instance() is None:
    return False
  return True if QGuiApplication.platformName() == 'xcb' else False
