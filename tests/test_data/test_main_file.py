"""
TestMainFile subclasses 'DataTest' and covers 'MainFile': its default home
directory, absolute-path validation, the 'dirPath'/'fileName'/'filePath'
relationship, the auto-incrementing 'untitled_NNN' default name, and the
non-directory guard.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worQt.data import MainFile
from . import DataTest

if TYPE_CHECKING:  # pragma: no cover
  pass


class TestMainFile(DataTest):
  """Covers the main file's path resolution and default naming."""

  def test_default_dir_is_home(self) -> None:
    """An unset 'dirPath' resolves to the user home directory."""
    self.assertEqual(MainFile().dirPath, os.path.expanduser('~'))

  def test_dir_path_must_be_absolute(self) -> None:
    """A relative 'dirPath' is rejected."""
    with self.assertRaises(ValueError):
      MainFile().dirPath = 'relative/dir'

  def test_filepath_joins_dir_and_name(self) -> None:
    """'filePath' is 'dirPath' joined with 'fileName'."""
    mainFile = MainFile()
    mainFile.dirPath = self.tempDir.directory
    mainFile.fileName = 'doc.json'
    self.assertEqual(
        mainFile.filePath,
        os.path.join(self.tempDir.directory, 'doc.json'))

  def test_set_filepath_splits_dir_and_name(self) -> None:
    """Assigning 'filePath' splits it into 'dirPath' and 'fileName'."""
    mainFile = MainFile()
    target = os.path.join(self.tempDir.directory, 'sub', 'doc.json')
    mainFile.filePath = target
    self.assertEqual(
        mainFile.dirPath, os.path.join(self.tempDir.directory, 'sub'))
    self.assertEqual(mainFile.fileName, 'doc.json')
    self.assertEqual(mainFile.filePath, target)

  def test_set_filepath_must_be_absolute(self) -> None:
    """A relative 'filePath' is rejected."""
    with self.assertRaises(ValueError):
      MainFile().filePath = 'relative/doc.json'

  def test_next_untitled_name_increments(self) -> None:
    """The default 'fileName' is the first free 'untitled_NNN' name."""
    first = MainFile()
    first.dirPath = self.tempDir.directory
    self.assertEqual(first.fileName, 'untitled_000.json')
    with open(first.filePath, 'w') as handle:
      handle.write('')
    second = MainFile()
    second.dirPath = self.tempDir.directory
    self.assertEqual(second.fileName, 'untitled_001.json')

  def test_dir_path_rejects_non_directory(self) -> None:
    """Pointing 'dirPath' at an existing file raises 'NotADirectoryError'."""
    filePath = os.path.join(self.tempDir.directory, 'a_file')
    with open(filePath, 'w') as handle:
      handle.write('')
    with self.assertRaises(NotADirectoryError):
      MainFile().dirPath = filePath

  def test_constructor_sets_dir(self) -> None:
    """'MainFile(directory)' sets the directory."""
    mainFile = MainFile(self.tempDir.directory)
    self.assertEqual(mainFile.dirPath, self.tempDir.directory)
