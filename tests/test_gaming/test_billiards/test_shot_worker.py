"""
TestShotWorker covers 'ShotWorker': a shot asked of it streams back as
it is recorded here; a shot asked for drops the one under way; asked
many in a row, as a map asks while the aim turns, it plays the last;
closed, its process is gone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time

from worQt.gaming.billiards import CaromTable, Cue, Motion, Recorder
from worQt.gaming.billiards import Recording
from worQt.gaming.billiards import ShotWorker

from . import BilliardsTest, firstBreak

RECORDER = Recorder(Motion())


def streamed(worker: ShotWorker, names: tuple) -> Recording:
  """The shot under way, all of it, as it streams back, a stretch or
  more at a time; a minute at most."""
  recording = Recording(names, RECORDER.rate)
  deadline = time.monotonic() + 60.0
  while not recording.over and time.monotonic() < deadline:
    for stretch in worker.waited(1.0):
      recording = recording.joined(stretch)
  return recording


class TestShotWorker(BilliardsTest):
  """Tests for 'ShotWorker'."""

  def test_streams(self) -> None:
    """A shot streams back as it is recorded here; asked for at once
    after another, the first is dropped; closed, the process is gone."""
    worker = ShotWorker()
    try:
      worker.warm()
      self.assertTrue(worker.running)
      struck = firstBreak()
      worker.start(RECORDER, CaromTable().opening())
      worker.start(RECORDER, struck)
      names = tuple(ball.name for ball in struck)
      recording = streamed(worker, names)
      here = RECORDER.recorded(struck)
      self.assertTrue(recording.over)
      self.assertEqual(recording.count(), here.count())
      self.assertEqual(recording.last(), here.last())
      self.assertEqual(recording.touches, here.touches)
    finally:
      worker.close()
    self.assertFalse(worker.running)

  def test_latest(self) -> None:
    """Asked many shots in a row, as a map asks while the aim turns, it
    plays the last, as it is recorded here."""
    worker = ShotWorker()
    table, cue = CaromTable(), Cue()
    white, yellow, red = table.opening()
    shots = []
    for k in range(20):
      angle = -1.9 + 0.01 * k
      struck = cue.sent(white, math.cos(angle), math.sin(angle), 3000.0,
                        0.2, 0.0, table.radius)
      shots.append((struck, yellow, red))
    try:
      worker.warm()
      for shot in shots:
        worker.start(RECORDER, shot)
      recording = streamed(worker, ('white', 'yellow', 'red'))
      self.assertTrue(recording.over)
      self.assertEqual(recording.last(), RECORDER.recorded(shots[-1]).last())
    finally:
      worker.close()
