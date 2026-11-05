"""
The 'worQt.ezword.gui' package provides the EZWord application: a page
to write on, a 'Vidget' from 'worQt.vidget' editing the way Vi does, in
a window whose File menu and ex commands save and open files of the
EZWord format. The text model in 'worQt.ezword' stays free of Qt; only
this package needs it.

Run it with:

  python -m worQt.ezword
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._page_widget import PageWidget
from ._ez_word_window import EZWordWindow
from ._ez_word_app import EZWordApp

__all__ = (
  'PageWidget',
  'EZWordWindow',
  'EZWordApp',
)
