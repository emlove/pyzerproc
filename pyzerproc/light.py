"""Device class"""
import asyncio
from binascii import hexlify
import logging
import math

import bleak

from .exceptions import ZerprocException

_LOGGER = logging.getLogger(__name__)

CHARACTERISTIC_COMMAND_WRITE = "0000ffe9-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_NOTIFY_VALUE = "0000ffe4-0000-1000-8000-00805f9b34fb"

NOTIFICATION_RESPONSE_TIMEOUT = 5


class Light():
    """Represents one connected light"""

    def __init__(self, address, name=None):
        self._address = address
        self._name = name
        self._adapter = None
        self._device = None
        self._client = bleak.BleakClient(self._address)
        self._notification_queue = asyncio.Queue(maxsize=1)

    @property
    def address(self):
        """Return the mac address of this light."""
        return self._address

    @property
    def name(self):
        """Return the discovered name of this light."""
        return self._name

    async def is_connected(self):
        """Returns true if the light is connected."""
        return await self._client.is_connected()

    async def connect(self):
        """Connect to this light"""
        if await self.is_connected():
            return

        _LOGGER.debug("Connecting to %s", self._address)

        try:
            await self._client.connect()
            await self._client.start_notify(
                CHARACTERISTIC_NOTIFY_VALUE, self._handle_data)
        except bleak.exc.BleakError as ex:
            raise ZerprocException() from ex

        _LOGGER.debug("Connected to %s", self._address)

    async def disconnect(self):
        """Close the connection to the light."""
        if not await self.is_connected():
            return

        _LOGGER.debug("Disconnecting from %s", self._address)
        try:
            await self._client.stop_notify(CHARACTERISTIC_NOTIFY_VALUE)
            await self._client.disconnect()
        except bleak.exc.BleakError as ex:
            raise ZerprocException() from ex
        _LOGGER.debug("Disconnected from %s", self._address)

    async def turn_on(self):
        """Turn on the light"""
        _LOGGER.info("Turning on %s", self._address)
        await self._write(CHARACTERISTIC_COMMAND_WRITE, b'\xCC\x23\x33')
        _LOGGER.debug("Turned on %s", self._address)

    async def turn_off(self):
        """Turn off the light"""
        _LOGGER.info("Turning off %s", self._address)
        await self._write(CHARACTERISTIC_COMMAND_WRITE, b'\xCC\x24\x33')
        _LOGGER.debug("Turned off %s", self._address)

    async def set_color(self, r, g, b):
        """Set the color of the light

        Accepts red, green, and blue values from 0-255
        """
        for value in (r, g, b):
            if not 0 <= value <= 255:
                raise ValueError(
                    "Value {} is outside the valid range of 0-255")

        _LOGGER.info("Changing color of %s to #%02x%02x%02x",
                     self._address, r, g, b)

        # Normalize to 0-31, the dimmable range of these lights. If setting to
        # full brightness, set the channel to 0xFF to mimic the vendor app
        # behavior
        r = 255 if r == 255 else int(math.ceil(r * 31 / 255))
        g = 255 if g == 255 else int(math.ceil(g * 31 / 255))
        b = 255 if b == 255 else int(math.ceil(b * 31 / 255))

        if r == 0 and g == 0 and b == 0:
            await self.turn_off()
        else:
            color_string = bytes((r, g, b))

            value = b'\x56' + color_string + b'\x00\xF0\xAA'
            await self._write(CHARACTERISTIC_COMMAND_WRITE, value)
            _LOGGER.debug("Changed color of %s", self._address)

    def _handle_data(self, handle, value):
        """Handle an incoming notification message."""
        _LOGGER.debug("Got handle '%s' and value %s", handle, hexlify(value))
        try:
            self._notification_queue.put_nowait(value)
        except asyncio.QueueFull:
            _LOGGER.debug("Discarding duplicate response", exc_info=True)

    async def get_state(self):
        """Get the current state of the light"""
        # Clear the queue if a value is somehow left over
        try:
            self._notification_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass

        await self._write(CHARACTERISTIC_COMMAND_WRITE, b'\xEF\x01\x77')

        try:
            response = await asyncio.wait_for(
                self._notification_queue.get(),
                timeout=NOTIFICATION_RESPONSE_TIMEOUT)
        except asyncio.TimeoutError as ex:
            raise ZerprocException("Timeout waiting for response") from ex

        on_off_value = int(response[2])

        r = int(response[6])
        g = int(response[7])
        b = int(response[8])

        if on_off_value == 0x23:
            is_on = True
        elif on_off_value == 0x24:
            is_on = False
        else:
            is_on = None

        # Normalize and clamp from 0-31, to 0-255
        r = int(min(r * 255 / 31, 255))
        g = int(min(g * 255 / 31, 255))
        b = int(min(b * 255 / 31, 255))

        state = LightState(is_on, (r, g, b))

        _LOGGER.info("Got state of %s: %s", self._address, state)

        return state

    async def _write(self, uuid, value):
        """Internal method to write to the device"""
        _LOGGER.debug("Writing 0x%s to characteristic %s", value.hex(), uuid)
        try:
            await self._client.write_gatt_char(uuid, bytearray(value))
        except bleak.exc.BleakError as ex:
            raise ZerprocException() from ex
        _LOGGER.debug("Wrote 0x%s to characteristic %s", value.hex(), uuid)


class LightState():
    """Represents the current state of the light"""
    __slots__ = 'is_on', 'color',

    def __init__(self, is_on, color):
        """Create the state object"""
        self.is_on = is_on
        self.color = color

    def __repr__(self):
        """Return a string representation of the state object"""
        return "<LightState is_on='{}' color='{}'>".format(
            self.is_on, self.color)

    def __eq__(self, other):
        """Check for equality."""
        return self.is_on == other.is_on and self.color == other.color
