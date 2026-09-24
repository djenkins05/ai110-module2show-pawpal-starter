# PawPal+ Project Reflection

## 1. System Design

**a. Initial design** 
My initial UML design breaks PawPal+ into five classes, separating the *data* (what a pet, owner, and task are) from the *behavior* (how a plan gets built and explained).

**`Owner`**
Holds the owner's basic info and preferences: name, the amount of time they have
available for pet care that day, and any scheduling preferences (e.g. preferred start time, whether they want high-priority tasks front-loaded). Responsible for storing the constraints the scheduler has to respect, and for owning one or more `Pet` objects.

**`Pet`**
Holds basic info about a single pet — name and species — and the list of `CareTask`
objects associated with that pet. Responsible for knowing what care the pet needs, and for adding/removing tasks from its own task list.

**`CareTask`**
Represents one unit of pet care (morning walk, feeding, medication, grooming,
enrichment). Stores a title, a duration in minutes, and a priority (low / medium /
high). Responsible for knowing its own cost in time and its importance, and for
converting priority into a numeric weight the scheduler can sort on.

**`Schedule`**
Represents the finished daily plan: an ordered list of scheduled tasks, each with a
start and end time, plus the set of tasks that had to be left out. Responsible for
holding the result of scheduling and for reporting totals (time used, time remaining, number of tasks included vs. skipped).

**`Scheduler`**
The class that does the actual work. Takes an `Owner` (with their time budget and
preferences) and a collection of `CareTask` objects, then selects and orders tasks that fit within the available time, prioritizing higher-priority tasks first. Responsible for producing a `Schedule` object and for generating an explanation of its decisions — why each task was included and placed where it was, and why any excluded task didn't make the cut.

**Why this split:** I kept `Scheduler` separate from `Owner` and `Pet` so the scheduling logic can be tested on its own without needing UI or a full object graph, and so the algorithm can be changed later without touching the data classes. `Schedule` exists as its own class rather than a plain list so the plan can carry its own summary and explanation data, which the Streamlit UI can display directly.

**b. Design changes**

Yes — a few changes came out of reviewing the class skeletons against the original UML:

- **Added a `ScheduledTask` class.** The original diagram had `Schedule.scheduled_tasks` typed as `list~ScheduledTask~` without `ScheduledTask` ever being defined, and my notes above describe "an ordered list of scheduled tasks, each with a start and end time", which is more than a bare `CareTask` carries. `ScheduledTask` now pairs a `CareTask` with a `start_time` and `end_time`, and `Schedule` references it instead of referencing `CareTask` directly.
- **Gave `CareTask` a `pet_name` field.** `Owner.get_all_tasks()` flattens every pet's tasks into one list, which meant that once a task reached the `Scheduler` or `Schedule`, there was no way to say which pet it belonged to. `Pet.add_task()` will stamp this field when a task is added, so `Schedule.summary()` and `Scheduler.explain()` can still report per-pet detail after the flattening.
- **Added a `PRIORITY_WEIGHTS` lookup table on `CareTask`.** `priority_weight()` needs some mapping from `"low"/"medium"/"high"` to a sortable number; putting it as a class constant on `CareTask` keeps that mapping in one place instead of letting the scheduler hardcode its own copy.
- **`Scheduler` now stores the `Schedule` it builds.** The UML shows `Scheduler *-- Schedule : produces` as a composition, but the original skeleton only *returned* a `Schedule` from `build_schedule()` without keeping a reference. `Scheduler` now keeps `self.schedule`, so `explain()` has something to describe after the fact.
- **`Scheduler`'s task list now defaults to the owner's tasks.** The constructor originally defaulted `tasks` to an empty list when none was passed, which could quietly desync from what the owner's pets actually need. It now defaults to `owner.get_all_tasks()`, while still accepting an explicit list so the scheduling algorithm can be unit-tested without building a full `Owner`/`Pet` graph.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler weighs four constraints, in order of how much they actually change the output:

- **Time budget** (`Owner.available_minutes` via `get_time_budget()`) - the hard constraint. `Scheduler.build_schedule()` never lets `total_minutes_used` exceed the budget; a task that doesn't fit is skipped, not truncated.
- **Priority** (`CareTask.priority` → `priority_weight()`) — the primary ordering constraint. `sort_by_priority()` fills the budget with high-priority tasks first, so if something has to be cut, it's low-priority work, not a medication reminder.
- **Recurrence due dates** (`CareTask.due_date` / `is_due()`) — a gating constraint. A recurring task's next occurrence is created immediately on completion but isn't eligible for today's schedule (or for "pending" filters) until its due date arrives, so `build_schedule()` doesn't schedule tomorrow's walk today.
- **Preferred time** (`CareTask.preferred_time`) — a soft, informational constraint. It doesn't affect *whether* a task gets scheduled or in what order (that's still priority-driven); it only feeds `sort_by_time()`'s chronological view and `detect_time_conflicts()`'s warnings.

