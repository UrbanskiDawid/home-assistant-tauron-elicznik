"""Tauron Energy: imports Tauron eLicznik hourly consumption as HA statistics."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta

import aiohttp
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    statistics_during_period,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from .api import TauronAuthError, TauronClient, TauronError
from .const import (
    BACKFILL_DAYS,
    CONF_METER_ID,
    DOMAIN,
    REFRESH_DAYS,
    TIME_ZONE,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def statistic_id(entry: ConfigEntry) -> str:
    """Return e.g. ``tauron_energy:jan_example_com_consumption``."""
    key = entry.data.get(CONF_METER_ID) or entry.data[CONF_USERNAME]
    return f"{DOMAIN}:{slugify(key)}_consumption"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Own session: Tauron's login cookies must not leak into HA's shared session.
    session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
    entry.async_on_unload(session.close)
    client = TauronClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_METER_ID),
    )
    try:
        await client.login()
    except TauronAuthError as err:
        await session.close()
        raise ConfigEntryError(str(err)) from err
    except (TauronError, aiohttp.ClientError) as err:
        await session.close()
        raise ConfigEntryNotReady(str(err)) from err

    lock = asyncio.Lock()

    async def _update(_now: datetime | None = None) -> None:
        if lock.locked():
            return
        async with lock:
            try:
                await _import_statistics(hass, client, statistic_id(entry), entry.title)
            except (TauronError, aiohttp.ClientError) as err:
                _LOGGER.warning("Tauron import failed, will retry: %s", err)

    entry.async_on_unload(async_track_time_interval(hass, _update, UPDATE_INTERVAL))
    entry.async_create_background_task(hass, _update(), f"{DOMAIN}_initial_import")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True


async def _import_statistics(
    hass: HomeAssistant, client: TauronClient, stat_id: str, name: str
) -> None:
    """Re-import the last few days (or backfill) as hourly external statistics."""
    recorder = get_instance(hass)
    tz = dt_util.get_time_zone(TIME_ZONE)
    today = dt_util.now(tz).date()

    last = await recorder.async_add_executor_job(
        get_last_statistics, hass, 1, stat_id, True, {"sum"}
    )
    if last.get(stat_id):
        last_start = dt_util.utc_from_timestamp(last[stat_id][0]["start"])
        from_day = min(last_start.astimezone(tz).date(), today - timedelta(days=REFRESH_DAYS))
    else:
        from_day = today - timedelta(days=BACKFILL_DAYS)
    window_start = dt_util.as_utc(datetime.combine(from_day, time.min, tzinfo=tz))

    # Running total just before the window, so re-imported sums stay continuous.
    base = 0.0
    if last.get(stat_id):
        before = await recorder.async_add_executor_job(
            statistics_during_period,
            hass,
            window_start - timedelta(days=7),
            window_start,
            {stat_id},
            "hour",
            None,
            {"sum"},
        )
        if before.get(stat_id):
            base = before[stat_id][-1]["sum"] or 0.0

    readings = await client.get_hourly(from_day, today)

    total = base
    rows = []
    for start, kwh in readings:
        if start < window_start:
            continue
        total += kwh
        rows.append({"start": start, "state": kwh, "sum": round(total, 3)})

    if not rows:
        _LOGGER.debug("No Tauron data for %s..%s", from_day, today)
        return

    metadata = {
        "source": DOMAIN,
        "statistic_id": stat_id,
        "name": f"{name} consumption",
        "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
        "unit_class": "energy",
        "has_mean": False,
        "mean_type": StatisticMeanType.NONE,
        "has_sum": True,
    }
    async_add_external_statistics(hass, metadata, rows)
    _LOGGER.debug("Imported %d hours into %s, last hour %s", len(rows), stat_id, rows[-1]["start"])
