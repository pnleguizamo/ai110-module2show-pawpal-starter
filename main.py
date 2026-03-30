from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def print_schedule(schedule: dict[str, object]) -> None:
    print("Today's Schedule")
    print("=" * 16)
    print(f"Owner: {schedule['owner_name']}")
    print()

    scheduled_items = schedule["scheduled"]
    if scheduled_items:
        print("Scheduled Tasks:")
        for index, item in enumerate(scheduled_items, start=1):
            print(
                f"{index}. {item['task_title']} for {item['pet_name']} at {item['preferred_time']}"
            )
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
    owner = Owner(name="Jordan", available_minutes_per_day=60)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    mochi.add_task(
        Task(
            title="Morning walk",
            description="Neighborhood walk before work.",
            duration_minutes=20,
            preferred_time=time(8, 0),
            frequency="daily",
            priority=Priority.HIGH,
        )
    )
    mochi.add_task(
        Task(
            title="Dinner feeding",
            description="Serve evening meal.",
            duration_minutes=10,
            preferred_time=time(18, 0),
            frequency="daily",
            priority=Priority.HIGH,
        )
    )
    luna.add_task(
        Task(
            title="Play session",
            description="Interactive play with feather toy.",
            duration_minutes=15,
            preferred_time=time(14, 30),
            frequency="daily",
            priority=Priority.MEDIUM,
        )
    )
    luna.add_task(
        Task(
            title="Brush coat",
            description="Quick grooming session.",
            duration_minutes=20,
            preferred_time=time(19, 0),
            frequency="weekly",
            priority=Priority.LOW,
        )
    )

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()
    print_schedule(schedule)


if __name__ == "__main__":
    main()
