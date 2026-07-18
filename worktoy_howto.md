# worktoy — how to use it (and why your Python instincts will betray you)

This is a survival guide for working on **worQt**, which is built on **worktoy**.
worktoy is a pinned, battle-tested 1.0 dependency; it is **not fragile** — if
something behaves oddly, suspect your own usage, not worktoy.

> **The single most important rule.** worktoy is built on custom metaclasses, a
> custom class-body namespace, and a *contextual* descriptor protocol. Almost
> every mechanism looks like ordinary Python and **is not**. Do **not** reason
> about a worktoy construct from stdlib intuition. When you touch one, open the
> real file and, if behaviour matters, prove it with a test or a 5-line probe —
> never from memory or from this document.

**Where the source lives (open it):**
`/home/AsgerJon/miniforge3/envs/worqt_env/lib/python3.14/site-packages/worktoy/`

Package dependency order (each layer imports only from earlier ones):
`utilities → waitaminute → core → dispatch → desc → mcls → lorem_ipsum →
keenum → ezdata → work_test`.

---

## 1. The mental-model reset

A worQt value class is either `class Foo(BaseObject):` or
`class Foo(metaclass=BaseMeta):`. That declaration changes the rules:

- `__prepare__` returns a **custom namespace object** (`BaseSpace`, a `dict`
  subclass), not a plain dict. It runs **space hooks** on every `__setitem__` /
  `__getitem__` *while the class body executes*. Hooks can claim, rewrite, or
  reject an assignment before it ever reaches the class dict.
- The metaclass routes builtin operations (`str(cls)`, `iter(cls)`,
  `cls(...)`, `isinstance`, attribute access, …) to **class-level hooks** named
  `__class_str__`, `__class_iter__`, `__class_call__`, `__class_instancecheck__`,
  `__class_getattr__`, `__class_init__`, etc. To customise class behaviour you
  define one of those hooks — you do **not** write a metaclass method. A hook
  left undefined resolves to the `METACALL` sentinel and falls back to `type`.
- `__class_init__(cls, name, bases, space, **kw)` runs *after* the class exists —
  the place to finalise a class.

Consequence: reading a class body top-to-bottom does not tell you what the class
does. The namespace hooks and the metaclass are doing invisible work.

---

## 2. Descriptors (`worktoy.desc`) — the core idiom

### `Field()` — property-like, but accessors resolve **by name at runtime**

```python
class Foo(BaseObject):
  __x__ = None                    # private backing slot
  x = Field()                     # public descriptor

  @x.GET
  def _getX(self) -> int: ...
  @x.SET
  def _setX(self, value) -> None: ...
  @x.preSet
  def _preSetX(self, value) -> None: ...   # also: onGet, preGet, onSet, pre/onDelete
```

