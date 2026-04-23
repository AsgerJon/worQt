"""
BoxModel encapsulates the box model properties for widgets. Please note
this class is not related to the classes based on 'AttriBox' despite the
similar name.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from worktoy.utilities import stringList, textFmt
from worktoy.desc import Field

from worQt.utils.geom.euclid import EuclideanObject, Dimension
from worQt.utils.geom import InSets, Rect, Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias, Self, Any, Union, Iterator

  InSetsField: TypeAlias = Union[InSets, Field]
  Keys: TypeAlias = tuple[str, str, str, str, str]


class BoxModel(BaseObject):
  """
  BoxModel encapsulates the box model properties for widgets. Please note
  this class is not related to the classes based on 'AttriBox' despite the
  similar name.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Static Helper Methods
  @staticmethod
  def dimKeys(level: str) -> dict[str, Keys]:
    keyDict = dict()
    if level.lower() in ('margin', 'border', 'padding'):
      level = """%ss""" % level.lower()
    if level not in ('margins', 'borders', 'paddings'):
      infoSpec = """Invalid level: '%s'! Expected one of: 'margins', 
      'borders', 'paddings'"""
      info = textFmt(infoSpec % level)
      raise ValueError(info)
    for dim in ('left', 'top', 'right', 'bottom'):
      keyDict[dim] = (
        """%s%s""" % (dim, level),
        """%s_%s""" % (dim, level),
        """%s_%s""" % (dim[0], level),
        """%s%s""" % (dim, level[:-1]),
        """%s_%s""" % (dim, level[:-1]),
        """%s_%s""" % (dim[0], level[:-1]),
      )
    return keyDict

  #  Public Variables
  #  #  Keys
  marginsKeys = dimKeys('margins')
  bordersKeys = dimKeys('borders')
  paddingsKeys = dimKeys('paddings')

  #  #  Margins
  leftMargin = Dimension(int, 0, *marginsKeys['left'])
  topMargin = Dimension(int, 0, *marginsKeys['top'])
  rightMargin = Dimension(int, 0, *marginsKeys['right'])
  bottomMargin = Dimension(int, 0, *marginsKeys['bottom'])

  #  #  Borders
  leftBorder = Dimension(int, 0, *bordersKeys['left'])
  topBorder = Dimension(int, 0, *bordersKeys['top'])
  rightBorder = Dimension(int, 0, *bordersKeys['right'])
  bottomBorder = Dimension(int, 0, *bordersKeys['bottom'])

  #  #  Paddings
  leftPadding = Dimension(int, 0, *paddingsKeys['left'])
  topPadding = Dimension(int, 0, *paddingsKeys['top'])
  rightPadding = Dimension(int, 0, *paddingsKeys['right'])
  bottomPadding = Dimension(int, 0, *paddingsKeys['bottom'])

  #  Virtual Variables
  margins: InSetsField = Field()
  borders: InSetsField = Field()
  paddings: InSetsField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @margins.GET
  def _getMargins(self, ) -> InSets:
    return InSets(
      self.leftMargin,
      self.topMargin,
      self.rightMargin,
      self.bottomMargin,
    )

  @borders.GET
  def _getBorders(self, ) -> InSets:
    return InSets(
      self.leftBorder,
      self.topBorder,
      self.rightBorder,
      self.bottomBorder,
    )

  @paddings.GET
  def _getPaddings(self, ) -> InSets:
    return InSets(
      self.leftPadding,
      self.topPadding,
      self.rightPadding,
      self.bottomPadding,
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def intrinsic(self, contentRect: Rect) -> Size:
    raise NotImplementedError
