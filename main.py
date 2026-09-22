from __future__ import annotations

from pawpal_system import CareTask, Owner, Pet, Scheduler


def build_demo_owner() -> Owner:
    owner = Owner(name="Dana", available_minutes=60, preferred_start_time="08:00")

    biscuit = Pet(name="Biscuit", species="Golden Retriever")
    # Tasks are added out of time order on purpose, to prove sort_by_time()
    # actually sorts rather than just echoing insertion order.
    biscuit.add_task(
        CareTask(title="Feeding", duration_minutes=10, priority="high", preferred_time="18:00")
    )
    biscuit.add_task(
        CareTask(title="Morning walk", duration_minutes=30, priority="high", preferred_time="07:00")
    )

    whiskers = Pet(name="Whiskers", species="Cat")
    whiskers.add_task(
        CareTask(
            title="Playtime", duration_minutes=20, priority="low", preferred_time="09:30"
        )
    )
    whiskers.add_task(
        CareTask(
            title="Litter box cleaning",
            duration_minutes=15,
            priority="medium",
            preferred_time="12:00",
            completed=True,
        )
    )
    # Same preferred_time as Biscuit's "Morning walk" above, on purpose, so
    # detect_time_conflicts() has a real cross-pet conflict to report.
    whiskers.add_task(
        CareTask(title="Medication", duration_minutes=5, priority="high", preferred_time="07:00")
    )

    owner.add_pet(biscuit)
    owner.add_pet(whiskers)
    return owner


def print_todays_schedule(scheduler: Scheduler) -> None:
    schedule = scheduler.schedule
    budget = scheduler.owner.get_time_budget()

    print("=== Today's Schedule ===")
    if schedule.scheduled_tasks:
        for scheduled in schedule.scheduled_tasks:
            task = scheduled.task
            start = scheduled.start_time.strftime("%H:%M")
            end = scheduled.end_time.strftime("%H:%M")
            pet = f" for {task.pet_name}" if task.pet_name else ""
            print(f"  {start}-{end}  {task.title}{pet} ({task.duration_minutes} min, {task.priority} priority)")
    else:
        print("  No tasks fit today's schedule.")

    if schedule.skipped_tasks:
        print("\nSkipped (not enough time left):")
        for task in schedule.skipped_tasks:
            pet = f" for {task.pet_name}" if task.pet_name else ""
            print(f"  {task.title}{pet} ({task.duration_minutes} min, {task.priority} priority)")

    print(
        f"\nTime used: {schedule.total_minutes_used}/{budget} min "
        f"({schedule.time_remaining(budget)} min remaining)"
    )


def print_sorted_by_time(scheduler: Scheduler) -> None:
    print("=== Tasks sorted by preferred time ===")
    for task in scheduler.sort_by_time():
        when = task.preferred_time or "no preferred time"
        print(f"  {when:>8}  {task.title} for {task.pet_name}")


def print_filtered_tasks(scheduler: Scheduler) -> None:
    print("\n=== Filter: pending tasks for Biscuit ===")
    for task in scheduler.filter_tasks(completed=False, pet_name="Biscuit"):
        print(f"  {task.title} ({task.priority} priority)")

    print("\n=== Filter: completed tasks (any pet) ===")
    completed = scheduler.filter_tasks(completed=True)
    if completed:
        for task in completed:
            print(f"  {task.title} for {task.pet_name}")
    else:
        print("  (none)")


def print_time_conflicts(scheduler: Scheduler) -> None:
    print("\n=== Conflict check ===")
    conflicts = scheduler.detect_time_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts found.")


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    print_todays_schedule(scheduler)

    print("\n=== Why this plan? ===")
    print(scheduler.explain())

    print()
    print_sorted_by_time(scheduler)
    print_filtered_tasks(scheduler)
    print_time_conflicts(scheduler)


if __name__ == "__main__":
    main()
