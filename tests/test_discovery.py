#!/usr/bin/env python
import pytest

import bleak

from pyzerproc import discover, ZerprocException


@pytest.mark.asyncio
async def test_discover_devices(scanner, client_class):
    """Test the CLI."""
    async def scan(*args, **kwargs):
        """Simulate a scanning response"""
        return [
            bleak.backends.device.BLEDevice(
                'AA:BB:CC:11:22:33',
                'LEDBlue-CC112233',
                uuids=[
                    "0000ffe0-0000-1000-8000-00805f9b34fb",
                    "0000ffe5-0000-1000-8000-00805f9b34fb",
                    "0000fff0-0000-1000-8000-00805f9b34fb",
                ],
                manufacturer_data={}
            ),
            bleak.backends.device.BLEDevice(
                address='AA:BB:CC:44:55:66',
                name='LEDBlue-CC445566',
                uuids=[
                    "0000ffe0-0000-1000-8000-00805f9b34fb",
                    "0000ffe5-0000-1000-8000-00805f9b34fb",
                    "0000fff0-0000-1000-8000-00805f9b34fb",
                ],
                manufacturer_data={}
            ),
            bleak.backends.device.BLEDevice(
                address='DD:EE:FF:11:22:33',
                name='Other',
                uuids=[
                    "0000fe9f-0000-1000-8000-00805f9b34fb",
                ],
                manufacturer_data={}
            ),
        ]

    scanner.discover.side_effect = scan

    devices = await discover(15)

    assert len(devices) == 2
    assert devices[0].address == 'AA:BB:CC:11:22:33'
    assert devices[0].name == 'LEDBlue-CC112233'
    assert devices[1].address == 'AA:BB:CC:44:55:66'
    assert devices[1].name == 'LEDBlue-CC445566'

    scanner.discover.assert_called_with(timeout=15)


@pytest.mark.asyncio
async def test_exception_wrapping(scanner):
    """Test the CLI."""
    async def raise_exception(*args, **kwargs):
        raise bleak.exc.BleakError("TEST")

    scanner.discover.side_effect = raise_exception

    with pytest.raises(ZerprocException):
        await discover()
