"""
RunEmpty is a harness fixture: an 'AppTest' whose only method is misnamed,
so it has no tests at all - which must be an error, never a silent pass.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.qtest import AppTest


class RunEmpty(AppTest):
  """Has no test methods."""

  def check_misnamed(self) -> None:
    """Not a test: 'check*' is not a test prefix."""
