# worQt — state of the project & next-larp plan

A handoff doc for a fresh context window. It describes (1) what worQt is and how
it is built, (2) the current state of every subpackage with emphasis on the
recently-built data layer, (3) the conventions you must follow, (4) the testing
harness, and (5) the plan for the next 'larp' example (a text editor) and the
abstractions we expect it to surface.

Quote identifiers with 'single quotes' in code docstrings/comments, never with
backticks — this is a hard house style. (Markdown code fences below are fine;
they are code, not quoted identifiers.)

---

## 0. The method (read this first)

worQt extends the 'worktoy' library with utilities for building Qt for Python
(PySide6) desktop apps. **The abstractions are the product; an example app is
only the vehicle.** We build a throwaway example, let it press on the core,
lift whatever generalises into real worQt, then delete the example.

This already happened once: a structural-CAD example ('larping') drove out the
whole data layer, the settings system, the value-edit widgets and the qtest
harness. That example was then removed in PR #1 (merged to 'main'), keeping the
extracted core. We are now about to do it again with a deliberately *smaller*
example so we stay focused on lifting abstractions rather than polishing an app.

**Discipline rule:** the moment the example makes you hand-wire something the
CAD example also hand-wired (a dirty flag, a save-guard, a title star, a
list/view sync), stop and lift it into core worQt instead of building it in the
example.

---

## 1. Environment & ground rules

- Published package 'worQt'; source under 'src/worQt'. Run from the repo root.
- 'worktoy' is an external dependency (currently 1.0.0-rc11) — do not vendor or
  reimplement it. Use only these parts of it: 'worktoy.core.Object',
  'worktoy.desc', 'worktoy.dispatch', 'worktoy.mcls'.
- Always prefix Python invocations with 'PYTHONDONTWRITEBYTECODE=1'.
- **Do not run the test suite** — the user runs tests and hands execution back.
  You may 'py_compile' to syntax-check, but do not run pytest/the qtest suite.
- pytest has been removed from this project; the suite runs through the in-house
  'worQt.qtest' harness (see §4).

### Coding conventions (enforced)
- Two-space indentation, max line length 77.
- 'camelCase' for variables/functions, 'PascalCase' for classes.
- Identifiers in docstrings/comments in 'single quotes', never backticks.
- Pipe unions ('int | None') in real annotations, not 'Optional[...]'. But
  'param: T = None' is acceptable as-is — do not rewrite it to 'T | None'.
- "True if x else False" / "1 if y else 0" ternaries are deliberate — do not
  collapse to 'bool(x)'.
- 'from __future__ import annotations' at the top of every module; heavy or
  typing-only imports under 'if TYPE_CHECKING:  # pragma: no cover'.
- Never use 'exec'/'eval'/'__import__' for dynamic codegen — use 'importlib',
  'getattr', or registries.
- **Positional args only** — no kwargs, even for AttriBox/Qt constructors.
- Never name a novel backing dunder with a single word ('__value__'); qualify
  it ('__setting_value__') to avoid future official-Python collisions.
- Follow the section-banner class-body layout in
  'src/worQt/_class_body_template.py' (NAMESPACE / GETTERS / SETTERS / …).

### worktoy descriptor idioms used everywhere
- 'AttriBox[T](*args)' — lazily-built, typed attribute; built 'T(*args)' on
  first read and cached. Use for static, per-class typing.
- 'Field' + private slots — use when a value's type/shape is per-instance or
  runtime; back it with a '__snake_named__' private slot and '@x.GET'/'@x.SET'.
