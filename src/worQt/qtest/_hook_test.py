"""
HookTest subclasses 'AbstractSpaceHook' and provides a space hook that
collects the test methods encountered in the class body.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from worktoy.mcls.space_hooks import AbstractSpaceHook

if TYPE_CHECKING:  # pragma: no cover
  from worktoy.mcls.space_hooks import SpaceDesc
  from . import SpaceTest


class HookTest(AbstractSpaceHook):
  """
  Space hook that collects the test methods encountered in the class body.
  """

  space: SpaceDesc[SpaceTest]

  def setItemPhase(self, key: str, val: Any, old: Any = None, ) -> bool:
    """
    The 'setItemPhase' method detects test methods in the class body and
    collects them in the '__test_methods__' variable of the space.

    Parameters
    ----------
    key : str
        The name of the item being set.
    val : Any
        The value of the item being set.
    old : Any, optional
        The old value of the item being set, by default None.

    Returns
    -------
    bool
        True if the item was handled by this hook, False otherwise.
    """

    if str.startswith(key, 'run') or str.startswith(key, 'test'):
      if callable(val):
        self.space.addTestMethod(key, val)
    return False

  def postCompilePhase(self, compiledSpace: dict) -> dict:
    """
    The 'postCompilePhase' method ensures that the '__test_methods__'
    variable
    is initialized in the space.

    Parameters
    ----------
    compiledSpace : dict
        The namespace dict being assembled.

    Returns
    -------
    dict
        The same dict, with '__test_methods__' initialized if it was not
        already.
    """
    compiledSpace['__test_methods__'] = self.space.getTestMethods()
    return compiledSpace
