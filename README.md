# GKD toolkit

Hi! Have you ever tried to SSH into a handheld that doesn't have wifi
connectivity? No? Well have I the solution you're maybe looking for!

## What is GKD toolkit/GKDTK

If you're familiar with ADB (android debug bridge), GKD toolkit is
basically that. It changes the device's USB driver to a serial port
and runs a shell on the device.

## Requirements

- picocom
  - `sudo dnf install picocom`

## Usage

Copy all files in `device/` onto the GKD Pixel or other handheld
device, and mark them executable. To begin using GKDTK, run
`handheld/setup_serial.sh` on the device.

Once the host scripts are ready for general use, you can run them on
your host computer. In the meanwhile, you can use
`picocom /dev/ttyACM* -b 38400` to connect to a basic shell terminal :)

## Planned functionality

On the host, you will be able to use the following commands:

```shell
$ host/gkd devices
/dev/ttyACM0 - GameKiddy GKD Pixel2

$ host/gkd push
gkd push LOCAL REMOTE
  Upload a local file onto the remote device.

$ host/gkd push ~/.ssh/id_ed25519 /storage/.ssh/id_ed25519
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

$
```
