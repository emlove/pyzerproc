"""Device discovery code"""
import logging

import bleak

from .light import Light
from .exceptions import ZerprocException

_LOGGER = logging.getLogger(__name__)

EXPECTED_SERVICES = [
    "0000ffe0-0000-1000-8000-00805f9b34fb",
    "0000ffe5-0000-1000-8000-00805f9b34fb",
    "0000fff0-0000-1000-8000-00805f9b34fb",
]


def is_valid_device(device):
    """Returns true if the given device is a Zerproc light."""
    for service in EXPECTED_SERVICES:
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
