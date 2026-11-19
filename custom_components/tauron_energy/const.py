"""Constants for the Tauron Energy integration."""

from datetime import timedelta

DOMAIN = "tauron_energy"

CONF_METER_ID = "meter_id"

SERVICE_URL = "https://elicznik.tauron-dystrybucja.pl"
LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
SELECT_METER_URL = f"{SERVICE_URL}/ustaw_punkt"
DATA_URL = f"{SERVICE_URL}/energia/do/dane"

TIME_ZONE = "Europe/Warsaw"

# Tauron publishes hourly data with a lag of roughly 8 hours, in batches.
UPDATE_INTERVAL = timedelta(hours=1)
# Days imported on the first run.
BACKFILL_DAYS = 30
# Days re-imported on every run, so late or corrected hours are picked up.
REFRESH_DAYS = 3
