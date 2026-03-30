from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import IntEnum


RECURRENCE_INTERVAL_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}

NON_RECURRING_FREQUENCIES = {"as needed", "once", "one-time"}


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


def _minutes_since_midnight(clock_time: time | None) -> int:
    """Convert a time value into total minutes after midnight."""
    if clock_time is None:
        return 24 * 60
    return clock_time.hour * 60 + clock_time.minute


def _format_clock_time(total_minutes: int) -> str:
    """Render a 24-hour minute offset as a user-friendly time string."""
    normalized_minutes = total_minutes % (24 * 60)
    hours = normalized_minutes // 60
    minutes = normalized_minutes % 60
    return time(hour=hours, minute=minutes).strftime("%I:%M %p").lstrip("0")


def _format_date_label(value: date) -> str:
    """Return a compact label for a calendar date."""
    return value.strftime("%b %d, %Y").replace(" 0", " ")


@dataclass
class Task:
    """Represents one care activity for a pet."""

    title: str
    description: str
    duration_minutes: int
    preferred_time: time | None = None
    frequency: str = "daily"
    due_date: date | None = None
    completed: bool = False
    completed_on: date | None = None
    priority: Priority = Priority.MEDIUM

    def __post_init__(self) -> None:
        """Validate the task and default it to today when no due date is given."""
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than 0 minutes.")
        if self.due_date is None:
            self.due_date = date.today()

    def recurrence_interval_days(self) -> int | None:
        """Return the recurrence interval in days when the task repeats."""
        frequency = self.frequency.lower()
        if frequency in RECURRENCE_INTERVAL_DAYS:
            return RECURRENCE_INTERVAL_DAYS[frequency]
        if frequency in NON_RECURRING_FREQUENCIES:
            return None
        raise ValueError(f"Unknown frequency: {self.frequency!r}")

    def is_recurring(self) -> bool:
        """Return whether this task should create another future occurrence."""
        return self.recurrence_interval_days() is not None

    def mark_complete(self, completed_on: date | None = None) -> None:
        """Mark this task instance as completed."""
        self.completed = True
        self.completed_on = date.today() if completed_on is None else completed_on

    def mark_incomplete(self) -> None:
        """Mark this task instance as not completed."""
        self.completed = False
        self.completed_on = None

    def is_pending(self) -> bool:
        """Return whether this task instance is still open."""
        return not self.completed

    def is_due(self, on_date: date | None = None) -> bool:
        """Return whether this task should be considered for the given day."""
        check_date = date.today() if on_date is None else on_date
        return self.is_pending() and self.due_date <= check_date

    def next_due_date(self) -> date | None:
        """Return this task instance's next due date or its recurring successor date."""
        if self.is_pending():
            return self.due_date

        interval_days = self.recurrence_interval_days()
        if interval_days is None or self.completed_on is None:
            return None

        return self.completed_on + timedelta(days=interval_days)

    def due_date_label(self, reference_date: date | None = None) -> str:
        """Return a friendly label for this task's due date."""
        check_date = date.today() if reference_date is None else reference_date
        if self.due_date == check_date:
            return "Today"
        return _format_date_label(self.due_date)

    def next_due_label(self) -> str:
        """Return a friendly label for the next due date in this task chain."""
        next_due = self.next_due_date()
        if next_due is None:
            return "Completed"
        if next_due == date.today():
            return "Today"
        return _format_date_label(next_due)

    def status_label(self, on_date: date | None = None) -> str:
        """Return a UI-friendly label for this task instance."""
        if self.completed:
            return "completed"
        if self.is_due(on_date=on_date):
            return "pending"
        return "upcoming"

    def get_priority_score(self) -> int:
        """Return the numeric score for the task priority."""
        return int(self.priority)

    def get_frequency_score(self) -> int:
        """Return a numeric weight based on how often the task occurs."""
        frequency_weights = {
            "daily": 3,
            "weekly": 2,
            "monthly": 1,
            "as needed": 0,
            "once": 0,
            "one-time": 0,
        }
        return frequency_weights.get(self.frequency.lower(), 1)

    def preferred_time_label(self) -> str:
        """Return the preferred time in a user-friendly format."""
        if self.preferred_time is None:
            return "Anytime"
        return self.preferred_time.strftime("%I:%M %p").lstrip("0")

    def preferred_time_window_label(self) -> str:
        """Return the preferred start and end window for this task."""
        if self.preferred_time is None:
            return "Anytime"

        start_minutes = _minutes_since_midnight(self.preferred_time)
        end_minutes = start_minutes + self.duration_minutes
        return f"{_format_clock_time(start_minutes)} - {_format_clock_time(end_minutes)}"

    def spawn_next_occurrence(self, completed_on: date | None = None) -> Task | None:
        """Create a future task instance for recurring work.

        Non-recurring tasks return ``None``. Daily, weekly, and monthly tasks
        are copied forward using ``completed_on + recurrence interval`` so the
        scheduler can treat the next occurrence as a normal task with its own
        due date.
        """
        interval_days = self.recurrence_interval_days()
        if interval_days is None:
            return None

        completion_date = date.today() if completed_on is None else completed_on
        return Task(
            title=self.title,
            description=self.description,
            duration_minutes=self.duration_minutes,
            preferred_time=self.preferred_time,
            frequency=self.frequency,
            due_date=completion_date + timedelta(days=interval_days),
            priority=self.priority,
        )


