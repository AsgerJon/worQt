"""
BoxModel subclasses 'BaseObject' and encapsulates the box model of a widget.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from . import InSets

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias


class BoxModel(BaseObject):
  """
  BoxModel subclasses 'BaseObject' and encapsulates the box model of a
  widget. It implements margin, border and padding as properties. These
  are implemented as 'InSets' objects through the 'AttriBox' descriptor.

  Attributes
  ----------
  margin : InSets
      The margin of the box model.
  border : InSets
      The border of the box model.
  padding : InSets
      The padding of the box model.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  margin = AttriBox[InSets]()
  border = AttriBox[InSets]()
  padding = AttriBox[InSets]()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(InSets, InSets, InSets)
  def __init__(self, *args, ) -> None:
    self.margin, self.border, self.padding = args

  @overload(int, int, int, int, int, int, int, int, int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.margin = InSets(*args[0:4])
    self.border = InSets(*args[4:8])
    self.padding = InSets(*args[8:12])

  @overload(int, int, int)
  def __init__(self, *args, ) -> None:
    self.margin = InSets(args[0])
    self.border = InSets(args[1])
    self.padding = InSets(args[2])

  @overload()
  def __init__(self, ) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self) -> str:
    marginStr: str = str(self.margin)
    borderStr: str = str(self.border)
    paddingStr: str = str(self.padding)
    dimDict: dict[str, str] = dict(
        margin=marginStr,
        border=borderStr,
        padding=paddingStr
    )
    dimLines = (*('%s: %s' % (k, v) for (k, v) in dict.items(dimDict, )),)
    dimStr = '<br><tab>'.join(dimLines)
    clsName: str = type(self).__name__
    infoSpec: str = """%s object:<br><tab>%s"""
    return infoSpec % (clsName, dimStr)

  def __repr__(self, ) -> str:
    marginRepr: str = repr(self.margin)
    borderRepr: str = repr(self.border)
    paddingRepr: str = repr(self.padding)
    dimDict: dict[str, str] = dict(
        margin=marginRepr,
        border=borderRepr,
        padding=paddingRepr
    )
    dimLines = (*('%s=%s' % (k, v) for (k, v) in dict.items(dimDict, )),)
    dimStr = ', '.join(dimLines)
    clsName: str = type(self).__name__
    infoSpec: str = """%s(%s)"""
    return infoSpec % (clsName, dimStr)
