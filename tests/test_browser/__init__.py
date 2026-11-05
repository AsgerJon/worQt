"""
The 'tests.test_browser' package contains tests for the 'worQt.browser'
package: 'FileNode' in a plain 'BaseTest', and 'FileBrowser' in a
'WidgetTest', both on folders of their own in a temporary directory.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._browser_test import BrowserTest, BrowserWidgetTest

__all__ = (
  'BrowserTest',
  'BrowserWidgetTest',
)
