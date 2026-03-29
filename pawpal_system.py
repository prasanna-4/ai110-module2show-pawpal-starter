"""
PawPal+ logic layer — Owner, Pet, Task, and Scheduler classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Tuple


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str                        # "HH:MM" 24-hour format
    frequency: str = "once"          # "once" | "daily" | "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return a follow-up task if recurring."""
        self.completed = True
        if self.frequency == "daily":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None

    def __str__(self) -> str:
        status = "[x]" if self.completed else "[ ]"
        freq = f" [{self.frequency}]" if self.frequency != "once" else ""
        return f"[{status}] {self.time}  {self.description}{freq}  (due {self.due_date})"


@dataclass
class Pet:
    """Stores pet details and a list of associated tasks."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)

    def __str__(self) -> str:
        return f"{self.name} ({self.species})"


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's collection."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return all (pet, task) pairs across every owned pet."""
        pairs = []
        for pet in self.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs

    def __str__(self) -> str:
        return f"Owner: {self.name} ({len(self.pets)} pet(s))"


class Scheduler:
    """The brain — retrieves, organizes, and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # ------------------------------------------------------------------
    # Retrieval helpers
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return all (pet, task) pairs from the owner."""
        return self.owner.get_all_tasks()

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(
        self, pairs: Optional[List[Tuple[Pet, Task]]] = None
    ) -> List[Tuple[Pet, Task]]:
        """Return tasks sorted chronologically by their time attribute."""
        if pairs is None:
            pairs = self.get_all_tasks()
        return sorted(pairs, key=lambda pt: pt[1].time)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_by_status(
        self,
        completed: bool,
        pairs: Optional[List[Tuple[Pet, Task]]] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Return only tasks that match the given completion status."""
        if pairs is None:
            pairs = self.get_all_tasks()
        return [pt for pt in pairs if pt[1].completed == completed]

    def filter_by_pet(
        self,
        pet_name: str,
        pairs: Optional[List[Tuple[Pet, Task]]] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Return only tasks belonging to the named pet (case-insensitive)."""
        if pairs is None:
            pairs = self.get_all_tasks()
        return [pt for pt in pairs if pt[0].name.lower() == pet_name.lower()]

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(
        self, pairs: Optional[List[Tuple[Pet, Task]]] = None
    ) -> List[str]:
        """
        Return a list of warning strings for tasks scheduled at the same time.

        Uses exact HH:MM matching; overlapping durations are not considered.
        Tradeoff: simple and fast, but misses e.g. a 30-minute task vs one
        scheduled 15 minutes later.
        """
        if pairs is None:
            pairs = self.get_all_tasks()

        seen: dict = {}  # time -> (pet_name, description)
        warnings: List[str] = []

        for pet, task in pairs:
            key = task.time
            if key in seen:
                prev_pet, prev_desc = seen[key]
                warnings.append(
                    f"CONFLICT at {key}: '{prev_desc}' ({prev_pet})"
                    f" overlaps with '{task.description}' ({pet.name})"
                )
            else:
                seen[key] = (pet.name, task.description)

        return warnings

    # ------------------------------------------------------------------
    # Task completion + recurrence
    # ------------------------------------------------------------------

    def mark_task_complete(self, pet: Pet, task: Task) -> None:
        """
        Mark a task complete on the given pet.

        If the task is recurring, a new instance is automatically added
        for the next occurrence.
        """
        follow_up = task.mark_complete()
        if follow_up is not None:
            pet.add_task(follow_up)

    # ------------------------------------------------------------------
    # Display helper
    # ------------------------------------------------------------------

    def todays_schedule(self) -> str:
        """Return a formatted string of today's pending tasks sorted by time."""
        today = date.today()
        pairs = self.get_all_tasks()
        due_today = [
            (pet, task)
            for pet, task in pairs
            if task.due_date == today and not task.completed
        ]
        sorted_pairs = self.sort_by_time(due_today)

        if not sorted_pairs:
            return "No tasks scheduled for today."

        lines = [f"=== Today's Schedule ({today}) ==="]
        for pet, task in sorted_pairs:
            lines.append(f"  {pet.name:12s}  {task}")
        return "\n".join(lines)
