"""
JsonFormWidget renders the scalar entries of a JSON object as a labelled
form of type-specific editors (see '_value_edits'). Non-scalar entries
(nested objects and arrays) are skipped: they stay in the raw text view.
Editing any field notifies an optional 'onChange' callback, and the current
field values can be read back with 'currentValues'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFormLayout
from worktoy.desc import AttriBox

from ._base_widget import BaseWidget
from ._value_edits import valueEditor

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable


class JsonFormWidget(BaseWidget):
  """A form of type-specific editors for the scalar keys of a JSON object."""

  #  Private Variables
  __on_change__ = None
  __editors__ = None

  #  Public Variables
  built = AttriBox[bool](False)
  formLayout = AttriBox[QFormLayout]()

  @staticmethod
  def _isScalar(value: Any) -> bool:
    """True for the JSON leaf types that get a dedicated editor widget."""
    return True if isinstance(value, (str, int, float, bool)) else False

  def _ensureLayout(self, ) -> None:
    """Install the form layout once."""
    if not self.built:
      self.formLayout.setContentsMargins(6, 6, 6, 6)
      self.setLayout(self.formLayout)
      self.built = True

  def _clear(self, ) -> None:
    """Drop every existing row and its editor widgets."""
    while self.formLayout.rowCount():
      self.formLayout.removeRow(0)
    self.__editors__ = dict()

  def loadFrom(self, data: dict, onChange: Callable = None) -> None:
    """
    Rebuild the form from 'data', one row per scalar entry. 'onChange' is
    called whenever any field is edited. Non-scalar entries are ignored.
    """
    self._ensureLayout()
    self._clear()
    self.__on_change__ = onChange
    editors = dict()
    for key, val in data.items():
      if not self._isScalar(val):
        continue
      editor = valueEditor(val)
      editor.build()
      if onChange is not None:
        editor.connectChanged(self._onAnyChange)
      self.formLayout.addRow(str(key), editor)
      editors[key] = editor
    self.__editors__ = editors

  def _onAnyChange(self, *_) -> None:
    """Forward any field edit to the registered callback."""
    if self.__on_change__ is not None:
      self.__on_change__()

  def currentValues(self, ) -> dict:
    """The current value of every scalar field, keyed as in the source."""
    out = dict()
    for key, editor in (self.__editors__ or dict()).items():
      out[key] = editor.value
    return out
