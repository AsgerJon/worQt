"""
TestPhrasebook covers 'Phrasebook', the words the billiards speak (the
user: "Besides the English version of the game add a Danish language
option and if possible a Korean and French and whatever weird af
language they speak in Belgium"): every language holds every phrase
English has and no other, each with the same blanks, so no phrase is
ever missing or loses a fact; a phrase there is not, or a language
there is not, raises; in keglebillard the yellow is the marked white;
counting is the language's own; each language walks and aims by the
keys in W A S D's places on its keyboards, Z Q S D on the AZERTY ones of
France and Belgium, and says so; a system's locale picks its language;
the club board's 5 by 7 glyphs draw every letter the board's line may
say in the languages they draw, Korean drawn from a font instead; and
the referees and the matches call in every language, the articles and
paragraphs the same in each, every blank filled.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import re
from pathlib import Path

from worQt.gaming.billiards import ENGLISH, KegleMatch, KegleReferee
from worQt.gaming.billiards import KegleShot, Match, Motion, Phrasebook
from worQt.gaming.billiards import Referee, Rules, Streak, Touch
from worQt.gaming.billiards._phrases import PHRASES

from . import BilliardsTest
from .test_referee import OPENING, cushion, meets, shot

#  The phrases that may reach the club board's dot-matrix line: the
#  calls, how a match stands, the lag, the board's own.
BOARD = ('ball.', 'the.', 'join.', 'player', 'cushion.', 'cushions.',
         'count.', 'call.', 'foul.', 'lag.', 'kegle.', 'match.',
         'kmatch.', 'board.', 'status.', 'skip.', 'fling.')
QML = (Path(__file__).parents[3] / 'src' / 'worQt' / 'gaming' /
       'billiards' / 'gui' / 'ClubBoard.qml')


def blanks(phrase: str) -> list[str]:
  """The numbered blanks in 'phrase', each once, in order."""
  return sorted(set(re.findall(r'\{(\d+)\}', phrase)))


def glyphs() -> set[str]:
  """The characters the club board's 5 by 7 glyph table draws."""
  text = QML.read_text(encoding='utf-8')
  return set(re.findall(r'^\s*"(.)": \["', text, re.MULTILINE))


