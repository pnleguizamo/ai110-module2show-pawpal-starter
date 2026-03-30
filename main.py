from datetime import date, time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def print_task_list(title: str, tasks: list[tuple[Pet, Task]], reference_date: date) -> None:
    print(title)
    print("-" * len(title))
    if not tasks:
        print("No tasks.")
        print()
        return

    for pet, task in tasks:
        print(
            f"- {pet.name}: {task.title} | due {task.due_date_label(reference_date)} | "
            f"time {task.preferred_time_label()} | status {task.status_label(on_date=reference_date)}"
        )
    print()


def print_conflicts(conflicts: list[dict[str, str | int]]) -> None:
    print("Conflict Warnings")
    print("-----------------")
    if not conflicts:
        print("No conflicts detected.")
        print()
        return

    for conflict in conflicts:
        print(
            f"- Warning: {conflict['warning']} "
            f"Overlap: {conflict['overlap_minutes']} minutes."
        )
    print()


def print_schedule(schedule: dict[str, object]) -> None:
    print("Today's Schedule")
    print("================")
    print(f"Owner: {schedule['owner_name']}")
    print(f"Date: {schedule['schedule_date']}")
    print()

    scheduled_items = schedule["scheduled"]
    if scheduled_items:
        print("Scheduled Tasks:")
        for index, item in enumerate(scheduled_items, start=1):
            print(
                f"{index}. {item['task_title']} for {item['pet_name']} at {item['preferred_time']}"
            )
            print(f"   Due: {item['due_date']}")
            print(f"   Window: {item['time_window']}")
            print(f"   Duration: {item['duration_minutes']} minutes")
            print(f"   Priority: {item['priority']}")
            print(f"   Reason: {item['reason']}")
    else:
        print("No tasks scheduled for today.")

    skipped_items = schedule["skipped"]
    if skipped_items:
        print()
        print("Skipped Tasks:")
        for item in skipped_items:
            print(f"- {item['task_title']} for {item['pet_name']}: {item['reason']}")

    print()
    print(f"Minutes used: {schedule['minutes_used']}")
    print(f"Minutes remaining: {schedule['minutes_remaining']}")


def main() -> None:
    today = date.today()
    owner = Owner(name="Jordan", available_minutes_per_day=60)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    # Intentionally add these out of time order to demonstrate sorting.
    mochi.add_task(
        Task(
            title="Dinner feeding",
            description="Serve evening meal.",
            duration_minutes=10,
            preferred_time=time(18, 0),
            frequency="daily",
            due_date=today,
            priority=Priority.HIGH,
        )
    )
    mochi.add_task(
        Task(
            title="Morning walk",
            description="Neighborhood walk before work.",
            duration_minutes=20,
            preferred_time=time(8, 0),
            frequency="daily",
            due_date=today,
            priority=Priority.HIGH,
        )
    )
    mochi.add_task(
        Task(
            title="Medication",
            description="Give daily medication with breakfast.",
            duration_minutes=10,
            preferred_time=time(8, 0),
            frequency="daily",
            due_date=today,
            priority=Priority.HIGH,
        )
    )
    luna.add_task(
        Task(
            title="Brush coat",
            description="Quick grooming session.",
            duration_minutes=20,
            preferred_time=time(19, 0),
            frequency="weekly",
            due_date=today,
            priority=Priority.LOW,
        )
    )
    luna.add_task(
        Task(
            title="Play session",
            description="Interactive play with feather toy.",
            duration_minutes=15,
            preferred_time=time(14, 30),
            frequency="daily",
            due_date=today,
            priority=Priority.MEDIUM,
        )
    )

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)

    print_task_list("Tasks In Added Order", scheduler.collect_all_tasks(), today)
    print_task_list("Tasks Sorted By Time", scheduler.sort_by_time(scheduler.collect_all_tasks()), today)
    print_task_list("Filtered: Mochi Pending Tasks", scheduler.filter_tasks(pet_name="Mochi", status="pending"), today)
    print_conflicts(scheduler.detect_conflicts(on_date=today))

    next_daily_task = scheduler.mark_task_complete(
        "Mochi",
        "Morning walk",
        task_due_date=today,
        completed_on=today,
    )
    next_weekly_task = scheduler.mark_task_complete(
        "Luna",
        "Brush coat",
        task_due_date=today,
        completed_on=today,
    )

    print("Recurring Task Demo")
    print("-------------------")
    print(
        f"Completed Morning walk. New occurrence due: "
        f"{next_daily_task.due_date.isoformat() if next_daily_task else 'none'}"
    )
    print(
        f"Completed Brush coat. New occurrence due: "
        f"{next_weekly_task.due_date.isoformat() if next_weekly_task else 'none'}"
    )
    print()

    print_task_list(
        "Filtered: Completed Tasks",
        scheduler.filter_tasks(status="completed"),
        today,
    )
    print_task_list(
        "Filtered: Pending Tasks After Recurrence",
        scheduler.filter_tasks(status="pending"),
        today,
    )

    schedule = scheduler.generate_daily_schedule(on_date=today)
    print_schedule(schedule)


if __name__ == "__main__":
    main()
