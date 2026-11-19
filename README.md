# Tauron Energy for Home Assistant

A minimal custom integration that imports **hourly grid consumption** from
[Tauron eLicznik](https://elicznik.tauron-dystrybucja.pl/) into Home Assistant, so you can
use it in the **Energy dashboard**.

It does one thing: logs in to eLicznik, downloads the hourly consumption CSV and stores it as a
long-term statistic. There are no sensors, no solar/export, no tariff zones.

## How fresh is the data?

Tauron has no live data. Hourly values show up on eLicznik in batches, roughly **~8 hours late**
(on 2026-11-19 at 14:00 the data covered up to 06:00 the same day), sometimes a day or more.
The integration checks every hour and re-imports the last 3 days each time, so late and
corrected hours fill in automatically.

## Install

**HACS:** HACS → ⋮ → Custom repositories → add `https://github.com/UrbanskiDawid/tauron-elicznik` as type *Integration* →
install *Tauron Energy* → restart Home Assistant.

**Manual:** copy `custom_components/tauron_energy` to `/config/custom_components/` and restart.

## Set up

1. Settings → Devices & services → Add integration → **Tauron Energy**.
2. Enter your eLicznik e-mail and password. Leave *Metering point ID* empty unless your account
   has several metering points.
3. The first import loads the last 30 days (takes a few seconds).
4. Settings → Dashboards → Energy → *Electricity grid* → *Add consumption* → pick
   **`<your account> consumption`** (statistic `tauron_energy:<account>_consumption`).

You can check the imported data under Developer tools → Statistics.

## Troubleshooting

```yaml
logger:
  logs:
    custom_components.tauron_energy: debug
```

- *Invalid username or password*: check you can log in at elicznik.tauron-dystrybucja.pl.
- *Too many login attempts*: Tauron temporarily blocks logins; the integration retries hourly.

## Development

```
python3 -m venv .venv && .venv/bin/pip install pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```

Unofficial; not affiliated with TAURON. Uses the same endpoints as the eLicznik website.
