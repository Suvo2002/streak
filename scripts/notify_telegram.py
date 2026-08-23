#!/usr/bin/env python3
"""
notify_telegram.py — Sends daily streak notifications to a Telegram chat/bot.
Uses only the Python standard library (urllib.request).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on all environments
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parent.parent))
LOG_DIR = REPO_ROOT / "log"
COMMIT_HISTORY = LOG_DIR / "commit_history.json"


def format_message() -> str:
    """Format the Telegram notification message from latest commit history."""
    if COMMIT_HISTORY.exists():
        try:
            history = json.loads(COMMIT_HISTORY.read_text(encoding="utf-8"))
            if history:
                latest = history[-1]
                day_num = latest.get("day_number", 1)
                streak = latest.get("streak", 1)
                date_str = latest.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                weekday = latest.get("weekday", "")
                quote_text = latest.get("quote", "")
                quote_author = latest.get("quote_author", "")

                msg = (
                    f"🔥 <b>Daily GitHub Streak Update</b>\n\n"
                    f"📅 <b>Date:</b> {date_str} ({weekday})\n"
                    f"🎯 <b>Day #:</b> {day_num}\n"
                    f"⚡ <b>Current Streak:</b> {streak} day{'s' if streak != 1 else ''}\n"
                    f"✅ <b>Status:</b> Commit pushed successfully\n\n"
                    f"💡 <i>\"{quote_text}\"</i>\n"
                    f"   — <b>{quote_author}</b>\n\n"
                    f"🔗 <a href=\"https://github.com/Suvo2002/streak\">View Repository</a>"
                )
                return msg
        except Exception as e:
            print(f"Notice: could not parse commit_history.json: {e}")

    now = datetime.now(timezone.utc)
    return (
        f"🔥 <b>Daily GitHub Streak Update</b>\n\n"
        f"📅 <b>Date:</b> {now.strftime('%Y-%m-%d (%A)')}\n"
        f"✅ <b>Status:</b> Commit pushed successfully\n\n"
        f"🔗 <a href=\"https://github.com/Suvo2002/streak\">View Repository</a>"
    )


def send_telegram_notification() -> bool:
    """Send message via Telegram Bot API."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        print("ℹ️ Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not provided.")
        return True

    text = format_message()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status == 200:
                print("✅ Telegram notification sent successfully!")
                return True
            print(f"⚠️ Telegram API returned HTTP status {response.status}")
            return False
    except Exception as e:
        print(f"⚠️ Failed to send Telegram notification: {e}")
        return False


if __name__ == "__main__":
    send_telegram_notification()
