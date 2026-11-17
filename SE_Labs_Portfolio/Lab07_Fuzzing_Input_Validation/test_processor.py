"""
Hypothesis Fuzz Test Suite for Bowling Alley Parser
Lab 7: Fuzzing for Input Validation Bugs
Student: Vasanth Kumar Reddy (PES2UG25CS829)
Course: Software Engineering Lab - PES University
"""

import pytest
from hypothesis import given, strategies as st, settings, Verbosity
from processor import format_player_name, parse_frame, parse_scoreboard


# ---------------------------------------------------------------------------
# 1. Tests for format_player_name
# ---------------------------------------------------------------------------

@settings(max_examples=100, verbosity=Verbosity.normal)
@given(st.text() | st.none())
def test_format_player_name_no_crash(s):
    """
    Property: For any string or None input, format_player_name must:
    1. Never raise an unhandled exception.
    2. Return a non-empty string fallback (e.g. 'Anonymous') if input is empty/whitespace/None.
    3. Not exceed the maximum display length (10 characters).
    4. Not contain untrimmed leading or trailing whitespace.
    """
    result = format_player_name(s)
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    assert len(result) > 0, "Formatted name should not be empty"
    assert len(result) <= 10, f"Formatted name exceeds 10 chars: {result!r}"
    assert result == result.strip(), f"Formatted name has untrimmed whitespace: {result!r}"


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", min_size=1, max_size=30).filter(lambda x: x.strip() != ""))
def test_format_player_name_valid_inputs(name):
    """
    Property: Valid non-empty alphabetic names should be properly title-cased
    and truncated to at most 10 characters without crashing.
    """
    result = format_player_name(name)
    assert isinstance(result, str)
    assert len(result) <= 10
    assert result == result.strip()


# ---------------------------------------------------------------------------
# 2. Tests for parse_frame
# ---------------------------------------------------------------------------

@settings(max_examples=100, verbosity=Verbosity.normal)
@given(st.text() | st.none())
def test_parse_frame_no_crash(f):
    """
    Property: For any string or None input, parse_frame must:
    1. Never raise an unhandled exception.
    2. Always return a 2-tuple of integers (roll1, roll2).
    3. Each roll must be between 0 and 10 pins.
    4. Total pins in a frame cannot exceed 10 (defensive validation against invalid frames).
    """
    result = parse_frame(f)
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-tuple, got {result}"
    r1, r2 = result
    assert isinstance(r1, int) and isinstance(r2, int), f"Rolls must be ints, got {result}"
    assert 0 <= r1 <= 10, f"Roll 1 out of bounds [0, 10]: {r1}"
    assert 0 <= r2 <= 10, f"Roll 2 out of bounds [0, 10]: {r2}"
    assert r1 + r2 <= 10, f"Total pins in frame exceed 10: {result}"


def test_parse_frame_standard_cases():
    """Verify expected behavior on standard valid bowling frames."""
    assert parse_frame("X") == (10, 0)
    assert parse_frame("7/") == (7, 3)
    assert parse_frame("45") == (4, 5)
    assert parse_frame("-5") == (0, 5)
    assert parse_frame("0/") == (0, 10)


def test_parse_frame_invalid_inputs():
    """Verify safe fallback (0, 0) on malformed or physically impossible frames."""
    assert parse_frame("") == (0, 0)
    assert parse_frame("88") == (0, 0)  # 8 + 8 = 16 > 10 (invalid bowling frame)
    assert parse_frame("abc") == (0, 0)
    assert parse_frame(None) == (0, 0)


def test_parse_frame_unicode_digits_regression():
    """
    Regression test: Ensure Unicode numeric characters (e.g. superscripts like '²')
    are safely rejected and do not cause unhandled ValueError or bypass validation.
    Python's str.isdigit() returns True for '²', but int('²') raises ValueError.
    """
    assert parse_frame("²") == (0, 0)
    assert parse_frame("²/") == (0, 0)
    assert parse_frame("²5") == (0, 0)
    assert parse_frame("5²") == (0, 0)
    assert parse_frame("²²") == (0, 0)
    assert parse_frame("³/") == (0, 0)
    assert parse_frame("¹") == (0, 0)
    assert parse_frame("⁴0") == (0, 0)


# ---------------------------------------------------------------------------
# 3. Tests for parse_scoreboard
# ---------------------------------------------------------------------------

@settings(max_examples=100, verbosity=Verbosity.normal)
@given(st.text() | st.none())
def test_parse_scoreboard_no_crash(s):
    """
    Property: For any arbitrary text or None input, parse_scoreboard must:
    1. Never raise an unhandled exception.
    2. Always return a dictionary.
    3. Every key in the dictionary must be a non-empty, stripped string.
    4. Every value must be an integer within legal bowling score range [0, 300].
    """
    result = parse_scoreboard(s)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    for name, score in result.items():
        assert isinstance(name, str) and len(name) > 0, f"Invalid player name: {name!r}"
        assert name == name.strip(), f"Name contains unstripped whitespace: {name!r}"
        assert isinstance(score, int), f"Score must be an int, got {type(score)}"
        assert 0 <= score <= 300, f"Score out of bowling range [0, 300]: {score}"


def test_parse_scoreboard_valid_cases():
    """Verify parsing of well-formed scoreboard data."""
    raw = "Alice:150,Bob:210,Charlie:95"
    expected = {"Alice": 150, "Bob": 210, "Charlie": 95}
    assert parse_scoreboard(raw) == expected


def test_parse_scoreboard_duplicate_names():
    """Verify deterministic duplicate policy: keeps highest score achieved."""
    raw = "Alice:150,Bob:200,Alice:220"
    result = parse_scoreboard(raw)
    assert result["Alice"] == 220
    assert result["Bob"] == 200


def test_parse_scoreboard_ascii_score_regression():
    """
    Regression: scoreboard scores must use ASCII decimal digits only.
    Reject Arabic-Indic digits and signed values, while accepting ordinary digits.
    """
    assert parse_scoreboard("Alice:١٥٠") == {}
    assert parse_scoreboard("Alice:+150") == {}
    assert parse_scoreboard("Alice:-150") == {}
    assert parse_scoreboard("Alice:150") == {"Alice": 150}


def test_parse_scoreboard_malformed_entries():
    """Verify defensive handling skips corrupt entries without crashing."""
    raw = "Alice:150,,Bob:bad,Charlie:-10,Dave:500,:100,Eve:200"
    result = parse_scoreboard(raw)
    # Valid entries: Alice (150) and Eve (200)
    assert result.get("Alice") == 150
    assert result.get("Eve") == 200
    assert "Bob" not in result
    assert "Charlie" not in result
    assert "Dave" not in result
