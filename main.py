from __future__ import annotations

from pawpal_system import CareTask, Owner, Pet, Scheduler


def build_demo_owner() -> Owner:
    owner = Owner(name="Dana", available_minutes=60, preferred_start_time="08:00")

    biscuit = Pet(name="Biscuit", species="Golden Retriever")
    biscuit.add_task(CareTask(title="Morning walk", duration_minutes=30, priority="high"))
    biscuit.add_task(CareTask(title="Feeding", duration_minutes=10, priority="high"))

    whiskers = Pet(name="Whiskers", species="Cat")
    whiskers.add_task(CareTask(title="Litter box cleaning", duration_minutes=15, priority="medium"))
    whiskers.add_task(CareTask(title="Playtime", duration_minutes=20, priority="low"))

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


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    print_todays_schedule(scheduler)

    print("\n=== Why this plan? ===")
    print(scheduler.explain())


if __name__ == "__main__":
    main()
