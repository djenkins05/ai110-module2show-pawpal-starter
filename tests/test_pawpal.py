from pawpal_system import CareTask, Pet


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
