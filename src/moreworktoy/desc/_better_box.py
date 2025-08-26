"""
BetterBox provides an improvement on AttriBox that sets the following
attributes from the AttriBox instance to the created field object:
- '__field_name__'
- '__field_owner__'
Both attributes are those set by the __set_name__ method.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import AttriBox

from typing import TYPE_CHECKING, Any


class BetterBox(AttriBox):
  """
  BetterBox provides an improvement on AttriBox that sets the following
  attributes from the AttriBox instance to the created field object:
  - '__field_name__'
  - '__field_owner__'
  Both attributes are those set by the __set_name__ method.
  """

  def _createFieldObject(self, ) -> Any:
    fieldObject = AttriBox._createFieldObject(self)
    try:
      setattr(fieldObject, '__field_name__', self.__field_name__)
      setattr(fieldObject, '__field_owner__', self.__field_owner__)
    except AttributeError as attributeError:
      phrases = """has no attribute""", """no __dict__ for setting"""
      for phrase in phrases:
        if phrase not in str(attributeError):
          raise attributeError
      else:
        return fieldObject
    else:
      return fieldObject
