"""
LabWindow subclasses 'MainWindow' and is the lab: a beam of reinforced
concrete on its rig, tested by actuators under a control loop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from worksees import Worker

from ....windows import MainWindow
from ...gui import TestStatus
from .. import Actuator, BeamExperiment, BeamSetup, Control, RCBeam, Rig
from .. import Support
from . import BeamPanel, BeamView, ControlCurve, ControlPanel, LabCurve
from . import LabToolBar

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QCloseEvent


def _widestGap(places: list[float]) -> float:
  """The middle of the widest gap between 'places', to the
  centimetre."""
  places = sorted({*places})
  _, start, end = max(
      (end - start, start, end)
      for start, end in zip(places, places[1:])
      )
  return round((start + end) / 2 / 10.0) * 10.0


class LabWindow(MainWindow):
  """
  LabWindow subclasses 'MainWindow' and is the lab: the 'toolBar' above;
  below it, the 'controlPanel' of the control loop and the part
  selected, the beam on its rig, 'beamView', over the total force
  against the displacements measured, 'curveView', and the control's
  command and feedback against time, 'controlView', and the 'beamPanel'
  of the beam's numbers; and along the bottom the 'status', saying what
  is going on.

  It opens on a beam cast and set up for four point bending, untested,
  the control reading the transducer at midspan and driving the left
  actuator, the right one pushing as hard. 'Add support', 'Add
  actuator' and 'Add transducer' put one in the widest gap, selected;
  any part is dragged along the beam, selected by a click and set in
  the control panel: a support's kind, an actuator's place in the
  chain of forces, the control's transducer, actuator, command and
  gains. 'Remove' takes the part selected away, where the rig keeps
  whole. 'Start test' runs the control loop, cycle by cycle, the beam
  bending, cracking, yielding and crushing as it goes, the curves and
  the readings following; 'Pause' stops it and becomes 'Resume', and
  the test stops by itself at its end, saying why. While it runs, the
  control's ramp, gains and top speed may be changed, retuning it as
  it goes; the rest of the rig and the beam may not, nor anything once
  it is tested: 'New beam' casts it afresh, its concrete scattered
  anew, on the rig as the test began.

  'Open…' and 'Save…', and the File menu's Open and Save, read and
  write the 'setup', the beam on its rig, as a '.beam' file holds it:
  as the test began, if there is one, retuning not counted. A setup
  opened ends the test, as 'New beam' does; a file that holds none is
  refused, the status saying why.

  The window looks at the test every 20 ms, reading a cycle when
  OpenSees has done it and beginning the next, so it answers the whole
  time; 'settle' waits for a cycle instead. OpenSees runs in a process of
  its own, its 'worker', started with the first test and kept for the
  tests after it until the window closes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Beam lab'
  __start_size__ = 1680, 960
  __step_ms__ = 20  # between two looks at OpenSees's cycle under way
  __file_filter__ = 'Beam setups (*.beam)'

  #  Private Variables
  __lab_test__: BeamExperiment | None = None
  __cast_number__: int = 1
  __run_seconds__: float = 0.0
  __test_setup__: BeamSetup | None = None
  __setup_path__: str | None = None
  __open_dialog__: QFileDialog | None = None
  __save_dialog__: QFileDialog | None = None

  #  Public Variables
  toolBar = AttriBox[LabToolBar](THIS)
  controlPanel = AttriBox[ControlPanel](THIS)
  beamView = AttriBox[BeamView](THIS)
  curveView = AttriBox[LabCurve](THIS)
  controlView = AttriBox[ControlCurve](THIS)
  beamPanel = AttriBox[BeamPanel](THIS)
  status = AttriBox[TestStatus](THIS)
  stepTimer = AttriBox[QTimer](THIS)
  worker = AttriBox[Worker]()

  #  Virtual Variables
  experiment: Field[BeamExperiment] = Field()
  running: Field[bool] = Field()
  cast: Field[int] = Field()
  setup: Field[BeamSetup] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @experiment.GET
  def _getExperiment(self, ) -> BeamExperiment | None:
    """The 'experiment' getter returns the test of the beam, or 'None'
    before it is started."""
    return self.__lab_test__

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the test is running, not
    paused and not at its end."""
    return True if self.stepTimer.isActive() else False

  @cast.GET
  def _getCast(self, ) -> int:
    """The 'cast' getter returns which beam this is, counted from 1: the
    seed its concrete's scatter is drawn from."""
    return self.__cast_number__

  @setup.GET
  def _getSetup(self, ) -> BeamSetup:
    """The 'setup' getter returns the beam on its rig: as the test
    began, if there is one, retuning not counted."""
    if self.__test_setup__ is not None:
      return self.__test_setup__
    return BeamSetup(self.beamView.beam, self.beamView.rig)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the lab out and sizes the window."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 4)
    layout.addWidget(self.controlPanel, 1, 0, 2, 1)
    layout.addWidget(self.beamView, 1, 1, 1, 2)
    layout.addWidget(self.curveView, 2, 1)
    layout.addWidget(self.controlView, 2, 2)
    layout.addWidget(self.beamPanel, 1, 3, 2, 1)
    layout.addWidget(self.status, 3, 0, 1, 4)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 3)
    layout.setColumnStretch(2, 2)
    layout.setColumnStretch(3, 0)
    layout.setRowStretch(1, 3)
    layout.setRowStretch(2, 2)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    beam = self.beamPanel.beam
    self.beamView.beam = beam
    self.beamView.rig = Rig.standard(beam)
    self.beamView.setFocus()
    self.setRig(self.beamView.rig)

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons, the edits and the
    timer."""
    bar = self.toolBar
    bar.startButton.clicked.connect(self.startTest)
    bar.pauseButton.clicked.connect(self.togglePause)
    bar.newButton.clicked.connect(self.newBeam)
    bar.openButton.clicked.connect(self.askOpen)
    bar.saveButton.clicked.connect(self.askSave)
    bar.supportButton.clicked.connect(self.addSupport)
    bar.actuatorButton.clicked.connect(self.addActuator)
    bar.transducerButton.clicked.connect(self.addTransducer)
    bar.gapButton.clicked.connect(self.addGap)
    bar.removeButton.clicked.connect(self.beamView.removeSelected)
    self.beamPanel.edited.connect(self.setBeam)
    self.controlPanel.rigEdited.connect(self.setRig)
    self.controlPanel.controlTuned.connect(self.retune)
    self.beamView.rigEdited.connect(self.setRig)
    self.beamView.beamEdited.connect(self.setBeam)
    self.controlPanel.beamEdited.connect(self.setBeam)
    self.beamView.selectionChanged.connect(self.selected)
    self.beamView.refused.connect(self.controlPanel.showNote)
    self.stepTimer.timeout.connect(self.advance)
    fileMenu = self.mainMenuBar.fileMenu
    fileMenu.openAction.triggered.connect(self.askOpen)
    fileMenu.saveAction.triggered.connect(self.askSave)
    fileMenu.exitAction.triggered.connect(self.close)

  def closeEvent(self, event: QCloseEvent) -> None:
    """Closing the window ends the test and OpenSees's process."""
    MainWindow.closeEvent(self, event)
    if event.isAccepted():
      self.stepTimer.stop()
      if self.experiment is not None:
        self.experiment.close()
      self.worker.close()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setBeam(self, beam: RCBeam) -> None:
    """The 'setBeam' method shows 'beam', its rig taken along, stretched
    if it is longer or shorter."""
    view = self.beamView
    rig = view.rig
    if beam.length != view.beam.length:
      rig = rig.stretched(beam.length / view.beam.length)
    view.beam = beam
    self.beamPanel.showBeam(beam)
    self.setRig(rig)

  def setRig(self, rig: Rig) -> None:
    """The 'setRig' method shows 'rig', in the view and the panel."""
    view = self.beamView
    view.rig = rig
    self.controlPanel.showRig(view.beam, rig, view.selected)
    self.refresh()

  def retune(self, control: Control) -> None:
    """The 'retune' method has the test's control run on as 'control',
    a new limit turning the rate's sign to head for it, or the panel
    say why it cannot."""
    experiment, view = self.experiment, self.beamView
    if experiment is None or experiment.finished:
      return
    if control.limit != experiment.rig.control.limit:
      control = control.towards(experiment.command)
    try:
      experiment.retune(control)
    except ValueError as exception:
      words = str(exception)
      self.controlPanel.showNote('%s%s.' % (words[:1].upper(), words[1:]))
    view.rig = experiment.rig
    self.controlPanel.showRig(view.beam, view.rig, view.selected)
    self.refresh()

  def selected(self, part: tuple[str, int] | None) -> None:
    """The 'selected' method shows the part selected in the panel."""
    view = self.beamView
    self.controlPanel.showNote('')
    self.controlPanel.showRig(view.beam, view.rig, part)
    self.refresh()

  def addSupport(self, ) -> None:
    """The 'addSupport' method puts a roller in the widest gap between
    the supports and the beam's ends, selected."""
    view = self.beamView
    if not view.editable:
      return
    rig = view.rig
    x = _widestGap(
        [
          0.0, view.beam.length,
          *[support.at for support in rig.supports]
        ]
        )
    self._added(
      rig.withSupports(*rig.supports, Support(x, 'roller')),
      ('support', len(rig.supports))
      )

  def addActuator(self, ) -> None:
    """The 'addActuator' method puts an actuator in the widest gap
    between the supports and the actuators, following the one driven,
    as hard, selected."""
    view = self.beamView
    if not view.editable:
      return
    rig = view.rig
    places = [support.at for support in rig.supports]
    places += [actuator.at for actuator in rig.actuators]
    actuator = Actuator(_widestGap(places), rig.driven, 1.0)
    self._added(
      rig.withActuators(*rig.actuators, actuator),
      ('actuator', len(rig.actuators))
      )

  def addTransducer(self, ) -> None:
    """The 'addTransducer' method puts a transducer in the widest gap
    between the supports and the transducers, selected."""
    view = self.beamView
    if not view.editable:
      return
    rig = view.rig
    places = [support.at for support in rig.supports]
    places += [*rig.transducers]
    self._added(
      rig.withTransducers(*rig.transducers, _widestGap(places)),
      ('transducer', len(rig.transducers))
      )

  def addGap(self, ) -> None:
    """The 'addGap' method leaves the widest stretch between the
    supports and the actuators without stirrups, but 50 mm at either
    end, selected."""
    view = self.beamView
    if not view.editable:
      return
    beam, rig = view.beam, view.rig
    places = sorted({*[support.at for support in rig.supports],
                     *[actuator.at for actuator in rig.actuators]})
    _, start, end = max((end - start, start, end)
                        for start, end in zip(places, places[1:]))
    inset = min(50.0, (end - start) / 4)
    stirrups = beam.stirrups.withGap(start + inset, end - inset)
    self.setBeam(beam.withStirrups(stirrups))
    view.select(('gap', len(stirrups.gaps) - 1))

  def _added(self, rig: Rig, part: tuple[str, int]) -> None:
    """Shows 'rig' with 'part' added, selected."""
    self.beamView.rig = rig
    self.beamView.select(part)
    self.setRig(rig)

  def startTest(self, ) -> None:
    """The 'startTest' method starts testing the beam as set up."""
    if self.experiment is not None:
      return
    view = self.beamView
    setup = BeamSetup(view.beam, view.rig)
    experiment = BeamExperiment(
      view.beam, view.rig, self.cast,
      self.worker
      )
    self.__lab_test__ = experiment
    self.__test_setup__ = setup
    self.__run_seconds__ = 0.0
    view.experiment = experiment
    self.curveView.experiment = experiment
    self.controlView.experiment = experiment
    self.stepTimer.start(self.__step_ms__)
    self.refresh()
    self.status.repaint()

  def togglePause(self, ) -> None:
    """The 'togglePause' method pauses the test running, or resumes the
    test paused."""
    experiment = self.experiment
    if experiment is None or experiment.finished:
      return
    if self.running:
      self.stepTimer.stop()
    else:
      self.stepTimer.start(self.__step_ms__)
    self.refresh()

  def newBeam(self, ) -> None:
    """The 'newBeam' method casts the beam afresh, untested, its
    concrete scattered anew, on its rig as the test began, any retuning
    undone."""
    self.stepTimer.stop()
    setup = self.__test_setup__
    if self.experiment is not None:
      self.experiment.close()
      self.__cast_number__ += 1
    self.__lab_test__ = None
    self.__test_setup__ = None
    for view in (self.beamView, self.curveView, self.controlView):
      view.experiment = None
    if setup is None:
      return self.refresh()
    self.setRig(setup.rig)

  def askOpen(self, *_) -> None:
    """The 'askOpen' method asks for a '.beam' file to open, without
    waiting for the answer: the setup is opened once a file is
    chosen."""
    dialog = self.__open_dialog__
    if dialog is None:
      dialog = self._fileDialog('Open setup', self.openFrom)
      dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
      self.__open_dialog__ = dialog
    dialog.setDirectory(os.path.dirname(self._suggestedPath()))
    dialog.open()

  def askSave(self, *_) -> None:
    """The 'askSave' method asks where to save the setup, without
    waiting for the answer: it is written once a file is chosen."""
    dialog = self.__save_dialog__
    if dialog is None:
      dialog = self._fileDialog('Save setup', self.saveTo)
      dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
      dialog.setDefaultSuffix('beam')
      self.__save_dialog__ = dialog
    dialog.selectFile(self._suggestedPath())
    dialog.open()

  def openFrom(self, path: str) -> None:
    """The 'openFrom' method sets the beam up on its rig as the file at
    'path' holds them, any test ended as 'New beam' ends it; a file
    that holds no setup is refused, the status saying why."""
    try:
      with open(path, 'r', -1, 'utf-8') as file:
        setup = BeamSetup(file.read())
    except (OSError, ValueError) as exception:
      name = os.path.basename(path)
      return self._say('could not open %s: %s' % (name, exception))
    self.__setup_path__ = path
    self.newBeam()
    view = self.beamView
    view.select(None)
    view.beam = setup.beam
    self.beamPanel.showBeam(setup.beam)
    self.setRig(setup.rig)
    self._say('opened %s' % os.path.basename(path))

  def saveTo(self, path: str) -> None:
    """The 'saveTo' method writes the setup to the file at 'path'."""
    try:
      with open(path, 'w', -1, 'utf-8') as file:
        file.write('%s\n' % self.setup)
    except OSError as exception:
      name = os.path.basename(path)
      return self._say('could not save %s: %s' % (name, exception))
    self.__setup_path__ = path
    self._say('saved to %s' % os.path.basename(path))

  def _fileDialog(self, title: str, slot: object) -> QFileDialog:
    """A dialog of 'title' for '.beam' files, Qt's own rather than the
    system's, calling 'slot' with the file chosen."""
    dialog = QFileDialog(self, title)
    dialog.setNameFilter(self.__file_filter__)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.fileSelected.connect(slot)
    return dialog

  def _suggestedPath(self, ) -> str:
    """The file last opened or saved, or else 'beam 1.beam', by the
    cast, in the home folder."""
    if self.__setup_path__ is not None:
      return self.__setup_path__
    name = 'beam %d.beam' % self.cast
    return os.path.join(os.path.expanduser('~'), name)

  def _say(self, words: str) -> None:
    """Shows 'words' in the status, for what is going on."""
    mode, text, _ = self.statusOf()
    self.status.showState(mode, text, words)

  def advance(self, ) -> None:
    """The 'advance' method moves the test on without waiting for
    OpenSees: it reads the cycle under way if it is done, and begins the
    next, so the window answers while OpenSees reckons; it stops the
    test at its end, and shows how far it has come."""
    experiment = self.experiment
    if experiment is None:
      return
    now = time.monotonic()
    read = False
    if experiment.pending and experiment.ready():
      read = experiment.collect() is not None
    if not experiment.pending and not experiment.finished:
      experiment.begin()
    self.__run_seconds__ += time.monotonic() - now
    if experiment.finished:
      self.stepTimer.stop()
    if read or experiment.finished:
      for view in (self.beamView, self.curveView, self.controlView):
        view.update()
      self.refresh()

  def settle(self, ) -> None:
    """The 'settle' method waits for the cycle under way, reads it and
    shows it: a step of the test made whole."""
    experiment = self.experiment
    if experiment is None:
      return
    if not experiment.pending:
      experiment.begin()
    experiment.collect()
    if experiment.finished:
      self.stepTimer.stop()
    for view in (self.beamView, self.curveView, self.controlView):
      view.update()
    self.refresh()

  def refresh(self, ) -> None:
    """The 'refresh' method greys out what cannot be done now, lights
    the test's button while it runs, and says what is going on."""
    bar = self.toolBar
    experiment = self.experiment
    live = experiment is not None and not experiment.finished
    bar.startButton.setEnabled(True if experiment is None else False)
    bar.startButton.checked = live
    bar.pauseButton.setEnabled(live)
    paused = live and not self.running
    bar.pauseButton.text = 'Resume' if paused else 'Pause'
    editable = self.beamView.editable
    for button in (
        bar.supportButton, bar.actuatorButton,
        bar.transducerButton, bar.gapButton
    ):
      button.setEnabled(editable)
    selected = self.beamView.selected is not None
    bar.removeButton.setEnabled(editable and selected)
    for button in (
        bar.startButton, bar.pauseButton, bar.supportButton,
        bar.actuatorButton, bar.transducerButton, bar.gapButton,
        bar.removeButton
    ):
      button.update()
    self.beamPanel.setLocked(not editable)
    if experiment is None:
      self.controlPanel.setStage('setup')
    else:
      self.controlPanel.setStage('testing' if live else 'tested')
    self.status.showState(*self.statusOf())

  def statusOf(self, ) -> tuple[str, str, str]:
    """The 'statusOf' method says what is going on: the state, in words,
    and the details."""
    experiment = self.experiment
    beam, rig = self.beamView.beam, self.beamView.rig
    control = rig.control
    loop = 'T%d drives A%d' % (control.transducer + 1, rig.driven + 1)
    if experiment is None:
      depth = beam.height - beam.bottom.depth
      ratio = 100 * beam.bottom.area / (beam.width * depth)
      details = ('%g × %g × %g mm, ρ = %.2f %% · %d supports, %d '
                 'actuators, %d transducers · %s at %.3g mm/s, '
                 'steps of %.3g mm every %.3g s' % (
                   beam.length, beam.height, beam.width, ratio,
                   len(rig.supports), len(rig.actuators),
                   len(rig.transducers), loop, control.rate,
                   abs(control.step * control.limit), rig.cycle
                 ))
      return 'idle', 'Beam %d ready' % self.cast, details
    seconds = int(self.__run_seconds__)
    clock = '%d:%02d' % (seconds // 60, seconds % 60)
    reading = experiment.latest
    if experiment.finished:
      peak = experiment.peak
      details = '%s · peak %.1f kN at %.2f mm · %.0f s · %s' % (
        experiment.ending, peak.force, peak.feedback, reading.time,
        clock
      )
      return 'finished', 'Test finished', details
    if not experiment.readings:
      return (
        'casting', 'Starting the test',
        'OpenSees is setting the beam up'
      )
    details = ('%s: command %.2f mm, reads %.2f mm · force %.1f kN · '
               'step %d of %.3g mm · %.0f s · %s' % (
                 loop, reading.command, reading.feedback,
                 reading.force, reading.step, experiment.stepLength,
                 reading.time, clock
               ))
    if self.running:
      return 'running', 'Test running', details
    return 'paused', 'Test paused', details
