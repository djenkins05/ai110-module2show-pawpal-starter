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
  08:00-08:30  Morning walk for Biscuit (30 min, high priority)
  08:30-08:40  Feeding for Biscuit (10 min, high priority)
  08:40-08:55  Litter box cleaning for Whiskers (15 min, medium priority)

Skipped (not enough time left):
  Playtime for Whiskers (20 min, low priority)

Time used: 55/60 min (5 min remaining)

=== Why this plan? ===
Included 'Morning walk' at 08:00 (priority=high, weight=3)
Included 'Feeding' at 08:30 (priority=high, weight=3)
Included 'Litter box cleaning' at 08:40 (priority=medium, weight=2)
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

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  3%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [  7%]
tests/test_pawpal.py::test_scheduled_tasks_sorted_by_time_out_of_insertion_order PASSED [ 11%]
tests/test_pawpal.py::test_filter_tasks_by_pet_and_status PASSED         [ 15%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_occurrence_due_tomorrow PASSED [ 19%]
tests/test_pawpal.py::test_completing_weekly_task_creates_next_occurrence_due_in_a_week PASSED [ 23%]
tests/test_pawpal.py::test_is_due_gates_pending_task_until_its_due_date PASSED [ 26%]
tests/test_pawpal.py::test_build_schedule_excludes_task_not_yet_due PASSED [ 30%]
tests/test_pawpal.py::test_completing_one_time_task_creates_no_next_occurrence PASSED [ 34%]
tests/test_pawpal.py::test_scheduler_mark_task_complete_adds_next_occurrence_to_owner_and_scheduler PASSED [ 38%]
tests/test_pawpal.py::test_detect_duplicate_tasks_flags_same_title_same_pet PASSED [ 42%]
tests/test_pawpal.py::test_scheduler_sort_by_time_orders_tasks_added_out_of_order PASSED [ 46%]
tests/test_pawpal.py::test_scheduler_filter_tasks_by_status_and_pet PASSED [ 50%]
tests/test_pawpal.py::test_detect_duplicate_tasks_ignores_completed_task PASSED [ 53%]
tests/test_pawpal.py::test_detect_time_conflicts_flags_cross_pet_same_time PASSED [ 57%]
tests/test_pawpal.py::test_detect_time_conflicts_returns_empty_list_when_no_overlap PASSED [ 61%]
tests/test_pawpal.py::test_build_schedule_happy_path_schedules_multiple_tasks_across_pets_by_priority PASSED [ 65%]
tests/test_pawpal.py::test_pet_with_no_tasks_produces_empty_schedule PASSED [ 69%]
tests/test_pawpal.py::test_owner_with_no_pets_has_no_tasks_and_no_duplicate_conflicts PASSED [ 73%]
tests/test_pawpal.py::test_two_tasks_at_exact_same_preferred_time_on_same_pet_flagged_as_conflict PASSED [ 76%]
tests/test_pawpal.py::test_build_schedule_task_exactly_filling_budget_is_included_boundary PASSED [ 80%]
tests/test_pawpal.py::test_build_schedule_with_zero_available_minutes_skips_everything PASSED [ 84%]
tests/test_pawpal.py::test_sort_by_priority_ties_preserve_insertion_order PASSED [ 88%]
tests/test_pawpal.py::test_care_task_rejects_unknown_priority PASSED     [ 92%]
tests/test_pawpal.py::test_care_task_rejects_unknown_frequency PASSED    [ 96%]
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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
