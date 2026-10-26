"""Display and input functions for the alarm clock.

Every ``print()`` and ``input()`` call in the application lives here.
Functions are stateless — they accept primitives, produce terminal
output, and return nothing (or raw user input).

No domain objects are imported; the CLI layer bridges models and display.

Design decisions:
    - ``\\r`` carriage return for in-place countdown (no curses dependency).
    - Lines padded to 50 chars to prevent stale-character artifacts.
    - ``flush=True`` on countdown to defeat stdout buffering.
    - Terminal bell ``\\a`` as best-effort audible alert.
"""

from __future__ import annotations

import sys
from datetime import timedelta


# ── Helpers ──────────────────────────────────────────────────────


def format_timedelta(td: timedelta) -> str:
    """Convert a timedelta to ``HH:MM:SS``.

    Negative values are clamped to ``00:00:00`` to prevent confusing
    output when an alarm is briefly overdue.
    """
    total = max(int(td.total_seconds()), 0)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ── Banner ───────────────────────────────────────────────────────


def show_banner() -> None:
    """Print the application header with usage hint."""
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║          ⏰  ALARM  CLOCK            ║")
    print("  ╠══════════════════════════════════════╣")
    print("  ║  24-hour format  ·  Ctrl+C to quit   ║")
    print("  ╚══════════════════════════════════════╝")
    print()


# ── Input Prompts ────────────────────────────────────────────────


def prompt_time() -> str:
    """Prompt for alarm time, return stripped raw input."""
    return input("  Enter alarm time (HH:MM): ").strip()


def prompt_add_more() -> bool:
    """Ask whether to add another alarm. Defaults to No."""
    resp = input("  Add another alarm? (y/N): ").strip().lower()
    return resp in ("y", "yes")


def prompt_snooze() -> str:
    """Ask to snooze or dismiss. Returns stripped, lowercased input."""
    return input("  [S]nooze / [D]ismiss: ").strip().lower()


# ── Feedback Messages ────────────────────────────────────────────


def show_error(message: str) -> None:
    """Display a formatted error message."""
    print(f"  ✗ {message}")


def show_alarm_set(time_str: str, remaining: timedelta) -> None:
    """Confirm that an alarm was set and show time until it fires."""
    print(f"  ✓ Alarm set for {time_str}  ({format_timedelta(remaining)} away)")


def show_alarm_list(alarms: list[tuple[str, str]]) -> None:
    """Display a summary table of all scheduled alarms.

    Args:
        alarms: List of ``(time_str, status_label)`` tuples.
    """
    print()
    print("  ┌──── Scheduled Alarms ─────┐")
    for i, (t, status) in enumerate(alarms, 1):
        print(f"  │  {i}. {t}   {status:<14s}│")
    print("  └────────────────────────────┘")
    print()


def show_waiting(index: int, total: int, time_str: str) -> None:
    """Announce which alarm the app is currently waiting for."""
    print(f"\n  ⏳ Waiting for alarm {index}/{total} — {time_str}")


# ── Live Countdown ───────────────────────────────────────────────


def show_countdown(remaining: timedelta) -> None:
    """Overwrite the current terminal line with a countdown.

    Pads to 50 characters to overwrite any residue from a previously
    longer line.  Uses ``flush=True`` to force immediate output.
    """
    text = f"  ⏳ {format_timedelta(remaining)}"
    print(f"\r{text:<50}", end="", flush=True)


# ── Alarm Alert ──────────────────────────────────────────────────


def show_alert(time_str: str) -> None:
    """Display a prominent alarm alert with terminal bell.

    Clears any countdown residue before printing the alert box.
    """
    print(f"\r{'':<50}", end="")
    print("\r")
    print("  ╔══════════════════════════════════════╗")
    print("  ║         🔔  ALARM!  🔔               ║")
    print(f"  ║         Time: {time_str:<22s}║")
    print("  ╚══════════════════════════════════════╝")
    # Terminal bell — silent on some terminals; visual alert is primary.
    sys.stdout.write("\a")
    sys.stdout.flush()
    print()


# ── Status Messages ──────────────────────────────────────────────


def show_snoozed(new_time_str: str, count: int) -> None:
    """Confirm snooze with new target time and snooze count."""
    print(f"  💤 Snoozed (×{count})! New alarm: {new_time_str}\n")


def show_snooze_failed(message: str) -> None:
    """Show why snooze was rejected and auto-dismiss."""
    print(f"  ✗ {message}")
    print("  ✗ Dismissing alarm instead.\n")


def show_dismissed() -> None:
    """Confirm alarm was dismissed."""
    print("  ✓ Alarm dismissed.\n")


def show_all_done() -> None:
    """All alarms handled — session complete."""
    print("  ✓ All alarms complete!")


def show_goodbye() -> None:
    """Clean exit message."""
    print("\n  Goodbye! 👋")
