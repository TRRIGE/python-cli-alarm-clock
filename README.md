# ⏰ Alarm Clock CLI

A Python command-line alarm clock built as a software engineering assessment. The goal was to demonstrate structured engineering thinking — requirement analysis, architecture design, deliberate tradeoffs, and disciplined implementation — not feature volume.

**No detailed specification was provided.** Requirements were derived through analysis, prioritisation, and engineering judgement.

---

## Features

- **Set alarms** using `HH:MM` (24-hour format) — one or many
- **Command-line arguments** — `python alarm.py 07:30 14:00` for quick setup
- **Interactive mode** — guided prompts when no arguments given
- **Input validation** with clear, actionable error messages
- **Live countdown** updating in-place every second
- **Visual + audible alert** — box-drawn banner + terminal bell
- **Snooze** with configurable duration (`--snooze 10`)
- **Midnight guard** — prevents snooze from rolling past midnight
- **Graceful Ctrl+C** at every stage — no stack traces, ever

---

## Quick Start

### Prerequisites

- **Python 3.11+** (no external dependencies)

### Installation

```bash
git clone <repo-url>
cd alarm_clock
```

### Usage

```bash
# Interactive mode — prompted step by step
python alarm.py

# Quick-set alarms via arguments
python alarm.py 07:30
python alarm.py 07:30 14:00 22:00

# Custom snooze duration (default: 5 minutes)
python alarm.py 07:30 --snooze 10

# Help
python alarm.py --help
```

---

## Example Session

```
  ╔══════════════════════════════════════╗
  ║          ⏰  ALARM  CLOCK            ║
  ╠══════════════════════════════════════╣
  ║  24-hour format  ·  Ctrl+C to quit   ║
  ╚══════════════════════════════════════╝

  Enter alarm time (HH:MM): abc
  ✗ Invalid format: 'abc'. Please use HH:MM (24-hour).
  Enter alarm time (HH:MM): 01:00
  ✗ Time 01:00 has already passed. Please enter a future time.
  Enter alarm time (HH:MM): 21:30
  ✓ Alarm set for 21:30  (00:05:12 away)
  Add another alarm? (y/N): y
  Enter alarm time (HH:MM): 21:35
  ✓ Alarm set for 21:35  (00:10:12 away)
  Add another alarm? (y/N): n

  ┌──── Scheduled Alarms ─────┐
  │  1. 21:30   pending       │
  │  2. 21:35   pending       │
  └────────────────────────────┘

  ⏳ Waiting for alarm 1/2 — 21:30
  ⏳ 00:00:03

  ╔══════════════════════════════════════╗
  ║         🔔  ALARM!  🔔               ║
  ║         Time: 21:30                  ║
  ╚══════════════════════════════════════╝

  [S]nooze / [D]ismiss: s
  💤 Snoozed (×1)! New alarm: 21:35

  ⏳ 00:04:58

  ╔══════════════════════════════════════╗
  ║         🔔  ALARM!  🔔               ║
  ║         Time: 21:35                  ║
  ╚══════════════════════════════════════╝

  [S]nooze / [D]ismiss: d
  ✓ Alarm dismissed.

  ⏳ Waiting for alarm 2/2 — 21:35
  ...

  ✓ All alarms complete!
```

---

## Architecture

### Three-Layer Design

```
┌──────────────────────────────────────────────────┐
│                alarm.py (CLI Layer)               │
│     argparse, signal handling, main loop          │
├──────────────────┬───────────────────────────────┤
│       ▼          │          ▼                    │
│   models.py      │      display.py               │
│   (Service)      │      (Display)                │
│   Pure logic     │      Pure formatting          │
│   Zero I/O       │      Zero domain logic        │
└──────────────────┴───────────────────────────────┘
```

| Module       | Lines | Responsibility                                | Imports From Project |
|-------------|-------|-----------------------------------------------|---------------------|
| `models.py`  | ~150  | `Alarm` dataclass, `AlarmState` enum, parsing, validation | None (pure logic) |
| `display.py` | ~145  | Every `print()` and `input()` in the entire app | None (pure formatting) |
| `alarm.py`   | ~200  | argparse, signal handling, orchestration loop  | models, display |

Both leaf modules (`models.py`, `display.py`) have **zero project dependencies**, making them independently testable with no mocking.

### Alarm Lifecycle

```
PENDING ──→ RINGING ──→ DISMISSED
               │
               ▼
            SNOOZED ──→ RINGING ──→ ...
```

---

## Design Decisions & Tradeoffs

| # | Decision | Alternative Rejected | Rationale |
|---|----------|---------------------|-----------|
| 1 | **`@dataclass`** for Alarm | Plain class, NamedTuple | Mutable (snooze needs mutation), minimal boilerplate, free `__repr__` |
| 2 | **`AlarmState` enum** | Boolean flags (`is_ringing`, `is_dismissed`) | Explicit state machine is self-documenting and prevents invalid states |
| 3 | **`time.sleep(1)` polling** | `threading.Event`, `asyncio`, `sched` | Simplest approach; meets ±1s accuracy; single-threaded CLI needs no concurrency |
| 4 | **Injectable `now` parameter** | `unittest.mock.patch` | Zero test infrastructure; pass a fixed `datetime` for deterministic tests |
| 5 | **Module-level functions** for display | `Display` class | No state to manage; a class would be an empty bag of methods |
| 6 | **`ValueError` exceptions** | Result types, `Optional` returns | Idiomatic Python; CLI layer already has try/except loops |
| 7 | **`\r` carriage return** for countdown | `curses`, `rich` | No dependencies; works cross-platform; sufficient for single-line update |
| 8 | **Sequential alarm processing** | Concurrent/threaded scheduling | Simple and predictable; right tradeoff for a CLI tool |
| 9 | **`argparse`** | Manual `sys.argv` parsing | Stdlib; auto-generates `--help`; handles edge cases robustly |
| 10 | **Midnight snooze guard** | Silent rollover, next-day scheduling | Same-day assumption prevents confusing behaviour; fails explicitly |

