"""
FullRunner runs every discovered test class and assembles the results.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from traceback import format_exc
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe
from ._discovery import Discovery
from ._single_result import SingleResult
from ._single_runner import SingleRunner
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator

  Results = tuple[SingleResult, ...]


class FullRunner(BaseObject):
  """
  FullRunner runs a whole test tree by handing each discovered class to
  its own 'SingleRunner' and collecting the results. It drives a
  'Discovery' for the class names and the top-level path, runs each name
  through a fresh 'SingleRunner', and turns every returned outcome dict
  into a 'SingleResult'. The collected tuple of results is the run, and
  the aggregate totals and overall pass or fail are folds over it.

  A class that raises while being imported or run does not abort the
  sweep. Its exception is caught and recorded as a 'SingleResult' holding
  a single error, so the offending class shows up red in the report
  rather than taking the rest of the run down with it.

  The runs happen in this interpreter, one class at a time, each scrubbed
  by its 'SingleRunner' afterwards. The single place that calls
  'SingleRunner' is '_runOne', which is the seam to swap for a subprocess
  per class when a test tree needs more isolation than an in-process
  scrub provides; the assembly above it does not change.

  Attributes
  ----------
  discovery : Discovery
      The 'Discovery' that supplies the class names and the top-level
      path for the run.
  results : tuple of SingleResult
      The results collected by the most recent 'run', one per discovered
      class. Empty before the first run. Read only.
  success : bool
      Whether every collected result succeeded. Read only.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __test_results__: Optional[Results] = None

  #  Public Variables
  discovery = AttriBox[Discovery]()

  #  Virtual Variables
  results: Field[Results] = Field()
  success: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @results.GET
  def _getResults(self) -> Results:
    """
    The results from the most recent run.

    Returns
    -------
    Results
        A tuple of 'SingleResult', empty before the first run.
    """
    return maybe(self.__test_results__, ())

  @success.GET
  def _getSuccess(self) -> bool:
    """
    Whether the run had no failing class.

    Returns
    -------
    bool
        True when every collected result succeeded, including the case of
        no results at all.
    """
    for result in self.results:
      if not result.success:
        return False
    return True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _runOne(name: str, topLevel: str) -> SingleResult:
    """
    Runs one class through a fresh 'SingleRunner' and builds its
    'SingleResult'. An exception raised while importing or running the
    class is caught and turned into a result holding a single error, so
    the failure is reported against the class rather than propagated.
    This is the seam a subprocess-per-class strategy replaces.

    Parameters
    ----------
    name : str
        The dotted 'module:ClassName' name of the class to run.
    topLevel : str
        The directory put on 'sys.path' for the import, from 'Discovery'.

    Returns
    -------
    SingleResult
        The class result, or a result holding a single error when the run
        raised.
    """
    try:
      raw = SingleRunner(name, topLevel).run()
    except Exception:  # noqa: catch broad on purpose, see docstring
      return SingleResult(name=name, errors=((name, format_exc()),))
    result = SingleResult.fromDict(raw)
    if isinstance(result, SingleResult):
      return result
    raise TypeException('result', result, SingleResult)

  def run(self) -> Results:
    """
    Discovers the test classes and runs every one, storing and returning
    the tuple of 'SingleResult' objects.

    Returns
    -------
    Results
        A tuple of 'SingleResult', one per discovered class, in discovery
        order.
    """
    discovery = self.discovery
    names = discovery.discover()
    topLevel = discovery.topLevel
    results: list[SingleResult] = []
    for name in names:
      result: SingleResult = self._runOne(name, topLevel)
      results.append(result)
    self.__test_results__ = (*results,)
    return (*results,)

  def totals(self) -> dict:
    """
    Returns the aggregate counts across every result: the number of
    classes, the number of test methods run, and the totals of passes,
    failures, errors, and skips, plus the summed wall-clock duration.

    Returns
    -------
    dict
        A mapping with the keys 'classes', 'testsRun', 'passed',
        'failures', 'errors', 'skips', and 'duration'.
    """
    results = self.results
    return dict(
        classes=len(results),
        testsRun=sum(r.testsRun for r in results),
        passed=sum(r.passed for r in results),
        failures=sum(len(r.failures) for r in results),
        errors=sum(len(r.errors) for r in results),
        skips=sum(len(r.skipped) for r in results),
        duration=sum(r.duration for r in results),
    )

  @staticmethod
  def _indent(text: str) -> str:
    """
    Indents every line of 'text' by four spaces for the report body.

    Parameters
    ----------
    text : str
        The possibly multi-line text to indent.

    Returns
    -------
    str
        The text with every line prefixed by four spaces.
    """
    return str.join('\n', ['    %s' % line for line in text.split('\n')])

  def report(self) -> str:
    """
    Renders a text report: a header with the aggregate totals and the
    overall status, then a detail block for every class that failed or
    errored, with each test's id and traceback, and finally any import
    errors that 'Discovery' collected.

    Returns
    -------
    str
        The rendered multi-line report.
    """
    totals = self.totals()
    status = 'PASSED' if self.success else 'FAILED'
    rule = '=' * 60
    headSpec = """%d classes, %d tests | %d passed, %d failed, """
    headSpec += """%d errored, %d skipped"""
    head = headSpec % (
      totals['classes'],
      totals['testsRun'],
      totals['passed'],
      totals['failures'],
      totals['errors'],
      totals['skips'],
    )
    tail = 'duration: %.3fs   status: %s' % (totals['duration'], status)
    lines = [rule, head, tail, rule]
    for result in self.results:
      if result.success:
        continue
      lines.append('')
      lines.append(result.name)
      for testId, message in result.failures:
        lines.append('  FAIL %s' % testId)
        lines.append(self._indent(message))
      for testId, message in result.errors:
        lines.append('  ERROR %s' % testId)
        lines.append(self._indent(message))
    discoveryErrors = self.discovery.errors
    if discoveryErrors:
      lines.append('')
      lines.append('discovery import errors:')
      for message in discoveryErrors:
        lines.append(self._indent(message))
    return str.join('\n', lines)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Discovery)
  def __init__(self, discovery: Discovery) -> None:
    self.discovery = discovery

  @overload(str, str)
  def __init__(self, testRoot: str, pattern: str) -> None:
    self.discovery = Discovery(testRoot, pattern)

  @overload(str)
  def __init__(self, testRoot: str) -> None:
    self.discovery = Discovery(testRoot)

  @overload()
  def __init__(self) -> None:
    self.discovery = Discovery()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __call__(self) -> Results:
    return self.run()

  def __iter__(self) -> Iterator[SingleResult]:
    yield from self.results

  def __str__(self) -> str:
    return self.report()

  def __repr__(self) -> str:
    infoSpec = """%s(%r)"""
    return infoSpec % (type(self).__name__, self.discovery)
