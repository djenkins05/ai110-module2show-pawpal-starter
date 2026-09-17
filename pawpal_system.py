from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import ClassVar


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str
    # Set by Pet.add_task() so a flattened task list (e.g. from
    # Owner.get_all_tasks()) can still be traced back to its pet.
    pet_name: str | None = None

    PRIORITY_WEIGHTS: ClassVar[dict[str, int]] = {"low": 1, "medium": 2, "high": 3}

    def priority_weight(self) -> int:
        pass

    def __str__(self) -> str:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        pass

    def remove_task(self, task: CareTask) -> None:
        pass

    def get_tasks(self) -> list[CareTask]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferred_start_time: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[CareTask]:
        pass

    def get_time_budget(self) -> int:
        pass


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
        pass

    def time_remaining(self, budget: int) -> int:
        pass

    def summary(self) -> str:
        pass


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
        pass

    def sort_by_priority(self) -> list[CareTask]:
        pass

    def explain(self) -> str:
        pass
