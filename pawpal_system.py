from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import ClassVar


def _add_minutes(moment: time, minutes: int) -> time:
    combined = datetime.combine(date.today(), moment) + timedelta(minutes=minutes)
    return combined.time()


def _parse_time(value: str) -> time:
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
    # How often this task recurs; controls when a completed task rolls back
    # to pending (see FREQUENCY_INTERVALS / rollover()).
    frequency: str = "once"
    completed: bool = False
    # Date the task was last marked complete; used by rollover() to tell
    # whether enough time has passed to reset it. None means never completed.
    completed_at: date | None = None
    # Set by Pet.add_task() so a flattened task list (e.g. from
    # Owner.get_all_tasks()) can still be traced back to its pet.
    pet_name: str | None = None

    PRIORITY_WEIGHTS: ClassVar[dict[str, int]] = {"low": 1, "medium": 2, "high": 3}
    # Days after completion before the task resets to pending. "once" maps to
    # None, meaning it never resets on its own.
    FREQUENCY_INTERVALS: ClassVar[dict[str, int | None]] = {
        "once": None,
        "daily": 1,
        "weekly": 7,
    }

    def __post_init__(self) -> None:
        self.priority = self.priority.strip().lower()
        if self.priority not in self.PRIORITY_WEIGHTS:
            valid = ", ".join(self.PRIORITY_WEIGHTS)
            raise ValueError(f"Unknown priority {self.priority!r}; expected one of: {valid}")

        self.frequency = self.frequency.strip().lower()
        if self.frequency not in self.FREQUENCY_INTERVALS:
            valid = ", ".join(self.FREQUENCY_INTERVALS)
            raise ValueError(f"Unknown frequency {self.frequency!r}; expected one of: {valid}")

    def priority_weight(self) -> int:
        return self.PRIORITY_WEIGHTS[self.priority]

    def mark_complete(self, today: date | None = None) -> None:
        self.completed = True
        self.completed_at = today or date.today()

    def rollover(self, today: date | None = None) -> None:
        if not self.completed or self.completed_at is None:
            return

        interval = self.FREQUENCY_INTERVALS[self.frequency]
        if interval is None:
            return

        today = today or date.today()
        if (today - self.completed_at).days >= interval:
            self.completed = False
            self.completed_at = None

    def __str__(self) -> str:
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
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: CareTask) -> None:
        self.tasks.remove(task)

    def get_tasks(self) -> list[CareTask]:
        return list(self.tasks)


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferred_start_time: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def get_all_tasks(self) -> list[CareTask]:
        return [task for pet in self.pets for task in pet.get_tasks()]

    def get_time_budget(self) -> int:
        return self.available_minutes


@dataclass
class ScheduledTask:
    task: CareTask
    start_time: time
    end_time: time


@dataclass
class Schedule:
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    skipped_tasks: list[CareTask] = field(default_factory=list)
    total_minutes_used: int = 0

    def add_scheduled_task(self, task: CareTask, start: time) -> None:
        end = _add_minutes(start, task.duration_minutes)
        self.scheduled_tasks.append(ScheduledTask(task=task, start_time=start, end_time=end))
        self.total_minutes_used += task.duration_minutes

    def time_remaining(self, budget: int) -> int:
        return budget - self.total_minutes_used

    def summary(self) -> str:
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

        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner, tasks: list[CareTask] | None = None) -> None:
        self.owner = owner
        # Defaults to every task the owner's pets need; callers can still pass
        # an explicit list to test the scheduling logic in isolation.
        self.tasks = tasks if tasks is not None else owner.get_all_tasks()
        # Holds the most recently built Schedule so explain() has something
        # to describe after the fact (mirrors the Scheduler *-- Schedule
        # composition in the UML).
        self.schedule: Schedule | None = None

    def build_schedule(self) -> Schedule:
        budget = self.owner.get_time_budget()
        current_time = _parse_time(self.owner.preferred_start_time)

        for task in self.tasks:
            task.rollover()

        schedule = Schedule()
        for task in self.sort_by_priority():
            if task.completed:
                continue
            if schedule.total_minutes_used + task.duration_minutes <= budget:
                schedule.add_scheduled_task(task, current_time)
                current_time = _add_minutes(current_time, task.duration_minutes)
            else:
                schedule.skipped_tasks.append(task)

        self.schedule = schedule
        return schedule

    def sort_by_priority(self) -> list[CareTask]:
        return sorted(self.tasks, key=lambda task: task.priority_weight(), reverse=True)

    def mark_task_complete(self, task: CareTask) -> None:
        task.mark_complete()

    def explain(self) -> str:
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
        return "\n".join(lines) if lines else "No tasks to schedule."
