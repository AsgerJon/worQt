"""
Speaker plays the sandbox's sound ('Mixer') in a process of its own,
streamed to the default speaker as it is made: away from the window (a
sound system once hung a window for good when played in its process),
the window writing what is going on into memory the two share and
never waiting on the sound.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import importlib
import multiprocessing
import sys
import time
from typing import TYPE_CHECKING

from ._mixer import TOLD, VOLUME

#  The sandbox's own mixer, as 'Speaker' is told which to play: its
#  module and class, 'module:Class'.
SANDBOX_MIXER = 'worQt.gaming.sandbox._mixer:Mixer'

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from multiprocessing.connection import Connection

#  Samples a second; how much sound is kept queued for the speaker, s
#  (what the sound lags behind the world), and how often it is topped
#  up, s; the channels (the same on both: in the middle).
RATE, AHEAD, EVERY, CHANNELS = 44100, 0.08, 0.01, 2
#  The speaker's errors that are none (an underrun: its queue run dry a
#  moment, fed on).
FINE = ('NoError', 'UnderrunError')


def mixerOf(source: str) -> type:
  """Returns the mixer class 'source' names ('module:Class'): found by
  its module's import, never made up from words."""
  module, name = source.split(':')
  return getattr(importlib.import_module(module), name)


def _played(connection: Connection, shared: object, source: str,
            count: int) -> None:
  """Plays the mixer 'source' names ('module:Class') as 'shared' tells
  it ('count' numbers) on the default speaker, in stereo, 'AHEAD' s
  queued; says ('ready', seconds) once playing or ('trouble', words).
  None over 'connection', or the asker gone, ends it."""
  from PySide6.QtCore import QLoggingCategory, QTimer
  from PySide6.QtGui import QGuiApplication
  from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices

  import numpy

  began = time.perf_counter()
  QLoggingCategory.setFilterRules('qt.multimedia.ffmpeg.info=false\n'
                                  'qt.multimedia.ffmpeg.debug=false')
  app = QGuiApplication(['worQt-sandbox-sound', '-platform', 'offscreen'])
  device = QMediaDevices.defaultAudioOutput()
  form = QAudioFormat()
  form.setSampleRate(RATE)
  form.setChannelCount(CHANNELS)
  form.setSampleFormat(QAudioFormat.SampleFormat.Int16)
  if device.isNull() or not device.isFormatSupported(form):
    try:
      connection.send(('trouble', 'no speaker found' if device.isNull()
                       else 'the speaker takes no 16-bit stereo at %d '
                       'Hz' % RATE))
    except (OSError, BrokenPipeError):
      pass
    sys.exit(0)
  mixer = mixerOf(source)(RATE)
  sink = QAudioSink(device, form)
  frame = 2 * CHANNELS
  sink.setBufferSize(2 * frame * int(RATE * AHEAD))
  speaker = sink.start()
  queue = frame * int(RATE * AHEAD)
  told = [False]

  def fed() -> None:
    """Writes as much sound as the speaker's queue lacks."""
    lacking = (queue - (sink.bufferSize() - sink.bytesFree())) // frame
    if lacking >= 64:
      sound = mixer.samples([shared[k] for k in range(count)], lacking)
      pcm = (numpy.clip(sound, -1.0, 1.0) * 32767.0).astype(numpy.int16)
      speaker.write(numpy.repeat(pcm, CHANNELS).tobytes())

  def heard() -> None:
    """Tops the speaker's queue up; says it is playing once."""
    try:
      if connection.poll() and connection.recv() is None:
        app.quit()
        return
      error = sink.error()
      if error.name not in FINE:
        if not told[0]:
          told[0] = True
          connection.send(('trouble', 'the speaker failed: %s'
                           % error.name))
        return
      fed()
      if not told[0]:
        told[0] = True
        connection.send(('ready', time.perf_counter() - began))
    except (EOFError, OSError, BrokenPipeError):
      app.quit()

  fed()
  timer = QTimer()
  timer.timeout.connect(heard)
  timer.start(int(1000 * EVERY))
  app.exec()
  sink.stop()
  sys.exit(0)


class Speaker:
  """
  Speaker plays a mixer's sound in a process of its own: the sandbox's
  ('SANDBOX_MIXER') or another ('source': 'module:Class', its 'samples'
  told 'count' numbers: the space's cabin). 'start' spawns it, 'heard'
  tells it what is going on, 'close' ends it. 'trouble' says why it is
  silent (None: playing, or starting).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  trouble: str

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, source: str = SANDBOX_MIXER,
               count: int = TOLD) -> None:
    self.source, self.count = source, int(count)
    self.trouble, self._shared, self._pipe, self._process = (
      None, None, None, None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def start(self, ) -> None:
    """The 'start' method spawns the sound's process (nothing of the
    window's goes with it)."""
    if self._process is not None:
      return
    context = multiprocessing.get_context('spawn')
    #  'lock' is keyword-only in multiprocessing: no way to pass it by
    #  place (the engine's sound does the same).
    self._shared = context.Array('d', self.count, lock=False)
    mine, theirs = context.Pipe()
    self._process = context.Process(None, _played, 'worQt-sandbox-sound',
                                    (theirs, self._shared, self.source,
                                     self.count))
    self._process.daemon = True
    self._process.start()
    theirs.close()
    self._pipe = mine

  def heard(self, told: tuple) -> None:
    """The 'heard' method tells the sound what is going on ('TOLD'
    numbers), and reads what it has said."""
    if self._shared is None:
      return
    for k, value in enumerate(told):
      self._shared[k] = float(value)
    try:
      while self._pipe.poll():
        said = self._pipe.recv()
        if said[0] == 'trouble':
          self.trouble = said[1]
    except (EOFError, OSError, BrokenPipeError):
      self.trouble = self.trouble or 'the sound stopped'

  def close(self, ) -> None:
    """The 'close' method ends the sound's process."""
    if self._process is None:
      return
    try:
      self._pipe.send(None)
    except (OSError, BrokenPipeError):
      pass
    self._process.join(1.0)
    if self._process.is_alive():
      self._process.terminate()
    self._process, self._shared = None, None
