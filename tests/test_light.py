#!/usr/bin/env python
import queue
import pytest

import pygatt

from pyzerproc import Light, LightState, ZerprocException


def test_connect_disconnect(adapter, device):
    """Test connecting and disconnecting."""
    light = Light("00:11:22")
    light.connect()

    adapter.start.assert_called_with(reset_on_start=False)
    adapter.connect.assert_called_with("00:11:22")
    device.subscribe.assert_called_with(
        "0000ffe4-0000-1000-8000-00805f9b34fb", callback=light._handle_data)

    # Duplicate call shouldn't connect again
    light.connect()

    adapter.start.assert_called_once()
    adapter.connect.assert_called_once()

    light.disconnect()

    adapter.stop.assert_called_once()

    # Duplicate disconnect shouldn't call stop again
    light.disconnect()

    adapter.stop.assert_called_once()


def test_disconnect_exception(adapter, device):
    """Test an exception while disconnecting."""
    light = Light("00:11:22")
    light.connect()

    adapter.start.assert_called_with(reset_on_start=False)
    adapter.connect.assert_called_with("00:11:22")
    device.subscribe.assert_called_with(
        "0000ffe4-0000-1000-8000-00805f9b34fb", callback=light._handle_data)

    assert light.connected

    adapter.stop.side_effect = pygatt.BLEError("TEST")

    with pytest.raises(ZerprocException):
        light.disconnect()

    adapter.stop.assert_called_once()
    assert not light.connected


def test_turn_on_not_connected(device):
    """Test turning on the light not connected."""
    light = Light("00:11:22")

    with pytest.raises(ZerprocException):
        light.turn_on()


def test_turn_on(device):
    """Test turning on the light."""
    light = Light("00:11:22")
    light.connect()

    light.turn_on()

    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb', b'\xCC\x23\x33')


def test_turn_off(device):
    """Test turning off the light."""
    light = Light("00:11:22")
    light.connect()

    light.turn_off()

    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb', b'\xCC\x24\x33')


def test_set_color(device):
    """Test setting light color."""
    light = Light("00:11:22")
    light.connect()

    light.set_color(255, 255, 255)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',
        b'\x56\xFF\xFF\xFF\x00\xF0\xAA')

    light.set_color(64, 128, 192)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',
        b'\x56\x08\x10\x18\x00\xF0\xAA')

    # Assert that lights are always on unless zero
    light.set_color(1, 1, 1)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',
        b'\x56\x01\x01\x01\x00\xF0\xAA')

    # When called with all zeros, just turn off the light
    light.set_color(0, 0, 0)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb', b'\xCC\x24\x33')

    with pytest.raises(ValueError):
        light.set_color(999, 999, 999)


def test_get_state(device, mocker):
    """Test getting the light state."""
    light = Light("00:11:22")
    light.connect()

    def send_response(*args, **kwargs):
        """Simulate a response from the light"""
        light._handle_data(
            63, b'\x66\xe3\x24\x16\x24\x01\xff\x00\x00\x00\x01\x99')

    device.char_write.side_effect = send_response

    state = light.get_state()
    assert state.is_on is False
    assert state.color == (255, 0, 0)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',  b'\xEF\x01\x77')
    assert state.__repr__() == "<LightState is_on='False' color='(255, 0, 0)'>"

    # Ensure duplicate responses are handled
    def send_response(*args, **kwargs):
        """Simulate a response from the light"""
        light._handle_data(
            63, b'\x66\xe3\x23\x16\x24\x01\x10\x05\x1C\x00\x01\x99')
        light._handle_data(
            63, b'\x66\xe3\x23\x16\x24\x01\x10\x05\x1C\x00\x01\x99')

    device.char_write.side_effect = send_response

    state = light.get_state()
    assert state.is_on is True
    assert state.color == (131, 41, 230)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',  b'\xEF\x01\x77')

    # Ensure leftover values are discarded before querying
    def send_response(*args, **kwargs):
        """Simulate a response from the light"""
        light._handle_data(
            63, b'\x66\xe3\x00\x16\x24\x01\xFF\xFF\xFF\x00\x01\x99')

    device.char_write.side_effect = send_response

    state = light.get_state()
    assert state.is_on is None
    assert state.color == (255, 255, 255)
    device.char_write.assert_called_with(
        '0000ffe9-0000-1000-8000-00805f9b34fb',  b'\xEF\x01\x77')

    # Test response timeout
    device.char_write.side_effect = None
    light._notification_queue = mocker.MagicMock()

    def get_queue(*args, **kwargs):
        """Simulate a queue timeout"""
        raise queue.Empty()

    light._notification_queue.get.side_effect = get_queue

    with pytest.raises(ZerprocException):
        state = light.get_state()


def test_light_state_equality():
    """Test the equality check for light state."""
    assert LightState(True, (0, 255, 0)) != LightState(False, (0, 255, 0))
    assert LightState(True, (0, 255, 0)) != LightState(True, (255, 255, 0))
    assert LightState(True, (0, 255, 0)) == LightState(True, (0, 255, 0))


def test_exception_wrapping(device, adapter):
    """Test that exceptions are wrapped."""
    def raise_exception(*args, **kwargs):
        raise pygatt.BLEError("TEST")

    adapter.start.side_effect = raise_exception

    with pytest.raises(ZerprocException):
        light = Light("00:11:22")
        light.connect()

    adapter.start.side_effect = None
    adapter.stop.side_effect = raise_exception

    with pytest.raises(ZerprocException):
        light = Light("00:11:22")
        light.connect()
        light.disconnect()

    device.char_write.side_effect = raise_exception

    with pytest.raises(ZerprocException):
        light = Light("00:11:22")
        light.connect()
        light.turn_on()
