"""Domain models and time logic for the alarm clock.

Pure logic module — no ``print()``, no ``input()``, no side effects.
All time-dependent functions accept an optional ``now`` parameter
for deterministic testing without mocking.

Design decisions:
    - ``AlarmState`` enum makes the lifecycle explicit and traceable.
    - Injectable ``now`` enables testing with zero infrastructure.
    - ``snooze()`` uses full ``datetime`` arithmetic for safe midnight handling.
    - Validation functions are module-level (they run *before* an Alarm exists).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum, auto


SNOOZE_MINUTES_DEFAULT: int = 5


class AlarmState(Enum):
    """Lifecycle states of an alarm.

    Transitions::

        PENDING ──► RINGING ──► DISMISSED
                       │
                       ▼
                    SNOOZED ──► RINGING ──► ...
    """

    PENDING = auto()
    RINGING = auto()
    SNOOZED = auto()
    DISMISSED = auto()


# ── Parsing & Validation ─────────────────────────────────────────


def parse_time(user_input: str) -> time:
    """Parse an ``HH:MM`` (24-hour) string into a :class:`datetime.time`.

    Args:
        user_input: Raw string, e.g. ``"07:30"``.

    Returns:
        A :class:`datetime.time` object.

    Raises:
        ValueError: On empty, malformed, or out-of-range input.
    """
    stripped = user_input.strip()
    if not stripped:
        raise ValueError("Input cannot be empty. Please use HH:MM (24-hour).")

    try:
        parsed = datetime.strptime(stripped, "%H:%M")
    except ValueError:
        raise ValueError(
            f"Invalid format: '{stripped}'. Please use HH:MM (24-hour)."
        ) from None

    return parsed.time()


def validate_future(alarm_time: time, now: datetime | None = None) -> None:
    """Ensure *alarm_time* is strictly in the future.

    Uses ``<=`` so that an alarm set for the *current* minute (where
    seconds have already elapsed) is correctly rejected.

    Raises:
        ValueError: If *alarm_time* has already passed today.
    """
    if now is None:
        now = datetime.now()

    if alarm_time <= now.time():
        raise ValueError(
            f"Time {alarm_time:%H:%M} has already passed. "
            "Please enter a future time."
        )


# ── Alarm Dataclass ──────────────────────────────────────────────


@dataclass
class Alarm:
    """A single alarm with lifecycle state management.

    Attributes:
        target_time: Wall-clock time this alarm should fire.
        snooze_minutes: Duration of each snooze in minutes.
    """

    target_time: time
    snooze_minutes: int = SNOOZE_MINUTES_DEFAULT
    state: AlarmState = field(default=AlarmState.PENDING, repr=False)
    _snooze_count: int = field(default=0, repr=False, init=False)

    # ── Properties ───────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        """``True`` if the alarm has not been dismissed."""
        return self.state != AlarmState.DISMISSED

    @property
    def snooze_count(self) -> int:
        """Number of times this alarm has been snoozed."""
        return self._snooze_count

    # ── Time Queries ─────────────────────────────────────────────

    def time_remaining(self, now: datetime | None = None) -> timedelta:
        """Duration until this alarm fires. Negative means overdue."""
        if now is None:
            now = datetime.now()
        target_dt = datetime.combine(now.date(), self.target_time)
        return target_dt - now

    def is_due(self, now: datetime | None = None) -> bool:
        """``True`` if the alarm should fire now (or is overdue)."""
        return self.time_remaining(now) <= timedelta(0)

    # ── State Transitions ────────────────────────────────────────

    def ring(self) -> None:
        """Transition to ``RINGING``."""
        self.state = AlarmState.RINGING

    def snooze(self, now: datetime | None = None) -> None:
        """Advance *target_time* by *snooze_minutes*.

        Uses full ``datetime`` arithmetic so that rollovers near
        midnight are handled safely.

        Raises:
            ValueError: If snooze would push the alarm past midnight
                (same-day assumption).
        """
        if now is None:
            now = datetime.now()

        target_dt = datetime.combine(now.date(), self.target_time)
        new_dt = target_dt + timedelta(minutes=self.snooze_minutes)

        if new_dt.date() > now.date():
            raise ValueError(
                "Cannot snooze — alarm would move past midnight."
            )

        self.target_time = new_dt.time()
        self._snooze_count += 1
        self.state = AlarmState.SNOOZED

    def dismiss(self) -> None:
        """Transition to ``DISMISSED``."""
        self.state = AlarmState.DISMISSED
