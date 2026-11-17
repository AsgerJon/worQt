"""
Teleprinter types the flight on paper in the cabin (user, 2026-11-16:
"Instead of a terminal, which real Asger looks at all day, let's have a
teleprinter"): line by line, a character at a time at a teletype's ten
a second, capitals only, a bell before what matters, the carriage
returning between lines, the paper rolling up.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  The font it types in (user, 2026-11-16: "It should use a modern font
#  like nerd monospace to be cheeky"): the Nerd Font build of JetBrains
#  Mono, its icons in the log's lines ('ICONS').
FONT = 'JetBrainsMono Nerd Font Mono'
#  Nerd Font icons (Font Awesome's, at their own code points): a rocket,
#  a flame, a stop, a globe, a chequered flag, a clock, a cog.
ICONS = {'rocket': '\uf135', 'flame': '\uf06d', 'stop': '\uf04d',
         'globe': '\uf0ac', 'flag': '\uf11e', 'clock': '\uf017',
         'cog': '\uf013', 'down': '\uf063'}
#  Characters a second (a teletype's); characters a line (user,
#  2026-11-17: "Smaller font on the teleprint. also make it wider. It
#  should fit 77 characters"), at a Teletype's pitch made 'LARGER' (a
#  Teletype's ten characters and six lines an inch on its 8.5 inch paper:
#  "the teleprinter should be larger", the dashboard's middle given to
#  it): 'PITCH', 'LINE', m; lines kept (as many as the paper shows above
#  the line typed); how long the carriage takes to return, s.
RATE = 10.0
WIDTH = 77
LARGER = 1.6
PITCH = LARGER * 0.0254 / 10.0
LINE = LARGER * 0.0254 / 6.0
KEPT = 24
RETURN = 0.25


class Teleprinter:
  """
  Teleprinter holds what it has printed ('printed', the last 'KEPT'
  lines), the line it is typing ('typing', None: none) and how much of
  it ('done', characters), and what it is still to type ('queue', each
  a line and whether its bell rings first). As it goes it counts the
  characters it has struck ('typed'), its bells ('bells') and its
  carriage returns ('returns'): the cabin's sound plays one of each as
  they grow.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  printed: list
  typing: str | None
  done: float
  queue: list
  typed: int
  bells: int
  returns: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.printed, self.typing, self.done, self.queue = [], None, 0.0, []
    self.typed, self.bells, self.returns = 0, 0, 0
    self._resting = 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def busy(self, ) -> bool:
    """The 'busy' property says whether it is typing or has lines to
    type."""
    return self.typing is not None or bool(self.queue)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def said(self, line: str, bell: bool = False) -> None:
    """The 'said' method gives it 'line' to type, in capitals, its bell
    rung first if 'bell'; past 'WIDTH' it wraps at a space (a word
    longer than a line cut)."""
    rows, row = [], ''
    for word in str(line).upper().split():
      word = word[:WIDTH]
      if row and len(row) + 1 + len(word) > WIDTH:
        rows.append(row)
        row = word
      else:
        row = word if not row else row + ' ' + word
    rows.append(row)
    for k, row in enumerate(rows):
      self.queue.append((row, bool(bell) and k == 0))

  def acted(self, seconds: float) -> None:
    """The 'acted' method types 'seconds' on: 'RATE' characters a second,
    the carriage returning 'RETURN' s between lines."""
    left = seconds
    while left > 0.0:
      if self._resting > 0.0:
        rest = min(self._resting, left)
        self._resting -= rest
        left -= rest
        continue
      if self.typing is None:
        if not self.queue:
          return
        self.typing, bell = self.queue.pop(0)
        self.done = 0.0
        self.bells += 1 if bell else 0
      can = (len(self.typing) - self.done) / RATE
      used = min(can, left)
      struck = int(self.done + used * RATE + 1e-9) - int(self.done)
      self.done += used * RATE
      self.typed += struck
      left -= used
      if self.done >= len(self.typing) - 1e-9:
        self.printed = (self.printed + [self.typing])[-KEPT:]
        self.typing, self.done = None, 0.0
        self.returns += 1
        self._resting = RETURN

  def paper(self, ) -> tuple:
    """The 'paper' method returns what the paper shows: the lines printed
    (the last 'KEPT'), the part of the line being typed, and the
    carriage's column."""
    part = '' if self.typing is None else self.typing[:int(self.done)]
    return list(self.printed), part, len(part)
