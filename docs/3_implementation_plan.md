# Implementation Plan

## Build Order

```
models.py (zero deps) → display.py (zero deps) → alarm.py (depends on both)
```

Leaf dependencies first — every file is runnable the moment it's saved.

## File-by-File Plan

### Step 1: `models.py` (~150 LOC)

| # | Component          | Purpose                                    |
|---|--------------------|--------------------------------------------|
| 1 | `SNOOZE_MINUTES_DEFAULT` | Module constant, 5 minutes               |
| 2 | `AlarmState`       | Enum: PENDING, RINGING, SNOOZED, DISMISSED |
| 3 | `parse_time()`     | Parse HH:MM → `time` object               |
| 4 | `validate_future()`| Reject past times                          |
| 5 | `Alarm` dataclass  | State, time queries, transitions           |

**Bugs to watch:**
- `time` name collision with stdlib `time` module → don't import `time` module here
- `snooze()` crossing midnight → use full datetime arithmetic + guard

### Step 2: `display.py` (~145 LOC)

| # | Component          | Purpose                                    |
|---|--------------------|--------------------------------------------|
| 1 | `format_timedelta` | timedelta → "HH:MM:SS" string             |
| 2 | `show_banner`      | App header                                 |
| 3 | `prompt_*`         | All input() calls (time, add_more, snooze) |
| 4 | `show_*`           | All print() calls (errors, alerts, status) |

**Bugs to watch:**
- `show_countdown` must `flush=True` to defeat stdout buffering
- `\r` overwrite must pad with spaces to clear stale characters
- `format_timedelta` must clamp negative values to zero

### Step 3: `alarm.py` (~200 LOC)

| # | Component            | Purpose                                  |
|---|----------------------|------------------------------------------|
| 1 | `build_parser()`     | argparse setup                           |
| 2 | `handle_sigint()`    | Clean Ctrl+C during sleep                |
| 3 | `create_alarm_from_arg()` | Validate + create from CLI arg      |
| 4 | `get_alarms_interactive()` | Prompt loop for multiple alarms    |
| 5 | `get_alarms()`       | Dispatch: args vs interactive            |
| 6 | `wait_for_alarm()`   | Countdown loop                           |
| 7 | `handle_trigger()`   | Alert → snooze/dismiss                   |
| 8 | `run()`              | Sequential alarm processing loop         |
| 9 | `main()`             | Entry point                              |

**Bugs to watch:**
- `import time as time_mod` to avoid shadowing `datetime.time`
- Dual Ctrl+C: `signal.signal` for sleep + `try/except` for input
- Snooze loop: `while snoozed` must return `False` on dismiss to exit

## Time Budget (30 minutes)

| Phase              | Time  | Deliverable                              |
|--------------------|-------|------------------------------------------|
| models.py          | 7 min | Alarm, parsing, validation               |
| display.py         | 7 min | 15 display/input functions               |
| alarm.py           | 10 min| argparse, multi-alarm loop, signal handling |
| Smoke test         | 3 min | End-to-end manual test                   |
| Polish             | 3 min | Docstrings, edge cases, code review      |
