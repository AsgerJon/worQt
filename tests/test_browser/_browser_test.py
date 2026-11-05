"""
BrowserTest and BrowserWidgetTest are the base classes for the tests of
'worQt.browser'. Each test gets a temporary folder holding a small tree
of files and folders:

  tree/
    notes/
      old/
        deep.ezw
      inner.ezw
    alpha.ezw
    Beta.ezw
    skip.txt
    .hidden.ezw
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worktoy.work_test import BaseTest

from worQt.qtest import WidgetTest

_FILES = (
  ('notes', 'old', 'deep.ezw'),
  ('notes', 'inner.ezw'),
  ('alpha.ezw',),
  ('Beta.ezw',),
  ('skip.txt',),
  ('.hidden.ezw',),
)


class _TreeMixin:
  """Builds the tree in a temporary folder and removes it again."""

  def makeTree(self) -> None:
    self.__temp_dir__ = tempfile.TemporaryDirectory()
    for parts in _FILES:
      path = self.path(*parts)
      os.makedirs(os.path.dirname(path), 0o777, True)
      with open(path, 'w') as file:
        file.write('Some text.\n')

  def removeTree(self) -> None:
    self.__temp_dir__.cleanup()

  def path(self, *parts: str) -> str:
    """The path of 'parts' within the tree."""
    return os.path.join(self.__temp_dir__.name, *parts)


class BrowserTest(BaseTest, _TreeMixin):
  """
  BrowserTest subclasses 'BaseTest' and is the base class for the tests
  of 'FileNode'.
  """

  def setUp(self) -> None:
    super().setUp()
    self.makeTree()

  def tearDown(self) -> None:
    try:
      super().tearDown()
    finally:
      self.removeTree()


class BrowserWidgetTest(WidgetTest, _TreeMixin):
  """
  BrowserWidgetTest subclasses 'WidgetTest' and is the base class for the
  tests of 'FileBrowser'.
  """

  def setUp(self) -> None:
    super().setUp()
    self.makeTree()

  def tearDown(self) -> None:
    try:
      super().tearDown()
    finally:
      self.removeTree()
