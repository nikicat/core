"""Support for Twente Milieu Calendar."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util

from .const import DOMAIN, WASTE_TYPE_TO_DESCRIPTION
from .entity import TwenteMilieuEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Twente Milieu calendar based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.data[CONF_ID]]
    async_add_entities([TwenteMilieuCalendar(coordinator, entry)])


class TwenteMilieuCalendar(TwenteMilieuEntity, CalendarEventDevice):
    """Defines a Twente Milieu calendar."""

    _attr_name = "Twente Milieu"
    _attr_icon = "mdi:delete-empty"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the Twente Milieu entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = str(entry.data[CONF_ID])
        self._event: dict[str, Any] | None = None

    @property
    def event(self) -> dict[str, Any] | None:
        """Return the next upcoming event."""
        return self._event

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Return calendar events within a datetime range."""
        events: list[dict[str, Any]] = []
        for waste_type, waste_dates in self.coordinator.data.items():
            events.extend(
                {
                    "all_day": True,
                    "start": {"date": waste_date.isoformat()},
                    "end": {"date": waste_date.isoformat()},
                    "summary": WASTE_TYPE_TO_DESCRIPTION[waste_type],
                }
                for waste_date in waste_dates
                if start_date.date() <= waste_date <= end_date.date()
            )

        return events

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        next_waste_pickup_type = None
        next_waste_pickup_date = None
        for waste_type, waste_dates in self.coordinator.data.items():
            if (
                waste_dates
                and (
                    next_waste_pickup_date is None
                    or waste_dates[0]  # type: ignore[unreachable]
                    < next_waste_pickup_date
                )
                and waste_dates[0] >= dt_util.now().date()
            ):
                next_waste_pickup_date = waste_dates[0]
                next_waste_pickup_type = waste_type

        self._event = None
        if next_waste_pickup_date is not None and next_waste_pickup_type is not None:
            self._event = {
                "all_day": True,
                "start": {"date": next_waste_pickup_date.isoformat()},
                "end": {"date": next_waste_pickup_date.isoformat()},
                "summary": WASTE_TYPE_TO_DESCRIPTION[next_waste_pickup_type],
            }

        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()