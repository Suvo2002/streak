#!/usr/bin/env python3
"""
generate_content.py — Daily content generator for the GitHub streak bot.

Creates / appends to:
  1. log/YYYY-MM-DD.md          — a daily journal entry with a random dev quote
  2. README.md                  — updates the "Streak Stats" block with today's count
  3. log/commit_history.json    — accumulates a JSON record of every commit

Uses only the Python standard library (no pip install needed on Actions).
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on all environments
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─── Configuration ───────────────────────────────────────────────────────────

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parent.parent))
LOG_DIR = REPO_ROOT / "log"
README = REPO_ROOT / "README.md"
COMMIT_HISTORY = LOG_DIR / "commit_history.json"

# ─── Curated quotes (expand freely) ─────────────────────────────────────────

QUOTES: list[dict[str, str]] = [
    {"text": "First, solve the problem. Then, write the code.", "author": "John Johnson"},
    {"text": "Code is like humor. When you have to explain it, it's bad.", "author": "Cory House"},
    {"text": "Make it work, make it right, make it fast.", "author": "Kent Beck"},
    {"text": "Simplicity is prerequisite for reliability.", "author": "Edsger Dijkstra"},
    {"text": "Programs must be written for people to read.", "author": "Harold Abelson"},
    {"text": "Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "author": "Martin Fowler"},
    {"text": "The best error message is the one that never shows up.", "author": "Thomas Fuchs"},
    {"text": "Walking on water and developing software from a specification are easy if both are frozen.", "author": "Edward V. Berard"},
    {"text": "The most damaging phrase in the language is: 'We've always done it this way.'", "author": "Grace Hopper"},
    {"text": "Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away.", "author": "Antoine de Saint-Exupéry"},
    {"text": "The function of good software is to make the complex appear to be simple.", "author": "Grady Booch"},
    {"text": "Before software can be reusable it first has to be usable.", "author": "Ralph Johnson"},
    {"text": "It's not a bug — it's an undocumented feature.", "author": "Anonymous"},
    {"text": "Talk is cheap. Show me the code.", "author": "Linus Torvalds"},
    {"text": "Truth can only be found in one place: the code.", "author": "Robert C. Martin"},
    {"text": "Java is to JavaScript what car is to carpet.", "author": "Chris Heilmann"},
    {"text": "Software and cathedrals are much the same — first we build them, then we pray.", "author": "Sam Redwine"},
    {"text": "In theory, there is no difference between theory and practice. But, in practice, there is.", "author": "Jan L. A. van de Snepscheut"},
    {"text": "Measuring programming progress by lines of code is like measuring aircraft building progress by weight.", "author": "Bill Gates"},
    {"text": "A language that doesn't affect the way you think about programming is not worth knowing.", "author": "Alan Perlis"},
]

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _day_count() -> int:
    """Count the total number of daily-log files (YYYY-MM-DD.md) in log/."""
    if not LOG_DIR.exists():
        return 0
    return sum(1 for f in LOG_DIR.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"))


def _streak_length(ref_date: datetime | None = None) -> int:
    """
    Walk backwards from the given date counting consecutive days that have a log file.
    """
    from datetime import timedelta

    current_date = (ref_date or datetime.now(timezone.utc)).date()
    streak = 0
    day = current_date
    while True:
        if (LOG_DIR / f"{day.isoformat()}.md").exists():
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return max(streak, 1)


def _generate_daily_log(now: datetime, quote: dict[str, str] | None = None) -> tuple[Path, int]:
    """Create log/YYYY-MM-DD.md with a timestamped entry and return (path, day_number)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    date_str = now.strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{date_str}.md"
    file_existed = log_file.exists()

    if quote is None:
        quote = random.choice(QUOTES)

    current_count = _day_count()
    day_number = current_count if file_existed else current_count + 1

    entry = textwrap.dedent(f"""\
        # 📅 Daily Log — {date_str}

        | Field | Value |
        |-------|-------|
        | **Day #** | {day_number} |
        | **Timestamp (UTC)** | {now.strftime("%Y-%m-%d %H:%M:%S")} |
        | **Weekday** | {now.strftime("%A")} |

        ## 💡 Quote of the Day

        > *"{quote['text']}"*
        > — {quote['author']}

        ## 📝 Changelog

        - Auto-generated streak entry for day **{day_number}**.
        - Workflow trigger: `{os.environ.get("GITHUB_EVENT_NAME", "local")}`

        ---
        *Generated by [streak-bot](https://github.com/features/actions)*
    """)

    # Append if file already exists (e.g., manual re-run on the same day)
    mode = "a" if file_existed else "w"
    if mode == "a":
        entry = "\n\n---\n\n" + f"## 🔄 Re-run at {now.strftime('%H:%M:%S')} UTC\n\n" + entry

    log_file.write_text(entry if mode == "w" else log_file.read_text(encoding="utf-8") + entry, encoding="utf-8")
    print(f"✅ Wrote daily log → {log_file.relative_to(REPO_ROOT)}")
    return log_file, day_number


def _update_readme_stats(now: datetime, day_number: int) -> None:
    """
    Insert or update a <!-- STREAK-STATS --> block in README.md.
    If no README exists, create a minimal one.
    """
    streak = _streak_length(now)
    stats_block = textwrap.dedent(f"""\
        <!-- STREAK-STATS:START -->
        ## 📊 Streak Stats

        | Metric | Value |
        |--------|-------|
        | 🔥 Current streak | **{streak} day{"s" if streak != 1 else ""}** |
        | 📅 Total entries | **{day_number}** |
        | 🕐 Last updated | {now.strftime("%Y-%m-%d %H:%M UTC")} |
        <!-- STREAK-STATS:END -->""")

    if README.exists():
        content = README.read_text(encoding="utf-8")
        pattern = r"<!-- STREAK-STATS:START -->.*?<!-- STREAK-STATS:END -->"
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, stats_block, content, flags=re.DOTALL)
        else:
            content += "\n\n" + stats_block + "\n"
    else:
        content = textwrap.dedent(f"""\
            # 🔥 GitHub Streak Bot

            Automated daily commits to maintain a contribution streak.

            {stats_block}
        """)

    README.write_text(content, encoding="utf-8")
    print(f"✅ Updated README stats block")


def _update_commit_history(now: datetime, day_number: int, quote: dict[str, str]) -> None:
    """
    Append today's commit record to log/commit_history.json.
    The file stores a JSON array so it's easy to parse and query.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing history or start fresh
    if COMMIT_HISTORY.exists():
        try:
            history = json.loads(COMMIT_HISTORY.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            history = []
    else:
        history = []

    record = {
        "id": len(history) + 1,
        "date": now.strftime("%Y-%m-%d"),
        "timestamp_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "weekday": now.strftime("%A"),
        "day_number": day_number,
        "streak": _streak_length(now),
        "quote": quote["text"],
        "quote_author": quote["author"],
        "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", None),
    }

    history.append(record)
    COMMIT_HISTORY.write_text(
        json.dumps(history, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"✅ Updated commit history → {len(history)} total entries")


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    now = datetime.now(timezone.utc)
    print(f"🕐 Current UTC time: {now.isoformat()}")

    # Pick today's quote once so the log and history record stay in sync
    quote = random.choice(QUOTES)

    _, day_number = _generate_daily_log(now, quote)
    _update_readme_stats(now, day_number)
    _update_commit_history(now, day_number, quote)

    print(f"🎯 Day #{day_number} content generated successfully.")


if __name__ == "__main__":
    main()
