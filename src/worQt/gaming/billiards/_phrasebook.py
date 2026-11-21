"""
Phrasebook is the words the billiards speak, in one of the languages
they know: English, Danish, French, Korean and Flemish.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._phrases import CONTROLS, LANGUAGES, NAMES, PHRASES

#  In keglebillard the yellow ball is the marked white: these phrases
#  name it so ('Phrasebook.kegler').
_MARKED = {'ball.yellow': 'ball.marked', 'the.yellow': 'the.marked'}


class Phrasebook:
  """
  Phrasebook is the words the billiards speak in its 'language', one of
  'LANGUAGES' (the user: "Besides the English version of the game add a
  Danish language option and if possible a Korean and French and
  whatever weird af language they speak in Belgium"): 'said' words a
  phrase, its facts put in where its '{0}', '{1}' stand, so a language
  may order them as it likes. English is the master; every language
  holds every phrase, and a phrase it lacks raises. 'kegler' is the
  same book speaking of keglebillard's balls, the yellow the marked
  white. 'controls' are the four keys its players walk and aim with,
  W A S D, or Z Q S D on the French and Belgian keyboards; phrases
  naming them take them as facts. 'languageOf' picks the language for a
  system's locale.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  __slots__ = ('__book_language__', '__book_marked__')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, language: str = 'en', marked: bool = False) -> None:
    if language not in PHRASES:
      raise ValueError('the billiards speak %s, not %r' % (
        ', '.join(LANGUAGES), language))
    self.__book_language__ = language
    self.__book_marked__ = True if marked else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PYTHON API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, Phrasebook):
      return NotImplemented
    return (self.language(), self.isMarked()) == (other.language(),
                                                  other.isMarked())

  def __hash__(self, ) -> int:
    return hash((self.language(), self.isMarked()))

  def __repr__(self, ) -> str:
    return 'Phrasebook(%r, %r)' % (self.language(), self.isMarked())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def languages() -> tuple[str, ...]:
    """The 'languages' method returns the languages there are, English
    first."""
    return LANGUAGES

  @staticmethod
  def languageOf(locale: str) -> str:
    """The 'languageOf' method returns the language for a system's
    'locale', as 'da_DK' or 'fr-BE': Danish, French, Korean, Flemish for
    any Dutch, else English."""
    head = locale.replace('-', '_').split('_')[0].lower()
    return {'da': 'da', 'fr': 'fr', 'ko': 'ko', 'nl': 'nl-BE'}.get(head,
                                                                    'en')

  def language(self, ) -> str:
    """The 'language' method returns the language spoken, as
    'LANGUAGES' has it."""
    return self.__book_language__

  def name(self, ) -> str:
    """The 'name' method returns the language's own name for itself."""
    return NAMES[self.__book_language__]

  def isMarked(self, ) -> bool:
    """The 'isMarked' method tells whether the yellow ball is spoken of
    as the marked white, as in keglebillard."""
    return self.__book_marked__

  def kegler(self, ) -> Phrasebook:
    """The 'kegler' method returns this book speaking of keglebillard's
    balls: the yellow is the marked white."""
    return Phrasebook(self.__book_language__, True)

  def carom(self, ) -> Phrasebook:
    """The 'carom' method returns this book speaking of three-cushion's
    balls: white, yellow and red."""
    return Phrasebook(self.__book_language__, False)

  def has(self, key: str) -> bool:
    """The 'has' method tells whether there is a phrase 'key'."""
    return key in PHRASES[self.__book_language__]

  def said(self, key: str, *facts: object) -> str:
    """The 'said' method returns the phrase 'key' in the language, each
    of 'facts' put in where its number stands; a phrase there is not
    raises."""
    if self.__book_marked__:
      key = _MARKED.get(key, key)
    phrases = PHRASES[self.__book_language__]
    if key not in phrases:
      raise KeyError('no phrase %r in %s' % (key, self.name()))
    return phrases[key].format(*facts)

  def counted(self, stem: str, count: int) -> str:
    """The 'counted' method returns 'count' things, the phrase 'stem'
    one or many as the language counts: French counts nought as one."""
    one = count == 1 or (count == 0 and self.__book_language__ == 'fr')
    return self.said('%s.%s' % (stem, 'one' if one else 'many'), count)

  def ball(self, name: str) -> str:
    """The 'ball' method returns the ball 'name' named alone, as a
    sentence begins: 'White'."""
    return self.said('ball.%s' % name)

  def theBall(self, name: str) -> str:
    """The 'theBall' method returns the ball 'name' as a sentence names
    it: 'the white'."""
    return self.said('the.%s' % name)

  def cushion(self, name: str) -> str:
    """The 'cushion' method returns the cushion 'name', one of
    'CUSHIONS', as a sentence names it: 'the foot cushion'."""
    return self.said('cushion.%s' % name)

  def joined(self, words: tuple | list) -> str:
    """The 'joined' method returns 'words' as a list in a sentence: 'a,
    b and c'."""
    words = list(words)
    if len(words) < 2:
      return ''.join(words)
    head = self.said('join.comma').join(words[:-1])
    return '%s%s%s' % (head, self.said('join.and'), words[-1])

  def players(self, ) -> tuple[str, str]:
    """The 'players' method returns the two players' names before they
    are given any: 'Player 1', 'Player 2'."""
    return self.said('player', 1), self.said('player', 2)

  def controls(self, ) -> tuple[str, str, str, str]:
    """The 'controls' method returns the keys the language's players
    walk and aim with, as letters: forward, left, back, right; 'W', 'A',
    'S', 'D', or on the AZERTY keyboards of France and Belgium, in the
    same places, 'Z', 'Q', 'S', 'D'."""
    forward, left, back, right = CONTROLS[self.__book_language__]
    return forward, left, back, right

  def dotted(self, ) -> bool:
    """The 'dotted' method tells whether the club board's dot-matrix line
    is drawn from a font, the language's letters too many strokes for
    its own 5 by 7 glyphs: Korean."""
    return self.__book_language__ == 'ko'


ENGLISH = Phrasebook()
