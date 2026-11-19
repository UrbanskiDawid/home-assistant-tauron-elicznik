# Tauron Energy for Home Assistant

[![GitHub Latest Release](https://img.shields.io/github/v/release/UrbanskiDawid/home-assistant-tauron-elicznik)](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/releases)
[![Test](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/actions/workflows/test.yaml/badge.svg)](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/actions/workflows/test.yaml)
[![Validate HACS](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/actions/workflows/hacs.yaml/badge.svg)](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/actions/workflows/hacs.yaml)
[![Validate with hassfest](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/actions/workflows/hassfest.yaml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/github/license/UrbanskiDawid/home-assistant-tauron-elicznik)](LICENSE)

A minimal custom integration that imports **hourly grid consumption** from
[Tauron eLicznik](https://elicznik.tauron-dystrybucja.pl/) into Home Assistant, so you can
use it in the **Energy dashboard**.

It does one thing: logs in to eLicznik, downloads the hourly consumption CSV and stores it as a
long-term statistic. There are no sensors, no solar/export, no tariff zones.

![Energy dashboard with Tauron hourly consumption](docs/energy_dashboard.jpg)

**[Installation](#installation)** ([INSTALL.md](INSTALL.md)) · **[Set up](#set-up)** · **[Related projects](#related-projects)** · **[License](LICENSE)**

## Installation

> 📄 Also available as a separate page: [INSTALL.md](INSTALL.md)

### Using [HACS](https://hacs.xyz/) (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UrbanskiDawid&repository=home-assistant-tauron-elicznik&category=integration)

Click the button above, or add it by hand:

* In HACS open the ⋮ menu → _Custom repositories_
* Add `https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik` with type _Integration_
* Search for "Tauron Energy" and click _Download_
* Restart Home Assistant

HACS not installed yet? Follow the [HACS download guide](https://hacs.xyz/docs/use/download/download/) first.

### Manual

Download [*tauron_energy.zip*](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/releases/latest/download/tauron_energy.zip) and extract it to `config/custom_components/tauron_energy`:
```bash
mkdir -p /config/custom_components/tauron_energy
cd /config/custom_components/tauron_energy
wget https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/releases/latest/download/tauron_energy.zip
unzip tauron_energy.zip
rm tauron_energy.zip
```

Then restart Home Assistant.

## Set up

1. Settings → Devices & services → Add integration → **Tauron Energy**.

   ![Tauron Energy integration](docs/integration.jpg)

2. Enter your eLicznik e-mail and password. Leave *Metering point ID* empty unless your account
   has several metering points.

   ![Configuration form](docs/config_flow.jpg)

3. The first import loads the last 30 days (takes a few seconds).
4. Settings → Dashboards → Energy → *Electricity grid* → *Add consumption* → pick
   **`<your account> consumption`** (statistic `tauron_energy:<account>_consumption`).

   ![Energy configuration](docs/energy_config.jpg)

You can check the imported data under Developer tools → Statistics.

### Optional: dashboard card

To show hourly usage on any dashboard, add a *Statistics graph* card:

```yaml
type: statistics-graph
title: Zużycie prądu (Tauron)
entities:
  - tauron_energy:<account>_consumption
stat_types:
  - change
chart_type: bar
period: hour
days_to_show: 3
```

![Dashboard card](docs/dashboard_card.png)

The integration icon (`brand/icon.png`) is shown by Home Assistant 2026.3 or newer.

## Related projects

**Tauron eLicznik in Home Assistant**
- [PiotrMachowski/Home-Assistant-custom-components-Tauron-AMIplus](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Tauron-AMIplus) – full-featured eLicznik integration (sensors, generation, tariffs, statistics). Use it if you need more than consumption.
- [staszekj/eltrue-tauron-elicznik-ha](https://github.com/staszekj/eltrue-tauron-elicznik-ha) – another eLicznik meter readings integration.

**Other Tauron integrations for Home Assistant**
- [direk/tauronizer](https://github.com/direk/tauronizer) – Tauron tariff comparison.
- [kubukoz/ha-tauron-g13](https://github.com/kubukoz/ha-tauron-g13) – current G13 tariff zone.
- [elmystico/ha-pl-energy-tariff](https://github.com/elmystico/ha-pl-energy-tariff) – hourly gross electricity prices for Polish G tariffs.
- [twiktorowicz/Pstryk-OSD-Compare](https://github.com/twiktorowicz/Pstryk-OSD-Compare) – compare Pstryk meter data with distribution operator statistics.
- [l4red0/tauron_awarie](https://github.com/l4red0/tauron_awarie), [Eales/tauron-dystrybucja](https://github.com/Eales/tauron-dystrybucja) – planned and unplanned power outages.

**Libraries and APIs**
- [mlesniew/elicznik](https://github.com/mlesniew/elicznik) – Python module and CLI for eLicznik readings.
- [DamianSowinski/tauron-api](https://github.com/DamianSowinski/tauron-api) – PHP JSON API over eLicznik (2021, uses the old login flow).

## License

[MIT](LICENSE)

Unofficial; not affiliated with TAURON. Uses the same endpoints as the eLicznik website.
