from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str

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
        self.tasks = tasks if tasks is not None else []

    def build_schedule(self) -> Schedule:
        pass

    def sort_by_priority(self) -> list[CareTask]:
        pass

    def explain(self) -> str:
        pass