**The unconventional part:** the decorators record the *method name*, not the
function. At access time the accessor is looked up with
`getattr(type(instance), name)`. So a **subclass overrides an accessor simply by
redefining a method of the same name** — no re-decoration needed. (This is how
`FloatSampler` replaces `IntSampler`'s getters.) If you rename a getter in a
subclass, you silently break the field.

A `Field` with no `@x.GET` raises `AccessError` on read; with no `@x.SET`,
assignment raises `ReadOnlyError`.

### `AttriBox[T](*args)` — lazy, type-enforced attribute

```python
x = AttriBox[int](0)              # built as int(0) on first read, cached
mom = AttriBox[Parent](THIS)      # built as Parent(instance) per instance
```

- The subscript `[T]` fixes the field type; the call `(*args)` captures deferred
  constructor args. The value is built by `T(*args)` on **first read**, then
  cached on the instance.
- **Sentinels** in the args are substituted at access time:
  `THIS` → **the instance** the attribute is read from; `OWNER` → the owner
  **class**; `DESC` → the descriptor. So `AttriBox[Parent](THIS)` builds a fresh
  `Parent(instance)` for each instance — a **child object, never an alias** of
  the instance. (Verify in `desc/_attri_box.py`; the sentinel table is in
  `core/_object.py::getContextualSentinels`.)
- On assignment: a value already of type `T` is stored as-is; otherwise a
  lossless `typeCast(T, value)` is tried, then `T(value)` / `T(*value)`. A
  received **tuple splats** into positional args (except for the builtin
  containers). Numeric-tower casts are authoritative (setting `1.5` into an
  `AttriBox[int]` raises rather than truncating).
- **worQt house rule:** put widgets and layouts in `AttriBox`; use `THIS` on
  **widgets only, never layouts**; positional args only — **no kwargs**.

### Other descriptors
- `FixBox[T]` — write-once `AttriBox` (second write → `WriteOnceError`; the
  lazy first read counts as the write).
- `FastBox[T]` — lean, fast, **no** descriptor context, hooks, or sentinels.
- `Alias('name')` — re-expose another attribute under a second name.
- `SymbolicName`, `BaseDescriptor`.

### The contextual base (`core.Object`)

Inside an accessor, `self.instance` and `self.owner` resolve to the object /
class currently being accessed, via a **per-descriptor context stack** pushed by
`__get__`/`__set__`/`__delete__`. This is why accessors don't take `(instance,
owner)` args. It is **not thread-safe** and **not async-safe** (the stack is
shared across instances). Reading `self.instance` outside an active access
raises `WithoutException`. Deletion is signalled by storing the `DELETED`
sentinel, which the next read turns into `MissingVariable`.

---

## 3. Overload dispatch (`worktoy.dispatch`)

```python
@overload(int, int)
def __init__(self, x: int, y: int) -> None: ...
@overload(QPoint, strict=True)              # strict: no coercion, exact isinstance
def __init__(self, p: QPoint) -> None: ...
@overload(THIS)                             # THIS = the enclosing class
def __init__(self, other: Self) -> None: ...
@overload()
def __init__(self) -> None: ...
```

- Stack `@overload(...)` decorators on the same method name; the metaclass
  compiles them into one `Dispatcher`.
- Also: `@overload.fallback` (no-match catch-all), `@overload.finalize` (runs in
  a `finally` for every call), `overload.flex(*types)` (any argument order).
- `THIS` in a signature means the enclosing class; `strict=True` disables the
  flexible `typeCast` pass for that signature (use it for Shiboken/Qt types so
  the dispatcher never coerces them).
- **Dispatch order:** exact-type hash lookup → `isinstance` scan → `typeCast`
  scan; **first-registered wins** among overlapping matches. Register against the
  **exact concrete types** callers pass — abstract/union signatures force the
  slow O(N) scan.
- `flexCall`: plain class-body functions are wrapped so they **silently truncate
  excess positional arguments**. This is why an accessor declared `def
  _getX(self)` can be invoked with extra args and not raise — do not "fix" a
  signature mismatch you see; it is often deliberate.

---

## 4. Enumerations (`worktoy.keenum`) — frozen singletons

```python
class MouseButtonNum(KeeNum):
  LEFT = Kee[Qt.MouseButton](Qt.MouseButton.LeftButton)   # names MUST be UPPER_CASE
  ...
  def apply(self, font): ...        # PLAIN method — see warning below
