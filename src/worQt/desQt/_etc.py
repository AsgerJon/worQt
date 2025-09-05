"""
Etc provides a descriptor to be owned by the running application providing
an absolute path to the etc directory of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.work_io import validateExistingDirectory

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


def _etcPath() -> str:
  """Builds the absolute path to the 'etc.' directory."""

  here = os.path.dirname(os.path.abspath(__file__))
  src = os.path.join(here, '..', '..', )
  src = os.path.normpath(src)
  etc = os.path.join(src, 'etc', )
  return os.path.normpath(etc)


class Etc:
  """
  Etc provides a descriptor to be owned by the running application providing
  an absolute path to the 'etc' directory of the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __etc_path__ = _etcPath()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, instance: Any, owner: type) -> Any:
    return validateExistingDirectory(self.__etc_path__, )
