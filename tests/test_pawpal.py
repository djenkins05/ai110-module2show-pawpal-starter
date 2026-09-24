from datetime import date, time

import pytest

from pawpal_system import CareTask, Owner, Pet, Schedule, ScheduledTask, Scheduler


def test_mark_complete_changes_status():
    task = CareTask(title="Walk", duration_minutes=15, priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Rex", species="Dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(CareTask(title="Walk", duration_minutes=15, priority="high"))

    assert len(pet.get_tasks()) == 1


def test_scheduled_tasks_sorted_by_time_out_of_insertion_order():
    schedule = Schedule()
    late_task = CareTask(title="Dinner", duration_minutes=10, priority="medium")
    early_task = CareTask(title="Breakfast", duration_minutes=10, priority="medium")
    schedule.scheduled_tasks.append(
        ScheduledTask(task=late_task, start_time=time(18, 0), end_time=time(18, 10))
    )
    schedule.scheduled_tasks.append(
        ScheduledTask(task=early_task, start_time=time(8, 0), end_time=time(8, 10))
    )

    ordered = schedule.get_scheduled_tasks_sorted_by_time()

    assert [scheduled.task.title for scheduled in ordered] == ["Breakfast", "Dinner"]


def test_filter_tasks_by_pet_and_status():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    dog = Pet(name="Rex", species="dog")
    cat = Pet(name="Momo", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    walk = CareTask(title="Walk", duration_minutes=15, priority="high")
    walk.mark_complete()
    dog.add_task(walk)
    dog.add_task(CareTask(title="Feed", duration_minutes=5, priority="medium"))
    cat.add_task(CareTask(title="Litter box", duration_minutes=5, priority="low"))

    assert [task.title for task in owner.filter_tasks(pet_name="Rex")] == ["Walk", "Feed"]
    assert [task.title for task in owner.filter_tasks(completed=True)] == ["Walk"]
    assert [task.title for task in owner.filter_tasks(pet_name="Momo", completed=False)] == [
        "Litter box"
    ]


def test_completing_daily_task_creates_next_occurrence_due_tomorrow():
    pet = Pet(name="Rex", species="dog")
    feed = CareTask(title="Feed", duration_minutes=5, priority="medium", frequency="daily")
    pet.add_task(feed)

    next_task = pet.complete_task(feed, today=date(2026, 1, 1))

    assert feed.completed is True
    assert next_task is not None
    assert next_task is not feed
    assert next_task.completed is False
    assert next_task.title == "Feed"
    assert next_task.frequency == "daily"
    assert next_task.pet_name == "Rex"
    assert next_task.due_date == date(2026, 1, 2)
    assert [task.title for task in pet.get_tasks()] == ["Feed", "Feed"]
    assert [task.completed for task in pet.get_tasks()] == [True, False]


def test_completing_weekly_task_creates_next_occurrence_due_in_a_week():
    pet = Pet(name="Rex", species="dog")
    groom = CareTask(title="Grooming", duration_minutes=30, priority="low", frequency="weekly")
    pet.add_task(groom)

    next_task = pet.complete_task(groom, today=date(2026, 1, 1))

    assert next_task.due_date == date(2026, 1, 8)


def test_is_due_gates_pending_task_until_its_due_date():
    task = CareTask(
        title="Feed", duration_minutes=5, priority="medium", due_date=date(2026, 1, 2)
    )

    assert task.is_due(today=date(2026, 1, 1)) is False
    assert task.is_due(today=date(2026, 1, 2)) is True
    assert task.is_due(today=date(2026, 1, 3)) is True


def test_build_schedule_excludes_task_not_yet_due():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    not_due = CareTask(
        title="Feed", duration_minutes=10, priority="high", due_date=date(2999, 1, 1)
    )
    pet.add_task(not_due)
    scheduler = Scheduler(owner)

    schedule = scheduler.build_schedule()

    assert schedule.scheduled_tasks == []
    assert schedule.not_due_tasks == [not_due]


def test_completing_one_time_task_creates_no_next_occurrence():
    pet = Pet(name="Rex", species="dog")
    vet_visit = CareTask(title="Vet visit", duration_minutes=30, priority="high", frequency="once")
    pet.add_task(vet_visit)

    next_task = pet.complete_task(vet_visit)

    assert next_task is None
    assert len(pet.get_tasks()) == 1


def test_scheduler_mark_task_complete_adds_next_occurrence_to_owner_and_scheduler():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    walk = CareTask(title="Walk", duration_minutes=15, priority="high", frequency="weekly")
    pet.add_task(walk)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    next_task = scheduler.mark_task_complete(walk)

    assert next_task is not None
    assert next_task in pet.get_tasks()
    assert next_task in scheduler.tasks
    assert len(scheduler.tasks) == 2


def test_detect_duplicate_tasks_flags_same_title_same_pet():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)

    first_walk = CareTask(title="Walk", duration_minutes=15, priority="high")
    second_walk = CareTask(title="walk", duration_minutes=20, priority="medium")
    pet.add_task(first_walk)
    pet.add_task(second_walk)
    pet.add_task(CareTask(title="Feed", duration_minutes=5, priority="low"))

    conflicts = owner.detect_duplicate_tasks()

    assert conflicts == [(first_walk, second_walk)]


def test_scheduler_sort_by_time_orders_tasks_added_out_of_order():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    tasks = [
        CareTask(title="Dinner", duration_minutes=10, priority="medium", preferred_time="18:00"),
        CareTask(title="Breakfast", duration_minutes=10, priority="medium", preferred_time="07:00"),
        CareTask(title="Lunch", duration_minutes=10, priority="medium", preferred_time="12:00"),
        CareTask(title="No fixed time", duration_minutes=5, priority="low"),
    ]
    scheduler = Scheduler(owner, tasks=tasks)

    ordered = scheduler.sort_by_time()

    assert [task.title for task in ordered] == ["Breakfast", "Lunch", "Dinner", "No fixed time"]


def test_scheduler_filter_tasks_by_status_and_pet():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    walk = CareTask(title="Walk", duration_minutes=15, priority="high")
    walk.mark_complete()
    pet.add_task(walk)
    pet.add_task(CareTask(title="Feed", duration_minutes=5, priority="medium"))
    scheduler = Scheduler(owner, tasks=pet.get_tasks())

    assert [task.title for task in scheduler.filter_tasks(completed=True)] == ["Walk"]
    assert [task.title for task in scheduler.filter_tasks(pet_name="Rex")] == ["Walk", "Feed"]
    assert scheduler.filter_tasks(completed=False, pet_name="Rex")[0].title == "Feed"


def test_detect_duplicate_tasks_ignores_completed_task():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)

    done_walk = CareTask(title="Walk", duration_minutes=15, priority="high")
    done_walk.mark_complete()
    pending_walk = CareTask(title="Walk", duration_minutes=15, priority="high")
    pet.add_task(done_walk)
    pet.add_task(pending_walk)

    assert owner.detect_duplicate_tasks() == []


