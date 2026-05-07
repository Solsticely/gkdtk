#!/bin/sh

clean_usb() {
	. ./serial_config.sh
	# References:
	# https://www.kernel.org/doc/html/latest/usb/gadget_configfs.html
	# https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/main/main/postmarketos-initramfs/init_functions.sh?ref_type=heads#L827

	if test -d        "$CFS" ; then	echo 'Rockchip gadget already registered, unregistering...'
		echo "" > "$CFS/UDC" && echo 'Done!' || echo 'Failed to unregister rockchip gadget. Doesn'"'"'t matter :)'
		sleep 2 ;                               echo 'Uprooting tree'
		rm -rf    "$CFS" &&     echo 'Done!' || echo 'Failed to uproot tree. Doesn'"'"'t matter :)'
	else                                            echo 'Rockchip gadget not found, not cleaning! :)'
	fi
}

clean_usb 2>&1 | tee clean_usb_log.out

