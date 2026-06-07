"""
LocalFile subclasses 'AbstractFile' and represents a member file living in
the same directory as a project's 'mainFile'. It does not own its directory:
the directory has exactly one owner, the 'mainFile', and the 'LocalFile'
derives 'dirPath' from it rather than storing a copy. So relocating the
project (moving its 'mainFile') moves every member with it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import MissingVariable, TypeException

from . import AbstractFile, MainFile

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional


class LocalFile(AbstractFile):
  """
  A member file sharing a project's directory.

  The 'dirPath' is owned by the project's 'mainFile' and derived here, never
  stored, so a member never drifts from the project folder. Assigning
  'dirPath' is therefore an error (relocate the project, not a member), and
  assigning 'filePath' may only rename the leaf within the owned directory.

  Attributes
  ----------
  mainFile : MainFile
      The directory-owning main file. Set at construction.
  fileName : str
      The bare leaf name of this member within the owned directory.
  dirPath : str
      The containing directory, delegated to 'mainFile.dirPath'. Read-only;
      assignment raises 'ReadOnlyError'.
  filePath : str
      The absolute path, 'dirPath' joined with 'fileName'. Assigning it may
      only rename within the owned directory; a path pointing elsewhere is
      rejected.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __main_file__: Optional[MainFile] = None
  __file_name__: Optional[str] = None

  #  Public Variables
  mainFile: Field[MainFile] = Field()
  fileName: Field[str] = Field()
  dirPath: Field[str] = Field()

  #  Virtual Variables
  filePath: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mainFile.GET
  def _getMainFile(self, ) -> MainFile:
    if self.__main_file__ is None:
      raise MissingVariable(self, '__main_file__', MainFile)
    if isinstance(self.__main_file__, MainFile):
      return self.__main_file__
    raise TypeException('__main_file__', self.__main_file__, MainFile)

  @fileName.GET
  def _getFileName(self, ) -> str:
    if self.__file_name__ is None:
      raise MissingVariable(self, '__file_name__', str)
    if isinstance(self.__file_name__, str):
      return self.__file_name__
    raise TypeException('__file_name__', self.__file_name__, str)

  @dirPath.GET
  def _getDirPath(self, ) -> str:
    return self.mainFile.dirPath

  @filePath.GET
  def _getFilePath(self, ) -> str:
    return str(os.path.join(self.dirPath, self.fileName))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mainFile.SET
  def _setMainFile(self, mainFile: MainFile) -> None:
    if not isinstance(mainFile, MainFile):
      raise TypeException('mainFile', mainFile, MainFile)
    self.__main_file__ = mainFile

  @fileName.SET
  def _setFileName(self, fileName: str) -> None:
    if not isinstance(fileName, str):
      raise TypeException('fileName', fileName, str)
    if fileName != os.path.basename(fileName):
      raise ValueError('fileName must be a bare name, not a path!')
    self.__file_name__ = fileName

  @filePath.SET
  def _setFilePath(self, filePath: str) -> None:
    if not isinstance(filePath, str):
      raise TypeException('filePath', filePath, str)
    directory = os.path.dirname(filePath)
    if directory and directory != self.dirPath:
      infoSpec = """A LocalFile stays in its owned directory '%s'; it """
      infoSpec += """cannot be moved to '%s'!"""
      raise ValueError(infoSpec % (self.dirPath, directory))
    self.fileName = os.path.basename(filePath)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(MainFile, str)
  def __init__(self, mainFile: MainFile, fileName: str) -> None:
    self.mainFile = mainFile
    self.fileName = fileName

  @overload(MainFile)
  def __init__(self, mainFile: MainFile) -> None:
    self.mainFile = mainFile
