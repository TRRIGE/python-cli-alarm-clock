"""CLI entry point and orchestration for the alarm clock.

Wires together domain logic (:mod:`models`) and terminal I/O
(:mod:`display`) into an interactive command-line flow.

Supports two modes:
    - **Argument mode**: ``python alarm.py 07:30 14:00 --snooze 10``
    - **Interactive mode**: ``python alarm.py`` (prompted input)

Design decisions:
    - ``import time as time_mod`` avoids shadowing ``datetime.time``.
    - Dual Ctrl+C strategy: ``signal.signal`` for interrupts during
      ``sleep``; ``try/except`` for interrupts during ``input()``.
    - Alarms processed sequentially (sorted by time) — simple and
      predictable, avoids threading for a CLI tool.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time as time_mod
from types import FrameType

import display
from models import (
    Alarm,
    SNOOZE_MINUTES_DEFAULT,
    parse_time,
    validate_future,
)


# ── CLI Argument Parsing ─────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        description="⏰ Alarm Clock CLI — set alarms from your terminal.",
        epilog="Run without arguments for interactive mode.",
    )
    parser.add_argument(
        "times",
        nargs="*",
        metavar="HH:MM",
        help="alarm time(s) in 24-hour format (e.g. 07:30 14:00)",
    )
    parser.add_argument(
        "--snooze",
        type=int,
        default=SNOOZE_MINUTES_DEFAULT,
        metavar="MIN",
        help=f"snooze duration in minutes (default: {SNOOZE_MINUTES_DEFAULT})",
    )
    return parser


# ── Signal Handling ──────────────────────────────────────────────


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    """Handle ``SIGINT`` (Ctrl+C) with a clean exit.

    Registered at startup so interrupts during ``time.sleep()``
    produce a friendly message instead of a traceback.
    """
    display.show_goodbye()
    sys.exit(0)


# ── Alarm Creation ───────────────────────────────────────────────


def create_alarm_from_arg(time_str: str, snooze: int) -> Alarm:
    """Create a validated :class:`Alarm` from a CLI argument.

    Args:
        time_str: Raw ``"HH:MM"`` string.
        snooze: Snooze duration in minutes.

    Returns:
        A ready-to-use :class:`Alarm`.

    Raises:
        ValueError: On invalid or past times.
    """
    alarm_time = parse_time(time_str)
    validate_future(alarm_time)
    return Alarm(target_time=alarm_time, snooze_minutes=snooze)


def get_alarms_interactive(snooze: int) -> list[Alarm]:
    """Prompt the user to set one or more alarms interactively.

    Loops until the user declines to add more alarms.
    Invalid input is rejected with a clear message and re-prompted.
    """
    alarms: list[Alarm] = []

    while True:
        try:
            raw = display.prompt_time()
            alarm_time = parse_time(raw)
            validate_future(alarm_time)
        except ValueError as exc:
            display.show_error(str(exc))
            continue

        alarm = Alarm(target_time=alarm_time, snooze_minutes=snooze)
        display.show_alarm_set(f"{alarm_time:%H:%M}", alarm.time_remaining())
        alarms.append(alarm)

        if not display.prompt_add_more():
            break

    return alarms


def get_alarms(args: argparse.Namespace) -> list[Alarm]:
    """Resolve alarms from CLI arguments or interactive prompts.

    Args:
        args: Parsed CLI arguments.

    Returns:
        A non-empty list of alarms, sorted by target time.
    """
    if args.times:
        alarms: list[Alarm] = []
        for t in args.times:
            try:
                alarm = create_alarm_from_arg(t, args.snooze)
                display.show_alarm_set(
                    f"{alarm.target_time:%H:%M}", alarm.time_remaining()
                )
                alarms.append(alarm)
            except ValueError as exc:
                display.show_error(str(exc))
                sys.exit(1)
        return alarms

    return get_alarms_interactive(args.snooze)


# ── Alarm Lifecycle ──────────────────────────────────────────────


def wait_for_alarm(alarm: Alarm) -> None:
    """Block until the alarm is due, showing a live countdown.

    Polls once per second.  The countdown line is overwritten in
    place using a carriage return.
    """
    while not alarm.is_due():
        display.show_countdown(alarm.time_remaining())
        time_mod.sleep(1)
    # Clear the \r countdown line before handing off to the alert.
    print()


def handle_trigger(alarm: Alarm) -> bool:
    """Display the alert and let the user snooze or dismiss.

    Args:
        alarm: The alarm that just fired.

    Returns:
        ``True`` if snoozed (caller should re-enter wait loop),
        ``False`` if dismissed.
    """
    alarm.ring()
    display.show_alert(f"{alarm.target_time:%H:%M}")

    while True:
        try:
            choice = display.prompt_snooze()
        except (KeyboardInterrupt, EOFError):
            display.show_goodbye()
            sys.exit(0)

        if choice == "s":
            try:
                alarm.snooze()
            except ValueError as exc:
                # Snooze would push past midnight — auto-dismiss.
                display.show_snooze_failed(str(exc))
                alarm.dismiss()
                return False
            display.show_snoozed(
                f"{alarm.target_time:%H:%M}", alarm.snooze_count
            )
            return True

        if choice == "d":
            alarm.dismiss()
            display.show_dismissed()
            return False

        display.show_error("Please enter 'S' to snooze or 'D' to dismiss.")


# ── Main Loop ────────────────────────────────────────────────────


def run(alarms: list[Alarm]) -> None:
    """Process alarms sequentially: wait → trigger → snooze/dismiss.

    Alarms are sorted by target time so they fire in chronological
    order.  Each alarm's snooze loop is independent.
    """
    alarms.sort(key=lambda a: a.target_time)

    if len(alarms) > 1:
        summary = [(f"{a.target_time:%H:%M}", "pending") for a in alarms]
        display.show_alarm_list(summary)

    for i, alarm in enumerate(alarms, 1):
        if len(alarms) > 1:
            display.show_waiting(i, len(alarms), f"{alarm.target_time:%H:%M}")

        snoozed = True
        while snoozed:
            wait_for_alarm(alarm)
            snoozed = handle_trigger(alarm)

    display.show_all_done()


def main() -> None:
    """Entry point: parse arguments → set alarms → run loop."""
    signal.signal(signal.SIGINT, handle_sigint)
    display.show_banner()

    parser = build_parser()
    args = parser.parse_args()

    try:
        alarms = get_alarms(args)
        if not alarms:
            display.show_error("No alarms set.")
            sys.exit(1)
        run(alarms)
    except (KeyboardInterrupt, EOFError):
        display.show_goodbye()
        sys.exit(0)


if __name__ == "__main__":
    main()
