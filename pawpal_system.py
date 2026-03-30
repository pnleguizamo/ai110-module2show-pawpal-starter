from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import IntEnum


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    """Represents one care activity for a pet."""

    title: str
    description: str
    duration_minutes: int
    preferred_time: time | None = None
    frequency: str = "daily"
    completed: bool = False
    priority: Priority = Priority.MEDIUM

    def __post_init__(self) -> None:
        """Validate that the task duration is positive."""
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than 0 minutes.")

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark the task as not completed."""
        self.completed = False

    def is_pending(self) -> bool:
        """Return whether the task still needs to be done."""
        return not self.completed

    def get_priority_score(self) -> int:
        """Return the numeric score for the task priority."""
        return int(self.priority)

    def get_frequency_score(self) -> int:
        """Return a numeric weight based on how often the task occurs."""
        frequency_weights = {
            "daily": 3,
            "twice daily": 3,
            "weekly": 2,
            "monthly": 1,
            "as needed": 0,
        }
        return frequency_weights.get(self.frequency.lower(), 1)

    def preferred_time_label(self) -> str:
        """Return the preferred time in a user-friendly format."""
        if self.preferred_time is None:
            return "Anytime"
        return self.preferred_time.strftime("%I:%M %p").lstrip("0")


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

    def remove_task(self, task_title: str) -> Task:
        """Remove and return a task that matches the given title."""
        for index, task in enumerate(self.tasks):
            if task.title == task_title:
                return self.tasks.pop(index)
        raise ValueError(f"Task '{task_title}' was not found for pet '{self.name}'.")

    def get_task(self, task_title: str) -> Task | None:
        """Return the task with the given title if it exists."""
        for task in self.tasks:
            if task.title == task_title:
                return task
        return None

    def get_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks for this pet."""
        return [task for task in self.tasks if task.is_pending()]

    def complete_task(self, task_title: str) -> None:
        """Mark a matching task as complete."""
        task = self.get_task(task_title)
        if task is None:
            raise ValueError(f"Task '{task_title}' was not found for pet '{self.name}'.")
        task.mark_complete()

    def total_task_minutes(self, pending_only: bool = True) -> int:
        """Return the total minutes of this pet's tasks."""
        relevant_tasks = self.get_pending_tasks() if pending_only else self.tasks
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

    def get_all_tasks(self, include_completed: bool = True) -> list[Task]:
        """Return tasks across all pets, optionally excluding completed ones."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            if include_completed:
                all_tasks.extend(pet.tasks)
            else:
                all_tasks.extend(pet.get_pending_tasks())
        return all_tasks

    def get_all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across every pet."""
        return self.get_all_tasks(include_completed=False)

    def total_pending_minutes(self) -> int:
        """Return the total minutes of all pending tasks."""
        return sum(task.duration_minutes for task in self.get_all_pending_tasks())


class Scheduler:
    """Retrieves, organizes, and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner."""
        self.owner = owner

    def collect_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Gather pending tasks from each pet."""
        pet_task_pairs: list[tuple[Pet, Task]] = []
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                pet_task_pairs.append((pet, task))
        return pet_task_pairs

    def prioritize_tasks(self) -> list[tuple[Pet, Task]]:
        """Return pending tasks sorted by scheduling priority."""
        pending_tasks = self.collect_pending_tasks()
        return sorted(pending_tasks, key=self._task_sort_key)

    def generate_daily_schedule(self, available_minutes: int | None = None) -> dict[str, object]:
        """Build a schedule of tasks that fit within the available time."""
        total_available = (
            self.owner.available_minutes_per_day
            if available_minutes is None
            else available_minutes
        )
        if total_available < 0:
            raise ValueError("Available minutes cannot be negative.")

        scheduled: list[dict[str, object]] = []
        skipped: list[dict[str, object]] = []
        minutes_used = 0

        for pet, task in self.prioritize_tasks():
            if minutes_used + task.duration_minutes <= total_available:
                scheduled.append(
                    {
                        "pet_name": pet.name,
                        "task_title": task.title,
                        "description": task.description,
                        "duration_minutes": task.duration_minutes,
                        "preferred_time": task.preferred_time_label(),
                        "frequency": task.frequency,
                        "priority": task.priority.name.lower(),
                        "reason": self.explain_task_selection(task),
                    }
                )
                minutes_used += task.duration_minutes
            else:
                skipped.append(
                    {
                        "pet_name": pet.name,
                        "task_title": task.title,
                        "duration_minutes": task.duration_minutes,
                        "reason": (
                            "Skipped because it would exceed the available time for today."
                        ),
                    }
                )

        return {
            "owner_name": self.owner.name,
            "scheduled": scheduled,
            "skipped": skipped,
            "minutes_used": minutes_used,
            "minutes_remaining": total_available - minutes_used,
        }

    def tasks_by_pet(self) -> dict[str, list[Task]]:
        """Return a mapping of pet names to their task lists."""
        return {pet.name: list(pet.tasks) for pet in self.owner.pets}

    def _task_sort_key(self, pet_task_pair: tuple[Pet, Task]) -> tuple[int, int, int, str]:
        """Return the sort key used to rank pending tasks."""
        _, task = pet_task_pair
        preferred_time_minutes = (
            24 * 60
            if task.preferred_time is None
            else task.preferred_time.hour * 60 + task.preferred_time.minute
        )
        return (
            -task.get_priority_score(),
            -task.get_frequency_score(),
            preferred_time_minutes,
            task.duration_minutes,
        )

    def explain_task_selection(self, task: Task) -> str:
        """Explain why a task was included in the daily schedule."""
        return (
            f"Selected because it is a {task.priority.name.lower()} priority "
            f"{task.frequency} task that fits within today's available time."
        )
