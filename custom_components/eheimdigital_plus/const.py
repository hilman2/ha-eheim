# Adapted from Home Assistant Core for ha-eheim. See NOTICE.
"""Constants for the EHEIM Digital integration."""

from logging import Logger, getLogger

from homeassistant.components.climate import PRESET_NONE
from homeassistant.components.light import EFFECT_OFF

from ._vendor.eheimdigital.types import HeaterMode, LightMode

LOGGER: Logger = getLogger(__package__)
DOMAIN = "eheimdigital_plus"
LEGACY_DOMAIN = "eheimdigital"
CONF_MIGRATE_FROM = "migrate_from"

EFFECT_DAYCL_MODE = "daycl_mode"

EFFECT_TO_LIGHT_MODE = {
    EFFECT_DAYCL_MODE: LightMode.DAYCL_MODE,
    EFFECT_OFF: LightMode.MAN_MODE,
}

HEATER_BIO_MODE = "bio_mode"
HEATER_SMART_MODE = "smart_mode"

HEATER_PRESET_TO_HEATER_MODE = {
    HEATER_BIO_MODE: HeaterMode.BIO,
    HEATER_SMART_MODE: HeaterMode.SMART,
    PRESET_NONE: HeaterMode.MANUAL,
}
