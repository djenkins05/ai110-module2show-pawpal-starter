# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

- **Priority-based scheduling** — `Scheduler.build_schedule()` greedily fills the owner's time budget with the highest-priority pending tasks first (via `sort_by_priority()`), skipping any task that would exceed the remaining budget.
- **Sorting by time** — `Scheduler.sort_by_time()` orders tasks by their optional `preferred_time` (`"HH:MM"` or `"H:MM AM/PM"`) instead of priority, so a day's plan can be viewed chronologically; tasks with no preferred time sort last.
- **Conflict warnings** — `Scheduler.detect_time_conflicts()` flags any two tasks (same pet or different pets) that want the exact same `preferred_time`; `Owner.detect_duplicate_tasks()` separately flags pending tasks on the same pet that share a title, in case a chore was added twice.
- **Daily & weekly recurrence** — completing a `"daily"`/`"weekly"` task (`Pet.complete_task()` or `Scheduler.mark_task_complete()`) leaves the completed instance as history and automatically creates a new pending occurrence due 1 day (daily) or 7 days (weekly) later.
- **Due-date gating** — `CareTask.is_due()` keeps a freshly-created recurring occurrence out of "pending" lists and out of the schedule until its due date actually arrives.
- **Filtering** — `Owner.filter_tasks()` and `Scheduler.filter_tasks()` narrow the task list by pet and/or completion status.
- **Plan explanation** — `Scheduler.explain()` reports, in plain language, why each task was included or skipped (not enough time remaining, or not due yet).
- **Interactive UI** — the Streamlit app (`app.py`) lets an owner add pets/tasks, toggle between priority/time sorting, see duplicate- and conflict-warnings inline, and generate a schedule with one click.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output from running `python main.py`:

```
=== Today's Schedule ===
  08:00-08:10  Feeding for Biscuit (10 min, high priority)
  08:10-08:40  Morning walk for Biscuit (30 min, high priority)
  08:40-08:45  Medication for Whiskers (5 min, high priority)

Skipped (not enough time left):
  Playtime for Whiskers (20 min, low priority)

Time used: 45/60 min (15 min remaining)

=== Why this plan? ===
Included 'Feeding' at 08:00 (priority=high, weight=3)
Included 'Morning walk' at 08:10 (priority=high, weight=3)
Included 'Medication' at 08:40 (priority=high, weight=3)
Skipped 'Playtime' — not enough time remaining (needed 20 min)
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The suite (`tests/test_pawpal.py`, 26 tests) covers:

- **Core task/pet behavior**: marking a task complete, adding tasks to a pet, `Pet.get_tasks()` returning the right count.
- **Sorting**: `Schedule.get_scheduled_tasks_sorted_by_time()` and `Scheduler.sort_by_time()` return tasks in chronological order regardless of insertion order; `Scheduler.sort_by_priority()` orders by priority weight and keeps insertion order for ties.
- **Filtering**: `Owner.filter_tasks()` and `Scheduler.filter_tasks()` narrow tasks by pet and/or completion status, correctly excluding not-yet-due recurring tasks from "pending".
- **Recurring tasks**: completing a `"daily"` task creates a new pending occurrence due the next day; completing a `"weekly"` task creates one due in 7 days; a `"once"` task creates no next occurrence; `CareTask.is_due()` gates a task until its due date arrives; `Scheduler.mark_task_complete()` adds the new occurrence to both the pet and the scheduler.
- **Conflict detection**: `Scheduler.detect_time_conflicts()` flags two tasks (same pet or different pets) scheduled at the exact same `preferred_time`, and returns an empty list when there's no overlap; `Owner.detect_duplicate_tasks()` flags pending tasks on the same pet that share a title, while ignoring completed ones.
- **Scheduling boundaries**: a happy-path run across multiple pets/tasks that all fit the time budget; a pet/owner with no tasks producing an empty schedule; a task whose duration exactly equals the remaining budget still being included; zero available minutes skipping everything.
- **Input validation**: constructing a `CareTask` with an unknown priority, unknown frequency, or an unparseable `preferred_time` raises `ValueError`.

Sample test output (`python -m pytest -v`):

```
============================= test session starts ==============================
platform darwin -- Python 3.12.1, pytest-9.1.1, pluggy-1.6.0 -- .venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/djenkins/Documents/GitHub/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collecting ... collected 26 items

tests/test_pawpal.py::test_care_task_rejects_unparseable_preferred_time PASSED [100%]

