"""
JsonDocument is the data model behind the generic JSON application. It is a
pure 'worktoy' 'BaseObject' with no Qt dependency, so it can be constructed
and tested without a running 'QApplication'. It owns the parsed JSON value
and the file path it was loaded from or last saved to, and it brokers the
file IO and the text round-trip on behalf of the view.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class JsonDocument(BaseObject):
  """
  Pure data model for the generic JSON application. Owns the parsed JSON
  value and the associated file path, and brokers load/save and the
  text round-trip. Carries no Qt state, so it is safe to construct and
  test outside a running 'QApplication'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_indent__: int = 2

  #  Private Variables
  __file_path__: str | None = None
  __json_data__: Any = None

  #  Public Variables
  path: Field[str | None] = Field()
  data: Field[Any] = Field()
  text: Field[str] = Field()
  compact: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @path.GET
  def _getPath(self, ) -> str | None:
    """The file path, or 'None' when the document has never been saved."""
    return self.__file_path__

  @data.GET
  def _getData(self, ) -> Any:
    """The parsed JSON value currently held by the document."""
    return self.__json_data__

  @text.GET
  def _getText(self, ) -> str:
    """The current data serialised as indented JSON text."""
    indent = self.__fallback_indent__
    return json.dumps(self.__json_data__, indent=indent, ensure_ascii=False)

  @compact.GET
  def _getCompact(self, ) -> str:
    """The current data serialised as minified, single-line JSON text."""
    separators = (',', ':')
    return json.dumps(self.__json_data__, separators=separators,
                      ensure_ascii=False)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @path.SET
  def _setPath(self, value: str) -> None:
    """Set the file path, rejecting non-string values."""
    if not isinstance(value, str):
      raise TypeException('path', value, str)
    self.__file_path__ = value

  @data.SET
  def _setData(self, value: Any) -> None:
    """Replace the held JSON value directly."""
    self.__json_data__ = value

  @text.SET
  def _setText(self, value: str) -> None:
    """
    Parse 'value' as JSON and replace the held data. Propagates
    'json.JSONDecodeError' (a 'ValueError' subclass) on invalid text, so
    the data is left untouched when the text does not parse.
    """
    if not isinstance(value, str):
      raise TypeException('text', value, str)
    self.__json_data__ = json.loads(value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, filePath: str) -> None:
    """Construct from a file on disk, loading and parsing it eagerly."""
    self.loadFile(filePath)

  @overload()
  def __init__(self, ) -> None:
    """Construct an empty document holding an empty JSON object."""
    self.__json_data__ = dict()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def validate(text: str) -> tuple[bool, str]:
    """
    Report whether 'text' is well-formed JSON without mutating anything.
    Returns '(True, "")' when it parses, otherwise '(False, message)'
    with the decoder's explanation. Suitable for a live validity readout.
    """
    try:
      json.loads(text)
    except ValueError as error:
      return False, str(error)
    return True, ''

  def loadFile(self, filePath: str) -> None:
    """
    Read 'filePath', parse it as JSON into 'data' and record the path.
    Parsing happens before the path is updated, so a malformed file
    leaves the document unchanged and the 'ValueError' propagates.
    """
    with open(filePath, 'r', encoding='utf-8') as jsonFile:
      raw = jsonFile.read()
    self.text = raw  # parse first; only adopt the path once it succeeds
    self.path = filePath

  def saveFile(self, ) -> None:
    """
    Write the current data as indented JSON to 'path'. Raises
    'MissingVariable' when no path has been set; callers should route to
    a 'save as' dialog in that case.
    """
    if self.__file_path__ is None:
      raise MissingVariable(self, 'path', str)
    with open(self.__file_path__, 'w', encoding='utf-8') as jsonFile:
      jsonFile.write(self.text)
