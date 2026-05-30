import sys
import time
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


# Packet prototypes
PKS, PKD = b"S", b"d"
ALNUM_PROTOS = {bytes([i]) for i in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"}

VERSION = "0.01"

SYNC_MAGIC_1 = (PKS, "What would you do for a Klondike bar? Say, "+VERSION)
SYNC_MAGIC_2 = (PKS, VERSION)

global stdin, stdout, is_client, role, debug
stdin, stdout, debug = None, None, False


async def unpack() -> (bytes, bytes):
    proto = await read(1)
    if proto not in ALNUM_PROTOS:
        raise DesyncError("Got invalid packet prototype %s" % proto)

    try:
        pkt_size = int(await read(2), 16)
    except ValueError as e:
        raise DesyncError("Got invalid packet length: "+repr(e))
    assert 0 <= pkt_size <= 255

    body = await read(pkt_size)
    delim = await read(1)
    if delim != b"\n":
        raise DesyncError(
            "Expected packet to end with a line feed, got %s instead" % delim)

    return (proto, body)


async def assert_packet(proto: bytes, body: bytes | str):
    if isinstance(body, str):
        body = body.encode("utf8")
    packet = await unpack()
    if packet != (proto, body):
        raise DesyncError("Expected packet %s, got %s" %
                          ((proto, body), packet))


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


async def write(x):
    if debug:
        bytes_repr = repr(bytes(x.replace(b"\n", b"")))[2:-1]
        log("\033[2m<packet> %s\033[0m" % bytes_repr)
    stdout.write(x)
    await stdout.drain()


async def writep(*args, **kwargs):
    return await write(pack(*args, **kwargs))


async def resync(*args, **kwargs):
    global is_client

    timeout = 8 if is_client else 2
    max_tries = 3 if is_client else 10
    try_resync = try_resync_with_server if is_client else try_resync_as_server

    if is_client:
        await write(b"CLIENT IS OUT OF SYNC\n")

    for tries in range(max_tries):
        log("Fallen out of sync, resyncing! try #%d" % (tries+1))

        try:
            async with aio.timeout(timeout):
                await try_resync(*args, **kwargs)

            await writep(
                PKD,
                "Hello! You're talking to mux.py %s V.%s" % (role, VERSION)
            )

            return log("Succesfully resynced!")

        except (DesyncError, TimeoutError) as e:
            log("Resync failed:", repr(e))
            if is_client:
                await clear_read_buffer()
            else:
                await aio.sleep(.2)

    log("Out of tries for resyncing")


async def try_resync_as_server():
    await clear_read_buffer()

    await write(b"YOU ARE OUT OF SYNC\n"+b"0"*764+b"1"+pack(PKS, "hi"))
    await assert_packet(PKS, "icu")
    await writep(*SYNC_MAGIC_1)
    await assert_packet(PKS, VERSION)


async def try_resync_with_server():
    while True:
        if await read(1) == b'0':
            break

    if await read(59) != b"0"*59:
        raise DesyncError(
            "Failed to resync, started resync too late, waiting for next cycle"
        )

    for i in range(800):
        if await read(1) == b'1':
            break

    await assert_packet(PKS, "hi")
    await writep(PKS, "icu")
    await assert_packet(*SYNC_MAGIC_1)
    await writep(PKS, VERSION)


async def listen_client():
    while True:
        await resync()
        await writep(PKD, "desync_for_fun")

        try:
            pass
        except DesyncError as e:
            log("Desynced!", e)
            continue

        return log("Exiting!")

    # Todo list for client:
    # TODO: maybe listen on a provided file instead of STDIO
    # TODO: daemonize, and open a port for commands/connections
    # TODO: implement a little packet packer and unpacker for the connections port
    # TODO: create host/gkd python file
    # TODO: implement really basic shell command through the connections port
    # TODO: maybe unify packet daemon for both client and server
    # TODO: implement socket tunneling


async def listen_server():
    while True:
        await resync()

        try:
            pass
        except DesyncError as e:
            log("Desynced!", e)
            continue

        return log("Exiting!")

    # Todo list for server:
    # TODO: implement really basic shell command
    # TODO: create host/gkd python file and implement shell with it
    # TODO: connect to 9p server?
    # TODO: maybe unify packet daemon for both client and server


async def main():
    global stdin, stdout, is_client, role, debug
    role = sys.argv[1]
    if len(sys.argv) > 2 and 'd' in sys.argv[2]:
        debug = True
    is_client = {"client": True, "server": False}[role]
    stdin, stdout = await get_streams()

    if is_client:
        await listen_client()
    else:
        await listen_server()
        

if __name__ == "__main__":
    aio.run(main())