- The recursion-guard getter pattern: '_create*' sets the slot, '_get*' calls
  it then re-reads via '_get*(_recursion=True)' (raises 'RecursionError' if the
  create didn't take).
- Sentinels: 'THIS' (instance at access time / Self in overloads), 'OWNER'
  (owner class), 'DESC' (the descriptor), 'DELETED', 'METACALL', 'ARGS'.
- 'AttriBox[T](THIS)' ALWAYS builds 'T(owner)' — it never aliases the owner.
  So to host a nested widget you box a *dedicated subclass* the owner does not
  inherit (see 'Container' in §3).
- '@overload(...)' constructors: stack '@overload(types)' on '__init__'; the
  metaclass compiles them into a runtime dispatcher. First-registered wins; no
  specificity ranking.

### Qt construction constraint (load-bearing)
Constructing a 'QObject' (any worQt class that mixes in a Qt type) **before a
'QApplication' exists hard-crashes the interpreter (segfault), not raises.** So:
- Keep QObject construction out of class bodies and import time.
- 'MixinBase.__set_name__' raises on purpose, to stop a QObject subclass being
  used as a class variable.
- Build all widgets/layouts lazily — in 'show()' / 'build()', never in
  '__init__'.
- worQt Qt-construction rule: widgets and layouts are boxed in 'AttriBox';
  'THIS' goes on widgets only, never layouts; a nested layout gets a dedicated
  host widget ('Container') added via 'addWidget'.

---

## 2. The metaclass fusion ('src/worQt/mixin') — the core idea

Qt classes are built by Shiboken's metaclass ('type(Shiboken.Object)'); worktoy
classes by 'worktoy.mcls.BaseMeta'. You cannot subclass both a Qt type and a
worktoy 'BaseObject' directly — Python rejects the metaclass conflict. 'mixin'
fuses them:

- '_Shiboken(_ObjectType)' — an intermediate metaclass. worktoy's
  'AbstractMetaclass' expects names matching the '__class*__' pattern to resolve
  to the 'METACALL' sentinel instead of raising 'AttributeError'; Shiboken does
  not honour that, so '_Shiboken.__getattr__' returns 'METACALL' for that
  pattern and otherwise defers.
- 'MixinMeta(_Shiboken, BaseMeta)' — the fused metaclass. '__new__' routes
  class creation through '_ObjectType.__new__' with the compiled namespace.
- 'MixinSpace(BaseSpace)' — the namespace ('__prepare__' returns it). Currently
  a thin subclass, reserved as the MixinMeta-specific hook point.
- 'MixinBase(BaseObject, metaclass=MixinMeta)' — the base users inherit from to
  get worktoy descriptor/overload machinery on a Qt class. Also exposes
  'app'/'src'/'root'/'etc'/'eps' Fields and the 'fieldOwner'/'fieldName'/
  'fieldBox' AttriBox-introspection helpers.

The '__init__.py' import order ('MixinSpace' → 'MixinMeta' → 'MixinBase') and
the MRO ordering are load-bearing; preserve both.

---

## 3. Current subpackages (the extracted core)

### 'app' — linear application chain
- 'ApplicationMixin(QApplication, MixinBase)' — the actual fusion point.
- 'AbstractApplication(ApplicationMixin)' — owns the lazily-built, app-scoped
  handles: 'returnCode', 'splash', 'window', 'settings'. A concrete app sets
  '__window_class__' (and optionally '__settings_class__'); construction, type
  checks and access live here. Overrides Qt's 'notify()' to funnel slot/event
  exceptions into 'handleException()' (a no-op hook; only 'Exception' is caught,
  'KeyboardInterrupt'/'SystemExit' propagate). 'self.app.window' /
  'self.app.settings' reach these from anywhere via 'MixinBase.app'.
- 'App(AbstractApplication)' — concrete, context-manager. '__window_class__ =
  MainWindow'. Usage:
  ```python
  with App(*sys.argv) as app:
    app.window.show()
  ```
  '__exit__' runs 'self.exec()' only on a clean exit (no exception in the body).

### 'window' — 'MainWindow(QMainWindow, MixinBase)'
A generic demo window; widgets boxed 'AttriBox[...](THIS)', layouts never
'THIS', UI built lazily in 'show()' → 'initUi()'. Proof the fusion generalises
beyond QApplication. 'python -m worQt' opens this via 'App'.

### 'widgets' — generic, reusable custom widgets
- 'BaseWidget(QWidget, MixinBase)'.
- 'Container(BaseWidget)' — a plain host for a nested layout. Exists because
  'AttriBox[BaseWidget](THIS)' on a 'BaseWidget'-derived owner would alias the
  owner; 'Container' is a type the owner does not inherit, so it builds a real
  child.
- 'StringValueEdit' / 'BoolValueEdit' / 'NumberValueEdit' + the 'valueEditor'
  factory — type-specific scalar editors (uniform 'value' Field, 'build()',
  'connectChanged(slot)').
- 'SettingsDialog(QDialog, MixinBase)' — VLC-style, model-driven editor over a
  'Settings' object; tabs on the left, per-setting editors on the right,
  Ok/Apply/Cancel/Restore-defaults; Apply reflects to the model and its file.

### 'settings' — Qt-free settings system
- 'Setting[T](default)' ('BaseDescriptor') — one named, typed value with label
  /description; assigning coerces to T.
- 'SettingsTab' — a named pane of settings ('define(name, default)' infers T).
- 'Settings' — tabs + the file they persist to (OS config path via
  '_config_path'); saved as a tiny in-house TOML ('_toml'), one '[tab]' table
  per pane. 'load' over defaults at startup, 'save' writes back.

### 'data' — the document/field/file layer (THE recent work — see §3a)

### 'qtest' — the in-house Qt test harness (see §4)

---

## 3a. The data layer in depth ('src/worQt/data')

This is what the next larp must exercise. All pure 'worktoy' ('BaseObject'),
no Qt — it builds and serialises without a 'QApplication'.

### Documents
'AbstractDocument(BaseObject)':
- Two class-level field registries: '__single_fields__' (name → SingleField)
  and '__array_fields__' (name → ArrayField). Fields register themselves at
  class creation via '__set_name__' (single vs array registry).
- 'mainFile = AttriBox[MainFile]()' — the document's file; 'mainDir' Field
  delegates to it.
- 'save()' → 'mainFile.save(self._encodeData)'; 'load()' →
  'mainFile.load(self._decodeData)'.
- '_encodeData(io)'/'_decodeData(io)' walk **both** registries and 'json.dump'/
  'json.load' a single dict '{fieldName: encoded}'. Single fields round-trip
  through 'field.__set__'; **array fields are written straight to the field's
  private slot** on decode (because 'ArrayField' blocks '__set__').
- Overloaded constructors: '__init__(str)' (a directory) and '__init__()'.

### Fields
'AbstractField(BaseDescriptor[T], metaclass=BaseMeta)':
- Holds the element type and an encoder/decoder contract **resolved by name
  against the owning document**: '@field.setEncoder def _encX(self, value)' just
  records 'func.__name__'; at I/O time the field does 'getattr(owner, key)'. So
  a subclass overrides serialisation by redefining the method — no re-decoration.
- '__set_name__' calls 'super().__set_name__(...)' to reach worktoy's
  'Object.__set_name__' bookkeeping (records '__field_owner__'/'__field_name__');
  registration is left to the concrete subclass. **Do not make '__set_name__'
  abstract** — the 'super()' hop is the only path to that bookkeeping and the
  subclasses route through it.
- Clone-on-subclass: '__get__' when 'docType is not owner' clones the field,
  re-registers it on the subclass, and returns the clone — so each subclass
  gets its own descriptor.

'SingleField(AbstractField, Generic[T])' — one value; '__call__(value)' sets the
fallback default; 'encode'/'decode' call the document-resolved codec.

'ArrayField(AbstractField, Generic[T])' — any number of items of an
'AbstractItem' subtype:
- '__class_getitem__' rejects non-'AbstractItem' element types
  ('SubclassException').
- '__call__' is a **guard, not a value-taker**: arrays start empty on every
  document and take **no default items** (default items would be shared mutable
  state across documents). 'ArrayField[T]' / 'ArrayField[T]()' declare the
  field; 'ArrayField[T](item)' raises.
- 'encode'/'decode' map the document's **per-item** codec across the array
  (encode → JSON-native list; decode → rebuilt 'ArrayLike', type-guarded, with
  owner stamped).
- '__instance_set__' raises ("Do not override!"); you mutate via
  'append'/'extend', which build a fresh 'ArrayLike', '_adopt' the items (stamp
  '__owning_field__'/'__owning_document__'), store it, and call 'notifyChange'.
- 'notifyChange(doc)' is **a no-op sink** — the documented extension point a
  real app wires to a dirty flag / undo / UI refresh. **Nothing consumes it
  yet.**

'ArrayLike(tuple, Generic[T])' — immutable container that knows its
'owningField'/'owningDocument'; 'append'/'extend' write through to the field
(so 'doc.items.append(x)' works).

### Items & change notification
'AbstractItem(BaseObject, metaclass=ItemMeta)':
- '__owning_field__'/'__owning_document__' slots; 'notifyChange()' forwards to
  'field.notifyChange(doc)' when owned, no-ops when not (a standalone item is
  still mutable). Identity-hashable via the default 'object' identity (no
  explicit '__hash__'/'__eq__' — that would just re-implement the default).

'NotifyBox(AttriBox, Generic[T])' — an 'AttriBox' whose 'hookOnSet' fires
'instance.notifyChange()' after every write. **Item state must be declared with
'NotifyBox', not plain 'AttriBox'.**

**Enforcement (metaclass):** 'ItemMeta(BaseMeta)' → 'ItemSpace(BaseSpace)' with
'ItemSpaceHook(AbstractSpaceHook)'. Its 'setItemPhase' raises 'TypeError' at
class creation if a class-body value is an 'AttriBox' that is not a 'NotifyBox'.
So you literally cannot declare item state with a non-notifying box.

The full live chain:
'item.x = 5' → 'NotifyBox.hookOnSet' → 'item.notifyChange()' → (if owned)
'field.notifyChange(doc)' → no-op sink (awaiting a consumer).

### Files
'AbstractFile(BaseObject)' — runs a caller callback against an open handle and
owns the open/close. 'save(cb, e=None)' writes atomically (write to
'<path>.tmp', 'os.replace', remove tmp on failure; optional error callback 'e');
'load(cb, e=None)' reads. 'filePath' is abstract.
- 'MainFile(AbstractFile)' — 'dirPath' (defaults to home, must be absolute),
  'fileName' (defaults to the first free 'untitled_NNN.json'), 'filePath' (join;
  assigning splits it back into dir + name).
- 'LocalFile(AbstractFile)' — a member file that **derives its directory from a
  'mainFile'** (read-only 'dirPath'), keeps a bare leaf name, and may only be
  renamed within the owned directory. So moving the project (its 'mainFile')
  moves every member. **Built but completely unexercised by any app yet.**

### Serialization format note (important for the next larp)
'AbstractDocument' **hardcodes JSON** ('json.dump'/'json.load' in
'_encodeData'/'_decodeData'); per-field codecs return JSON-native values. A
plain-text document wants raw text, not '{"body": "..."}'. So the very first
thing a text editor will crack open is "document serialization format should be
pluggable" (a strategy, not a baked-in 'json' call). Treat that crack as the
prize, not an annoyance.

### What the data layer's tests cover (all green)
'tests/test_data/': 'test_document' (SingleField round-trip), 'test_array_field'
(ArrayField/ArrayLike basics), 'test_array_item' (NotifyBox enforcement, the
no-default guard, the notify chain, array save/load round-trip), 'test_main_file'
, 'test_local_file', 'test_field_inheritance' (clone-on-subclass). Base class
'DataTest(BaseTest)' provides a cleared temp dir via 'tests/_temp_dir.TempDir'.

---

## 4. The testing harness ('src/worQt/qtest') — and how to run it

Two execution modes:
- Plain 'BaseTest'/'TestCase' (no Qt) run **in-process** ('AppTestRun._runPlain'
  via 'unittest').
- 'AppTest' subclasses (need a 'QApplication') run **one per child process**
  ('AppTestRun._runPopen' → 'python -m worQt.qtest <module>'), with a SIGKILL
  deadline, so a hang/segfault becomes a reported status, not a frozen terminal.

Authoring: subclass 'AppTest' (metaclass 'MetaTest' collects every
'test*'/'run*' method via 'SpaceTest'/'HookTest'); 'runTest()' creates a shared
'QApplication' and pumps each method on a 'QTimer'. Build Qt inside test methods
(there is a live exec loop); use 'QTest.qWait' to see windows; no naked event
loops or modal dialogs (drive handlers directly / monkeypatch
'QFileDialog'/'QMessageBox'); a raised exception = failure.

Discovery ('AppTestSuite'): walks 'tests/' for 'run*'/'test*' module files
(without importing), resolves each to its single 'Run*'/'Test*' class on demand.
'_getSrcDir' walks up for the 'tests/' folder and falls back to the cwd if none
is found above the package.

Run commands (the **user** runs these):
```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest                       # whole suite
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest tests.test_data.test_array_item   # one class
```

**Coverage is deferred** (the subprocess-per-AppTest model makes it non-trivial).
When we return to it, the chosen approach is: run the suite under
'coverage run --parallel-mode', and have 'AppTestRun' spawn each child as
'coverage run --parallel-mode -m worQt.qtest <module>' (gated by an env flag),
then 'coverage combine' — keeps the per-class isolation, no 'process_startup'
hook baked into '__main__'. (Caveat: a SIGKILL'd/segfaulted child writes no
coverage data.)

---

## 5. Git / repo state

- On 'main' at the PR-#1 merge ('Merge pull request #1 from AsgerJon/data-layer')
  — cad removed, the data/qtest/settings/widgets core kept.
- Dead local branches to prune when ready: 'cad', 'cad_off', 'data-layer',
  'reset6/7/8'.
- Repo noise worth a future sweep (not urgent): 'htmlcov/' (stale pytest-cov
  output), 'work_test_runner/' (an orphaned, non-package generic runner —
  possibly a 'worktoy' stray like the removed 'coverage_test.sh'), and root
  scratch ('main.py', 'yolo.py', 'run_tests.py').

### Known gaps / deferred (not blocking)
- Coverage testing (see §4).
- 'AbstractFile' error-callback branches, 'AbstractDocument.mainDir'/the
  'overload(str)' constructor, and scattered guard branches are untested
  (low value).
- 'LocalFile'/'MainFile' multi-file project model is built but unexercised.
- The 'notifyChange' sink is a no-op awaiting a consumer.

---

## 6. The plan — next larp: a minimal text editor

**Why a text editor:** small enough not to become a rabbit hole (the real risk),
which keeps focus on lifting abstractions rather than polishing an app.

**Honest scope caveat:** a straight text editor barely touches the array/item
half of the data layer (its content is basically one 'SingleField[str]'). That
is fine — examples are targeted. A *second*, list-shaped larp later (todo /
contacts) should beat on 'ArrayField'/'AbstractItem'/'NotifyBox' and the
'MainFile'/'LocalFile' multi-file model.

**Abstractions we expect this larp to surface (the actual deliverables):**
1. **Pluggable document serialization** — the JSON-hardcoding crack in
   'AbstractDocument' (text wants raw bytes/str, not JSON). Likely the first and
   juiciest lift.
2. **Document-window controller** — New / Open / Save / Save-As + the
   unsaved-changes guard. CAD hand-wired all of this; generalise it.
3. **dirty → window title ('*')** — the first real consumer of the
   'notifyChange' chain (and/or Qt's 'textChanged').
4. **'MainFile' for real** — untitled-name generation, atomic save; first
   actual use of it by an app.
5. **single 'SingleField' ↔ widget two-way binding** — we currently bind
   widgets to *settings*, not to *document fields*.

**Setup:** an isolated 'src/worQt/<name>' package (name undecided — 'edit'?
'notepad'? 'scratchpad'?) on a **new branch off 'main'**; core never imports it;
strip it at the end, keeping whatever generalised.

**Minimal skeleton to start:** a 'TextDocument(AbstractDocument)' (a body field
+ a file) and a window ('QMainWindow' + 'MixinBase') with a 'QPlainTextEdit'
central widget and a File menu (New/Open/Save/Save-As/Quit), title-with-dirty-
star, and the unsaved-changes guard. Resist tabs, find/replace, syntax
highlighting — that is the rabbit hole.

**The loop:** build the bare editor → each time you reach for something CAD also
hand-wired, stop and lift it into core worQt → keep the example dumb → at the
end, delete the example and keep the abstractions.
