"""Test the Home Assistant Yellow integration."""
from unittest.mock import patch

import pytest

from homeassistant.components.homeassistant_yellow.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, MockModule, mock_integration


@pytest.mark.parametrize(
    "onboarded, num_entries, num_flows", ((False, 1, 0), (True, 0, 1))
)
async def test_setup_entry(
    hass: HomeAssistant, onboarded, num_entries, num_flows
) -> None:
    """Test setup of a config entry, including setup of zha."""
    mock_integration(hass, MockModule("hassio"))

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Home Assistant Yellow",
    )
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.homeassistant_yellow.get_os_info",
        return_value={"board": "yellow"},
    ) as mock_get_os_info, patch(
        "homeassistant.components.onboarding.async_is_onboarded", return_value=onboarded
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert len(mock_get_os_info.mock_calls) == 1

    assert len(hass.config_entries.async_entries("zha")) == num_entries
    assert len(hass.config_entries.flow.async_progress_by_handler("zha")) == num_flows


async def test_setup_entry_wrong_board(hass: HomeAssistant) -> None:
    """Test setup of a config entry with wrong board type."""
    mock_integration(hass, MockModule("hassio"))

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Home Assistant Yellow",
    )
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.homeassistant_yellow.get_os_info",
        return_value={"board": "generic-x86-64"},
    ) as mock_get_os_info:
        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert len(mock_get_os_info.mock_calls) == 1


async def test_setup_entry_wait_hassio(hass: HomeAssistant) -> None:
    """Test setup of a config entry when hassio has not fetched os_info."""
    mock_integration(hass, MockModule("hassio"))

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Home Assistant Yellow",
    )
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.homeassistant_yellow.get_os_info",
        return_value=None,
    ) as mock_get_os_info:
        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert len(mock_get_os_info.mock_calls) == 1
        assert config_entry.state == ConfigEntryState.SETUP_RETRY
