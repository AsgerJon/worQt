"""
RunMesoApp covers 'MesoApp' and its 'MesoWindow': the window opens at
once, nothing cast yet, the tests greyed out; 'New cylinder' casts one
and shows it, and casts another each time after; 'Compression test' and
'Tension test' start one on it, running as the window steps it, 'Pause'
and 'Resume' stop and go on. A test run to its end
stops, and its curve reads off its strength. The 'Paste' slider makes
the paste clear, to see the stones of the whole cylinder through it.

The window casts the whole cylinder and builds its lattice in space; a
test is of the materials the ingredient sliders show, on the graphics
card if 'Use GPU' is ticked and torch has one. The window here casts a
small cylinder on a coarse lattice, so a test runs in half a minute.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

import torch

from worQt.engineering.meso import CompressionTest, TensionTest
from worQt.engineering.meso import Lattice3D, WholeCylinder
from worQt.engineering.meso.gui import MesoApp, MesoWindow

from . import MesoWidgetTest


class _SmallWindow(MesoWindow):
  """The window, casting a small cylinder on a coarse lattice."""

  __cast_diameter__ = 30.0
  __cast_height__ = 60.0
  __cast_max_size__ = 8.0
  __lattice_spacing__ = 2.0


class RunMesoApp(MesoWidgetTest):
  """Tests for 'MesoApp' and 'MesoWindow'."""

  __application_type__ = MesoApp
  __time_out__ = 300.0

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)

  def openWindow(self) -> MesoWindow:
    """The small window, shown live, so its UI is built, a cylinder cast
    in it."""
    window = self.openEmpty()
    self.click(window.toolBar.newButton)
    return window

  def openEmpty(self) -> MesoWindow:
    """The small window, shown live, nothing cast yet."""
    window = _SmallWindow()
    self.showLive(window)
    return window

  def run_opens_at_once(self) -> None:
    """The window opens at once, nothing cast, the tests and 'Pause'
    greyed out and 'New cylinder' not."""
    window = self.openEmpty()
    bar = window.toolBar
    self.assertEqual(window.windowTitle(), 'Concrete')
    self.assertIsNone(window.cylinder)
    self.assertIsNone(window.lattice)
    self.assertIsNone(window.cylinderView.lattice)
    self.assertIsNone(window.test)
    self.assertFalse(window.running)
    self.assertTrue(bar.newButton.isEnabled())
    self.assertFalse(bar.compressionButton.isEnabled())
    self.assertFalse(bar.tensionButton.isEnabled())
    self.assertFalse(bar.pauseButton.isEnabled())

  def run_the_first_cylinder(self) -> None:
    """'New cylinder' casts the first cylinder and shows it, untested,
    with the tests to start and nothing to pause."""
    window = self.openEmpty()
    bar = window.toolBar
    self.click(bar.newButton)
    self.assertEqual(window.cylinder.seed, 1)
    self.assertIsInstance(window.lattice, Lattice3D)
    self.assertIs(window.cylinderView.lattice, window.lattice)
    self.assertIsNone(window.test)
    self.assertTrue(bar.compressionButton.isEnabled())
    self.assertTrue(bar.tensionButton.isEnabled())
    self.assertFalse(bar.pauseButton.isEnabled())

  def run_a_compression_test(self) -> None:
    """'Compression test' starts crushing the cylinder; the window steps
    it, and both views show it."""
    window = self.openWindow()
    self.click(window.toolBar.compressionButton)
    self.assertIsInstance(window.test, CompressionTest)
    self.assertTrue(window.running)
    self.assertTrue(window.toolBar.pauseButton.isEnabled())
    self.assertEqual(window.toolBar.pauseButton.text, 'Pause')
    window.advance()
    self.assertGreater(window.test.step, 0)
    self.assertIs(window.cylinderView.test, window.test)
    self.assertIs(window.curveView.test, window.test)

  def run_pause_and_resume(self) -> None:
    """'Pause' stops the test and becomes 'Resume', which goes on."""
    window = self.openWindow()
    self.click(window.toolBar.tensionButton)
    self.click(window.toolBar.pauseButton)
    self.assertFalse(window.running)
    self.assertEqual(window.toolBar.pauseButton.text, 'Resume')
    step = window.test.step
    self.click(window.toolBar.pauseButton)
    self.assertTrue(window.running)
    self.assertEqual(window.toolBar.pauseButton.text, 'Pause')
    window.advance()
    self.assertGreater(window.test.step, step)

  def run_a_new_cylinder(self) -> None:
    """'New cylinder' casts another, untested."""
    window = self.openWindow()
    seed = window.cylinder.seed
    self.click(window.toolBar.compressionButton)
    self.click(window.toolBar.newButton)
    self.assertEqual(window.cylinder.seed, seed + 1)
    self.assertIsNone(window.test)
    self.assertFalse(window.running)
    self.assertIs(window.cylinderView.lattice, window.lattice)

  def run_to_the_end(self) -> None:
    """A test run to its end stops, with nothing left to pause, and its
    curve reads off its strength."""
    window = self.openWindow()
    self.click(window.toolBar.tensionButton)
    self.assertIsInstance(window.test, TensionTest)
    while not window.test.finished:
      window.advance()
    self.assertFalse(window.running)
    self.assertFalse(window.toolBar.pauseButton.isEnabled())
    self.assertTrue(window.curveView.peakText().startswith('ft = '))
    sliders = window.ingredients.sliders()
    self.assertTrue(all(slider.isEnabled() for slider in sliders))

  def run_the_paste_slider(self) -> None:
    """The cylinder is cast whole and shown; the 'Paste' slider starts
    solid, and what it is set to the section's paste is."""
    window = self.openWindow()
    self.assertIsInstance(window.cylinder, WholeCylinder)
    self.assertIs(window.cylinderView.cylinder, window.cylinder)
    slider = window.toolBar.pasteSlider
    self.assertEqual(slider.text, 'Paste')
    self.assertEqual(slider.value, 1.0)
    slider.value = 0.3
    self.assertAlmostEqual(window.cylinderView.pasteOpacity, 0.3)
    self.click(window.toolBar.newButton)
    self.assertIs(window.cylinderView.cylinder, window.cylinder)
    self.assertAlmostEqual(window.cylinderView.pasteOpacity, 0.3)

  def run_the_gpu_box(self) -> None:
    """'Use GPU' can be ticked only where torch has a graphics card;
    without one, or unticked, tests are reckoned on the processor."""
    window = self.openWindow()
    gpu = window.toolBar.gpuBox
    self.assertEqual(gpu.text, 'Use GPU')
    self.assertEqual(gpu.isEnabled(), torch.cuda.is_available())
    self.assertEqual(window.device(), 'cpu')
    gpu.checked = True
    wanted = 'cuda' if torch.cuda.is_available() else 'cpu'
    self.assertEqual(window.device(), wanted)

  def run_the_ingredients(self) -> None:
    """A test is of the materials the sliders show, and the sliders are
    greyed out while it runs."""
    window = self.openWindow()
    window.ingredients.pasteTension.quantity = 6.0
    self.click(window.toolBar.compressionButton)
    self.assertEqual(window.test.materials[1].tension, 6.0)
    self.assertEqual(window.test.device, 'cpu')
    sliders = window.ingredients.sliders()
    self.assertFalse(any(slider.isEnabled() for slider in sliders))

  def run_the_status(self) -> None:
    """The strip along the bottom says what is going on: nothing cast,
    a cylinder ready, a test running, paused, finished."""
    window = self.openEmpty()
    status = window.status
    self.assertEqual(status.mode, 'idle')
    self.assertEqual(status.text, 'No cylinder yet')
    self.click(window.toolBar.newButton)
    self.assertEqual(status.mode, 'idle')
    self.assertEqual(status.text, 'Cylinder 1 ready')
    self.click(window.toolBar.tensionButton)
    self.assertEqual(status.mode, 'running')
    self.assertEqual(status.text, 'Tension test running')
    window.advance()
    self.assertIn('strain', status.details)
    self.assertIn('steps', status.details)
    self.click(window.toolBar.pauseButton)
    self.assertEqual(status.mode, 'paused')
    self.assertEqual(status.text, 'Tension test paused')
    self.click(window.toolBar.pauseButton)
    while not window.test.finished:
      window.advance()
    self.assertEqual(status.mode, 'finished')
    self.assertEqual(status.text, 'Tension test finished')
    self.assertIn('ft = ', status.details)

  def run_the_running_button(self) -> None:
    """While a test runs, its button stays lit, and only its button."""
    window = self.openWindow()
    bar = window.toolBar
    self.assertFalse(bar.compressionButton.checked)
    self.click(bar.compressionButton)
    self.assertTrue(bar.compressionButton.checked)
    self.assertFalse(bar.tensionButton.checked)
    self.click(bar.newButton)
    self.assertFalse(bar.compressionButton.checked)

  def run_the_export(self) -> None:
    """'Export PDF' is greyed out until a test is begun; then it asks
    where to write the report, and the report is written there."""
    window = self.openWindow()
    bar = window.toolBar
    self.assertFalse(bar.exportButton.isEnabled())
    self.click(bar.tensionButton)
    window.advance()
    self.assertTrue(bar.exportButton.isEnabled())
    self.click(bar.exportButton)
    dialog = window.exportDialog
    self.assertTrue(dialog.isVisible())
    dialog.reject()
    folder = tempfile.mkdtemp()
    path = os.path.join(folder, 'report.pdf')
    window.exportPdf(path)
    with open(path, 'rb') as file:
      self.assertEqual(file.read(5), b'%PDF-')
