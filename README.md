# GKD toolkit

Hi! Have you ever tried to SSH into a handheld that doesn't have wifi
connectivity? No? Well have I the solution you're maybe looking for!

## What is GKD toolkit/GKDTK

If you're familiar with ADB (android debug bridge), GKD toolkit is
basically that. It changes the device's USB driver to a serial port
and runs a shell on the device.

## Requirements

### Host requirements

- picocom
  - `sudo dnf install picocom`
- python3
- bash

### Guest requirements

- python3
- bash
- A linux kernel with configfs enabled

## Usage

Copy all files in `device/` onto the GKD Pixel or other handheld
device, and mark them executable. To begin using GKDTK, run
`handheld/setup_serial.sh` on the device.

Once the host scripts are ready for general use, you can run them on
your host computer. In the meanwhile, you can use
`picocom /dev/ttyACM* -b 38400` to connect to a basic shell terminal :)

## Planned functionality

### Backend features

On the device, a socket multiplexer will be ran after you run 
`handheld/setup_serial.sh`. This multiplexer will multiplex multiple streams 
through the serial port and connect them to multiple destinations; namely:

1. A plan9 FS server running on the device for the purposes of
`host/gkd push`, `host/gkd pull`, and `host/gkd mount`; and
2. A shell for the purposes of running commands on the device.

See [packets](Packets) for the format of the serial packets.

On the host, a simple connection management system is implemented, for
each device a server will open a unix socket at `/tmp/gkdtk_<DEVICEID>`
for as long as the device is accessible.

### Unified command line argument

On the host, you will be able to use the following commands:

```console
$ host/gkd devices
Finding devices...
/dev/ttyACM0 - GameKiddy GKD Pixel2 [ID: ACM1]

$ host/gkd push
gkd push LOCAL REMOTE
  Upload a local file onto the remote device.

$ host/gkd push ~/.ssh/id_ed25519 /storage/.ssh/id_ed25519
Finding devices...
Only 1 device found, connecting to RK3326_ttyACM0
Done! Took 0.01 seconds.

$ host/gkd pull
gkd pull REMOTE LOCAL
  Download a remote file

$ host/gkd pull /etc/passwd ./passwd
Done! Took 0.01 seconds.

$ host/gkd shell
gkd shell COMMAND
  Run a command on the device

$ host/gkd shell sh
echo hi
hi
hostnamectl hostname
RK3326
^D

$ host/gkd mount
gkd mount PATH
  Mount the device’s r/w filesystem to a desired path on this device.

$ host/gkd mount /tmp/GkdPixelMount
Done! Took 0.01 seconds.

$ tree /tmp/GkdPixelMount -L2
|- .gkdtk -> home/gkdtk
|- .root
|  |- bin
|  |- dev
|  |- etc
|  [the rest is omitted]
|- home
|  |- roms
|  |- gkdtk

$ host/gkd disconnect
gkd disconnect DEVICE_ID
  Stop the GKDTK device daemon on the device and disconnect.

$ host/gkd disconnect '*'
Bye!
Done! Took 0.01 seconds.

```

## Packets

A packet's format is `ABBCCCCCC...LF` where:
1. `A` is a single ascii character denoting the type of the packet
2. `BB` is __two__ digits __in lowercase hex__ denoting the length of `CCCCCC...`,
3. `CCCCCC...` is a variable-length string, the contents of the packet, and
4. `LF` is an ascii line feed character, and is the last character of every packet.

For the sake of brevity, LF is not included in the documentation when a packet is
written. Each packet HAS to end with a line feed, or it will cause a desync.

Example packets:

- `S00` Server-side desync packet.
- `s03icu` Client-side syncing packet response.
- `A04ping` Ping packet
- `P25What would you do for a Klondike bar?` A __37-byte__ packet destined
for the backend `P`, namely plan9.

### Syncing dance

At the beginning of a connection or after a desync, the syncing dance takes place.
Side A is the device, and side B is the host.

1. Side A will consume all buffered text and send the ascii character
`0` 764 times, then send (without a linefeed) `S02hi` and wait 2 seconds for a response. If the
timeout expires or the response received is invalid, the desynced side will
wait an extra 300 milliseconds and repeat step 1.
2. Side B notices the desync, makes sure to read atleast 60 repetitions of
`0` and wait until it reads `S02hi`. It then sends `S03icu` over the wire.
3. Side A reads the response and replies with
`S2fWhat would you do for a Klondike bar? Say, $$$$` where `$$$$` is
any 4 ascii characters.
4. Side B sends `s04$$$$`, where `$$$$` is the same 4 characters it received in
the last packet.
5. The devices are now synced.

Side B may intentionally cause a desync if it has fallen out of sync,
but it has to wait atleast 3 seconds if resyncing doesn't start.

### Packet backends

- `P` - Plan9 backend
- `A` - System backend, for internal use.
- `$` - Shell backend
- `d` - Ignore
- `S` - Syncing dance


