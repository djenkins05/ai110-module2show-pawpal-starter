import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Schedule, ScheduledTask, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes today", min_value=0, max_value=600, value=120)
preferred_start_time = st.text_input("Preferred start time (Hour:Min)", value="09:00")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferred_start_time=preferred_start_time,
    )

owner: Owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes = int(available_minutes)
owner.preferred_start_time = preferred_start_time

st.divider()

st.subheader("Add a Pet")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if any(pet.name == pet_name for pet in owner.pets):
        st.warning(f"{pet_name} is already added.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added {pet_name} the {species}.")

if owner.pets:
    st.write("Pets:", ", ".join(pet.name for pet in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Schedule a Task")

if owner.pets:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_pet_name = st.selectbox("Pet", [pet.name for pet in owner.pets])
    with col2:
        task_title = st.text_input("Task title", value="Morning walk")
    with col3:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    preferred_time = st.text_input(
        "Preferred time (optional, e.g. 07:30 or 7:30 AM)", value=""
    ).strip()

    if st.button("Add task"):
        pet = next(pet for pet in owner.pets if pet.name == task_pet_name)
        try:
            pet.add_task(
                CareTask(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    preferred_time=preferred_time or None,
                )
            )
            st.success(f"Added '{task_title}' for {task_pet_name}.")
        except ValueError as error:
            st.error(str(error))
else:
    st.info("Add a pet before scheduling tasks.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")

    sort_option = st.radio("Sort by", ["Priority", "Time"], horizontal=True)
    preview_scheduler = Scheduler(owner)
    ordered_tasks = (
        preview_scheduler.sort_by_priority()
        if sort_option == "Priority"
        else preview_scheduler.sort_by_time()
    )

    for first, second in owner.detect_duplicate_tasks():
        st.warning(
            f"⚠️ Possible duplicate for {first.pet_name}: '{first.title}' is listed more than once."
        )

    for conflict in preview_scheduler.detect_time_conflicts():
        st.warning(f"⚠️ {conflict}")

    st.table(
        [
            {
                "Pet": task.pet_name,
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Preferred Time": task.preferred_time or "—",
                "Status": "✅ Done" if task.completed else "⏳ Pending",
            }
            for task in ordered_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner)

        for conflict in scheduler.detect_time_conflicts():
            st.warning(f"⚠️ {conflict}")

        schedule = scheduler.build_schedule()

        if schedule.scheduled_tasks:
            st.success(
                f"Scheduled {len(schedule.scheduled_tasks)} task(s) using "
                f"{schedule.total_minutes_used} of {available_minutes} available minutes."
            )
            st.table(
                [
                    {
                        "Start": scheduled.start_time.strftime("%H:%M"),
                        "End": scheduled.end_time.strftime("%H:%M"),
                        "Pet": scheduled.task.pet_name,
                        "Task": scheduled.task.title,
                        "Duration (min)": scheduled.task.duration_minutes,
                        "Priority": scheduled.task.priority,
                    }
                    for scheduled in schedule.get_scheduled_tasks_sorted_by_time()
                ]
            )
        else:
            st.warning("No tasks could be scheduled with the available time.")

        if schedule.skipped_tasks:
            st.warning(f"{len(schedule.skipped_tasks)} task(s) skipped — not enough time remaining:")
            st.table(
                [
                    {
                        "Pet": task.pet_name,
                        "Task": task.title,
                        "Duration (min)": task.duration_minutes,
                        "Priority": task.priority,
                    }
                    for task in schedule.skipped_tasks
                ]
            )

        if schedule.not_due_tasks:
            st.info(f"{len(schedule.not_due_tasks)} task(s) not due yet:")
            st.table(
                [
                    {
                        "Pet": task.pet_name,
                        "Task": task.title,
                        "Due": task.due_date.isoformat() if task.due_date else "—",
                    }
                    for task in schedule.not_due_tasks
                ]
            )

        with st.expander("Why this plan?"):
            st.text(scheduler.explain())
