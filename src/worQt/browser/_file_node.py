"""
FileNode is one file or folder in the tree a 'FileBrowser' shows.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class FileNode(BaseObject):
  """
  FileNode is one file or folder in the tree a 'FileBrowser' shows. A
  folder lists its children the first time they are asked for, folders
  first and then files, each in alphabetical order, leaving out hidden
  names - those starting with '.' - and any file whose suffix is not
  among 'suffixes', when there are any. 'refresh' lists them again,
  keeping the nodes, and so which folders are open, of what is still
  there. Nothing here needs Qt.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __node_path__: Optional[str] = None
  __node_depth__: Optional[int] = None
  __node_suffixes__: Optional[tuple[str, ...]] = None
  __node_children__: Optional[list[Self]] = None

  #  Public Variables
  expanded = AttriBox[bool](False)

  #  Virtual Variables
  path: Field[str] = Field()
  name: Field[str] = Field()
  depth: Field[int] = Field()
  isDir: Field[bool] = Field()
  children: Field[list] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @path.GET
  def _getPath(self, ) -> str:
    if self.__node_path__ is None:
      raise MissingVariable(self, '__node_path__', str)
    if isinstance(self.__node_path__, str):
      return self.__node_path__
    raise TypeException('__node_path__', self.__node_path__, str)

  @name.GET
  def _getName(self, ) -> str:
    return os.path.basename(self.path) or self.path

  @depth.GET
  def _getDepth(self, ) -> int:
    return 0 if self.__node_depth__ is None else self.__node_depth__

  @isDir.GET
  def _getIsDir(self, ) -> bool:
    return True if os.path.isdir(self.path) else False

  @children.GET
  def _getChildren(self, ) -> list[Self]:
    """
    The 'children' getter returns the folder's children, listed the first
    time they are asked for. A file, or a folder that cannot be read, has
    none.
    """
    if self.__node_children__ is None:
      self.__node_children__ = self._list({})
    return self.__node_children__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, path: str, depth: int, suffixes: tuple) -> None:
    self.__node_path__ = os.path.abspath(path)
    self.__node_depth__ = depth
    self.__node_suffixes__ = (*suffixes,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _shows(self, entry: os.DirEntry) -> bool:
    """Whether 'entry' is listed: not hidden, and a folder or a file
    with one of the suffixes, if there are any."""
    if str.startswith(entry.name, '.'):
      return False
    if entry.is_dir() or not self.__node_suffixes__:
      return True
    suffix = os.path.splitext(entry.name)[1]
    return True if suffix in self.__node_suffixes__ else False

  def _list(self, known: dict[str, Self]) -> list[Self]:
    """List the folder's children, reusing the nodes in 'known' by
    path."""
    if not self.isDir:
      return []
    try:
      with os.scandir(self.path) as scan:
        entries = [entry for entry in scan if self._shows(entry)]
    except OSError:
      return []
    #  Folders sort before files, each by name regardless of case.
    order = sorted(
      (not entry.is_dir(), str.lower(entry.name), entry.path)
      for entry in entries
    )
    out, depth, suffixes = [], self.depth + 1, self.__node_suffixes__
    for _, _, path in order:
      node = known.get(os.path.abspath(path), None)
      out.append(type(self)(path, depth, suffixes) if node is None else node)
    return out

  def refresh(self, ) -> None:
    """
    The 'refresh' method lists the folder again, and every open folder
    below it, keeping the nodes of what is still there.
    """
    if self.__node_children__ is None:
      return
    known = {child.path: child for child in self.__node_children__}
    self.__node_children__ = self._list(known)
    for child in self.__node_children__:
      if child.expanded:
        child.refresh()

  def visible(self, ) -> Iterator[Self]:
    """The 'visible' method yields the nodes below this one that show:
    its children, and theirs where they are open, depth first."""
    for child in self.children:
      yield child
      if child.expanded:
        yield from child.visible()

  def find(self, path: str) -> Optional[Self]:
    """
    The 'find' method returns the node of 'path' below this one, opening
    the folders on the way to it, or 'None' if it is not there.
    """
    path = os.path.abspath(path)
    for child in self.children:
      if child.path == path:
        return child
      if str.startswith(path, '%s%s' % (child.path, os.sep)):
        child.expanded = True
        return child.find(path)
    return None
