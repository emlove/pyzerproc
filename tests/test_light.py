#!/usr/bin/env python
import asyncio
import pytest

import bleak

from pyzerproc import Light, LightState, ZerprocException
from .conftest import MagicMock


@pytest.mark.asyncio
async def test_connect_disconnect(client_class, client):
    """Test connecting and disconnecting."""
    light = Light("00:11:22")

    client_class.assert_called_with("00:11:22")

    await light.connect()

    client.connect.assert_called_once()
    client.start_notify.assert_called_once()
    client.start_notify.assert_called_with(
        "0000ffe4-0000-1000-8000-00805f9b34fb", light._handle_data)

    await light.disconnect()

    client.disconnect.assert_called_once()
    client.stop_notify.assert_called_once()
    client.stop_notify.assert_called_with(
        "0000ffe4-0000-1000-8000-00805f9b34fb")


@pytest.mark.asyncio
async def test_connect_exception(client):
    """Test an exception while connecting."""
    light = Light("00:11:22")

    client.connect.side_effect = bleak.exc.BleakError("TEST")

    with pytest.raises(ZerprocException):
        await light.connect()


@pytest.mark.asyncio
async def test_disconnect_exception(client):
    """Test an exception while disconnecting."""
    light = Light("00:11:22")
    await light.connect()

    client.disconnect.side_effect = bleak.exc.BleakError("TEST")

    with pytest.raises(ZerprocException):
        await light.disconnect()


@pytest.mark.asyncio
async def test_is_connected(client):
    """Test turning on the light."""
    light = Light("00:11:22")
    await light.connect()

    connected = False

    async def is_connected():
        nonlocal connected
        return connected

    client.is_connected.side_effect = is_connected

    assert not await light.is_connected()

    connected = True

    assert await light.is_connected()

    client.is_connected.side_effect = asyncio.TimeoutError("Mock timeout")

    assert not await light.is_connected()


@pytest.mark.asyncio
async def test_turn_on(client):
    """Test turning on the light."""
    light = Light("00:11:22")
    await light.connect()

    await light.turn_on()

    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb', b'\xCC\x23\x33')

    light._write = MagicMock()
    light._write.side_effect = asyncio.TimeoutError("Mock timeout")

    with pytest.raises(ZerprocException):
        await light.turn_on()


@pytest.mark.asyncio
async def test_turn_off(client):
    """Test turning off the light."""
    light = Light("00:11:22")
    await light.connect()

    await light.turn_off()

    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb', b'\xCC\x24\x33')

    light._write = MagicMock()
    light._write.side_effect = asyncio.TimeoutError("Mock timeout")

    with pytest.raises(ZerprocException):
        await light.turn_off()


@pytest.mark.asyncio
async def test_set_color(client):
    """Test setting light color."""
    light = Light("00:11:22")
    await light.connect()

    await light.set_color(255, 255, 255)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',
        b'\x56\xFF\xFF\xFF\x00\xF0\xAA')

    await light.set_color(64, 128, 192)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',
        b'\x56\x08\x10\x18\x00\xF0\xAA')

    # Assert that lights are always on unless zero
    await light.set_color(1, 1, 1)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',
        b'\x56\x01\x01\x01\x00\xF0\xAA')

    # When called with all zeros, just turn off the light
    await light.set_color(0, 0, 0)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb', b'\xCC\x24\x33')

    with pytest.raises(ValueError):
        await light.set_color(999, 999, 999)

    light._write = MagicMock()
    light._write.side_effect = asyncio.TimeoutError("Mock timeout")

    with pytest.raises(ZerprocException):
        await light.set_color(255, 255, 255)


@pytest.mark.asyncio
async def test_get_state(client):
    """Test getting the light state."""
    light = Light("00:11:22")
    await light.connect()

    async def send_response(*args, **kwargs):
        """Simulate a response from the light"""
        light._handle_data(
            63, b'\x66\xe3\x24\x16\x24\x01\xff\x00\x00\x00\x01\x99')

    client.write_gatt_char.side_effect = send_response

    state = await light.get_state()
    assert state.is_on is False
    assert state.color == (255, 0, 0)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',  b'\xEF\x01\x77')
    assert state.__repr__() == "<LightState is_on='False' color='(255, 0, 0)'>"

    # Ensure duplicate responses are handled
    async def send_response(*args, **kwargs):
        """Simulate a response from the light"""
        light._handle_data(
            63, b'\x66\xe3\x23\x16\x24\x01\x10\x05\x1C\x00\x01\x99')
        light._handle_data(
            63, b'\x66\xe3\x23\x16\x24\x01\x10\x05\x1C\x00\x01\x99')

    client.write_gatt_char.side_effect = send_response

    state = await light.get_state()
    assert state.is_on is True
    assert state.color == (131, 41, 230)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',  b'\xEF\x01\x77')

    # Ensure leftover values are discarded before querying
    async def send_response(*args, **kwargs):
        """Simulate a response from the light"""
        light._handle_data(
            63, b'\x66\xe3\x00\x16\x24\x01\xFF\xFF\xFF\x00\x01\x99')

    client.write_gatt_char.side_effect = send_response

    state = await light.get_state()
    assert state.is_on is None
    assert state.color == (255, 255, 255)
    client.write_gatt_char.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',  b'\xEF\x01\x77')

    # Test response timeout
    client.write_gatt_char.side_effect = None
    light._notification_queue = MagicMock()

    async def get_queue(*args, **kwargs):
        """Simulate a queue timeout"""
        raise asyncio.TimeoutError()

    light._notification_queue.get.side_effect = get_queue

    with pytest.raises(ZerprocException):
        state = await light.get_state()


def test_light_state_equality():
    """Test the equality check for light state."""
    assert LightState(True, (0, 255, 0)) != LightState(False, (0, 255, 0))
    assert LightState(True, (0, 255, 0)) != LightState(True, (255, 255, 0))
    assert LightState(True, (0, 255, 0)) == LightState(True, (0, 255, 0))


@pytest.mark.asyncio
async def test_exception_wrapping(client):
    """Test that exceptions are wrapped."""
    light = Light("00:11:22")
    await light.connect()

    client.is_connected.side_effect = bleak.exc.BleakError("TEST")

    with pytest.raises(ZerprocException):
        await light.is_connected()

    client.write_gatt_char.side_effect = bleak.exc.BleakError("TEST")

    with pytest.raises(ZerprocException):
        await light.turn_on()

    # Upstream misses some None checks and doesn't wrap the exceptions
    client.write_gatt_char.side_effect = AttributeError("TEST")

    with pytest.raises(ZerprocException):
        await light.turn_on()
