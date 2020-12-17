"""Device discovery code"""
import logging

import bleak

from .light import Light
from .exceptions import ZerprocException
from .const import DISCOVERY_EXPECTED_SERVICES

_LOGGER = logging.getLogger(__name__)


def is_valid_device(device):
    """Returns true if the given device is a Zerproc light."""
    for service in DISCOVERY_EXPECTED_SERVICES:
        if service not in device.metadata['uuids']:
            return False
    return True


async def discover(timeout=10):
    """Returns nearby discovered lights."""
    _LOGGER.info("Starting scan for local devices")

    lights = []
    try:
        devices = await bleak.BleakScanner.discover(timeout=timeout)
    except bleak.exc.BleakError as ex:
        raise ZerprocException() from ex
    for device in devices:
        if is_valid_device(device):
            lights.append(Light(device.address, device.name))

    _LOGGER.info("Scan complete")
    return lights
