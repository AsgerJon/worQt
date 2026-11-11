"""
RunBeamView covers 'BeamView', the beam on its rig as the lab sees it:
any part of the rig is selected by a click and dragged along the beam
to the centimetre, never where the rig would not fit; Delete removes
the part selected, or says why it cannot; during a test nothing moves,
and the beam deflects and cracks from the face pulled.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF

from worksees import Worker

from worQt.engineering.lab import BeamExperiment, Support
from worQt.engineering.lab.gui import BeamView

from . import LabWidgetTest, smallBeam, smallRig, standardBeam


class RunBeamView(LabWidgetTest):
  """Tests for 'BeamView'."""

  def openView(self) -> BeamView:
    """The view of the standard beam, shown live."""
    view = BeamView()
    view.resize(1100, 480)
    self.showLive(view)
    return view

  def partPoint(self, view: BeamView, part: tuple[str, int]) -> QPointF:
    """The middle of 'part' on screen."""
    for found, rect in view.parts():
      if found == part:
        return rect.center()
    raise KeyError(part)

  def dragTo(self, view: BeamView, part: tuple[str, int],
             x: float) -> None:
    """Drags 'part' with the mouse to 'x' along the beam."""
    start = self.partPoint(view, part)
    target = QPointF(view.toScreen(x, 0.0).x(), start.y())
    self.press(view, start)
    self.move(view, target)
    self.release(view, target)

  def run_drag_each_part(self) -> None:
    """A transducer, an actuator and a support dragged along the beam
    move there, to the centimetre, selected, emitting 'rigEdited'."""
    view = self.openView()
    spy = self.spy(view.rigEdited)
    self.dragTo(view, ('transducer', 2), 1234.0)
    self.assertEqual(view.rig.transducers[2], 1230.0)
    self.assertEqual(view.selected, ('transducer', 2))
    self.dragTo(view, ('actuator', 1), 2400.0)
    self.assertEqual(view.rig.actuators[1].at, 2400.0)
    self.dragTo(view, ('support', 0), 300.0)
    self.assertEqual(view.rig.supports[0], Support(300.0, 'pin'))
    self.assertGreaterEqual(spy.count, 3)

  def run_never_where_it_does_not_fit(self) -> None:
    """Nothing is dragged off the beam."""
    view = self.openView()
    rig = view.rig
    view.drag(('support', 1), 3500.0)
    view.drag(('actuator', 0), -50.0)
    self.assertEqual(view.rig.supports, rig.supports)
    self.assertEqual(view.rig.actuators, rig.actuators)

  def run_select_and_delete(self) -> None:
    """A click selects a part; Delete removes it, emitting 'rigEdited';
    a click on nothing selects nothing."""
    view = self.openView()
    selections = self.spy(view.selectionChanged)
    self.click(view, self.partPoint(view, ('transducer', 0)))
    self.assertEqual(view.selected, ('transducer', 0))
    self.assertEqual(selections.emissions[-1], (('transducer', 0),))
    edits = self.spy(view.rigEdited)
    self.key(view, Qt.Key.Key_Delete)
    self.assertEqual(view.rig.transducers, (2150.0, 1650.0))
    self.assertEqual(view.rig.control.transducer, 1)
    self.assertIsNone(view.selected)
    self.assertEqual(edits.count, 1)
    self.click(view, QPointF(5.0, 5.0))
    self.assertIsNone(view.selected)

  def run_refused(self) -> None:
    """The actuator driven, or the last support but one, is not removed;
    'refused' says why."""
    view = self.openView()
    refusals = self.spy(view.refused)
    view.select(('actuator', 0))
    view.removeSelected()
    self.assertEqual(len(view.rig.actuators), 2)
    self.assertIn('A1 stays', refusals.emissions[-1][0])
    view.select(('support', 1))
    view.removeSelected()
    self.assertEqual(len(view.rig.supports), 2)
    self.assertIn('turn', refusals.emissions[-1][0])

  def run_during_a_test(self) -> None:
    """During a test nothing moves; the beam deflects, and cracks open
    on its face between its supports, each the way it runs."""
    view = self.openView()
    beam = smallBeam()
    worker = Worker()
    experiment = BeamExperiment(beam, smallRig(), 1, worker)
    try:
      view.experiment = experiment
      self.assertFalse(view.editable)
      experiment.advance(15)
      view.drag(('transducer', 0), 500.0)
      self.assertEqual(view.rig.transducers[0], 600.0)
      self.assertGreater(view.deflectionAt(800.0), 1.0)
      self.assertLess(view.deflectionAt(0.0), 0.0)
      cracks = view.cracks()
      self.assertGreater(len(cracks), 3)
      for x, y, run, width in cracks:
        self.assertTrue(100.0 < x < 1500.0)
        self.assertTrue(0.0 < y < beam.height)
        self.assertGreater(width, 0.0)
      self.assertEqual(len(view.stirrups()),
                       len(experiment.mesh.stirrupPlaces))
    finally:
      experiment.close()
      worker.close()

  def run_gaps(self) -> None:
    """A gap in the stirrups is dragged whole along the beam, emitting
    'beamEdited', and Delete fills it."""
    view = self.openView()
    view.beam = standardBeam().withStirrups(
        standardBeam().stirrups.withGap(200.0, 1000.0))
    edits = self.spy(view.beamEdited)
    view.select(('gap', 0))
    view.drag(('gap', 0), 1700.0)
    self.assertEqual(view.beam.stirrups.gaps, ((1300.0, 2100.0),))
    self.assertEqual(edits.count, 1)
    self.key(view, Qt.Key.Key_Delete)
    self.assertEqual(view.beam.stirrups.gaps, ())
    self.assertIsNone(view.selected)
