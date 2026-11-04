"""
RenderMode enumerates how an 'AppTest' child process renders: 'AUTHENTIC'
inherits the environment's real windowing platform and shows actual visible
windows, while 'HEADLESS' forces the 'offscreen' Qt platform plugin. The
runner tries 'AUTHENTIC' first and falls back to 'HEADLESS' when no display
is available.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias

  Env: TypeAlias = dict[str, str]


class RenderMode(KeeNum):
  """
  RenderMode enumerates the rendering modes for an 'AppTest' child process.
  Each member's value is the 'QT_QPA_PLATFORM' hint it imposes: the
  authentic mode leaves the environment untouched (an empty hint) so the
  real platform is used, while the headless mode forces 'offscreen'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ENUMERATIONS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  AUTHENTIC = Kee[str]('')
  HEADLESS = Kee[str]('offscreen')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def applyEnv(self, env: Env) -> Env:
    """The 'applyEnv' method returns a copy of 'env' carrying the
    'QT_QPA_PLATFORM' hint for this mode. The authentic mode leaves the
    environment unchanged so the real platform is used. A plain method,
    not an '@overload', because a frozen 'KeeNum' member rejects the
    per-instance caching the dispatcher performs."""
    out = {**env, }
    if self.value:
      out['QT_QPA_PLATFORM'] = self.value
    return out
