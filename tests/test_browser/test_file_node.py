"""
TestFileNode covers 'FileNode': how a folder lists its children, which
it leaves out, opening folders, refreshing and finding a path.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os

from worQt.browser import FileNode

from . import BrowserTest


class TestFileNode(BrowserTest):
  """Tests for 'FileNode'."""

  def _root(self, *suffixes: str) -> FileNode:
    return FileNode(self.path(), -1, suffixes)

  def test_folders_first_then_files_by_name(self) -> None:
    """A folder lists its folders first, then its files, each by name
    regardless of case, and leaves hidden names out."""
    names = [child.name for child in self._root().children]
    self.assertEqual(names, ['notes', 'alpha.ezw', 'Beta.ezw', 'skip.txt'])

  def test_suffixes(self) -> None:
    """With suffixes, only the files having one are listed; folders all
    are."""
    names = [child.name for child in self._root('.ezw').children]
    self.assertEqual(names, ['notes', 'alpha.ezw', 'Beta.ezw'])

  def test_depth_and_kind(self) -> None:
    """A child is one level deeper than its folder, and knows whether it
    is a folder."""
    notes, alpha = self._root().children[:2]
    self.assertEqual((notes.depth, alpha.depth), (0, 0))
    self.assertTrue(notes.isDir)
    self.assertFalse(alpha.isDir)
    self.assertEqual(notes.children[0].depth, 1)

  def test_visible_follows_open_folders(self) -> None:
    """Only the children of open folders show."""
    root = self._root('.ezw')
    self.assertEqual(len([*root.visible()]), 3)
    root.children[0].expanded = True
    names = [node.name for node in root.visible()]
    self.assertEqual(names, ['notes', 'old', 'inner.ezw', 'alpha.ezw',
                             'Beta.ezw'])

  def test_refresh_keeps_open_folders(self) -> None:
    """Refreshing lists new files and drops gone ones, keeping which
    folders are open."""
    root = self._root('.ezw')
    root.children[0].expanded = True
    with open(self.path('notes', 'new.ezw'), 'w') as file:
      file.write('New.\n')
    os.remove(self.path('alpha.ezw'))
    root.refresh()
    names = [node.name for node in root.visible()]
    self.assertEqual(names, ['notes', 'old', 'inner.ezw', 'new.ezw',
                             'Beta.ezw'])

  def test_find_opens_the_way(self) -> None:
    """Finding a path opens the folders down to it."""
    root = self._root('.ezw')
    node = root.find(self.path('notes', 'old', 'deep.ezw'))
    self.assertEqual(node.name, 'deep.ezw')
    self.assertEqual(node.depth, 2)
    self.assertTrue(root.children[0].expanded)
    self.assertIsNone(root.find(self.path('nowhere.ezw')))

  def test_a_file_has_no_children(self) -> None:
    """A file, or a folder that is not there, lists nothing."""
    self.assertEqual(FileNode(self.path('alpha.ezw'), 0, ()).children, [])
    self.assertEqual(FileNode(self.path('gone'), 0, ()).children, [])
