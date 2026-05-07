#!/bin/sh

# USB device controller name
# shellcheck disable=SC2012
UDC="$(ls /sys/class/udc/ | awk '{print $1}')"

# USB vendor ID and product ID
# We currently just identify as Fuzhou Rockchip Electronics Company Pixel2
USB_VENDORID='0x2207'
USB_PRODUCTID='0x0000'
USB_SERIAL='0123456789ABCDEF'
USB_MANUFACTURER='GameKiddy'
USB_PRODUCT='Pixel2'
USB_FUNCTION_DRIVER='acm.usb0'
CFS='/sys/kernel/config/usb_gadget/rockchip'

echo UDC "$UDC"
echo USB_VENDORID "$USB_VENDORID"
echo USB_PRODUCTID "$USB_PRODUCTID"
echo USB_SERIAL "$USB_SERIAL"
echo USB_MANUFACTURER "$USB_MANUFACTURER"
echo USB_PRODUCT "$USB_PRODUCT"
echo USB_FUNCTION_DRIVER "$USB_FUNCTION_DRIVER"
echo CFS "$CFS"


