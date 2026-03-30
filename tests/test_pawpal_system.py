from datetime import date, time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def test_mark_complete_updates_task_status() -> None:
    task = Task(
        title="Morning walk",
        description="Take the dog outside for a walk.",
        duration_minutes=20,
        frequency="once",
        due_date=date(2026, 3, 29),
    )

    task.mark_complete(completed_on=date(2026, 3, 29))

    assert task.completed is True
    assert task.is_pending() is False
    assert task.is_due(on_date=date(2026, 3, 29)) is False


def test_complete_daily_task_creates_next_occurrence_for_tomorrow() -> None:
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(
        Task(
            title="Medication",
            description="Give medication after breakfast.",
            duration_minutes=10,
            frequency="daily",
            due_date=date(2026, 3, 29),
        )
    )

    next_task = pet.complete_task("Medication", completed_on=date(2026, 3, 29))

    assert next_task is not None
    assert next_task.due_date == date(2026, 3, 30)
    assert next_task.completed is False
    assert len(pet.tasks) == 2


def test_complete_weekly_task_creates_next_occurrence_for_next_week() -> None:
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(
        Task(
            title="Brush coat",
            description="Quick grooming session.",
            duration_minutes=20,
            frequency="weekly",
            due_date=date(2026, 3, 29),
        )
    )

    next_task = pet.complete_task("Brush coat", completed_on=date(2026, 3, 29))

    assert next_task is not None
    assert next_task.due_date == date(2026, 4, 5)


def test_add_task_increases_pet_task_count() -> None:
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task(
        title="Dinner feeding",
        description="Serve evening meal.",
        duration_minutes=10,
        due_date=date(2026, 3, 29),
    )

    starting_count = len(pet.tasks)
    pet.add_task(task)

    assert len(pet.tasks) == starting_count + 1
    assert pet.tasks[-1] == task


def test_filter_tasks_can_limit_results_by_pet_and_status() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    walk = Task(
        title="Morning walk",
        description="Take the dog outside.",
        duration_minutes=20,
        frequency="daily",
        due_date=date(2026, 3, 29),
    )
    feeding = Task(
        title="Dinner feeding",
        description="Serve evening meal.",
        duration_minutes=10,
        frequency="once",
        due_date=date(2026, 3, 29),
    )
    feeding.mark_complete(completed_on=date(2026, 3, 29))

    mochi.add_task(walk)
    luna.add_task(feeding)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)
    filtered_tasks = scheduler.filter_tasks(pet_name="Mochi", status="pending")

    assert len(filtered_tasks) == 1
    filtered_pet, filtered_task = filtered_tasks[0]
    assert filtered_pet.name == "Mochi"
    assert filtered_task.title == "Morning walk"


def test_sort_by_time_orders_earlier_tasks_first() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog", age=3)

    breakfast = Task(
        title="Breakfast",
        description="Serve morning meal.",
        duration_minutes=10,
        preferred_time=time(7, 30),
        priority=Priority.MEDIUM,
        due_date=date(2026, 3, 29),
    )
    walk = Task(
        title="Walk",
        description="Morning walk.",
        duration_minutes=20,
        preferred_time=time(8, 0),
        priority=Priority.HIGH,
        due_date=date(2026, 3, 29),
    )
    anytime_task = Task(
        title="Brush coat",
        description="Quick grooming.",
        duration_minutes=15,
        preferred_time=None,
        priority=Priority.LOW,
        due_date=date(2026, 3, 29),
    )

    pet.add_task(anytime_task)
    pet.add_task(walk)
    pet.add_task(breakfast)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    ordered_titles = [task.title for _, task in scheduler.sort_by_time(scheduler.collect_all_tasks())]

    assert ordered_titles == ["Breakfast", "Walk", "Brush coat"]


def test_sort_by_time_orders_by_due_date_before_clock_time() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog", age=3)

    tomorrow_medication = Task(
        title="Medication",
        description="Tomorrow morning medication.",
        duration_minutes=10,
        preferred_time=time(7, 0),
        due_date=date(2026, 3, 30),
    )
    today_feeding = Task(
        title="Dinner feeding",
        description="Serve dinner tonight.",
        duration_minutes=10,
        preferred_time=time(18, 0),
        due_date=date(2026, 3, 29),
    )

    pet.add_task(tomorrow_medication)
    pet.add_task(today_feeding)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    ordered_titles = [task.title for _, task in scheduler.sort_by_time(scheduler.collect_all_tasks())]

    assert ordered_titles == ["Dinner feeding", "Medication"]


