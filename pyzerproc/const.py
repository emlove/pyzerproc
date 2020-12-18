"""Constants for pyzerproc."""
__author__ = """Emily Mills"""
__email__ = 'emily@emlove.me'
__version__ = '0.4.2'

CHARACTERISTIC_COMMAND_WRITE = "0000ffe9-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_NOTIFY_VALUE = "0000ffe4-0000-1000-8000-00805f9b34fb"

DISCOVERY_EXPECTED_SERVICES = [
    "0000ffe0-0000-1000-8000-00805f9b34fb",
    "0000ffe5-0000-1000-8000-00805f9b34fb",
    "0000fff0-0000-1000-8000-00805f9b34fb",
]
