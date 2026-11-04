"""
The 'tests.test_widgets' package contains tests for the 'worQt.widgets'
package. Each 'Run*' class subclasses 'worQt.qtest.WidgetTest' (a live
'QApplication' in a child process, plus the event-based gesture surface),
imported directly, hence the 'run_*.py' / 'Run*' naming the 'worQt.qtest'
runner discovers.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations
