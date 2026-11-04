"""
TestMenuRegistration subclasses 'WindowsTest' and tests the class-level
registration the declarative menu system performs at import: 'MenuBox'
fields register their menu type on 'MainMenuBar', and 'ActionBox' fields
register their action type on each menu. This is pure class-level state,
so no 'QApplication' is built.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.windows.menus import MainMenuBar, AbstractMenu, AbstractAction
from worQt.windows.menus.file_menu import File, NewAction, ExitAction

from . import WindowsTest


class TestMenuRegistration(WindowsTest):
  """Tests for the declarative menu/action registration."""

  def test_menu_bar_registers_four_menus(self) -> None:
    """'MainMenuBar' registers the File, Edit, View and Help menus."""
    menuTypes = MainMenuBar._classGetRegisteredMenuTypes()
    self.assertEqual(set(menuTypes),
                     {'fileMenu', 'editMenu', 'viewMenu', 'helpMenu'})

  def test_registered_menus_are_abstract_menus(self) -> None:
    """Every registered menu type is an 'AbstractMenu' subclass."""
    for menuType in MainMenuBar._classGetRegisteredMenuTypes().values():
      self.assertTrue(issubclass(menuType, AbstractMenu))

  def test_file_menu_type(self) -> None:
    """The 'fileMenu' field registers the 'File' menu type."""
    menuTypes = MainMenuBar._classGetRegisteredMenuTypes()
    self.assertIs(menuTypes['fileMenu'], File)

  def test_file_registers_five_actions(self) -> None:
    """The 'File' menu registers its five actions by field name."""
    actionTypes = File._classGetRegisteredActionTypes()
    self.assertEqual(set(actionTypes), {
      'newAction', 'openAction', 'saveAction', 'renameAction', 'exitAction',
    })
    self.assertIs(actionTypes['newAction'], NewAction)
    self.assertIs(actionTypes['exitAction'], ExitAction)

  def test_menu_action_counts(self) -> None:
    """Each menu registers the expected number of actions."""
    menuTypes = MainMenuBar._classGetRegisteredMenuTypes()
    counts = {name: len(menuType._classGetRegisteredActionTypes())
              for name, menuType in menuTypes.items()}
    self.assertEqual(counts, {
      'fileMenu': 5, 'editMenu': 7, 'viewMenu': 4, 'helpMenu': 3,
    })

  def test_all_registered_actions_are_abstract_actions(self) -> None:
    """Every registered action type, in every menu, is an action."""
    for menuType in MainMenuBar._classGetRegisteredMenuTypes().values():
      for actionType in menuType._classGetRegisteredActionTypes().values():
        self.assertTrue(issubclass(actionType, AbstractAction))
