"""Compatibility entry point for the installed ``email-assist`` command."""

from email_assist.cli import main


if __name__ == "__main__":
    raise SystemExit(main())