class TestPhrasebook(BilliardsTest):
  """Tests for 'Phrasebook'."""

  def test_complete(self) -> None:
    """Every language holds every English phrase and no other, with the
    same blanks, and names itself."""
    english = PHRASES['en']
    self.assertEqual(Phrasebook.languages(),
                     ('en', 'da', 'fr', 'ko', 'nl-BE'))
    for language in Phrasebook.languages():
      words = PHRASES[language]
      self.assertEqual(set(words), set(english), language)
      for key, phrase in english.items():
        self.assertEqual(blanks(words[key]), blanks(phrase),
                         (language, key))
      self.assertTrue(Phrasebook(language).name())

  def test_loud(self) -> None:
    """A language there is not, or a phrase there is not, raises."""
    with self.assertRaises(ValueError):
      Phrasebook('de')
    with self.assertRaises(KeyError):
      ENGLISH.said('no.such.phrase')

  def test_said(self) -> None:
    """A phrase is said with its facts put in, in the order the
    language puts them; lists are joined as the language joins them."""
    self.assertEqual(ENGLISH.said('call.point', 'one cushion',
                                  'the red', '2.2.05'),
                     'Point: one cushion before the red (2.2.05)')
    korean = Phrasebook('ko')
    self.assertEqual(korean.said('call.point', '쿠션 3개', '노란 공',
                                 '2.2.05'),
                     '득점: 노란 공 전에 쿠션 3개 (2.2.05)')
    self.assertEqual(ENGLISH.joined(['a', 'b', 'c']), 'a, b and c')
    self.assertEqual(Phrasebook('da').joined(['a', 'b']), 'a og b')
    self.assertEqual(korean.joined(['노란 공', '빨간 공']),
                     '노란 공과 빨간 공')

  def test_marked(self) -> None:
    """In keglebillard the yellow is the marked white; three-cushion's
    yellow stays yellow."""
    for language in Phrasebook.languages():
      book = Phrasebook(language)
      kegler = book.kegler()
      self.assertTrue(kegler.isMarked())
      self.assertEqual(kegler.theBall('yellow'), book.said('the.marked'))
      self.assertEqual(kegler.ball('yellow'), book.said('ball.marked'))
      self.assertEqual(kegler.carom().theBall('yellow'),
                       book.said('the.yellow'))
      self.assertEqual(kegler.theBall('red'), book.theBall('red'))

  def test_counted(self) -> None:
    """Counting is the language's own: one, or many; French counts
    nought as one."""
    self.assertEqual(ENGLISH.counted('count.cushion', 1), '1 cushion')
    self.assertEqual(ENGLISH.counted('count.cushion', 0), '0 cushions')
    french = Phrasebook('fr')
    self.assertEqual(french.counted('count.cushion', 0), '0 bande')
    self.assertEqual(french.counted('count.pin', 3), '3 quilles')

  def test_controls(self) -> None:
    """Each language walks and aims by the keys in W A S D's places on
    its keyboards: French and Flemish by Z Q S D (AZERTY, France and
    Belgium), the others W A S D; the phrases naming them name those."""
    for language in Phrasebook.languages():
      book = Phrasebook(language)
      azerty = language in ('fr', 'nl-BE')
      keys = ('Z', 'Q', 'S', 'D') if azerty else ('W', 'A', 'S', 'D')
      self.assertEqual(book.controls(), keys, language)
      for key in ('room.look', 'aim.stroke'):
        words = book.said(key, *book.controls())
        self.assertIn(' '.join(keys), words, (language, key))
        self.assertEqual(azerty, 'W A S D' not in words)

  def test_locale(self) -> None:
    """A system's locale picks its language: Danish, French (Belgian
    French too), Korean, Flemish for any Dutch, else English."""
    picks = {'da_DK': 'da', 'fr_FR': 'fr', 'fr_BE': 'fr', 'ko_KR': 'ko',
             'nl_BE': 'nl-BE', 'nl-NL': 'nl-BE', 'en_GB': 'en',
             'de_DE': 'en', 'C': 'en'}
    for locale, language in picks.items():
      self.assertEqual(Phrasebook.languageOf(locale), language, locale)

  def test_board_glyphs(self) -> None:
    """The club board's 5 by 7 glyphs draw every letter, in capitals,
    of every phrase that may reach its line, in every language drawn in
    them; Korean's line is drawn from a font ('dotted')."""
    drawn = glyphs()
    self.assertIn('Ø', drawn)
    for language in Phrasebook.languages():
      book = Phrasebook(language)
      if book.dotted():
        self.assertEqual(language, 'ko')
        continue
      for key, phrase in PHRASES[language].items():
        if not key.startswith(BOARD):
          continue
        missing = set(phrase.format(*'0' * 5).upper()) - drawn
        self.assertEqual(missing, set(), (language, key))

  def test_referee(self) -> None:
    """The referee calls a point, a miss, a foul and the lag in every
    language: the article the same, every blank filled, and in other
    languages than English other words."""
    point = (meets('white', 'red'), cushion('white', 'foot'),
             cushion('white', 'left'), cushion('white', 'head'),
             meets('white', 'yellow'))
    missed = (cushion('white', 'foot'),)
    after = OPENING
    lag = (cushion('white', 'foot'), cushion('white', 'head'),
           meets('yellow', 'red'))
    english = Referee()
    for language in Phrasebook.languages():
      referee = Referee(Rules(), Motion(), Phrasebook(language))
      for touches in (point, missed):
        call = referee.call(shot(touches, False))
        same = english.call(shot(touches, False))
        self.assertEqual(call[:3], same[:3], language)
        self.assertIn('(%s)' % call.article, call.words)
        self.assertNotIn('{', call.words)
        if language != 'en':
          self.assertNotEqual(call.words, same.words, language)
      winner, words = referee.lagCall(lag, after)
      self.assertEqual(winner, 'white', language)
      self.assertIn('(2.1.02)', words)
      self.assertNotIn('{', words)

  def test_kegler(self) -> None:
    """Keglebillard's referee calls in every language, the paragraph the
    same; its lag speaks of the marked white."""
    pins = KegleShot((), ((0, 'white'), (1, 'white')))
    foul = KegleShot((Touch('off', 'red', ''),), ())
    lag = (cushion('white', 'foot'), cushion('white', 'head'),
           meets('yellow', 'red'))
    for language in Phrasebook.languages():
      book = Phrasebook(language)
      referee = KegleReferee(KegleReferee().table, book)
      call = referee.call(pins, Streak())
      self.assertEqual((call.points, call.rule), (4, '3.4'))
      self.assertIn(book.counted('count.pin', 2), call.words)
      self.assertIn('(11)', referee.call(foul, Streak()).words)
      winner, words = referee.lagCall(lag, OPENING)
      self.assertEqual(winner, 'white')
      self.assertIn(book.said('the.marked'), words)

  def test_matches(self) -> None:
    """The matches say how they stand in every language, the players
    named as the language names them."""
    for language in Phrasebook.languages():
      book = Phrasebook(language)
      match = Match(Rules(), book.players()).begun()
      for step in (match, match.lagged('white'),
                   match.lagged('white').chosen(True)):
        words = step.said(book)
        self.assertNotIn('{', words)
      self.assertIn(book.players()[0],
                    match.lagged('white').chosen(True).said(book))
      kegle = KegleMatch(book.players()).begun()
      self.assertIn('400', kegle.said(book))
      self.assertEqual(kegle.named(('A', 'B')).names, ('A', 'B'))
