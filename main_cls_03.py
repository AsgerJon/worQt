"""
slice test
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class SliceTest:

  def __getitem__(self, item: Any) -> Any:
    print("""isinstance(item, slice): %s""" % isinstance(item, slice))
    return item
