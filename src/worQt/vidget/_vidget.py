"""
Vidget subclasses 'VidgetBase' and edits text the way Vi does.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent
from worktoy.desc import AttriBox, Field
from worktoy.waitaminute.control_flow import SkipSet

from . import ViMode, VidgetBase, viMotions

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias, Union

  from PySide6.QtGui import QMouseEvent

  Motion: TypeAlias = tuple[str, str]  # the motion's keys, a found char
  Span: TypeAlias = tuple[int, int, bool]  # from, to, whole lines
  Spec: TypeAlias = tuple  # a parsed command
  Parsed: TypeAlias = Union[Spec, None, bool]  # None: wait, False: bad
  KeyEntry: TypeAlias = tuple[int, Qt.KeyboardModifier, str]

_CTRL = Qt.KeyboardModifier.ControlModifier
_RETURN_KEYS = (Qt.Key.Key_Return, Qt.Key.Key_Enter)
_DIGITS = '0123456789'
_EXCLUSIVE, _INCLUSIVE, _LINES = 'exclusive', 'inclusive', 'lines'


class Vidget(VidgetBase):
  """
  Vidget subclasses 'VidgetBase' and edits its text the way Vi does. It
  starts in 'NORMAL' mode, where keys are commands, each after an
  optional count:

  - Motions: 'h j k l', 'w b e' and 'W B E', '0 ^ $', 'gg G', '{ }',
    'f t F T' with a character and ';' ',' to repeat them, the searches
    'n N * #', and 'H M L' for the top, middle and bottom of the view.
  - Operators 'd', 'c' and 'y' delete, change or yank as far as any
    motion goes, or whole lines when doubled: 'dw', 'c$', 'yj', 'dG',
    'ct.', 'dd', 'cc', 'yy'. 'x X D C s S Y' are their shorthands.
  - 'p' and 'P' put the register back; 'r' replaces under the cursor;
    'J' joins lines; 'u' undoes, Ctrl+R redoes and '.' repeats the last
    change.
  - 'i a I A o O' enter 'INSERT' mode, where keys type until Esc.
  - ':' enters 'COMMAND' mode for an ex command: ':w', ':q', ':wq',
    ':x', ':q!' and ':' with a line number. '/' and '?' search forward
    and back. 'ZZ' writes and quits, 'ZQ' quits.
  - Scrolling: Ctrl+E and Ctrl+Y a line, Ctrl+D and Ctrl+U half a view,
    Ctrl+F and Ctrl+B a view, and 'zt zz zb' to put the cursor's line at
    the top, middle or bottom.
  - Tabs: 'gt' and ':tabn' go to the next tab, 'gT' and ':tabp' to the
    previous one, ':tabnew' opens a new one.

  The vidget writes, quits and switches tabs for nothing itself: ':w'
  emits 'writeRequested', ':q' emits 'quitRequested', the tab commands
  emit 'tabStepRequested' and 'newTabRequested', for its window to act
  on. Like Vi, ':q' refuses while there are unsaved changes, and ':q!'
  throws them away.

  Vi as it is, but no trap: a click puts the cursor where it lands in any
  mode, and the mouse and Tab move the focus to other widgets as they
  would anywhere else. The arrow keys and the wheel work in every mode,
  and menus and shortcuts keep working throughout.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __motions__ = {  # keys -> (method returning where it lands, its kind)
    'h' : ('_motionLeft', _EXCLUSIVE),
    'l' : ('_motionRight', _EXCLUSIVE),
    'j' : ('_motionDown', _LINES),
    'k' : ('_motionUp', _LINES),
    'w' : ('_motionWordForward', _EXCLUSIVE),
    'W' : ('_motionBigWordForward', _EXCLUSIVE),
    'b' : ('_motionWordBackward', _EXCLUSIVE),
    'B' : ('_motionBigWordBackward', _EXCLUSIVE),
    'e' : ('_motionWordEnd', _INCLUSIVE),
    'E' : ('_motionBigWordEnd', _INCLUSIVE),
    '0' : ('_motionLineStart', _EXCLUSIVE),
    '^' : ('_motionFirstNonBlank', _EXCLUSIVE),
    '$' : ('_motionLineEnd', _EXCLUSIVE),
    'gg': ('_motionFirstLine', _LINES),
    'G' : ('_motionLastLine', _LINES),
    '{' : ('_motionParagraphBackward', _EXCLUSIVE),
    '}' : ('_motionParagraphForward', _EXCLUSIVE),
    ';' : ('_motionFindAgain', _INCLUSIVE),
    ',' : ('_motionFindBack', _EXCLUSIVE),
    'n' : ('_motionSearchNext', _EXCLUSIVE),
    'N' : ('_motionSearchBack', _EXCLUSIVE),
    '*' : ('_motionWordSearchForward', _EXCLUSIVE),
    '#' : ('_motionWordSearchBackward', _EXCLUSIVE),
    'H' : ('_motionViewTop', _LINES),
    'M' : ('_motionViewMiddle', _LINES),
    'L' : ('_motionViewBottom', _LINES),
  }
  __finds__ = {  # key -> (forward, till), each taking a character
    'f': (True, False),
    't': (True, True),
    'F': (False, False),
    'T': (False, True),
  }
  __operators__ = {
    'd': '_operateDelete',
    'c': '_operateChange',
    'y': '_operateYank',
  }
  __commands__ = {
    'x' : '_deleteChars',
    'X' : '_deleteCharsBefore',
    'D' : '_deleteToLineEnd',
    'C' : '_changeToLineEnd',
    's' : '_substituteChars',
    'S' : '_substituteLines',
    'Y' : '_yankLines',
    'p' : '_putAfter',
    'P' : '_putBefore',
    'J' : '_joinLines',
    'u' : 'undo',
    '.' : '_repeatChange',
    'i' : '_insertHere',
    'a' : '_insertAfter',
    'I' : '_insertAtFirstNonBlank',
    'A' : '_insertAtLineEnd',
    'o' : '_openBelow',
    'O' : '_openAbove',
    ':' : '_enterCommand',
    '/' : '_enterSearchForward',
    '?' : '_enterSearchBackward',
    'zt': '_scrollCursorTop',
    'zz': '_scrollCursorMiddle',
    'zb': '_scrollCursorBottom',
    'ZZ': '_writeAndQuit',
    'ZQ': '_quitWithoutWriting',
    'gt': '_nextTab',
    'gT': '_previousTab',
  }
  __changes__ = ('x', 'X', 'D', 'C', 's', 'S', 'p', 'P', 'J', 'i', 'a',
                 'I', 'A', 'o', 'O')  # the commands '.' repeats
  __char_commands__ = {'r': '_replaceChars'}  # each taking a character
  __ctrl_commands__ = {
    Qt.Key.Key_R: 'redo',
    Qt.Key.Key_E: '_scrollRowDown',
    Qt.Key.Key_Y: '_scrollRowUp',
    Qt.Key.Key_D: '_halfViewDown',
    Qt.Key.Key_U: '_halfViewUp',
    Qt.Key.Key_F: '_viewDown',
    Qt.Key.Key_B: '_viewUp',
  }
  __ex_commands__ = {
    'w' : '_exWrite',
    'q' : '_exQuit',
    'wq': '_exWriteQuit',
    'x' : '_exWriteQuit',
    'q!': '_exForceQuit',
    'tabnew'     : '_exNewTab',
    'tabn'       : '_exNextTab',
    'tabnext'    : '_exNextTab',
    'tabp'       : '_exPreviousTab',
    'tabprevious': '_exPreviousTab',
  }
  __arrow_keys__ = {
    Qt.Key.Key_Left : 'cursorLeft',
    Qt.Key.Key_Right: 'cursorRight',
    Qt.Key.Key_Up   : 'cursorUp',
    Qt.Key.Key_Down : 'cursorDown',
    Qt.Key.Key_Home : 'cursorHome',
    Qt.Key.Key_End  : 'cursorEnd',
  }

  #  Private Variables
  __pending_keys__: Optional[str] = None
  __command_prompt__: Optional[str] = None  # ':', '/' or '?'
  __command_line__: Optional[str] = None
  __status_message__: Optional[str] = None
  __last_find__: Optional[tuple[str, bool, bool]] = None
  __last_search__: Optional[tuple[str, bool]] = None
  __key_record__: Optional[list[KeyEntry]] = None
  __last_change__: Optional[list[KeyEntry]] = None

  #  Public Variables
  mode = AttriBox[ViMode](ViMode.NORMAL)
  replaying = AttriBox[bool](False)  # while '.' replays the last change

  #  Virtual Variables
  pendingKeys: Field[str] = Field()
  commandPrompt: Field[str] = Field()
  commandLine: Field[str] = Field()

  #  Signals
  writeRequested = Signal()
  quitRequested = Signal()
  newTabRequested = Signal()
  tabStepRequested = Signal(int)  # 1 for the next tab, -1 the previous

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @pendingKeys.GET
  def _getPendingKeys(self, ) -> str:
    """The 'pendingKeys' getter returns the keys of a command not yet
    complete, such as '3d', or nothing."""
    return '' if self.__pending_keys__ is None else self.__pending_keys__

  @commandPrompt.GET
  def _getCommandPrompt(self, ) -> str:
    """The 'commandPrompt' getter returns what the command line opened
    with: ':' for an ex command, '/' or '?' for a search."""
    prompt = self.__command_prompt__
    return ':' if prompt is None else prompt

  @commandLine.GET
  def _getCommandLine(self, ) -> str:
    """The 'commandLine' getter returns the command being written."""
    return '' if self.__command_line__ is None else self.__command_line__

  def _getBlockCursor(self, ) -> bool:
    """The cursor is a block in 'NORMAL' mode, a bar otherwise."""
    return True if self.mode is ViMode.NORMAL else False

  def _getStatusLeft(self, ) -> str:
    """
    The status line tells the command being written, else the latest
    message, else '-- INSERT --' in 'INSERT' mode, else the keys of a
    command not yet complete.
    """
    if self.mode is ViMode.COMMAND:
      return '%s%s' % (self.commandPrompt, self.commandLine)
    if self.__status_message__ is not None:
      return self.__status_message__
    if self.mode is ViMode.INSERT:
      return '-- INSERT --'
    return self.pendingKeys

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mode.preSet
  def _preSetMode(self, mode: ViMode) -> None:
    if mode is self.mode:
      raise SkipSet

  @mode.onSet
  def _onSetMode(self, mode: ViMode) -> None:
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showsCursor(self, ) -> bool:
    """The cursor is drawn while the vidget has the focus, except while
    a command is written on the status line."""
    if self.mode is ViMode.COMMAND:
      return False
    return VidgetBase.showsCursor(self)

  def matchable(self, text: str) -> str:
    """
    The 'matchable' method returns 'text' as searches compare it: as it
    is, here. A subclass whose case means nothing may fold it.
    """
    return text

  def _lastColumn(self, ) -> int:
    """The position of the last character on the cursor's line, where
    'NORMAL' mode keeps the cursor."""
    start, end = self.lineStartAt(self.cursor), self.lineEndAt(self.cursor)
    return end - 1 if end > start else start

  def _settle(self, ) -> None:
    """In 'NORMAL' mode the cursor sits on a character, never past the
    last one of its line."""
    if self.mode is ViMode.NORMAL and self.cursor > self._lastColumn():
      self.cursor = self._lastColumn()

  def _message(self, message: str) -> None:
    self.__status_message__ = message

  # \_____________________
  #  Reading the keys  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  @staticmethod
  def _readCount(keys: str, at: int) -> tuple[int, int]:
    """
    The '_readCount' method reads a count from 'keys' at 'at', returning
    it, 0 for none, and where it ends. A leading '0' is no count but the
    motion to the start of the line.
    """
    end = at
    while end < len(keys) and keys[end] in _DIGITS:
      if end == at and keys[end] == '0':
        break
      end += 1
    return (int(keys[at:end]) if end > at else 0), end

  def _readMotion(self, keys: str) -> Union[Motion, None, bool]:
    """
    The '_readMotion' method reads 'keys' as a motion: the motion, or
    'None' while it may still become one, or 'False' if it cannot.
    """
    if not keys:
      return None
    if keys[0] in self.__finds__:
      if len(keys) == 1:
        return None
      return (keys[0], keys[1]) if len(keys) == 2 else False
    if keys in self.__motions__:
      return keys, ''
    if any(str.startswith(key, keys) for key in self.__motions__):
      return None
    return False

  def _parse(self, keys: str) -> Parsed:
    """
    The '_parse' method reads 'keys' as a 'NORMAL' mode command: the
    command, or 'None' while the keys may still become one, or 'False'
    if they cannot.
    """
    count, at = self._readCount(keys, 0)
    rest = keys[at:]
    if not rest:
      return None
    head = rest[0]
    if head in self.__operators__:
      inner, at = self._readCount(keys, at + 1)
      total = count * inner if count and inner else count or inner
      tail = keys[at:]
      if tail == head:
        return 'operate', head, None, total
      motion = self._readMotion(tail)
      return ('operate', head, motion, total) if motion else motion
    if head in self.__char_commands__:
      if len(rest) == 1:
        return None
      return ('char', head, rest[1], count) if len(rest) == 2 else False
    if rest in self.__commands__:
      return 'command', rest, count
    motion = self._readMotion(rest)
    if motion:
      return 'move', motion, count
    if motion is None:
      return None
    if any(str.startswith(key, rest) for key in self.__commands__):
      return None
    return False

  def _run(self, spec: Spec) -> bool:
    """
    The '_run' method runs the parsed command 'spec' and tells whether it
    was a change, which '.' repeats.
    """
    kind = spec[0]
    if kind == 'move':
      target = self._motionTarget(spec[1], spec[2])
      if target is not None:
        self.cursor = target
      return False
    if kind == 'operate':
      _, operator, motion, count = spec
      if motion is None:
        span = self._linesSpan(count)
      else:
        span = self._motionSpan(operator, motion, count)
      if span is not None:
        getattr(self, self.__operators__[operator])(*span)
      return True if operator != 'y' and span is not None else False
    if kind == 'char':
      _, key, char, count = spec
      getattr(self, self.__char_commands__[key])(char, max(count, 1))
      return True
    _, key, count = spec
    getattr(self, self.__commands__[key])(max(count, 1))
    return True if key in self.__changes__ else False

  def _runPending(self, keys: str) -> None:
    """
    The '_runPending' method runs the command 'keys' spell, keeps them
    pending while they may still become one, and drops them when they
    cannot.
    """
    spec = self._parse(keys)
    if spec is None:
      self.__pending_keys__ = keys
      return
    self.__pending_keys__ = None
    if spec is False:
      return self._dropRecord()
    if not self._run(spec):
      self._dropRecord()
    elif self.mode is ViMode.NORMAL:
      self._finishRecord()
    self._settle()

  def _normalKey(self, event: QKeyEvent) -> bool:
    key, text = event.key(), event.text()
    if key == Qt.Key.Key_Escape:
      self.__pending_keys__ = None
      self._dropRecord()
      return True
    if event.modifiers() & _CTRL:
      return self._ctrlKey(key)
    if self._arrowKey(key):
      self.__pending_keys__ = None
      self._dropRecord()
      self._settle()
      return True
    if len(text) != 1 or not str.isprintable(text):
      self._dropRecord()
      return False
    self._runPending('%s%s' % (self.pendingKeys, text))
    return True

  def _ctrlKey(self, key: int) -> bool:
    """Ctrl+R redoes and the other Ctrl keys scroll; a pending count
    counts for them."""
    name = self.__ctrl_commands__.get(key, None)
    count, _ = self._readCount(self.pendingKeys, 0)
    self.__pending_keys__ = None
    self._dropRecord()
    if name is None:
      return False
    getattr(self, name)(max(count, 1))
    self._settle()
    return True

  def _insertKey(self, event: QKeyEvent) -> bool:
    key, text = event.key(), event.text()
    if key == Qt.Key.Key_Escape:
      self.leaveInsert()
    elif key in _RETURN_KEYS:
      self.insertText('\n')
    elif key == Qt.Key.Key_Backspace:
      self.deleteBackward()
    elif key == Qt.Key.Key_Delete:
      self.deleteForward()
    elif self._arrowKey(key):
      pass
    elif text and all(self.accepts(char) for char in text):
      self.insertText(text)
    else:
      return False
    return True

  def _commandKey(self, event: QKeyEvent) -> bool:
    key, text, line = event.key(), event.text(), self.commandLine
    if key == Qt.Key.Key_Escape:
      self._leaveCommand()
    elif key in _RETURN_KEYS:
      prompt = self.commandPrompt
      self._leaveCommand()
      if prompt == ':':
        self.execute(line)
      else:
        self.searchFor(line, True if prompt == '/' else False)
    elif key == Qt.Key.Key_Backspace:
      if line:
        self.__command_line__ = line[:-1]
      else:
        self._leaveCommand()
    elif len(text) == 1 and str.isprintable(text):
      self.__command_line__ = '%s%s' % (line, text)
    else:
      return False
    return True

  def _arrowKey(self, key: int) -> bool:
    name = self.__arrow_keys__.get(key, None)
    if name is None:
      return False
    getattr(self, name)()
    return True

  # \_____________________
  #  Repeating with '.'  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _startRecord(self, ) -> None:
    if not self.replaying:
      self.__key_record__ = []

  def _record(self, event: QKeyEvent) -> None:
    if not self.replaying and self.__key_record__ is not None:
      entry = (event.key(), event.modifiers(), event.text())
      self.__key_record__.append(entry)

  def _dropRecord(self, ) -> None:
    if not self.replaying:
      self.__key_record__ = None

  def _finishRecord(self, ) -> None:
    """The keys recorded since the change began become the change '.'
    repeats."""
    if not self.replaying and self.__key_record__ is not None:
      self.__last_change__ = self.__key_record__
      self.__key_record__ = None

  def _repeatChange(self, count: int) -> None:
    """'.' replays the keys of the last change, 'count' times."""
    entries = self.__last_change__
    if not entries:
      return
    self.replaying = True
    try:
      for _ in range(count):
        for key, modifiers, text in entries:
          press = QEvent.Type.KeyPress
          self._handleKey(QKeyEvent(press, key, modifiers, text))
    finally:
      self.replaying = False

  # \_______________
  #  Motions    ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _motionTarget(self, motion: Motion, count: int) -> Optional[int]:
    """Where 'motion' lands from the cursor, or 'None' if nowhere. A
    count of 0 means none was given."""
    key, char = motion
    if key in self.__finds__:
      forward, till = self.__finds__[key]
      self.__last_find__ = (char, forward, till)
      return self._find(char, max(count, 1), forward, till)
    return getattr(self, self.__motions__[key][0])(count)

  def _motionKind(self, motion: Motion) -> str:
    """Whether 'motion' is exclusive, inclusive or covers whole lines.
    A find forward takes its character with it; one back does not."""
    key, _ = motion
    if key in self.__finds__:
      return _INCLUSIVE if self.__finds__[key][0] else _EXCLUSIVE
    if key in (';', ',') and self.__last_find__ is not None:
      forward = self.__last_find__[1]
      forward = forward if key == ';' else not forward
      return _INCLUSIVE if forward else _EXCLUSIVE
    return self.__motions__[key][1]

  def _motionLeft(self, count: int) -> int:
    return max(self.lineStartAt(self.cursor), self.cursor - max(count, 1))

  def _motionRight(self, count: int) -> int:
    return min(self.lineEndAt(self.cursor), self.cursor + max(count, 1))

  def _motionLine(self, steps: int) -> int:
    """Where 'steps' lines down (up when negative) lands, keeping the
    column as far as that line allows."""
    column = self.cursor - self.lineStartAt(self.cursor)
    start = self.startOfLine(self.lineNumberAt(self.cursor) + steps)
    return min(start + column, self.lineEndAt(start))

  def _motionDown(self, count: int) -> int:
    return self._motionLine(max(count, 1))

  def _motionUp(self, count: int) -> int:
    return self._motionLine(-max(count, 1))

  def _motionWordForward(self, count: int) -> int:
    text, cursor = self.text, self.cursor
    return viMotions.wordForward(text, cursor, max(count, 1), False)

  def _motionBigWordForward(self, count: int) -> int:
    text, cursor = self.text, self.cursor
    return viMotions.wordForward(text, cursor, max(count, 1), True)

  def _motionWordBackward(self, count: int) -> int:
    text, cursor = self.text, self.cursor
    return viMotions.wordBackward(text, cursor, max(count, 1), False)

  def _motionBigWordBackward(self, count: int) -> int:
    text, cursor = self.text, self.cursor
    return viMotions.wordBackward(text, cursor, max(count, 1), True)

  def _motionWordEnd(self, count: int) -> int:
    return viMotions.wordEnd(self.text, self.cursor, max(count, 1), False)

  def _motionBigWordEnd(self, count: int) -> int:
    return viMotions.wordEnd(self.text, self.cursor, max(count, 1), True)

  def _motionLineStart(self, count: int) -> int:
    return self.lineStartAt(self.cursor)

  def _motionFirstNonBlank(self, count: int) -> int:
    return viMotions.firstNonBlank(self.text, self.cursor)

  def _motionLineEnd(self, count: int) -> int:
    return self.lineEndAt(self.cursor)

  def _motionFirstLine(self, count: int) -> int:
    """'gg' goes to the first line, or to line 'count'."""
    start = self.startOfLine(count - 1 if count else 0)
    return viMotions.firstNonBlank(self.text, start)

  def _motionLastLine(self, count: int) -> int:
    """'G' goes to the last line, or to line 'count'."""
    number = count - 1 if count else self.lineCount() - 1
    return viMotions.firstNonBlank(self.text, self.startOfLine(number))

  def _motionParagraphForward(self, count: int) -> int:
    text, cursor = self.text, self.cursor
    return viMotions.paragraphForward(text, cursor, max(count, 1))

  def _motionParagraphBackward(self, count: int) -> int:
    text, cursor = self.text, self.cursor
    return viMotions.paragraphBackward(text, cursor, max(count, 1))

  def _find(
      self,
      char: str,
      count: int,
      forward: bool,
      till: bool,
  ) -> Optional[int]:
    text, cursor = self.text, self.cursor
    return viMotions.findInLine(text, cursor, char, count, forward, till)

  def _motionFindAgain(self, count: int) -> Optional[int]:
    """';' repeats the last 'f', 't', 'F' or 'T'."""
    if self.__last_find__ is None:
      return None
    char, forward, till = self.__last_find__
    return self._find(char, max(count, 1), forward, till)

  def _motionFindBack(self, count: int) -> Optional[int]:
    """',' repeats the last 'f', 't', 'F' or 'T' the other way."""
    if self.__last_find__ is None:
      return None
    char, forward, till = self.__last_find__
    return self._find(char, max(count, 1), not forward, till)

  # \_______________
  #  Searching  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _search(self, pattern: str, forward: bool) -> Optional[int]:
    text, found = self.matchable(self.text), self.matchable(pattern)
    return viMotions.search(text, self.cursor, found, forward)

  def searchFor(self, pattern: str, forward: bool) -> None:
    """
    The 'searchFor' method moves the cursor to where 'pattern' next
    occurs, forward or back, and remembers it for 'n' and 'N'. An empty
    pattern searches for the last one again.
    """
    if not pattern and self.__last_search__ is not None:
      pattern = self.__last_search__[0]
    self.__last_search__ = (pattern, forward)
    target = self._search(pattern, forward)
    if target is None:
      return self._message('Pattern not found: %s' % pattern)
    self.cursor = target

  def _motionSearchNext(self, count: int) -> Optional[int]:
    """'n' finds the last search again, the same way."""
    return self._searchAgain(max(count, 1), True)

  def _motionSearchBack(self, count: int) -> Optional[int]:
    """'N' finds the last search again, the other way."""
    return self._searchAgain(max(count, 1), False)

  def _searchAgain(self, count: int, same: bool) -> Optional[int]:
    if self.__last_search__ is None:
      return None
    pattern, forward = self.__last_search__
    forward = forward if same else not forward
    at, cursor = None, self.cursor
    for _ in range(count):
      at = self._search(pattern, forward)
      if at is None:
        break
      self.cursor = at
    self.cursor = cursor
    if at is None:
      self._message('Pattern not found: %s' % pattern)
    return at

  def _wordUnderCursor(self, ) -> str:
    text, start = self.text, self.cursor
    while start > 0 and viMotions.charKind(text[start - 1], False) == 1:
      start -= 1
    end = self.cursor
    while end < len(text) and viMotions.charKind(text[end], False) == 1:
      end += 1
    return text[start:end]

  def _motionWordSearchForward(self, count: int) -> Optional[int]:
    """'*' searches forward for the word under the cursor."""
    word = self._wordUnderCursor()
    if not word:
      return None
    self.__last_search__ = (word, True)
    return self._searchAgain(max(count, 1), True)

  def _motionWordSearchBackward(self, count: int) -> Optional[int]:
    """'#' searches back for the word under the cursor."""
    word = self._wordUnderCursor()
    if not word:
      return None
    self.__last_search__ = (word, False)
    return self._searchAgain(max(count, 1), True)

  # \_____________________
  #  The view and paging  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _rowsShown(self, ) -> int:
    layout = self._laidOut()
    if layout is None:
      return 1
    return self.rowsInView(layout, self.paintView.height)

  def _viewRow(self, place: float) -> Optional[int]:
    """The start of the row 'place' of the way down the view: 0 for the
    top, 1 for the bottom."""
    layout = self._laidOut()
    if layout is None or not layout.lineCount():
      return None
    shown = self.rowsInView(layout, self.paintView.height)
    last = min(self.scrollTop + shown - 1, layout.lineCount() - 1)
    row = self.scrollTop + int((last - self.scrollTop) * place)
    return layout.lineAt(row).textStart()

  def _motionViewTop(self, count: int) -> Optional[int]:
    return self._viewRow(0.0)

  def _motionViewMiddle(self, count: int) -> Optional[int]:
    return self._viewRow(0.5)

  def _motionViewBottom(self, count: int) -> Optional[int]:
    return self._viewRow(1.0)

  def _pageBy(self, rows: int) -> None:
    """Scroll 'rows' rows and take the cursor the same number of rows
    along, as Ctrl+D and Ctrl+F do."""
    layout = self._laidOut()
    if layout is None or not layout.lineCount():
      return
    lastRow = layout.lineCount() - 1
    row = self.cursorRow(layout)
    x, _ = layout.lineAt(row).cursorToX(self.cursor)
    self.scrollTop = min(max(self.scrollTop + rows, 0), lastRow)
    target = min(max(row + rows, 0), lastRow)
    self.cursor = layout.lineAt(target).xToCursor(x)

  def _scrollRowDown(self, count: int) -> None:
    self.scrollBy(count)

  def _scrollRowUp(self, count: int) -> None:
    self.scrollBy(-count)

  def _halfViewDown(self, count: int) -> None:
    self._pageBy(max(self._rowsShown() // 2, 1))

  def _halfViewUp(self, count: int) -> None:
    self._pageBy(-max(self._rowsShown() // 2, 1))

  def _viewDown(self, count: int) -> None:
    self._pageBy(max(self._rowsShown() - 2, 1) * count)

  def _viewUp(self, count: int) -> None:
    self._pageBy(-max(self._rowsShown() - 2, 1) * count)

  def _scrollCursorTo(self, place: float) -> None:
    """Scroll so the cursor's row is 'place' of the way down the view."""
    layout = self._laidOut()
    if layout is None:
      return
    shown = self.rowsInView(layout, self.paintView.height)
    row = self.cursorRow(layout)
    self.scrollTop = max(row - int((shown - 1) * place), 0)

  def _scrollCursorTop(self, count: int) -> None:
    self._scrollCursorTo(0.0)

  def _scrollCursorMiddle(self, count: int) -> None:
    self._scrollCursorTo(0.5)

  def _scrollCursorBottom(self, count: int) -> None:
    self._scrollCursorTo(1.0)

  # \___________________
  #  Operators      ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _linesSpan(self, count: int) -> Span:
    """The 'count' whole lines from the cursor's, as 'dd' takes them."""
    first = self.lineNumberAt(self.cursor)
    last = min(first + max(count, 1) - 1, self.lineCount() - 1)
    return first, last, True

  def _motionSpan(
      self,
      operator: str,
      motion: Motion,
      count: int,
  ) -> Optional[Span]:
    """
    The span an operator covers with 'motion': whole lines for a motion
    over lines, else the characters from the cursor to where it lands -
    the last one included for an inclusive motion. As in Vi, 'cw' changes
    to the end of the word, and 'w' stops at the end of the line.
    """
    key, char = motion
    onWord = self.cursor < len(self.text) and self.text[self.cursor] != ' '
    if operator == 'c' and key in ('w', 'W') and onWord:
      motion = ('e' if key == 'w' else 'E', char)
    target = self._motionTarget(motion, count)
    if target is None:
      return None
    kind = self._motionKind(motion)
    if kind == _LINES:
      lines = (self.lineNumberAt(self.cursor), self.lineNumberAt(target))
      return min(lines), max(lines), True
    start, end = min(self.cursor, target), max(self.cursor, target)
    if kind == _INCLUSIVE:
      end = min(end + 1, len(self.text))
    lineEnd = self.lineEndAt(self.cursor)
    if motion[0] in ('w', 'W') and end > lineEnd > start:
      end = lineEnd
    return start, end, False

  def _cutInto(self, start: int, end: int) -> None:
    """Cut the text from 'start' to 'end' into the register, as
    characters, remembering the state before for 'undo'."""
    if start < end:
      self.remember()
      self.keep(self.splice(start, end, ''), False)

  def _cutLines(self, first: int, last: int, keepOne: bool) -> None:
    """
    The '_cutLines' method cuts the lines 'first' to 'last' into the
    register as whole lines. With 'keepOne' an empty line stays in their
    place, for 'cc' to type on; otherwise cutting the last line takes the
    line break before it, so no empty line is left behind.
    """
    start = self.startOfLine(first)
    end = self.lineEndAt(self.startOfLine(last))
    lines = '%s\n' % self.text[start:end]
    self.remember()
    if keepOne:
      self.splice(start, end, '')
    elif end < len(self.text):
      self.splice(start, end + 1, '')
    elif start:
      self.splice(start - 1, end, '')
      start = self.lineStartAt(start - 1)
    else:
      self.splice(start, end, '')
    self.keep(lines, True)
    if keepOne:
      self.cursor = start
    else:
      start = min(start, len(self.text))
      self.cursor = viMotions.firstNonBlank(self.text, start)

  def _operateDelete(self, start: int, end: int, lines: bool) -> None:
    if lines:
      return self._cutLines(start, end, False)
    self._cutInto(start, end)

  def _operateChange(self, start: int, end: int, lines: bool) -> None:
    if lines:
      self._cutLines(start, end, True)
    else:
      self.remember()
      self.keep(self.splice(start, end, ''), False)
    self.mode = ViMode.INSERT

  def _operateYank(self, start: int, end: int, lines: bool) -> None:
    if not lines:
      self.keep(self.text[start:end], False)
      self.cursor = start
      return
    first = self.startOfLine(start)
    last = self.lineEndAt(self.startOfLine(end))
    self.keep('%s\n' % self.text[first:last], True)
    if start < self.lineNumberAt(self.cursor):
      self.cursor = first

  # \_____________________
  #  Simple commands  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _deleteChars(self, count: int) -> None:
    end = min(self.cursor + count, self.lineEndAt(self.cursor))
    self._cutInto(self.cursor, end)

  def _deleteCharsBefore(self, count: int) -> None:
    start = max(self.cursor - count, self.lineStartAt(self.cursor))
    self._cutInto(start, self.cursor)

  def _deleteToLineEnd(self, count: int) -> None:
    self._cutInto(self.cursor, self.lineEndAt(self.cursor))

  def _changeToLineEnd(self, count: int) -> None:
    self._operateChange(self.cursor, self.lineEndAt(self.cursor), False)

  def _substituteChars(self, count: int) -> None:
    end = min(self.cursor + count, self.lineEndAt(self.cursor))
    self._operateChange(self.cursor, end, False)

  def _substituteLines(self, count: int) -> None:
    self._operateChange(*self._linesSpan(count))

  def _yankLines(self, count: int) -> None:
    self._operateYank(*self._linesSpan(count))

  def _replaceChars(self, char: str, count: int) -> None:
    """'r' replaces 'count' characters under the cursor with 'char', and
    does nothing if the line holds not so many."""
    end = self.cursor + count
    if not self.accepts(char) or end > self.lineEndAt(self.cursor):
      return
    self.remember()
    self.splice(self.cursor, end, char * count)
    self.cursor = end - 1

  def _joinLines(self, count: int) -> None:
    """'J' joins the cursor's line with the next, 'count' lines in all,
    with a space between them where neither side has one."""
    self.remember()
    for _ in range(max(count - 1, 1)):
      end = self.lineEndAt(self.cursor)
      if end >= len(self.text):
        break
      after = end + 1
      while after < len(self.text) and self.text[after] in ' \t':
        after += 1
      emptyLine = True if end == self.lineStartAt(end) else False
      nextEmpty = True if self.lineEndAt(after) == after else False
      spaced = end and self.text[end - 1] == ' '
      gap = '' if emptyLine or nextEmpty or spaced else ' '
      self.splice(end, after, gap)
      self.cursor = end

  def _putAfter(self, count: int) -> None:
    """'p' puts the register after the cursor's character, or whole
    lines below the cursor's line."""
    block = self.register * count
    if not block:
      return
    self.remember()
    if self.registerLines:
      end = self.lineEndAt(self.cursor)
      if end >= len(self.text):
        self.splice(end, end, '\n%s' % block[:-1])
      else:
        self.splice(end + 1, end + 1, block)
      self.cursor = end + 1
      return
    at = min(self.cursor + 1, self.lineEndAt(self.cursor))
    self.splice(at, at, block)
    self.cursor = at + len(block) - 1

  def _putBefore(self, count: int) -> None:
    """'P' puts the register before the cursor, or whole lines above the
    cursor's line."""
    block = self.register * count
    if not block:
      return
    self.remember()
    if self.registerLines:
      start = self.lineStartAt(self.cursor)
      self.splice(start, start, block)
      self.cursor = start
      return
    at = self.cursor
    self.splice(at, at, block)
    self.cursor = at + len(block) - 1

  # \_______________________
  #  Changing the mode  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def enterInsert(self, ) -> None:
    """The 'enterInsert' method enters 'INSERT' mode. All the typing
    until Esc is undone as one."""
    self.remember()
    self.mode = ViMode.INSERT

  def leaveInsert(self, ) -> None:
    """The 'leaveInsert' method returns to 'NORMAL' mode, the cursor
    stepping back onto the last character typed, as in Vi."""
    self.mode = ViMode.NORMAL
    if self.cursor > self.lineStartAt(self.cursor):
      self.cursor = self.cursor - 1
    self._settle()

  def _insertHere(self, count: int) -> None:
    self.enterInsert()

  def _insertAfter(self, count: int) -> None:
    self.cursor = min(self.cursor + 1, self.lineEndAt(self.cursor))
    self.enterInsert()

  def _insertAtFirstNonBlank(self, count: int) -> None:
    self.cursor = viMotions.firstNonBlank(self.text, self.cursor)
    self.enterInsert()

  def _insertAtLineEnd(self, count: int) -> None:
    self.cursor = self.lineEndAt(self.cursor)
    self.enterInsert()

  def _openBelow(self, count: int) -> None:
    self.enterInsert()
    end = self.lineEndAt(self.cursor)
    self.splice(end, end, '\n')

  def _openAbove(self, count: int) -> None:
    self.enterInsert()
    start = self.lineStartAt(self.cursor)
    self.splice(start, start, '\n')
    self.cursor = start

  def _openCommandLine(self, prompt: str) -> None:
    self.__command_prompt__ = prompt
    self.__command_line__ = ''
    self.mode = ViMode.COMMAND

  def _enterCommand(self, count: int) -> None:
    self._openCommandLine(':')

  def _enterSearchForward(self, count: int) -> None:
    self._openCommandLine('/')

  def _enterSearchBackward(self, count: int) -> None:
    self._openCommandLine('?')

  def _leaveCommand(self, ) -> None:
    self.__command_prompt__ = None
    self.__command_line__ = None
    self.mode = ViMode.NORMAL

  # \___________________
  #  Ex commands    ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def execute(self, command: str) -> None:
    """
    The 'execute' method runs the ex command 'command', as written after
    ':'. A line number goes to that line, '$' to the last. A command it
    does not know leaves a message on the status line.
    """
    command = str.strip(command)
    if command == '$':
      command = str(self.lineCount())
    if command and all(char in _DIGITS for char in command):
      start = self.startOfLine(int(command) - 1)
      self.cursor = viMotions.firstNonBlank(self.text, start)
      return self._settle()
    name = self.__ex_commands__.get(command, None)
    if name is None:
      return self._message('Not an editor command: %s' % command)
    getattr(self, name)()

  def _exWrite(self, ) -> None:
    self.writeRequested.emit()

  def _exQuit(self, ) -> None:
    if self.modified:
      info = 'No write since last change (add ! to override)'
      return self._message(info)
    self.quitRequested.emit()

  def _exWriteQuit(self, ) -> None:
    self._exWrite()
    self._exQuit()

  def _exForceQuit(self, ) -> None:
    self.modified = False
    self.quitRequested.emit()

  def _nextTab(self, count: int) -> None:
    self.tabStepRequested.emit(count)

  def _previousTab(self, count: int) -> None:
    self.tabStepRequested.emit(-count)

  def _exNewTab(self, ) -> None:
    self.newTabRequested.emit()

  def _exNextTab(self, ) -> None:
    self.tabStepRequested.emit(1)

  def _exPreviousTab(self, ) -> None:
    self.tabStepRequested.emit(-1)

  def _writeAndQuit(self, count: int) -> None:
    """'ZZ' writes and quits, as ':x' does."""
    self._exWriteQuit()

  def _quitWithoutWriting(self, count: int) -> None:
    """'ZQ' quits without writing, as ':q!' does."""
    self._exForceQuit()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _handleKey(self, event: QKeyEvent) -> bool:
    """
    The '_handleKey' method reads one key as the mode says, recording the
    keys of a change as it goes, for '.' to replay.
    """
    if self.mode is ViMode.INSERT:
      self._record(event)
      handled = self._insertKey(event)
      if self.mode is ViMode.NORMAL:
        self._finishRecord()
      return handled
    if self.mode is ViMode.COMMAND:
      return self._commandKey(event)
    if not self.pendingKeys:
      self._startRecord()
    self._record(event)
    return self._normalKey(event)

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """
    The vidget reads each key as its mode says. A key the mode has no
    use for is passed on, so shortcuts and menus keep working.
    """
    self.__status_message__ = None
    handled = self._handleKey(event)
    self.update()
    if handled:
      return event.accept()
    return VidgetBase.keyPressEvent(self, event)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click puts the cursor where it lands in any mode, giving up a
    command being written."""
    if self.mode is ViMode.COMMAND:
      self._leaveCommand()
    self.__pending_keys__ = None
    self._dropRecord()
    VidgetBase.mousePressEvent(self, event)
    self._settle()
