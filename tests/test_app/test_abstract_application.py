"""
TestAbstractApplication subclasses 'AppTest' and provides testing for the
'AbstractApplication' class in 'worQt.app' package.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.app import AbstractApplication
from worQt.mixin import MixinMeta
from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union


class TestAbstractApplication(AppTest):
  """
  Test class for 'AbstractApplication' in 'worQt.app' package.
  """

  def test_metaclass(self, ) -> None:
    """
    Test that 'AbstractApplication' has the correct metaclass.
    """

    self.assertIsInstance(AbstractApplication, MixinMeta)
