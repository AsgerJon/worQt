"""
Exercises the VLC-style 'SettingsDialog' against a live 'QApplication'. The
dialog is built and driven through its handlers directly (no modal 'exec',
which would hang the harness), and the model is pinned to a temp file so
Apply never touches the real config directory.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worQt.qtest import AppTest
from worQt.settings import Settings
from worQt.widgets import SettingsDialog


class TestSettingsDialog(AppTest):
  """Builds the dialog from a model and round-trips edits through it."""

  @staticmethod
  def _model() -> Settings:
    """A two-tab model pinned to a fresh temp config file."""
    settings = Settings('demoapp')
    settings.setPath(os.path.join(tempfile.mkdtemp(), '.demoapp.config'))
    audio = settings.addTab('audio', 'Audio')
    audio.define('volume', 80).withLabel('Master volume').withHelp('0..100')
    audio.define('muted', False)
    ui = settings.addTab('interface', 'Interface')
    ui.define('theme', 'dark')
    ui.define('scale', 1.0)
    return settings

  def test_dialog_lists_tabs_and_pages(self, ) -> None:
    """The dialog shows one list row and one page per tab, with editors."""
    model = self._model()
    dialog = SettingsDialog()
    dialog.setModel(model)
    dialog.build()
    self.assertEqual(dialog.tabList.count(), 2)
    self.assertEqual(dialog.stack.count(), 2)
    self.assertEqual(dialog.tabList.item(0).text(), 'Audio')
    editors = getattr(dialog, '__editor_map__')
    self.assertEqual(set(editors),
                     {('audio', 'volume'), ('audio', 'muted'),
                      ('interface', 'theme'), ('interface', 'scale')})
    self.assertFalse(dialog.grab().isNull())  # it paints

  def test_apply_reflects_edits_into_model_and_file(self, ) -> None:
    """Apply writes the editor values into the model and to its file."""
    model = self._model()
    dialog = SettingsDialog()
    dialog.setModel(model)
    dialog.build()
    editors = getattr(dialog, '__editor_map__')
    editors[('audio', 'volume')].value = 42
    editors[('audio', 'muted')].value = True
    editors[('interface', 'theme')].value = 'light'
    dialog._onApply()
    self.assertEqual(model.tab('audio')['volume'], 42)
    self.assertIs(model.tab('audio')['muted'], True)
    self.assertEqual(model.tab('interface')['theme'], 'light')
    self.assertTrue(os.path.exists(model.path()))
    reloaded = Settings('demoapp')
    reloaded.setPath(model.path())
    reloaded.addTab('audio').define('volume', 80)
    reloaded.load()
    self.assertEqual(reloaded.tab('audio')['volume'], 42)

  def test_restore_defaults_resets_model_and_editors(self, ) -> None:
    """Restore-defaults resets the model and reloads the editors."""
    model = self._model()
    dialog = SettingsDialog()
    dialog.setModel(model)
    dialog.build()
    editors = getattr(dialog, '__editor_map__')
    editors[('audio', 'volume')].value = 5
    dialog._onApply()
    self.assertEqual(model.tab('audio')['volume'], 5)
    dialog._onReset()
    self.assertEqual(model.tab('audio')['volume'], 80)  # model reset
    self.assertEqual(editors[('audio', 'volume')].value, 80)  # editor too

  def test_accept_applies_and_reject_discards(self, ) -> None:
    """Ok applies before closing; Cancel leaves the model untouched."""
    model = self._model()
    dialog = SettingsDialog()
    dialog.setModel(model)
    dialog.build()
    editors = getattr(dialog, '__editor_map__')
    editors[('audio', 'volume')].value = 11
    dialog._onAccept()  # Ok
    self.assertEqual(model.tab('audio')['volume'], 11)

    other = self._model()
    second = SettingsDialog()
    second.setModel(other)
    second.build()
    getattr(second, '__editor_map__')[('audio', 'volume')].value = 99
    second._onReject()  # Cancel: no apply
    self.assertEqual(other.tab('audio')['volume'], 80)

  def test_apply_enables_only_when_dirty(self, ) -> None:
    """Apply is disabled on a fresh dialog, enabled by an edit, disabled
    again after Apply, and re-enabled by Restore-defaults."""
    from PySide6.QtWidgets import QDialogButtonBox
    model = self._model()
    dialog = SettingsDialog()
    dialog.setModel(model)
    dialog.build()
    apply = dialog.buttons.button(QDialogButtonBox.StandardButton.Apply)
    self.assertFalse(dialog.dirty)  # a freshly populated dialog is clean
    self.assertFalse(apply.isEnabled())
    #  a real user edit on the inner widget fires the change signal
    editors = getattr(dialog, '__editor_map__')
    editors[('audio', 'volume')].numberEdit.setText('42')
    self.assertTrue(dialog.dirty)
    self.assertTrue(apply.isEnabled())
    dialog._onApply()
    self.assertFalse(dialog.dirty)  # persisted: clean again
    self.assertFalse(apply.isEnabled())
    dialog._onReset()
    self.assertTrue(dialog.dirty)  # defaults in memory, not yet saved
    self.assertTrue(apply.isEnabled())
