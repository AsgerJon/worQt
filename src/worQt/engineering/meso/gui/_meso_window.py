"""
MesoWindow subclasses 'MainWindow' and tests a concrete cylinder: a row
of buttons above the cylinder, its stress-strain curve and the sliders
of what it is made of.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import time

import torch
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ....windows import MainWindow
from .. import Cylinder, WholeCylinder, Grading, Lattice3D, UniaxialTest
from .. import CompressionTest, TensionTest
from . import MesoToolBar, CylinderView, CurveWidget, IngredientPanel
from . import TestStatus, TestReport


class MesoWindow(MainWindow):
  """
  MesoWindow subclasses 'MainWindow' and tests a concrete cylinder, the
  way a laboratory does: the 'toolBar' above, with 'New cylinder',
  'Compression test', 'Tension test', 'Pause', the 'Paste' slider and
  'Use GPU'; below it the whole cylinder, 'cylinderView', turned by
  dragging, beside it the test's stress-strain curve, 'curveView', and
  beside that the 'ingredients', the sliders of the stones, the paste
  and the bond.

  It opens at once, nothing cast yet, the tests greyed out. 'New
  cylinder' casts one, Ø100 × 200 mm, of a Fuller grading up to 16 mm,
  and builds its lattice in space; another of the same mix each time
  after. A test button starts that test on it, of the materials the
  sliders show, on the graphics card if 'Use GPU' is ticked, the
  cylinder and the curve following as it runs; 'Pause' stops it and
  becomes 'Resume', and the test stops by itself at its end. While a
  test runs, the sliders and 'Use GPU' are greyed out; 'Use GPU' is
  greyed out too while torch finds no graphics card it can use. The
  'Paste' slider makes the paste clear, to see the stones and the
  cracks inside.

  Along the bottom, the 'status' says what is going on: nothing cast, a
  cylinder ready, being cast, a test running, paused or finished, with
  its strain, stress, steps and time; its bar moves while work goes on,
  and the running test's button stays lit. 'Export PDF' asks where to
  write the test's report, a 'TestReport', and writes it there.

  The window runs the test a quarter of a second at a time, drawing the
  curve in between and the cylinder every second and a half, so it
  answers the whole time.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Concrete'
  __start_size__ = 1440, 820
  __cast_diameter__ = 100.0  # mm
  __cast_height__ = 200.0  # mm
  __cast_max_size__ = 16.0  # mm: the largest stone
  __grading_power__ = 0.5  # Fuller's
  __lattice_spacing__ = 2.5  # mm between nodes, at least
  __first_seed__ = 1
  __step_seconds__ = 0.25  # stepping between two looks at the window
  __step_chunk__ = 5  # steps between looks at the clock
  __view_seconds__ = 1.5  # between two drawings of the cylinder

  #  Private Variables
  __shown_cylinder__: Cylinder | None = None
  __shown_lattice__: Lattice | None = None
  __running_test__: UniaxialTest | None = None
  __last_drawn__: float = 0.0
  __run_seconds__: float = 0.0
  __export_dialog__: QFileDialog | None = None

  #  Public Variables
  toolBar = AttriBox[MesoToolBar](THIS)
  cylinderView = AttriBox[CylinderView](THIS)
  curveView = AttriBox[CurveWidget](THIS)
  ingredients = AttriBox[IngredientPanel](THIS)
  status = AttriBox[TestStatus](THIS)
  stepTimer = AttriBox[QTimer](THIS)

  #  Virtual Variables
  cylinder: Field[Cylinder] = Field()
  lattice: Field[Lattice3D] = Field()
  test: Field[UniaxialTest] = Field()
  running: Field[bool] = Field()
  exportDialog: Field[QFileDialog] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cylinder.GET
  def _getCylinder(self, ) -> Cylinder | None:
    """The 'cylinder' getter returns the cylinder cast, or 'None' before
    the window is first shown."""
    return self.__shown_cylinder__

  @lattice.GET
  def _getLattice(self, ) -> Lattice3D | None:
    """The 'lattice' getter returns the lattice of the cylinder."""
    return self.__shown_lattice__

  @test.GET
  def _getTest(self, ) -> UniaxialTest | None:
    """The 'test' getter returns the test begun on the cylinder, or
    'None'."""
    return self.__running_test__

  @exportDialog.GET
  def _getExportDialog(self, ) -> QFileDialog | None:
    """The 'exportDialog' getter returns the dialog asking where to
    write a report, or 'None' before one has been asked for."""
    return self.__export_dialog__

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether a test is running, not paused
    and not at its end."""
    return True if self.stepTimer.isActive() else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    The 'initUI' method puts the buttons above the cylinder, the curve
    beside it and the sliders beside that, and sizes the window, nothing
    cast yet.
    """
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 3)
    layout.addWidget(self.cylinderView, 1, 0)
    layout.addWidget(self.curveView, 1, 1)
    layout.addWidget(self.ingredients, 1, 2)
    layout.addWidget(self.status, 2, 0, 1, 3)
    layout.setColumnStretch(0, 2)
    layout.setColumnStretch(1, 3)
    layout.setColumnStretch(2, 0)
    layout.setRowStretch(1, 1)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.refresh()

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons and the timer."""
    bar = self.toolBar
    bar.newButton.clicked.connect(self.newCylinder)
    bar.compressionButton.clicked.connect(self.startCompression)
    bar.tensionButton.clicked.connect(self.startTension)
    bar.pauseButton.clicked.connect(self.togglePause)
    bar.exportButton.clicked.connect(self.askExport)
    bar.pasteSlider.valueChanged.connect(self.setPasteOpacity)
    self.stepTimer.timeout.connect(self.advance)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def cast(self, seed: int) -> None:
    """The 'cast' method casts a cylinder by 'seed', builds its lattice
    and shows it, untested."""
    self.stepTimer.stop()
    self.status.showState('casting', 'Casting cylinder %d' % seed,
                          'placing the stones and building the lattice')
    self.status.repaint()
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
      grading = Grading.fuller(self.__cast_max_size__,
                               self.__grading_power__)
      cylinder = WholeCylinder(self.__cast_diameter__,
                               self.__cast_height__, grading, seed)
      lattice = Lattice3D(cylinder, self.__lattice_spacing__)
    finally:
      QApplication.restoreOverrideCursor()
    self.__shown_cylinder__ = cylinder
    self.__shown_lattice__ = lattice
    self.__running_test__ = None
    self.cylinderView.cylinder = cylinder
    self.cylinderView.lattice = lattice
    self.curveView.update()
    self.refresh()

  def setPasteOpacity(self, opacity: float) -> None:
    """The 'setPasteOpacity' method draws the paste as opaque as
    'opacity'."""
    self.cylinderView.pasteOpacity = opacity

  def device(self, ) -> str:
    """The 'device' method returns where a test is to be reckoned: on
    the graphics card if 'Use GPU' is ticked and torch has one, else on
    the processor."""
    if self.toolBar.gpuBox.checked and torch.cuda.is_available():
      return 'cuda'
    return 'cpu'

  def newCylinder(self, ) -> None:
    """The 'newCylinder' method casts the first cylinder of the mix, or
    the next."""
    if self.cylinder is None:
      return self.cast(self.__first_seed__)
    self.cast(self.cylinder.seed + 1)

  def startCompression(self, ) -> None:
    """The 'startCompression' method starts crushing the cylinder, once
    one is cast."""
    if self.lattice is not None:
      materials = self.ingredients.materials()
      self.begin(CompressionTest(self.lattice, materials, self.device()))

  def startTension(self, ) -> None:
    """The 'startTension' method starts pulling the cylinder apart, once
    one is cast."""
    if self.lattice is not None:
      materials = self.ingredients.materials()
      self.begin(TensionTest(self.lattice, materials, self.device()))

  def begin(self, test: UniaxialTest) -> None:
    """The 'begin' method shows 'test' and starts running it."""
    self.__running_test__ = test
    self.__run_seconds__ = 0.0
    self.cylinderView.test = test
    self.curveView.test = test
    self.stepTimer.start(0)
    self.refresh()

  def togglePause(self, ) -> None:
    """The 'togglePause' method pauses the test running, or resumes the
    test paused."""
    test = self.test
    if test is None or test.finished:
      return
    if self.running:
      self.stepTimer.stop()
    else:
      self.stepTimer.start(0)
    self.refresh()

  def advance(self, ) -> None:
    """The 'advance' method runs the test for a quarter of a second or
    so, stopping it at its end, and shows how far it has come: the curve
    each time, the cylinder every second and a half, and at the end."""
    test = self.test
    if test is None:
      return
    now = time.monotonic()
    until = now + self.__step_seconds__
    while not test.finished and time.monotonic() < until:
      test.advance(self.__step_chunk__)
    self.__run_seconds__ += time.monotonic() - now
    if test.finished:
      self.stepTimer.stop()
    if test.finished or now - self.__last_drawn__ >= self.__view_seconds__:
      self.__last_drawn__ = now
      self.cylinderView.update()
    self.curveView.update()
    self.refresh()

  def refresh(self, ) -> None:
    """The 'refresh' method greys out the tests while nothing is cast
    and 'Pause' while there is no test to pause, and has it say 'Resume'
    while one is paused."""
    cast = False if self.lattice is None else True
    for button in (self.toolBar.compressionButton,
                   self.toolBar.tensionButton):
      button.setEnabled(cast)
      button.update()
    test = self.test
    pause = self.toolBar.pauseButton
    live = False if test is None or test.finished else True
    pause.setEnabled(live)
    pause.text = 'Resume' if live and not self.running else 'Pause'
    pause.update()
    self.ingredients.setLocked(live)
    gpu = self.toolBar.gpuBox
    gpu.setEnabled(torch.cuda.is_available() and not live)
    gpu.update()
    bar = self.toolBar
    bar.compressionButton.checked = live and isinstance(test,
                                                         CompressionTest)
    bar.tensionButton.checked = live and isinstance(test, TensionTest)
    bar.compressionButton.update()
    bar.tensionButton.update()
    bar.exportButton.setEnabled(False if test is None else True)
    bar.exportButton.update()
    self.status.showState(*self.statusOf())

  def statusOf(self, ) -> tuple[str, str, str]:
    """The 'statusOf' method says what is going on: the state, in words,
    and the details."""
    test = self.test
    if self.lattice is None:
      return 'idle', 'No cylinder yet', ''
    if test is None:
      lattice = self.lattice
      details = '%d stones, %d cells' % (len(self.cylinder.stones),
                                         lattice.nodeCount)
      return 'idle', 'Cylinder %d ready' % self.cylinder.seed, details
    name = 'Compression test' if test.direction < 0 else 'Tension test'
    seconds = int(self.__run_seconds__)
    clock = '%d:%02d' % (seconds // 60, seconds % 60)
    if test.finished:
      label = 'fc' if test.direction < 0 else 'ft'
      details = '%s = %.3g MPa at %.3g ‰ · %d steps · %s on %s' % (
          label, test.strength, test.strengthStrain * 1e3, test.step,
          clock, test.device)
      return 'finished', '%s finished' % name, details
    details = 'strain %.3f ‰ · stress %.3g MPa · %d steps · %s on %s' % (
        abs(test.strain) * 1e3, abs(test.stress), test.step, clock,
        test.device)
    if self.running:
      return 'running', '%s running' % name, details
    return 'paused', '%s paused' % name, details

  def askExport(self, ) -> None:
    """The 'askExport' method asks where to write the test's report,
    without waiting for the answer: the report is written once a file
    is chosen."""
    if self.test is None:
      return
    dialog = self.__export_dialog__
    if dialog is None:
      dialog = QFileDialog(self, 'Export PDF')
      dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
      dialog.setNameFilter('PDF files (*.pdf)')
      dialog.setDefaultSuffix('pdf')
      dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
      dialog.fileSelected.connect(self.exportPdf)
      self.__export_dialog__ = dialog
    report = TestReport(self.cylinder, self.lattice, self.test)
    name = '%s cylinder %d.pdf' % (report.title().lower(),
                                   self.cylinder.seed)
    dialog.selectFile(os.path.join(os.path.expanduser('~'), name))
    dialog.open()

  def exportPdf(self, path: str) -> None:
    """The 'exportPdf' method writes the test's report to 'path'."""
    if self.test is None:
      return
    report = TestReport(self.cylinder, self.lattice, self.test)
    report.write(path, self.curveView, self.cylinderView)
    mode, text, _ = self.statusOf()
    self.status.showState(mode, text, 'report written to %s' % path)
