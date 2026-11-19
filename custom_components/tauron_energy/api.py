"""Minimal client for Tauron eLicznik hourly consumption data.

Kept free of Home Assistant imports so the parser can be unit tested on its own.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .const import DATA_URL, LOGIN_URL, SELECT_METER_URL, SERVICE_URL, TIME_ZONE

_LOGGER = logging.getLogger(__name__)

_LOGIN_FORM_RE = re.compile(r'<form[^>]+id="kc-form-login"[^>]+action="([^"]+)"')
_RATE_LIMITED = "Przekroczono maksymalną liczbę logowań."


class TauronError(Exception):
    """Communication with Tauron failed."""


class TauronAuthError(TauronError):
    """Tauron rejected the credentials."""


class TauronClient:
    """Logs in to eLicznik and downloads hourly consumption."""

    def __init__(self, session, username: str, password: str, meter_id: str | None = None):
        # `session` is an aiohttp.ClientSession with its own cookie jar.
        self._session = session
        self._username = username
        self._password = password
        self._meter_id = meter_id or None

    async def login(self) -> None:
        """Log in through Tauron's Keycloak form and select the meter."""
        async with self._session.get(LOGIN_URL, params={"service": SERVICE_URL}) as resp:
            page = await resp.text()
        match = _LOGIN_FORM_RE.search(page)
        if match is None:
            raise TauronError("Tauron login form not found")

        async with self._session.post(
            html.unescape(match.group(1)),
            data={"username": self._username, "password": self._password, "credentialId": ""},
        ) as resp:
            page = await resp.text()
        if _RATE_LIMITED in page:
            raise TauronError("Too many login attempts, Tauron temporarily blocked logins")
        if 'id="kc-form-login"' in page:
            raise TauronAuthError("Invalid Tauron username or password")

        if self._meter_id:
            async with self._session.post(
                SELECT_METER_URL, data={"site[client]": self._meter_id}
            ) as resp:
                resp.raise_for_status()
        _LOGGER.debug("Logged in to eLicznik")

    async def get_hourly(self, start: date, end: date) -> list[tuple[datetime, float]]:
        """Return (hour start in UTC, kWh) for all published hours in [start, end]."""
        text = await self._download_csv(start, end)
        if not _is_csv(text):
            # Session expired (we got an HTML page) – log in again and retry once.
            await self.login()
            text = await self._download_csv(start, end)
            if not _is_csv(text):
                raise TauronError("Unexpected response from eLicznik data export")
        return parse_csv(text)

    async def _download_csv(self, start: date, end: date) -> str:
        params = {
            "form[from]": start.strftime("%d.%m.%Y"),
            "form[to]": end.strftime("%d.%m.%Y"),
            "form[type]": "godzin",
            "form[energy][consum]": "1",
            "form[fileType]": "CSV",
        }
        async with self._session.get(DATA_URL, params=params) as resp:
            return (await resp.read()).decode("utf-8", errors="replace")


def _is_csv(text: str) -> bool:
    return text.lstrip("﻿ \r\n").startswith("Data")


def parse_csv(text: str) -> list[tuple[datetime, float]]:
    """Parse the eLicznik hourly CSV export.

    Rows look like ``2026-11-19 1:00;T3;0,171;pobór [kWh]; licznik;`` where the
    time is the *end* of the hour, numbered 1..24 (23/25 on DST days). The hour
    start is computed as UTC midnight of that local day plus (hour - 1) hours,
    so DST days need no special casing. A repeated label is treated as the next
    hour, in case the export repeats the label for the extra autumn hour.
    """
    tz = ZoneInfo(TIME_ZONE)
    result: dict[datetime, float] = {}
    previous: datetime | None = None
    for line in text.splitlines()[1:]:
        cols = [c.strip() for c in line.split(";")]
        if len(cols) < 3 or not cols[0] or not cols[2]:
            continue
        day_str, _, time_str = cols[0].partition(" ")
        day = date.fromisoformat(day_str)
        hour = int(time_str.split(":")[0])
        midnight = datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc)
        start = midnight + timedelta(hours=hour - 1)
        if previous is not None and start <= previous:  # rows are chronological
            start = previous + timedelta(hours=1)
        result[start] = float(cols[2].replace(",", "."))
        previous = start
    return sorted(result.items())
