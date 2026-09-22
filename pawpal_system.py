from __future__ import annotations

from itertools import combinations
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import ClassVar


def _add_minutes(moment: time, minutes: int) -> time:
    """Return the time-of-day that is `minutes` after `moment`."""
    combined = datetime.combine(date.today(), moment) + timedelta(minutes=minutes)
    return combined.time()


def _parse_time(value: str) -> time:
    """Parse a 'HH:MM' or 'H:MM AM/PM' string into a time object."""
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Could not parse time {value!r}; use 'HH:MM' (24h) or 'H:MM AM/PM'")


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str
    # How often this task recurs; a daily/weekly task spawns a new pending
    # instance via create_next_occurrence() when marked complete (see
    # Pet.complete_task()). "once" tasks never recur.
    frequency: str = "once"
    completed: bool = False
    # Date the task was last marked complete. None means never completed.
    completed_at: date | None = None
    # Set by Pet.add_task() so a flattened task list (e.g. from
    # Owner.get_all_tasks()) can still be traced back to its pet.
    pet_name: str | None = None
    # Optional preferred time of day for this task, e.g. "07:30" or "7:30 AM".
    # None means the task has no fixed time and can be scheduled whenever.
    preferred_time: str | None = None
    # Set on tasks created by create_next_occurrence(); the task isn't
    # considered due (see is_due()) until this date. None means no gating.
    due_date: date | None = None

    PRIORITY_WEIGHTS: ClassVar[dict[str, int]] = {"low": 1, "medium": 2, "high": 3}
    # "once" tasks never recur. Daily/weekly tasks spawn a next occurrence
    # when completed (see create_next_occurrence()), due this many days later.
    VALID_FREQUENCIES: ClassVar[set[str]] = {"once", "daily", "weekly"}
    FREQUENCY_INTERVALS: ClassVar[dict[str, int]] = {"daily": 1, "weekly": 7}

    def __post_init__(self) -> None:
        """Normalize and validate the priority and frequency fields."""
        self.priority = self.priority.strip().lower()
        if self.priority not in self.PRIORITY_WEIGHTS:
            valid = ", ".join(self.PRIORITY_WEIGHTS)
            raise ValueError(f"Unknown priority {self.priority!r}; expected one of: {valid}")

        self.frequency = self.frequency.strip().lower()
        if self.frequency not in self.VALID_FREQUENCIES:
            valid = ", ".join(sorted(self.VALID_FREQUENCIES))
            raise ValueError(f"Unknown frequency {self.frequency!r}; expected one of: {valid}")

        if self.preferred_time is not None:
            _parse_time(self.preferred_time)

    def priority_weight(self) -> int:
        """Return the numeric weight used to sort tasks by priority."""
        return self.PRIORITY_WEIGHTS[self.priority]

    def mark_complete(self, today: date | None = None) -> None:
        """Mark the task complete as of today (or a given date)."""
        self.completed = True
        self.completed_at = today or date.today()

    def create_next_occurrence(self) -> CareTask | None:
        """Return a fresh CareTask for this task's next occurrence, or None if it doesn't recur.

        This completed instance is left as-is (a historical record); the
        returned task is a brand-new instance, due today + the frequency's
        interval (e.g. +1 day for "daily", +7 for "weekly"), that the caller
        should add to the relevant pet's task list.
        """
        if self.frequency == "once":
            return None
        interval_days = self.FREQUENCY_INTERVALS[self.frequency]
        due_date = (self.completed_at or date.today()) + timedelta(days=interval_days)
        return CareTask(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            preferred_time=self.preferred_time,
            due_date=due_date,
        )

    def is_due(self, today: date | None = None) -> bool:
        """Return True if this task has no due date, or its due date has arrived."""
        return self.due_date is None or self.due_date <= (today or date.today())

    def __str__(self) -> str:
        """Return a human-readable summary of the task."""
        status = "done" if self.completed else "pending"
        label = (
            f"{self.title} ({self.duration_minutes} min, {self.priority} priority, "
            f"{self.frequency}, {status})"
        )
        return f"{label} for {self.pet_name}" if self.pet_name else label


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a task to this pet's list, tagging it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: CareTask) -> None:
        """Remove a task from this pet's list."""
        self.tasks.remove(task)

    def complete_task(self, task: CareTask, today: date | None = None) -> CareTask | None:
        """Mark a task complete and, if it recurs, add a new pending task for its next occurrence."""
        task.mark_complete(today)
        next_task = task.create_next_occurrence()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def get_tasks(self) -> list[CareTask]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferred_start_time: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[CareTask]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def get_time_budget(self) -> int:
        """Return the owner's available minutes for care tasks today."""
        return self.available_minutes

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[CareTask]:
        """Return tasks across all pets, optionally narrowed by pet name and/or completion status.

        Requesting completed=False excludes tasks whose due_date hasn't
        arrived yet (see CareTask.is_due()) — a recurring task's next
        occurrence isn't "pending" until it's actually due.
        """
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [task for task in tasks if task.pet_name == pet_name]
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
            if completed is False:
                tasks = [task for task in tasks if task.is_due()]
        return tasks

    def detect_duplicate_tasks(self) -> list[tuple[CareTask, CareTask]]:
        """Return pairs of pending tasks for the same pet that share a title (likely duplicates)."""
        conflicts: list[tuple[CareTask, CareTask]] = []
        for pet in self.pets:
            pending = [task for task in pet.get_tasks() if not task.completed]
            groups: dict[str, list[CareTask]] = {}
            for task in pending:
                groups.setdefault(task.title.strip().lower(), []).append(task)
            for group in groups.values():
                conflicts.extend(combinations(group, 2))
        return conflicts


