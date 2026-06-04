"""
The 'project' subpackage abstracts file access for worQt applications.
'AbstractFile' resolves where a document lives and opens it, handing the
caller an already-open handle to read from or write to; the caller owns the
file's contents (serialisation), while the gateway owns the path resolution
and the open/close (and optional open-error) plumbing.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_file import AbstractFile
from ._main_file import MainFile

__all__ = [
  'AbstractFile',
  'MainFile',
]
