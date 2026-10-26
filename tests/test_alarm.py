"""Unit tests for the Alarm Clock CLI application.

Uses Python standard library `unittest` — zero external dependencies.
Run with: python -m unittest discover -s tests
"""
import io
import unittest
from datetime import datetime, time, timedelta
from unittest.mock import patch

from models import (
    Alarm,
    AlarmState,
    SNOOZE_MINUTES_DEFAULT,
    parse_time,
    validate_future,
)
import display


class TestParseTime(unittest.TestCase):
    """Test parse_time parsing and validation."""

    def test_valid_times(self):
        self.assertEqual(parse_time("00:00"), time(0, 0))
        self.assertEqual(parse_time("07:30"), time(7, 30))
        self.assertEqual(parse_time("23:59"), time(23, 59))
        self.assertEqual(parse_time("  12:00  "), time(12, 0))

    def test_invalid_formats(self):
        with self.assertRaises(ValueError) as ctx:
            parse_time("12-30")
        self.assertIn("Invalid format", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            parse_time("abc")
        self.assertIn("Invalid format", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            parse_time("25:00")
        self.assertIn("Invalid format", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            parse_time("12:60")
        self.assertIn("Invalid format", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            parse_time("")
        self.assertIn("empty", str(ctx.exception))


class TestValidateFuture(unittest.TestCase):
    """Test future validation with deterministic `now` injection."""

    def test_future_time(self):
        now = datetime(2026, 1, 1, 10, 0, 0)
        # Should complete without raising
        validate_future(time(10, 1), now=now)

    def test_past_time(self):
        now = datetime(2026, 1, 1, 10, 0, 0)
        with self.assertRaises(ValueError) as ctx:
            validate_future(time(9, 59), now=now)
        self.assertIn("already passed", str(ctx.exception))

    def test_exact_current_time(self):
        now = datetime(2026, 1, 1, 10, 0, 0)
        with self.assertRaises(ValueError) as ctx:
            validate_future(time(10, 0), now=now)
        self.assertIn("already passed", str(ctx.exception))


class TestAlarmModel(unittest.TestCase):
    """Test Alarm lifecycle, snooze, and edge cases."""

    def test_time_remaining_and_due(self):
        now = datetime(2026, 1, 1, 10, 0, 0)
        alarm = Alarm(target_time=time(10, 5))
        rem = alarm.time_remaining(now=now)
        self.assertEqual(rem, timedelta(minutes=5))
        self.assertFalse(alarm.is_due(now=now))

        now_due = datetime(2026, 1, 1, 10, 5, 0)
        self.assertTrue(alarm.is_due(now=now_due))
        self.assertEqual(alarm.time_remaining(now=now_due), timedelta(0))

    def test_snooze_success(self):
        now = datetime(2026, 1, 1, 10, 0, 0)
        alarm = Alarm(target_time=time(10, 0), snooze_minutes=5)
        alarm.snooze(now=now)
        self.assertEqual(alarm.target_time, time(10, 5))
        self.assertEqual(alarm.state, AlarmState.SNOOZED)
        self.assertEqual(alarm.snooze_count, 1)

    def test_snooze_cumulative_count(self):
        now1 = datetime(2026, 1, 1, 10, 0, 0)
        alarm = Alarm(target_time=time(10, 0), snooze_minutes=5)
        alarm.snooze(now=now1)

        now2 = datetime(2026, 1, 1, 10, 5, 0)
        alarm.snooze(now=now2)
        self.assertEqual(alarm.target_time, time(10, 10))
        self.assertEqual(alarm.snooze_count, 2)

    def test_midnight_snooze_guard(self):
        """Edge case #7: Snooze cannot roll over midnight in a single-day app."""
        now = datetime(2026, 1, 1, 23, 58, 0)
        alarm = Alarm(target_time=time(23, 58), snooze_minutes=5)
        with self.assertRaises(ValueError) as ctx:
            alarm.snooze(now=now)
        self.assertIn("midnight", str(ctx.exception).lower())
        self.assertEqual(alarm.target_time, time(23, 58))
        self.assertEqual(alarm.snooze_count, 0)

    def test_dismiss_lifecycle(self):
        alarm = Alarm(target_time=time(10, 0))
        self.assertTrue(alarm.is_active)
        alarm.dismiss()
        self.assertFalse(alarm.is_active)
        self.assertEqual(alarm.state, AlarmState.DISMISSED)


class TestDisplayModule(unittest.TestCase):
    """Test display formatting functions."""

    def test_format_timedelta(self):
        self.assertEqual(
            display.format_timedelta(timedelta(hours=2, minutes=15, seconds=30)),
            "02:15:30",
        )
        self.assertEqual(
            display.format_timedelta(timedelta(minutes=5, seconds=3)),
            "00:05:03",
        )
        self.assertEqual(
            display.format_timedelta(timedelta(seconds=-10)),
            "00:00:00",
        )

    def test_banner_and_box_drawing(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            display.show_banner()
        output = buf.getvalue()
        self.assertIn("ALARM", output)
        self.assertIn("CLOCK", output)


if __name__ == "__main__":
    unittest.main()
