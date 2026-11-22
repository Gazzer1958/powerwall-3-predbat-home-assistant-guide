"""Tesla Fleet TOU helper for Home Assistant.

This custom integration exposes three Home Assistant services which send
time-of-use (TOU) tariff definitions directly to the Tesla Fleet API:

    * set_force_discharge_tariff
    * set_force_charge_tariff
    * restore_neutral

DESIGN NOTE - SITE ID
---------------------
The Tesla Energy Site ID is deliberately NOT stored as a Python default.

Every service call must supply ``site_id`` explicitly. The Home Assistant
scripts already know which Powerwall site they are operating on, so keeping
the site ID visible at the call site avoids silently targeting a hard-coded
installation.

The service schema validates that the field exists and is non-empty before
the service callback runs. Therefore a missing site_id is rejected locally
by Home Assistant; it does not produce a request with a blank site ID.

A non-empty but incorrect site_id cannot be proven wrong locally. It is sent
to the Tesla Fleet API, which is then responsible for rejecting an unknown or
unauthorised energy site.

AUTHENTICATION
--------------
Authentication is deliberately obtained from the existing Home Assistant
Tesla Fleet config entry. This integration does not store a second set of
Tesla OAuth credentials. Home Assistant's OAuth2 session is asked to ensure
the access token is valid before each Fleet API operation.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import jwt
import voluptuous as vol
from aiohttp import ClientError

from homeassistant.components.tesla_fleet.const import (
    DOMAIN as TESLA_FLEET_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)

REGION_SERVERS = {
    "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
    "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
    "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.com",
}

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tesla_fleet_tou_test"

SERVICE_SET_FORCE_DISCHARGE_TARIFF = "set_force_discharge_tariff"
SERVICE_SET_FORCE_CHARGE_TARIFF = "set_force_charge_tariff"
SERVICE_RESTORE_NEUTRAL = "restore_neutral"


def _validate_site_id(value: Any) -> str:
    """Validate the Tesla Energy Site ID supplied by a service call.

    ``vol.Required`` catches a completely missing site_id. This validator
    additionally rejects an empty string so that a blank value cannot make
    it into the URL sent to Tesla.

    It deliberately does not try to verify that the ID belongs to this
    user's Tesla account. That can only be established by Tesla's API.
    Therefore an incorrect but non-empty ID is still passed to Tesla and
    Tesla can reject it.

    Leading/trailing whitespace is removed so it cannot accidentally become
    part of the REST URL.
    """
    site_id = cv.string(value).strip()

    if not site_id:
        raise vol.Invalid("site_id must be a non-empty Tesla Energy Site ID.")

    return site_id


# All three services require the caller to provide the site ID explicitly.
#
# There is intentionally NO default here.
#
# Failure behaviour is therefore:
#   1. site_id omitted  -> Home Assistant rejects the service call locally.
#   2. site_id is blank -> _validate_site_id rejects it locally.
#   3. wrong non-empty ID -> the request reaches Tesla, which can reject it.
#
# This is safer than silently falling back to one hard-coded Powerwall site.
SET_SCHEMA = vol.Schema(
    {
        vol.Required("site_id"): _validate_site_id,
    }
)


FORCE_CHARGE_SCHEMA = vol.Schema(
    {
        vol.Required("site_id"): _validate_site_id,
    }
)


RESTORE_SCHEMA = vol.Schema(
    {
        vol.Required("site_id"): _validate_site_id,
    }
)


def _parse_time(value: str) -> tuple[int, int]:
    try:
        hour, minute = [int(x) for x in value.strip().split(":")]
    except (TypeError, ValueError):
        raise ServiceValidationError(
            f"Invalid time '{value}'. Use HH:MM."
        ) from None

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ServiceValidationError(
            f"Invalid time '{value}'. Use HH:MM."
        )

    return hour, minute


def _period(
    from_hour: int,
    from_minute: int,
    to_hour: int,
    to_minute: int,
) -> dict[str, int]:
    return {
        "fromDayOfWeek": 0,
        "toDayOfWeek": 6,
        "fromHour": from_hour,
        "fromMinute": from_minute,
        "toHour": to_hour,
        "toMinute": to_minute,
    }


def _build_test_periods(
    start_time: str,
    end_time: str,
) -> tuple[list[dict[str, int]], list[dict[str, int]]]:

    sh, sm = _parse_time(start_time)
    eh, em = _parse_time(end_time)

    start = sh * 60 + sm
    end = eh * 60 + em

    if start == end:
        raise ServiceValidationError(
            "Start and end time cannot be identical."
        )

    off_peak: list[dict[str, int]] = []
    on_peak: list[dict[str, int]] = []

    # Tesla Fleet represents midnight as toHour=0/toMinute=0.
    # Do not manufacture a 23:59 -> 00:00 period: the Fleet API
    # validates the complete schedule for overlaps and gaps.

    # Normal same-day window.
    if start < end:
        if start > 0:
            off_peak.append(
                _period(0, 0, sh, sm)
            )

        on_peak.append(
            _period(sh, sm, eh, em)
        )

        # End at midnight is represented by toHour=0.
        off_peak.append(
            _period(eh, em, 0, 0)
        )

    # Cross-midnight window.
    else:
        # Portion before midnight.
        on_peak.append(
            _period(sh, sm, 0, 0)
        )

        # Portion after midnight, if any.
        if end > 0:
            on_peak.append(
                _period(0, 0, eh, em)
            )

        # The remaining part of the day is off-peak.
        if end > 0:
            off_peak.append(
                _period(eh, em, sh, sm)
            )
        else:
            off_peak.append(
                _period(0, 0, sh, sm)
            )

    return off_peak, on_peak


def _build_tariff(
    *,
    name: str,
    off_peak_import: float,
    peak_import: float,
    off_peak_export: float,
    peak_export: float,
    off_peak_periods: list[dict[str, int]],
    peak_periods: list[dict[str, int]],
) -> dict[str, Any]:

    return {
        "version": 1,
        "monthly_minimum_bill": 0,
        "min_applicable_demand": 0,
        "max_applicable_demand": 0,
        "monthly_charges": 0,
        "utility": "Octopus Energy",
        "code": "OCTO-CUSTOM-FLEET-TEST",
        "name": name,
        "currency": "GBP",

        "daily_charges": [
            {
                "name": "Charge",
                "amount": 0
            }
        ],

        "daily_demand_charges": {},

        "demand_charges": {
            "ALL": {
                "rates": {
                    "ALL": 0
                }
            },
            "AllYear": {
                "rates": {}
            }
        },

        "energy_charges": {
            "ALL": {
                "rates": {
                    "ALL": 0
                }
            },
            "AllYear": {
                "rates": {
                    "OFF_PEAK": off_peak_import,
                    "ON_PEAK": peak_import
                }
            }
        },

        "seasons": {
            "AllYear": {
                "fromMonth": 1,
                "fromDay": 1,
                "toMonth": 12,
                "toDay": 31,

                "tou_periods": {
                    "OFF_PEAK": {
                        "periods": off_peak_periods
                    },
                    "ON_PEAK": {
                        "periods": peak_periods
                    }
                }
            }
        },

        "sell_tariff": {
            "min_applicable_demand": 0,
            "monthly_minimum_bill": 0,
            "monthly_charges": 0,
            "max_applicable_demand": 0,
            "utility": "Octopus Energy",

            "daily_charges": [
                {
                    "name": "Charge",
                    "amount": 0
                }
            ],

            "demand_charges": {
                "ALL": {
                    "rates": {
                        "ALL": 0
                    }
                },
                "AllYear": {
                    "rates": {}
                }
            },

            "energy_charges": {
                "ALL": {
                    "rates": {
                        "ALL": 0
                    }
                },
                "AllYear": {
                    "rates": {
                        "OFF_PEAK": off_peak_export,
                        "ON_PEAK": peak_export
                    }
                }
            },

            "seasons": {
                "AllYear": {
                    "fromMonth": 1,
                    "fromDay": 1,
                    "toMonth": 12,
                    "toDay": 31,

                    "tou_periods": {
                        "OFF_PEAK": {
                            "periods": off_peak_periods
                        },
                        "ON_PEAK": {
                            "periods": peak_periods
                        }
                    }
                }
            },

            "code": ""
        }
    }


async def _get_authenticated_fleet_session(
    hass: HomeAssistant,
) -> tuple[Any, str, str]:
    """Return the HTTP session, Fleet server and valid access token.

    The custom TOU integration deliberately reuses Home Assistant's existing
    Tesla Fleet OAuth config entry. It does not maintain a second login.

    ``async_ensure_token_valid()`` below is important because it lets the
    Home Assistant OAuth2 implementation refresh the token when necessary.
    A change to the Python site-ID handling therefore has no reason to
    trigger Tesla re-authorisation.
    """

    # Find the existing Tesla Fleet config entry. Authentication belongs to
    # the official Tesla Fleet integration, not to this custom TOU helper.
    entries = hass.config_entries.async_entries(TESLA_FLEET_DOMAIN)

    if not entries:
        raise HomeAssistantError(
            "Tesla Fleet integration is not configured."
        )

    entry: ConfigEntry = entries[0]

    implementation = (
        await async_get_config_entry_implementation(
            hass,
            entry,
        )
    )

    oauth_session = OAuth2Session(
        hass,
        entry,
        implementation,
    )

    # Ensure the access token is current before calling Tesla. This uses
    # Home Assistant's existing OAuth refresh mechanism.
    await oauth_session.async_ensure_token_valid()

    access_token = oauth_session.token[CONF_ACCESS_TOKEN]

    token = jwt.decode(
        access_token,
        options={"verify_signature": False},
    )

    region_code = token.get("ou_code")

    if not region_code:
        raise HomeAssistantError(
            "Tesla Fleet access token has no region code."
        )

    region_code = region_code.lower()

    if region_code not in REGION_SERVERS:
        raise HomeAssistantError(
            f"Unknown Tesla Fleet region: {region_code}"
        )

    session = async_get_clientsession(hass)

    return session, REGION_SERVERS[region_code], access_token


async def _send_tou(
    hass: HomeAssistant,
    site_id: str,
    tariff: dict[str, Any],
) -> None:
    """Send one complete TOU tariff to the explicitly named Tesla site.

    At this point the Home Assistant service schema has already checked that
    site_id exists and is non-empty.

    The ID is inserted into Tesla's REST path:
        /api/1/energy_sites/<site_id>/time_of_use_settings

    A valid-looking but wrong site ID is still possible. Only Tesla can
    determine whether that ID is a real energy site accessible to the
    authenticated account.
    """

    session, server, access_token = (
        await _get_authenticated_fleet_session(hass)
    )

    # Tesla identifies the target Powerwall installation through the
    # energy_sites/<site_id> part of the URL. There is deliberately no
    # fallback/default here: the validated caller-supplied ID is used.
    url = (
        f"{server}/api/1/energy_sites/"
        f"{site_id}/time_of_use_settings"
    )

    payload = {
        "tou_settings": {
            "tariff_content_v2": tariff
        }
    }

    _LOGGER.warning(
        "TESLA FLEET TOU TEST: sending tariff to site %s",
        site_id,
    )

    try:

        async with session.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        ) as response:

            response_text = await response.text()

            if response.status >= 400:

                _LOGGER.error(
                    "TESLA FLEET TOU TEST FAILED: HTTP %s: %s",
                    response.status,
                    response_text,
                )

                raise HomeAssistantError(
                    f"Tesla Fleet TOU request failed: "
                    f"HTTP {response.status}. "
                    f"See HA log for Tesla response."
                )

            _LOGGER.warning(
                "TESLA FLEET TOU TEST SUCCESS: "
                "Tesla returned HTTP %s",
                response.status,
            )

    except ClientError as err:

        _LOGGER.exception(
            "TESLA FLEET TOU TEST HTTP error"
        )

        raise HomeAssistantError(
            f"Tesla Fleet HTTP error: {err}"
        ) from err


async def async_setup(
    hass: HomeAssistant,
    config: dict[str, Any],
) -> bool:

    async def set_force_discharge_tariff(
        call: ServiceCall,
    ) -> None:
        """
        Set a dynamic six-hour force-discharge tariff.

        WHAT:
            Creates an ON_PEAK window with 80p import / 80p export and
            leaves the rest of the day at 30p import / 12p export.

        HOW:
            The window starts on the current 30-minute boundary and ends
            six hours later. _build_test_periods() handles normal and
            cross-midnight windows before the tariff is sent to Tesla.

        WHY:
            PredBat can temporarily make discharge/export economically
            attractive while it controls the Powerwall.

        The window starts at the current time rounded down to the
        nearest 30-minute slot and ends six hours later.

        Peak:
          Import 80p/kWh
          Export 80p/kWh

        Off-peak:
          Import 30p/kWh
          Export 12p/kWh
        """

        now = dt_util.now()

        # Round down to the latest 30-minute slot.
        start = now.replace(
            minute=(now.minute // 30) * 30,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(hours=6)

        start_time = start.strftime("%H:%M")
        end_time = end.strftime("%H:%M")

        off_peak, peak = _build_test_periods(
            start_time,
            end_time,
        )

        tariff = _build_tariff(
            name=f"Force Discharge {start_time}-{end_time}",
            off_peak_import=0.30,
            peak_import=0.80,
            off_peak_export=0.12,
            peak_export=0.80,
            off_peak_periods=off_peak,
            peak_periods=peak,
        )

        _LOGGER.warning(
            "TESLA FLEET TOU: setting force discharge tariff "
            "%s to %s",
            start_time,
            end_time,
        )

        await _send_tou(
            hass,
            call.data["site_id"],
            tariff,
        )

    async def set_force_charge_tariff(
        call: ServiceCall,
    ) -> None:
        """
        Set an all-day 5p import / 5p export tariff.

        WHAT:
            Creates a full-day OFF_PEAK tariff at 5p/kWh for both import
            and export.

        HOW:
            The tariff is built locally and sent to the exact site_id
            supplied by the calling Home Assistant script.

        WHY:
            The deliberately low import price makes grid charging
            attractive during a PredBat force-charge operation.

        This is used to make grid charging attractive during
        a PredBat force-charge operation.
        """

        full_day = [
            _period(
                0,
                0,
                23,
                59,
            )
        ]

        tariff = _build_tariff(
            name="PredBat Force Charge 5p/5p",
            off_peak_import=0.05,
            peak_import=0.05,
            off_peak_export=0.05,
            peak_export=0.05,
            off_peak_periods=full_day,
            peak_periods=[],
        )

        # There is no ON_PEAK period in this tariff,
        # so remove the unused ON_PEAK rates.
        tariff["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.05
        }

        tariff["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        tariff["sell_tariff"]["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.05
        }

        tariff["sell_tariff"]["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        await _send_tou(
            hass,
            call.data["site_id"],
            tariff,
        )


    async def restore_neutral(
        call: ServiceCall,
    ) -> None:
        """Restore the known-good 30p import / 12p export neutral tariff.

        This is the normal resting tariff used after a temporary force-charge
        or force-discharge operation. The caller must explicitly provide the
        Tesla site_id, just like the two force tariff services.
        """

        # Known-good neutral tariff structure:
        # Import 30p/kWh
        # Export 12p/kWh
        #
        # One full-day OFF_PEAK period.
        #
        # IMPORTANT:
        # The OFF_PEAK period must have a matching
        # OFF_PEAK price. Do not replace this with
        # an ALL rate while leaving an OFF_PEAK period.

        full_day = [
            _period(0, 0, 23, 59),
        ]

        tariff = _build_tariff(
            name="Neutral Baseline",
            off_peak_import=0.30,
            peak_import=0.30,
            off_peak_export=0.12,
            peak_export=0.12,
            off_peak_periods=full_day,
            peak_periods=[],
        )

        # Remove the unused ON_PEAK rates because
        # the neutral tariff has no ON_PEAK period.
        tariff["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.30
        }

        tariff["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        tariff["sell_tariff"]["energy_charges"]["AllYear"]["rates"] = {
            "OFF_PEAK": 0.12
        }

        tariff["sell_tariff"]["seasons"]["AllYear"]["tou_periods"] = {
            "OFF_PEAK": {
                "periods": full_day
            }
        }

        await _send_tou(
            hass,
            call.data["site_id"],
            tariff,
        )

    # Register each service with its schema. Voluptuous validation runs
    # before the callback, so a missing/blank site_id never reaches
    # _send_tou() and cannot become a malformed Tesla URL.
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FORCE_DISCHARGE_TARIFF,
        set_force_discharge_tariff,
        schema=SET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FORCE_CHARGE_TARIFF,
        set_force_charge_tariff,
        schema=FORCE_CHARGE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE_NEUTRAL,
        restore_neutral,
        schema=RESTORE_SCHEMA,
    )

    _LOGGER.warning(
        "Tesla Fleet TOU integration loaded; site_id is required for every service call."
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Tesla Fleet TOU Test from a config entry."""

    return True
