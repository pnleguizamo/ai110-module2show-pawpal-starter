from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


FREQUENCY_OPTIONS = ["daily", "weekly", "monthly", "as needed", "once"]
STATUS_OPTIONS = ["all", "pending", "completed"]


def initialize_state() -> None:
    """Create the owner object and latest schedule once per session."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="Jordan", available_minutes_per_day=60)
    if "latest_schedule" not in st.session_state:
        st.session_state.latest_schedule = None


def clear_schedule() -> None:
    """Reset the saved schedule when the underlying task data changes."""
    st.session_state.latest_schedule = None


def priority_from_label(priority_label: str) -> Priority:
    """Convert the UI priority label into a Priority enum value."""
    return Priority[priority_label.upper()]


def build_pet_rows(owner: Owner) -> list[dict[str, str | int]]:
    """Build table rows for the current pets."""
    return [
        {
            "name": pet.name,
            "species": pet.species,
            "age": pet.age,
            "task_count": len(pet.tasks),
        }
        for pet in owner.pets
    ]


def build_task_rows(
    owner: Owner,
    pet_filter: str | None = None,
    status_filter: str = "all",
) -> list[dict[str, str | int]]:
    """Build task rows using the scheduler's filter and time sort logic."""
    scheduler = Scheduler(owner)
    rows: list[dict[str, str | int]] = []

    filtered_tasks = scheduler.filter_tasks(pet_name=pet_filter, status=status_filter)
    for pet, task in scheduler.sort_by_time(filtered_tasks):
        rows.append(
            {
                "pet": pet.name,
                "title": task.title,
                "duration_minutes": task.duration_minutes,
                "preferred_time": task.preferred_time_label(),
                "time_window": task.preferred_time_window_label(),
                "frequency": task.frequency,
                "due_date": task.due_date_label(reference_date=date.today()),
                "priority": task.priority.name.lower(),
                "status": task.status_label(on_date=date.today()),
                "next_due": task.next_due_label(),
            }
        )

    return rows