@dataclass
class Pet:
    """Stores pet information and the tasks associated with that pet."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task_title: str, task_due_date: date | None = None) -> Task:
        """Remove and return a task matching the given title and optional due date."""
        task = self.get_task(task_title, task_due_date=task_due_date)
        if task is None:
            raise ValueError(f"Task '{task_title}' was not found for pet '{self.name}'.")
        self.tasks.remove(task)
        return task

    def get_task(
        self,
        task_title: str,
        task_due_date: date | None = None,
        include_completed: bool = True,
    ) -> Task | None:
        """Return the best matching task for the given title and optional due date."""
        matches = [
            task
            for task in self.tasks
            if task.title == task_title and (task_due_date is None or task.due_date == task_due_date)
        ]
        if not include_completed:
            matches = [task for task in matches if task.is_pending()]
        if not matches:
            return None

        return sorted(
            matches,
            key=lambda task: (
                task.completed,
                task.due_date,
                _minutes_since_midnight(task.preferred_time),
            ),
        )[0]

    def get_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks for this pet."""
        return [task for task in self.tasks if task.is_pending()]

    def get_due_tasks(self, on_date: date | None = None) -> list[Task]:
        """Return all tasks due on or before the given day for this pet."""
        return [task for task in self.tasks if task.is_due(on_date=on_date)]

    def complete_task(
        self,
        task_title: str,
        task_due_date: date | None = None,
        completed_on: date | None = None,
    ) -> Task | None:
        """Complete one task instance and append its next recurrence if needed.

        The method finds the matching incomplete task, marks that specific
        occurrence complete, then creates and stores the next daily/weekly/monthly
        instance when the task frequency requires it. It returns the new future
        task when one is created, otherwise ``None``.
        """
        task = self.get_task(
            task_title,
            task_due_date=task_due_date,
            include_completed=False,
        )
        if task is None:
            raise ValueError(f"Task '{task_title}' was not found for pet '{self.name}'.")

        completion_date = date.today() if completed_on is None else completed_on
        task.mark_complete(completed_on=completion_date)

        next_task = task.spawn_next_occurrence(completed_on=completion_date)
        if next_task is None:
            return None

        duplicate = self.get_task(
            next_task.title,
            task_due_date=next_task.due_date,
            include_completed=False,
        )
        if duplicate is None:
            self.tasks.append(next_task)
            return next_task

        return duplicate

    def total_task_minutes(self, pending_only: bool = True, on_date: date | None = None) -> int:
        """Return the total minutes of this pet's tasks."""
        if pending_only and on_date is not None:
            relevant_tasks = self.get_due_tasks(on_date=on_date)
        elif pending_only:
            relevant_tasks = self.get_pending_tasks()
        else:
            relevant_tasks = self.tasks
        return sum(task.duration_minutes for task in relevant_tasks)


@dataclass
class Owner:
    """Manages multiple pets and provides task-level access across them."""

    name: str
    available_minutes_per_day: int
    pets: list[Pet] = field(default_factory=list)
    preferences: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate that the owner's available time is not negative."""
        if self.available_minutes_per_day < 0:
            raise ValueError("Available minutes per day cannot be negative.")

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> Pet:
        """Remove and return a pet that matches the given name."""
        for index, pet in enumerate(self.pets):
            if pet.name == pet_name:
                return self.pets.pop(index)
        raise ValueError(f"Pet '{pet_name}' was not found for owner '{self.name}'.")

    def get_pet(self, pet_name: str) -> Pet | None:
        """Return the pet with the given name if it exists."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task paired with its pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every incomplete task paired with its pet."""
        return [(pet, task) for pet, task in self.get_all_tasks() if task.is_pending()]

    def get_all_due_tasks(self, on_date: date | None = None) -> list[tuple[Pet, Task]]:
        """Return every task due on or before the given day paired with its pet."""
        return [(pet, task) for pet, task in self.get_all_tasks() if task.is_due(on_date=on_date)]

    def total_pending_minutes(self, on_date: date | None = None) -> int:
        """Return the total minutes of open tasks."""
        task_pairs = (
            self.get_all_due_tasks(on_date=on_date)
            if on_date is not None
            else self.get_all_pending_tasks()
        )
        return sum(task.duration_minutes for _, task in task_pairs)


