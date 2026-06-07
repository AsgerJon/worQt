"""
TestLocalFile subclasses 'DataTest' and covers 'LocalFile': it derives its
directory from the owning 'mainFile' (so it cannot be relocated on its own),
keeps a bare leaf name, may only be renamed within the owned directory, and
follows the project when the 'mainFile' moves.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

from worktoy.waitaminute.desc import ReadOnlyError

from worQt.data import MainFile, LocalFile
from . import DataTest

if TYPE_CHECKING:  # pragma: no cover
  pass


class TestLocalFile(DataTest):
  """Covers the member file's directory ownership and rename rules."""

  def _main(self) -> MainFile:
    """A 'MainFile' rooted at the test's temp directory."""
    mainFile = MainFile()
    mainFile.dirPath = self.tempDir.directory
    return mainFile

  def test_dir_derived_from_main_file(self) -> None:
    """'dirPath' comes from the owning 'mainFile'."""
    local = LocalFile(self._main(), 'data.bin')
    self.assertEqual(local.dirPath, self.tempDir.directory)

  def test_filepath_is_dir_plus_name(self) -> None:
    """'filePath' is the owned directory joined with the leaf name."""
    local = LocalFile(self._main(), 'data.bin')
    self.assertEqual(
        local.filePath, os.path.join(self.tempDir.directory, 'data.bin'))

  def test_dir_path_is_read_only(self) -> None:
    """A member cannot set its own directory."""
    local = LocalFile(self._main(), 'data.bin')
    with self.assertRaises(ReadOnlyError):
      local.dirPath = self.tempDir.directory

  def test_filename_must_be_bare(self) -> None:
    """The leaf name may not contain a directory component."""
    local = LocalFile(self._main(), 'data.bin')
    with self.assertRaises(ValueError):
      local.fileName = os.path.join('sub', 'data.bin')

  def test_filepath_renames_within_dir(self) -> None:
    """Assigning 'filePath' within the owned directory renames the leaf."""
    local = LocalFile(self._main(), 'data.bin')
    local.filePath = os.path.join(self.tempDir.directory, 'renamed.bin')
    self.assertEqual(local.fileName, 'renamed.bin')
    self.assertEqual(local.dirPath, self.tempDir.directory)

  def test_filepath_to_other_dir_rejected(self) -> None:
    """Assigning a 'filePath' in another directory is rejected."""
    local = LocalFile(self._main(), 'data.bin')
    with self.assertRaises(ValueError):
      local.filePath = os.path.join(tempfile.mkdtemp(), 'data.bin')

  def test_relocating_main_file_moves_member(self) -> None:
    """Moving the 'mainFile' moves the member with it."""
    mainFile = self._main()
    local = LocalFile(mainFile, 'data.bin')
    newDir = tempfile.mkdtemp()
    mainFile.dirPath = newDir
    self.assertEqual(local.dirPath, newDir)
