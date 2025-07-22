"""PlaySound encapsulates sound effects. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QUrl, Slot
from PySide6.QtMultimedia import QSoundEffect
from worktoy.desc import Field
from worktoy.utilities import maybe

from worQt.desQt import Etc

if TYPE_CHECKING:  # pragma: no cover
  pass


class PlaySound(QSoundEffect):
  """PlaySound encapsulates sound effects."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  fallback variables
  __fallback_sound__ = 'startup.wav'
  __fallback_volume__ = 0.9

  #  private variables
  __sound_effect__ = None
  __relative_volume__ = None

  #  public variables
  relVolume = Field()
  etc = Etc()

  #  getter methods
  @relVolume.GET
  def _getRelativeVolume(self, ) -> float:
    """Get the relative volume."""
    return maybe(self.__relative_volume__, self.__fallback_volume__)

  #  private methods

  def _getSoundURL(self, ) -> QUrl:
    """Get the sound effect."""
    return QUrl.fromLocalFile()

  @Slot()
  def play(self, ) -> None:
    """Readies the sound effect for playback."""
    self.setSource(self._getSoundURL())
    self.setVolume(self.relVolume)
    if TYPE_CHECKING:
      assert isinstance(QSoundEffect.Loop.Infinite, int)
    self.setLoopCount(QSoundEffect.Loop.Infinite)
    QSoundEffect.play(self)
