"""Config flow + setup, with Tauron mocked."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.tauron_energy.api import TauronAuthError
from custom_components.tauron_energy.const import DOMAIN

USER = {"username": "jan@example.com", "password": "secret", "meter_id": ""}


async def test_flow_and_setup(recorder_mock, enable_custom_integrations, hass):
    with patch(
        "custom_components.tauron_energy.api.TauronClient.login", new=AsyncMock()
    ), patch(
        "custom_components.tauron_energy.api.TauronClient.get_hourly",
        new=AsyncMock(return_value=[]),
    ) as get_hourly:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "jan@example.com"
        await hass.async_block_till_done()
        await async_wait_recording_done(hass)
        await hass.async_block_till_done()

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        assert entry.state is ConfigEntryState.LOADED
        assert get_hourly.await_count == 1  # initial import ran

        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_flow_invalid_auth(recorder_mock, enable_custom_integrations, hass):
    with patch(
        "custom_components.tauron_energy.api.TauronClient.login",
        new=AsyncMock(side_effect=TauronAuthError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
