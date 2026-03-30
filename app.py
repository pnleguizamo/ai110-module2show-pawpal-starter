from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def initialize_owner() -> None:
    """Create the owner object once and persist it in session state."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="Jordan", available_minutes_per_day=60)


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


def build_task_rows(owner: Owner) -> list[dict[str, str | int]]:
    """Build table rows for all pet tasks."""
    rows: list[dict[str, str | int]] = []
    for pet in owner.pets:
        for task in pet.tasks:
            rows.append(
                {
                    "pet": pet.name,
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "preferred_time": task.preferred_time_label(),
                    "priority": task.priority.name.lower(),
                    "completed": "yes" if task.completed else "no",
                }
            )
    return rows


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
initialize_owner()

owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ is a pet care planning assistant. This version connects the Streamlit UI
to your backend classes so pets, tasks, and schedules persist during the session.
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
        selected_pet_name = st.selectbox(
            "Choose a pet",
            [pet.name for pet in owner.pets],
        )
        task_title = st.text_input("Task title", value="")
        task_description = st.text_input("Description", value="")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        preferred_time = st.time_input("Preferred time", value=time(8, 0))
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
                        preferred_time=preferred_time,
                        priority=priority_from_label(priority_label),
                    )
                )
                st.success(f"Added task '{task_title.strip()}' for {selected_pet_name}")

    task_rows = build_task_rows(owner)
    if task_rows:
        st.write("Current tasks:")
        st.table(task_rows)
    else:
        st.info("No tasks added yet.")
else:
    st.info("Add a pet first before creating tasks.")

st.divider()

st.subheader("Today's Schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()

    scheduled_items = schedule["scheduled"]
    skipped_items = schedule["skipped"]

    if scheduled_items:
        st.write("Scheduled tasks:")
        st.table(scheduled_items)
    else:
        st.warning("No tasks fit into today's schedule.")

    if skipped_items:
        st.write("Skipped tasks:")
        st.table(skipped_items)

    st.caption(
        f"Minutes used: {schedule['minutes_used']} | "
        f"Minutes remaining: {schedule['minutes_remaining']}"
    )
