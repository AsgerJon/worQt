"""
QtBox subclasses 'AttriBox' from 'worktoy.desc' and forwards field name
and owner passed to '__set_name__' to field objects returned by
'__instance_get__' and eventually '__get__'. This is achieved by extending
the '__get__' to enable returned objects access to the awareness provided
by the '__set_name__' method.

When an 'AttriBox' descriptor object returns a field object to an owning
instance, it tries to call '__set_name__' on the field object before
returning it. If available, it receives the same 'owner' and 'name' as
received by the descriptor itself. This requires that 'fieldType' types
implement '__set_name__' appropriately. The alternative of dynamically
setting attributes is more brittle and requires that the field type allows
dynamic setting of attributes, i.e. does not implement '__slots__'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import AttriBox

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class QtBox(AttriBox):
  """
  QtBox subclasses 'AttriBox' from 'worktoy.desc' and forwards field name
  and owner passed to '__set_name__' to field objects returned by
  '__instance_get__' and eventually '__get__'. This is achieved by extending
  the '__get__' to enable returned objects access to the awareness provided
  by the '__set_name__' method.

  When an 'AttriBox' descriptor object returns a field object to an owning
  instance, it tries to call '__set_name__' on the field object before
  returning it. If available, it receives the same 'owner' and 'name' as
  received by the descriptor itself. This requires that 'fieldType' types
  implement '__set_name__' appropriately. The alternative of dynamically
  setting attributes is more brittle and requires that the field type allows
  dynamic setting of attributes, i.e. does not implement '__slots__'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, instance: Any, owner: Any) -> Any:
    fieldObject = AttriBox.__get__(self, instance, owner)
    if instance is not None:
      fieldOwner = self.getFieldOwner()
      fieldName = self.getFieldName()
      try:
        fieldObject.__set_name__(fieldOwner, fieldName)
      except AttributeError as attributeError:
        traceStr = """has no attribute '__set_name__'"""
        if traceStr not in str(attributeError):
          raise attributeError
    return fieldObject
