"""
GenericFamilyNum enumerates 'serif', 'sans' and 'mono'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.keenum import KeeNum, Kee
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

from . import FontFamilyNum, FontFamilyMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, Type, TypeAlias, Self

  FontFamilyNumField: TypeAlias = Union[Field, FontFamilyNum]


class GenericFamilyNum(KeeNum, ):
  """
  GenericFamilyNum enumerates 'serif', 'sans' and 'mono'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations

  MONO: Self = Kee[str]('mono')
  SANS: Self = Kee[str]('sans')
  SERIF: Self = Kee[str]('serif')

  #  Virtual Variables

  default: FontFamilyNumField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @default.GET
  def _getFamily(self, **kwargs) -> FontFamilyNum:
    if self is self.MONO:
      return FontFamilyNum.defaultMono
    if self is self.SANS:
      return FontFamilyNum.defaultSans
    if self is self.SERIF:
      return FontFamilyNum.defaultSerif
    raise RuntimeError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  METACLASS METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_resolve__(cls, identifier: FontFamilyNum) -> Self:
    try:
      name = getattr(identifier, 'name')
    except AttributeError as attributeError:
      name, value = 'identifier', identifier
      raise TypeException(name, value, FontFamilyNum) from attributeError
    else:
      if name in FontFamilyMeta.__mono_space__:
        return cls.MONO
      if name in FontFamilyMeta.__sans_space__:
        return cls.SANS
      if name in FontFamilyMeta.__serif_space__:
        return cls.SERIF
      infoSpec = """Received unrecognized font family name: '%s'!"""
      info = textFmt(infoSpec % name)
      raise ValueError(info)
