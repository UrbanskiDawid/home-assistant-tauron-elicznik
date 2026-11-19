# Installation

← Back to [README](README.md)


## Using [HACS](https://hacs.xyz/) (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UrbanskiDawid&repository=home-assistant-tauron-elicznik&category=integration)

Click the button above, or add it by hand:

* In HACS open the ⋮ menu → _Custom repositories_
* Add `https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik` with type _Integration_
* Search for "Tauron Energy" and click _Download_
* Restart Home Assistant

HACS not installed yet? Follow the [HACS download guide](https://hacs.xyz/docs/use/download/download/) first.

## Manual

Download [*tauron_energy.zip*](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/releases/latest/download/tauron_energy.zip) and extract it to `config/custom_components/tauron_energy`:
```bash
mkdir -p /config/custom_components/tauron_energy
cd /config/custom_components/tauron_energy
wget https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik/releases/latest/download/tauron_energy.zip
unzip tauron_energy.zip
rm tauron_energy.zip
```

Then restart Home Assistant.

Next: [Set up](README.md#set-up)
