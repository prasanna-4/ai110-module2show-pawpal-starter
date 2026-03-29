"""
PawPal+ Streamlit UI — connects the Streamlit frontend to pawpal_system.py.
"""

from datetime import date
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session state bootstrap ────────────────────────────────────────────────────
# Streamlit reruns top-to-bottom on every interaction, so we store the Owner
# object in st.session_state so it persists across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("My Family")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# ── Sidebar — Add a Pet ────────────────────────────────────────────────────────
st.sidebar.header("🐾 PawPal+")
st.sidebar.subheader("Add a New Pet")

with st.sidebar.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    pet_species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
    submitted_pet = st.form_submit_button("Add Pet")
    if submitted_pet:
        if pet_name.strip():
            owner.add_pet(Pet(pet_name.strip(), pet_species))
            st.success(f"Added {pet_name} the {pet_species}!")
        else:
            st.error("Pet name cannot be empty.")

# ── Sidebar — Add a Task ───────────────────────────────────────────────────────
st.sidebar.subheader("Schedule a Task")

pet_names = [p.name for p in owner.pets]
if pet_names:
    with st.sidebar.form("add_task_form", clear_on_submit=True):
        selected_pet = st.selectbox("For pet", pet_names)
        task_desc = st.text_input("Task description")
        task_time = st.text_input("Time (HH:MM)", value="08:00")
        task_freq = st.selectbox("Frequency", ["once", "daily", "weekly"])
        task_due = st.date_input("Due date", value=date.today())
        submitted_task = st.form_submit_button("Add Task")
        if submitted_task:
            if task_desc.strip() and task_time.strip():
                pet = next(p for p in owner.pets if p.name == selected_pet)
                pet.add_task(Task(task_desc.strip(), task_time.strip(), task_freq, due_date=task_due))
                st.success(f"Task '{task_desc}' added for {selected_pet}!")
            else:
                st.error("Task description and time are required.")
else:
    st.sidebar.info("Add a pet first to schedule tasks.")

# ── Main area ──────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+ — Smart Pet Care Manager")

if not owner.pets:
    st.info("No pets yet! Add a pet using the sidebar to get started.")
    st.stop()

# ── Conflict warnings ──────────────────────────────────────────────────────────
conflicts = scheduler.detect_conflicts()
if conflicts:
    st.subheader("⚠️ Schedule Conflicts")
    for warning in conflicts:
        st.warning(warning)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_schedule, tab_pets, tab_filter = st.tabs(
    ["📅 Today's Schedule", "🐶 Pets & Tasks", "🔍 Filter & Search"]
)

# ── Tab 1: Today's Schedule ────────────────────────────────────────────────────
with tab_schedule:
    st.subheader(f"Schedule for {date.today().strftime('%A, %B %d %Y')}")

    today_pairs = [
        (pet, task)
        for pet, task in scheduler.get_all_tasks()
        if task.due_date == date.today()
    ]
    sorted_pairs = scheduler.sort_by_time(today_pairs)

    if not sorted_pairs:
        st.info("Nothing scheduled for today.")
    else:
        for pet, task in sorted_pairs:
            col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
            col1.write(f"**{pet.name}** ({pet.species})")
            col2.write(f"{task.time} — {task.description}")
            col3.write(f"`{task.frequency}`")
            if task.completed:
                col4.success("Done")
            else:
                if col4.button("Complete", key=f"complete_{id(task)}"):
                    scheduler.mark_task_complete(pet, task)
                    st.rerun()

# ── Tab 2: Pets & All Tasks ────────────────────────────────────────────────────
with tab_pets:
    for pet in owner.pets:
        with st.expander(f"{pet.name} — {pet.species} ({len(pet.tasks)} task(s))"):
            if not pet.tasks:
                st.write("No tasks yet.")
            else:
                for task in sorted(pet.tasks, key=lambda t: t.time):
                    status_icon = "✅" if task.completed else "⬜"
                    st.write(
                        f"{status_icon} **{task.time}** {task.description} "
                        f"`{task.frequency}` — due {task.due_date}"
                    )

# ── Tab 3: Filter & Search ─────────────────────────────────────────────────────
with tab_filter:
    st.subheader("Filter Tasks")

    col_pet, col_status = st.columns(2)
    filter_pet = col_pet.selectbox("Filter by pet", ["All"] + pet_names)
    filter_status = col_status.selectbox(
        "Filter by status", ["All", "Pending", "Completed"]
    )

    pairs = scheduler.get_all_tasks()
    if filter_pet != "All":
        pairs = scheduler.filter_by_pet(filter_pet, pairs)
    if filter_status == "Pending":
        pairs = scheduler.filter_by_status(completed=False, pairs=pairs)
    elif filter_status == "Completed":
        pairs = scheduler.filter_by_status(completed=True, pairs=pairs)

    pairs = scheduler.sort_by_time(pairs)

    if not pairs:
        st.info("No tasks match the current filter.")
    else:
        table_data = [
            {
                "Pet": pet.name,
                "Time": task.time,
                "Task": task.description,
                "Frequency": task.frequency,
                "Due": str(task.due_date),
                "Status": "✅ Done" if task.completed else "⬜ Pending",
            }
            for pet, task in pairs
        ]
        st.table(table_data)
