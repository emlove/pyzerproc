"""Console script for pyzerproc."""
import asyncio
import sys
from binascii import hexlify
import click
import logging

import pyzerproc


@click.group()
@click.option('-v', '--verbose', count=True,
              help="Pass once to enable pyzerproc debug logging. Pass twice "
                   "to also enable bleak debug logging.")
def main(verbose):
    """Console script for pyzerproc."""
    logging.basicConfig()
    logging.getLogger('pyzerproc').setLevel(logging.INFO)
    if verbose >= 1:
        logging.getLogger('pyzerproc').setLevel(logging.DEBUG)
    if verbose >= 2:
        logging.getLogger('bleak').setLevel(logging.DEBUG)


@main.command()
def discover():
    """Discover nearby lights"""
    async def run():
        lights = await pyzerproc.discover()
        if not lights:
            click.echo("No nearby lights found")
        for light in lights:
            click.echo(light.address)

    asyncio.get_event_loop().run_until_complete(run())
    return 0


@main.command()
@click.argument('address')
def turn_on(address):
    """Turn on the light with the given MAC address"""
    async def run():
        light = pyzerproc.Light(address)
        try:
            await light.connect()
            await light.turn_on()
        finally:
            await light.disconnect()

    asyncio.get_event_loop().run_until_complete(run())
    return 0


@main.command()
@click.argument('address')
def turn_off(address):
    """Turn off the light with the given MAC address"""
    async def run():
        light = pyzerproc.Light(address)
        try:
            await light.connect()
            await light.turn_off()
        finally:
            await light.disconnect()

    asyncio.get_event_loop().run_until_complete(run())
    return 0


@main.command()
@click.argument('address')
@click.argument('color')
def set_color(address, color):
    """Set the light with the given MAC address to an RRGGBB hex color"""
    async def run():
        light = pyzerproc.Light(address)

        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

        try:
            await light.connect()
            await light.set_color(r, g, b)
        finally:
            await light.disconnect()

    asyncio.get_event_loop().run_until_complete(run())
    return 0


@main.command()
@click.argument('address')
def is_on(address):
    """Get the current on/off status of the light"""
    async def run():
        light = pyzerproc.Light(address)

        try:
            await light.connect()
            state = await light.get_state()
            click.echo(state.is_on)
        finally:
            await light.disconnect()

    asyncio.get_event_loop().run_until_complete(run())
    return 0


@main.command()
@click.argument('address')
def get_color(address):
    """Get the current color of the light"""
    async def run():
        light = pyzerproc.Light(address)

        try:
            await light.connect()
            state = await light.get_state()
            click.echo(hexlify(bytes(state.color)))
        finally:
            await light.disconnect()

    asyncio.get_event_loop().run_until_complete(run())
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