I decided time and priority mattered most because they're the two constraints an owner literally cannot ignore — they don't have unlimited minutes, and not every task is equally important if something has to be dropped. Due dates and preferred time matter for *usability* (not nagging the owner about a task that isn't due yet, not double-booking two pets at 7am) but they don't compete for a slot in the schedule the way time and priority do.

**b. Tradeoffs**

**The tradeoff:** `Scheduler.detect_time_conflicts()` only checks whether two tasks share the *exact same* `preferred_time` string (e.g. two tasks both set to `"07:00"`). It does not check whether their time **windows** actually overlap — a 30-minute walk starting at 07:00 and a 10-minute feeding starting at 07:15 both occupy
07:15, but the exact-match check won't flag them, because their
`preferred_time` values ("07:00" vs "07:15") don't match.

A full overlap check would compare every pair of tasks' `[start, start + duration)` ranges (an `O(n²)` scan, or `O(n log n)` with a sort-and-sweep), and it would also have to decide what to do about tasks with no fixed time at all, since those get placed wherever the greedy scheduler finds room. The exact-match version, by contrast, is a single pass that groups tasks into a
dict keyed by parsed time (`O(n)`), and its output is trivial to read: "these tasks want the *same* time," full stop — no minute-level interval math for the pet owner to interpret.

For PawPal+'s scale (a handful of tasks per pet per day, entered by hand), this tradeoff is reasonable: exact matches already catch the most common real mistake (re-adding a task at a time you already used, or two pets needing attention at once), it can never throw an exception since it just returns an
empty list when nothing collides, and the added complexity of true interval overlap detection isn't yet justified by how the app is actually used. If tasks start getting entered with tightly packed, slightly-offset times, this would be the first piece of scheduling logic worth upgrading to real interval
overlap checking.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code as a pair programmer for the parts of this project that had a clear "right answer" to converge on, and as a hands-on collaborator for the parts that needed something built and then proven to work. Concretely:

- **Edge-case brainstorming, then implementation.** I asked what the most important edge cases were for a scheduler with sorting and recurring tasks (an empty pet, two tasks at the exact same time, exact-budget boundaries, invalid input) and had it both name them and write the corresponding tests directly into `tests/test_pawpal.py` nine new tests covering happy paths and boundaries the original suite hadn't touched.
- **Wiring the backend into the UI.** I had it update `app.py`'s display logic to actually use `Scheduler` methods (`sort_by_priority()`/`sort_by_time()`, `detect_time_conflicts()`) and `Owner.detect_duplicate_tasks()`, replacing plain text with `st.success`/`st.warning`/`st.table`.
- **Keeping documentation in sync with the code.** I had it update the UML diagram (`diagrams/uml_final.mmd`) to match the final class shapes and methods, and rewrite the README's testing, features, and demo sections using the project's actual, freshly-run output instead of placeholder text.

The most useful prompts were the ones with a concrete, checkable target — "add tests for these specific edge cases," "use `st.table` for this data" — rather than open-ended ones, because the result was immediately verifiable (a passing test, a rendered table) instead of something I had to judge by eye.

**b. Judgment and verification**

When the AI updated `app.py` to show `detect_time_conflicts()` warnings, I didn't just accept that the feature was "done" once the code looked reasonable. It turned out the "Add a Task" form never actually collected a `preferred_time`, which meant the conflict-warning code could never fire from the UI at all, it was dead code dressed up as a feature. Rather than let that slide, I had it add the missing input field and re-verify that the warning actually appeared with real data.

I also didn't take "the code looks right" as proof the UI worked. I had the AI drive the real Streamlit app end-to-end using Streamlit's `AppTest` harness to add a pet, add two conflicting tasks, toggle the sort order, and generate a schedule and only accepted the change once that run showed the actual warning text and tables rendering correctly with no exceptions, rather than trusting a read-through of the source.

---

## 4. Testing and Verification

**a. What you tested**

The suite (`tests/test_pawpal.py`, 26 tests) focuses on the behaviors most likely to silently break as the scheduler grew: sorting (`Schedule.get_scheduled_tasks_sorted_by_time()`, `Scheduler.sort_by_time()`/`sort_by_priority()`, including tie-stability), recurrence (`create_next_occurrence()` producing a due-tomorrow/due-next-week task, `is_due()` gating it), conflict and duplicate detection (`detect_time_conflicts()` and `detect_duplicate_tasks()`, both the positive and negative cases), filtering (`Owner.filter_tasks()`/`Scheduler.filter_tasks()`), scheduling boundaries (an empty pet/owner, a task that exactly fills the remaining budget, zero available minutes), and input validation (invalid `priority`/`frequency`/`preferred_time` raising `ValueError`).

These mattered because they're exactly the places where "it works on the example I tried" and "it's actually correct" diverge a sort that happens to look right for three hand-picked tasks can still be unstable on ties, and a `<=` budget check is one off-by-one away from either wasting a minute of budget or overflowing it.

**b. Confidence**

I'm fairly confident that the core scheduling algorithm is correct: all 26 tests pass, and they specifically target the boundary and tie-breaking cases where greedy scheduling algorithms tend to hide bugs. The one star I'm holding back is for two known, accepted gaps: `detect_time_conflicts()`'s exact-match-on-`preferred_time` check (see section 2b) instead of true interval overlap, and the fact that the Streamlit UI itself has no *permanent* automated test. It was verified manually and with a one-off `AppTest` script, not a checked-in test that runs on every change.

If I had more time, I'd test: true `[start, start + duration)` overlap conflicts (two tasks at different preferred times whose durations still collide); whether tie-breaking stays deterministic across a full `build_schedule()` run for multiple pets competing for the same budget, not just in `sort_by_priority()` alone; and a recurring task whose due date lands on a day the owner has zero available minutes, to make sure it's correctly reported as skipped rather than not-due or silently dropped.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with keeping `Scheduler` decoupled from `Owner`/`Pet` from the start. Because the scheduling algorithm only depends on a list of `CareTask` objects and a time budget, every test in `test_pawpal.py` — including the new edge-case tests could exercise `build_schedule()`, `sort_by_time()`, and `detect_time_conflicts()` directly, without ever touching Streamlit. That decoupling is also what made it possible to add real UI features later (the sort toggle, the warnings) with confidence, since the underlying methods were already proven correct.

**b. What you would improve**

If I had another iteration, I'd replace the exact-match `preferred_time` conflict check with true interval-overlap detection, since it's the one piece of scheduling logic I already know is a simplification rather than a design choice I'd defend indefinitely. I'd also turn the one-off `AppTest` smoke script from this session into a permanent, checked-in test file, so the Streamlit display logic gets the same regression protection as the backend.

**c. Key takeaway**

The biggest lesson was that "the AI wrote the feature" and "the feature works" are two different claims, and the gap between them only closes by actually running the thing like a test suite for the backend, and driving the real app for the UI, rather than by reading code and deciding it looks plausible. The `preferred_time` gap in the Add Task form is the clearest example: the conflict-detection code was correct in isolation, but nothing in the UI could ever reach it, and that only surfaced once I insisted on an end-to-end check instead of a code review.

**d. Being the lead architect**

Working with an AI this capable, my job shifted from writing every line myself to staying the one who decides what "done" means and directing the AI toward it. I made the calls on the system's shape — the `Scheduler`/`Owner`/`Pet` split in section 1, which constraints actually mattered in 2a, which tradeoff to accept in 2b and used the AI to implement and verify inside those boundaries, rather than asking it to decide what the system should be.

Two habits stood out as the most valuable parts of that arrangement. First, having the AI run genuine end-to-end tests on the code instead of stopping at "the code looks right": using Streamlit's `AppTest` harness to actually drive `app.py`(add a pet, add conflicting tasks, toggle the sort, generate a schedule) is what caught the `preferred_time` gap in section 3b, a defect a code read-through had missed entirely. Second, having the AI come up with edge cases and tests up front, before I asked for a single line of test code, was genuinely useful: prompting it for "the most important edge cases for a scheduler with sorting and recurring tasks" surfaced boundary conditions (an empty pet, two tasks at the exact same time, an exact-budget-fit task, invalid priority/frequency input) that I hadn't thought to ask for, and it could turn each one into a runnable, inspectable test immediately. My role was to set the direction and judge whether the results actually cleared the bar not to enumerate every edge case or trust a passing-looking diff by itself.
