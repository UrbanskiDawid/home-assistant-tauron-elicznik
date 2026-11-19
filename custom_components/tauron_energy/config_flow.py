"""Config flow for Tauron Energy."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .api import TauronAuthError, TauronClient
from .const import CONF_METER_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_METER_ID, default=""): str,
    }
)


class TauronEnergyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_METER_ID] = user_input.get(CONF_METER_ID, "").strip()
            await self.async_set_unique_id(
                f"{user_input[CONF_USERNAME].lower()}/{user_input[CONF_METER_ID]}"
            )
            self._abort_if_unique_id_configured()

            try:
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
                    await TauronClient(
                        session,
                        user_input[CONF_USERNAME],
                        user_input[CONF_PASSWORD],
                        user_input[CONF_METER_ID],
                    ).login()
            except TauronAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Tauron login failed")
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_METER_ID] or user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)
