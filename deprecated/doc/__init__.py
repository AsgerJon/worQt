"""
The 'doc' subpackage exposes the document model classes for worQt. These
are pure 'worktoy' models with no Qt dependency.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._json_document import JsonDocument

__all__ = (
  'JsonDocument',
)
