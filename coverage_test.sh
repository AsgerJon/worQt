#!/usr/bin/env bash
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
#
#  Run the 'worQt.qtest' suite under coverage and report.
#
#  'worQt.qtest' isolates each 'AppTest' in its own child process; with
#  'WORQT_COVERAGE=1' the harness launches each child under 'coverage run'
#  ('parallel = true' in 'pyproject.toml [tool.coverage.run]' gives every
#  process its own data file), so 'combine' is needed before reporting. A
#  child killed on
#  timeout or segfault flushes no data - coverage of a failed run is not
#  produced, and is not wanted.
#
#  Coverage is measured for the WHOLE suite only - a partial run gives a
#  misleading picture - so this script takes no arguments.
#
#  Usage:
#    ./coverage_test.sh
#
#  The report is built and opened only when the whole suite passes; if any
#  class fails the script prints that and exits with the suite's status
#  without producing or opening a report.

#  No '-e': the suite's exit status is captured explicitly and branched on.
set -uo pipefail

if [ "$#" -gt 0 ]; then
  echo "coverage_test.sh takes no arguments: coverage is whole-suite only." >&2
  exit 2
fi

#  Run from the repository root (the directory holding this script).
cd "$(dirname "$0")"

export WORQT_COVERAGE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src
#  Honour an existing Qt platform (a real display); otherwise go offscreen.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

#  Remove any stray parallel data files left by a previously killed run
#  ('.coverage.<host>.<pid>.<rand>', e.g. '.coverage.HAL9000.12345.678901').
#  A run aborted before 'combine' leaves these behind, and the next
#  'combine' would otherwise fold their stale data into this report.
#  'rm -f' is silent when none exist.
rm -f .coverage .coverage.*
python -m coverage erase
python -m coverage run -m worQt.qtest
status=$?

#  Coverage only makes sense for a clean, complete suite. If any class
#  failed, surface that and stop - no report is built and nothing is opened.
if [ "${status}" -ne 0 ]; then
  echo "Tests failed (status ${status}); skipping coverage report." >&2
  exit "${status}"
fi

python -m coverage combine
python -m coverage report -m

reportDir="htmlcov"
python -m coverage html -d "${reportDir}"

#  Open the report in the default browser, detached, like the worktoy
#  coverage script. Silent and non-fatal when there is no display.
if [ -f "${reportDir}/index.html" ]; then
  setsid xdg-open "${reportDir}/index.html" >/dev/null 2>&1 || true
fi

exit "${status}"
