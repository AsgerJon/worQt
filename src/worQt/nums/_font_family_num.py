"""
FontFamilyNum enumerates the available font families.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import KeeNum, Kee
from worktoy.waitaminute import attributeErrorFactory

from . import FontFamilies


class FontFamilyNum(KeeNum):
  """FontFamilyNum enumerates the available font families."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  families = FontFamilies()

  #  Enumerations
  MONTSERRAT = Kee[str]('Montserrat')
  DEJAVU = Kee[str]('DejaVu Sans')
  ROBOTO = Kee[str]('Roboto')
  INCONSOLATA = Kee[str]('Inconsolata')
  MONOSPACE = Kee[str]('Monospace')
  MESLOLGS = Kee[str]('MesloLGS NF')
  ADWAITA = Kee[str]('Adwaita Mono')
  LIBERATION = Kee[str]('Liberation Mono')
  CANTARELL = Kee[str]('Cantarell')

  @classmethod
  def __class_getattr__(cls, key: str) -> Kee[str]:
    """Returns the Kee instance for the given font family name."""
    for name in cls.families:
      if key.lower().replace(' ', '') == name.lower().replace(' ', ''):
        return name
    raise attributeErrorFactory(cls, key)
