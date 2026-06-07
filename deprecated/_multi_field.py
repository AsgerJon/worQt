"""
MultiField subclasses 'AttriBox' from 'worktoy.desc' and provides a multi
value field in an application document or project.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject

from deprecated.codecs import AbstractCodec

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Type, Union

  CodecType: TypeAlias = Union[Type[AbstractCodec], AbstractCodec]


class MultiField(BaseObject):
  """
  MultiField subclasses 'AttriBox' from 'worktoy.desc' and provides a multi
  value field in an application document or project.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
