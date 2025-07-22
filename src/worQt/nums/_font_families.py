"""
FontFamilies provides a list of available font families in the running
system. This class implements the descriptor protocol to retrieve the
available font families. Please note that the available font families are
available only when a running 'QApplication' instance is available.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtGui import QFontDatabase
from worktoy.desc import Field
from worktoy.mcls import BaseObject

from ..desQt import App, Etc

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class FontFamilies(BaseObject):
  """
  FontFamilies provides a list of available font families in the running
  system. This class implements the descriptor protocol to retrieve the
  available font families. Please note that the available font families are
  available only when a running 'QApplication' instance is available.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  app = App()
  etc = Etc()
  fileName = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fileName.GET
  def _getFileName(self) -> str:
    return os.path.join(self.etc, 'font_families.txt')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, instance: Any, owner: type) -> Any:
    """Returns the list of available font families."""
    try:
      out = self._loadFromCache()
    except FileNotFoundError:
      if self.app.isRunning():
        out = self._liveLoad()
        self._saveToCache(*out, )
      else:
        raise NotImplementedError("""TODO: app not running!""")
    except Exception as exception:
      raise exception
    else:
      return out
    finally:
      pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _liveLoad() -> list[str]:
    """
    Returns the list of available font families.
    This method is called when the 'QApplication' instance is available.
    """
    return [*QFontDatabase.families(QFontDatabase.WritingSystem.Any), ]

  def _saveToCache(self, *families: str) -> None:
    """Saves the families to the cache file. """
    f = type('_', (), {'close': lambda *_: None})  # callable close
    try:
      f = open(self.fileName, 'w', encoding='utf-8')
    except Exception as exception:
      raise exception
    else:
      f.write('\n'.join([*families, ]))
    finally:
      f.close()

  def _loadFromCache(self, ) -> list[str]:
    """Loads the families from the cache file."""
    f = type('_', (), {'close': lambda *_: None})  # callable close
    out = []
    try:
      f = open(self.fileName, 'r', encoding='utf-8')
    except Exception as exception:
      raise exception
    else:
      for line in f:
        family = line.strip()
        if family:
          out.append(family)
    finally:
      f.close()
