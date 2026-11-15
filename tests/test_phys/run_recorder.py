"""
RunRecorder covers 'Recorder', which writes what a view paints into a
video (through ffmpeg) and what each frame was painted from into a log
beside it: frames handed over a sixtieth of a second apart make one
frame of the video each, a slow one as many as the time it stood for;
the log holds an entry for every frame handed over, with its number in
the video and how often it was written; the video is as long as the
time the frames stood for.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

from PySide6.QtGui import QColor, QImage

from worQt.phys.gui import Recorder
from worQt.qtest import AppTest


class RunRecorder(AppTest):
  """Tests for 'Recorder'."""

  def run_writes_video_and_log(self) -> None:
    """Twenty frames a sixtieth apart, then one a tenth of a second
    later: the video has 26 frames at 60 a second, the last written six
    times; the log has the 21 frames handed over."""
    if shutil.which('ffmpeg') is None:
      self.skipTest('ffmpeg is not installed')
    folder = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, folder, True)
    path = os.path.join(folder, 'clip.mp4')
    recorder = Recorder(path, 60, 1.0, {'place': 'nowhere'})
    times = [(k + 0.5) / 60.0 for k in range(20)] + [(25.5) / 60.0]
    for k, now in enumerate(times):
      image = QImage(64, 48, QImage.Format.Format_RGB32)
      image.fill(QColor(10 * k, 100, 200))
      self.assertTrue(recorder.add(image, 100.0 + now, {'k': k}))
    recorder.finish()
    recorder.thread.join(60.0)
    self.assertFalse(recorder.writing)
    self.assertIsNone(recorder.error)
    counted = subprocess.run(
      ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
       '-count_frames', '-show_entries', 'stream=nb_read_frames,'
       'r_frame_rate', '-of', 'default=nw=1:nk=1', path],
      capture_output=True, text=True).stdout.split()
    self.assertEqual(counted, ['60/1', '26'])
    with open(os.path.join(folder, 'clip.json')) as file:
      log = json.load(file)
    self.assertEqual(log['meta'], {'place': 'nowhere'})
    frames = log['frames']
    self.assertEqual([frame['k'] for frame in frames], list(range(21)))
    self.assertEqual([frame['video'] for frame in frames], list(range(21)))
    self.assertEqual(frames[-1]['repeats'], 6)
    self.assertEqual(sum(frame['repeats'] for frame in frames), 26)

  def run_time_is_up(self) -> None:
    """A frame handed over past the time to record says so."""
    folder = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, folder, True)
    recorder = Recorder(os.path.join(folder, 'clip.mp4'), 60, 0.5, {})
    image = QImage(16, 16, QImage.Format.Format_RGB32)
    image.fill(QColor(0, 0, 0))
    self.assertTrue(recorder.add(image, 10.0, {}))
    self.assertFalse(recorder.add(image, 10.6, {}))
    recorder.finish()
    recorder.thread.join(60.0)
