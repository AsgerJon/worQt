"""
The 'worQt.window' package provides the main window for the application.
The following describes in details the design pattern 'worQt' sets out for
derived applications, which should inherit each of the following with
their own implementations suiting the application. Many actions are
provided, but left unimplemented, and derived applications should either
provide an implementation or remove the action.

WINDOWS, MENUS AND ACTIONS
class BaseWindow(QMainWindow): ...

The 'BaseWindow' class provides the menu bar, status bar and the menus. By
default, it provides common menus and connects them to actions defined in
the BaseWindow class. Most of these actions are left unimplemented,
except for:

- 'File' > 'Exit' ALT+F4: Closes the application.
- 'Help' > 'About Qt' F12: Shows the familiar 'About Qt' dialog.
- 'Help' > 'About worQt': Opens a dialog showing this documentation.

The following actions and their suggested function are left for derived
applications to implement:

- 'File' > 'New' CTRL+N: Create a new project.
- 'File' > 'Open' CTRL+O: Open an existing project.
- 'File' > 'Save' CTRL+S: Save the current project.

- 'Edit' > 'Preferences': This does open the 'preferences' dialog, but by
default, no preferences are defined. The dialog includes buttons: Cancel,
apply and ok. None of these buttons are implemented by default.

Please note the absense of 'Save As'. When creating a new project, a name
should be set. Instead, the 'Rename' action should be used to change the
name of the current project. To clone the current project, as would
typically result from saving with 'save as', derived applications should
provide for this elsewhere, for example when implementing the 'New' action.

- 'File' > 'Rename': Rename the current project.
- 'File' > 'Close': Close the current project, but leave the application
running.
- 'File' > 'Exit' ALT+F4: (Already implemented!)

Please note the flag attributes defined further down. The implemented
'Exit' action will automatically check the 'unsavedChanges' flag, which is
not implemented by default. Since 'Save' also is not implemented, pressing
'Save and Exit' in the default confirmation dialog will simply reopen
the confirmation dialog. To exit in this state, use 'Exit without saving'
or use 'Cancel' to close the confirmation dialog without exiting.

- 'Edit' > 'Undo' CTRL+Z: Undo the last action.
- 'Edit' > 'Redo' CTRL+Y: Redo the last undone action.
- 'Edit' > 'Cut' CTRL+X: Cut the selected contents.
- 'Edit' > 'Copy' CTRL+C: Copy the selected contents.
- 'Edit' > 'Paste' CTRL+V: Paste the contents from the clipboard.
- 'Edit' > 'Select All' CTRL+A: Select all contents.
- 'Edit' > 'Unselect All' CTRL+U: Unselect all contents.
- 'Edit' > 'Preferences': Open the 'preferences' dialog.

See the dialogs section further down for more information related to the
'preferences' dialog.

- 'View' The view menu is present, but have no actions by default. Derived
applications should either implement actions in this menu or remove it.

- 'Tools' Empty by default like 'View'.

- 'Help' > 'About' F1: Derived applications should implement this to open
the documentation for the application.
- 'Help' > 'About worQt': Opens a dialog showing this documentation.
- 'Help' > 'About Qt' F12: Opens the familiar 'About Qt' dialog.

class LayoutWindow(BaseWindow): ...

The 'LayoutWindow' class should inherit from the 'BaseWindow' class
described above. It should provide the main window widgets and organize
them in layouts as appropriate.

class MainWindow(LayoutWindow): ...

The 'MainWindow' class should provide the 'business logic' of the
application by connecting actions to slots and signals.

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_window import AbstractWindow
from ._base_window import BaseWindow
from ._layout_window import LayoutWindow

__all__ = [
    'AbstractWindow',
    'BaseWindow',
    'LayoutWindow',
]
