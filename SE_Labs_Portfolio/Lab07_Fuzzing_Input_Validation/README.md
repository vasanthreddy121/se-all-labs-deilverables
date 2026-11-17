# Software Engineering Lab 7 — Fuzzing for Input Validation Bugs

**Institution:** PES University  
**Department:** Computer Science and Engineering  
**Course:** Software Engineering Lab (UE23CS352A)  
**Student Name:** Vasanth Kumar Reddy  
**SRN:** PES2UG25CS829  
**Domain:** Bowling Alley Score Parser  
**Repository:** [https://github.com/vasanthreddy121/se-lab7](https://github.com/vasanthreddy121/se-lab7)  
**Branch:** `main`  

---

## 1. Executive Summary

This laboratory explores **property-based fuzz testing** using the Python **Hypothesis** library to detect and remediate input-validation vulnerabilities in a Bowling Alley score parsing application. While traditional unit tests evaluate pre-selected "happy-path" inputs, fuzz testing automatically generates diverse, unexpected, and adversarial inputs (including null bytes, extreme Unicode, empty strings, delimiter violations, and invalid boundaries) and minimizes failing examples to pinpoint bugs.

---

## 2. Directory Layout & Deliverables

```
se-lab7/
├── .gitignore
├── README.md                              <- Project overview & quick start
└── LAB7/
    ├── README.md                          <- This technical specification & guide
    ├── requirements.txt                   <- Python package dependencies
    ├── processor.py                       <- Hardened Bowling Alley parser (Handout primary)
    ├── bowling_alley_parser.py            <- Hardened Bowling Alley parser (Specification alias)
    ├── test_processor.py                  <- Hypothesis fuzz test suite (Handout primary)
    ├── test_bowling_alley_parser.py       <- Hypothesis fuzz test suite (Specification alias)
    ├── PES2UG25CS829_Vasanth_Kumar_Reddy_LAB7.pdf <- Final comprehensive laboratory report
    └── screenshots/
        ├── SS1_buggy_cli.png              <- Step 2: Buggy CLI execution (happy path)
        ├── SS2_fuzz_failures.png          <- Step 4: Hypothesis test failures on buggy code
        ├── SS2_fuzz_failures_p1.png       <- SS2 failure trace part 1 (for PDF)
        ├── SS2_fuzz_failures_p2.png       <- SS2 failure trace part 2 & summary (for PDF)
        ├── SS3_fixed_cli.png              <- Step 5: Hardened CLI execution (edge cases handled)
        └── SS4_fuzz_passes.png            <- Step 6: 100% passing Hypothesis test execution
```

*Note on file naming:* Both `processor.py` / `test_processor.py` (prescribed by the lab handout) and `bowling_alley_parser.py` / `test_bowling_alley_parser.py` (prescribed by the task specification) are fully supported and operate identically.

---

## 3. Function Specifications & Defensive Validation Policies

### Function 1: `format_player_name(name)`
- **Purpose:** Formats player names for the bowling alley scorecard display.
- **Valid Behavior:** Strips surrounding whitespace, normalizes multiple internal spaces, converts to Title Case, and enforces a maximum length of 10 characters.
- **Defensive Policy:** If `name` is `None`, non-string, or collapses to an empty string, returns the safe default fallback `"Anonymous"`. Guarantees a non-empty string with no untrimmed whitespace and length <= 10.

### Function 2: `parse_frame(frame_str)`
- **Purpose:** Parses bowling frame strings into a 2-tuple `(roll1, roll2)` representing pins knocked down per roll.
- **Valid Formats:**
  - Strike: `"X"` or `"x"` -> `(10, 0)`
  - Spare: `"<d>/"` where `<d>` is ASCII decimal `'0'`-`'9'` or `'-'` (gutter ball = 0) -> `(d, 10 - d)` (e.g. `"7/"` -> `(7, 3)`, `"-/"` -> `(0, 10)`)
  - Open Frame: `"<d1><d2>"` where each roll is an ASCII decimal digit or `'-'` -> `(d1, d2)` (e.g. `"45"` -> `(4, 5)`, `"-5"` -> `(0, 5)`)
- **Domain Invariant & Decimal Validation:** In 10-pin bowling, open-frame rolls must satisfy `roll1 + roll2 < 10`. Frames totaling 10 or more without spare notation (e.g., `"88"`) are physically impossible and rejected. Furthermore, non-ASCII/Unicode numeric characters (such as superscripts like `'²'`, `'³'`) that pass Python's `str.isdigit()` but fail `int()` conversions or violate bowling notation are strictly rejected.
- **Defensive Policy:** Any `None`, non-string, malformed, empty, Unicode numeric, or rule-violating input safely returns fallback `(0, 0)`.

### Function 3: `parse_scoreboard(data)`
- **Purpose:** Parses comma-separated `Name:Score` records into a dictionary mapping player names to integer scores.
- **Valid Format:** e.g., `"Alice:150,Bob:210,Charlie:95"` -> `{'Alice': 150, 'Bob': 210, 'Charlie': 95}`
- **Defensive Policies:**
  - `None` or non-string inputs safely return an empty dictionary `{}`.
  - Comma splitting ignores empty records caused by leading, trailing, or consecutive commas.
  - Each entry must contain exactly one `:` delimiter; invalid delimiters are skipped.
  - Player names are cleaned via `format_player_name`; blank names are rejected.
  - Scores are validated as integers within legal 10-pin bowling range `[0, 300]`. Negative or out-of-range scores are discarded.
  - **Duplicate Resolution Policy:** If a player appears multiple times on the scoreboard, the highest score achieved is retained (`max(existing, score)`).

---

## 4. Fuzz-Discovered Bugs & Remediation Matrix

| Function | Fuzz-Exposed Bug | Minimal Failing Input | Root Cause | Implemented Fix |
|---|---|---|---|---|
| `format_player_name` | Unhandled `AttributeError` | `s=None` | Called `.strip()` directly on `None` | Type guard `isinstance(name, str)` returning `'Anonymous'` fallback |
| `format_player_name` | Empty string display violation | `s=''` or `s='   '` | No check for empty string after strip | Fallback to `'Anonymous'` if normalized string is empty |
| `parse_frame` | Unhandled `TypeError` | `f=None` | Checked `'/' in frame_str` on `NoneType` | Type guard returning safe fallback `(0, 0)` |
| `parse_frame` | Unhandled `IndexError` | `f=''` | Unchecked string indexing `frame_str[0]` | Empty string check returning safe fallback `(0, 0)` |
| `parse_frame` | Unhandled `ValueError` | `f='/'` or `f=':'` | Unchecked `int(frame_str[0])` conversion | Character validation against valid digits and `'-'` |
| `parse_frame` | Invalid frame over-acceptance | `f='88'` | Blindly parsed `(8, 8)` = 16 pins > 10 | Strict domain check `roll1 + roll2 < 10` for open frames |
| `parse_frame` | Unicode numeric crash | `f='²'` or `f='²/'` | `'²'.isdigit()` is True, but `int('²')` raises `ValueError` | Strict ASCII decimal validation via `_char_to_pins` (`c in '0123456789'`) |
| `parse_scoreboard` | Unhandled `AttributeError` | `s=None` | Called `.split(',')` on `NoneType` | Returns empty dict `{}` on non-string |
| `parse_scoreboard` | Unhandled `ValueError` (unpack) | `s=''` or `s='Alice:150,'` | Expected 2 tokens from `split(':')` | Validates `len(parts) == 2` per record |
| `parse_scoreboard` | Unhandled `ValueError` (int) | `s='Alice:bad'` | Unchecked `int()` conversion | `try-except (ValueError, TypeError)` validation |
| `parse_scoreboard` | Corrupt out-of-bounds scores | `s='Alice:-10'` | Accepted negative bowling scores | Enforces legal bowling score range `[0, 300]` |
| `parse_scoreboard` | Non-ASCII numerals & signed scores | `s='Alice:١٥٠'` or `s='Alice:+150'` | Accepted Arabic-Indic digits or signed strings | Enforces `raw_score.isascii() and raw_score.isdecimal()` |
| `parse_scoreboard` | Non-deterministic duplicate names | `s='Alice:100,Alice:200'` | Overwrote previous scores arbitrarily | High-score retention policy `max(old, new)` |

---

## 5. Setup & Execution Instructions

### Prerequisites
- Python 3.8+ (tested on Python 3.12.3)
- `pip`

### Step 1: Install Dependencies
```bash
cd se-lab7/LAB7
pip install -r requirements.txt
```

### Step 2: Run Application Demonstration
```bash
python processor.py
# Or using the alias:
python bowling_alley_parser.py
```

### Step 3: Run Hypothesis Fuzz Test Suite
```bash
pytest test_processor.py -v
# Or using the alias:
pytest test_bowling_alley_parser.py -v
```

---

## 6. Test Suite Results

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/vasanth-reddy/Documents/se/lab7/Codex_Lab7_Task_Pack/se-lab7/LAB7
plugins: hypothesis-6.170.15
collected 11 items

test_processor.py::test_format_player_name_no_crash PASSED               [  9%]
test_processor.py::test_format_player_name_valid_inputs PASSED           [ 18%]
test_processor.py::test_parse_frame_no_crash PASSED                      [ 27%]
test_processor.py::test_parse_frame_standard_cases PASSED                [ 36%]
test_processor.py::test_parse_frame_invalid_inputs PASSED                [ 45%]
test_processor.py::test_parse_frame_unicode_digits_regression PASSED     [ 54%]
test_processor.py::test_parse_scoreboard_no_crash PASSED                 [ 63%]
test_processor.py::test_parse_scoreboard_valid_cases PASSED              [ 72%]
test_processor.py::test_parse_scoreboard_duplicate_names PASSED          [ 81%]
test_processor.py::test_parse_scoreboard_ascii_score_regression PASSED   [ 90%]
test_processor.py::test_parse_scoreboard_malformed_entries PASSED        [100%]

============================== 11 passed in 0.47s ==============================
```

- Total Property Tests: 3 property-based fuzz tests (each executing 100 random examples = 300 fuzz iterations).
- Total Unit / Boundary / Regression Tests: 8 targeted domain tests (including Unicode numeric frame regression and ASCII scoreboard score regression).
- Status: **11 passed, 0 failed (100% pass rate)**.
