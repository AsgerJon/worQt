"""
MouseClickSettings exposes the mouse click settings from the settings file
in the 'etc' directory.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractSettings, SettingsField

if TYPE_CHECKING:  # pragma: no cover
  pass


class MouseClickSettings(AbstractSettings):
  """
  MouseClickSettings exposes the mouse click settings from the settings file
  in the 'etc' directory.

  The settings file is at: 'etc/mouse_click_settings.json'. The settings
  available are timings and tolerances used to interpret user actions as
  mouse clicks.

  - pressTime (int): If a mouse button is pressed for longer than this
  time, the following release will not be interpreted as a click.
  - releaseTime (int): After a mouse button is released, this time allows
  another press to be interpreted as a click that is part of the current
  user command. Once exceeded, the click event propagates and the next
  press is understood as a new independent user command.
  - holdTime (int): To submit a 'press-hold' command, this the time the
  mouse button must be held.

  - pressRadius (int): For user action to be interpreted as a click,
  the distance between  cursor positions at press and release, must not
  exceed this value. If it does, the user action is interpreted as being
  'undefined'. This permits a user to cancel a click before whilst the
  button is still pressed, by moving the cursor. This reflex is commonly
  seen among users, and is now specifically interpreted to mean that the
  user action should not be understood as anything.
  - releaseRadius (int): Following a release, the system waits for a
  potential press to concatenate another click to the user command.
  However, if the cursor moves more than this distance, the waiting click
  propagates immediately instead of waiting for a potential press. Users
  will typically move the cursor to a widget a submit a click and then
  immediately move the cursor to the next action. This setting causes the
  click to propagate without waiting for the double click window.
  - holdRadius (int): For a user action to be interpreted as a
  'press-hold' action, the cursor must not move more than this distance
  from the press position. Please note that the 'BaseWidget'
  implementation implements in the 'mouseMoveEvent' method a check if the
  'press-hold' timer is running and then if the cursor is further away
  from the press position than this radius, the 'press-hold' is cancelled.
  It does not simply check the positions at the press moment and the hold
  timeout moment. If at any point this radius is exceeded, the action is
  cancelled.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __file_name__ = 'mouse_click_settings.json'

  #  Public Variables
  pressTime = SettingsField[int](100)
  releaseTime = SettingsField[int](100)
  holdTime = SettingsField[int](500)
  pressRadius = SettingsField[int](10)
  releaseRadius = SettingsField[int](10)
  holdRadius = SettingsField[int](10)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
