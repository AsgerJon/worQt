"""
TapeDeck plays the cabin's tape on the reel-to-reel deck to Asger's
right (user, 2026-11-16: "Upon escaping the atmosphere a B&O styled
casette deck should begin play some celebratory sound file"; then "use
@previews/stereo reel to reel", "it should prolly be off to the right
of Asger. Then when it starts playing, have it make a bunch of clicky
sounds to get Asger's attention. just until the music starts", "The
tape clickies are only when the tape gets ready to play music to draw
your attention to it. The music should start only upon clearing the
atmosphere"; the tape: 'tmp/celebration.*', the user's own, kept out of
git): announced 'LEAD_IN' s before the vessel leaves the air (the
deck's solenoids, relays and motor clicking: the cabin's sound plays
them), the music from the tape's beginning as it leaves, once; played,
stopped and rewound by its keys.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from pathlib import Path

#  The tape: the repository's 'tmp' folder, a file named so.
TAPE_FOLDER = Path(__file__).resolve().parents[4] / 'tmp'
TAPE_NAME = 'celebration'
#  How fast the reels turn playing, rad/s (the take-up reel the faster
#  at first: it starts empty).
REEL_TURN = 2.0 * math.pi * 0.6
#  How long the deck clicks getting ready before the music, s (the
#  instruments announce it this long before the vessel is out of the
#  air; the cabin's sound's clicks last as long: '_cabinmixer').
LEAD_IN = 2.0


def tapeFile() -> Path | None:
  """Returns the tape's file ('tmp/celebration.*'), None if there is
  none."""
  if not TAPE_FOLDER.is_dir():
    return None
  for path in sorted(TAPE_FOLDER.iterdir()):
    if path.stem == TAPE_NAME and path.is_file():
      return path
  return None


class TapeDeck:
  """
  TapeDeck holds the deck: whether it plays ('playing'), whether it has
  been announced ('announced': clicking itself ready for the music) and
  how often ('announcements': the sound plays the clicks each time it
  grows), how much of the clicking is left ('leading', s), how often it
  has been rewound ('rewinds': the sound starts the tape from its
  beginning each time it grows), how long it has played since
  ('played', s), whether it has cheered the vessel out of the air yet
  ('cheered'), and its reels' turns ('reels', rad).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  playing: bool
  announced: bool
  announcements: int
  leading: float
  rewinds: int
  played: float
  cheered: bool
  reels: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.playing, self.announced, self.announcements = False, False, 0
    self.leading, self.rewinds, self.played = 0.0, 0, 0.0
    self.cheered, self.reels = False, (0.0, 0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def announce(self, ) -> bool:
    """The 'announce' method has the deck click itself ready for the
    music ('LEAD_IN' s), once, before it has cheered; returns whether
    it did."""
    if self.announced or self.cheered:
      return False
    self.announced, self.leading = True, LEAD_IN
    self.announcements += 1
    return True

  def play(self, ) -> None:
    """The 'play' method plays the tape on from where it stands."""
    self.playing = True

  def halt(self, ) -> None:
    """The 'halt' method stops the tape where it stands."""
    self.playing = False

  def eject(self, ) -> None:
    """The 'eject' method stops the tape and winds it back to its
    beginning."""
    self.playing, self.played = False, 0.0
    self.rewinds += 1

  def celebrated(self, ) -> bool:
    """The 'celebrated' method plays the tape from its beginning the
    first time it is asked (the vessel out of the air: the clicks, if
    still going, stop); returns whether it did."""
    if self.cheered:
      return False
    self.cheered, self.leading = True, 0.0
    self.eject()
    self.play()
    return True

  def acted(self, seconds: float) -> None:
    """The 'acted' method runs the deck 'seconds' on: the clicking's
    time, and while it plays the tape, its reels turning."""
    self.leading = max(0.0, self.leading - seconds)
    if not self.playing:
      return
    self.played += seconds
    take = REEL_TURN * (1.6 - 0.6 * min(1.0, self.played / 240.0))
    give = REEL_TURN * (0.8 + 0.4 * min(1.0, self.played / 240.0))
    self.reels = ((self.reels[0] - give * seconds) % (2.0 * math.pi),
                  (self.reels[1] - take * seconds) % (2.0 * math.pi))
