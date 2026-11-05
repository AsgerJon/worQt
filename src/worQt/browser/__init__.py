"""
The 'worQt.browser' package provides the 'FileBrowser', a slim tree of a
folder's files and folders, as the project view of an IDE shows one,
painted with worQt's own widgets and paint operations.

- FileNode: one file or folder in the tree, free of Qt.
- PaintFileTree: the paint operation drawing the tree.
- FileBrowser: the widget.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._file_node import FileNode
from ._paint_file_tree import PaintFileTree
from ._file_browser import FileBrowser

__all__ = (
  'FileNode',
  'PaintFileTree',
  'FileBrowser',
)
