"""
The 'validateIterable' method provides a utility function checking if an
object is iterable. Please note that this implementation attempts
iteration with no inspection. This function does not solve a situation
where iteration fails during an implemented '__iter__'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


def validateIterable(obj: Any, **kwargs, ) -> bool:
  try:
    iter(obj)
  except TypeError:
    return False
  else:
    return True
