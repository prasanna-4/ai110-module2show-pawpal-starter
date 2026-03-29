# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed four classes:

| Class | Responsibility |
|-------|---------------|
| `Task` | Holds a single care activity: description, time (HH:MM), frequency (once/daily/weekly), completion status, and due date. Also knows how to produce its own follow-up when completed. |
| `Pet` | Stores pet identity (name, species) and owns a list of `Task` objects. Exposes `add_task()` and `remove_task()`. |
| `Owner` | Aggregates multiple `Pet` objects. Provides `get_all_tasks()` to flatten the pet-task tree into a list of `(Pet, Task)` pairs used by the Scheduler. |
| `Scheduler` | The algorithmic brain. Receives an `Owner` reference and provides sorting, filtering, conflict detection, and recurring-task management without owning any data itself. |

`Task` and `Pet` were implemented as Python `@dataclass` objects to reduce boilerplate. `Owner` and `Scheduler` are plain classes because they carry meaningful behavioural logic.

**b. Design changes**

Yes, the design evolved in two ways:

1. **`due_date` added to `Task`**: The initial sketch left it off. Once I implemented recurring tasks I realized there was no way to calculate "tomorrow" without a concrete date anchor, so `due_date: date` with `timedelta` was added to `Task`.
2. **`(Pet, Task)` tuples instead of bare tasks**: Early drafts had `Scheduler` work with plain `Task` lists. When I implemented conflict warnings and filters that needed to name the responsible pet, I changed every method to work with `(Pet, Task)` pairs instead so the pet context is never lost.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:
- **Time** — every task has an HH:MM start time used for chronological sorting and conflict detection.
- **Due date** — only tasks due today appear in "Today's Schedule"; future recurring instances are hidden until relevant.
- **Completion status** — pending and completed tasks can be separated via `filter_by_status()`.
- **Frequency** — `once`, `daily`, and `weekly` tasks behave differently on completion: daily tasks reschedule for +1 day, weekly for +7 days, one-off tasks simply stay completed.

Time was the most important constraint because pet care tasks (medications, feeding windows) are strictly time-sensitive. Priority levels were considered but omitted from the base design to keep the data model simple.

**b. Tradeoffs**

**Exact-time conflict detection only.** The `detect_conflicts()` method flags two tasks as conflicting when they share an identical HH:MM start time. It does not check whether task durations cause a partial overlap (e.g., a 30-minute walk at 09:00 and a vet visit at 09:15 would not be flagged).

This tradeoff is reasonable because tasks in PawPal+ do not carry a duration field. Adding duration would require changes to `Task`, the UI, and the sort logic. For the most common real-world mistake — accidentally double-booking the same time slot — exact-time matching catches the error at very low complexity cost.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used at every phase:
- **Design brainstorming**: Asked Copilot/Claude to review the initial class sketch and flag missing relationships or bottlenecks. It suggested separating the display layer (`todays_schedule`) from raw data retrieval.
- **Scaffolding**: Used Agent Mode to generate class skeletons from a plain-English description of the UML, then filled in logic manually.
- **Algorithm implementation**: Used Inline Chat for the `timedelta` recurrence calculation and for the `sorted()` lambda key on HH:MM strings.
- **Test generation**: Used the "Generate tests" smart action to bootstrap `test_pawpal.py`, then manually added edge-case tests (empty list, case-insensitive filter, one-off recurrence) that auto-generation missed.
- **Debugging**: Used Inline Chat on a failing `UnicodeEncodeError` on Windows to identify that Unicode symbols in `Task.__str__` needed ASCII replacements.

The most effective prompt pattern was providing `#file:pawpal_system.py` as context and asking a specific, scoped question rather than an open-ended request.

**b. Judgment and verification**

Copilot initially suggested giving `Scheduler` a direct `pets: List[Pet]` attribute instead of delegating through an `Owner`. I rejected this because it would violate the ownership hierarchy: the Scheduler should be stateless relative to pet data and should always read from the Owner. Accepting the suggestion would have created two sources of truth for the pet list and made `Owner` redundant.

I verified the correct approach by tracing the UML: `Owner → Pet → Task` is the ownership chain; `Scheduler` is a service that reads from it, not a container that duplicates it.

---

## 4. Testing and Verification

**a. What you tested**

The automated suite in `tests/test_pawpal.py` covers 14 behaviors:

- `mark_complete()` flips `completed` to `True` — core status transition
- `add_task()` increases the pet's task count — basic data integrity
- Daily task produces a follow-up due tomorrow — recurrence correctness
- Weekly task produces a follow-up due in 7 days — recurrence correctness
- One-off task returns `None` on completion — no phantom tasks created
- `sort_by_time()` returns tasks in chronological order — scheduler's primary feature
- `sort_by_time()` on an empty list returns `[]` — edge case
- `filter_by_status(False)` excludes completed tasks — filter correctness
- `filter_by_pet("Luna")` returns only Luna's tasks — filter correctness
- Pet name filter is case-insensitive — UX robustness
- Conflict flagged when two tasks share a time — safety warning system
- No conflict when all times are unique — no false positives
- `mark_task_complete()` auto-adds a follow-up to the pet — integration test
- `get_all_tasks()` count matches the sum across all pets — data integrity

These tests mattered because the scheduler's value depends entirely on the correctness of sorting, filtering, recurrence, and conflict detection. A bug in any of these silently produces wrong schedules.

**b. Confidence**

Confidence: **4 out of 5 stars.**

All happy paths and meaningful edge cases pass (14/14). I would test next:
- Malformed time strings (e.g., `"9:5"` instead of `"09:05"`) to validate input handling.
- An owner with zero pets — empty schedule, no crash.
- Tasks spanning midnight (`"23:30"` and `"00:15"`) to confirm lexicographic sort still works.
- End-to-end Streamlit UI behavior using Playwright or similar.

---

## 5. Reflection

**a. What went well**

The "CLI-first" workflow worked exactly as intended. Building and verifying `pawpal_system.py` through `main.py` before touching the Streamlit UI meant every bug was caught in a tight terminal feedback loop. By the time `app.py` was written, the backend had zero surprises and wiring the UI took very little time.

**b. What you would improve**

I would add a `duration_minutes` field to `Task` from the start. The current conflict detection is simple (exact-time matching only), but a duration field would unlock true overlap detection, next-available-slot suggestions, and more realistic schedule visualizations — all features a real pet owner would value.

**c. Key takeaway**

The most important lesson was that AI accelerates the *mechanical* parts of coding — boilerplate, syntax, standard library lookups — but consistently suggests the *convenient* solution rather than the *architecturally correct* one. The Scheduler-owns-pets suggestion was faster to implement but wrong for the design. Being the "lead architect" meant holding the design invariants and treating AI as a fast collaborator whose output always needs a design review before accepting.
