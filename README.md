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
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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
