"""Import logic against a real HA recorder (pytest-homeassistant-custom-component)."""

from datetime import datetime, timedelta, timezone

from homeassistant.components.recorder.statistics import statistics_during_period
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.tauron_energy import _import_statistics

STAT = "tauron_energy:test_consumption"


class FakeClient:
    def __init__(self, readings):
        self.readings = readings  # {utc hour start: kWh}
        self.calls = []

    async def get_hourly(self, start, end):
        self.calls.append((start, end))
        return sorted(self.readings.items())


def hours(start, end):
    t = start
    while t < end:
        yield t
        t += timedelta(hours=1)


async def _rows(hass):
    stats = await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        None,
        {STAT},
        "hour",
        None,
        {"state", "sum"},
    )
    return stats.get(STAT, [])


async def test_backfill_then_refresh_keeps_sum_continuous(recorder_mock, hass, freezer):
    freezer.move_to("2026-11-19 13:00:00+00:00")
    tauron_end = datetime(2026, 11, 19, 5, tzinfo=timezone.utc)  # ~8h lag
    readings = {t: 1.0 for t in hours(datetime(2026, 10, 1, tzinfo=timezone.utc), tauron_end)}
    client = FakeClient(readings)

    await _import_statistics(hass, client, STAT, "Test")
    await async_wait_recording_done(hass)
    rows = await _rows(hass)
    # Backfill starts at local midnight 30 days ago (2026-10-20 00:00 CEST = 10-19 22:00 UTC).
    assert client.calls[-1] == (datetime(2026, 10, 20).date(), datetime(2026, 11, 19).date())
    assert rows[0]["start"] == datetime(2026, 10, 19, 22, tzinfo=timezone.utc).timestamp()
    assert rows[-1]["sum"] == len(rows)
    first_total = rows[-1]["sum"]

    # Later: Tauron publishes more hours today and corrects one hour from yesterday.
    freezer.move_to("2026-11-19 20:00:00+00:00")
    corrected = datetime(2026, 11, 18, 10, tzinfo=timezone.utc)
    readings[corrected] = 3.0
    for t in hours(tauron_end, datetime(2026, 11, 19, 12, tzinfo=timezone.utc)):
        readings[t] = 1.0

    await _import_statistics(hass, client, STAT, "Test")
    await async_wait_recording_done(hass)
    rows = await _rows(hass)

    # Second run only re-reads the refresh window, not the whole backfill.
    assert client.calls[-1] == (datetime(2026, 11, 16).date(), datetime(2026, 11, 19).date())
    assert rows[-1]["sum"] == first_total + 7 + 2  # 7 new hours + corrected hour (+2)
    previous = 0.0
    for row in rows:
        assert abs(row["sum"] - previous - row["state"]) < 1e-6
        previous = row["sum"]