============================== 26 passed in 0.02s ==============================
```

### Confidence Level: ⭐⭐⭐⭐☆ (4/5)

All 26 tests pass, covering the core scheduling algorithm, sorting, filtering, recurrence, conflict/duplicate detection, boundary conditions (exact-budget fit, zero budget, empty pet/owner), and input validation. One star is held back because `detect_time_conflicts()` uses an exact-match on `preferred_time` rather than true `[start, start + duration)` overlap detection (a documented, deliberate tradeoff — see `reflection.md`, section 2b), and the Streamlit UI (`app.py`) itself isn't covered by automated tests, only by manual verification.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | `sort_by_priority()` orders tasks highest-to-lowest by `CareTask.priority_weight()`. `sort_by_time()` orders tasks by their optional `preferred_time` (`"HH:MM"`/`"H:MM AM/PM"`, parsed with `_parse_time()`); tasks with no preferred time sort last. |
| Filtering | `Owner.filter_tasks(pet_name=None, completed=None)`, `Scheduler.filter_tasks(completed=None, pet_name=None)` | Narrows a task list by pet name and/or completion status. Requesting `completed=False` also excludes tasks that aren't due yet (see recurring tasks below), so "pending" only means tasks actually actionable today. |
| Conflict detection | `Scheduler.detect_time_conflicts()`, `Owner.detect_duplicate_tasks()` | `detect_time_conflicts()` groups tasks by exact `preferred_time` match and returns a list of warning strings (never raises) when two tasks — for the same pet or different pets — want the same time. `detect_duplicate_tasks()` separately flags pending tasks for the same pet that share a title, in case the same chore got added twice. See `reflection.md` (section 2b) for the exact-match-vs-overlap tradeoff behind `detect_time_conflicts()`. |
| Recurring tasks | `CareTask.create_next_occurrence()`, `Pet.complete_task()`, `CareTask.is_due()` | Completing a `"daily"`/`"weekly"` task (via `Pet.complete_task()` or `Scheduler.mark_task_complete()`) leaves that instance completed as history and creates a brand-new pending `CareTask` due `today + 1 day` (daily) or `+ 7 days` (weekly). `CareTask.is_due()` gates scheduling/filtering so that new instance isn't treated as pending until its due date arrives. |

## 📸 Demo Walkthrough

### Main UI features

- **Owner setup**: enter a name, available minutes for the day, and a preferred start time.
- **Add a Pet**: give a pet a name and species; added pets appear in a running list.
- **Schedule a Task**: pick a pet, title, duration, priority, frequency (`once`/`daily`/`weekly`), and an optional preferred time (`HH:MM` or `H:MM AM/PM`).
- **Current Tasks table**: a "Sort by" toggle re-orders the table live by Priority or Time; duplicate-title and same-preferred-time conflicts show up as warnings above the table as soon as they exist.
- **Generate Schedule**: builds the day's plan and shows scheduled, skipped, and not-yet-due tasks as separate tables, plus an expandable "Why this plan?" explanation.

### Example workflow

1. Set up the owner (e.g., 60 available minutes, preferred start time `08:00`).
2. Add a pet, "Biscuit" (dog).
3. Add a task for Biscuit: "Morning walk", 30 min, high priority, preferred time `07:00`.
4. Add a second task for Biscuit at the same preferred time (e.g., "Medication", 07:00) — a conflict warning appears immediately above the Current Tasks table, before any schedule is even built.
5. Click "Generate schedule" — Biscuit's high-priority tasks are placed back-to-back starting at 08:00; anything that doesn't fit the remaining time budget lands in the skipped table instead.

### Key Scheduler behaviors shown

- **Priority-first greedy scheduling** within a fixed time budget (`build_schedule()`).
- **Sorting**, toggled live between priority order and chronological preferred-time order.
- **Conflict warnings** for same-time tasks and duplicate-title tasks, surfaced before scheduling even runs.
- **Recurrence**: completing a daily/weekly task creates its next occurrence, gated by `is_due()` so it doesn't count as pending until its due date arrives.

### Sample CLI output

`main.py` runs a fixed demo scenario (independent of the Streamlit session) that exercises sorting, filtering, and conflict detection end-to-end:

```
=== Today's Schedule ===
  08:00-08:10  Feeding for Biscuit (10 min, high priority)
  08:10-08:40  Morning walk for Biscuit (30 min, high priority)
  08:40-08:45  Medication for Whiskers (5 min, high priority)

Skipped (not enough time left):
  Playtime for Whiskers (20 min, low priority)

Time used: 45/60 min (15 min remaining)

=== Why this plan? ===
Included 'Feeding' at 08:00 (priority=high, weight=3)
Included 'Morning walk' at 08:10 (priority=high, weight=3)
Included 'Medication' at 08:40 (priority=high, weight=3)
Skipped 'Playtime' — not enough time remaining (needed 20 min)

=== Tasks sorted by preferred time ===
     07:00  Morning walk for Biscuit
     07:00  Medication for Whiskers
     09:30  Playtime for Whiskers
     12:00  Litter box cleaning for Whiskers
     18:00  Feeding for Biscuit

=== Filter: pending tasks for Biscuit ===
  Feeding (high priority)
  Morning walk (high priority)

=== Filter: completed tasks (any pet) ===
  Litter box cleaning for Whiskers

=== Conflict check ===
  WARNING: Conflict at 07:00: 'Morning walk' (Biscuit), 'Medication' (Whiskers) are all scheduled at the same time.
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
