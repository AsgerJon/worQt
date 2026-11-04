"""
The 'tests.test_qtest.fixtures' package holds test modules that end in
every way a test class can end - passing, failing, crashing, hanging,
failing to load - for the harness tests to run in child processes and
check that each ending is reported for what it is. Their file names begin
with an underscore, so discovery never runs them as part of the suite.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations
