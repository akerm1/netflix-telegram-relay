"""Interactive one-time setup: answers a few questions and writes .env."""

import sys

ENV_PATH = ".env"
EXAMPLE_PATH = ".env.example"


def ask(label, default=None, secret=False):
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"{label}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            sys.exit(1)
        if value:
            return value
        if default is not None:
            return default
        print("  This value is required.")


def main():
    print("=" * 52)
    print(" Netflix Telegram Relay - Setup Wizard")
    print("=" * 52)
    print("(Press Enter to accept the value in [brackets])\n")

    bot_token = ask("1) Bot token from @BotFather")
    if ":" not in bot_token:
        print("  WARN: a BotFather token looks like 123456789:AA... (contains a colon)")
    group_id = ask("2) Telegram GROUP id (starts with -100)")
    admin_id = ask("3) Your ADMIN Telegram id (number)")
    imap_server = ask("4) IMAP server", default="imap.gmail.com")
    email = ask("5) Email address that receives Netflix mails")
    app_password = ask("6) Email App Password (16 chars for Gmail)")
    app_password = app_password.replace(" ", "")  # Gmail shows 16 chars in groups
    poll = ask("7) Poll interval seconds", default="10")

    lines = [
        f"TELEGRAM_BOT_TOKEN={bot_token}",
        f"TELEGRAM_GROUP_ID={group_id}",
        f"ADMIN_TELEGRAM_ID={admin_id}",
        f"IMAP_SERVER={imap_server}",
        f"EMAIL_ACCOUNT={email}",
        f"EMAIL_APP_PASSWORD={app_password}",
        f"POLL_INTERVAL_SECONDS={poll}",
    ]

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nSaved {ENV_PATH}.")
    print("Now run:  python bot.py   (or double-click start.bat)")
    print("\nChecks:")
    for name, value in [
        ("group id", group_id),
        ("admin id", admin_id),
        ("poll seconds", poll),
    ]:
        try:
            int(value)
            print(f"  OK   {name} is a number")
        except ValueError:
            print(f"  WARN {name} is not a number: {value} (bot may fail)")


if __name__ == "__main__":
    main()
