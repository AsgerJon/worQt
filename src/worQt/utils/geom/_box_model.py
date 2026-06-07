"""
BoxModel encapsulates the box model properties for widgets. Please note
this class is not related to the classes based on 'AttriBox' despite the
similar name.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from worktoy.desc import Field
from worktoy.waitaminute import TypeException, MissingVariable

from . import InSets, Rect, BoxDims

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union

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
  __fallback_margin_dims__ = 2, 2, 2, 2
  __fallback_border_dims__ = 1, 1, 1, 1
  __fallback_padding_dims__ = 2, 2, 2, 2

  #  Private Variables
  __margins_insets__ = None
  __borders_insets__ = None
  __paddings_insets__ = None

  #  Public Variables
  marginDims: InSetsField = Field()
  borderDims: InSetsField = Field()
  paddingDims: InSetsField = Field()

  #  Virtual Variables
  fieldOwner = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createMargins(self, ) -> None:
    try:
      fallback = self.fieldOwner.__fallback_margin_dims__
    except (MissingVariable, AttributeError):
      fallback = self.__fallback_margin_dims__
    self.__margins_insets__ = InSets(*fallback, )

  @marginDims.GET
  def _getMargins(self, **kwargs) -> InSets:
    if self.__margins_insets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMargins()
      return self._getMargins(_recursion=True)
    if isinstance(self.__margins_insets__, InSets):
      return self.__margins_insets__
    name, value = '__margins_insets__', self.__margins_insets__
    raise TypeException(name, value, InSets)

  def _createBorders(self, ) -> None:
    try:
      fallback = self.fieldOwner.__fallback_border_dims__
    except (MissingVariable, AttributeError):
      fallback = self.__fallback_border_dims__
    self.__borders_insets__ = InSets(*fallback, )

  @borderDims.GET
  def _getBorders(self, **kwargs) -> InSets:
    if self.__borders_insets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBorders()
      return self._getBorders(_recursion=True)
    if isinstance(self.__borders_insets__, InSets):
      return self.__borders_insets__
    name, value = '__borders_insets__', self.__borders_insets__
    raise TypeException(name, value, InSets)

  def _createPaddings(self, ) -> None:
    try:
      fallback = self.fieldOwner.__fallback_padding_dims__
    except (MissingVariable, AttributeError):
      fallback = self.__fallback_padding_dims__
    self.__paddings_insets__ = InSets(*fallback, )

  @paddingDims.GET
  def _getPaddings(self, **kwargs) -> InSets:
    if self.__paddings_insets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPaddings()
      return self._getPaddings(_recursion=True)
    if isinstance(self.__paddings_insets__, InSets):
      return self.__paddings_insets__
    name, value = '__paddings_insets__', self.__paddings_insets__
    raise TypeException(name, value, InSets)

  @fieldOwner.GET
  def _getFieldOwner(self, ) -> type:
    if self.__widget_type__ is None:
      raise MissingVariable(self, '__field_owner__', type)
    if isinstance(self.__widget_type__, type):
      return self.__widget_type__
    name, value = '__field_owner__', self.__widget_type__
    raise TypeException(name, value, type)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def requiredMaximum(self, content: Rect) -> BoxDims:
    raise NotImplementedError

  def minimumExpanding(self, outer: Rect) -> BoxDims:
    return BoxDims.extrinsic(outer, self)
