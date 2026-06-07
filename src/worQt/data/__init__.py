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

from ._array_like import ArrayLike
from ._notify_box import NotifyBox
from ._abstract_item import AbstractItem
from ._abstract_field import AbstractField
from ._single_field import SingleField
from ._array_field import ArrayField
from ._abstract_file import AbstractFile
from ._main_file import MainFile
from ._local_file import LocalFile
from ._abstract_document import AbstractDocument

__all__ = [
  'ArrayLike',
  'NotifyBox',
  'AbstractItem',
  'AbstractField',
  'SingleField',
  'ArrayField',
  'AbstractFile',
  'MainFile',
  'LocalFile',
  'AbstractDocument',
]
