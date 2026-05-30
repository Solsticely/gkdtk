import sys
import time
from typing import Literal
import asyncio as aio

start_time = time.time_ns()


class FragmentedPacketError(Exception):
    pass


class DesyncError(Exception):
    pass


def log(*args, **kwargs):
    time_diff = (time.time_ns() - start_time)/1000000000
    clr = 37 if is_client else 32
    header = "[% 10.2f \033[%dm%s\033[0m]" % (time_diff, clr, role.upper())
    print(header, *args, **kwargs, file=sys.stderr)


def pack(proto: bytes, body: bytes | str) -> bytes:
    assert len(proto) == 1
    if isinstance(body, str):
        body = body.encode("utf8")
    if len(body) > 255:
        raise FragmentedPacketError("Packet length too big: %s" % repr(body))

    return proto+('%02x' % len(body)).encode("ascii")+body+b"\n"


# Packet types
PKS, PKD = b"S", b"d"

VERSION = "0.01"

SYNC_MAGIC_1 = pack(
    PKS,
    "What would you do for a Klondike bar? Say, "+VERSION
)
SYNC_MAGIC_2 = pack(
    PKS,
    VERSION
)

global stdin, stdout, is_client, role, debug
stdin, stdout, debug = None, None, False


# Credit: https://stackoverflow.com/q/64303607 CC-BY-SA 4.0
async def get_streams(in_stream=sys.stdin, out_stream=sys.stdout) \
        -> (aio.StreamReader, aio.StreamWriter):
    loop = aio.get_event_loop()
    reader = aio.StreamReader()
    r_proto = aio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: r_proto, in_stream)

    w_trans, w_proto = \
        await loop.connect_write_pipe(aio.streams.FlowControlMixin, out_stream)
    writer = aio.StreamWriter(w_trans, w_proto, reader, loop)
    return reader, writer


async def read(count: int) -> bytes:
    return await stdin.readexactly(count)


async def clear_read_buffer(timeout: float = .05):
    try:
        async with aio.timeout(timeout):
            while True:
                await read(1)
    except TimeoutError:
        pass


async def read_match(text: bytes):
    for char in text:
        new = await read(1)
        if new[0] != char:
            msg = "Expected %s, got %s" % (repr(bytes([char])), repr(new))
            raise DesyncError(msg)


async def write(x):
    if debug:
        bytes_repr = repr(bytes(x.replace(b"\n", b"")))[2:-1]
        log("\033[2m<packet> %s\033[0m" % bytes_repr)
    stdout.write(x)
    await stdout.drain()


async def writep(*args, **kwargs):
    return await write(pack(*args, **kwargs))


async def resync(noclear: bool = False, *args, **kwargs):
    global is_client

    timeout = 8 if is_client else 2
    max_tries = 3 if is_client else 10

    if is_client:
        await write(b"CLIENT IS OUT OF SYNC\n")

    for tries in range(max_tries):
        log("Fallen out of sync, resyncing! try #%d" % (tries+1))

        try:
            async with aio.timeout(timeout):
                if is_client:
                    await try_resync_with_server(*args, **kwargs)
                else:
                    await try_resync_as_server(
                        *args,
                        noclear=noclear,
                        **kwargs
                    )

            await writep(
                PKD,
                "Hello! You're talking to mux.py %s V.%s" % (role, VERSION)
            )

            return log("Succesfully resynced!")

        except (DesyncError, TimeoutError) as e:
            log("Resync failed:", repr(e))
            if is_client and not noclear:
                await clear_read_buffer()
            elif not is_client:
                await aio.sleep(.2)

    log("Out of tries for resyncing")


async def try_resync_as_server(noclear: bool = False):
    if not noclear:
        await clear_read_buffer()

    await write(b"YOU ARE OUT OF SYNC\n"+b"0"*764+pack(PKS, "hi"))
    await read_match(pack(PKS, "icu"))
    await write(SYNC_MAGIC_1)
    await read_match(SYNC_MAGIC_2)


async def try_resync_with_server():
    while True:
        if await read(1) == b'0':
            break

    await read_match(b"0"*59)

    for i in range(800):
        if await read(1) == b'S':
            break

    await read_match(pack(PKS, "hi")[1:])
    await writep(PKS, "icu")
    await read_match(SYNC_MAGIC_1)
    await write(SYNC_MAGIC_2)


async def main():
    global stdin, stdout, is_client, role, debug
    role = sys.argv[1]
    if len(sys.argv) > 2 and 'd' in sys.argv[2]:
        debug = True
    is_client = {"client": True, "server": False}[role]
    stdin, stdout = await get_streams()
    await resync()

if __name__ == "__main__":
    aio.run(main())
