from pawpal_system import Pet, Task


def test_task_mark_complete_updates_completion_status() -> None:
    task = Task(
        title="Morning walk",
        description="Take the dog outside for a walk.",
        duration_minutes=20,
    )

    task.mark_complete()

    assert task.completed is True
    assert task.is_pending() is False


def test_add_task_increases_pet_task_count() -> None:
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task(
        title="Dinner feeding",
        description="Serve evening meal.",
        duration_minutes=10,
    )

    starting_count = len(pet.tasks)
    pet.add_task(task)

    assert len(pet.tasks) == starting_count + 1
    assert pet.tasks[-1] == task
