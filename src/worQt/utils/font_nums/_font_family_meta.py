"""
FontMeta subclasses 'KeeMeta' and provides the metaclass for the font
family enumeration. The 'FontSpace' namespace class provides all the
custom functionality required. This metaclass preserves the behaviour of
the 'KeeMeta' except for replacing the namespace returned from
'__prepare__' with a 'FontSpace' instance.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from worktoy.desc import Field
from worktoy.keenum import KeeMeta, Kee

from . import FontFamilySpace, FontMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias

  Bases: TypeAlias = tuple[type, ...]


class FontFamilyMeta(FontMeta):
  """
  FontMeta subclasses 'KeeMeta' and provides the metaclass for the font
  family enumeration. The 'FontSpace' namespace class provides all the
  custom functionality required. This metaclass preserves the behaviour of
  the 'KeeMeta' except for replacing the namespace returned from
  '__prepare__' with a 'FontSpace' instance.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __sans_serif__ = (
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
  __serif_families__ = (
    'FreeSerif',
    'Liberation Serif',
    'LiterationSerif',
    'Nimbus Roman',
    'Noto Serif',
    'Tinos',
    'URW Bookman',
    'IosevkaTermSlab',
    )

  __mono_space__ = (
    'Adwaita Mono',
    'Agave',
    'AnonymicePro',
    'AtkynsonMono',
    'BigBlueTermPlus',
    'BitstromWera',
    'BlexMono',
    'Cascadia Code',
    'Cascadia Code PL',
    'Cascadia Mono',
    'Cascadia Mono PL',
    'CaskaydiaCove',
    'CaskaydiaMono',
    'CodeNewRoman',
    'ComicShannsMono',
    'CommitMono',
    'Cousine',
    'DaddyTimeMono',
    'EnvyCodeR',
    'FiraCode',
    'FiraMono',
    'FreeMono',
    'GeistMono',
    'GoMono',
    'Hack',
    'Hasklug',
    'HeavyData',
    'Hurmit',
    'Inconsolata',
    'Inconsolata LGC',
    'InconsolataGo',
    'IntoneMono',
    'Iosevka',
    'IosevkaTerm',
    'JetBrainsMono',
    'JetBrainsMonoNL',
    'Lekton',
    'Liberation Mono',
    'Lilex',
    'LiterationMono',
    'MartianMono',
    'MesloLG',
    'MesloLGL',
    'MesloLGLDZ',
    'MesloLGMDZ',
    'MesloLGS',
    'MesloLGSDZ',
    'MonaspiceAr',
    'MonaspiceKr',
    'MonaspiceNe',
    'MonaspiceRn',
    'MonaspiceXe',
    'Monofur',
    'Monoid',
    'Mononoki',
    'Nimbus Mono PS',
    'Noto Sans Mono',
    'NotoMono',
    'OpenDyslexic',
    'OpenDyslexicAlt',
    'ProFont IIx',
    'ProFontWindows',
    'ProggyClean',
    'ProggyClean CE',
    'ProggyCleanSZ',
    'RecMonoCasual',
    'RecMonoDuotone',
    'RecMonoLinear',
    'RecMonoSmCasual',
    'SauceCodePro',
    'ShureTechMono',
    'SpaceMono',
    'Terminess',
    'UbuntuMono',
    'VictorMono',
    'ZedMono',
    'iMWritingDuo',
    'iMWritingMono',
    'iMWritingQuat',
    )
  __good_serif__ = (
    'Noto Serif',
    'Liberation Serif',
    'Tinos',
    )
  __good_sans__ = (
    'Montserrat',
    'Adwaita Sans',
    'Noto Sans',
    'Roboto',
    'Ubuntu',
    )
  __good_mono__ = (
    'JetBrainsMono',
    'FiraMono',
    'IosevkaTerm',
    'Cascadia Code',
    'Hack',
    )

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  defaultSerif = Field()
  defaultSans = Field()
  defaultMono = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @defaultSerif.GET
  def _getDefaultSerif(cls, ) -> Any:
    goodSerifs = [f.lower() for f in cls.__good_serif__]
    midSerifs = [f.lower() for f in cls.__serif_families__]
    for family in cls:
      if family.value.lower() in goodSerifs:
        return family
    for family in cls:
      if family.value.lower() in midSerifs:
        return family
    return cls.FALLBACK_SERIF

  @defaultSans.GET
  def _getDefaultSans(cls, ) -> Any:
    goodSans = [f.lower() for f in cls.__good_sans__]
    midSans = [f.lower() for f in cls.__sans_serif__]
    for family in cls:
      if family.value.lower() in goodSans:
        return family
    for family in cls:
      if family.value.lower() in midSans:
        return family
    return cls.FALLBACK_SANS

  @defaultMono.GET
  def _getDefaultMono(cls, ) -> Any:
    goodMonos = [f.lower() for f in cls.__good_mono__]
    midMonos = [f.lower() for f in cls.__mono_space__]
    for family in cls:
      if family.value.lower() in goodMonos:
        return family
    for family in cls:
      if family.value.lower() in midMonos:
        return family
    return cls.FALLBACK_MONO

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kw, ) -> FontFamilySpace:
    return FontFamilySpace(mcls, name, bases, **kw)

  def __getattr__(cls, key: str, ) -> Any:
    #  Dunder/internal names are never font families. Deferring here also
    #  stops this hook recursing when worktoy probes private attributes.
    if str.startswith(key, '__') and str.endswith(key, '__'):
      return type.__getattribute__(cls, key)  # expected to raise
    #  Dynamic creation needs a running app and a finished enumeration:
    #  during class construction '_createMembers' probes member names by
    #  'getattr', and the registry it appends to does not exist yet.
    if QApplication.instance() is None:
      return type.__getattribute__(cls, key)  # expected to raise again
    if cls.__dict__.get('__registered_members__') is None:
      return type.__getattribute__(cls, key)  # still building members
    fontFamilies = QFontDatabase.families()
    keyParts = str.split(str.lower(key), '_')
    for family in fontFamilies:
      familyName = str(family).lower()
      for keyPart in keyParts:
        if keyPart not in family.lower():
          break
        familyName = str.replace(familyName, keyPart, '', 1)
      else:
        if str.strip(familyName):
          continue  # Name has parts not in key, so skip.
        kee = Kee[str](family)
        kee.name = str.upper(key)  # Kee requires an upper-case name
        kee.index = len(cls.__registered_members__)
        cls.__allow_instantiation__ = True
        num = cls(kee, )
        cls.__allow_instantiation__ = False
        setattr(cls, key, num)
        cls.__registered_members__ = (*cls.__registered_members__, num)
        break  # breaks out of else clause, restarting
    else:  # Found no match
      return type.__getattribute__(cls, key)  # expected to raise again
    return getattr(cls, key)  # should run the getter again.
