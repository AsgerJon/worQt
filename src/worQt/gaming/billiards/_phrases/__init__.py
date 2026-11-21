"""
The billiards' phrases, a catalog for each language they speak, English
the master: 'PHRASES' each language's phrases by key, 'NAMES' each
language's own name for itself, 'CONTROLS' the keys its players walk
and aim with, 'LANGUAGES' them all, English first.
'Phrasebook' speaks them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from .english import WORDS as ENGLISH
from .danish import WORDS as DANISH
from .french import WORDS as FRENCH
from .korean import WORDS as KOREAN
from .flemish import WORDS as FLEMISH

PHRASES = {'en': ENGLISH, 'da': DANISH, 'fr': FRENCH, 'ko': KOREAN,
           'nl-BE': FLEMISH}
#  The four keys a player of each language walks and aims with, as the
#  keyboards sold there have them in W A S D's places: forward, left,
#  back, right. French and Belgian keyboards are AZERTY, Z Q S D (the
#  user: the keys change with the language, and the words say so).
CONTROLS = {'en': 'WASD', 'da': 'WASD', 'fr': 'ZQSD', 'ko': 'WASD',
            'nl-BE': 'ZQSD'}
NAMES = {'en': 'English', 'da': 'Dansk', 'fr': 'Français', 'ko': '한국어',
         'nl-BE': 'Vlaams'}
LANGUAGES = tuple(PHRASES)