def test_detect_conflicts_finds_overlapping_preferred_times() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog", age=3)

    pet.add_task(
        Task(
            title="Morning walk",
            description="Walk around the block.",
            duration_minutes=20,
            preferred_time=time(8, 0),
            due_date=date(2026, 3, 29),
        )
    )
    pet.add_task(
        Task(
            title="Medication",
            description="Give medication after breakfast.",
            duration_minutes=10,
            preferred_time=time(8, 10),
            due_date=date(2026, 3, 29),
        )
    )
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts(on_date=date(2026, 3, 29))

    assert len(conflicts) == 1
    assert conflicts[0]["task_a"] == "Morning walk"
    assert conflicts[0]["task_b"] == "Medication"
    assert conflicts[0]["overlap_minutes"] == 10


def test_detect_conflicts_flags_tasks_with_the_exact_same_start_time() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog", age=3)

    pet.add_task(
        Task(
            title="Breakfast",
            description="Serve breakfast.",
            duration_minutes=15,
            preferred_time=time(8, 0),
            due_date=date(2026, 3, 29),
        )
    )
    pet.add_task(
        Task(
            title="Medication",
            description="Give medication with breakfast.",
            duration_minutes=5,
            preferred_time=time(8, 0),
            due_date=date(2026, 3, 29),
        )
    )
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts(on_date=date(2026, 3, 29))

    assert len(conflicts) == 1
    assert conflicts[0]["task_a"] == "Breakfast"
    assert conflicts[0]["task_b"] == "Medication"
    assert conflicts[0]["overlap_minutes"] == 5


def test_generate_daily_schedule_only_uses_tasks_due_today() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=40)
    pet = Pet(name="Mochi", species="dog", age=3)

    pet.add_task(
        Task(
            title="Evening feeding",
            description="Serve dinner.",
            duration_minutes=10,
            preferred_time=time(18, 0),
            priority=Priority.HIGH,
            due_date=date(2026, 3, 29),
        )
    )
    pet.add_task(
        Task(
            title="Morning walk",
            description="Walk before work.",
            duration_minutes=20,
            preferred_time=time(8, 0),
            priority=Priority.HIGH,
            due_date=date(2026, 3, 29),
        )
    )
    pet.add_task(
        Task(
            title="Medication",
            description="Tomorrow's medication.",
            duration_minutes=10,
            preferred_time=time(8, 0),
            priority=Priority.HIGH,
            due_date=date(2026, 3, 30),
        )
    )
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule(on_date=date(2026, 3, 29))
    scheduled_titles = [item["task_title"] for item in schedule["scheduled"]]

    assert scheduled_titles == ["Morning walk", "Evening feeding"]
    assert schedule["minutes_used"] == 30


def test_generate_daily_schedule_handles_pet_with_no_tasks() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=40)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule(on_date=date(2026, 3, 29))

    assert schedule["scheduled"] == []
    assert schedule["skipped"] == []
    assert schedule["conflicts"] == []
    assert schedule["minutes_used"] == 0
    assert schedule["minutes_remaining"] == 40


def test_complete_task_reuses_existing_future_occurrence_instead_of_duplicating() -> None:
    pet = Pet(name="Mochi", species="dog", age=3)
    existing_next_task = Task(
        title="Medication",
        description="Tomorrow's medication.",
        duration_minutes=10,
        frequency="daily",
        due_date=date(2026, 3, 30),
    )
    pet.add_task(
        Task(
            title="Medication",
            description="Today's medication.",
            duration_minutes=10,
            frequency="daily",
            due_date=date(2026, 3, 29),
        )
    )
    pet.add_task(existing_next_task)

    next_task = pet.complete_task("Medication", task_due_date=date(2026, 3, 29), completed_on=date(2026, 3, 29))

    assert next_task == existing_next_task
    assert len(pet.tasks) == 2
