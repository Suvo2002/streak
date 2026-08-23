# 🔥 GitHub Streak Bot

Automated daily commits to maintain a GitHub contribution streak — powered entirely by GitHub Actions.

---

## How It Works

```
┌──────────────────────┐     ┌───────────────────────┐     ┌────────────────────┐
│  GitHub Actions Cron │────▶│  generate_content.py  │────▶│  git commit & push │
│  (09:17 UTC daily)   │     │  • daily log .md      │     │  • bot identity    │
│  + workflow_dispatch │     │  • README stats block  │     │  • descriptive msg │
└──────────────────────┘     └───────────────────────┘     └────────────────────┘
                                                                    │
                                                           ┌────────▼────────┐
                                                           │  On failure:    │
                                                           │  auto-create    │
                                                           │  GitHub Issue   │
                                                           └─────────────────┘
```

Each day the workflow:

1. **Generates content** — a `log/YYYY-MM-DD.md` file with a dev quote, day counter, and timestamp.
2. **Updates the README** — refreshes the streak stats table (current streak, total entries, last updated).
3. **Commits & pushes** — using a dedicated bot identity (`streak-bot`).
4. **Logs the outcome** — appends to `log/status.json` (JSONL) for auditability.
5. **Alerts on failure** — auto-creates a GitHub Issue with a link to the failed run.

---

## Quick Setup

### 1. Create your repository

```bash
# Option A: Fresh repo
mkdir my-streak && cd my-streak
git init
cp -r /path/to/github-streak-bot/.github .
cp -r /path/to/github-streak-bot/scripts .
cp /path/to/github-streak-bot/README.md .
git add -A && git commit -m "🚀 initial streak bot setup"
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

```bash
# Option B: Add to an existing repo
cp -r /path/to/github-streak-bot/.github/workflows/daily-commit.yml .github/workflows/
cp -r /path/to/github-streak-bot/scripts .
git add -A && git commit -m "🤖 add streak bot workflow"
git push
```

### 2. Enable Actions permissions

Go to **Settings → Actions → General** in your repository:

- Under **Workflow permissions**, select **Read and write permissions**.
- Check **Allow GitHub Actions to create and approve pull requests** (needed for issue creation).

### 3. (Optional) Add labels

The failure notification creates issues with the labels `streak-bot` and `bug`. Create the `streak-bot` label in **Issues → Labels** to keep things organized.

### 4. Test it

Trigger a manual run from the **Actions** tab:

1. Select **Daily Streak Commit**.
2. Click **Run workflow**.
3. Optionally set **Dry Run** to `true` for a no-push test.

---

## Customization

### Change the schedule

Edit the cron expression in `.github/workflows/daily-commit.yml`:

```yaml
schedule:
  - cron: "17 9 * * *"   # ← change this
```

> [!TIP]
> Use [crontab.guru](https://crontab.guru/) to build your expression. GitHub Actions cron uses UTC and has ±5–20 min natural jitter.

### Change the target branch

Set the `TARGET_BRANCH` env var in the workflow:

```yaml
env:
  TARGET_BRANCH: "streak"   # push to a dedicated branch instead of main
```

### Change the bot identity

```yaml
env:
  BOT_NAME: "my-bot"
  BOT_EMAIL: "my-bot@users.noreply.github.com"
```

### Add your own quotes

Edit the `QUOTES` list in `scripts/generate_content.py`:

```python
QUOTES = [
    {"text": "Your quote here.", "author": "You"},
    # ...
]
```

### Change what gets committed

The `generate_content.py` script is the single source of truth for generated content. Modify `_generate_daily_log()` and `_update_readme_stats()` to change the output format, or add entirely new generators.

---

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── daily-commit.yml    # GitHub Actions workflow
├── scripts/
│   └── generate_content.py     # Content generator (Python, stdlib only)
├── log/
│   ├── 2026-08-02.md           # Daily log entries (auto-created)
│   ├── 2026-08-03.md
│   └── status.json             # JSONL audit log of every run
└── README.md                   # This file (stats block auto-updated)
```

---

## Security

| Concern | Approach |
|---------|----------|
| **Credentials** | Uses the built-in `GITHUB_TOKEN` — no PAT or secrets needed |
| **Permissions** | Scoped to `contents: write` and `issues: write` only |
| **No external deps** | Python script uses stdlib only — no `pip install`, no supply-chain risk |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Workflow never runs | Check that Actions are enabled and the file is on the default branch |
| Push rejected (403) | Go to **Settings → Actions → General → Workflow permissions** → enable **Read and write** |
| Issue creation fails | Add `issues: write` to workflow permissions (already included) |
| "Nothing to commit" | The script already ran today — this is normal and the job exits cleanly |
| Streak shows on profile but not on graph | Ensure commits are on the **default branch** and the committer email is [linked to your GitHub account](https://github.com/settings/emails) |

---

## FAQ

**Will this count toward my contribution graph?**
Yes — as long as the commits are pushed to the **default branch** of a non-fork repository. The bot uses a noreply email; if you want the commits attributed to *your* profile, change `BOT_EMAIL` to your GitHub noreply address (`ID+username@users.noreply.github.com`).

**Is this against GitHub ToS?**
GitHub's Terms don't prohibit automated commits to your own repositories. This creates real, meaningful content (logs, stats) — not empty commits.

**What if the cron misses a day?**
GitHub Actions cron is best-effort and can occasionally skip. If reliability is critical, add a second cron time as a fallback or set up an external monitor.

---

<!-- STREAK-STATS:START -->
## 📊 Streak Stats

| Metric | Value |
|--------|-------|
| 🔥 Current streak | **22 days** |
| 📅 Total entries | **22** |
| 🕐 Last updated | 2026-08-23 08:46 UTC |
<!-- STREAK-STATS:END -->
