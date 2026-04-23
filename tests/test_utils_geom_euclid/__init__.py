"""
The 'tests.test_utils_geom_euclid' package contains unit tests for the
'worktoy.utils.geom.euclid' package, which implements the base class for
geometric objects: EuclideanObject. The test package here implements a few
example subclasses of EuclideanObject, which exposing the base class
functionality for testing purposes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._euclid_test import EuclidTest
from ._wessel_point import WesselPoint

__all__ = [
  'EuclidTest',
  'WesselPoint',
]
