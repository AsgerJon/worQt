"""
Char enumerates 'English' language characters.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import Kee, KeeNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Optional


class Char(KeeNum):
  """
  A Char is a single character, which is a string of length one that
  represents a single unit of text. Characters can be letters, digits,
  punctuation marks, or other symbols, and they are the basic building
  blocks of words and sentences.
  """

  A: Kee[str] = Kee[str]('A')
  B: Kee[str] = Kee[str]('B')
  C: Kee[str] = Kee[str]('C')
  D: Kee[str] = Kee[str]('D')
  E: Kee[str] = Kee[str]('E')
  F: Kee[str] = Kee[str]('F')
  G: Kee[str] = Kee[str]('G')
  H: Kee[str] = Kee[str]('H')
  I: Kee[str] = Kee[str]('I')
  J: Kee[str] = Kee[str]('J')
  K: Kee[str] = Kee[str]('K')
  L: Kee[str] = Kee[str]('L')
  M: Kee[str] = Kee[str]('M')
  N: Kee[str] = Kee[str]('N')
  O: Kee[str] = Kee[str]('O')
  P: Kee[str] = Kee[str]('P')
  Q: Kee[str] = Kee[str]('Q')
  R: Kee[str] = Kee[str]('R')
  S: Kee[str] = Kee[str]('S')
  T: Kee[str] = Kee[str]('T')
  U: Kee[str] = Kee[str]('U')
  V: Kee[str] = Kee[str]('V')
  W: Kee[str] = Kee[str]('W')
  X: Kee[str] = Kee[str]('X')
  Y: Kee[str] = Kee[str]('Y')
  Z: Kee[str] = Kee[str]('Z')
