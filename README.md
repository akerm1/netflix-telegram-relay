# Netflix Telegram Email Relay Bot

Automated relay that monitors a Netflix account email inbox for verification codes, household update links, and password reset links, then forwards them to Telegram with secure routing.

## Features

- **Category A — OTP/Access Codes**: 4-digit verification codes forwarded to the Telegram group with HTML formatting.
- **Category B — Household Update Links**: `netflix.com/account/travel` / `netflix.com/verify` links forwarded to the group with an inline open button.
- **Category C — Password Reset Links (SENSITIVE)**: Routed **only** to the admin via private message, never to the shared group.
- IMAP polling with exponential-backoff reconnection.
- Processed emails are marked as read to prevent duplicate dispatch.
- Access control on `/start`, `/status`, `/check` — only the admin or group members may use them.
- All sensitive tokens/passwords masked in logs.

## Setup (easy way)

1. **Double-click `start.bat`** — it runs the setup wizard automatically on first use.
   - Or run `python setup.py` yourself, then `python bot.py`.

The wizard asks 7 questions:

1. **Bot token** — create a bot with [@BotFather](https://t.me/BotFather), copy the token (`123456:AA...`).
2. **Group ID** — add [@RawDataBot](https://t.me/RawDataBot) to your Telegram group; it prints `chat.id` (starts with `-100`).
3. **Admin ID** — message [@userinfobot](https://t.me/userinfobot) to get your user id.
4. **IMAP server** — press Enter for Gmail (`imap.gmail.com`).
5. **Email address** — the mailbox that receives Netflix emails.
6. **App Password** — for Gmail: enable 2-Step Verification, then create one at https://myaccount.google.com/apppasswords (16 chars).
7. **Poll interval** — press Enter for the default (10 seconds).

Your answers are saved to `.env` and you only ever do this once.

## Setup (manual way)

1. Copy `.env.example` to `.env` and fill in your values.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run:
   ```
   python bot.py
   ```

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather API token |
| `TELEGRAM_GROUP_ID` | Target group chat ID (negative number) |
| `ADMIN_TELEGRAM_ID` | Admin user ID for sensitive alerts |
| `IMAP_SERVER` | IMAP host (e.g. `imap.gmail.com`) |
| `EMAIL_ACCOUNT` | Netflix account email address |
| `EMAIL_APP_PASSWORD` | Dedicated app password for the mailbox |
| `POLL_INTERVAL_SECONDS` | Polling frequency (default: 10) |
| `DISPATCH_EXISTING_ON_START` | `false` (default): on first run, emails already unread **before** the bot started are skipped (not sent), so old backlog doesn't flood the group. Set `true` to relay everything. |
| `LOOKBACK_MINUTES` | Only relay emails newer than this many minutes (default: `15`). Used by `run_once.py`. |

## 24/7 Deployment (GitHub Actions)

The bot runs as a scheduled GitHub Actions workflow (free forever on a public
repo — no server, no card, PC can stay off):

1. Push this repository to GitHub and make it **public** (public repos get
   unlimited Actions minutes; private repos are capped at 2000/min month).
2. Add repository secrets (`gh secret set NAME --body "value"`):
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_GROUP_ID`, `ADMIN_TELEGRAM_ID`,
   `IMAP_SERVER`, `EMAIL_ACCOUNT`, `EMAIL_APP_PASSWORD`.
3. `.github/workflows/relay.yml` runs `python run_once.py` every 5 minutes —
   a single IMAP cycle over only the newest unread emails, limited by
   `LOOKBACK_MINUTES` so old backlog is never touched.

Latency is at most 5 minutes. For 10-second latency run `python bot.py`
locally instead — do not run both at the same time if you want to avoid the
rare case of a duplicate delivery (both poll the same mailbox).

## Architecture

```
bot.py               Main entry point & orchestration (long-running, 10s poll)
run_once.py          One-shot relay cycle for scheduled CI runs
config.py            Environment configuration & validation
logger.py            Logging with sensitive-data masking
parser.py            Email parsing & category detection (regex)
email_monitor.py     IMAP polling loop with reconnect/backoff
telegram_handler.py  aiogram v3 bot with routing & access control
utils.py             Masking & backoff helpers
```

## Security Notes

- Category C (password resets) is **never** sent to the shared group.
- App passwords and bot tokens are never logged (masked by `MaskSensitiveFilter`).
- Emails are marked `\Seen` after fetch to prevent reprocessing.
