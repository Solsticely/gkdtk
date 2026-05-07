#!/bin/sh

setup_serial() {
	echo 'Setting up serial!'
	. ./serial_config.sh
	# References:
	# https://www.kernel.org/doc/html/latest/usb/gadget_configfs.html
	# https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/main/main/postmarketos-initramfs/init_functions.sh?ref_type=heads#L827

	sh ./clean_usb.sh

	modprobe libcomposite || echo 'Couldn'"'"'t load libcomposite module'
	modprobe udc_core     || echo 'Couldn'"'"'t load udc_core module'
	modprobe u_serial     || echo 'Couldn'"'"'t load serial module'
	modprobe usb_f_acm    || echo 'Couldn'"'"'t load ACM module'

	mkdir -p                   "$CFS"
	echo "$USB_VENDORID"     > "$CFS/idVendor"
	echo "$USB_PRODUCTID"    > "$CFS/idProduct"
	# USB 2.0
	echo 0x0200              > "$CFS/bcdUSB"

	# Add some strings
	mkdir -p                   "$CFS/strings/0x409"
	echo "$USB_MANUFACTURER" > "$CFS/strings/0x409/manufacturer"
	echo "$USB_SERIAL"       > "$CFS/strings/0x409/serialnumber"
	echo "$USB_PRODUCT"      > "$CFS/strings/0x409/product"

	# Add the function/driver/mode
	mkdir -p                   "$CFS/functions/$USB_FUNCTION_DRIVER"
	# echo "$TTYGS_PORT_NUM"   > "$CFS/functions/$USB_FUNCTION_DRIVER/port_num"
 
	mkdir -p                   "$CFS/configs/c.1/strings/0x409"
	echo "USB serial"        > "$CFS/configs/c.1/strings/0x409/configuration"
	echo 500                 > "$CFS/configs/c.1/MaxPower"

	# Activate config
	ln -sf                     "$CFS/functions/$USB_FUNCTION_DRIVER" \
	                           "$CFS/configs/c.1"

	tree                       "$CFS"
	tree                       "/dev"

	# Activate gadget
	echo "$UDC"              > "$CFS/UDC" || echo "Couldn't write new UDC"
}

shell_serial () {
	: > /tmp/count_tries
	while [ "$(du -b /tmp/count_tries | awk '{print $1}')" -lt 5 ] && ! ls '/dev/ttyGS'* ; do
		echo 'tty not found yet, sleeping 4 seconds...'
		sleep 4
		printf 1 >>/tmp/count_tries
	done
	# shellcheck disable=SC2012
	TTYFILE=$(ls '/dev/ttyGS'* | head -1)
	echo 'Running loop on '"$TTYFILE"' (should never return)'
	cat "$TTYFILE" | bash > "$TTYFILE" 2>&1
}

setup_serial 2>&1 | tee ./setup_serial_log.out
sleep 4
shell_serial  2>&1 | tee ./shell_serial_log.out

