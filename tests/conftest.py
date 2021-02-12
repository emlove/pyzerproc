import pytest
import sys

import bleak

if sys.version_info[:2] < (3, 8):
    from asynctest import patch, MagicMock
else:
    from unittest.mock import patch, MagicMock


@pytest.fixture
def client_class():
    with patch('bleak.BleakClient', autospec=True) as client_class:
        yield client_class


@pytest.fixture
def client(client_class):
    client = MagicMock(spec=bleak.BleakClient)
    client_class.return_value = client

    connected = False

    async def is_connected():
        nonlocal connected
        return connected

    async def connect():
        nonlocal connected
        connected = True

    async def disconnect():
        nonlocal connected
        connected = False

    client.is_connected.side_effect = is_connected
    client.connect.side_effect = connect
    client.disconnect.side_effect = disconnect

    yield client


@pytest.fixture
def scanner():
    with patch('bleak.BleakScanner', autospec=True) as scanner:
        yield scanner
