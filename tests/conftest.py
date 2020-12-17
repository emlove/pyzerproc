import pytest
import asynctest

import bleak


@pytest.fixture
def client_class():
    with asynctest.patch('bleak.BleakClient', autospec=True) as client_class:
        yield client_class


@pytest.fixture
def client(client_class):
    client = asynctest.MagicMock(spec=bleak.BleakClient)
    client_class.return_value = client

    connected = False

    async def is_connected():
        nonlocal connected
        print("CALLING IS_CONNECTED")
        return connected

    async def connect():
        nonlocal connected
        print("CALLING CONNECT")
        connected = True

    async def disconnect():
        nonlocal connected
        print("CALLING DISCONNECT")
        connected = False

    client.is_connected.side_effect = is_connected
    client.connect.side_effect = connect
    client.disconnect.side_effect = disconnect

    yield client


@pytest.fixture
def scanner():
    with asynctest.patch('bleak.BleakScanner', autospec=True) as scanner:
        yield scanner
