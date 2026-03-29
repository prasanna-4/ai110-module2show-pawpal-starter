"""
PawPal+ CLI demo — verifies the backend logic in pawpal_system.py.
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # ── Setup ──────────────────────────────────────────────────────────
    owner = Owner("Alex")

    buddy = Pet("Buddy", "Dog")
    whiskers = Pet("Whiskers", "Cat")

    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    today = date.today()

    # ── Add tasks (intentionally out of chronological order) ──────────
    buddy.add_task(Task("Evening walk",     "18:00", "daily",  due_date=today))
    buddy.add_task(Task("Morning walk",     "07:30", "daily",  due_date=today))
    buddy.add_task(Task("Heartworm tablet", "08:00", "weekly", due_date=today))
    buddy.add_task(Task("Vet appointment",  "10:00", "once",   due_date=today))

    whiskers.add_task(Task("Breakfast",     "07:30", "daily",  due_date=today))  # same time as Buddy → conflict
    whiskers.add_task(Task("Litter clean",  "09:00", "daily",  due_date=today))
    whiskers.add_task(Task("Flea treatment","14:00", "monthly" if False else "weekly", due_date=today))

    scheduler = Scheduler(owner)

    # ── Today's sorted schedule ────────────────────────────────────────
    print(scheduler.todays_schedule())

    # ── Conflict detection ─────────────────────────────────────────────
    print("\n=== Conflict Check ===")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts found.")

    # ── Mark Buddy's morning walk complete (recurring → auto-reschedule) ─
    print("\n=== Completing 'Morning walk' for Buddy ===")
    morning_walk = buddy.tasks[1]          # index 1 after insertion order
    scheduler.mark_task_complete(buddy, morning_walk)
    print(f"  Task marked complete: {morning_walk}")
    print(f"  Buddy now has {len(buddy.tasks)} task(s) (follow-up auto-added)")

    # ── Filtering demo ─────────────────────────────────────────────────
    print("\n=== Pending tasks only ===")
    pending = scheduler.filter_by_status(completed=False)
    for pet, task in scheduler.sort_by_time(pending):
        print(f"  {pet.name:12s}  {task}")

    print("\n=== Tasks for Whiskers only ===")
    whiskers_tasks = scheduler.filter_by_pet("Whiskers")
    for pet, task in scheduler.sort_by_time(whiskers_tasks):
        print(f"  {pet.name:12s}  {task}")


if __name__ == "__main__":
    main()
