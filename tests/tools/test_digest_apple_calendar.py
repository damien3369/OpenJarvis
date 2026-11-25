"""Morning digest must surface Apple Calendar events by start date."""

from datetime import datetime, timedelta

from openjarvis.connectors._stubs import Document
from openjarvis.tools.digest_collect import (
    _CONNECTOR_TO_SECTION,
    _format_apple_calendar,
    _upcoming_apple_events,
)


def _ev(title, start, all_day=False, modified=None, location=""):
    return Document(
        doc_id=f"apple_calendar:{title}",
        source="apple_calendar",
        doc_type="calendar_event",
        content="",
        title=title,
        author="Perso",
        # The connector stamps last-modified time, often weeks ago.
        timestamp=modified or datetime(2020, 1, 1),
        metadata={"start": start.isoformat(), "all_day": all_day, "location": location},
    )


def test_apple_calendar_is_in_calendar_section():
    assert _CONNECTOR_TO_SECTION["apple_calendar"] == "CALENDAR"


def test_old_modified_events_today_are_kept_and_sorted():
    now = datetime(2026, 11, 25, 7, 0)
    docs = [
        _ev("Dentiste", now.replace(hour=15)),
        _ev("Réunion", now.replace(hour=9)),
        _ev("Hier", now - timedelta(days=1)),
        _ev("Dans 10 jours", now + timedelta(days=10)),
    ]
    kept = [d.title for d in _upcoming_apple_events(docs, now)]
    assert kept == ["Réunion", "Dentiste"]


def test_format_with_time_and_location():
    line = _format_apple_calendar(
        _ev("Dentiste", datetime(2026, 11, 25, 15, 30), location="Lyon")
    )
    assert "15:30" in line and "Dentiste" in line and "Lyon" in line


def test_format_all_day():
    line = _format_apple_calendar(_ev("Congés", datetime(2026, 11, 25), all_day=True))
    assert "all day" in line
