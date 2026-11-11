"""
RunPusherWindow covers 'PusherApp' and its 'PusherWindow': it opens on
an empty machine starting in a process of its own, saying so until the
first frame comes, the strip along the bottom moving meanwhile, the
chutes shut; 'Start game' has the house pour the
coins in, counts down over the machine and says GO!, and then the
chutes open and each drops a coin;
'Pause' stops the machine and says 'Play'; closing the window ends the
process.

The first run on a computer compiles the coin solver, which takes a
minute: the first frame is waited for up to two.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.pusher.gui import PusherApp, PusherWindow

from . import PusherWidgetTest


class RunPusherWindow(PusherWidgetTest):
  """Tests for 'PusherWindow'."""

  __time_out__ = 240

  def openWindow(self) -> PusherWindow:
    """The window, shown live, its machine's first frame come."""
    window = PusherWindow()
    self.showLive(window)
    self.assertTrue(window.panel.starting())
    self.wait(300)
    if window.snapshot is None:
      self.assertEqual(window.status.text, 'Starting the machine')
      self.assertTrue(window.status.moving)
    came = self.waitUntil(lambda: window.snapshot is not None, 120000)
    self.assertTrue(came)
    return window

  def startedWindow(self) -> PusherWindow:
    """The window, a game started and the coins poured in."""
    window = self.openWindow()
    self.click(window.toolBar.newButton)
    self.assertTrue(self.waitUntil(lambda: window.snapshot.filling, 5000))
    banner = lambda: window.view.rootObject().property('banner')
    self.assertTrue(self.waitUntil(lambda: banner() == '3', 60000))
    self.assertTrue(self.waitUntil(lambda: banner() == 'GO!', 10000))
    self.assertTrue(window.snapshot.started)
    return window

  def run_opens(self) -> None:
    """It opens titled, the scene in with no errors, the machine empty,
    the purse full, the chutes shut, the panel asking for a game."""
    window = self.openWindow()
    self.assertEqual(window.windowTitle(), 'Coin pusher')
    self.assertIs(PusherApp.__window_class__, PusherWindow)
    self.assertTrue(self.waitUntil(lambda: window.view.loaded, 10000))
    self.assertEqual(window.view.problems, ())
    snapshot = window.snapshot
    self.assertEqual((snapshot.purse, snapshot.onMachine), (60, 0))
    self.assertFalse(snapshot.started)
    bar = window.toolBar
    self.assertFalse(bar.leftButton.isEnabled())
    self.assertFalse(bar.rightButton.isEnabled())
    self.assertEqual(bar.newButton.text, 'Start game')
    self.assertIn('Start game', window.panel.words())
    window.close()
    self.assertFalse(window.worker.running)

  def run_start_game(self) -> None:
    """'Start game' pours the coins in; then the chutes open, each
    dropping a coin from the purse, the books balanced."""
    window = self.startedWindow()
    snapshot = window.snapshot
    self.assertGreater(snapshot.onMachine, 140)
    self.assertEqual(len(snapshot.places), snapshot.onMachine)
    self.assertEqual(snapshot.purse, 60)
    bar = window.toolBar
    self.assertTrue(bar.leftButton.isEnabled())
    self.click(bar.leftButton)
    self.click(bar.rightButton)
    dropped = lambda: window.snapshot.dropped == 2
    self.assertTrue(self.waitUntil(dropped, 5000))
    snapshot = window.snapshot
    self.assertEqual(snapshot.purse, 58)
    self.assertEqual(snapshot.purse + snapshot.onMachine + snapshot.inTray,
                     snapshot.total)
    window.close()

  def run_pause(self) -> None:
    """'Pause' stops the machine and says 'Play'; 'Play' runs it on."""
    window = self.openWindow()
    bar = window.toolBar
    self.click(bar.playButton)
    self.assertTrue(window.paused)
    self.assertEqual(bar.playButton.text, 'Play')
    self.wait(300)
    stopped = window.snapshot.time
    self.wait(500)
    self.assertAlmostEqual(window.snapshot.time, stopped, 6)
    self.click(bar.playButton)
    self.assertFalse(window.paused)
    self.assertTrue(self.waitUntil(lambda: window.snapshot.time > stopped,
                                   3000))
    window.close()
