"""
AbstractColor provides the abstract base class for the immutable color
classes. Subclasses must provide getter functions for the 'red', 'green'
and 'blue' color channels as integer properties in the range 0-255. The
base class provides the 'alpha' channel that defaults to 255. Subclasses
are may use any internal collection of immutable values.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from typing import TYPE_CHECKING

from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  pass


class AbstractColor(BaseObject):
  """
  AbstractColor provides the abstract base class for the immutable color
  classes. Subclasses must provide getter functions for the 'red', 'green'
  and 'blue' color channels as integer properties in the range 0-255. The
  base class provides the 'alpha' channel that defaults to 255. Subclasses
  are may use any internal collection of immutable values.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_alpha__ = 255

  #  Private Variables
  __alpha_value__ = None

  #  Public Variables
  alpha = Field()

  #  Virtual Variables
  red = Field()
  green = Field()
  blue = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @alpha.GET
  def _getAlpha(self, **kwargs) -> int:
    if self.__alpha_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__alpha_value__ = self.__fallback_alpha__
      return self._getAlpha(_recursion=True, )
    if isinstance(self.__alpha_value__, int):
      if 0 <= self.__alpha_value__ <= 255:
        return self.__alpha_value__
      infoSpec = """Expected alpha channel to be in range 0-255, 
      but received '%d'!"""
      info = infoSpec % self.__alpha_value__
      raise ValueError(textFmt(info))
    raise TypeException('__alpha_value__', self.__alpha_value__, int)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @red.GET
  def _getRed(self, **kwargs) -> int:
    raise NotImplementedError

  @green.GET
  def _getGreen(self, **kwargs) -> int:
    raise NotImplementedError

  @blue.GET
  def _getBlue(self, **kwargs) -> int:
    raise NotImplementedError