class Scheduler:
    """Retrieves, organizes, and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner."""
        self.owner = owner

    def collect_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Gather every task from each pet."""
        return self.owner.get_all_tasks()

    def collect_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Gather incomplete tasks from each pet."""
        return self.owner.get_all_pending_tasks()

    def collect_due_tasks(self, on_date: date | None = None) -> list[tuple[Pet, Task]]:
        """Gather tasks due on or before the given day from each pet."""
        return self.owner.get_all_due_tasks(on_date=on_date)

    def filter_tasks(
        self,
        pet_name: str | None = None,
        status: str = "all",
    ) -> list[tuple[Pet, Task]]:
        """Return tasks filtered by pet name and completion status.

        This is a linear scan over every task owned by the scheduler's owner.
        ``pet_name`` narrows the results to one pet, while ``status`` keeps all
        tasks, only incomplete tasks, or only completed tasks.
        """
        status_value = status.lower()
        filtered_tasks: list[tuple[Pet, Task]] = []

        for pet, task in self.collect_all_tasks():
            if pet_name is not None and pet.name != pet_name:
                continue
            if status_value == "pending" and not task.is_pending():
                continue
            if status_value == "completed" and task.is_pending():
                continue
            filtered_tasks.append((pet, task))

        return filtered_tasks

    def sort_by_time(self, pet_task_pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return task pairs in chronological display order.

        The sort key favors earlier due dates first, then earlier preferred
        times, then incomplete tasks, then higher priority tasks. This keeps
        the displayed task list readable without changing which tasks the
        scheduler ultimately selects.
        """
        return sorted(pet_task_pairs, key=self._time_sort_key)

    def sort_tasks_by_time(self, pet_task_pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Backward-compatible wrapper for time-based sorting."""
        return self.sort_by_time(pet_task_pairs)

    def prioritize_tasks(self, on_date: date | None = None) -> list[tuple[Pet, Task]]:
        """Rank due tasks in the order they should be considered for scheduling.

        Only tasks due on or before ``on_date`` are included. They are then
        sorted by a greedy priority key: higher priority first, more frequent
        recurring work first, earlier preferred times first, and shorter tasks
        first when earlier factors tie.
        """
        due_tasks = self.collect_due_tasks(on_date=on_date)
        return sorted(due_tasks, key=self._task_selection_key)

    def mark_task_complete(
        self,
        pet_name: str,
        task_title: str,
        task_due_date: date | None = None,
        completed_on: date | None = None,
    ) -> Task | None:
        """Complete a named task for one pet and return any spawned recurrence.

        This is a small coordination method: it resolves the pet, delegates the
        completion work to ``Pet.complete_task()``, and surfaces the future task
        instance when recurring logic creates one.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' was not found for owner '{self.owner.name}'.")
        return pet.complete_task(
            task_title,
            task_due_date=task_due_date,
            completed_on=completed_on,
        )

    def detect_conflicts(
        self,
        pet_task_pairs: list[tuple[Pet, Task]] | None = None,
        on_date: date | None = None,
    ) -> list[dict[str, str | int]]:
        """Detect overlapping preferred-time windows among relevant tasks.

        The algorithm first sorts tasks by time, then walks forward comparing
        each task only against later tasks whose start times still fall inside
        the current task's window. Each overlap is returned as a warning record
        instead of raising an error so the app can show conflicts non-fatally.
        """
        relevant_tasks = self.collect_due_tasks(on_date=on_date) if pet_task_pairs is None else pet_task_pairs
        ordered_tasks = self.sort_by_time(relevant_tasks)
        conflicts: list[dict[str, str | int]] = []

        for index, (first_pet, first_task) in enumerate(ordered_tasks):
            first_window = self._task_time_window(first_task)
            if first_window is None:
                continue

            first_start, first_end = first_window
            for second_pet, second_task in ordered_tasks[index + 1 :]:
                second_window = self._task_time_window(second_task)
                if second_window is None:
                    continue

                second_start, second_end = second_window
                if second_start >= first_end:
                    break

                overlap_minutes = min(first_end, second_end) - max(first_start, second_start)
                if overlap_minutes <= 0:
                    continue

                conflicts.append(
                    {
                        "pet_a": first_pet.name,
                        "task_a": first_task.title,
                        "time_a": first_task.preferred_time_window_label(),
                        "pet_b": second_pet.name,
                        "task_b": second_task.title,
                        "time_b": second_task.preferred_time_window_label(),
                        "overlap_minutes": overlap_minutes,
                        "warning": (
                            f"{first_task.title} for {first_pet.name} overlaps with "
                            f"{second_task.title} for {second_pet.name}."
                        ),
                    }
                )

        return conflicts

    def generate_daily_schedule(
        self,
        available_minutes: int | None = None,
        on_date: date | None = None,
    ) -> dict[str, object]:
        """Build a greedy daily schedule that fits inside the time budget.

        The scheduler ranks due tasks with ``prioritize_tasks()``, walks through
        them once, and keeps each task only if its duration still fits within
        the remaining minutes for the day. Chosen tasks are re-sorted by time
        for display, while overflow tasks are returned in ``skipped``.
        """
        total_available = (
            self.owner.available_minutes_per_day
            if available_minutes is None
            else available_minutes
        )
        if total_available < 0:
            raise ValueError("Available minutes cannot be negative.")

        check_date = date.today() if on_date is None else on_date
        selected_tasks: list[tuple[Pet, Task]] = []
        skipped: list[dict[str, object]] = []
        minutes_used = 0

        for pet, task in self.prioritize_tasks(on_date=check_date):
            if minutes_used + task.duration_minutes <= total_available:
                selected_tasks.append((pet, task))
                minutes_used += task.duration_minutes
            else:
                skipped.append(
                    {
                        "pet_name": pet.name,
                        "task_title": task.title,
                        "duration_minutes": task.duration_minutes,
                        "preferred_time": task.preferred_time_label(),
                        "due_date": task.due_date_label(reference_date=check_date),
                        "reason": "Skipped because it would exceed the available time for today.",
                    }
                )

        scheduled = [
            self._build_scheduled_item(pet, task, check_date)
            for pet, task in self.sort_by_time(selected_tasks)
        ]

        return {
            "owner_name": self.owner.name,
            "schedule_date": check_date.isoformat(),
            "scheduled": scheduled,
            "skipped": skipped,
            "conflicts": self.detect_conflicts(selected_tasks, on_date=check_date),
            "minutes_used": minutes_used,
            "minutes_remaining": total_available - minutes_used,
        }

    def tasks_by_pet(self) -> dict[str, list[Task]]:
        """Return a mapping of pet names to their task lists."""
        return {pet.name: list(pet.tasks) for pet in self.owner.pets}

    def _time_sort_key(self, pet_task_pair: tuple[Pet, Task]) -> tuple[date, int, int, int, str]:
        """Return the tuple used to order tasks for chronological display."""
        _, task = pet_task_pair
        return (
            task.due_date,
            _minutes_since_midnight(task.preferred_time),
            task.completed,
            -task.get_priority_score(),
            task.title.lower(),
        )

    def _task_selection_key(self, pet_task_pair: tuple[Pet, Task]) -> tuple[int, int, int, int]:
        """Return the tuple used by the greedy scheduling priority algorithm."""
        _, task = pet_task_pair
        return (
            -task.get_priority_score(),
            -task.get_frequency_score(),
            _minutes_since_midnight(task.preferred_time),
            task.duration_minutes,
        )

    def _task_time_window(self, task: Task) -> tuple[int, int] | None:
        """Return a task's preferred start/end window in minutes after midnight."""
        if task.preferred_time is None:
            return None

        start_minutes = _minutes_since_midnight(task.preferred_time)
        return (start_minutes, start_minutes + task.duration_minutes)

    def _build_scheduled_item(self, pet: Pet, task: Task, on_date: date) -> dict[str, object]:
        """Build the structured row returned for one scheduled task."""
        return {
            "pet_name": pet.name,
            "task_title": task.title,
            "description": task.description,
            "duration_minutes": task.duration_minutes,
            "preferred_time": task.preferred_time_label(),
            "time_window": task.preferred_time_window_label(),
            "frequency": task.frequency,
            "due_date": task.due_date_label(reference_date=on_date),
            "priority": task.priority.name.lower(),
            "status": task.status_label(on_date=on_date),
            "next_due": task.next_due_label(),
            "reason": self.explain_task_selection(task, on_date=on_date),
        }

    def explain_task_selection(self, task: Task, on_date: date | None = None) -> str:
        """Explain why a task was included in the daily schedule."""
        check_date = date.today() if on_date is None else on_date
        return (
            f"Selected because it is a {task.priority.name.lower()} priority "
            f"{task.frequency} task due {task.due_date_label(reference_date=check_date).lower()} "
            f"and it fits within today's available time."
        )
