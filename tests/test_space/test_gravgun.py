"""
TestGravGun covers the Grav-Gun (user, 2026-11-17: "the official name is
'zero point energy field manipulator, if you really want to'. But
'gravgun' is the code name in the code and Grav-Gun is the public name.
All it does is that when aimed at an interactable object, right click
starts a force acting between the gun and its holder and the
interactable object that increases in magnitude with distance. Left
click sends a pulse of a greater force opposite of the right click"):
the field's pull on its holder toward its target, 'PULL' a metre apart
(its target feels it the other way); off, nothing; the pulse 'PUNT'
times as hard the other way for 'PULSE' s, ending the field; it takes
bolts and loose things alone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._gravgun import PULL, PULSE, PUNT, GravGun
from worQt.gaming.space._inventory import ITEMS

from . import SpaceTest


class TestGravGun(SpaceTest):
  """Tests for the Grav-Gun."""

  def test_named(self) -> None:
    """In the inventory it is the Grav-Gun ('gravgun' in the code)."""
    self.assertEqual(ITEMS['gravgun'][0], 'Grav-Gun')

  def test_field(self) -> None:
    """Its field pulls its holder toward its target, harder the further
    apart (in proportion); off, it pulls nothing."""
    gun = GravGun()
    self.assertEqual(gun.pushOf((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), 0.1),
                     (0.0, 0.0, 0.0))
    gun.gripped(('bolt', 2))
    near = gun.pushOf((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.1)
    far = gun.pushOf((1.0, 1.0, 1.0), (1.0, 5.0, 1.0), 0.1)
    self.assertClose(near, (PULL, 0.0, 0.0), 1e-12)
    self.assertClose(far, (0.0, 4.0 * PULL, 0.0), 1e-12)
    self.assertEqual(gun.acting, ('bolt', 2))
    gun.released()
    self.assertIsNone(gun.acting)

  def test_pulse(self) -> None:
    """A pulse pushes the other way, 'PUNT' times the pull, for 'PULSE'
    s of frames, then nothing; it ends the field and is counted."""
    gun = GravGun()
    gun.gripped(('loose', 0))
    gun.punted(('loose', 0))
    self.assertIsNone(gun.target)
    self.assertEqual(gun.pulses, 1)
    pushes, frames = [], 0
    while gun.acting is not None:
      pushes.append(gun.pushOf((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), 0.01))
      frames += 1
    self.assertEqual(frames, round(PULSE / 0.01))
    for push in pushes:
      self.assertClose(push, (-2.0 * PUNT * PULL, 0.0, 0.0), 1e-12)
    self.assertEqual(gun.pushOf((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), 0.01),
                     (0.0, 0.0, 0.0))

  def test_targets(self) -> None:
    """It takes a magic bolt or a loose thing by index, nothing else."""
    gun = GravGun()
    for bad in (('chair', 0), ('bolt', -1), ('loose', 1.5)):
      with self.assertRaises(ValueError):
        gun.gripped(bad)