---

## AI-Assisted Development Process

This project was developed using AI-assisted tooling. Each phase involved AI generation followed by **human review, validation, and iteration**:

| Phase | AI Contribution | Human Contribution |
|-------|----------------|-------------------|
| **1. Requirement Refinement** | Generated structured requirements, assumptions, edge cases | Reviewed for completeness, adjusted priorities |
| **2. Architecture Design** | Proposed three-layer architecture with design rationale | Evaluated tradeoffs, confirmed alignment with constraints |
| **3. Implementation Planning** | Produced build order, LOC estimates, bug watch list | Verified dependency order, validated time budget |
| **4. Code Generation** | Implemented each module following the plan | Reviewed every function for correctness and style |
| **5. Code Review** | Identified potential bugs (14 catalogued, 4 crash-severity) | Verified each bug was addressed in implementation |
| **6. Validation** | Generated 40+ automated assertions across 3 modules | Ran tests, confirmed all pass, performed manual smoke test |

> **Key principle:** AI output was treated as a draft — every artifact was
> reviewed, questioned, and validated before adoption. The value of AI
> assistance was in accelerating design-space exploration, not in bypassing
> engineering judgement.

### Planning Artifacts

The thinking-before-coding process is documented in [`docs/`](docs/):
1. [`1_requirements.md`](docs/1_requirements.md) — Functional/non-functional requirements, assumptions, edge cases
2. [`2_architecture.md`](docs/2_architecture.md) — Three-layer design, class structure, 9 design decisions
3. [`3_implementation_plan.md`](docs/3_implementation_plan.md) — Build order, bug watch list, time budget

---

## Testing & Validation

### Automated Assertions (40+)

| Module      | Tests | Coverage |
|-------------|-------|----------|
| `models.py` | 18    | `parse_time` (valid/invalid/edge), `validate_future` (past/future/boundary), `Alarm` (state transitions, snooze with count, midnight guard, configurable duration) |
| `display.py`| 12    | `format_timedelta` (normal/negative/fractional), import isolation, all 15 functions present, output content correctness |
| `alarm.py`  | 10    | Dismiss path, snooze path, invalid input retry, Ctrl+C handling, midnight auto-dismiss, already-due alarm, argparse defaults/args |

### Manual Smoke Tests

| # | Scenario                  | Expected                           | Result |
|---|---------------------------|------------------------------------|--------|
| 1 | Invalid input (`abc`)      | Error + re-prompt                 | ✅     |
| 2 | Out-of-range (`25:99`)     | Error + re-prompt                 | ✅     |
| 3 | Empty input                | Error + re-prompt                 | ✅     |
| 4 | Past time                  | Rejected with clear message       | ✅     |
| 5 | Valid alarm 1 min ahead    | Countdown starts                  | ✅     |
| 6 | Alarm triggers             | Alert + bell fires                | ✅     |
| 7 | Snooze                     | New time shown, countdown resumes | ✅     |
| 8 | Dismiss                    | Clean exit                        | ✅     |
| 9 | Ctrl+C during countdown    | "Goodbye!", clean exit            | ✅     |
| 10| Ctrl+C during snooze       | "Goodbye!", clean exit            | ✅     |
| 11| CLI args (`07:30 14:00`)   | Both alarms created               | ✅     |
| 12| `--snooze 10`              | Snooze uses 10 minutes            | ✅     |

---

## Project Structure

```
alarm_clock/
├── alarm.py                  # Entry point — CLI orchestration
├── models.py                 # Domain logic — Alarm, parsing, validation
├── display.py                # Display layer — all terminal I/O
├── tests/
│   └── test_alarm.py         # Standard library unittest suite (zero dependencies)
├── docs/
│   ├── 1_requirements.md     # Requirement analysis (pre-coding)
│   ├── 2_architecture.md     # Architecture design (pre-coding)
│   └── 3_implementation_plan.md  # Build plan (pre-coding)
└── README.md                 # Project documentation
```

### Running Tests

```bash
# Run the automated test suite with standard library unittest
python -m unittest discover -s tests
```

**Total:** ~500 lines across 3 source files.

---

## Future Improvements

| Improvement                   | Complexity | Value  |
|-------------------------------|-----------|--------|
| Unit test suite with `pytest` | Low       | High   |
| Recurring / repeating alarms  | Medium    | Medium |
| Persistent storage (JSON)     | Low       | Low    |
| Named / labeled alarms        | Low       | Medium |
| Custom alarm sounds           | Medium    | Low    |

---

## Conclusion

This project demonstrates that a well-scoped, well-structured solution communicates engineering maturity more effectively than a sprawling feature set.

**What this project shows:**

1. **Requirements before code.** Deriving requirements from an ambiguous prompt is itself an engineering skill. Documenting assumptions and scope boundaries prevents accidental complexity.

2. **Architecture at every scale.** Even a ~500-line project benefits from separation of concerns. The three-layer split makes the code readable, testable, and extensible — without over-engineering.

3. **Tradeoffs over defaults.** Every design decision was an explicit choice with alternatives considered and rejected. Good engineering is about *choosing well*, not choosing the most sophisticated option.

4. **AI as an accelerator, not a replacement.** AI shortened the exploration phase but did not bypass judgement. Every output was reviewed, questioned, and validated — the same standard applied to any generated code in a professional setting.
