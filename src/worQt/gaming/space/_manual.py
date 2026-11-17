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
SUBTITLE = 'MAGIC BOLTS AND THE GRAV-GUN'
LEAD = 'Read this before you leave the ground.'
ITEMS = (
  ('MAGIC BOLTS', 'The bolts with the violet glow are magic. Nothing '
   'pulls them loose: not your hands, not the gun, not the end of the '
   'world.'),
  ('THE GRAV-GUN', 'Officially the Zero Point Energy Field Manipulator, if '
   'you really want to. Point it at a magic bolt or at anything loose and '
   'hold the right button: a field pulls the two of you together, the '
   'harder the further apart. A bolt will not budge, so it pulls YOU. A '
   'mug comes to you. Let go early and the field is off. Once the gun is '
   'near the bolt, or the mug is in your hands, it holds on by itself: '
   'right click again to let go.'),
  ('THE PULSE', 'Left click sends a pulse the other way, ten times as '
   'hard: you push off the bolt, the mug flies. The pulse ends the '
   'field and the hold.'),
  ('NEVER UNDER GRAVITY', 'Never use the gun where things fall: on Terra, '
   'on the pad, or with the engine burning. A pulse throws you, and then '
   'you fall. Falls past 1.5 Asger heights hurt. Twelve Asger heights, '
   'and it is over.'),
  ('IN SPACE', 'Weightless, the gun is how you get about: the field to '
   'go, a pulse to stop or to push off. From far off you come in fast: '
   'let go of the field on the way and pulse to brake.'))
SMALL_PRINT = 'Made in China. Not for children under 3.'
