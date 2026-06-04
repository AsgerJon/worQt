"""
MainFile subclasses 'AbstractFile' and provides the main file for a
particular document or project.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypeVar

from worktoy.desc import AttriBox, Field
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet

from . import AbstractFile

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

T = TypeVar('T')


class MainFile(AbstractFile):
  """
  The main file for a document or project.

  Implements the 'filePath' that 'AbstractFile' leaves abstract by
  resolving it from a directory and a file name, both of which are
  configurable and resolve lazily on first read.

  Attributes
  ----------
  extension : str
      The on-disk file extension. Defaults to 'json'.
  defaultNameSpec : str
      A format string taking a number and an extension, used to generate a
      default file name. Defaults to 'untitled_%03d.%s'.
  dirPath : str
      The containing directory. Reading it before it is set populates it
      with the user home directory. Assigning it validates that the value
      is an absolute path; assigning the current value is skipped, and an
      existing path that is not a directory is rejected.
  fileName : str
      The bare file name. Reading it before it is set populates it with the
      first 'defaultNameSpec' name (counter 0..999) not already present in
      'dirPath'.
  filePath : str
      The absolute path, derived as 'dirPath' joined with 'fileName'.
      Assigning it splits the path into 'dirPath' and 'fileName'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __dir_path__: Optional[str] = None
  __file_name__: Optional[str] = None

  #  Public Variables
  extension = AttriBox[str]('json')  # the on-disk file extension
  defaultNameSpec = AttriBox[str]('untitled_%03d.%s')  # number, extension
  dirPath: Field[str] = Field()
  fileName: Field[str] = Field()

  #  Virtual Variables
  filePath: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createDirPath(self, ) -> None:
    self.__dir_path__ = os.path.expanduser('~')

  @dirPath.GET
  def _getDirPath(self, **kwargs) -> str:
    if self.__dir_path__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createDirPath()
      return self._getDirPath(_recursion=True)
    if not isinstance(self.__dir_path__, str):
      raise TypeException('__dir_path__', self.__dir_path__, str)
    return self.__dir_path__

  def _getNextName(self, **kwargs) -> str:
    c = kwargs.get('_startCounter', 0)
    spec = self.defaultNameSpec
    ext = self.extension
    while os.path.exists(os.path.join(self.dirPath, spec % (c, ext))):
      c += 1
      if c > 999:
        break
    else:
      return spec % (c, ext)
    raise RecursionError

  def _createFileName(self, ) -> None:
    self.__file_name__ = self._getNextName()

  @fileName.GET
  def _getFileName(self, **kwargs) -> str:
    if self.__file_name__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createFileName()
      return self._getFileName(_recursion=True)
    if isinstance(self.__file_name__, str):
      return self.__file_name__
    raise TypeException('__file_name__', self.__file_name__, str)

  @filePath.GET
  def _getFilePath(self, ) -> str:
    return str(os.path.join(self.dirPath, self.fileName))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @dirPath.SET
  def _setDirPath(self, dirPath: str, **kwargs) -> None:
    if not isinstance(dirPath, str):
      raise TypeException('dirPath', dirPath, str)
    if not os.path.isabs(dirPath):
      raise ValueError('dirPath must be an absolute path!')
    self.__dir_path__ = dirPath

  @fileName.SET
  def _setFileName(self, fileName: str) -> None:
    if not isinstance(fileName, str):
      raise TypeException('fileName', fileName, str)
    self.__file_name__ = fileName

  @filePath.SET
  def _setFilePath(self, filePath: str) -> None:
    if not isinstance(filePath, str):
      raise TypeException('filePath', filePath, str)
    if not os.path.isabs(filePath):
      raise ValueError('filePath must be an absolute path!')
    self.dirPath = os.path.dirname(filePath)
    self.fileName = os.path.basename(filePath)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @dirPath.preSet
  def _preSetDirPath(self, dirPath: str, **kwargs) -> None:
    try:
      existingPath = self._getDirPath(_recursion=True)
    except RecursionError:
      pass
    else:
      if existingPath == dirPath:
        raise SkipSet
    if os.path.exists(dirPath):
      if not os.path.isdir(dirPath):
        raise NotADirectoryError
