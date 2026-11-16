"""
TestTapeDeck covers the cabin's tape (user, 2026-11-16: "Upon escaping
the atmosphere a B&O styled casette deck should begin play some
celebratory sound file"; "The tape clickies are only when the tape gets
ready to play music to draw your attention to it. The music should start
only upon clearing the atmosphere"): announced, it clicks itself ready;
it cheers once, from the tape's beginning; it plays, stops and is
rewound by its keys; its reels turn only while the tape runs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._tapedeck import LEAD_IN, TAPE_NAME, TapeDeck
from worQt.gaming.space._tapedeck import tapeFile

from . import SpaceTest


class TestTapeDeck(SpaceTest):
  """Tests for 'TapeDeck'."""

  def test_cheers_once(self) -> None:
    """The first time out of the air it plays from the beginning; never
    again by itself."""
    deck = TapeDeck()
    self.assertFalse(deck.playing)
    self.assertTrue(deck.celebrated())
    self.assertTrue(deck.playing)
    self.assertEqual(deck.rewinds, 1)
    deck.halt()
    self.assertFalse(deck.celebrated())
    self.assertFalse(deck.playing)
    self.assertEqual(deck.rewinds, 1)

  def test_keys(self) -> None:
    """Play runs the tape on from where it stands, stop holds it there,
    eject stops it and winds it back."""
    deck = TapeDeck()
    deck.play()
    deck.acted(3.0)
    deck.halt()
    deck.acted(3.0)
    self.assertAlmostEqual(deck.played, 3.0)
    deck.play()
    deck.acted(1.0)
    self.assertAlmostEqual(deck.played, 4.0)
    deck.eject()
    self.assertFalse(deck.playing)
    self.assertEqual((deck.played, deck.rewinds), (0.0, 1))

  def test_reels(self) -> None:
    """The reels turn while it plays (the take-up reel the faster at
    first), and stand still stopped."""
    deck = TapeDeck()
    deck.acted(1.0)
    self.assertEqual(deck.reels, (0.0, 0.0))
    deck.play()
    deck.acted(0.1)
    give, take = (2.0 * math.pi - r for r in deck.reels)
    self.assertGreater(take, give)
    self.assertGreater(give, 0.0)
    for _ in range(1000):
      deck.acted(0.37)
    for reel in deck.reels:
      self.assertGreaterEqual(reel, 0.0)
      self.assertLess(reel, 2.0 * math.pi)
    deck.halt()
    still = deck.reels
    deck.acted(1.0)
    self.assertEqual(deck.reels, still)

  def test_announced(self) -> None:
    """Announced, it clicks itself ready for 'LEAD_IN' s, once, the tape
    still; cheered, the music starts at once from the beginning (the
    clicks stop); announced after that, nothing."""
    deck = TapeDeck()
    self.assertTrue(deck.announce())
    self.assertFalse(deck.announce())
    self.assertEqual((deck.announcements, deck.leading), (1, LEAD_IN))
    deck.acted(0.5)
    self.assertFalse(deck.playing)
    self.assertEqual(deck.reels, (0.0, 0.0))
    self.assertAlmostEqual(deck.leading, LEAD_IN - 0.5)
    self.assertTrue(deck.celebrated())
    self.assertTrue(deck.playing)
    self.assertEqual((deck.leading, deck.played), (0.0, 0.0))
    fresh = TapeDeck()
    fresh.celebrated()
    self.assertFalse(fresh.announce())

  def test_tape(self) -> None:
    """The tape, if the user has put one in 'tmp', is named so."""
    path = tapeFile()
    if path is not None:
      self.assertEqual(path.stem, TAPE_NAME)
      self.assertTrue(path.is_file())
