"""
Exercises the pure 'worQt.settings' system: the small TOML codec, the
OS-specific config-path resolver, and the Setting/SettingsTab/Settings
model with its file round-trip. No Qt is involved, so these run in-process
without a 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
import tempfile

from worktoy.work_test import BaseTest

from worQt.settings import (
  Settings,
  SettingsTab,
  Setting,
  configPath,
  configFileName,
  dumpToml,
  loadToml,
  humanizeName,
)


class TestSettings(BaseTest):
  """Covers the codec, the config path and the settings model."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TOML CODEC   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_toml_round_trips_all_scalar_types(self, ) -> None:
    """str, int, float and bool survive a dump/load cycle unchanged."""
    data = {'audio': {'volume': 80, 'gain': 1.5, 'muted': False,
                      'device': 'Speakers'},
            'ui': {'theme': 'dark', 'scale': 2.0}}
    self.assertEqual(loadToml(dumpToml(data)), data)

  def test_toml_escapes_special_characters(self, ) -> None:
    """Quotes, backslashes, tabs and newlines round-trip inside a string."""
    data = {'s': {'k': 'a "quote"\tand\na\\slash'}}
    text = dumpToml(data)
    self.assertIn('\\"', text)  # the quote was escaped
    self.assertEqual(loadToml(text), data)

  def test_toml_honours_comments_and_blanks(self, ) -> None:
    """'#' starts a comment outside strings; blank lines are skipped."""
    text = '# header\n\n[a]\nx = 1   # inline\ny = "a#b"\n'
    self.assertEqual(loadToml(text), {'a': {'x': 1, 'y': 'a#b'}})

  def test_toml_rejects_malformed_line(self, ) -> None:
    """A non-blank line that is neither header nor pair raises."""
    with self.assertRaises(ValueError):
      loadToml('[a]\nnonsense\n')

  def test_toml_empty_is_blank(self, ) -> None:
    """Empty data dumps to '' and empty text loads to '{}'."""
    self.assertEqual(dumpToml({}), '')
    self.assertEqual(loadToml(''), {})

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONFIG PATH   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _pathUnder(platform: str, environ: dict, home: str) -> str:
    """'configPath('myapp')' as seen under a faked platform, environment
    and home directory, restoring all three afterwards."""
    oldPlatform = sys.platform
    oldEnviron = dict(os.environ)
    try:
      sys.platform = platform
      os.environ['HOME'] = home
      for key in ('APPDATA', 'XDG_CONFIG_HOME'):
        os.environ.pop(key, None)
      os.environ.update(environ)
      return configPath('myapp')
    finally:
      sys.platform = oldPlatform
      os.environ.clear()
      os.environ.update(oldEnviron)

  def test_config_file_name(self, ) -> None:
    """The file is named '.<appName>.config'."""
    self.assertEqual(configFileName('worQt'), '.worQt.config')

  def test_config_path_falls_back_to_xdg_home(self, ) -> None:
    """An unrecognised platform uses '~/.config' (the Arch/XDG layout)."""
    path = self._pathUnder('linux', {}, '/home/u')
    self.assertEqual(path, '/home/u/.config/.myapp.config')

  def test_config_path_respects_xdg_config_home(self, ) -> None:
    """'$XDG_CONFIG_HOME' overrides the default config directory."""
    path = self._pathUnder(
        'linux', {'XDG_CONFIG_HOME': '/tmp/xdg'}, '/home/u')
    self.assertEqual(path, '/tmp/xdg/.myapp.config')

  def test_config_path_macos(self, ) -> None:
    """macOS uses '~/Library/Application Support'."""
    path = self._pathUnder('darwin', {}, '/Users/u')
    self.assertEqual(
        path, '/Users/u/Library/Application Support/.myapp.config')

  def test_config_path_windows(self, ) -> None:
    """Windows uses the '%APPDATA%' roaming directory."""
    path = self._pathUnder('win32', {'APPDATA': '/roam'}, '/home/u')
    self.assertEqual(path, '/roam/.myapp.config')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_setting_type_from_subscript(self, ) -> None:
    """'Setting[T]' fixes the value type; default and value follow it."""
    self.assertIs(Setting[int](7).valueType, int)
    self.assertIs(Setting[float](1.5).valueType, float)
    self.assertIs(Setting[bool](True).valueType, bool)
    self.assertIs(Setting[str]('hi').valueType, str)

  def test_setting_subscript_coerces_default(self, ) -> None:
    """The default is coerced to the subscript type, not its own type."""
    setting = Setting[float](10)
    self.assertEqual(setting.default, 10.0)
    self.assertIs(type(setting.value), float)

  def test_setting_coerces_on_assignment(self, ) -> None:
    """Assigning the value casts it to the declared type."""
    setting = Setting[int](80).withName('volume')
    setting.set('95')
    self.assertEqual(setting.value, 95)
    self.assertIs(type(setting.value), int)

  def test_setting_bool_parses_truthy_strings(self, ) -> None:
    """A bool setting reads the usual truthy/falsey strings."""
    setting = Setting[bool](False)
    setting.set('true')
    self.assertIs(setting.value, True)
    setting.set('off')
    self.assertIs(setting.value, False)

  def test_setting_reset_and_fluent(self, ) -> None:
    """'reset' restores the default; the fluent setters chain."""
    setting = Setting[int](80).withName('v').withLabel('Volume')
    setting.withHelp('0..100')
    setting.set(10)
    setting.reset()
    self.assertEqual(setting.value, 80)
    self.assertEqual(setting.label, 'Volume')
    self.assertEqual(setting.description, '0..100')

  def test_setting_label_humanised_from_name(self, ) -> None:
    """With no explicit label, the label humanises the name."""
    setting = Setting[int](0).withName('max_count')
    self.assertEqual(setting.label, 'Max count')

  def test_setting_name_from_class_body(self, ) -> None:
    """A 'Setting' in a class body takes its name from '__set_name__'."""
    from worktoy.core import Object

    class Host(Object):
      volume = Setting[int](80)

    self.assertEqual(Host.volume.name, 'volume')
    self.assertEqual(Host.volume.value, 80)

  def test_humanize_name(self, ) -> None:
    """Names become spaced, capitalised labels."""
    self.assertEqual(humanizeName('master_volume'), 'Master volume')
    self.assertEqual(humanizeName('grid-step'), 'Grid step')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TAB   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_tab_defines_and_reads(self, ) -> None:
    """A tab defines settings and reads them as a mapping, in order."""
    tab = SettingsTab('audio')
    tab.define('volume', 80)
    tab.define('muted', False)
    self.assertEqual(tab.names(), ['volume', 'muted'])
    self.assertEqual(tab.toDict(), {'volume': 80, 'muted': False})
    self.assertIs(tab.setting('volume').valueType, int)  # define inferred
    self.assertIs(tab.setting('muted').valueType, bool)
    tab['volume'] = 50
    self.assertEqual(tab['volume'], 50)

  def test_tab_apply_dict_ignores_unknown_and_missing(self, ) -> None:
    """Applying a mapping sets known keys and leaves the rest at default."""
    tab = SettingsTab('audio')
    tab.define('volume', 80)
    tab.define('muted', False)
    tab.applyDict({'volume': 30, 'unknown': 1})  # unknown key ignored
    self.assertEqual(tab.toDict(), {'volume': 30, 'muted': False})

  def test_tab_reset(self, ) -> None:
    """Resetting a tab restores every setting to its default."""
    tab = SettingsTab('audio')
    tab.define('volume', 80)
    tab['volume'] = 10
    tab.reset()
    self.assertEqual(tab['volume'], 80)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTINGS (file round-trip)   # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _demoModel(path: str) -> Settings:
    """A two-tab model pinned to 'path', mirroring an app's schema."""
    settings = Settings('demoapp')
    settings.setPath(path)
    audio = settings.addTab('audio', 'Audio')
    audio.define('volume', 80)
    audio.define('muted', False)
    ui = settings.addTab('ui')
    ui.define('theme', 'dark')
    ui.define('scale', 1.25)
    return settings

  def test_settings_save_load_round_trip(self, ) -> None:
    """Saved values reload into a fresh model with the same schema."""
    path = os.path.join(tempfile.mkdtemp(), '.demoapp.config')
    first = self._demoModel(path)
    first.tab('audio')['volume'] = 33
    first.tab('ui')['scale'] = 2.0
    written = first.save()
    self.assertEqual(written, path)
    self.assertTrue(os.path.exists(path))

    second = self._demoModel(path)  # same schema, defaults
    second.load()
    self.assertEqual(second.tab('audio')['volume'], 33)
    self.assertEqual(second.tab('ui')['scale'], 2.0)
    self.assertIs(second.tab('audio')['muted'], False)

  def test_settings_file_is_toml_with_tab_tables(self, ) -> None:
    """The saved file is legible TOML with one '[tab]' table per pane."""
    path = os.path.join(tempfile.mkdtemp(), '.demoapp.config')
    self._demoModel(path).save()
    with open(path, 'r', encoding='utf-8') as handle:
      text = handle.read()
    self.assertIn('[audio]', text)
    self.assertIn('[ui]', text)
    self.assertIn('volume = 80', text)

  def test_settings_missing_file_keeps_defaults(self, ) -> None:
    """Loading a non-existent file is a no-op: the defaults stand."""
    path = os.path.join(tempfile.mkdtemp(), 'absent', '.demoapp.config')
    model = self._demoModel(path)
    returned = model.load()  # missing file: no raise
    self.assertIs(returned, model)  # load returns self
    self.assertEqual(model.tab('audio')['volume'], 80)

  def test_settings_reset_all(self, ) -> None:
    """Resetting the whole model restores every tab's defaults."""
    path = os.path.join(tempfile.mkdtemp(), '.demoapp.config')
    model = self._demoModel(path)
    model.tab('audio')['volume'] = 1
    model.tab('ui')['theme'] = 'light'
    model.reset()
    self.assertEqual(model.tab('audio')['volume'], 80)
    self.assertEqual(model.tab('ui')['theme'], 'dark')

  def test_settings_path_override_else_os_default(self, ) -> None:
    """A pinned path wins; without one the OS config path is used."""
    model = Settings('demoapp')
    self.assertEqual(model.path(), configPath('demoapp'))
    model.setPath('/tmp/custom.config')
    self.assertEqual(model.path(), '/tmp/custom.config')
