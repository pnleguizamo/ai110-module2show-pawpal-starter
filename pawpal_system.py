from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCategory(str, Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


class TimeBlock(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANYTIME = "anytime"


@dataclass
class OwnerProfile:
    name: str
    available_minutes_per_day: int
    preferred_start_time: time
    preferences: dict[str, str] = field(default_factory=dict)

    def update_preferences(self, new_preferences: dict[str, str]) -> None:
        pass

    def set_available_time(self, minutes: int) -> None:
        pass

    def can_fit_task(self, duration_minutes: int) -> bool:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)

    def update_profile(
        self,
        *,
        name: str | None = None,
        species: str | None = None,
        age: int | None = None,
    ) -> None:
        pass

    def add_special_need(self, need: str) -> None:
        pass

    def get_care_context(self) -> dict[str, str | int | list[str]]:
        pass


@dataclass
class Task:
    task_id: str
    title: str
    category: TaskCategory
    duration_minutes: int
    priority: Priority
    preferred_time_block: TimeBlock
    required_today: bool
    notes: str = ""

    def is_required(self) -> bool:
        pass

    def get_priority_score(self) -> int:
        pass

    def matches_time_block(self, time_block: TimeBlock) -> bool:
        pass


@dataclass
class DailyConstraints:
    date: date
    available_minutes: int
    start_time: time
    allowed_time_blocks: list[TimeBlock] = field(default_factory=list)

    def allows(self, task: Task) -> bool:
        pass

    def remaining_minutes(self, used_minutes: int) -> int:
        pass

    def has_capacity_for(self, task: Task, used_minutes: int) -> bool:
        pass


@dataclass
class ScheduleItem:
    task: Task
    start_time: time
    end_time: time
    selection_reason: str

    def duration(self) -> int:
        pass

    def to_display_dict(self) -> dict[str, str | int]:
        pass


@dataclass
class DailyPlan:
    date: date
    scheduled_items: list[ScheduleItem] = field(default_factory=list)
    skipped_tasks: list[tuple[Task, str]] = field(default_factory=list)
    total_minutes_used: int = 0
    summary_reasoning: str = ""

    def add_item(self, schedule_item: ScheduleItem) -> None:
        pass

    def add_skipped_task(self, task: Task, reason: str) -> None:
        pass

    def remaining_minutes(self, total_available: int) -> int:
        pass

    def to_table_rows(self) -> list[dict[str, str | int]]:
        pass


class Scheduler:
    def __init__(
        self,
        default_sort_rules: list[str] | None = None,
        default_start_time: time | None = None,
    ) -> None:
        self.default_sort_rules = default_sort_rules or [
            "required_today",
            "priority",
            "duration",
        ]
        self.default_start_time = default_start_time

    def generate_plan(
        self,
        owner: OwnerProfile,
        pet: Pet,
        tasks: list[Task],
        constraints: DailyConstraints,
    ) -> DailyPlan:
        pass

    def rank_tasks(self, tasks: list[Task], owner: OwnerProfile, pet: Pet) -> list[Task]:
        pass

    def schedule_tasks(
        self,
        ranked_tasks: list[Task],
        constraints: DailyConstraints,
    ) -> list[ScheduleItem]:
        pass

    def explain_choice(self, task: Task, constraints: DailyConstraints) -> str:
        pass

    def explain_skip(self, task: Task, reason: str) -> str:
        pass