def test_detect_time_conflicts_flags_cross_pet_same_time():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    dog = Pet(name="Rex", species="dog")
    cat = Pet(name="Momo", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(CareTask(title="Walk", duration_minutes=15, priority="high", preferred_time="07:00"))
    cat.add_task(
        CareTask(title="Feed cat", duration_minutes=5, priority="high", preferred_time="07:00")
    )
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "07:00" in warnings[0]
    assert "Walk" in warnings[0] and "Feed cat" in warnings[0]


def test_detect_time_conflicts_returns_empty_list_when_no_overlap():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    pet.add_task(CareTask(title="Walk", duration_minutes=15, priority="high", preferred_time="07:00"))
    pet.add_task(CareTask(title="Feed", duration_minutes=5, priority="high", preferred_time="18:00"))
    pet.add_task(CareTask(title="Play", duration_minutes=10, priority="low"))
    scheduler = Scheduler(owner)

    assert scheduler.detect_time_conflicts() == []


def test_build_schedule_happy_path_schedules_multiple_tasks_across_pets_by_priority():
    owner = Owner(name="Jordan", available_minutes=120, preferred_start_time="09:00")
    dog = Pet(name="Rex", species="dog")
    cat = Pet(name="Momo", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(CareTask(title="Walk", duration_minutes=30, priority="high"))
    cat.add_task(CareTask(title="Feed", duration_minutes=20, priority="medium"))
    dog.add_task(CareTask(title="Play", duration_minutes=10, priority="low"))
    scheduler = Scheduler(owner)

    schedule = scheduler.build_schedule()

    assert [scheduled.task.title for scheduled in schedule.scheduled_tasks] == ["Walk", "Feed", "Play"]
    assert schedule.skipped_tasks == []
    assert schedule.not_due_tasks == []
    assert schedule.total_minutes_used == 60
    assert schedule.scheduled_tasks[0].start_time == time(9, 0)
    assert schedule.scheduled_tasks[1].start_time == time(9, 30)
    assert schedule.scheduled_tasks[2].start_time == time(9, 50)


def test_pet_with_no_tasks_produces_empty_schedule():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    assert pet.get_tasks() == []
    scheduler = Scheduler(owner)

    schedule = scheduler.build_schedule()

    assert schedule.scheduled_tasks == []
    assert schedule.skipped_tasks == []
    assert schedule.total_minutes_used == 0


def test_owner_with_no_pets_has_no_tasks_and_no_duplicate_conflicts():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")

    assert owner.get_all_tasks() == []
    assert owner.detect_duplicate_tasks() == []


def test_two_tasks_at_exact_same_preferred_time_on_same_pet_flagged_as_conflict():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    pet.add_task(CareTask(title="Walk", duration_minutes=15, priority="high", preferred_time="07:00"))
    pet.add_task(CareTask(title="Brush", duration_minutes=5, priority="low", preferred_time="07:00"))
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Brush" in warnings[0]


def test_build_schedule_task_exactly_filling_budget_is_included_boundary():
    owner = Owner(name="Jordan", available_minutes=30, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    exact_fit = CareTask(title="Groom", duration_minutes=30, priority="high")
    overflow = CareTask(title="Play", duration_minutes=5, priority="low")
    pet.add_task(exact_fit)
    pet.add_task(overflow)
    scheduler = Scheduler(owner)

    schedule = scheduler.build_schedule()

    assert [scheduled.task.title for scheduled in schedule.scheduled_tasks] == ["Groom"]
    assert schedule.total_minutes_used == 30
    assert [task.title for task in schedule.skipped_tasks] == ["Play"]


def test_build_schedule_with_zero_available_minutes_skips_everything():
    owner = Owner(name="Jordan", available_minutes=0, preferred_start_time="09:00")
    pet = Pet(name="Rex", species="dog")
    owner.add_pet(pet)
    task = CareTask(title="Feed", duration_minutes=5, priority="high")
    pet.add_task(task)
    scheduler = Scheduler(owner)

    schedule = scheduler.build_schedule()

    assert schedule.scheduled_tasks == []
    assert schedule.skipped_tasks == [task]
    assert schedule.total_minutes_used == 0


def test_sort_by_priority_ties_preserve_insertion_order():
    owner = Owner(name="Jordan", available_minutes=60, preferred_start_time="09:00")
    tasks = [
        CareTask(title="A", duration_minutes=5, priority="medium"),
        CareTask(title="B", duration_minutes=5, priority="medium"),
        CareTask(title="C", duration_minutes=5, priority="medium"),
    ]
    scheduler = Scheduler(owner, tasks=tasks)

    ordered = scheduler.sort_by_priority()

    assert [task.title for task in ordered] == ["A", "B", "C"]


def test_care_task_rejects_unknown_priority():
    with pytest.raises(ValueError):
        CareTask(title="Bad", duration_minutes=5, priority="urgent")


def test_care_task_rejects_unknown_frequency():
    with pytest.raises(ValueError):
        CareTask(title="Bad", duration_minutes=5, priority="low", frequency="monthly")


def test_care_task_rejects_unparseable_preferred_time():
    with pytest.raises(ValueError):
        CareTask(title="Bad", duration_minutes=5, priority="low", preferred_time="not a time")
