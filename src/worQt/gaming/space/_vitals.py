"""
Vitals are Asger's health and hunger (user, 2026-11-17: "AsgerJon should
have a health bar and hunger bar like in minecraft. To eat, Asger goes
to the kitchen where an endless supply of RCIR from the French armed
forces. 4g would kill Asger in 20 seconds. 3g would kill Asger in 80
seconds. 2g will not kill Asger but will increase his need of food by
4x"), Qt-free, at real time (the cabin's: a warp of the flight's time is
not his).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._aerospike import G0
from ._cockpit import SCALE

#  His health and his food when full, points (ten hearts, ten drumsticks,
#  each two points: as a game's bars).
HEALTH = 20.0
FOOD = 20.0
#  Within this of his whole food he is full: he eats no more, and time
#  may warp (user, 2026-11-17: "fully saturated").
FULL_WITHIN = 0.5
#  Pulled harder than 'CRUSHING_FROM' g it hurts him, 'CRUSHING' of his
#  health a second for each g past it squared: three g kills him in 80
#  s, four g in 20 s, two g never.
CRUSHING_FROM = 2.0
CRUSHING = HEALTH / 80.0
#  A full stomach lasts 'FOOD_LASTS' s pulled one g or less; pulled
#  harder he grows hungrier, 'HUNGRIER' times at two g and past it (the
#  rate kept there: three g kills him in its 80 s, not starved first).
FOOD_LASTS = 1200.0
HUNGRIER = 4.0
#  Fed at least 'FED' points (and not hurting) he mends 'MENDING' points
#  a second; with nothing left to eat he starves 'STARVING' points a
#  second.
FED = 18.0
MENDING = 0.25
STARVING = 0.25
#  A ration (an RCIR's menu) feeds him 'RATION' points; eating one takes
#  'EATING' s.
RATION = 10.0
EATING = 2.0
#  Pork scratchings under the dashboard, always there (user, 2026-11-17:
#  "Asger needs to be able to grab some snacks whilst sitting in his
#  chair so as to not starve himself"): a handful feeds 'SNACK' points
#  in 'SNACKING' s; at 'PECKISH' points or less (three drumsticks) he is
#  reminded of them, again once he has been fed past 'REMINDED'.
SNACK = 4.0
SNACKING = 1.0
#  A commando bar from his inventory (user, 2026-11-17: "put some
#  commandobars in Asgers inventory") feeds 'BAR' points in 'MUNCHING'
#  s (as long as Minecraft's eating).
BAR = 6.0
MUNCHING = 1.6
PECKISH = 6.0
REMINDED = 8.0
#  How fast the red of being hurt fades (most of the way in), s.
HURT_FADES = 0.4
#  Falling (user, 2026-11-17: "Up to 1.5 Asger heights, Asger takes no
#  fall dmg. Falling 12 Asger heights and it's over for old Asger"): his
#  height, m (his skin's 32 pixels); a meeting as fast as a fall from
#  'SAFE_FALL' of his heights (at one g) hurts him not, as fast as from
#  'DEADLY_FALL' takes all his health, between as the height (any pull:
#  a wall met weightless hurts as the floor does).
TALL = 32.0 * SCALE
SAFE_FALL = 1.5
DEADLY_FALL = 12.0


class Vitals:
  """
  Vitals keep Asger alive: his 'health' and 'food' (points, 'HEALTH' and
  'FOOD' at most), what killed him ('cause', None while he lives),
  how red he sees from being hurt ('hurt', nought to one: red each
  point lost, fading), how much of
  a ration he has still to eat ('eating', s) and the counts the sound
  plays one of as they grow ('hurts': each point lost to harm; 'meals':
  each ration begun). 'lived' lives 'seconds' pulled 'gees'; 'fell'
  meets something; 'ate' begins a ration; 'revived' wakes him whole.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('health', 'food', 'cause', 'hurt', 'eating', 'bite', 'took',
           'reminded')

  #  Public Variables
  health: float
  food: float
  cause: str | None
  hurt: float
  eating: float
  hurts: int
  meals: int
  snacks: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.hurts = self.meals = self.snacks = 0
    self.bite, self.took, self.reminded = RATION, EATING, False
    self.revived()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def lived(self, seconds: float, gees: float, seated: bool = False,
            warped: bool = False) -> None:
    """The 'lived' method lives 'seconds' s (real time) pulled 'gees' g:
    hungrier the harder he is pulled (not while time is 'warped': user,
    2026-11-17, "During warp, Asger does not lose hunger"), hurt past two
    g (not 'seated': his chair keeps him from the pull's harm, user,
    2026-11-17: "When Asger sits in the seat, he is protected from damage
    taken by g forces") or starving, mending when fed and unhurt, a
    ration eaten on; dead at no health (what killed him in 'cause')."""
    if self.cause is not None or seconds <= 0.0:
      return
    hunger = 0.0 if warped else FOOD / FOOD_LASTS * HUNGRIER ** min(
      1.0, max(0.0, gees - 1.0))
    self.food = max(0.0, self.food - hunger * seconds)
    if self.eating > 0.0:
      self.eating -= seconds
      if self.eating <= 0.0:
        self.eating, self.food = 0.0, min(FOOD, self.food + self.bite)
    crushing = 0.0 if seated else CRUSHING * max(
      0.0, gees - CRUSHING_FROM) ** 2
    starving = STARVING if self.food <= 0.0 else 0.0
    harm = (crushing + starving) * seconds
    mend = MENDING * seconds if (self.food >= FED and not harm) else 0.0
    before = self.health
    self.health = min(HEALTH, max(0.0, self.health - harm + mend))
    lost = max(0, math.ceil(before) - math.ceil(self.health))
    self.hurts += lost
    self.hurt = 1.0 if lost else self.hurt * 0.05 ** (seconds / HURT_FADES)
    if self.health <= 0.0:
      self.cause = ('crushed by %.1f g' % gees if crushing >= starving
                    else 'starved')

  def fell(self, speed: float) -> None:
    """The 'fell' method meets something at 'speed' m/s: hurt as by a
    fall from as high (at one g), past 'SAFE_FALL' of his heights, all
    his health at 'DEADLY_FALL'; dead, what killed him in 'cause'."""
    if self.cause is not None:
      return
    high = speed * speed / (2.0 * G0)
    past = high / TALL - SAFE_FALL
    if past <= 0.0:
      return
    before = self.health
    self.health = max(0.0, self.health - HEALTH * past / (
      DEADLY_FALL - SAFE_FALL))
    self.hurts += max(1, math.ceil(before) - math.ceil(self.health))
    self.hurt = 1.0
    if self.health <= 0.0:
      self.cause = 'hit something at %.0f m/s' % speed

  def ate(self, ) -> str:
    """The 'ate' method begins a ration if he may eat one; returns why
    not ('' he eats): dead, already eating, full."""
    if self.cause is not None:
      return 'Asger is dead'
    if self.eating > 0.0:
      return 'Asger is eating'
    if self.food >= FOOD - FULL_WITHIN:
      return 'Asger is full'
    self.eating, self.meals = EATING, self.meals + 1
    self.bite, self.took = RATION, EATING
    return ''

  def snacked(self, ) -> str:
    """The 'snacked' method begins a handful of pork scratchings if he
    may eat; returns why not ('' he eats): dead, already eating,
    full."""
    if self.cause is not None:
      return 'Asger is dead'
    if self.eating > 0.0:
      return 'Asger is eating'
    if self.food >= FOOD - FULL_WITHIN:
      return 'Asger is full'
    self.eating, self.snacks = SNACKING, self.snacks + 1
    self.bite, self.took = SNACK, SNACKING
    return ''

  def munched(self, ) -> str:
    """The 'munched' method begins a commando bar if he may eat; returns
    why not ('' he eats): dead, already eating, full."""
    if self.cause is not None:
      return 'Asger is dead'
    if self.eating > 0.0:
      return 'Asger is eating'
    if self.food >= FOOD - FULL_WITHIN:
      return 'Asger is full'
    self.eating, self.snacks = MUNCHING, self.snacks + 1
    self.bite, self.took = BAR, MUNCHING
    return ''

  def reminder(self, ) -> bool:
    """The 'reminder' method says whether he is to be reminded of the
    snacks now: once each time his food falls to 'PECKISH'."""
    if self.food > REMINDED:
      self.reminded = False
    if self.food <= PECKISH and not self.reminded and self.cause is None:
      self.reminded = True
      return True
    return False

  @property
  def full(self, ) -> bool:
    """The 'full' property says whether he is fed full (user,
    2026-11-17: "Asger must be seated and fully saturated for warp to be
    permitted")."""
    return self.food >= FOOD - FULL_WITHIN

  @property
  def eaten(self, ) -> float:
    """The 'eaten' property is how much of what he eats he has eaten
    (nought to one; nought: nothing)."""
    return 1.0 - self.eating / self.took if self.eating > 0.0 else 0.0

  def revived(self, ) -> None:
    """The 'revived' method wakes him whole: full health and food, alive,
    nothing half eaten."""
    self.health, self.food, self.cause = HEALTH, FOOD, None
    self.hurt, self.eating = 0.0, 0.0