def build_conflict_rows(conflicts: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    """Build display rows for preferred-time conflicts."""
    return [
        {
            "task_a": f"{conflict['pet_a']} | {conflict['task_a']}",
            "time_a": conflict["time_a"],
            "task_b": f"{conflict['pet_b']} | {conflict['task_b']}",
            "time_b": conflict["time_b"],
            "overlap_minutes": conflict["overlap_minutes"],
        }
        for conflict in conflicts
    ]


def render_conflict_warnings(
    conflicts: list[dict[str, str | int]],
    empty_message: str,
) -> None:
    """Render conflict warnings with both summaries and a table."""
    if not conflicts:
        st.success(empty_message)
        return

    plural = "s" if len(conflicts) != 1 else ""
    st.warning(f"Detected {len(conflicts)} preferred-time conflict{plural} that may require a schedule adjustment.")
    for conflict in conflicts:
        st.warning(
            f"{conflict['pet_a']}'s {conflict['task_a']} ({conflict['time_a']}) overlaps with "
            f"{conflict['pet_b']}'s {conflict['task_b']} ({conflict['time_b']}) by "
            f"{conflict['overlap_minutes']} minutes."
        )

    st.table(build_conflict_rows(conflicts))


def format_task_option(pet: Pet, task: Task) -> str:
    """Build a unique label for task selection controls."""
    return (
        f"{pet.name} | {task.title} | due {task.due_date.isoformat()} | "
        f"{task.status_label(on_date=date.today())}"
    )


def build_task_option_map(owner: Owner) -> dict[str, tuple[Pet, Task]]:
    """Map UI task labels back to their underlying task objects."""
    return {format_task_option(pet, task): (pet, task) for pet, task in owner.get_all_tasks()}


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
initialize_state()

owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ is a pet care planning assistant. This version adds smarter task logic:
time sorting, pet and status filters, recurring tasks, and basic conflict detection.
"""
)

st.divider()

st.subheader("Owner Setup")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes_per_day = st.number_input(
    "Available minutes today",
    min_value=0,
    max_value=1440,
    value=owner.available_minutes_per_day,
)

st.divider()

st.subheader("Add a Pet")
with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age", min_value=0, max_value=50, value=1)
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if not pet_name.strip():
        st.error("Enter a pet name before adding a pet.")
    elif owner.get_pet(pet_name.strip()) is not None:
        st.error("A pet with that name already exists.")
    else:
        owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
        clear_schedule()
        st.success(f"Added pet: {pet_name.strip()}")

if owner.pets:
    st.write("Current pets:")
    st.table(build_pet_rows(owner))
else:
    st.info("No pets added yet.")

st.divider()

st.subheader("Add a Task")
if owner.pets:
    with st.form("add_task_form"):
        selected_pet_name = st.selectbox("Choose a pet", [pet.name for pet in owner.pets])
        task_title = st.text_input("Task title", value="")
        task_description = st.text_input("Description", value="")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        no_preferred_time = st.checkbox("No preferred time", value=False)
        preferred_time = st.time_input("Preferred time", value=time(8, 0))
        frequency = st.selectbox("Recurrence", FREQUENCY_OPTIONS, index=0)
        due_date = st.date_input("Due date", value=date.today())
        priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        if not task_title.strip():
            st.error("Enter a task title before adding a task.")
        else:
            pet = owner.get_pet(selected_pet_name)
            if pet is None:
                st.error("The selected pet could not be found.")
            else:
                pet.add_task(
                    Task(
                        title=task_title.strip(),
                        description=task_description.strip() or task_title.strip(),
                        duration_minutes=int(duration),
                        preferred_time=None if no_preferred_time else preferred_time,
                        frequency=frequency,
                        due_date=due_date,
                        priority=priority_from_label(priority_label),
                    )
                )
                clear_schedule()
                st.success(f"Added task '{task_title.strip()}' for {selected_pet_name}")
else:
    st.info("Add a pet first before creating tasks.")

task_option_map = build_task_option_map(owner)
if task_option_map:
    st.subheader("Update Task Status")
    with st.form("update_task_form"):
        selected_task_label = st.selectbox("Task", list(task_option_map))
        task_status = st.selectbox("Set status", ["pending", "completed"], index=0)
        update_status_submitted = st.form_submit_button("Save status")

    if update_status_submitted:
        pet, task = task_option_map[selected_task_label]
        if task_status == "completed":
            if task.completed:
                st.info(f"'{task.title}' is already completed.")
            else:
                next_task = Scheduler(owner).mark_task_complete(
                    pet.name,
                    task.title,
                    task_due_date=task.due_date,
                    completed_on=date.today(),
                )
                clear_schedule()
                if next_task is None:
                    st.success(f"Marked '{task.title}' as completed.")
                else:
                    st.success(
                        f"Marked '{task.title}' as completed and created the next occurrence for "
                        f"{next_task.due_date_label(reference_date=date.today())}."
                    )
        else:
            task.mark_incomplete()
            clear_schedule()
            st.success(f"Marked '{task.title}' as pending.")

st.divider()

st.subheader("Task Explorer")
if task_option_map:
    filter_col, status_col = st.columns(2)
    with filter_col:
        pet_filter_label = st.selectbox("Filter by pet", ["All pets", *[pet.name for pet in owner.pets]])
    with status_col:
        status_filter = st.selectbox("Filter by status", STATUS_OPTIONS, index=1)

    pet_filter_value = None if pet_filter_label == "All pets" else pet_filter_label
    task_rows = build_task_rows(owner, pet_filter=pet_filter_value, status_filter=status_filter)
    scheduler = Scheduler(owner)
    visible_pending_tasks = scheduler.filter_tasks(pet_name=pet_filter_value, status="pending")
    todays_conflicts = scheduler.detect_conflicts(
        pet_task_pairs=[
            (pet, task)
            for pet, task in visible_pending_tasks
            if task.is_due(on_date=date.today())
        ],
        on_date=date.today(),
    )

    if task_rows:
        st.caption("Tasks are sorted by due date and preferred time so the closest care windows surface first.")
        st.table(task_rows)
    else:
        st.info("No tasks match the current filters.")

    st.caption("Conflict warnings compare today's pending tasks with preferred times so you can spot overlaps before they become a problem.")
    render_conflict_warnings(
        todays_conflicts,
        empty_message="Today's pending care windows do not overlap.",
    )
else:
    st.info("No tasks added yet.")

st.divider()

st.subheader("Today's Schedule")
if st.button("Generate schedule"):
    st.session_state.latest_schedule = Scheduler(owner).generate_daily_schedule(on_date=date.today())

schedule = st.session_state.latest_schedule
if schedule is not None:
    scheduled_items = schedule["scheduled"]
    skipped_items = schedule["skipped"]
    conflict_items = schedule["conflicts"]
    summary_col_1, summary_col_2, summary_col_3, summary_col_4 = st.columns(4)
    summary_col_1.metric("Scheduled", len(scheduled_items))
    summary_col_2.metric("Skipped", len(skipped_items))
    summary_col_3.metric("Conflicts", len(conflict_items))
    summary_col_4.metric("Minutes left", schedule["minutes_remaining"])

    render_conflict_warnings(
        conflict_items,
        empty_message="No preferred-time conflicts were detected in today's generated plan.",
    )

    if scheduled_items:
        st.success("The planner selected the tasks below based on priority, recurrence, due date, and the time you have available today.")
        st.table(scheduled_items)
    else:
        st.warning("No tasks fit into today's schedule.")

    if skipped_items:
        st.warning("These due tasks were left out because they would push the plan over today's available minutes.")
        st.table(skipped_items)
    elif scheduled_items:
        st.success("All due tasks fit into today's schedule.")

    st.caption(
        f"Minutes used: {schedule['minutes_used']} | "
        f"Minutes remaining: {schedule['minutes_remaining']}"
    )
