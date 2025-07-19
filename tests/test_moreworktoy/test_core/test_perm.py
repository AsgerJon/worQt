"""
TestPerm tests the 'perm' function from the moreworktoy module.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from moreworktoy.core import perm

from . import CoreTest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from typing import Any, List, Tuple


class TestPerm(CoreTest):
  """
  TestPerm tests the 'perm' function from the moreworktoy.core module.
  It extends CoreTest to provide a common setup and teardown for tests.
  """

  def test_good_perm(self) -> None:
    """
    Test the 'perm' function with a simple case.
    """
    for result in perm('Tom', 'Dick', 'Harry'):
      self.assertIsInstance(result, tuple)
      self.assertEqual(len(result), 3)
      self.assertIn('Tom', result)
      self.assertIn('Dick', result)
      self.assertIn('Harry', result)
