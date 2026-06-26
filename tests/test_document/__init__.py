"""
The 'tests.test_document' package contains tests for the 'worQt.document'
package, exercised through a small FEM-skeleton example ('examples').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from . import examples
from ._document_test import DocumentTest

__all__ = (
  'examples',
  'DocumentTest',
)
