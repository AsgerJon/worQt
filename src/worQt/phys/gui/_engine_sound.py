"""
EngineSound plays the car's engine ('EngineVoice': its revolutions and
load as they go) in a process of its own, streamed to the speaker as it
is made (user, 2026-11-13: "sound. engine. sound."): a recording of
an engine looped and pitched with the revolutions ('RecordedVoice'),
when one is given and can be read, else the engine made from what it
does ('EngineVoice'). As the coin
pusher's sounds, it is played away from the window: the sound system on
the user's machine once hung a window for good when played in its
process. The window writes what the engine is doing into memory the two
share (it never waits on the sound); the process reads it, makes the
next few milliseconds of sound and keeps the speaker's queue topped up
('AHEAD': what lags behind the engine).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import multiprocessing
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from multiprocessing.connection import Connection

#  Samples a second; how much sound is kept queued for the speaker, s,
#  and how often it is topped up, s; the channels (user, 2026-11-13:
#  "only in left side. let's make it stereo": one channel, the sound
#  system put it on the left alone; the same on both now, in the
#  middle).
RATE, AHEAD, EVERY, CHANNELS = 44100, 0.1, 0.01, 2
#  The speaker's errors that are none: told by name (the sink's are
#  'QtAudio.Error', not the older 'QAudio.Error', which never equals
#  them: 'the speaker failed: NoError', the user's window, 2026-11-13).
FINE = ('NoError', 'UnderrunError')
#  What 'start' is given to play the engine as AngeTheGreat's Engine
#  Simulator hears one ('_enginesim.EngineSimVoice': its V12), not a
#  recording's path.
ENGINE_SIM = 'engine-sim'


def _played(connection: Connection, shared: object,
            recording: str | None) -> None:
  """Plays the engine as 'shared' says (revolutions a minute, load,
  volume), the 'recording' at that path looped and pitched
  ('RecordedVoice'; none, or unreadable: an 'EngineVoice'), written to
  the default speaker, in stereo ('CHANNELS', alike), 'AHEAD' s
  queued; says which ('voice', words),
  ('ready', seconds) once playing, or ('trouble', words). None over
  'connection', or the asker gone, ends it."""
  from PySide6.QtCore import QLoggingCategory, QTimer
  from PySide6.QtGui import QGuiApplication
  from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices

  import numpy

  from .._voice import EngineVoice, RecordedVoice, pcm, recordingOf

  began = time.perf_counter()
  QLoggingCategory.setFilterRules('qt.multimedia.ffmpeg.info=false\n'
                                  'qt.multimedia.ffmpeg.debug=false')
  app = QGuiApplication(['worQt-engine', '-platform', 'offscreen'])
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
  if recording == ENGINE_SIM:
    from .._enginesim import EngineSimVoice
    voice = EngineSimVoice(RATE)
    voice.samples(0.0, 0.0, 64)
    said = 'the V12 as AngeTheGreat\'s Engine Simulator hears it'
  else:
    sound = None if recording is None else recordingOf(recording, RATE)
    voice = (EngineVoice(RATE, 0) if sound is None
             else RecordedVoice(sound, RATE, RATE))
    said = ('the engine made' if sound is None
            else 'the recording %s' % recording)
  try:
    connection.send(('voice', said))
  except (OSError, BrokenPipeError):
    sys.exit(0)
  sink = QAudioSink(device, form)
  frame = 2 * CHANNELS
  sink.setBufferSize(2 * frame * int(RATE * AHEAD))
  speaker = sink.start()
  queue = frame * int(RATE * AHEAD)
  told = [False]

  def fed() -> None:
    """Writes as much of the engine as the speaker's queue lacks."""
    queued = sink.bufferSize() - sink.bytesFree()
    lacking = (queue - queued) // frame
    if lacking >= 64:
      rpm, load, volume = shared[0], shared[1], shared[2]
      sound = volume * voice.samples(rpm, load, lacking)
      speaker.write(pcm(numpy.repeat(sound, CHANNELS)))

  def heard() -> None:
    """Tops the speaker's queue up with the engine as it is now. An
    underrun (the queue run dry a moment: at the start, or a hitch) is
    no failure: it is fed on (stopping at the first, it fell silent for
    good, 2026-11-13)."""
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


class EngineSound:
  """
  EngineSound plays the engine in a process of its own: 'start' spawns
  it (playing the recording at a path given, if it can be read), 'heard'
  tells it what the engine does now (revolutions a minute,
  load, volume: written to memory both share, never waiting) and reads
  what it said ('ready', after 'readyAfter' s, or 'trouble'; which
  'voice' it plays, printed); 'running' tells whether it is there;
  'close' ends it.
  """

  def __init__(self, ) -> None:
    self._process, self._pipe, self._shared = None, None, None
    self.readyAfter, self.trouble, self.voice = None, None, None

  @property
  def running(self, ) -> bool:
    """Whether the process is there."""
    return self._process is not None and self._process.is_alive()

  @property
  def ready(self, ) -> bool:
    """Whether it plays."""
    return self.readyAfter is not None

  def start(self, recording: str = None) -> None:
    """The 'start' method spawns the process (nothing of the window's
    carried over), the engine silent, to play the 'recording' at that
    path (none: the engine made)."""
    if self.running:
      return
    self.close()
    context = multiprocessing.get_context('spawn')
    shared = context.Array('d', 3, lock=False)
    mine, theirs = context.Pipe()
    process = context.Process(None, _played, 'worQt-engine',
                              (theirs, shared, recording))
    process.daemon = True
    process.start()
    theirs.close()
    self._process, self._pipe, self._shared = process, mine, shared
    self.readyAfter, self.trouble, self.voice = None, None, None

  def heard(self, rpm: float, load: float, volume: float) -> None:
    """The 'heard' method tells the process the engine turns 'rpm'
    revolutions a minute at 'load' (0 to 1), to be played at 'volume'
    (0 to 1), and reads what it said; it never waits."""
    shared = self._shared
    if shared is not None:
      shared[0], shared[1], shared[2] = rpm, load, volume
    pipe = self._pipe
    if pipe is None:
      return
    try:
      while pipe.poll():
        kind, value = pipe.recv()
        if kind == 'ready':
          self.readyAfter = value
        elif kind == 'voice':
          self.voice = value
          print('engine sound: playing %s' % value, flush=True)
        else:
          self.trouble = value
    except (EOFError, OSError):
      self._pipe = None

  def close(self, ) -> None:
    """The 'close' method ends the process, if it is there."""
    pipe, process = self._pipe, self._process
    self._pipe = self._process = self._shared = None
    if pipe is not None:
      try:
        pipe.send(None)
      except (OSError, BrokenPipeError):
        pass
      pipe.close()
    if process is not None:
      process.join(1.0)
      if process.is_alive():
        process.terminate()
