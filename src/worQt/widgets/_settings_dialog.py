"""
SettingsDialog presents a 'worQt.settings.Settings' model VLC-style: a list
of tabs (panes) on the left selects the matching page of that tab's settings
on the right, with Ok / Apply / Cancel / Restore-defaults along the bottom.
Each setting gets a type-appropriate editor reused from '_value_edits'
(checkbox, number, or line edit). Apply writes the edited values back into
the model and reflects them to its file; Restore-defaults resets the model
and reloads the editors; Cancel discards. Apply stays disabled until an edit
is made. The dialog is generic: it shows whatever tabs and settings the model
carries.

Per the QObject construction constraint, the fixed widgets are 'AttriBox'
slots built lazily; the per-tab pages are runtime widgets created in
'build()', after a 'QApplication' exists.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
  QDialog,
  QListWidget,
  QStackedWidget,
  QWidget,
  QFormLayout,
  QHBoxLayout,
  QVBoxLayout,
  QDialogButtonBox,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..mixin import MixinBase
from ._value_edits import valueEditor

if TYPE_CHECKING:  # pragma: no cover
  from worQt.settings import Settings


class SettingsDialog(QDialog, MixinBase):
  """A tabbed settings editor over a 'Settings' model: tabs on the left,
  their settings on the right, Apply reflecting changes to the file."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __settings_model__ = None  # the Settings instance being edited
  __editor_map__ = None  # mapping (tabName, settingName) -> value editor

  #  Public Variables
  built = AttriBox[bool](False)
  dirty = AttriBox[bool](False)  # an editor changed since the last Apply
  vbox = AttriBox[QVBoxLayout]()
  hbox = AttriBox[QHBoxLayout]()
  tabList = AttriBox[QListWidget](THIS)
  stack = AttriBox[QStackedWidget](THIS)
  buttons = AttriBox[QDialogButtonBox](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setModel(self, settings: Settings) -> None:
    """Adopt 'settings' as the model to edit. Set this before building."""
    self.__settings_model__ = settings

  def model(self, ) -> Settings:
    """The 'Settings' model currently being edited."""
    return self.__settings_model__

  def build(self, ) -> None:
    """Assemble the dialog from the model. Idempotent."""
    if self.built:
      return
    self._buildLayout()
    self._populate()
    self.built = True

  def _buildLayout(self, ) -> None:
    """Lay out the tab list, the page stack and the button box."""
    title = 'Settings'
    if self.__settings_model__ is not None:
      title = 'Settings - %s' % (self.__settings_model__.appName,)
    self.setWindowTitle(title)
    self.resize(560, 380)
    self.tabList.setMaximumWidth(180)
    self.tabList.currentRowChanged.connect(self.stack.setCurrentIndex)
    self.hbox.addWidget(self.tabList)
    self.hbox.addWidget(self.stack, 1)
    standard = QDialogButtonBox.StandardButton
    self.buttons.setStandardButtons(
        standard.Ok | standard.Apply | standard.Cancel
        | standard.RestoreDefaults)
    self.buttons.accepted.connect(self._onAccept)
    self.buttons.rejected.connect(self._onReject)
    self.buttons.clicked.connect(self._onButtonClicked)
    self.vbox.addLayout(self.hbox)
    self.vbox.addWidget(self.buttons)
    self.setLayout(self.vbox)

  def _populate(self, ) -> None:
    """Build one list entry and one settings page per tab in the model."""
    self.__editor_map__ = dict()
    model = self.__settings_model__
    if model is None:
      return
    for tab in model.tabs():
      self.tabList.addItem(tab.label)
      page = QWidget(self)  # runtime widget: QApplication exists by now
      form = QFormLayout(page)
      for setting in tab:
        editor = valueEditor(setting.value)
        editor.build()
        if setting.description:
          editor.setToolTip(setting.description)
        editor.connectChanged(self._onEdited)  # after build: no false dirty
        form.addRow(setting.label, editor)
        self.__editor_map__[(tab.name, setting.name)] = editor
      self.stack.addWidget(page)
    if self.tabList.count():
      self.tabList.setCurrentRow(0)
    self._setDirty(False)  # a freshly populated dialog is clean

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HANDLERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _applyButton(self, ) -> object:
    """The Apply push button (or None before the button box is built)."""
    return self.buttons.button(QDialogButtonBox.StandardButton.Apply)

  def _setDirty(self, flag: bool) -> None:
    """Record the edited state and enable Apply only while dirty."""
    self.dirty = True if flag else False
    button = self._applyButton()
    if button is not None:
      button.setEnabled(self.dirty)

  def _onEdited(self, *_) -> None:
    """An editor changed: the dialog now has unsaved edits."""
    self._setDirty(True)

  def _applyToModel(self, ) -> None:
    """Push every editor's value back into the model."""
    model = self.__settings_model__
    if model is None:
      return
    editors = self.__editor_map__ or dict()
    for (tabName, settingName), editor in editors.items():
      model.tab(tabName).setValue(settingName, editor.value)

  def _reloadEditors(self, ) -> None:
    """Refresh every editor from the model's current values."""
    model = self.__settings_model__
    if model is None:
      return
    editors = self.__editor_map__ or dict()
    for (tabName, settingName), editor in editors.items():
      editor.value = model.tab(tabName).value(settingName)

  def _onApply(self, ) -> None:
    """Write the edited values into the model and reflect them to file."""
    self._applyToModel()
    if self.__settings_model__ is not None:
      self.__settings_model__.save()
    self._setDirty(False)  # persisted: clean again

  def _onAccept(self, ) -> None:
    """Apply, then close the dialog accepted."""
    self._onApply()
    self.accept()

  def _onReject(self, ) -> None:
    """Close the dialog rejected, discarding the edits."""
    self.reject()

  def _onReset(self, ) -> None:
    """Restore the model to its defaults and reload the editors."""
    if self.__settings_model__ is None:
      return
    self.__settings_model__.reset()
    self._reloadEditors()
    self._setDirty(True)  # defaults are in memory but not yet saved

  def _onButtonClicked(self, button: object) -> None:
    """Dispatch the Apply and Restore-defaults buttons (Ok/Cancel use the
    accepted/rejected signals)."""
    standard = QDialogButtonBox.StandardButton
    role = self.buttons.standardButton(button)
    if role == standard.Apply:
      self._onApply()
    elif role == standard.RestoreDefaults:
      self._onReset()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def show(self, ) -> None:
    self.build()
    super().show()

  def exec(self, ) -> int:
    self.build()
    return super().exec()
