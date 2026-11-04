"""
GenericFamilyNum enumerates the three kinds of font a widget asks for when
it cares about the look but not the exact face: 'SERIF', 'SANS' and
'MONO'. Its 'family' is the best family of that kind installed on this
system: the first installed from a short list of preferred families, else
from a longer list of acceptable ones, else whatever Qt itself picks for
that kind. So code can always ask for 'MONO' and get a monospaced font,
on any machine.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from worktoy.desc import Field
from worktoy.keenum import KeeNum, Kee

from . import FontFamily

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias

  Families: TypeAlias = tuple[str, ...]

_PREFERRED_SERIF = ('Noto Serif', 'Liberation Serif', 'Tinos',)
_WIDER_SERIF = (
  'FreeSerif',
  'Liberation Serif',
  'LiterationSerif',
  'Nimbus Roman',
  'Noto Serif',
  'Tinos',
  'URW Bookman',
  'IosevkaTermSlab',
)
_PREFERRED_SANS = (
  'Montserrat', 'Adwaita Sans', 'Noto Sans', 'Roboto', 'Ubuntu',)
_WIDER_SANS = (
  'Adwaita Sans',
  'Arimo',
  'DejaVuSans',
  'DroidSans',
  'FantasqueSans',
  'FreeSans',
  'Liberation Sans',
  'LiterationSans',
  'Montserrat',
  'Nimbus Sans Narrow',
  'Noto Sans',
  'Overpass',
  'Roboto',
  'Roboto Condensed',
  'URW Gothic',
  'Ubuntu',
)
_PREFERRED_MONO = (
  'JetBrainsMono', 'FiraMono', 'IosevkaTerm', 'Cascadia Code', 'Hack',)
_WIDER_MONO = (
  'Adwaita Mono', 'Agave', 'AnonymicePro', 'AtkynsonMono',
  'BigBlueTermPlus', 'BitstromWera', 'BlexMono', 'Cascadia Code',
  'Cascadia Code PL', 'Cascadia Mono', 'Cascadia Mono PL', 'CaskaydiaCove',
  'CaskaydiaMono', 'CodeNewRoman', 'ComicShannsMono', 'CommitMono',
  'Cousine', 'DaddyTimeMono', 'EnvyCodeR', 'FiraCode', 'FiraMono',
  'FreeMono', 'GeistMono', 'GoMono', 'Hack', 'Hasklug', 'HeavyData',
  'Hurmit', 'Inconsolata', 'Inconsolata LGC', 'InconsolataGo',
  'IntoneMono', 'Iosevka', 'IosevkaTerm', 'JetBrainsMono',
  'JetBrainsMonoNL', 'Lekton', 'Liberation Mono', 'Lilex',
  'LiterationMono', 'MartianMono', 'MesloLG', 'MesloLGL', 'MesloLGLDZ',
  'MesloLGMDZ', 'MesloLGS', 'MesloLGSDZ', 'MonaspiceAr', 'MonaspiceKr',
  'MonaspiceNe', 'MonaspiceRn', 'MonaspiceXe', 'Monofur', 'Monoid',
  'Mononoki', 'Nimbus Mono PS', 'Noto Sans Mono', 'NotoMono',
  'OpenDyslexic', 'OpenDyslexicAlt', 'ProFont IIx', 'ProFontWindows',
  'ProggyClean', 'ProggyClean CE', 'ProggyCleanSZ', 'RecMonoCasual',
  'RecMonoDuotone', 'RecMonoLinear', 'RecMonoSmCasual', 'SauceCodePro',
  'ShureTechMono', 'SpaceMono', 'Terminess', 'UbuntuMono', 'VictorMono',
  'ZedMono', 'iMWritingDuo', 'iMWritingMono', 'iMWritingQuat',
)

#  For each member value: the preferred families, the acceptable ones, and
#  the style hint for asking Qt when none of them is installed.
_KINDS = {
  'serif': (_PREFERRED_SERIF, _WIDER_SERIF, QFont.StyleHint.Serif),
  'sans': (_PREFERRED_SANS, _WIDER_SANS, QFont.StyleHint.SansSerif),
  'mono': (_PREFERRED_MONO, _WIDER_MONO, QFont.StyleHint.Monospace),
}


class GenericFamilyNum(KeeNum):
  """
  GenericFamilyNum enumerates 'SERIF', 'SANS' and 'MONO'; each member's
  'family' is the best installed family of that kind.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  SERIF = Kee[str]('serif')
  SANS = Kee[str]('sans')
  MONO = Kee[str]('mono')

  #  Virtual Variables
  family: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @family.GET
  def _getFamily(self, ) -> str:
    """
    The 'family' getter returns the installed family this member means on
    this system. It needs a running 'QApplication'.
    """
    family = self.familyAmong(FontFamily.installed())
    if family is not None:
      return family
    _, _, hint = _KINDS[self.value]
    return FontFamily.hinted(hint)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def familyAmong(self, installed: Families) -> Optional[str]:
    """
    The 'familyAmong' method returns the family of this kind that it would
    choose from 'installed': the first preferred family present, else the
    first acceptable one, else 'None'. A plain method, not an '@overload':
    a frozen 'KeeNum' member rejects the dispatcher's caching.
    """
    preferred, wider, _ = _KINDS[self.value]
    return FontFamily.pick(installed, *preferred, *wider)

  def apply(self, font: QFont) -> QFont:
    """
    The 'apply' method sets this member's family on 'font' and returns it.
    """
    font.setFamily(self.family)
    return font
