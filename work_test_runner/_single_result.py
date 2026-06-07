"""
SingleResult is the serializable outcome of running one test class.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self

  Pair = tuple[str, str]
  Pairs = tuple[Pair, ...]


class SingleResult(BaseObject):
  """
  SingleResult is the outcome of running a single test class: the class
  name, the number of test methods run, the failures, errors, and skips
  with their tracebacks, and the wall-clock duration. A 'FullRunner'
  builds one from the raw dict a 'SingleRunner' emits, through 'fromDict',
  and the type carries its own serialization for the subprocess case:
  'asDict' and 'toJson' on the way out, 'fromDict' and 'fromJson' on the
  way in.

  Failures, errors, and skips are each stored as a tuple of
  '(testId, message)' pairs, where 'testId' is the fully qualified test
  method name and 'message' is the traceback or, for a skip, the reason.

  Attributes
  ----------
  name : str
      The dotted 'module:ClassName' name of the test class.
  testsRun : int
      The number of test methods that ran.
  failures : tuple of (str, str)
      The '(testId, traceback)' pairs for tests that raised an
      'AssertionError'.
  errors : tuple of (str, str)
      The '(testId, traceback)' pairs for tests that raised any other
      exception.
  skipped : tuple of (str, str)
      The '(testId, reason)' pairs for tests that were skipped.
  duration : float
      The wall-clock seconds the class took to run.
  passed : int
      The number of tests that neither failed, errored, nor skipped. Read
      only.
  success : bool
      Whether the class had no failures and no errors. Read only.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  name = AttriBox[str]()
  testsRun = AttriBox[int]()
  failures = AttriBox[tuple]()
  errors = AttriBox[tuple]()
  skipped = AttriBox[tuple]()
  duration = AttriBox[float]()

  #  Virtual Variables
  passed: Field[int] = Field()
  success: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @passed.GET
  def _getPassed(self) -> int:
    spent = len(self.failures) + len(self.errors) + len(self.skipped)
    return self.testsRun - spent

  @success.GET
  def _getSuccess(self) -> bool:
    return True if not (self.failures or self.errors) else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _toPairs(raw: Any) -> Pairs:
    """
    Normalizes a sequence of two-item sequences into a tuple of string
    pairs, so a JSON round-trip (which turns tuples into lists) lands
    back as the tuple form the fields expect.

    Parameters
    ----------
    raw : Any
        A sequence of two-item sequences, as the pair lists arrive from
        JSON.

    Returns
    -------
    Pairs
        A tuple of two-item string tuples.
    """
    return (*((str(left), str(right)) for left, right in raw),)

  def asDict(self) -> dict:
    """
    Returns a plain JSON-ready dict of the result, with each pair tuple
    flattened to a two-item list. The dict is a fresh object on every
    call.

    Returns
    -------
    dict
        A mapping with the keys 'name', 'testsRun', 'failures', 'errors',
        'skipped', and 'duration', ready for 'json.dumps'.
    """
    return dict(
        name=self.name,
        testsRun=self.testsRun,
        failures=[[testId, message] for testId, message in self.failures],
        errors=[[testId, message] for testId, message in self.errors],
        skipped=[[testId, message] for testId, message in self.skipped],
        duration=self.duration,
    )

  def toJson(self) -> str:
    """
    Returns the result encoded as a JSON string.

    Returns
    -------
    str
        The 'asDict' mapping encoded with 'json.dumps'.
    """
    return json.dumps(self.asDict())

  @classmethod
  def fromDict(cls, data: dict) -> SingleResult:
    """
    Rebuilds a 'SingleResult' from the dict produced by 'asDict',
    coercing the pair lists back into string-pair tuples.

    Parameters
    ----------
    data : dict
        A mapping in the shape 'asDict' produces. Missing keys fall back
        to empty defaults.

    Returns
    -------
    Self
        A 'SingleResult' carrying the dict's values.
    """
    self = cls()
    self.name = data.get('name', '')
    self.testsRun = data.get('testsRun', 0)
    self.failures = cls._toPairs(data.get('failures', ()))
    self.errors = cls._toPairs(data.get('errors', ()))
    self.skipped = cls._toPairs(data.get('skipped', ()))
    self.duration = data.get('duration', 0.0)
    return self

  @classmethod
  def fromJson(cls, text: str) -> Self:
    """
    Rebuilds a 'SingleResult' from a JSON string produced by 'toJson'.

    Parameters
    ----------
    text : str
        A JSON string in the shape 'toJson' produces.

    Returns
    -------
    Self
        A 'SingleResult' carrying the decoded values.
    """
    return cls.fromDict(json.loads(text))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload()
  def __init__(self, **kwargs) -> None:
    keys = ('name', 'testsRun', 'failures', 'errors', 'skipped', 'duration')
    for key in keys:
      if key in kwargs:
        setattr(self, key, kwargs[key])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self) -> str:
    infoSpec = """<%s: %s | %d run, %d passed, %d failed, %d errored, """
    infoSpec += """%d skipped (%.3fs)>"""
    return infoSpec % (
      type(self).__name__,
      self.name,
      self.testsRun,
      self.passed,
      len(self.failures),
      len(self.errors),
      len(self.skipped),
      self.duration,
    )

  def __repr__(self) -> str:
    infoSpec = """%s.fromDict(%s)"""
    return infoSpec % (type(self).__name__, self.asDict())
