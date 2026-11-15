"""
Recorder writes what a view paints into a video file as it is shown,
and what each frame was painted from into a log beside it: frames
handed to it with the time they were shown are written at a steady
'fps', each as often as the time it stood for (a slow frame shows as
long as it took), stamped with their number and time, through ffmpeg
(H.264) in a process of its own, fed from a thread so the window never
waits on it. The log (JSON: 'meta', then 'frames', one for each frame
handed over, its number in the video and what it was painted from) lets
a frame be painted again offscreen.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import queue
import subprocess
import threading

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage, QPainter


class Recorder:
  """Recorder writes 'seconds' of frames to the video 'path' (an .mp4)
  at 'fps' frames a second, and their log, with 'meta' at its head, to
  'path' with '.json' for its ending. 'add' a frame as it is shown;
  'finish' once done ('add' says when the time is up); 'writing' tells
  whether the file is still being written, 'pending' how many frames
  wait for it, 'error' what went wrong, if anything."""

  def __init__(self, path: str, fps: int, seconds: float,
               meta: dict) -> None:
    self.path, self.fps, self.seconds = path, fps, seconds
    self.log = {'meta': dict(meta), 'frames': []}
    self.started, self.written, self.size = None, 0, None
    self.error, self.process = None, None
    self.frames = queue.Queue()
    self.thread = threading.Thread(target=self._write, daemon=True)

  def add(self, image: QImage, now: float, drawn: dict) -> bool:
    """The 'add' method takes 'image' shown at 'now' (s, a steady clock),
    painted from 'drawn', and queues it for as many of the video's
    frames as have come due by then (none if it came within one; a
    frame due at the very time it is shown counts, the clock's rounding
    forgiven); returns whether there is time left to record."""
    if self.started is None:
      self.started, self.size = now, (image.width(), image.height())
      self._start()
    passed = now - self.started
    due = int(passed * self.fps + 1e-6) + 1
    repeats = max(0, due - self.written)
    self.log['frames'].append(dict(drawn, video=self.written,
                                   repeats=repeats, time=passed))
    if repeats and self.error is None:
      self._stamp(image, self.written, passed)
      self.frames.put((image, repeats))
      self.written += repeats
    return passed < self.seconds

  def left(self, now: float) -> float:
    """The 'left' method returns how long is left to record at 'now',
    s."""
    if self.started is None:
      return self.seconds
    return max(0.0, self.seconds - (now - self.started))

  def finish(self, ) -> None:
    """The 'finish' method ends the recording: the frames queued are
    written, the video closed, the log written, all on the writer's
    thread."""
    self.frames.put(None)
    if self.started is None:
      self.error = 'nothing was shown'

  @property
  def writing(self, ) -> bool:
    """Whether the video is still being written."""
    return self.thread.is_alive()

  @property
  def pending(self, ) -> int:
    """How many frames wait to be written."""
    return self.frames.qsize()

  def _start(self, ) -> None:
    """Starts ffmpeg on frames the size of the first, and the writer."""
    width, height = self.size
    command = ['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pix_fmt', 'bgra', '-s', '%dx%d' % (width, height), '-r',
               str(self.fps), '-i', '-', '-vf',
               'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264',
               '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
               '-movflags', '+faststart', self.path]
    try:
      self.process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    except OSError as reason:
      self.error = 'ffmpeg could not start: %s' % reason
    self.thread.start()

  def _write(self, ) -> None:
    """Writes the frames queued, each as often as asked, till told to
    stop; then closes the video and writes the log."""
    width, height = self.size
    while True:
      item = self.frames.get()
      if item is None:
        break
      if self.process is None or self.error is not None:
        continue
      image, repeats = item
      if (image.width(), image.height()) != (width, height):
        image = image.scaled(width, height)
      image = image.convertToFormat(QImage.Format.Format_RGB32)
      data = bytes(image.constBits())[:width * height * 4]
      try:
        for _ in range(repeats):
          self.process.stdin.write(data)
      except OSError as reason:
        self.error = 'ffmpeg stopped taking frames: %s' % reason
    if self.process is not None:
      try:
        self.process.stdin.close()
      except OSError:
        pass
      said = self.process.stderr.read().decode(errors='replace').strip()
      if self.process.wait() != 0 and self.error is None:
        self.error = 'ffmpeg failed: %s' % said[-300:]
    with open(self.path.rsplit('.', 1)[0] + '.json', 'w') as file:
      json.dump(self.log, file)

  @staticmethod
  def _stamp(image: QImage, number: int, passed: float) -> None:
    """Writes the frame's number in the video and its time in a corner
    of 'image'."""
    painter = QPainter(image)
    painter.setPen(QColor(255, 80, 80))
    painter.drawText(QPointF(8.0, 16.0), 'REC  frame %d  %.3f s'
                     % (number, passed))
    painter.end()
