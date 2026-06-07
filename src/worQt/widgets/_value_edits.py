"""
Type-specific editor widgets for JSON scalar values, plus the 'valueEditor'
factory that picks one from a Python value. Each editor exposes a uniform
informal interface:

  - 'value'              a 'Field' holding the current Python value
  - 'build()'           assemble the inner widgets and layout (idempotent)
  - 'connectChanged(s)' connect 's' to the editor's native change signal

The editors are 'BaseWidget' fusions, so worktoy descriptors live alongside
the Qt widgets. Inner widgets are boxed in 'AttriBox' with 'THIS' as parent;
layouts never take 'THIS'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSlider, QCheckBox
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ._base_widget import BaseWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable


class StringValueEdit(BaseWidget):
  """A single-line text editor for JSON string values."""

  #  Private Variables
  __pending_value__ = ''

  #  Public Variables
  built = AttriBox[bool](False)
  hbox = AttriBox[QHBoxLayout]()
  lineEdit = AttriBox[QLineEdit](THIS)
  value: Field[str] = Field()

  @value.GET
  def _getValue(self, ) -> str:
    return self.lineEdit.text() if self.built else self.__pending_value__

  @value.SET
  def _setValue(self, value: Any) -> None:
    self.__pending_value__ = '' if value is None else str(value)
    if self.built:
      self.lineEdit.setText(self.__pending_value__)

  def build(self, ) -> None:
    """Assemble the line edit into the widget. Idempotent."""
    if self.built:
      return
    self.hbox.setContentsMargins(0, 0, 0, 0)
    self.hbox.addWidget(self.lineEdit)
    self.setLayout(self.hbox)
    self.lineEdit.setText(self.__pending_value__)
    self.built = True

  def connectChanged(self, slot: Callable) -> None:
    """Connect 'slot' to the editor's value-changed signal."""
    self.lineEdit.textChanged.connect(slot)


class BoolValueEdit(BaseWidget):
  """A checkbox editor for JSON boolean values."""

  #  Private Variables
  __pending_value__ = False

  #  Public Variables
  built = AttriBox[bool](False)
  hbox = AttriBox[QHBoxLayout]()
  checkBox = AttriBox[QCheckBox](THIS)
  value: Field[bool] = Field()

  @value.GET
  def _getValue(self, ) -> bool:
    if self.built:
      return True if self.checkBox.isChecked() else False
    return self.__pending_value__

  @value.SET
  def _setValue(self, value: Any) -> None:
    self.__pending_value__ = True if value else False
    if self.built:
      self.checkBox.setChecked(self.__pending_value__)

  def build(self, ) -> None:
    """Assemble the checkbox into the widget. Idempotent."""
    if self.built:
      return
    self.hbox.setContentsMargins(0, 0, 0, 0)
    self.checkBox.setText('')
    self.hbox.addWidget(self.checkBox)
    self.hbox.addStretch(1)
    self.setLayout(self.hbox)
    self.checkBox.setChecked(self.__pending_value__)
    self.built = True

  def connectChanged(self, slot: Callable) -> None:
    """Connect 'slot' to the editor's value-changed signal."""
    self.checkBox.toggled.connect(slot)


class NumberValueEdit(BaseWidget):
  """
  A slider paired with a line edit for JSON numbers. The line edit is the
  precise input; the slider is a bounded convenience that tracks a window
  of +/-100 steps around the current value. Whether the value is an 'int'
  or a 'float' is fixed by the value first loaded; floats are tracked at a
  hundredth-step resolution on the slider.
  """

  #  Private Variables
  __pending_value__ = 0
  __is_float__ = False

  #  Public Variables
  built = AttriBox[bool](False)
  hbox = AttriBox[QHBoxLayout]()
  slider = AttriBox[QSlider](THIS)
  numberEdit = AttriBox[QLineEdit](THIS)
  value: Field[object] = Field()

  @value.GET
  def _getValue(self, ) -> object:
    return self.__pending_value__

  @value.SET
  def _setValue(self, value: Any) -> None:
    self.__is_float__ = True if isinstance(value, float) else False
    if self.built:
      self._applyValue(value)
    else:
      self.__pending_value__ = value

  def _scale(self, ) -> int:
    """Slider steps per unit: 100 for floats, 1 for ints."""
    return 100 if self.__is_float__ else 1

  def _fmt(self, value: Any) -> str:
    """Render a number for the line edit without trailing noise."""
    return str(value) if self.__is_float__ else str(int(value))

  def _applyValue(self, value: Any) -> None:
    """Push 'value' onto both the slider and the line edit, silently."""
    scaled = int(round(value * self._scale()))
    self.slider.blockSignals(True)
    self.slider.setRange(scaled - 100, scaled + 100)
    self.slider.setValue(scaled)
    self.slider.blockSignals(False)
    self.numberEdit.blockSignals(True)
    self.numberEdit.setText(self._fmt(value))
    self.numberEdit.blockSignals(False)
    self.__pending_value__ = value

  def build(self, ) -> None:
    """Assemble the slider and line edit. Idempotent."""
    if self.built:
      return
    self.slider.setOrientation(Qt.Orientation.Horizontal)
    self.numberEdit.setMaximumWidth(90)
    self.hbox.setContentsMargins(0, 0, 0, 0)
    self.hbox.addWidget(self.slider)
    self.hbox.addWidget(self.numberEdit)
    self.setLayout(self.hbox)
    self.slider.valueChanged.connect(self._onSlider)
    self.numberEdit.textChanged.connect(self._onText)
    self._applyValue(self.__pending_value__)
    self.built = True

  def _onSlider(self, raw: int) -> None:
    """Mirror a slider move into the line edit and the held value."""
    value = raw / self._scale() if self.__is_float__ else int(raw)
    self.numberEdit.blockSignals(True)
    self.numberEdit.setText(self._fmt(value))
    self.numberEdit.blockSignals(False)
    self.__pending_value__ = value

  def _onText(self, *_) -> None:
    """Mirror a valid line-edit number into the slider and held value."""
    text = self.numberEdit.text()
    try:
      value = float(text) if self.__is_float__ else int(text)
    except ValueError:
      return  # mid-edit or invalid: leave the slider where it is
    scaled = int(round(value * self._scale()))
    self.slider.blockSignals(True)
    if scaled < self.slider.minimum() or scaled > self.slider.maximum():
      self.slider.setRange(scaled - 100, scaled + 100)
    self.slider.setValue(scaled)
    self.slider.blockSignals(False)
    self.__pending_value__ = value

  def connectChanged(self, slot: Callable) -> None:
    """Connect 'slot' to both the slider and line-edit change signals."""
    self.slider.valueChanged.connect(slot)
    self.numberEdit.textChanged.connect(slot)


def valueEditor(value: Any) -> BaseWidget:
  """
  Build the editor widget best suited to 'value'. 'bool' is checked before
  'int'/'float' because 'bool' is a subclass of 'int'. The returned widget
  is seeded with 'value' but not yet built; the caller calls 'build()'.
  """
  if isinstance(value, bool):
    editor = BoolValueEdit()
  elif isinstance(value, (int, float)):
    editor = NumberValueEdit()
  else:
    editor = StringValueEdit()
  editor.value = value
  return editor
