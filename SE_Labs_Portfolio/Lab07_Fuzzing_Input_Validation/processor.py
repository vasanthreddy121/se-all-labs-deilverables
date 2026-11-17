"""
Bowling Alley Parser (Hardened / Fixed Version)
Lab 7: Fuzzing for Input Validation Bugs
Student: Vasanth Kumar Reddy (PES2UG25CS829)
Course: Software Engineering Lab - PES University

Hardened implementation with comprehensive defensive input validation,
robust type checking, safe fallbacks, decimal-digit validation, and deterministic error handling.
Resistant to crashes from fuzz-discovered edge cases, Unicode numeric characters, and malicious inputs.
"""

from typing import Dict, Tuple, Any, Optional

DECIMAL_DIGITS = "0123456789"


def format_player_name(name: Any) -> str:
    """
    Format player name into title case, truncated to 10 characters.

    Defensive Validation Policy:
    - If name is None, non-string, or empty/whitespace: returns fallback 'Anonymous'.
    - Strips leading/trailing whitespace and collapses internal multiple spaces.
    - Formats to Title Case.
    - Truncates to a maximum length of 10 characters.
    - Guarantees non-empty string without untrimmed whitespace.
    """
    if name is None or not isinstance(name, str):
        return "Anonymous"

    # Normalize internal and surrounding whitespace
    cleaned = " ".join(name.split())
    if not cleaned:
        return "Anonymous"

    # Format to Title Case and enforce max length 10
    formatted = cleaned.title()[:10].strip()
    return formatted if formatted else "Anonymous"


def _char_to_pins(c: str) -> Optional[int]:
    """
    Convert a single roll character to pins knocked down (0-9).
    Returns integer pinfall for valid ASCII digits or '-' (gutter ball = 0).
    Returns None for any non-decimal character (including Unicode superscripts like '²').
    """
    if c == "-":
        return 0
    if c in DECIMAL_DIGITS:
        return int(c)
    return None


def parse_frame(frame_str: Any) -> Tuple[int, int]:
    """
    Parse a bowling frame representation into pins knocked down per roll.
    - Strike: 'X' or 'x' -> (10, 0)
    - Spare:  '<digit>/' (e.g. '7/') -> (7, 3), '-/' -> (0, 10)
    - Open:   '<d1><d2>' (e.g. '45') -> (4, 5), '-5' -> (0, 5)

    Defensive Validation Policy:
    - Safe fallback: (0, 0) on any invalid, malformed, or out-of-range input.
    - Validates type (must be str).
    - Checks for strike ('X' or 'x').
    - Robust Decimal Digit Validation: Rejects non-ASCII/Unicode digits (e.g. '²', '³')
      that pass str.isdigit() but crash int() conversions or represent invalid notation.
    - Spare validation: verifies roll 1 is a valid ASCII decimal digit (0-9) or '-' (0),
      and computes roll 2 as (10 - roll 1).
    - Open frame validation: verifies both rolls are valid ASCII decimal digits or '-',
      and strictly enforces the fundamental bowling rule that roll1 + roll2 < 10
      (frames totaling >= 10 without spare notation, e.g. '88', are invalid).
    - Guarantees return value is always a 2-tuple (roll1, roll2) of integers
      with 0 <= roll1 <= 10, 0 <= roll2 <= 10, and roll1 + roll2 <= 10.
    """
    if frame_str is None or not isinstance(frame_str, str):
        return (0, 0)

    s = frame_str.strip().upper()
    if not s:
        return (0, 0)

    # 1. Strike
    if s == "X":
        return (10, 0)

    # 2. Spare: length 2, second roll is '/'
    if len(s) == 2 and s[1] == "/":
        r1 = _char_to_pins(s[0])
        if r1 is None:
            return (0, 0)
        return (r1, 10 - r1)

    # 3. Open frame or two rolls
    if len(s) == 2:
        r1 = _char_to_pins(s[0])
        r2 = _char_to_pins(s[1])
        if r1 is None or r2 is None:
            return (0, 0)
        # Bowling rule: open frame total pins must be strictly less than 10
        if r1 + r2 >= 10:
            return (0, 0)
        return (r1, r2)

    # 4. Single roll fallback
    if len(s) == 1:
        r1 = _char_to_pins(s[0])
        if r1 is not None:
            return (r1, 0)

    return (0, 0)


def parse_scoreboard(data: Any) -> Dict[str, int]:
    """
    Parse scoreboard string formatted as 'Name:Score,Name:Score,...'
    into a dictionary mapping player name to integer score.

    Defensive Validation Policy:
    - Safe fallback: returns empty dict {} if data is None or non-string.
    - Handles missing/extra delimiters: splits entries by comma, discarding
      empty segments caused by leading, trailing, or consecutive commas.
    - Strict pair requirement: each entry must contain exactly one ':' delimiter.
    - Name validation: formats name via format_player_name; skips entry if name is empty.
    - Score validation: must parse to a valid integer within legal bowling game
      range [0, 300]. Validates ASCII decimal characters. Negative or >300 scores are ignored.
    - Duplicate names policy: retains the highest score achieved by the player.
    - Guarantees return value is always a Dict[str, int] with non-empty keys
      and scores in [0, 300].
    """
    if data is None or not isinstance(data, str):
        return {}

    scoreboard: Dict[str, int] = {}
    entries = data.split(",")

    for raw_entry in entries:
        entry = raw_entry.strip()
        if not entry:
            continue

        parts = entry.split(":")
        if len(parts) != 2:
            continue

        raw_name, raw_score = parts[0].strip(), parts[1].strip()
        if not raw_name:
            continue

        # Format and validate player name (10-char limit)
        name = format_player_name(raw_name)
        if not name:
            continue

        # Accept ASCII decimal digits only; reject Unicode numerals and signs.
        if not raw_score or not raw_score.isascii() or not raw_score.isdecimal():
            continue

        # Convert and validate legal bowling score range [0, 300].
        score = int(raw_score)

        if not (0 <= score <= 300):
            continue

        # Duplicate resolution policy: keep highest score
        if name in scoreboard:
            scoreboard[name] = max(scoreboard[name], score)
        else:
            scoreboard[name] = score

    return scoreboard


def main():
    print("=" * 60)
    print("  BOWLING ALLEY PARSER - HARDENED SYSTEM DEMONSTRATION")
    print("=" * 60)

    print("\n[1] Formatting Player Names (Max 10 Chars & Safe Fallbacks):")
    sample_names = [
        "alice smith",
        "BOB JONES",
        "  charlie brown  ",
        None,
        "",
        "   ",
        "a_very_long_player_name_exceeding_limit",
    ]
    for name in sample_names:
        print(f"    Input: {name!r:<42} -> Formatted: {format_player_name(name)!r}")

    print("\n[2] Parsing Bowling Frames (Happy Path, Unicode & Malformed Cases):")
    sample_frames = ["X", "x", "7/", "45", "-5", "88", "²/", "²5", "abc", "", None]
    for frame in sample_frames:
        print(f"    Frame: {frame!r:<8} -> Rolls: {parse_frame(frame)}")

    print("\n[3] Parsing Scoreboard (Normal, Corrupt & Boundary Entries):")
    raw_board = "Alice:150,Bob:210,Charlie:95,Alice:220,,Dave:bad,Eve:-10,:100"
    print(f"    Raw input : {raw_board}")
    print(f"    Scoreboard: {parse_scoreboard(raw_board)}")

    print("\n" + "=" * 60)
    print("  Hardened demonstration completed successfully without errors.")
    print("=" * 60)


if __name__ == "__main__":
    main()
