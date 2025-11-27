# backend/utils/timewin.py
# Utilities for parsing time strings and checking open-hour windows.

from typing import Tuple, Optional

def parse_time_hhmm(hhmm: str) -> int:
    """
    'HH:MM' -> minutes since midnight.
    Accepts '8:5' as 8:05 as well.
    """
    hhmm = hhmm.strip()
    if not hhmm:
        raise ValueError("Empty time string")
    parts = hhmm.split(":")
    if len(parts) != 2:
        raise ValueError(f"Bad time format: {hhmm}")
    h = int(parts[0])
    m = int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Out of range time: {hhmm}")
    return h * 60 + m

def normalize_dash(s: str) -> str:
    """
    Normalize different dash characters to a plain hyphen.
    Handles '–', '—', '−' -> '-'
    """
    return s.replace("–", "-").replace("—", "-").replace("−", "-")

def parse_window_str(win: str) -> Tuple[int, int]:
    """
    'HH:MM-HH:MM' or 'HH:MM–HH:MM' -> (start_min, end_min)
    Assumes same-day windows (no overnight).
    """
    if not win:
        raise ValueError("Empty window string")
    win = normalize_dash(win.strip())
    if "-" not in win:
        raise ValueError(f"Bad window format: {win}")
    left, right = [w.strip() for w in win.split("-", 1)]
    start = parse_time_hhmm(left)
    end = parse_time_hhmm(right)
    if end <= start:
        # If your data might include overnight spans, handle here.
        # For now, enforce same-day increasing windows.
        raise ValueError(f"Non-increasing window: {win}")
    return (start, end)

def window_overlap_minutes(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """
    Overlap length (in minutes) between [a.start,a.end) and [b.start,b.end).
    Returns 0 if no overlap.
    """
    s = max(a[0], b[0])
    e = min(a[1], b[1])
    return max(0, e - s)

def is_open_for_window(open_str: str, target_win: Tuple[int, int]) -> bool:
    """
    Returns True if the restaurant open window intersects the target window by any positive minutes.
    """
    try:
        ow = parse_window_str(open_str)
    except Exception:
        return False
    return window_overlap_minutes(ow, target_win) > 0

# Common lunch/dinner windows as minutes
LUNCH_WINDOW = (parse_time_hhmm("11:30"), parse_time_hhmm("14:00"))
DINNER_WINDOW = (parse_time_hhmm("17:30"), parse_time_hhmm("20:30"))