@dataclass
class ScheduledTask:
    task: CareTask
    start_time: time
    end_time: time


@dataclass
class Schedule:
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    skipped_tasks: list[CareTask] = field(default_factory=list)
    # Pending tasks whose due_date hasn't arrived yet (see CareTask.is_due()),
    # kept separate from skipped_tasks since they weren't excluded for lack
    # of time.
    not_due_tasks: list[CareTask] = field(default_factory=list)
    total_minutes_used: int = 0

    def add_scheduled_task(self, task: CareTask, start: time) -> None:
        """Add a task to the schedule at the given start time and track its minutes."""
        end = _add_minutes(start, task.duration_minutes)
        self.scheduled_tasks.append(ScheduledTask(task=task, start_time=start, end_time=end))
        self.total_minutes_used += task.duration_minutes

    def time_remaining(self, budget: int) -> int:
        """Return how many minutes of the given budget are still unused."""
        return budget - self.total_minutes_used

    def get_scheduled_tasks_sorted_by_time(self) -> list[ScheduledTask]:
        """Return the day's scheduled tasks ordered chronologically by start time."""
        return sorted(self.scheduled_tasks, key=lambda scheduled: scheduled.start_time)

    def summary(self) -> str:
        """Return a human-readable report of scheduled and skipped tasks."""
        lines = [f"Scheduled tasks ({self.total_minutes_used} min used):"]
        if self.scheduled_tasks:
            for scheduled in self.scheduled_tasks:
                start = scheduled.start_time.strftime("%H:%M")
                end = scheduled.end_time.strftime("%H:%M")
                lines.append(f"  {start}-{end}  {scheduled.task}")
        else:
            lines.append("  (none)")

        lines.append(f"Skipped tasks ({len(self.skipped_tasks)}):")
        if self.skipped_tasks:
            for task in self.skipped_tasks:
                lines.append(f"  {task}")
        else:
            lines.append("  (none)")

        lines.append(f"Not yet due ({len(self.not_due_tasks)}):")
        if self.not_due_tasks:
            for task in self.not_due_tasks:
                lines.append(f"  {task} (due {task.due_date})")
        else:
            lines.append("  (none)")

        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner, tasks: list[CareTask] | None = None) -> None:
        """Set up the scheduler with an owner and the tasks it should schedule."""
        self.owner = owner
        # Defaults to every task the owner's pets need; callers can still pass
        # an explicit list to test the scheduling logic in isolation.
        self.tasks = tasks if tasks is not None else owner.get_all_tasks()
        # Holds the most recently built Schedule so explain() has something
        # to describe after the fact (mirrors the Scheduler *-- Schedule
        # composition in the UML).
        self.schedule: Schedule | None = None

    def build_schedule(self) -> Schedule:
        """Greedily schedule pending tasks by priority within the owner's time budget."""
        budget = self.owner.get_time_budget()
        current_time = _parse_time(self.owner.preferred_start_time)

        schedule = Schedule()
        for task in self.sort_by_priority():
            if task.completed:
                continue
            if not task.is_due():
                schedule.not_due_tasks.append(task)
                continue
            if schedule.total_minutes_used + task.duration_minutes <= budget:
                schedule.add_scheduled_task(task, current_time)
                current_time = _add_minutes(current_time, task.duration_minutes)
            else:
                schedule.skipped_tasks.append(task)

        self.schedule = schedule
        return schedule

    def sort_by_priority(self) -> list[CareTask]:
        """Return this scheduler's tasks sorted from highest to lowest priority."""
        return sorted(self.tasks, key=lambda task: task.priority_weight(), reverse=True)

    def sort_by_time(self) -> list[CareTask]:
        """Return this scheduler's tasks ordered by preferred time of day.

        Uses _parse_time to turn each "HH:MM"/"H:MM AM/PM" string into a
        directly comparable `time` object. Tasks with no preferred_time sort
        last.
        """
        return sorted(
            self.tasks,
            key=lambda task: _parse_time(task.preferred_time) if task.preferred_time else time.max,
        )

    def detect_time_conflicts(self) -> list[str]:
        """Return one human-readable warning per group of tasks that want the same preferred_time.

        This is a deliberately lightweight check: it groups tasks by an
        exact preferred_time match (same pet or not) rather than computing
        whether their [start, start + duration) windows overlap. It never
        raises — an empty list just means no conflicts were found — so a
        caller can safely show these as warnings without crashing the
        scheduling flow. See reflection.md, section 2b, for why this
        exact-match tradeoff is acceptable here.
        """
        groups: dict[time, list[CareTask]] = {}
        for task in self.tasks:
            if task.preferred_time is None:
                continue
            groups.setdefault(_parse_time(task.preferred_time), []).append(task)

        warnings: list[str] = []
        for moment, group in sorted(groups.items()):
            if len(group) < 2:
                continue
            names = ", ".join(f"'{task.title}' ({task.pet_name or 'unassigned'})" for task in group)
            warnings.append(f"Conflict at {moment.strftime('%H:%M')}: {names} are all scheduled at the same time.")
        return warnings

    def filter_tasks(
        self, completed: bool | None = None, pet_name: str | None = None
    ) -> list[CareTask]:
        """Return this scheduler's tasks narrowed by completion status and/or pet name.

        Requesting completed=False excludes tasks that aren't due yet (see
        CareTask.is_due()).
        """
        tasks = self.tasks
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
            if completed is False:
                tasks = [task for task in tasks if task.is_due()]
        if pet_name is not None:
            tasks = [task for task in tasks if task.pet_name == pet_name]
        return tasks

    def mark_task_complete(self, task: CareTask) -> CareTask | None:
        """Mark a task complete and add its next occurrence (if it recurs) to this scheduler's tasks.

        Looks up the owning pet by task.pet_name so the new occurrence lands
        in that pet's task list too. If the task isn't tied to one of the
        owner's pets, it's just marked complete with no next occurrence.
        """
        pet = next((p for p in self.owner.pets if p.name == task.pet_name), None)
        if pet is None:
            task.mark_complete()
            return None

        next_task = pet.complete_task(task)
        if next_task is not None:
            self.tasks.append(next_task)
        return next_task

    def explain(self) -> str:
        """Return a human-readable explanation of why each task was included or skipped."""
        if self.schedule is None:
            self.build_schedule()

        lines: list[str] = []
        for scheduled in self.schedule.scheduled_tasks:
            start = scheduled.start_time.strftime("%H:%M")
            lines.append(
                f"Included '{scheduled.task.title}' at {start} "
                f"(priority={scheduled.task.priority}, weight={scheduled.task.priority_weight()})"
            )
        for task in self.schedule.skipped_tasks:
            lines.append(
                f"Skipped '{task.title}' — not enough time remaining "
                f"(needed {task.duration_minutes} min)"
            )
        for task in self.schedule.not_due_tasks:
            lines.append(f"Skipped '{task.title}' — not due until {task.due_date}")
        return "\n".join(lines) if lines else "No tasks to schedule."
