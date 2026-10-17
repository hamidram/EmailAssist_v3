"""Compatibility exports; application code lives in :mod:`email_assist.parser`."""

from email_assist.parser import filter_yesterbox, load_emails, parse_received_date

__all__ = ["filter_yesterbox", "load_emails", "parse_received_date"]