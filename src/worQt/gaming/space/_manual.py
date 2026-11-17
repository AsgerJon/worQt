"""
The warning manual on the placard by the door (user, 2026-11-17: "Read
warning manual by going to warning panel. Here Asger has the bolts and
temu-grav-gun explained to him. He's warned to never use it whilst nder
gravitational effect like on earth"; "it should be possible, but
annoying to read it diegetically, but with E you get a better view at
it. Like in RDR2"): its title, its lines (each a heading and what it
says), its small print. Qt-free: '_cabinpictures.manualPainted' paints
it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

TITLE = 'WARNING'
SUBTITLE = 'MAGIC BOLTS AND THE TEMU GRAVITY GUN'
LEAD = 'Read this before you leave the ground.'
ITEMS = (
  ('MAGIC BOLTS', 'The bolts with the violet glow are magic. Nothing '
   'pulls them loose: not your hands, not the gun, not the end of the '
   'world.'),
  ('THE GUN', 'Point the Temu gravity gun at a magic bolt and hold the '
   'right button. The gun tries to pick the bolt up. The bolt will not '
   'budge, so the gun pulls YOU to the bolt instead. Let go on the way and '
   'you drift on; reach the bolt and the gun holds you there.'),
  ('LETTING GO', 'Space pushes you off the bolt you are held at. Right '
   'click lets go.'),
  ('NEVER UNDER GRAVITY', 'Never use the gun where things fall: on Terra, '
   'on the pad, or with the engine burning. It holds you at the bolt '
   'until you let go, and then you fall. Falls past 1.5 Asger heights '
   'hurt. Twelve Asger heights, and it is over.'),
  ('IN SPACE', 'Weightless, the gun is how you get about: bolt to bolt, in '
   'the rocket and aboard Terra Prime.'))
SMALL_PRINT = 'Made in China. Not for children under 3.'
