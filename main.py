from __future__ import annotations

from pawpal_system import CareTask, Owner, Pet, Scheduler


def _prompt_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a whole number.")


def _add_tasks(pet: Pet) -> None:
    print(f"\nAdd care tasks for {pet.name} (leave title blank to stop):")
    while True:
        title = input("  Task title: ").strip()
        if not title:
            break
        duration = _prompt_int("  Duration (minutes): ")
        priority = input("  Priority (low/medium/high): ").strip().lower()
        try:
            pet.add_task(CareTask(title=title, duration_minutes=duration, priority=priority))
        except ValueError as exc:
            print(f"  {exc}")


def _add_pets(owner: Owner) -> None:
    print("\nAdd pets (leave name blank to stop):")
    while True:
        name = input("  Pet name: ").strip()
        if not name:
            break
        species = input("  Species: ").strip()
        pet = Pet(name=name, species=species)
        _add_tasks(pet)
        owner.add_pet(pet)


def main() -> None:
    print("=== PawPal+ CLI ===")
    name = input("Owner name: ").strip()
    available_minutes = _prompt_int("Available minutes today: ")
    preferred_start_time = input("Preferred start time (HH:MM, 24h): ").strip()

    owner = Owner(
        name=name,
        available_minutes=available_minutes,
        preferred_start_time=preferred_start_time,
    )
    _add_pets(owner)

    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    print("\n=== Schedule ===")
    print(scheduler.schedule.summary())
    print("\n=== Explanation ===")
    print(scheduler.explain())


if __name__ == "__main__":
    main()
