"""
Automated test suite for PawPal+ (pawpal_system.py).

Run with:
    python -m pytest
"""

from datetime import date, timedelta
import pytest

from pawpal_system import Owner, Pet, Task, Scheduler


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def owner_with_pets():
    """Return an Owner containing two pets with a handful of tasks."""
    owner = Owner("Test Owner")
    today = date.today()

    rex = Pet("Rex", "Dog")
    rex.add_task(Task("Dinner",       "18:00", "daily",  due_date=today))
    rex.add_task(Task("Morning walk", "07:00", "daily",  due_date=today))
    rex.add_task(Task("Vet visit",    "10:00", "once",   due_date=today))

    luna = Pet("Luna", "Cat")
    luna.add_task(Task("Breakfast",   "07:00", "daily",  due_date=today))  # conflict with Rex
    luna.add_task(Task("Litter",      "09:00", "daily",  due_date=today))

    owner.add_pet(rex)
    owner.add_pet(luna)
    return owner


# ── Task tests ─────────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip completed to True."""
    task = Task("Feed", "08:00")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_count():
    """Adding a task to a Pet should increase its task list length by 1."""
    pet = Pet("Goldie", "Fish")
    initial_count = len(pet.tasks)
    pet.add_task(Task("Water change", "10:00"))
    assert len(pet.tasks) == initial_count + 1


def test_daily_recurrence_creates_follow_up():
    """Completing a daily task should return a new task due the next day."""
    today = date.today()
    task = Task("Walk", "07:00", "daily", due_date=today)
    follow_up = task.mark_complete()
    assert follow_up is not None
    assert follow_up.due_date == today + timedelta(days=1)
    assert follow_up.completed is False


def test_weekly_recurrence_creates_follow_up():
    """Completing a weekly task should return a new task due in 7 days."""
    today = date.today()
    task = Task("Bath", "12:00", "weekly", due_date=today)
    follow_up = task.mark_complete()
    assert follow_up is not None
    assert follow_up.due_date == today + timedelta(weeks=1)


def test_once_task_has_no_follow_up():
    """Completing a one-off task should return None (no recurrence)."""
    task = Task("Vet", "09:00", "once")
    follow_up = task.mark_complete()
    assert follow_up is None


# ── Sorting tests ──────────────────────────────────────────────────────────────

def test_sort_by_time_is_chronological(owner_with_pets):
    """sort_by_time() must return tasks in ascending HH:MM order."""
    scheduler = Scheduler(owner_with_pets)
    sorted_pairs = scheduler.sort_by_time()
    times = [task.time for _, task in sorted_pairs]
    assert times == sorted(times), f"Expected sorted times, got {times}"


def test_sort_by_time_empty_list():
    """sort_by_time() on an empty list should return an empty list."""
    owner = Owner("Empty")
    scheduler = Scheduler(owner)
    assert scheduler.sort_by_time() == []


# ── Filtering tests ────────────────────────────────────────────────────────────

def test_filter_by_status_pending(owner_with_pets):
    """filter_by_status(False) should exclude completed tasks."""
    scheduler = Scheduler(owner_with_pets)
    # Complete one task first
    pet = owner_with_pets.pets[0]
    task = pet.tasks[0]
    task.mark_complete()

    pending = scheduler.filter_by_status(completed=False)
    assert all(not t.completed for _, t in pending)


def test_filter_by_pet_returns_correct_pet(owner_with_pets):
    """filter_by_pet() should return only tasks belonging to the named pet."""
    scheduler = Scheduler(owner_with_pets)
    luna_pairs = scheduler.filter_by_pet("Luna")
    assert all(pet.name == "Luna" for pet, _ in luna_pairs)
    assert len(luna_pairs) == 2


def test_filter_by_pet_case_insensitive(owner_with_pets):
    """Pet name lookup in filter_by_pet() should be case-insensitive."""
    scheduler = Scheduler(owner_with_pets)
    assert scheduler.filter_by_pet("luna") == scheduler.filter_by_pet("Luna")


# ── Conflict detection tests ───────────────────────────────────────────────────

def test_detect_conflicts_finds_duplicate_time(owner_with_pets):
    """Two tasks at 07:00 (Rex morning walk + Luna breakfast) should be flagged."""
    scheduler = Scheduler(owner_with_pets)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) >= 1
    assert any("07:00" in w for w in warnings)


def test_no_conflicts_when_times_differ():
    """No conflicts should be reported when all task times are unique."""
    owner = Owner("Solo")
    dog = Pet("Max", "Dog")
    dog.add_task(Task("Walk",    "07:00", "daily"))
    dog.add_task(Task("Dinner",  "18:00", "daily"))
    dog.add_task(Task("Tablet",  "08:00", "weekly"))
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


# ── Scheduler integration tests ───────────────────────────────────────────────

def test_mark_task_complete_adds_follow_up(owner_with_pets):
    """mark_task_complete() on a daily task should auto-add a follow-up to the pet."""
    scheduler = Scheduler(owner_with_pets)
    rex = owner_with_pets.pets[0]
    daily_task = next(t for t in rex.tasks if t.frequency == "daily")
    count_before = len(rex.tasks)

    scheduler.mark_task_complete(rex, daily_task)
    assert daily_task.completed is True
    assert len(rex.tasks) == count_before + 1


def test_owner_get_all_tasks_count(owner_with_pets):
    """get_all_tasks() should return all tasks across every pet."""
    total = sum(len(p.tasks) for p in owner_with_pets.pets)
    assert len(owner_with_pets.get_all_tasks()) == total
