# Architecture Design

## High-Level Architecture

Three-layer architecture with strict **unidirectional** dependency flow:

```
┌──────────────────────────────────────────────────┐
│                alarm.py (CLI Layer)               │
│     argparse, signal handling, main loop          │
├──────────────────┬───────────────────────────────┤
│                  │                               │
│       ▼          │          ▼                    │
│                  │                               │
│   models.py      │      display.py               │
│   (Service)      │      (Display)                │
│                  │                               │
│   Alarm state,   │      Output formatting,       │
│   time logic,    │      alerts, prompts          │
│   validation     │                               │
│                  │                               │
└──────────────────┴───────────────────────────────┘
```

## Module Responsibilities

| Module         | Responsibility                                | Depends On      |
|----------------|-----------------------------------------------|-----------------|
| `models.py`    | Alarm dataclass, time parsing, validation     | Nothing (pure)  |
| `display.py`   | Every `print()` and `input()` in the app      | Nothing (pure)  |
| `alarm.py`     | Orchestration, argparse, signals, main loop   | models, display |

## Key Classes

### `AlarmState` (Enum)
Explicit lifecycle states: `PENDING → RINGING → SNOOZED → DISMISSED`

### `Alarm` (Dataclass)
- `target_time: time` — when to fire
- `snooze_minutes: int` — configurable snooze duration
- `state: AlarmState` — current lifecycle state
- Methods: `time_remaining()`, `is_due()`, `ring()`, `snooze()`, `dismiss()`

### Module-level functions
- `parse_time()` — input parsing (runs *before* Alarm exists)
- `validate_future()` — temporal validation

## Design Decisions

| # | Decision | Alternative Rejected | Rationale |
|---|----------|---------------------|-----------|
| 1 | `@dataclass` | Plain class, NamedTuple | Mutable (snooze needs mutation), minimal boilerplate |
| 2 | `AlarmState` enum | Boolean flags | Explicit state machine is self-documenting and traceable |
| 3 | `time.sleep(1)` polling | threading, asyncio, sched | Simplest; meets ±1s accuracy; no concurrency needed |
| 4 | Injectable `now` parameter | `unittest.mock.patch` | Zero test infrastructure; just pass a fixed datetime |
| 5 | Functions for display (not class) | `Display` class | No state to manage; a class would be an empty bag |
| 6 | `ValueError` exceptions | Result types, Optional | Idiomatic Python; CLI layer already has try/except |
| 7 | `\r` carriage return | curses, rich | No dependencies; sufficient for single-line countdown |
| 8 | Sequential alarm processing | Concurrent/threaded | Simple, predictable; right tradeoff for a CLI tool |
| 9 | `argparse` for CLI args | Manual `sys.argv` parsing | Stdlib, auto-generates `--help`, handles edge cases |

## Data Flow

```
User Input → alarm.py → parse_time() → validate_future() → Alarm()
                ↓
           wait_for_alarm() ←→ Alarm.is_due() / .time_remaining()
                ↓                    ↑
           show_countdown()          │
                ↓                    │
           show_alert() → prompt_snooze()
                              ↓
                    ┌─── snooze ───→ Alarm.snooze() ──→ (back to wait)
                    └─── dismiss ──→ Alarm.dismiss() ─→ (next alarm or exit)
```