```

- `KeeNum` + `Kee[T](value)`: members are declared UPPER_CASE (a lowercase name
  raises `KeeCaseException` at class creation). Members are **write-once, frozen
  singletons** — equality is identity; any attribute write raises
  `KeeWriteOnceError`.
- **Do NOT put `@overload` on a method of a KeeNum/KeeFlags member.** The
  dispatcher caches a bound method on the instance via `setattr`, which a frozen
  member rejects with `KeeWriteOnceError`. Use a **plain method** (see
  `FontWeightNum.apply`, `Alignum.apply`).
- Resolution: `cls('LEFT')` / `cls(value)` / `cls[index]`. Provide a
  `@classmethod __class_resolve__` hook for custom resolution (see the font
  enums).
- `KeeFlags`/`KeeFlag`: a bitmask enum that **materialises all 2**N** members at
  import**. N ≤ 8 is cheap; N ≥ 16 is a lot of memory — do not declare large
  flag enums casually.
- `KeeBox[EnumType](...)` — an `AttriBox` whose field type is an enum; it
  resolves its args to a member instead of constructing the value type.
- To *extend* the metaclass, subclass `KeeMeta` and use `YourMeta.keeNum` as the
  enumeration base — **not** plain `KeeNum` (which was built by vanilla
  `KeeMeta`, bypassing your customisation). See `KeeMetaMeta`.

---

## 5. `__set_name__` is not what you think

Because space hooks claim class-body entries, a descriptor's `__set_name__` may
**never fire** (the namespace intercepted it), or may **raise by design**:

- `Kee` / `KeeFlag`: `__set_name__` **raises** if reached — reaching it means the
  member was placed in a non-KeeNum class body.
- worQt's `MixinBase.__set_name__` **raises `RuntimeError`** — deliberately, to
  stop a `QObject` subclass being used as a class variable (constructing a
  `QObject` before a `QApplication` exists **segfaults** the interpreter, it does
  not raise). This is a load-bearing guard, not a bug.

Never assume `__set_name__` behaves conventionally for a worktoy descriptor.

---

## 6. Exceptions (`worktoy.waitaminute`) — fail fast, typed

worktoy raises a **specific typed exception** rather than returning a sentinel.
The ones you will see constantly:

- `TypeException(name, value, *types)` — wrong type (not for `None`; that is
  `MissingVariable`).
- `MissingVariable(instance, name, *types)` — an expected value was `None`.
- `VariableNotNone`, `SubclassException`, `UnpackException`.
- `desc`: `ReadOnlyError`, `ProtectedError`, `WriteOnceError`, `AccessError`,
  `WithoutException`.
- `control_flow.SkipSet` — **raise it from an `@x.preSet` hook to abort a
  redundant set** (value unchanged → don't fire `onSet`). This is a control
  signal, not an error; use it only for redundant-set elision.

---

## 7. Utilities you will reach for (`worktoy.utilities`)

`maybe(*args)` (first non-None) · `textFmt(...)` (collapse whitespace; `<br>` /
`<tab>` tokens) · `stringList`, `joinWords`, `wordWrap` · `unpack` ·
`typeCast(type, value)` · `resolveMRO` · `QuickDesc('__slot__')` (minimal
read-only descriptor) · `ExceptionInfo`.

---

## 7b. `moreworktoy` — the staging area (not worktoy)

`src/moreworktoy/` is **not part of worktoy** and lives in the worQt repo, not
the dependency. It is worQt's holding pen for utilities that may eventually be
promoted upstream into worktoy but aren't there yet. `moreworktoy.utilities`
re-exports everything from `worktoy.utilities` (`from worktoy.utilities import
*`) and appends its own, so callers get one import surface.

Right now it holds exactly one addition: **`errorFmt(exception)`** — a colourised
traceback formatter that renders each frame as a boxed source window with sticky
`def`/`class` headers and a red caret under the exact failing column span
(`co_positions`, 3.11+). The `worQt.qtest` runner uses it to print test failures
(`AppTest._runMethod`, `AppTestSuite`). It is plain Python — no worktoy
machinery, nothing unconventional.

Treat `moreworktoy` as provisional: import `errorFmt` from it, but don't build
deep dependencies on its shape — its purpose is to shrink as things graduate
into worktoy proper.

---

## 8. The idioms you must mirror (do not reinvent)

**Lazy getter + recursion guard** — the single most common pattern in the tree.
The `_recursion=True` kwarg is the one accepted keyword idiom (worQt is otherwise
positional-only):

```python
@x.GET
def _getX(self, **kwargs) -> T:
  if self.__x__ is None:
    if kwargs.get('_recursion', False):
      raise RecursionError            # build failed — fail loud, never loop
    self._createX()                   # or assign a fallback
    return self._getX(_recursion=True)
  if isinstance(self.__x__, T):
    return self.__x__
  raise TypeException('__x__', self.__x__, T)
```

**preSet SkipSet + onSet update:**

```python
@x.preSet
def _preSetX(self, value) -> None:
  if value == self.x:               # unchanged
    raise SkipSet                    # elide the write; onSet won't fire
@x.onSet
def _onSetX(self, value) -> None:
  self.update()                      # e.g. repaint
```

When adding a new field, **copy an existing getter/setter of the same shape**
rather than writing one from first principles — the recursion-guard and
type-guard details are easy to get subtly wrong.

---

## 9. Conventions (enforced — match them)

- Two-space indent, ≤ 77 columns; `camelCase` vars/functions, `PascalCase`
  classes.
- `'single quotes'` for identifiers in **docstrings/comments**, never backticks.
- `from __future__ import annotations` at the top of every module; typing-only
  imports under `if TYPE_CHECKING:  # pragma: no cover`.
- Pipe unions (`int | None`), not `Optional[...]`; but `param: T = None` stays
  as-is.
- Never `exec` / `eval` / `__import__` for dynamic codegen — use `importlib`,
  `getattr`, or registries.
- Positional args only (the `_recursion=True` guard is the accepted exception).

---

## 10. When in doubt

The worktoy source is on disk (path at the top). The **tests encode the true
semantics** — worktoy ships `work_test`, and worQt's own suite asserts the exact
behaviour of every descriptor and dispatch path. To answer "what does X actually
do", find the test that pins it or run a 5-line probe in the env; do **not**
reason it out from this document, and do **not** assume conventional Python. That
assumption is precisely what causes regressions here.
