"""
DiskWindow subclasses 'MainWindow' and edits a disk: a row of buttons
above the drawing, and beside it the panel of what is selected.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ...windows import MainWindow
from .. import Disk
from . import DiskToolBar, DiskWidget, DiskInspector


class DiskWindow(MainWindow):
  """
  DiskWindow subclasses 'MainWindow' and edits a disk, the way any
  drawing program edits: the 'toolBar' above, with 'Add support', 'Add
  load', 'Add reinforcement', 'Undo' and 'Redo'; the drawing, 'diskView',
  below it; and beside the drawing the 'inspector', showing what is
  selected as numbers to type over. A click on the drawing selects, the
  panel follows, and every edit, in the drawing or in the panel, shows
  in both at once.
  Undo and Redo are greyed out while there is nothing to undo or redo,
  and are in the Edit menu too, with Ctrl+Z and Ctrl+Shift+Z.

  It opens on the wall over the entrance of KIT's 'AC20-Institute-Var-2',
  a deep beam.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Disk'
  __start_size__ = 1100, 680
  __example_text__ = """disk 6 x 2.7 x 0.3 fc 30 fy 800 E 200000
support bottom 0 0.3 y
support bottom 5.7 6 x y
load top 0 6 F 0 -1200"""

  #  Public Variables
  toolBar = AttriBox[DiskToolBar](THIS)
  diskView = AttriBox[DiskWidget](THIS)
  inspector = AttriBox[DiskInspector](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    The 'initUI' method puts the buttons above the drawing and the panel
    beside it, the drawing taking the room there is, sizes the window and
    shows the example.
    """
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 2)
    layout.addWidget(self.diskView, 1, 0)
    layout.addWidget(self.inspector, 1, 1)
    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 0)
    layout.setRowStretch(1, 1)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.diskView.disk = Disk(self.__example_text__)
    self.refresh()
    self.diskView.setFocus()

  def initLogic(self, ) -> None:
    """
    The 'initLogic' method wires the buttons and the Edit menu to the
    drawing, the drawing to the panel and the panel to the drawing.
    """
    bar, view = self.toolBar, self.diskView
    bar.addSupportButton.clicked.connect(view.addSupport)
    bar.addLoadButton.clicked.connect(view.addLoad)
    bar.addRebarButton.clicked.connect(view.addRebar)
    bar.undoButton.clicked.connect(view.undo)
    bar.redoButton.clicked.connect(view.redo)
    editMenu = self.mainMenuBar.editMenu
    editMenu.undoAction.triggered.connect(view.undo)
    editMenu.redoAction.triggered.connect(view.redo)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)
    view.diskEdited.connect(self.refresh)
    view.selectionChanged.connect(self.refresh)
    self.inspector.edited.connect(view.edit)
    self.inspector.removeRequested.connect(view.removeSelected)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def refresh(self, ) -> None:
    """
    The 'refresh' method shows in the panel what is selected on the
    drawing, and greys out Undo and Redo while there is nothing to undo
    or redo.
    """
    view = self.diskView
    self.inspector.inspect(view.disk, view.selection)
    self.toolBar.undoButton.setEnabled(view.canUndo)
    self.toolBar.redoButton.setEnabled(view.canRedo)
